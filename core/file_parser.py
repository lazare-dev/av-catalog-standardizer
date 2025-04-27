"""
AV Catalog Standardizer - File Parser
-----------------------------------
Multi-format file parsing utilities.
"""

import os
import pandas as pd
import PyPDF2
import pdfplumber
import logging
import magic
from typing import List, Dict, Union, Tuple

logger = logging.getLogger(__name__)

class FileParser:
    """A class for parsing different file formats while preserving structure."""
    
    def __init__(self):
        """Initialize the FileParser."""
        self.supported_formats = {
            'csv': self._parse_csv,
            'xlsx': self._parse_excel,
            'xls': self._parse_excel,
            'pdf': self._parse_pdf
        }
    
    def parse(self, file_path: str) -> Dict:
        """
        Parse the file at the given path.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dict containing parsed data and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect file type
        file_ext = os.path.splitext(file_path)[1].lower().replace('.', '')
        mime_type = magic.from_file(file_path, mime=True)
        
        logger.info(f"Parsing file: {file_path} (type: {file_ext}, MIME: {mime_type})")
        
        # Validate supported format
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Parse the file using the appropriate parser
        parser_func = self.supported_formats[file_ext]
        parsed_data = parser_func(file_path)
        
        # Add metadata
        parsed_data['metadata'] = {
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'file_type': file_ext,
            'mime_type': mime_type
        }
        
        return parsed_data
    
    def _parse_csv(self, file_path: str) -> Dict:
        """
        Parse a CSV file while preserving structure.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dict containing raw data and structural info
        """
        # Try different encodings and delimiters
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        delimiters = [',', ';', '\t', '|']
        
        data = None
        encoding_used = None
        delimiter_used = None
        
        for encoding in encodings:
            if data is not None:
                break
                
            try:
                # First, read as text to analyze structure
                with open(file_path, 'r', encoding=encoding) as f:
                    sample_content = f.read(4096)  # Read first 4KB to analyze
                
                # Try to determine delimiter from sample
                for delimiter in delimiters:
                    if delimiter in sample_content:
                        # Try parsing with this delimiter
                        try:
                            # Read file using pandas but preserve original structure
                            df = pd.read_csv(
                                file_path, 
                                delimiter=delimiter,
                                encoding=encoding,
                                dtype=str,  # Keep everything as strings to preserve format
                                keep_default_na=False,  # Don't convert empty cells to NaN
                                na_filter=False  # Don't interpret NA values
                            )
                            data = df
                            encoding_used = encoding
                            delimiter_used = delimiter
                            break
                        except Exception as e:
                            logger.debug(f"Failed with delimiter {delimiter}: {str(e)}")
                            continue
            
            except Exception as e:
                logger.debug(f"Failed with encoding {encoding}: {str(e)}")
                continue
        
        if data is None:
            raise ValueError("Could not parse CSV file with any encoding/delimiter combination")
        
        # Convert to structured raw data
        raw_data = []
        
        # Get headers
        headers = data.columns.tolist()
        
        # Get data rows including empty cells (preserving structure)
        for _, row in data.iterrows():
            raw_data.append(row.tolist())
        
        # Detect possible section headers or category markers
        structure_markers = self._detect_structure_markers(raw_data)
        
        return {
            'raw_data': raw_data,
            'headers': headers,
            'structure': {
                'potential_markers': structure_markers,
                'format': 'csv',
                'encoding': encoding_used,
                'delimiter': delimiter_used
            }
        }
    
    def _parse_excel(self, file_path: str) -> Dict:
        """
        Parse an Excel file while preserving structure.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dict containing raw data and structural info
        """
        try:
            # Read all sheets to determine which might contain product data
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            # Initialize data structure
            all_sheets_data = {}
            
            # Process each sheet
            for sheet in sheet_names:
                logger.debug(f"Processing sheet: {sheet}")
                
                # Read sheet data preserving formats
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet,
                    dtype=str,  # Keep everything as strings
                    keep_default_na=False,  # Don't convert empty cells to NaN
                    na_filter=False  # Don't interpret NA values
                )
                
                # Check if sheet might contain product data
                # (simple heuristic: sheets with many rows are likely data)
                if len(df) > 5:  # Arbitrary threshold
                    headers = df.columns.tolist()
                    raw_data = []
                    
                    for _, row in df.iterrows():
                        raw_data.append(row.tolist())
                    
                    # Detect section markers or special formatting
                    structure_markers = self._detect_structure_markers(raw_data)
                    
                    all_sheets_data[sheet] = {
                        'raw_data': raw_data,
                        'headers': headers,
                        'structure': {
                            'potential_markers': structure_markers
                        }
                    }
            
            # Identify the main product data sheet (most rows)
            main_sheet = max(all_sheets_data.keys(), key=lambda x: len(all_sheets_data[x]['raw_data']))
            
            return {
                'raw_data': all_sheets_data[main_sheet]['raw_data'],
                'headers': all_sheets_data[main_sheet]['headers'],
                'structure': {
                    'format': 'excel',
                    'main_sheet': main_sheet,
                    'all_sheets': list(all_sheets_data.keys()),
                    'potential_markers': all_sheets_data[main_sheet]['structure']['potential_markers']
                },
                'all_sheets_data': all_sheets_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise
    
    def _parse_pdf(self, file_path: str) -> Dict:
        """
        Parse a PDF file while attempting to preserve tabular structure.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing raw data and structural info
        """
        try:
            # First get document info
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                info = pdf_reader.metadata
                num_pages = len(pdf_reader.pages)
            
            # Now extract tables with pdfplumber
            all_tables = []
            text_content = []
            
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Extract text for context
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Filter out empty rows
                            filtered_table = [row for row in table if any(cell and cell.strip() for cell in row)]
                            if filtered_table:
                                all_tables.append({
                                    'page': i + 1,
                                    'data': filtered_table
                                })
            
            # If we have tables, use the first complete one as our main data
            raw_data = []
            headers = []
            
            if all_tables:
                # Find the most likely "main" table (most rows with reasonable column count)
                main_table = max(all_tables, key=lambda t: len(t['data']))
                
                # Extract headers and data
                if len(main_table['data']) > 1:
                    headers = main_table['data'][0]
                    raw_data = main_table['data'][1:]
            
            # If no tables found or tables seem sparse, try parsing text content
            if not raw_data and text_content:
                raw_data, headers = self._extract_structure_from_text(text_content)
            
            structure_markers = self._detect_structure_markers(raw_data)
            
            return {
                'raw_data': raw_data,
                'headers': headers,
                'structure': {
                    'format': 'pdf',
                    'num_pages': num_pages,
                    'all_tables': all_tables,
                    'text_content': text_content,
                    'potential_markers': structure_markers
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF file: {str(e)}")
            raise
    
    def _detect_structure_markers(self, raw_data: List[List]) -> List[Dict]:
        """
        Detect potential structure markers in the data.
        
        Args:
            raw_data: Raw data as list of lists
            
        Returns:
            List of detected marker info
        """
        markers = []
        
        # Look for rows that might indicate category changes
        for i, row in enumerate(raw_data):
            # Check for mostly empty rows
            if row and sum(1 for cell in row if cell and str(cell).strip()) <= 2:
                # This might be a category marker
                non_empty_cells = [str(cell).strip() for cell in row if cell and str(cell).strip()]
                if non_empty_cells:
                    markers.append({
                        'row_index': i,
                        'text': ' '.join(non_empty_cells),
                        'type': 'section_divider',
                        'confidence': 0.8
                    })
            
            # Check for rows with special markers like "#VALUE!" (KEF catalog)
            if any('#VALUE!' in str(cell) for cell in row if cell):
                markers.append({
                    'row_index': i,
                    'text': ' '.join(str(cell).strip() for cell in row if cell and str(cell).strip()),
                    'type': 'category_change',
                    'confidence': 0.9
                })
            
            # Check for rows that might be headers (caps, special formatting)
            has_caps = sum(1 for cell in row if cell and str(cell).strip() and str(cell).strip().isupper()) > 1
            might_be_header = has_caps or any(keyword in str(cell) for cell in row for keyword in ['Brand:', 'Network Series', 'DANTE', 'RAVENNA'])
            
            if might_be_header:
                markers.append({
                    'row_index': i,
                    'text': ' '.join(str(cell).strip() for cell in row if cell and str(cell).strip()),
                    'type': 'header',
                    'confidence': 0.7
                })
        
        return markers
    
    def _extract_structure_from_text(self, text_content: List[str]) -> Tuple[List[List], List[str]]:
        """
        Attempt to extract tabular data from text content.
        
        Args:
            text_content: List of text blocks
            
        Returns:
            Tuple of (raw_data, headers)
        """
        raw_data = []
        headers = []
        
        # If we have text content, try to find table-like structures
        for text_block in text_content:
            lines = text_block.split('\n')
            current_section = []
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                
                # If line has multiple tab or multiple space separators, it might be tabular
                if '\t' in line or '  ' in line:
                    if '\t' in line:
                        cells = line.split('\t')
                    else:
                        # Split by multiple spaces (2 or more)
                        import re
                        cells = re.split(r'\s{2,}', line.strip())
                    
                    cells = [cell.strip() for cell in cells]
                    
                    # If this is the first row with this pattern, assume it's headers
                    if not headers and all(cell for cell in cells):
                        headers = cells
                    else:
                        raw_data.append(cells)
                        
                # Otherwise, it might be a section header or non-tabular content
                else:
                    # Check if this might be a section header
                    if line.isupper() or line.endswith(':'):
                        current_section = [line.strip()]
        
        # If we couldn't find proper headers, generate default ones
        if not headers and raw_data:
            max_cols = max(len(row) for row in raw_data)
            headers = [f'Column{i+1}' for i in range(max_cols)]
            
            # Ensure all rows have the same number of columns
            for i, row in enumerate(raw_data):
                if len(row) < max_cols:
                    raw_data[i] = row + [''] * (max_cols - len(row))
        
        return raw_data, headers