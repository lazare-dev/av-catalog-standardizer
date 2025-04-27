"""
AV Catalog Standardizer - Structure Analyzer
------------------------------------------
Document structure analysis service.
"""

import logging
from typing import Dict, List, Any

from utils.response_parser import parse_llm_response

logger = logging.getLogger(__name__)

class StructureAnalyzer:
    """Service for analyzing document structure."""
    
    def __init__(self):
        """Initialize the structure analyzer."""
        pass
    
    def analyze(self, parsed_data: Dict, llm_response: Dict) -> Dict:
        """
        Analyze document structure based on LLM response.
        
        Args:
            parsed_data: Dictionary containing parsed file data
            llm_response: LLM response for structure analysis
            
        Returns:
            Structure information dictionary
        """
        logger.debug("Analyzing document structure")
        
        # Start with original headers
        structure_info = {
            'headers': parsed_data.get('headers', []),
            'data_start_row': 0,
            'non_data_rows': [],
            'structure_markers': []
        }
        
        # Update with information from LLM response
        if 'headers' in llm_response:
            structure_info['headers'] = llm_response['headers']
            
        if 'data_start_row' in llm_response:
            structure_info['data_start_row'] = llm_response['data_start_row']
            
        if 'non_data_rows' in llm_response:
            structure_info['non_data_rows'] = llm_response['non_data_rows']
            
        if 'structure_markers' in llm_response:
            structure_info['structure_markers'] = llm_response['structure_markers']
        
        # Extract file format information
        structure_info['file_format'] = parsed_data.get('structure', {}).get('format', 'unknown')
        
        # Additional processing for special cases
        self._handle_special_cases(structure_info, parsed_data)
        
        # Validate structure information
        structure_info = self._validate_structure_info(structure_info, parsed_data)
        
        logger.debug(f"Structure analysis complete: data starts at row {structure_info['data_start_row']}, "
                    f"found {len(structure_info['structure_markers'])} structure markers")
        
        return structure_info
    
    def _handle_special_cases(self, structure_info: Dict, parsed_data: Dict) -> None:
        """
        Handle special cases based on catalog format.
        
        Args:
            structure_info: Structure information to update
            parsed_data: Dictionary containing parsed file data
        """
        # Check for Excel-specific structure
        if parsed_data.get('structure', {}).get('format') == 'excel':
            # If we have multi-sheet data, add sheet information
            if 'all_sheets_data' in parsed_data:
                structure_info['excel_info'] = {
                    'main_sheet': parsed_data.get('structure', {}).get('main_sheet', ''),
                    'all_sheets': parsed_data.get('structure', {}).get('all_sheets', [])
                }
        
        # Check for PDF-specific structure
        elif parsed_data.get('structure', {}).get('format') == 'pdf':
            # Add table information for PDFs
            if 'all_tables' in parsed_data.get('structure', {}):
                structure_info['pdf_info'] = {
                    'num_pages': parsed_data.get('structure', {}).get('num_pages', 0),
                    'num_tables': len(parsed_data.get('structure', {}).get('all_tables', []))
                }
    
    def _validate_structure_info(self, structure_info: Dict, parsed_data: Dict) -> Dict:
        """
        Validate and clean structure information.
        
        Args:
            structure_info: Structure information to validate
            parsed_data: Dictionary containing parsed file data
            
        Returns:
            Validated structure information
        """
        # Ensure data_start_row is valid
        raw_data = parsed_data.get('raw_data', [])
        
        if not raw_data:
            structure_info['data_start_row'] = 0
            structure_info['non_data_rows'] = []
            return structure_info
            
        max_row = len(raw_data) - 1
        
        if structure_info['data_start_row'] > max_row:
            logger.warning(f"Invalid data_start_row: {structure_info['data_start_row']} > {max_row}")
            structure_info['data_start_row'] = 0
        
        # Validate non_data_rows (ensure they're all integers and in range)
        valid_non_data_rows = []
        for row in structure_info['non_data_rows']:
            try:
                row_idx = int(row)
                if 0 <= row_idx <= max_row:
                    valid_non_data_rows.append(row_idx)
            except (ValueError, TypeError):
                continue
                
        structure_info['non_data_rows'] = valid_non_data_rows
        
        # Validate structure markers
        valid_markers = []
        for marker in structure_info['structure_markers']:
            if not isinstance(marker, dict):
                continue
                
            # Ensure required fields are present
            if 'row_index' not in marker or 'text' not in marker or 'type' not in marker:
                continue
                
            # Validate row_index
            try:
                row_idx = int(marker['row_index'])
                if 0 <= row_idx <= max_row:
                    # Update the marker with validated row_index
                    marker['row_index'] = row_idx
                    valid_markers.append(marker)
            except (ValueError, TypeError):
                continue
                
        structure_info['structure_markers'] = valid_markers
        
        return structure_info