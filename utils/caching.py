"""
AV Catalog Standardizer - Caching Utilities
-----------------------------------------
Caching mechanisms for improved performance.
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional, Callable, List, Tuple

from config.settings import CACHE_ENABLED, CACHE_DIR

logger = logging.getLogger(__name__)

class Cache:
    """Simple file-based caching system."""
    
    def __init__(self, cache_dir: str = CACHE_DIR, enabled: bool = CACHE_ENABLED):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled
        """
        self.cache_dir = cache_dir
        self.enabled = enabled
        
        # Create cache directory if it doesn't exist
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Optional[Dict]:
        """
        Get a cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
            
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
            
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # Check if cache has expired
            if 'expiry' in cached_data and cached_data['expiry'] is not None:
                if time.time() > cached_data['expiry']:
                    logger.debug(f"Cache expired for key: {key}")
                    return None
                    
            return cached_data.get('data')
            
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Set a cached value.
        
        Args:
            key: Cache key
            value: Value to cache
            expiry: Expiry time in seconds (None for no expiry)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            # Calculate expiry timestamp
            expiry_timestamp = None
            if expiry is not None:
                expiry_timestamp = time.time() + expiry
                
            # Prepare cache data
            cache_data = {
                'data': value,
                'timestamp': time.time(),
                'expiry': expiry_timestamp
            }
            
            # Write to cache file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a cached value.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return False
            
        try:
            os.remove(cache_file)
            return True
            
        except Exception as e:
            logger.warning(f"Error deleting cache for key {key}: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cached values.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
                    
            return True
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}")
            return False
    
    def create_key(self, *args: Any, **kwargs: Any) -> str:
        """
        Create a cache key from arguments.
        
        Args:
            *args: Positional arguments to include in the key
            **kwargs: Keyword arguments to include in the key
            
        Returns:
            Cache key string
        """
        # Convert args and kwargs to a string representation
        key_parts = []
        
        for arg in args:
            key_parts.append(str(arg))
            
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}={value}")
            
        key_string = "|".join(key_parts)
        
        # Create a hash of the key string
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        return key_hash

# Global cache instance
cache = Cache()

def memoize(expiry: Optional[int] = None):
    """
    Decorator to memoize a function.
    
    Args:
        expiry: Expiry time in seconds (None for no expiry)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        def wrapper(*args: Any, **kwargs: Any):
            if not cache.enabled:
                return func(*args, **kwargs)
                
            # Create cache key
            prefix = f"{func.__module__}.{func.__name__}"
            key = f"{prefix}:{cache.create_key(*args, **kwargs)}"
            
            # Check cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {prefix}")
                return cached_result
                
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result, expiry)
            
            return result
            
        return wrapper
        
    return decorator

def clear_cache_for_prefix(prefix: str) -> int:
    """
    Clear all cached values with a specific prefix.
    
    Args:
        prefix: Prefix to match
        
    Returns:
        Number of items cleared
    """
    if not cache.enabled:
        return 0
        
    count = 0
    
    try:
        for filename in os.listdir(cache.cache_dir):
            if filename.endswith('.json'):
                key = filename[:-5]  # Remove .json extension
                if key.startswith(prefix):
                    if cache.delete(key):
                        count += 1
                        
        return count
        
    except Exception as e:
        logger.warning(f"Error clearing cache for prefix {prefix}: {str(e)}")
        return count

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    if not cache.enabled:
        return {'enabled': False}
        
    try:
        total_items = 0
        total_size = 0
        expired_items = 0
        
        for filename in os.listdir(cache.cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(cache.cache_dir, filename)
                total_items += 1
                total_size += os.path.getsize(file_path)
                
                # Check if item is expired
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        
                    if 'expiry' in cached_data and cached_data['expiry'] is not None:
                        if time.time() > cached_data['expiry']:
                            expired_items += 1
                            
                except json.JSONDecodeError:
                    # Count corrupt files as expired
                    expired_items += 1
                    
        return {
            'enabled': True,
            'total_items': total_items,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'expired_items': expired_items,
            'cache_dir': cache.cache_dir
        }
        
    except Exception as e:
        logger.warning(f"Error getting cache stats: {str(e)}")
        return {'enabled': True, 'error': str(e)}