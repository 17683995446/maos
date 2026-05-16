"""
MAOS v6.0 - 缓存层实现
高性能内存缓存和LRU策略
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
from typing import Any, Optional, Dict, Callable, Generic, TypeVar
from dataclasses import dataclass
from collections import OrderedDict
from datetime import datetime, timedelta


T = TypeVar('T')


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)


class LRUCache(Generic[T]):
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """获取缓存值"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return default
            
            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return default
            
            # 更新访问时间和位置
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            # 如果已存在，更新值
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                if ttl is not None:
                    entry.ttl_seconds = ttl
                self._cache.move_to_end(key)
                return
            
            # 如果缓存已满，删除最旧的
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                ttl_seconds=ttl or self.default_ttl
            )
            self._cache[key] = entry
    
    def _evict_oldest(self):
        """删除最旧的条目"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._stats = {'hits': 0, 'misses': 0, 'evictions': 0, 'expirations': 0}
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats['expirations'] += 1
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.2%}",
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations']
            }
    
    def __len__(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            return key in self._cache


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._caches: Dict[str, LRUCache] = {}
        self._lock = threading.Lock()
        self._create_default_caches()
    
    def _create_default_caches(self):
        """创建默认缓存"""
        self.create_cache("default", max_size=1000, ttl=3600)
        self.create_cache("llm", max_size=500, ttl=1800)
        self.create_cache("tasks", max_size=2000, ttl=300)
        self.create_cache("metrics", max_size=5000, ttl=60)
    
    def create_cache(self, name: str, max_size: int = 1000, ttl: Optional[int] = None) -> LRUCache:
        """创建缓存"""
        with self._lock:
            cache = LRUCache(max_size=max_size, default_ttl=ttl)
            self._caches[name] = cache
            return cache
    
    def get_cache(self, name: str) -> Optional[LRUCache]:
        """获取缓存"""
        return self._caches.get(name)
    
    def get_or_create_cache(self, name: str, max_size: int = 1000, ttl: Optional[int] = None) -> LRUCache:
        """获取或创建缓存"""
        with self._lock:
            if name not in self._caches:
                self._caches[name] = LRUCache(max_size=max_size, default_ttl=ttl)
            return self._caches[name]
    
    def cleanup_all(self) -> int:
        """清理所有缓存的过期条目"""
        total = 0
        for cache in self._caches.values():
            total += cache.cleanup_expired()
        return total
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计"""
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }


# 全局缓存管理器
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(cache_name: str = "default", ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """缓存装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            cache = get_cache_manager().get_or_create_cache(cache_name)
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试获取缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
