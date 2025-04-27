"""
AV Catalog Standardizer - Category Extractor
-----------------------------------------
Category extraction service.
"""

import logging
from typing import Dict, List, Any, Optional

from utils.response_parser import parse_llm_response

logger = logging.getLogger(__name__)

class CategoryExtractor:
    """Service for extracting categories based on content and structure."""
    
    def __init__(self):
        """Initialize the category extractor."""
        pass
    
    def extract_categories(self, parsed_data: Dict, structure_info: Dict, llm_response: Dict) -> Dict:
        """
        Extract category information based on LLM response.
        
        Args:
            parsed_data: Dictionary containing parsed file data
            structure_info: Structure information from analysis
            llm_response: LLM response for category extraction
            
        Returns:
            Category information dictionary
        """
        logger.debug("Extracting category information")
        
        # Initialize category info
        category_info = {
            'row_categories': [],
            'content_patterns': [],
            'default_category': None
        }
        
        # Process LLM response
        if 'category_structure' in llm_response:
            # Extract category structure from LLM response
            category_structure = llm_response['category_structure']
            
            # Convert category structure to row-based mappings
            self._convert_structure_to_mappings(category_structure, parsed_data, structure_info, category_info)
        
        # Process explicit row categories if available
        if 'row_categories' in llm_response:
            for row_category in llm_response['row_categories']:
                if isinstance(row_category, dict) and 'start_row' in row_category:
                    # Validate row indices
                    start_row = row_category.get('start_row', 0)
                    end_row = row_category.get('end_row', len(parsed_data.get('raw_data', [])) - 1)
                    
                    # Add to category info
                    category_info['row_categories'].append({
                        'start_row': start_row,
                        'end_row': end_row,
                        'category_group': row_category.get('category_group', ''),
                        'category': row_category.get('category', '')
                    })
        
        # Process content patterns if available
        if 'content_patterns' in llm_response:
            for pattern in llm_response['content_patterns']:
                if isinstance(pattern, dict) and 'field' in pattern and 'pattern' in pattern:
                    # Add to category info
                    category_info['content_patterns'].append({
                        'field': pattern['field'],
                        'pattern': pattern['pattern'],
                        'category_group': pattern.get('category_group', ''),
                        'category': pattern.get('category', '')
                    })
        
        # Process default category if available
        if 'default_category' in llm_response:
            default_category = llm_response['default_category']
            
            if isinstance(default_category, dict):
                category_info['default_category'] = {
                    'category_group': default_category.get('category_group', ''),
                    'category': default_category.get('category', '')
                }
        
        # If we still have no defaults, try to infer from structure
        if not category_info['row_categories'] and not category_info['content_patterns'] and not category_info['default_category']:
            self._infer_categories_from_structure(parsed_data, structure_info, category_info)
        
        logger.debug(f"Category extraction complete: found {len(category_info['row_categories'])} row categories, "
                    f"{len(category_info['content_patterns'])} content patterns")
        
        return category_info
    
    def _convert_structure_to_mappings(self, category_structure: List[Dict], 
                                     parsed_data: Dict, structure_info: Dict, 
                                     category_info: Dict) -> None:
        """
        Convert category structure to row-based mappings.
        
        Args:
            category_structure: Category structure from LLM response
            parsed_data: Dictionary containing parsed file data
            structure_info: Structure information from analysis
            category_info: Category information to update
        """
        raw_data = parsed_data.get('raw_data', [])
        
        if not raw_data or not category_structure:
            return
        
        # Get structure markers
        structure_markers = structure_info.get('structure_markers', [])
        
        # Track current category
        current_category_group = ""
        current_category = ""
        current_start_row = 0
        
        # Sort structure markers by row index
        sorted_markers = sorted(structure_markers, key=lambda x: x.get('row_index', 0))
        
        for i, marker in enumerate(sorted_markers):
            marker_text = marker.get('text', '')
            marker_row = marker.get('row_index', 0)
            
            # Check if this marker indicates a category change
            category_match = None
            
            for cat_struct in category_structure:
                start_pattern = cat_struct.get('start_pattern', '')
                
                if start_pattern and start_pattern in marker_text:
                    # Found a matching category
                    category_match = cat_struct
                    break
            
            if category_match:
                # If we had a previous category, add it to row_categories
                if current_category or current_category_group:
                    category_info['row_categories'].append({
                        'start_row': current_start_row,
                        'end_row': marker_row - 1,
                        'category_group': current_category_group,
                        'category': current_category
                    })
                
                # Update current category
                current_category_group = category_match.get('category_group', '')
                current_category = category_match.get('category', '')
                current_start_row = marker_row + 1
        
        # Add the last category if exists
        if current_category or current_category_group:
            category_info['row_categories'].append({
                'start_row': current_start_row,
                'end_row': len(raw_data) - 1,
                'category_group': current_category_group,
                'category': current_category
            })
    
    def _infer_categories_from_structure(self, parsed_data: Dict, structure_info: Dict, category_info: Dict) -> None:
        """
        Infer categories from document structure.
        
        Args:
            parsed_data: Dictionary containing parsed file data
            structure_info: Structure information from analysis
            category_info: Category information to update
        """
        # Try to identify manufacturer first
        manufacturer = None
        
        # Common manufacturer keywords in headers
        manufacturer_keywords = ["Brand:", "Manufacturer:", "KEF", "Audio-Technica", "Glensound"]
        
        # Check structure markers for manufacturer indicators
        for marker in structure_info.get('structure_markers', []):
            marker_text = marker.get('text', '')
            
            for keyword in manufacturer_keywords:
                if keyword in marker_text:
                    # Extract manufacturer name
                    if "Brand:" in marker_text:
                        manufacturer = marker_text.split("Brand:")[1].strip()
                    elif "Manufacturer:" in marker_text:
                        manufacturer = marker_text.split("Manufacturer:")[1].strip()
                    else:
                        # Use the keyword itself
                        manufacturer = keyword
                        
                    break
                    
            if manufacturer:
                break
        
        # If we found a manufacturer, use it as default category group
        if manufacturer:
            category_info['default_category'] = {
                'category_group': manufacturer,
                'category': ''
            }
            
            # Also try to identify specific product categories
            self._infer_product_categories(parsed_data, structure_info, category_info, manufacturer)
    
    def _infer_product_categories(self, parsed_data: Dict, structure_info: Dict, 
                                category_info: Dict, manufacturer: str) -> None:
        """
        Infer product categories based on manufacturer-specific patterns.
        
        Args:
            parsed_data: Dictionary containing parsed file data
            structure_info: Structure information from analysis
            category_info: Category information to update
            manufacturer: Detected manufacturer name
        """
        # Manufacturer-specific category patterns
        category_patterns = {
            'KEF': {
                'column': 0,  # First column often contains series info for KEF
                'luxury': ["MUON", "REFERENCE", "BLADE"],
                'premium': ["LS50", "R SERIES"],
                'standard': ["Q SERIES", "T SERIES"]
            },
            'Audio-Technica': {
                'prefix_patterns': {
                    'AT-LP': 'Turntables',
                    'ATH-M': 'Headphones',
                    'AT2': 'Microphones',
                    'ATND': 'Network Audio'
                }
            },
            'Glensound': {
                'header_patterns': {
                    'DANTE': 'Network Audio',
                    'RAVENNA': 'Network Audio',
                    'MILAN': 'Network Audio',
                    'COMMENTARY': 'Commentary Systems',
                    'DARK': 'Dark Outside Broadcast'
                }
            }
        }
        
        # If manufacturer is in our patterns list
        if manufacturer in category_patterns:
            patterns = category_patterns[manufacturer]
            
            # Handle KEF category patterns
            if 'luxury' in patterns and 'premium' in patterns and 'standard' in patterns:
                column_idx = patterns.get('column', 0)
                
                # Examine first column of data for series information
                raw_data = parsed_data.get('raw_data', [])
                
                for i, row in enumerate(raw_data):
                    if i >= structure_info.get('data_start_row', 0) and len(row) > column_idx:
                        value = str(row[column_idx])
                        
                        # Check for luxury/premium/standard patterns
                        if any(luxury in value.upper() for luxury in patterns['luxury']):
                            category = "Luxury Audio"
                        elif any(premium in value.upper() for premium in patterns['premium']):
                            category = "Premium Audio"
                        elif any(standard in value.upper() for standard in patterns['standard']):
                            category = "Standard Audio"
                        else:
                            continue
                            
                        # Add content pattern
                        category_info['content_patterns'].append({
                            'field': f"Column{column_idx}",
                            'pattern': value,
                            'category_group': manufacturer,
                            'category': category
                        })
            
            # Handle Audio-Technica prefix patterns
            if 'prefix_patterns' in patterns:
                # Add content patterns for each prefix
                for prefix, category in patterns['prefix_patterns'].items():
                    category_info['content_patterns'].append({
                        'field': 'SKU',  # Usually in SKU field
                        'pattern': prefix,
                        'category_group': manufacturer,
                        'category': category
                    })
            
            # Handle Glensound header patterns
            if 'header_patterns' in patterns:
                # Check structure markers for header patterns
                for marker in structure_info.get('structure_markers', []):
                    marker_text = marker.get('text', '').upper()
                    
                    for header_pattern, category in patterns['header_patterns'].items():
                        if header_pattern in marker_text:
                            # This header indicates a category section
                            category_info['row_categories'].append({
                                'start_row': marker.get('row_index', 0) + 1,
                                'end_row': len(parsed_data.get('raw_data', [])) - 1,  # Until end of file or next marker
                                'category_group': manufacturer,
                                'category': category
                            })
                            break