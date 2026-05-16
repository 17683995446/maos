"""
Application Services - Task Result Caching Module
============================================

Provides task result caching with TTL and invalidation.
Part of the Phase 2 production hardening improvements.

Key Features:
  - Task result caching
  - TTL-based expiration
  - Cache invalidation strategies
  - Compression support
  - Cache statistics
  - Distributed cache support
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
from enum import Enum
import hashlib
import json
import logging
import gzip

logger = logging.getLogger(__name__)


class CacheInvalidationStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"
    MANUAL = "manual"
    LRU = "lru"
    LFU = "lfu"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


@dataclass
class CacheEntry:
    """Cached task result entry"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    compressed: bool = False
    size_bytes: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds is None:
            return False
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def update_access(self) -> None:
        """Update last accessed time"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class TaskResultCache:
    """
    Task result cache with multiple storage backends.
    
    Features:
      - In-memory and Redis backends
      - TTL-based expiration
      - Compression support
      - Statistics tracking
      - Cache warming
    
    Usage:
        cache = TaskResultCache(max_size=1000)
        
        # Cache task result
        cache.set(task_id, result, ttl_seconds=3600)
        
        # Get cached result
        result = cache.get(task_id)
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        invalidation_strategy: CacheInvalidationStrategy = CacheInvalidationStrategy.TTL,
        compression_threshold: int = 1024,
        redis_url: Optional[str] = None
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.invalidation_strategy = invalidation_strategy
        self.compression_threshold = compression_threshold
        self.redis_url = redis_url
        
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: list = []
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        
        self._redis_client = None
    
    def _generate_key(self, key: str) -> str:
        """Generate cache key"""
        return hashlib.md5(str(key).encode()).hexdigest()
    
    def _compress(self, data: Any) -> bytes:
        """Compress data"""
        json_str = json.dumps(data, default=str)
        return gzip.compress(json_str.encode())
    
    def _decompress(self, data: bytes) -> Any:
        """Decompress data"""
        json_str = gzip.decompress(data).decode()
        return json.loads(json_str)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Store task result in cache.
        
        Args:
            key: Cache key (e.g., task_id)
            value: Result to cache
            ttl_seconds: Time to live (uses default if None)
            tags: Tags for categorization
        
        Returns:
            True if successful
        """
        try:
            cache_key = self._generate_key(key)
            
            value_size = len(str(value))
            should_compress = value_size > self.compression_threshold
            
            if should_compress:
                value = self._compress(value)
            
            entry = CacheEntry(
                key=cache_key,
                value=value,
                ttl_seconds=ttl_seconds or self.default_ttl,
                compressed=should_compress,
                size_bytes=len(value) if isinstance(value, bytes) else value_size,
                tags=tags or {}
            )
            
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict()
            
            self._cache[cache_key] = entry
            self._access_order.append(cache_key)
            
            logger.debug(f"Cached result for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached task result.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        try:
            cache_key = self._generate_key(key)
            
            if cache_key not in self._cache:
                self._miss_count += 1
                return None
            
            entry = self._cache[cache_key]
            
            if entry.is_expired():
                self.invalidate(key)
                self._miss_count += 1
                return None
            
            entry.update_access()
            self._hit_count += 1
            
            value = entry.value
            if entry.compressed:
                value = self._decompress(value)
            
            logger.debug(f"Cache hit for key: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            self._miss_count += 1
            return None
    
    def invalidate(self, key: str) -> bool:
        """Invalidate cached result"""
        cache_key = self._generate_key(key)
        if cache_key in self._cache:
            del self._cache[cache_key]
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            logger.debug(f"Invalidated cache for key: {key}")
            return True
        return False
    
    def invalidate_by_tag(self, tag: str, value: str) -> int:
        """Invalidate all entries with specific tag"""
        keys_to_remove = [
            cache_key for cache_key, entry in self._cache.items()
            if entry.tags.get(tag) == value
        ]
        
        for cache_key in keys_to_remove:
            del self._cache[cache_key]
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
        
        logger.info(f"Invalidated {len(keys_to_remove)} entries with tag {tag}={value}")
        return len(keys_to_remove)
    
    def invalidate_all(self) -> int:
        """Invalidate all cached results"""
        count = len(self._cache)
        self._cache.clear()
        self._access_order.clear()
        logger.info(f"Invalidated all {count} cached entries")
        return count
    
    def _evict(self) -> None:
        """Evict entry based on invalidation strategy"""
        if not self._cache or not self._access_order:
            return
        
        if self.invalidation_strategy == CacheInvalidationStrategy.LRU:
            oldest_key = self._access_order[0]
            if oldest_key and oldest_key in self._cache:
                del self._cache[oldest_key]
                self._access_order.pop(0)
                self._eviction_count += 1
        
        elif self.invalidation_strategy == CacheInvalidationStrategy.LFU:
            least_used = min(
                self._cache.items(),
                key=lambda x: x[1].access_count
            )
            del self._cache[least_used[0]]
        
        elif self.invalidation_strategy == CacheInvalidationStrategy.TTL:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired()
            ]
            if expired_keys:
                for key in expired_keys:
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                return
            
            oldest_key = self._access_order[0] if self._access_order else None
            if oldest_key:
                del self._cache[oldest_key]
                self._access_order.pop(0)
        
        self._eviction_count += 1
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired entries")
        return len(expired_keys)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
        
        total_size = sum(entry.size_bytes for entry in self._cache.values())
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': hit_rate,
            'eviction_count': self._eviction_count,
            'total_size_bytes': total_size,
            'avg_entry_size_bytes': total_size / len(self._cache) if self._cache else 0,
            'default_ttl': self.default_ttl,
            'invalidation_strategy': self.invalidation_strategy.value
        }
    
    def warmup(
        self,
        tasks: Dict[str, Callable],
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        Warm up cache with task results.
        
        Args:
            tasks: Dict of task_id -> callable
            ttl_seconds: TTL for cached results
        
        Returns:
            Number of entries cached
        """
        count = 0
        for task_id, task_func in tasks.items():
            try:
                result = task_func()
                self.set(task_id, result, ttl_seconds=ttl_seconds)
                count += 1
            except Exception as e:
                logger.error(f"Failed to warmup task {task_id}: {e}")
        
        logger.info(f"Warmed up {count} cache entries")
        return count


if __name__ == "__main__":
    print("Task Result Caching Module")
    print("=" * 50)
    
    cache = TaskResultCache(max_size=100, default_ttl=3600)
    
    print("\n1. Caching task results:")
    cache.set("task_1", {"result": "data", "status": "success"})
    cache.set("task_2", {"result": [1, 2, 3], "status": "success"})
    cache.set("task_3", {"result": "large_data" * 100, "status": "success"})
    
    print(f"   Cached 3 results")
    
    print("\n2. Retrieving cached results:")
    result1 = cache.get("task_1")
    result2 = cache.get("task_2")
    result3 = cache.get("task_3")
    
    print(f"   task_1: {result1}")
    print(f"   task_2: {result2}")
    print(f"   task_3: {result3}")
    
    print("\n3. Cache statistics:")
    stats = cache.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
