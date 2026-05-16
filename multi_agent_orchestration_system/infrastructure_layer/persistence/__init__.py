"""
Infrastructure Layer - Persistence Module
======================================

Provides data persistence and caching capabilities using industry-standard tools.

Key Components:
  - CacheManager: Redis-based caching with TTL support
  - DatabaseModels: SQLAlchemy ORM models for PostgreSQL
  - RepositoryPattern: Data access abstraction layer
  - MigrationManager: Alembic-based database migrations

Architecture:
  - Redis: Distributed caching, session storage, pub/sub
  - PostgreSQL: Persistent relational data storage
  - SQLAlchemy: ORM for database operations
  - Alembic: Database schema migrations

Supported Databases:
  - PostgreSQL (primary)
  - SQLite (development/testing)
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List, Type, TypeVar, Generic
from abc import ABC, abstractmethod
import json
import logging

try:
    import redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseModel:
    """Base model with common fields for all database models"""
    if SQLALCHEMY_AVAILABLE:
        id = Column(Integer, primary_key=True, index=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RedisCacheManager:
    """
    Redis-based distributed cache manager.
    
    Features:
      - Key-value caching with TTL
      - JSON serialization support
      - Automatic key prefixing
      - Cache invalidation patterns
      - Connection pooling
    
    Usage:
      cache = RedisCacheManager(redis_url='redis://localhost:6379/0')
      cache.set('user:123', user_data, ttl_seconds=3600)
      data = cache.get('user:123')
    """
    
    _instances: Dict[str, 'RedisCacheManager'] = {}
    
    def __init__(
        self,
        redis_url: str = 'redis://localhost:6379/0',
        key_prefix: str = 'maos:cache:',
        default_ttl: int = 3600,
        max_connections: int = 50
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._client = None
        self._async_client = None
        self._connection_pool = None
    
    @classmethod
    def get_instance(cls, name: str = 'default', **kwargs) -> 'RedisCacheManager':
        """Get or create singleton cache manager instance"""
        if name not in cls._instances:
            cls._instances[name] = cls(**kwargs)
        return cls._instances[name]
    
    def _get_client(self):
        """Get or create Redis client (lazy initialization)"""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install with: pip install redis")
        
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Apply key prefix to cache key"""
        return f"{self.key_prefix}{key}"
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        serialize_json: bool = True
    ) -> bool:
        """
        Set a cache value with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string)
            ttl_seconds: Time to live in seconds (uses default if None)
            serialize_json: Whether to JSON serialize the value
        
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            
            if serialize_json and not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            client.setex(cache_key, ttl, value)
            
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as error:
            logger.error(f"Cache SET failed: {error}")
            return False
    
    def get(self, key: str, deserialize_json: bool = True) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            deserialize_json: Whether to deserialize JSON value
        
        Returns:
            Cached value or None if not found
        """
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            
            value = client.get(cache_key)
            
            if value is None:
                return None
            
            if deserialize_json:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            
            return value
            
        except Exception as error:
            logger.error(f"Cache GET failed: {error}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            client.delete(cache_key)
            return True
        except Exception as error:
            logger.error(f"Cache DELETE failed: {error}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            return client.exists(cache_key) > 0
        except Exception:
            return False
    
    def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration time on existing key"""
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            return client.expire(cache_key, ttl_seconds)
        except Exception:
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key"""
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            return client.ttl(cache_key)
        except Exception:
            return -2
    
    def keys(self, pattern: str = '*') -> List[str]:
        """Get all keys matching pattern"""
        try:
            client = self._get_client()
            search_pattern = self._make_key(pattern)
            return [k.replace(self.key_prefix, '') for k in client.keys(search_pattern)]
        except Exception:
            return []
    
    def flush_pattern(self, pattern: str = '*') -> int:
        """Delete all keys matching pattern"""
        try:
            client = self._get_client()
            search_pattern = self._make_key(pattern)
            keys = client.keys(search_pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value"""
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            return client.incrby(cache_key, amount)
        except Exception:
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a numeric value"""
        try:
            client = self._get_client()
            cache_key = self._make_key(key)
            return client.decrby(cache_key, amount)
        except Exception:
            return None
    
    def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once (pipeline)"""
        try:
            client = self._get_client()
            cache_keys = [self._make_key(k) for k in keys]
            
            pipeline = client.pipeline()
            for cache_key in cache_keys:
                pipeline.get(cache_key)
            
            values = pipeline.execute()
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
            
            return result
            
        except Exception as error:
            logger.error(f"Cache GET MULTIPLE failed: {error}")
            return {}
    
    def set_multiple(self, mapping: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        """Set multiple values at once (pipeline)"""
        try:
            client = self._get_client()
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            
            pipeline = client.pipeline()
            for key, value in mapping.items():
                cache_key = self._make_key(key)
                if not isinstance(value, str):
                    value = json.dumps(value, default=str)
                pipeline.setex(cache_key, ttl, value)
            
            pipeline.execute()
            return True
            
        except Exception as error:
            logger.error(f"Cache SET MULTIPLE failed: {error}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health and connectivity"""
        try:
            client = self._get_client()
            start_time = datetime.now()
            client.ping()
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            info = client.info('server')
            
            return {
                'healthy': True,
                'latency_ms': round(latency, 2),
                'redis_version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown')
            }
            
        except Exception as error:
            return {
                'healthy': False,
                'error': str(error)
            }
    
    def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            self._client.close()
            self._client = None


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


class RepositoryBase(ABC, Generic[T]):
    """
    Base repository class implementing repository pattern.
    
    Provides generic CRUD operations and query methods.
    Should be subclassed for specific entity types.
    
    Usage:
      class UserRepository(RepositoryBase[User]):
          def find_by_email(self, email: str) -> Optional[User]:
              ...
    """
    
    def __init__(self, model_class: Type[T], session: Session):
        self.model_class = model_class
        self.session = session
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by primary key"""
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities with pagination"""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity"""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        pass


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base(cls=BaseModel)
    
    class AgentPersistenceModel(Base):
        """SQLAlchemy model for agent persistence"""
        __tablename__ = 'agents'
        
        name = Column(String(255), unique=True, nullable=False, index=True)
        description = Column(Text)
        capabilities = Column(JSON, nullable=False, default=list)
        status = Column(String(50), nullable=False, default='idle')
        metadata = Column(JSON, default=dict)
        is_active = Column(Boolean, default=True, nullable=False)
    
    class TaskPersistenceModel(Base):
        """SQLAlchemy model for task persistence"""
        __tablename__ = 'tasks'
        
        task_name = Column(String(255), nullable=False)
        task_description = Column(Text)
        task_type = Column(String(100))
        required_capabilities = Column(JSON, nullable=False, default=list)
        priority = Column(Integer, default=3)
        status = Column(String(50), nullable=False, default='pending_creation')
        assigned_agent_name = Column(String(255), index=True)
        input_data = Column(JSON)
        output_data = Column(JSON)
        error_message = Column(Text)
        metadata = Column(JSON, default=dict)
        is_active = Column(Boolean, default=True, nullable=False)
    
    class WorkflowPersistenceModel(Base):
        """SQLAlchemy model for workflow persistence"""
        __tablename__ = 'workflows'
        
        workflow_name = Column(String(255), nullable=False)
        workflow_description = Column(Text)
        execution_strategy = Column(String(50), default='sequential')
        status = Column(String(50), nullable=False, default='pending')
        completed_steps = Column(JSON, default=list)
        failed_steps = Column(JSON, default=list)
        results = Column(JSON)
        errors = Column(JSON)
        metadata = Column(JSON, default=dict)


def get_cache_manager(
    redis_url: str = 'redis://localhost:6379/0',
    use_fallback: bool = True
) -> Any:
    """
    Get cache manager instance with optional fallback.
    
    Args:
        redis_url: Redis connection URL
        use_fallback: Use in-memory fallback if Redis unavailable
    
    Returns:
        RedisCacheManager or InMemoryCacheFallback
    """
    try:
        return RedisCacheManager.get_instance('default', redis_url=redis_url)
    except RuntimeError:
        if use_fallback:
            logger.warning("Redis unavailable, using in-memory cache fallback")
            return InMemoryCacheFallback()
        raise
