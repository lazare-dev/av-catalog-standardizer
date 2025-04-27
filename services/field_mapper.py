"""
AV Catalog Standardizer - Field Mapper
------------------------------------
Field mapping service.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple

from config.schema import OUTPUT_SCHEMA
from utils.response_parser import parse_llm_response

logger = logging.getLogger(__name__)

class FieldMapper:
    """Service for mapping fields based on content patterns."""
    
    def __init__(self):
        """Initialize the field mapper."""
        # Get valid standard fields from schema
        self.valid_fields = list(OUTPUT_SCHEMA.get('properties', {}).keys())
        self.required_fields = OUTPUT_SCHEMA.get('required', [])
    
    def map_fields(self, headers: List[str], sample_rows: List[List], llm_response: Dict) -> Dict:
        """
        Map fields based on LLM response.
        
        Args:
            headers: Column headers
            sample_rows: Sample data rows
            llm_response: LLM response for field mapping
            
        Returns:
            Field mapping information
        """
        logger.debug("Mapping fields based on content patterns")
        
        # Initialize field mappings
        field_mappings = {
            'field_mappings': {},
            'manufacturer_detection': None
        }
        
        # Process LLM response
        if 'field_mappings' in llm_response:
            # Extract mappings from LLM response
            raw_mappings = llm_response['field_mappings']
            
            # Validate and normalize mappings
            for original_field, mapping_info in raw_mappings.items():
                if isinstance(mapping_info, dict) and 'standard_field' in mapping_info:
                    # Get the standard field
                    standard_field = mapping_info['standard_field']
                    
                    # Validate standard field
                    if standard_field and standard_field not in self.valid_fields:
                        logger.warning(f"Invalid standard field: {standard_field}")
                        continue
                    
                    # Add to mappings
                    field_mappings['field_mappings'][original_field] = {
                        'standard_field': standard_field,
                        'confidence': mapping_info.get('confidence', 0.5),
                        'reasoning': mapping_info.get('reasoning', '')
                    }
        
        # Get manufacturer detection if available
        if 'manufacturer_detection' in llm_response:
            manufacturer_info = llm_response['manufacturer_detection']
            
            if isinstance(manufacturer_info, dict) and 'name' in manufacturer_info:
                field_mappings['manufacturer_detection'] = {
                    'name': manufacturer_info['name'],
                    'confidence': manufacturer_info.get('confidence', 0.5),
                    'reasoning': manufacturer_info.get('reasoning', '')
                }
        
        # Check if all required fields are mapped
        self._check_required_fields(field_mappings, headers, sample_rows)
        
        logger.debug(f"Field mapping complete: mapped {len(field_mappings['field_mappings'])} fields")
        
        return field_mappings
    
    def _check_required_fields(self, field_mappings: Dict, headers: List[str], sample_rows: List[List]) -> None:
        """
        Check if all required fields are mapped, attempt fallback mapping if not.
        
        Args:
            field_mappings: Field mapping information to update
            headers: Column headers
            sample_rows: Sample data rows
        """
        # Check which required fields are missing
        mapped_standard_fields = {mapping['standard_field'] for mapping in field_mappings['field_mappings'].values()}
        missing_required = [field for field in self.required_fields if field not in mapped_standard_fields]
        
        if not missing_required:
            return
            
        logger.warning(f"Missing required fields: {missing_required}")
        
        # Attempt fallback mapping based on header names
        for missing_field in missing_required:
            # Try to find a matching header (case-insensitive)
            for i, header in enumerate(headers):
                if not header:
                    continue
                    
                header_lower = str(header).lower()
                field_lower = missing_field.lower()
                
                # Check for exact or partial match
                if header_lower == field_lower or field_lower in header_lower:
                    # Add as a fallback mapping with low confidence
                    field_mappings['field_mappings'][header] = {
                        'standard_field': missing_field,
                        'confidence': 0.3,
                        'reasoning': 'Fallback mapping based on header name similarity'
                    }
                    logger.info(f"Added fallback mapping: {header} -> {missing_field}")
                    break
        
        # For required fields still missing, try to infer from content patterns
        mapped_standard_fields = {mapping['standard_field'] for mapping in field_mappings['field_mappings'].values()}
        still_missing = [field for field in self.required_fields if field not in mapped_standard_fields]
        
        # Track already mapped source fields to avoid duplicates
        mapped_source_fields = set(field_mappings['field_mappings'].keys())
        
        if still_missing:
            for missing_field in still_missing:
                # Try to infer from content patterns
                inferred_header, confidence = self._infer_field_from_content(missing_field, headers, sample_rows, mapped_source_fields)
                
                if inferred_header:
                    field_mappings['field_mappings'][inferred_header] = {
                        'standard_field': missing_field,
                        'confidence': confidence,
                        'reasoning': 'Inferred mapping based on content patterns'
                    }
                    mapped_source_fields.add(inferred_header)
                    logger.info(f"Added inferred mapping: {inferred_header} -> {missing_field}")
        
        # Add manufacturer if still missing and not detected
        if 'Manufacturer' in still_missing and not field_mappings.get('manufacturer_detection'):
            # Try to infer manufacturer from product codes or formatting
            manufacturer = self._infer_manufacturer(headers, sample_rows)
            
            if manufacturer:
                field_mappings['manufacturer_detection'] = {
                    'name': manufacturer,
                    'confidence': 0.3,
                    'reasoning': 'Inferred from product coding patterns'
                }
                logger.info(f"Added inferred manufacturer: {manufacturer}")
    
    def _infer_field_from_content(self, field_name: str, headers: List[str], sample_rows: List[List], 
                                 mapped_source_fields: Set[str]) -> Tuple[Optional[str], float]:
        """
        Infer a field mapping based on content patterns.
        
        Args:
            field_name: Name of the field to infer
            headers: Column headers
            sample_rows: Sample data rows
            mapped_source_fields: Set of already mapped source fields
            
        Returns:
            Tuple of (header name that might map to the field or None, confidence score)
        """
        patterns = {
            'SKU': [
                # SKU patterns (alphanumeric, often shorter)
                lambda val: isinstance(val, str) and 5 <= len(val) <= 20 and any(c.isdigit() for c in val) and any(c.isalpha() for c in val),
                # Product code patterns
                lambda val: isinstance(val, str) and ('code' in str(val).lower() or val.upper() == val)
            ],
            'Short_Description': [
                # Description patterns (longer text, no currency symbols)
                lambda val: isinstance(val, str) and 10 <= len(val) <= 100 and not any(c in val for c in ['£', '$', '€'])
            ],
            'Unit_Of_Measure': [
                # Unit patterns (PAIR, EA, PIECE, etc.)
                lambda val: isinstance(val, str) and val.upper() in ['PAIR', 'PR', 'EA', 'EACH', 'PIECE', 'PC', 'SET', 'UNIT']
            ],
            'Manufacturer': [
                # Manufacturer patterns (brand names)
                lambda val: isinstance(val, str) and val.lower() in ['kef', 'audio-technica', 'glensound', 'denon', 'yamaha', 'sony', 'sennheiser', 'shure', 'bowers & wilkins']
            ]
        }
        
        if field_name not in patterns:
            return None, 0.0
        
        # Check each column for matching patterns
        matches = []
        
        for i, header in enumerate(headers):
            # Skip columns already mapped
            if header in mapped_source_fields:
                continue
                
            column_values = [row[i] if i < len(row) else None for row in sample_rows]
            column_values = [val for val in column_values if val is not None and val != '']
            
            if not column_values:
                continue
            
            # Count pattern matches
            match_count = 0
            for pattern in patterns[field_name]:
                for value in column_values:
                    if pattern(value):
                        match_count += 1
            
            # Calculate match score (percentage of values matching patterns)
            match_score = match_count / len(column_values) if column_values else 0
            
            if match_score > 0.0:
                matches.append((header, match_score))
        
        # Sort matches by score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Return the best match if score is reasonable
        threshold = 0.7  # Higher threshold for more confident matches
        
        if matches and matches[0][1] >= threshold:
            return matches[0]
        elif matches and matches[0][1] >= 0.5:
            # Return with lower confidence
            return matches[0][0], 0.2  
            
        return None, 0.0
    
    def _infer_manufacturer(self, headers: List[str], sample_rows: List[List]) -> Optional[str]:
        """
        Infer manufacturer from product patterns.
        
        Args:
            headers: Column headers
            sample_rows: Sample data rows
            
        Returns:
            Inferred manufacturer name or None
        """
        # Common manufacturers with their prefix patterns
        manufacturer_patterns = {
            'KEF': ['KEF', 'MUON', 'LS', 'R'],
            'Audio-Technica': ['AT', 'ATND', 'ATH'],
            'Glensound': ['DARK', 'VITTORIA', 'DIVINE'],
            'Bowers & Wilkins': ['B&W', 'BW', '600'],
            'Denon': ['DENON', 'AVR', 'HEOS'],
            'Yamaha': ['YAM', 'YSTX'],
            'Sony': ['SONY', 'STR', 'HT'],
            'Sennheiser': ['SENN', 'HD', 'MX'],
            'Shure': ['SHURE', 'SM', 'BETA']
        }
        
        # Count prefix matches
        manufacturer_counts = {mfr: 0 for mfr in manufacturer_patterns}
        
        # Check first column or any column that might contain product codes
        for row in sample_rows:
            if not row:
                continue
                
            # Check first column (often product code)
            if row[0]:
                value = str(row[0]).upper()
                
                for mfr, prefixes in manufacturer_patterns.items():
                    if any(value.startswith(prefix) for prefix in prefixes):
                        manufacturer_counts[mfr] += 1
        
        # Return the manufacturer with the most matches (if any)
        if manufacturer_counts:
            best_manufacturer = max(manufacturer_counts.items(), key=lambda x: x[1])
            
            if best_manufacturer[1] >= 3:  # Require at least 3 matches for confidence
                return best_manufacturer[0]
        
        return None