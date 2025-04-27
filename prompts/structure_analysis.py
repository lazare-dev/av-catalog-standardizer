"""
AV Catalog Standardizer - Structure Analysis Prompts
--------------------------------------------------
Prompts for document structure analysis.
"""

from typing import Dict, List

def get_structure_analysis_prompt(parsed_data: Dict) -> str:
    """
    Create a prompt for analyzing the structure of a catalog document.
    
    Args:
        parsed_data: Dictionary containing parsed file data
        
    Returns:
        Prompt string for structure analysis
    """
    # Extract relevant data
    file_format = parsed_data.get('structure', {}).get('format', 'unknown')
    headers = parsed_data.get('headers', [])
    raw_data = parsed_data.get('raw_data', [])
    
    # Display a sample of the data (first 20 rows or all if less)
    sample_size = min(20, len(raw_data))
    sample_data = raw_data[:sample_size]
    
    # Format the sample data as text
    sample_text = _format_sample_data(headers, sample_data)
    
    prompt = f"""
    Analyze this product catalog data:
    
    File Format: {file_format}
    
    Data Sample:
    {sample_text}
    
    Identify:
    1. Which rows contain headers or titles
    2. Which rows represent category markers or section divisions
    3. Where the actual product data begins (row index)
    4. Any special formatting patterns or markers that indicate structure
    5. For each column, do a preliminary assessment of what type of data it might contain
    
    Pay special attention to:
    - Rows that might indicate category changes
    - Special markers like "#VALUE!" in KEF catalogs
    - Section headers like "Brand: Audio-Technica" or "AT - Network Series"
    - Headers like "DANTE/RAVENNA/MILAN NETWORK AUDIO UNITS" in Glensound catalogs
    
    Explain your reasoning for each identification.
    
    Return your analysis as a JSON object with the following structure:
    {{
      "headers": [list of identified headers],
      "data_start_row": index where product data begins,
      "non_data_rows": [indices of rows that are not product data],
      "structure_markers": [
        {{
          "row_index": index,
          "text": "marker text",
          "type": "category_header|section_divider|special_marker",
          "significance": "explanation"
        }}
      ],
      "column_assessments": [
        {{
          "column_index": index,
          "header": "header name",
          "likely_content": "SKU|description|price|unit|etc",
          "confidence": 0.0-1.0,
          "reasoning": "explanation"
        }}
      ]
    }}
    """
    
    return prompt

def _format_sample_data(headers: List[str], sample_data: List[List]) -> str:
    """
    Format sample data as a readable text block.
    
    Args:
        headers: Column headers
        sample_data: Sample data rows
        
    Returns:
        Formatted text representation
    """
    # Start with headers if available
    lines = []
    
    if headers:
        header_line = " | ".join([str(h) for h in headers])
        lines.append(header_line)
        lines.append("-" * len(header_line))
    
    # Add data rows
    for i, row in enumerate(sample_data):
        # Format each cell, handling None values
        formatted_row = [str(cell) if cell is not None else "" for cell in row]
        line = f"Row {i}: " + " | ".join(formatted_row)
        lines.append(line)
    
    return "\n".join(lines)