"""
AV Catalog Standardizer - Response Parser
---------------------------------------
LLM response parsing utilities.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

def parse_llm_response(response: str) -> Dict:
    """
    Parse a response from the LLM to extract structured data.
    
    Args:
        response: Text response from LLM
        
    Returns:
        Parsed data as dictionary
    """
    logger.debug("Parsing LLM response")
    
    if not response or not isinstance(response, str):
        logger.warning("Empty or invalid response")
        return {}
    
    # First try to clean the response
    cleaned_response = clean_json_response(response)
    
    # Try to parse the cleaned response
    try:
        data = json.loads(cleaned_response)
        return data
    except json.JSONDecodeError:
        # If cleaning didn't help, try to extract JSON blocks
        try:
            # Look for JSON-like content (between curly braces)
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                
                # Try to parse the extracted JSON
                data = json.loads(json_str)
                return data
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Raw response: {response[:500]}...")
    
    # Return empty dict if all parsing attempts failed
    return {}

def extract_field_mappings(llm_response: Dict) -> Dict[str, str]:
    """
    Extract field mappings from LLM response.
    
    Args:
        llm_response: Parsed LLM response
        
    Returns:
        Dictionary mapping original fields to standard fields
    """
    mappings = {}
    
    if 'field_mappings' in llm_response:
        for original_field, mapping_info in llm_response['field_mappings'].items():
            if isinstance(mapping_info, dict) and 'standard_field' in mapping_info:
                mappings[original_field] = mapping_info['standard_field']
            elif isinstance(mapping_info, str):
                # Handle case where mapping is just a string
                mappings[original_field] = mapping_info
    
    return mappings

def extract_category_structure(llm_response: Dict) -> Dict:
    """
    Extract category structure from LLM response.
    
    Args:
        llm_response: Parsed LLM response
        
    Returns:
        Dictionary containing category structure information
    """
    category_info = {
        'categories': [],
        'default_category': None
    }
    
    if 'category_structure' in llm_response:
        category_structure = llm_response['category_structure']
        if isinstance(category_structure, list):
            category_info['categories'] = category_structure
        elif isinstance(category_structure, dict):
            # Handle case where it's a dict with additional info
            category_info['categories'] = category_structure.get('categories', [])
    
    if 'default_category' in llm_response:
        category_info['default_category'] = llm_response['default_category']
    
    return category_info

def extract_structure_markers(llm_response: Dict) -> Dict:
    """
    Extract structure markers from LLM response.
    
    Args:
        llm_response: Parsed LLM response
        
    Returns:
        Dictionary containing structure marker information
    """
    structure_info = {
        'headers': [],
        'data_start_row': 0,
        'markers': []
    }
    
    if 'headers' in llm_response:
        headers = llm_response['headers']
        if isinstance(headers, list):
            structure_info['headers'] = headers
    
    if 'data_start_row' in llm_response:
        try:
            structure_info['data_start_row'] = int(llm_response['data_start_row'])
        except (ValueError, TypeError):
            # If it's not a valid integer, default to 0
            structure_info['data_start_row'] = 0
    
    if 'structure_markers' in llm_response:
        markers = llm_response['structure_markers']
        if isinstance(markers, list):
            structure_info['markers'] = markers
    
    return structure_info

def extract_normalization_rules(llm_response: Dict) -> Dict:
    """
    Extract normalization rules from LLM response.
    
    Args:
        llm_response: Parsed LLM response
        
    Returns:
        Dictionary containing normalization rules
    """
    normalization_rules = {
        'price_normalization': {},
        'unit_normalization': {},
        'category_normalization': {}
    }
    
    if 'price_normalization' in llm_response and isinstance(llm_response['price_normalization'], dict):
        normalization_rules['price_normalization'] = llm_response['price_normalization']
    
    if 'unit_normalization' in llm_response and isinstance(llm_response['unit_normalization'], dict):
        normalization_rules['unit_normalization'] = llm_response['unit_normalization']
    
    if 'category_normalization' in llm_response and isinstance(llm_response['category_normalization'], dict):
        normalization_rules['category_normalization'] = llm_response['category_normalization']
    
    return normalization_rules

def clean_json_response(response: str) -> str:
    """
    Clean a response to ensure it can be parsed as JSON.
    
    Args:
        response: Raw response from LLM
        
    Returns:
        Cleaned response
    """
    if not response:
        return "{}"
    
    # Try to extract just the JSON part
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r'(\{.*\})', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response
    
    # Remove markdown code block syntax if present
    json_str = re.sub(r'^```json\s*', '', json_str)
    json_str = re.sub(r'```$', '', json_str)
    json_str = re.sub(r'```python\s*', '', json_str)
    json_str = re.sub(r'```javascript\s*', '', json_str)
    
    # Fix common JSON syntax errors
    
    # Replace single quotes with double quotes (but not within quoted strings)
    # This is a simplified approach and might not handle all cases correctly
    json_str = re.sub(r"(?<!\\\")\'([^\']*?)(?<!\\)\'", r'"\1"', json_str)
    
    # Ensure property names are double-quoted
    json_str = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', json_str)
    
    # Handle trailing commas
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    # Add missing quotes around property names
    json_str = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', json_str)
    
    # Remove any non-JSON content before the first { or after the last }
    start_idx = json_str.find('{')
    end_idx = json_str.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = json_str[start_idx:end_idx+1]
    
    # Check if the result is valid JSON
    if not is_valid_json(json_str):
        # If still not valid, try a more aggressive approach
        # Replace any non-ASCII characters
        json_str = re.sub(r'[^\x00-\x7F]+', '', json_str)
        
        # Try to balance braces
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            json_str = '{' * (close_braces - open_braces) + json_str
    
    return json_str

def is_valid_json(json_str: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        json_str: String to check
        
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False