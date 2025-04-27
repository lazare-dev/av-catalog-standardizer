"""
AV Catalog Standardizer - Field Mapping Prompts
---------------------------------------------
Prompts for field mapping based on content patterns.
"""

from typing import Dict, List

def get_field_mapping_prompt(headers: List[str], sample_rows: List[List]) -> str:
    """
    Create a prompt for mapping fields based on content patterns.
    
    Args:
        headers: Column headers
        sample_rows: Sample data rows
        
    Returns:
        Prompt string for field mapping
    """
    # Format the sample data as text
    sample_text = _format_sample_data(headers, sample_rows)
    
    # List of standard output fields for reference
    standard_fields = [
        "SKU", "Short_Description", "Long_Description", 
        "Model", "Category_Group", "Category", 
        "Manufacturer", "Manufacturer_SKU", "Image_URL", 
        "Document_Name", "Document_URL", "Unit_Of_Measure", 
        "Buy_Cost", "Trade_Price", "MSRP_GBP", 
        "MSRP_USD", "MSRP_EUR", "Discontinued"
    ]
    
    # Description of each standard field
    field_descriptions = {
        "SKU": "Primary product identifier, typically alphanumeric code",
        "Short_Description": "Brief product name/title",
        "Long_Description": "Detailed product description",
        "Model": "Model number or variant information (e.g., color, finish)",
        "Category_Group": "General product category group",
        "Category": "Specific product category",
        "Manufacturer": "Brand name",
        "Manufacturer_SKU": "Manufacturer's own product code",
        "Image_URL": "Link to product image",
        "Document_Name": "Associated document name",
        "Document_URL": "Link to product documentation",
        "Unit_Of_Measure": "Unit type (PAIR, EA, PIECE, etc.)",
        "Buy_Cost": "Purchasing cost",
        "Trade_Price": "Wholesale/dealer price",
        "MSRP_GBP": "Retail price in British Pounds",
        "MSRP_USD": "Retail price in US Dollars",
        "MSRP_EUR": "Retail price in Euros",
        "Discontinued": "Flag for discontinued products"
    }
    
    # Create a formatted field reference
    field_reference = "\n".join([f"- {field}: {field_descriptions[field]}" for field in standard_fields])
    
    prompt = f"""
    Examine these sample rows with headers:
    
    {sample_text}
    
    For each column, determine which standard product field it represents based on the content patterns, not just the header names.
    
    Standard Output Fields:
    {field_reference}
    
    Look for:
    - SKU patterns (typically alphanumeric codes)
    - Descriptive text (product names, descriptions)
    - Price indicators (currency symbols, decimal formats)
    - Category information
    - Measurement units
    
    Also, try to identify the manufacturer based on product naming patterns, formatting, or other clues.
    
    Return mappings with confidence scores as a JSON object with the following structure:
    {{
      "field_mappings": {{
        "<original_field1>": {{
          "standard_field": "<mapped_standard_field>",
          "confidence": 0.0-1.0,
          "reasoning": "explanation of why this mapping was chosen"
        }},
        "<original_field2>": {{
          "standard_field": "<mapped_standard_field>",
          "confidence": 0.0-1.0,
          "reasoning": "explanation of why this mapping was chosen"
        }},
        ...
      }},
      "manufacturer_detection": {{
        "name": "detected manufacturer name",
        "confidence": 0.0-1.0,
        "reasoning": "explanation of why this manufacturer was detected"
      }}
    }}
    
    If a field doesn't map to any standard field, you can set "standard_field" to null.
    """
    
    return prompt

def _format_sample_data(headers: List[str], sample_rows: List[List]) -> str:
    """
    Format sample data as a readable text block.
    
    Args:
        headers: Column headers
        sample_rows: Sample data rows
        
    Returns:
        Formatted text representation
    """
    # Start with headers
    lines = []
    
    if headers:
        header_line = " | ".join([str(h) for h in headers])
        lines.append(header_line)
        lines.append("-" * len(header_line))
    
    # Add data rows
    for i, row in enumerate(sample_rows):
        # Format each cell, handling None values
        formatted_row = [str(cell) if cell is not None else "" for cell in row]
        line = f"Row {i}: " + " | ".join(formatted_row)
        lines.append(line)
    
    return "\n".join(lines)