"""
Infrastructure Layer - Cache Manager Module
=======================================

Provides Redis-based and in-memory caching capabilities.
Part of the persistence infrastructure layer.
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
import json
import logging

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class InMemoryCacheFallback:
    """
    In-memory cache fallback when Redis is not available.
    
    Provides basic caching functionality for development/testing.
    Not suitable for production distributed systems.
    """
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, Optional[datetime]]] = {}
        self._access_times: Dict[str, datetime] = {}
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set cache value with TTL"""
        expiry = None
        if ttl_seconds:
            expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        
        self._cache[key] = (value, expiry)
        self._access_times[key] = datetime.now()
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value if not expired"""
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        if expiry and datetime.now() > expiry:
            del self._cache[key]
            return None
        
        self._access_times[key] = datetime.now()
        return value
    
    def delete(self, key: str) -> bool:
        """Delete cache value"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def keys(self, pattern: str = '*') -> List[str]:
        """Get keys matching pattern"""
        import fnmatch
        return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
    
    def flush_pattern(self, pattern: str = '*') -> int:
        """Delete keys matching pattern"""
        keys_to_delete = self.keys(pattern)
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)


if __name__ == "__main__":
    cache = InMemoryCacheFallback()
    cache.set("test", "value", ttl_seconds=60)
    print(f"Get test: {cache.get('test')}")
    print(f"Keys: {cache.keys()}")
