"""
AV Catalog Standardizer - Schema
-------------------------------
Standardized output schema definition.
"""

# Schema for standardized output format
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "SKU": {
            "type": "string",
            "description": "Primary product identifier"
        },
        "Short_Description": {
            "type": "string",
            "description": "Brief product name/title"
        },
        "Long_Description": {
            "type": ["string", "null"],
            "description": "Detailed product description"
        },
        "Model": {
            "type": ["string", "null"],
            "description": "Model number or variant information"
        },
        "Category_Group": {
            "type": ["string", "null"],
            "description": "General product category group"
        },
        "Category": {
            "type": ["string", "null"],
            "description": "Specific product category"
        },
        "Manufacturer": {
            "type": "string",
            "description": "Brand name"
        },
        "Manufacturer_SKU": {
            "type": ["string", "null"],
            "description": "Manufacturer's own product code"
        },
        "Image_URL": {
            "type": ["string", "null"],
            "description": "Link to product image"
        },
        "Document_Name": {
            "type": ["string", "null"],
            "description": "Associated document name"
        },
        "Document_URL": {
            "type": ["string", "null"],
            "description": "Link to product documentation"
        },
        "Unit_Of_Measure": {
            "type": "string",
            "description": "Unit type (PAIR, EA, PIECE)",
            "enum": ["PAIR", "EA", "EACH", "PIECE", "SET", "KIT", "PACK", "BOX", "UNIT"]
        },
        "Buy_Cost": {
            "type": ["number", "null"],
            "description": "Purchasing cost"
        },
        "Trade_Price": {
            "type": ["number", "null"],
            "description": "Wholesale/dealer price"
        },
        "MSRP_GBP": {
            "type": ["number", "null"],
            "description": "Retail price in British Pounds"
        },
        "MSRP_USD": {
            "type": ["number", "null"],
            "description": "Retail price in US Dollars"
        },
        "MSRP_EUR": {
            "type": ["number", "null"],
            "description": "Retail price in Euros"
        },
        "Discontinued": {
            "type": ["boolean", "null"],
            "description": "Flag for discontinued products"
        }
    },
    "required": ["SKU", "Short_Description", "Manufacturer", "Unit_Of_Measure"]
}

# Enumeration of valid unit types for normalization
VALID_UNIT_TYPES = {
    "PAIR": ["PAIR", "PR", "PAIRS", "PRS"],
    "EA": ["EA", "EACH", "UNIT", "SINGLE", "1PC"],
    "PIECE": ["PIECE", "PC", "PCS", "PIECES"],
    "SET": ["SET", "SETS", "KIT", "KITS"],
    "PACK": ["PACK", "PACKAGE", "PKG", "BOX"]
}

# Currency symbols and formats for normalization
CURRENCY_FORMATS = {
    "GBP": ["£", "GBP", "£GBP"],
    "USD": ["$", "USD", "$USD"],
    "EUR": ["€", "EUR", "€EUR"]
}

# Common price format patterns for normalization
PRICE_PATTERNS = {
    "european": {
        "decimal_separator": ",",
        "thousands_separator": "."
    },
    "uk_us": {
        "decimal_separator": ".",
        "thousands_separator": ","
    }
}

# Definition of field types for validation
FIELD_TYPES = {
    "string_fields": [
        "SKU", "Short_Description", "Long_Description", 
        "Model", "Category_Group", "Category", 
        "Manufacturer", "Manufacturer_SKU", "Image_URL", 
        "Document_Name", "Document_URL", "Unit_Of_Measure"
    ],
    "numeric_fields": [
        "Buy_Cost", "Trade_Price", "MSRP_GBP", 
        "MSRP_USD", "MSRP_EUR"
    ],
    "boolean_fields": [
        "Discontinued"
    ]
}