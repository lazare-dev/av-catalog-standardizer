"""
AV Catalog Standardizer - Data Processor
--------------------------------------
Main data processing pipeline.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd

from core.file_parser import FileParser
from core.llm_client import phi_client
from config.settings import CHUNK_SIZE
from prompts.structure_analysis import get_structure_analysis_prompt
from prompts.field_mapping import get_field_mapping_prompt
from prompts.category_extraction import get_category_extraction_prompt
from prompts.value_normalization import get_value_normalization_prompt
from services.structure_analyzer import StructureAnalyzer
from services.field_mapper import FieldMapper
from services.category_extractor import CategoryExtractor
from services.value_normalizer import ValueNormalizer
from services.validator import validate_output
from utils.response_parser import parse_llm_response

logger = logging.getLogger(__name__)

def process_catalog(file_path: str) -> Tuple[List[Dict], Dict, Dict]:
    """
    Process a catalog file into standardized format.
    
    Args:
        file_path: Path to the catalog file
        
    Returns:
        Tuple of (transformed_data, validation_results, field_mappings)
    """
    logger.info(f"Processing catalog file: {file_path}")
    
    # Initialize components
    file_parser = FileParser()
    structure_analyzer = StructureAnalyzer()
    field_mapper = FieldMapper()
    category_extractor = CategoryExtractor()
    value_normalizer = ValueNormalizer()
    
    # Step 1: Parse the file
    logger.info("Step 1: Parsing file")
    parsed_data = file_parser.parse(file_path)
    
    # Step 2: Analyze document structure
    logger.info("Step 2: Analyzing document structure")
    structure_prompt = get_structure_analysis_prompt(parsed_data)
    structure_analysis_response = phi_client.generate_json(structure_prompt)
    structure_info = structure_analyzer.analyze(parsed_data, structure_analysis_response)
    
    # Step 3: Extract headers and sample data based on structure
    logger.info("Step 3: Extracting headers and sample data")
    headers = structure_info.get('headers', parsed_data.get('headers', []))
    
    # Get sample data for field mapping
    sample_rows = _get_sample_rows(parsed_data['raw_data'], structure_info)
    
    # Step 4: Map fields based on content patterns
    logger.info("Step 4: Mapping fields")
    mapping_prompt = get_field_mapping_prompt(headers, sample_rows)
    mapping_response = phi_client.generate_json(mapping_prompt)
    field_mappings = field_mapper.map_fields(headers, sample_rows, mapping_response)
    
    # Step 5: Extract category information
    logger.info("Step 5: Extracting categories")
    category_prompt = get_category_extraction_prompt(parsed_data, structure_info)
    category_response = phi_client.generate_json(category_prompt)
    category_info = category_extractor.extract_categories(parsed_data, structure_info, category_response)
    
    # Step 6: Process data in chunks
    logger.info("Step 6: Processing data in chunks")
    transformed_data = []
    
    # Get data rows (filtering out non-data rows based on structure analysis)
    data_rows = _get_data_rows(parsed_data['raw_data'], structure_info)
    
    # Process in chunks to avoid memory issues
    for i in range(0, len(data_rows), CHUNK_SIZE):
        chunk = data_rows[i:i+CHUNK_SIZE]
        chunk_transformed = _transform_chunk(
            chunk, 
            headers,
            field_mappings, 
            category_info, 
            structure_info,
            value_normalizer
        )
        transformed_data.extend(chunk_transformed)
        logger.debug(f"Processed chunk {i//CHUNK_SIZE + 1}/{(len(data_rows) + CHUNK_SIZE - 1)//CHUNK_SIZE}")
    
    # Step 7: Validate output
    logger.info("Step 7: Validating output")
    validation_results = validate_output(transformed_data)
    
    # Step 8: Remove invalid entries and ensure required fields
    logger.info("Step 8: Filtering and finalizing data")
    final_data = _filter_and_finalize_data(transformed_data, validation_results)
    
    return final_data, validation_results, field_mappings

def _get_sample_rows(raw_data: List[List], structure_info: Dict) -> List[List]:
    """
    Get representative sample rows for field mapping.
    
    Args:
        raw_data: Raw data as list of lists
        structure_info: Structure information from analysis
        
    Returns:
        List of sample rows
    """
    data_rows = _get_data_rows(raw_data, structure_info)
    
    # Get a representative sample (first, middle, and last rows)
    sample_indices = [0]
    
    if len(data_rows) > 1:
        sample_indices.append(len(data_rows) // 2)
        
    if len(data_rows) > 2:
        sample_indices.append(len(data_rows) - 1)
    
    # Deduplicate indices
    sample_indices = list(set(sample_indices))
    
    return [data_rows[i] for i in sample_indices]

def _get_data_rows(raw_data: List[List], structure_info: Dict) -> List[List]:
    """
    Extract just the data rows based on structure analysis.
    
    Args:
        raw_data: Raw data as list of lists
        structure_info: Structure information from analysis
        
    Returns:
        List of data rows
    """
    start_row = structure_info.get('data_start_row', 0)
    
    # Get indices to exclude (headers, section markers, etc.)
    exclude_indices = set()
    
    # Add any non-data rows identified in structure analysis
    if 'non_data_rows' in structure_info:
        exclude_indices.update(structure_info['non_data_rows'])
    
    # Filter the data
    data_rows = []
    
    for i, row in enumerate(raw_data):
        # Skip rows before data starts
        if i < start_row:
            continue
            
        # Skip explicitly excluded rows
        if i in exclude_indices:
            continue
            
        # Skip empty or near-empty rows
        if not row or sum(1 for cell in row if cell and str(cell).strip()) <= 1:
            continue
            
        data_rows.append(row)
    
    return data_rows

def _transform_chunk(chunk: List[List], headers: List[str], 
                   field_mappings: Dict, category_info: Dict, 
                   structure_info: Dict, normalizer: ValueNormalizer) -> List[Dict]:
    """
    Transform a chunk of data using the field mappings and category info.
    
    Args:
        chunk: Chunk of data rows
        headers: Column headers
        field_mappings: Field mapping information
        category_info: Category information
        structure_info: Structure information
        normalizer: Value normalizer instance
        
    Returns:
        List of transformed data dictionaries
    """
    transformed_chunk = []
    
    for row_idx, row in enumerate(chunk):
        # Create a dictionary for the row using original headers
        row_dict = {}
        for i, header in enumerate(headers):
            if i < len(row):
                row_dict[header] = row[i]
        
        # Apply transformations using field mappings
        transformed_row = {}
        
        # Apply field mappings
        for original_field, mapping in field_mappings.get('field_mappings', {}).items():
            standard_field = mapping.get('standard_field')
            if standard_field and original_field in row_dict:
                # Get the value
                value = row_dict[original_field]
                
                # Normalize the value based on field type
                normalized_value = normalizer.normalize_value(value, standard_field)
                
                # Add to transformed row
                transformed_row[standard_field] = normalized_value
        
        # Apply category information if available
        if category_info:
            # Determine applicable category based on row index or content
            category = _get_applicable_category(row_dict, row_idx, category_info)
            
            if category:
                if 'Category_Group' in category and not transformed_row.get('Category_Group'):
                    transformed_row['Category_Group'] = category['Category_Group']
                    
                if 'Category' in category and not transformed_row.get('Category'):
                    transformed_row['Category'] = category['Category']
        
        # Add manufacturer if detected
        if 'manufacturer_detection' in field_mappings and not transformed_row.get('Manufacturer'):
            manufacturer = field_mappings['manufacturer_detection'].get('name')
            if manufacturer:
                transformed_row['Manufacturer'] = manufacturer
        
        transformed_chunk.append(transformed_row)
    
    return transformed_chunk

def _get_applicable_category(row_dict: Dict, row_idx: int, category_info: Dict) -> Optional[Dict]:
    """
    Determine the applicable category for a row.
    
    Args:
        row_dict: Dictionary representation of the row
        row_idx: Index of the row in the chunk
        category_info: Category information from extraction
        
    Returns:
        Dict with applicable category info or None
    """
    # Check if there are explicit row-to-category mappings
    if 'row_categories' in category_info:
        for cat_mapping in category_info['row_categories']:
            start_row = cat_mapping.get('start_row', 0)
            end_row = cat_mapping.get('end_row', float('inf'))
            
            if start_row <= row_idx <= end_row:
                return {
                    'Category_Group': cat_mapping.get('category_group', ''),
                    'Category': cat_mapping.get('category', '')
                }
    
    # Check for content-based category matching
    if 'content_patterns' in category_info:
        for pattern in category_info['content_patterns']:
            field = pattern.get('field')
            value_pattern = pattern.get('pattern')
            
            if field and value_pattern and field in row_dict:
                row_value = str(row_dict[field])
                
                # Simple string matching for now
                if value_pattern in row_value:
                    return {
                        'Category_Group': pattern.get('category_group', ''),
                        'Category': pattern.get('category', '')
                    }
    
    # Return default category if available
    if 'default_category' in category_info:
        return {
            'Category_Group': category_info['default_category'].get('category_group', ''),
            'Category': category_info['default_category'].get('category', '')
        }
    
    return None

def _filter_and_finalize_data(transformed_data: List[Dict], validation_results: Dict) -> List[Dict]:
    """
    Filter out invalid entries and ensure required fields.
    
    Args:
        transformed_data: List of transformed data dictionaries
        validation_results: Validation results
        
    Returns:
        Filtered and finalized data
    """
    from config.schema import OUTPUT_SCHEMA
    required_fields = OUTPUT_SCHEMA.get('required', [])
    
    filtered_data = []
    
    for i, item in enumerate(transformed_data):
        # Skip items with missing required fields
        if any(field not in item or not item[field] for field in required_fields):
            continue
        
        # Skip items with validation errors if they're critical
        if validation_results.get('errors'):
            item_errors = [e for e in validation_results['errors'] if e.get('index') == i]
            if any(e.get('severity') == 'critical' for e in item_errors):
                continue
        
        filtered_data.append(item)
    
    return filtered_data