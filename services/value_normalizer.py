"""
AV Catalog Standardizer - Value Normalizer
----------------------------------------
Value normalization service.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal

from config.schema import VALID_UNIT_TYPES, CURRENCY_FORMATS, PRICE_PATTERNS, FIELD_TYPES
from core.llm_client import phi_client
from prompts.value_normalization import get_sample_value_normalization_prompt

logger = logging.getLogger(__name__)

class ValueNormalizer:
    """Service for normalizing values based on field types."""
    
    def __init__(self):
        """Initialize the value normalizer."""
        # Cache for normalization strategies
        self.normalization_strategies = {}
        
        # Field type information
        self.string_fields = FIELD_TYPES['string_fields']
        self.numeric_fields = FIELD_TYPES['numeric_fields']
        self.boolean_fields = FIELD_TYPES['boolean_fields']
        
        # Unit type mapping
        self.unit_mapping = VALID_UNIT_TYPES
        
        # Currency and price patterns
        self.currency_formats = CURRENCY_FORMATS
        self.price_patterns = PRICE_PATTERNS
    
    def normalize_value(self, value: Any, field_name: str) -> Any:
        """
        Normalize a value based on field type.
        
        Args:
            value: Value to normalize
            field_name: Name of the field
            
        Returns:
            Normalized value
        """
        if value is None or value == '':
            return None
            
        # Convert to string for consistent handling
        str_value = str(value)
        
        # Handle string fields
        if field_name in self.string_fields:
            return self._normalize_string(str_value, field_name)
            
        # Handle numeric fields
        elif field_name in self.numeric_fields:
            return self._normalize_numeric(str_value, field_name)
            
        # Handle boolean fields
        elif field_name in self.boolean_fields:
            return self._normalize_boolean(str_value)
            
        # Default: return as string
        return str_value
    
    def _normalize_string(self, value: str, field_name: str) -> str:
        """
        Normalize a string value based on field type.
        
        Args:
            value: String value to normalize
            field_name: Name of the field
            
        Returns:
            Normalized string value
        """
        # Handle special field types
        if field_name == 'Unit_Of_Measure':
            return self._normalize_unit(value)
            
        # Basic string normalization
        normalized = value.strip()
        
        # Remove any special encoding artifacts
        normalized = re.sub(r'\u00A0', ' ', normalized)  # Replace non-breaking spaces
        
        # Truncate very long values for description fields
        if field_name == 'Long_Description' and len(normalized) > 1000:
            normalized = normalized[:997] + '...'
            
        # For category fields, ensure proper capitalization
        if field_name in ['Category', 'Category_Group']:
            # Title case, but preserve common abbreviations
            words = normalized.split()
            normalized_words = []
            
            for word in words:
                # Preserve abbreviations and special terms
                if word.upper() in ['AV', 'TV', 'HDMI', 'USB', 'PC', 'IP', 'HD', '4K']:
                    normalized_words.append(word.upper())
                else:
                    normalized_words.append(word.capitalize())
                    
            normalized = ' '.join(normalized_words)
        
        return normalized
    
    def _normalize_unit(self, value: str) -> str:
        """
        Normalize a unit value to a standard format.
        
        Args:
            value: Unit value to normalize
            
        Returns:
            Normalized unit value
        """
        upper_value = value.upper().strip()
        
        # Check for direct matches
        for standard_unit, variants in self.unit_mapping.items():
            if upper_value in variants or upper_value == standard_unit:
                return standard_unit
        
        # Check for partial matches
        for standard_unit, variants in self.unit_mapping.items():
            for variant in variants:
                if variant in upper_value or upper_value in variant:
                    return standard_unit
        
        # Default to 'EA' for unknown values
        logger.warning(f"Unknown unit value: {value}, defaulting to 'EA'")
        return 'EA'
    
    def _normalize_numeric(self, value: str, field_name: str) -> Optional[float]:
        """
        Normalize a numeric value.
        
        Args:
            value: Numeric value to normalize
            field_name: Name of the field
            
        Returns:
            Normalized numeric value
        """
        # For price fields, special handling
        if field_name.startswith('MSRP_') or field_name in ['Buy_Cost', 'Trade_Price']:
            return self._normalize_price(value, field_name)
            
        # General numeric normalization
        try:
            # Remove any currency symbols and non-numeric characters
            cleaned = re.sub(r'[^\d\.\,\-]', '', value)
            
            # Handle European number format (comma as decimal separator)
            if ',' in cleaned and '.' in cleaned:
                # If both comma and period are present, assume comma is thousands separator
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # If only comma is present, assume it's decimal separator
                cleaned = cleaned.replace(',', '.')
            
            # Convert to float
            return float(cleaned)
            
        except (ValueError, TypeError):
            logger.warning(f"Could not normalize numeric value: {value}")
            return None
    
    def _normalize_price(self, value: str, field_name: str) -> Optional[float]:
        """
        Normalize a price value.
        
        Args:
            value: Price value to normalize
            field_name: Name of the field
            
        Returns:
            Normalized price value
        """
        # Determine expected currency
        expected_currency = None
        
        if field_name == 'MSRP_GBP':
            expected_currency = 'GBP'
        elif field_name == 'MSRP_USD':
            expected_currency = 'USD'
        elif field_name == 'MSRP_EUR':
            expected_currency = 'EUR'
        
        # Try to extract currency and numeric value
        currency_match = None
        
        for currency, symbols in self.currency_formats.items():
            for symbol in symbols:
                if symbol in value:
                    currency_match = currency
                    break
                    
            if currency_match:
                break
        
        # If we found a currency and it doesn't match the expected one, log warning
        if currency_match and expected_currency and currency_match != expected_currency:
            logger.warning(f"Currency mismatch: found {currency_match} in {field_name} field")
            
        # Determine decimal and thousands separators based on currency or patterns
        decimal_sep = '.'
        thousands_sep = ','
        
        if currency_match == 'EUR':
            # European format (likely)
            decimal_sep = ','
            thousands_sep = '.'
        
        # Clean and normalize
        cleaned = value
        
        # Remove currency symbols and other non-numeric characters
        for symbol_list in self.currency_formats.values():
            for symbol in symbol_list:
                cleaned = cleaned.replace(symbol, '')
        
        # Remove remaining non-numeric characters except decimal and thousands separators
        cleaned = re.sub(r'[^\d\.\,\-]', '', cleaned.strip())
        
        # Handle different number formats
        if ',' in cleaned and '.' in cleaned:
            # Both separators present, determine which is which based on position
            comma_pos = cleaned.rfind(',')
            dot_pos = cleaned.rfind('.')
            
            if comma_pos > dot_pos:
                # Comma is decimal separator (European format)
                cleaned = cleaned.replace('.', '')  # Remove thousands separators
                cleaned = cleaned.replace(',', '.')  # Convert decimal separator to standard
            else:
                # Dot is decimal separator (UK/US format)
                cleaned = cleaned.replace(',', '')  # Remove thousands separators
        elif ',' in cleaned:
            # Only comma present, determine if it's thousands or decimal separator
            # If there are exactly 2 digits after the last comma, it's likely decimal
            comma_pos = cleaned.rfind(',')
            if len(cleaned) - comma_pos == 3:
                # Likely a decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Likely a thousands separator
                cleaned = cleaned.replace(',', '')
        
        try:
            # Convert to float
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"Could not normalize price value: {value}")
            return None
    
    def _normalize_boolean(self, value: str) -> Optional[bool]:
        """
        Normalize a boolean value.
        
        Args:
            value: Boolean value to normalize
            
        Returns:
            Normalized boolean value
        """
        value_lower = value.lower().strip()
        
        # True values
        if value_lower in ['true', 'yes', 'y', '1', 't', 'discontinued']:
            return True
            
        # False values
        if value_lower in ['false', 'no', 'n', '0', 'f', 'active']:
            return False
            
        # If not clearly boolean, return None
        return None
    
    def learn_normalization_strategy(self, field_name: str, sample_values: List[Any]) -> Dict:
        """
        Use LLM to learn a normalization strategy for a field.
        
        Args:
            field_name: Name of the field
            sample_values: Sample values for this field
            
        Returns:
            Normalization strategy
        """
        # Check if we already have a strategy for this field
        if field_name in self.normalization_strategies:
            return self.normalization_strategies[field_name]
            
        # Create a prompt for value normalization
        prompt = get_sample_value_normalization_prompt(field_name, sample_values)
        
        # Get LLM response
        llm_response = phi_client.generate_json(prompt)
        
        # Extract and store the strategy
        strategy = {
            'field': field_name,
            'value_type': llm_response.get('value_type', 'text'),
            'patterns': llm_response.get('patterns', []),
            'default_strategy': llm_response.get('default_strategy', 'pass-through')
        }
        
        # Cache the strategy
        self.normalization_strategies[field_name] = strategy
        
        return strategy
    
    def apply_learned_strategy(self, value: Any, field_name: str) -> Any:
        """
        Apply a learned normalization strategy to a value.
        
        Args:
            value: Value to normalize
            field_name: Name of the field
            
        Returns:
            Normalized value
        """
        # If we don't have a strategy for this field, use default normalization
        if field_name not in self.normalization_strategies:
            return self.normalize_value(value, field_name)
            
        # Get the strategy
        strategy = self.normalization_strategies[field_name]
        
        # Convert value to string for pattern matching
        str_value = str(value) if value is not None else ''
        
        # Try to match each pattern
        for pattern_info in strategy.get('patterns', []):
            pattern = pattern_info.get('pattern', '')
            example = pattern_info.get('example', '')
            normalization = pattern_info.get('normalization', '')
            
            # Simple pattern matching (could be improved with regex)
            if pattern in str_value or example in str_value:
                # Apply normalization rule (placeholder for more complex rules)
                if normalization == 'convert_to_float':
                    return self._normalize_numeric(str_value, field_name)
                elif normalization == 'convert_to_boolean':
                    return self._normalize_boolean(str_value)
                elif normalization.startswith('standardize_unit:'):
                    standard_unit = normalization.split(':')[1]
                    return standard_unit
                else:
                    return str_value
        
        # If no pattern matched, apply default strategy
        default_strategy = strategy.get('default_strategy', 'pass-through')
        
        if default_strategy == 'pass-through':
            return str_value
        elif default_strategy == 'convert_to_float':
            return self._normalize_numeric(str_value, field_name)
        elif default_strategy == 'convert_to_boolean':
            return self._normalize_boolean(str_value)
        elif default_strategy == 'convert_to_standard_unit':
            return self._normalize_unit(str_value)
        else:
            return str_value