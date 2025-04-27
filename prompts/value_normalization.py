"""
AV Catalog Standardizer - Value Normalization Prompts
--------------------------------------------------
Prompts for value normalization guidance.
"""

from typing import Dict, List, Any

def get_value_normalization_prompt(sample_values: Dict[str, List[Any]]) -> str:
    """
    Create a prompt for normalizing values.
    
    Args:
        sample_values: Dictionary mapping field types to sample values
        
    Returns:
        Prompt string for value normalization
    """
    # Format sample values as text
    values_text = _format_sample_values(sample_values)
    
    prompt = f"""
    Transform these sample values to standardized formats:
    
    {values_text}
    
    For each type of value, identify:
    1. The patterns you recognize
    2. How to normalize similar values to a standardized format
    3. Any special cases or exceptions to handle
    
    Pay particular attention to:
    
    - Price formats: Different currency symbols, thousand separators, decimal separators
      - European format uses comma as decimal separator (e.g., "220,000 €")
      - UK/US format uses period as decimal separator (e.g., "£2,399.00")
      
    - Unit formats: Different ways of expressing the same unit
      - "PAIR", "PR", "PAIRS", etc. should normalize to "PAIR"
      - "EA", "EACH", "UNIT", "SINGLE", etc. should normalize to "EA"
      - "PIECE", "PC", "PCS", etc. should normalize to "PIECE"
      
    - Category formats: Standardizing category naming
      - Remove redundant prefixes/suffixes
      - Proper capitalization
      - Handling abbreviations
    
    Return normalization rules as a JSON object with the following structure:
    {{
      "price_normalization": {{
        "detected_patterns": [
          {{
            "pattern": "pattern description",
            "example": "example value",
            "normalization_rule": "how to normalize this pattern"
          }},
          ...
        ],
        "currency_symbols": {{
          "EUR": ["€", "EUR", ...],
          "GBP": ["£", "GBP", ...],
          "USD": ["$", "USD", ...]
        }},
        "decimal_separators": {{
          "european": ",",
          "uk_us": "."
        }},
        "thousands_separators": {{
          "european": ".",
          "uk_us": ","
        }}
      }},
      "unit_normalization": {{
        "mapping": {{
          "PAIR": ["PAIR", "PR", "PAIRS", ...],
          "EA": ["EA", "EACH", "UNIT", ...],
          "PIECE": ["PIECE", "PC", "PCS", ...],
          ...
        }}
      }},
      "category_normalization": {{
        "rules": [
          {{
            "pattern": "pattern to match",
            "replacement": "normalized form",
            "description": "explanation of the rule"
          }},
          ...
        ]
      }}
    }}
    """
    
    return prompt

def _format_sample_values(sample_values: Dict[str, List[Any]]) -> str:
    """
    Format sample values as a readable text block.
    
    Args:
        sample_values: Dictionary mapping field types to sample values
        
    Returns:
        Formatted text representation
    """
    lines = []
    
    for field_type, values in sample_values.items():
        lines.append(f"{field_type}:")
        for value in values:
            lines.append(f"  - {value}")
        lines.append("")
    
    return "\n".join(lines)

def get_sample_value_normalization_prompt(field_name: str, sample_values: List[Any]) -> str:
    """
    Create a prompt for normalizing a specific field's values.
    
    Args:
        field_name: Name of the field to normalize
        sample_values: Sample values for this field
        
    Returns:
        Prompt string for value normalization
    """
    # Format sample values as text
    values_text = "\n".join([f"- {value}" for value in sample_values])
    
    prompt = f"""
    Analyze these sample values for the '{field_name}' field:
    
    {values_text}
    
    1. Identify common patterns in these values
    2. Determine how to normalize them to a consistent format
    3. Handle any special cases or exceptions
    
    Return a normalization strategy as a JSON object with the following structure:
    {{
      "field": "{field_name}",
      "value_type": "price|unit|category|text|etc",
      "patterns": [
        {{
          "pattern": "pattern description",
          "example": "example matching this pattern",
          "normalization": "how to normalize this pattern"
        }},
        ...
      ],
      "default_strategy": "default normalization approach if no patterns match"
    }}
    """
    
    return prompt