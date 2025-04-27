"""
AV Catalog Standardizer - Category Extraction Prompts
--------------------------------------------------
Prompts for category extraction based on content and structure.
"""

from typing import Dict, List

def get_category_extraction_prompt(parsed_data: Dict, structure_info: Dict) -> str:
    """
    Create a prompt for extracting category information.
    
    Args:
        parsed_data: Dictionary containing parsed file data
        structure_info: Structure information from analysis
        
    Returns:
        Prompt string for category extraction
    """
    # Extract relevant sections that may indicate categories
    relevant_sections = _extract_relevant_sections(parsed_data, structure_info)
    
    # Format the relevant sections as text
    sections_text = _format_sections(relevant_sections)
    
    prompt = f"""
    Review these sections that may indicate categories:
    
    {sections_text}
    
    Identify:
    1. Main category headers/groups
    2. Subcategory markers
    3. How categories apply to subsequent product rows
    
    For each identified category structure, determine:
    - If it's a main category or subcategory
    - How to extract the category name clearly
    - The pattern that indicates when this category starts applying to products
    - The pattern that indicates when this category stops applying to products
    
    Pay special attention to:
    - Section headers like "Brand: Audio-Technica" or "AT - Network Series"
    - Headers like "DANTE/RAVENNA/MILAN NETWORK AUDIO UNITS" in Glensound catalogs
    - Luxury/Premium/Standard category indicators 
    - Special markers like "#VALUE!" in KEF catalogs which might indicate category changes
    
    Return the category structure and rules for applying categories to products as a JSON object with the following structure:
    {{
      "category_structure": [
        {{
          "category_group": "main category group",
          "category": "specific category",
          "start_pattern": "pattern indicating where this category starts",
          "end_pattern": "pattern indicating where this category ends",
          "confidence": 0.0-1.0
        }},
        ...
      ],
      "row_categories": [
        {{
          "start_row": row index where category begins,
          "end_row": row index where category ends,
          "category_group": "main category group",
          "category": "specific category"
        }},
        ...
      ],
      "content_patterns": [
        {{
          "field": "field to check",
          "pattern": "content pattern to match",
          "category_group": "main category group",
          "category": "specific category"
        }},
        ...
      ],
      "default_category": {{
        "category_group": "default main category group",
        "category": "default specific category"
      }}
    }}
    """
    
    return prompt

def _extract_relevant_sections(parsed_data: Dict, structure_info: Dict) -> List[Dict]:
    """
    Extract sections that may indicate categories.
    
    Args:
        parsed_data: Dictionary containing parsed file data
        structure_info: Structure information from analysis
        
    Returns:
        List of relevant sections
    """
    relevant_sections = []
    
    # Extract structure markers from structure info
    structure_markers = structure_info.get('structure_markers', [])
    
    for marker in structure_markers:
        if marker.get('type') in ['category_header', 'section_divider', 'special_marker']:
            relevant_sections.append({
                'type': marker.get('type'),
                'text': marker.get('text', ''),
                'row_index': marker.get('row_index', 0)
            })
    
    # Also include any potential markers from the original parsing
    original_markers = parsed_data.get('structure', {}).get('potential_markers', [])
    
    for marker in original_markers:
        # Avoid duplicates
        if not any(rs.get('row_index') == marker.get('row_index') for rs in relevant_sections):
            relevant_sections.append({
                'type': marker.get('type', 'unknown'),
                'text': marker.get('text', ''),
                'row_index': marker.get('row_index', 0)
            })
    
    # Sort by row index
    relevant_sections.sort(key=lambda x: x.get('row_index', 0))
    
    return relevant_sections

def _format_sections(sections: List[Dict]) -> str:
    """
    Format sections as a readable text block.
    
    Args:
        sections: List of relevant sections
        
    Returns:
        Formatted text representation
    """
    lines = []
    
    for section in sections:
        row_index = section.get('row_index', 0)
        section_type = section.get('type', 'unknown')
        text = section.get('text', '')
        
        line = f"Row {row_index} [{section_type}]: {text}"
        lines.append(line)
    
    if not lines:
        return "No category markers detected in the data."
    
    return "\n".join(lines)