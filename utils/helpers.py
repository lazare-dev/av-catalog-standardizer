"""
AV Catalog Standardizer - Helper Utilities
----------------------------------------
Miscellaneous helper functions.
"""

import os
import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

def create_response(success: bool, message: str, data: Optional[Dict] = None) -> Dict:
    """
    Create a standardized API response.
    
    Args:
        success: Whether the operation was successful
        message: Response message
        data: Optional data to include
        
    Returns:
        Standardized response dictionary
    """
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
        
    return response

def create_cache_key(content: str) -> str:
    """
    Create a cache key from content.
    
    Args:
        content: Content to create a cache key for
        
    Returns:
        Cache key string
    """
    # Create a hash of the content
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    return content_hash

def save_debug_info(data: Any, prefix: str = 'debug', ext: str = 'json') -> str:
    """
    Save debug information to a file.
    
    Args:
        data: Data to save
        prefix: File name prefix
        ext: File extension
        
    Returns:
        Path to saved file
    """
    # Create a unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{prefix}_{timestamp}.{ext}"
    
    # Create debug directory if it doesn't exist
    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug')
    os.makedirs(debug_dir, exist_ok=True)
    
    filepath = os.path.join(debug_dir, filename)
    
    # Save the data
    try:
        if ext == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(data))
                
        logger.debug(f"Saved debug info to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving debug info: {str(e)}")
        return ""

def get_file_extension(filename: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (lowercase, without the dot)
    """
    return os.path.splitext(filename)[1].lower().replace('.', '')

def format_timestamp(timestamp: float) -> str:
    """
    Format a timestamp as a human-readable string.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted timestamp string
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        add_ellipsis: Whether to add an ellipsis
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
        
    truncated = text[:max_length]
    
    if add_ellipsis:
        truncated += '...'
        
    return truncated

def clean_filename(filename: str) -> str:
    """
    Clean a filename to ensure it's valid.
    
    Args:
        filename: Filename to clean
        
    Returns:
        Cleaned filename
    """
    # Replace invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
        
    # Ensure filename isn't too long
    if len(filename) > 255:
        extension = get_file_extension(filename)
        base_name = os.path.splitext(filename)[0]
        
        # Truncate base name to fit within limit
        max_base_length = 255 - len(extension) - 1  # -1 for the dot
        truncated_base = base_name[:max_base_length]
        
        filename = f"{truncated_base}.{extension}"
        
    return filename

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours"

def merge_dicts(dict1: Dict, dict2: Dict, recursive: bool = True) -> Dict:
    """
    Merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        recursive: Whether to merge recursively
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict) and recursive:
            result[key] = merge_dicts(result[key], value, recursive)
        else:
            result[key] = value
            
    return result

def safe_get(data: Dict, key_path: str, default: Any = None) -> Any:
    """
    Safely get a value from a nested dictionary.
    
    Args:
        data: Dictionary to get value from
        key_path: Path to the key (dot-separated)
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    if not data:
        return default
        
    keys = key_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
            
    return current

def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if valid URL, False otherwise
    """
    import re
    
    # Simple URL validation regex
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ipv4
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    return bool(url_pattern.match(url))