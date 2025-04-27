"""
AV Catalog Standardizer - Validator
---------------------------------
Output validation service.
"""

import logging
from typing import Dict, List, Any
import jsonschema

from config.schema import OUTPUT_SCHEMA

logger = logging.getLogger(__name__)

def validate_output(transformed_data: List[Dict]) -> Dict:
    """
    Validate transformed data against schema.
    
    Args:
        transformed_data: List of transformed data dictionaries
        
    Returns:
        Validation results
    """
    logger.debug("Validating output data")
    
    validation_results = {
        'valid_count': 0,
        'invalid_count': 0,
        'errors': [],
        'warnings': []
    }
    
    # Get required fields from schema
    required_fields = OUTPUT_SCHEMA.get('required', [])
    
    # Loop through items and validate
    for i, item in enumerate(transformed_data):
        # Validate required fields
        missing_required = [field for field in required_fields if field not in item or not item[field]]
        
        if missing_required:
            validation_results['invalid_count'] += 1
            validation_results['errors'].append({
                'index': i,
                'type': 'missing_required',
                'message': f"Missing required fields: {', '.join(missing_required)}",
                'severity': 'critical'
            })
            continue
        
        # Validate data types
        try:
            jsonschema.validate(instance=item, schema=OUTPUT_SCHEMA)
            validation_results['valid_count'] += 1
        except jsonschema.exceptions.ValidationError as e:
            validation_results['invalid_count'] += 1
            validation_results['errors'].append({
                'index': i,
                'type': 'schema_error',
                'message': str(e),
                'severity': 'critical'
            })
        
        # Additional custom validations
        custom_validations(item, i, validation_results)
    
    logger.debug(f"Validation complete: {validation_results['valid_count']} valid, "
                f"{validation_results['invalid_count']} invalid")
    
    return validation_results

def custom_validations(item: Dict, index: int, validation_results: Dict) -> None:
    """
    Perform custom validations on an item.
    
    Args:
        item: Data item to validate
        index: Index of the item
        validation_results: Validation results to update
    """
    # Check for nonsensical price values
    price_fields = ['MSRP_GBP', 'MSRP_USD', 'MSRP_EUR', 'Buy_Cost', 'Trade_Price']
    
    for field in price_fields:
        if field in item and item[field] is not None:
            # Negative prices
            if item[field] < 0:
                validation_results['warnings'].append({
                    'index': index,
                    'type': 'negative_price',
                    'message': f"Negative price in {field}: {item[field]}",
                    'severity': 'warning'
                })
            
            # Extremely high prices (might indicate parsing error)
            elif item[field] > 1000000:  # Arbitrary threshold
                validation_results['warnings'].append({
                    'index': index,
                    'type': 'extreme_price',
                    'message': f"Extremely high price in {field}: {item[field]}",
                    'severity': 'warning'
                })
    
    # Check for inconsistent category hierarchy
    if 'Category' in item and 'Category_Group' in item:
        category = item['Category']
        category_group = item['Category_Group']
        
        # If we have a category but no category group
        if category and not category_group:
            validation_results['warnings'].append({
                'index': index,
                'type': 'missing_category_group',
                'message': f"Category '{category}' has no Category_Group",
                'severity': 'warning'
            })
    
    # Check for unusual SKU formats
    if 'SKU' in item:
        sku = item['SKU']
        
        # SKU is too short
        if len(sku) < 3:
            validation_results['warnings'].append({
                'index': index,
                'type': 'short_sku',
                'message': f"SKU is unusually short: '{sku}'",
                'severity': 'warning'
            })
        
        # SKU has no alphanumeric characters
        if not any(c.isalnum() for c in sku):
            validation_results['warnings'].append({
                'index': index,
                'type': 'non_alphanumeric_sku',
                'message': f"SKU has no alphanumeric characters: '{sku}'",
                'severity': 'warning'
            })

def get_validation_summary(validation_results: Dict) -> str:
    """
    Get a human-readable summary of validation results.
    
    Args:
        validation_results: Validation results
        
    Returns:
        Summary string
    """
    total = validation_results['valid_count'] + validation_results['invalid_count']
    
    summary = f"Validation summary:\n"
    summary += f"- Total items: {total}\n"
    summary += f"- Valid items: {validation_results['valid_count']} ({validation_results['valid_count'] / total * 100:.1f}%)\n"
    summary += f"- Invalid items: {validation_results['invalid_count']} ({validation_results['invalid_count'] / total * 100:.1f}%)\n"
    
    if validation_results['errors']:
        summary += f"\nErrors:\n"
        error_types = {}
        
        for error in validation_results['errors']:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        for error_type, count in error_types.items():
            summary += f"- {error_type}: {count}\n"
    
    if validation_results['warnings']:
        summary += f"\nWarnings:\n"
        warning_types = {}
        
        for warning in validation_results['warnings']:
            warning_type = warning['type']
            if warning_type not in warning_types:
                warning_types[warning_type] = 0
            warning_types[warning_type] += 1
        
        for warning_type, count in warning_types.items():
            summary += f"- {warning_type}: {count}\n"
    
    return summary