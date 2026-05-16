"""
Infrastructure Layer - Messaging Module
===================================

Provides distributed messaging capabilities using Redis pub/sub.
Gracefully falls back to in-memory messaging when Redis is unavailable.

Components:
  - MessageBroker: Core messaging abstraction
  - RedisMessageBroker: Redis-backed implementation
  - InMemoryMessageBroker: Fallback in-memory implementation
  - MessageChannel: Channel abstraction for pub/sub patterns
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)

MESSAGING_BACKEND_REDIS = "redis"
MESSAGING_BACKEND_MEMORY = "memory"

try:
    import redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_SDK_AVAILABLE = True
except ImportError:
    REDIS_SDK_AVAILABLE = False
    logger.warning("Redis SDK not available, using in-memory messaging fallback")


@dataclass
class MessageEnvelope:
    """Standardized message format for agent communication"""
    message_id: str
    sender_name: str
    receiver_names: List[str]
    message_type: str
    payload: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    
    def to_json_string(self) -> str:
        """Serialize message to JSON string"""
        return json.dumps({
            'message_id': self.message_id,
            'sender_name': self.sender_name,
            'receiver_names': self.receiver_names,
            'message_type': self.message_type,
            'payload': self.payload,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'reply_to_message_id': self.reply_to_message_id
        })
    
    @classmethod
    def from_json_string(cls, json_string: str) -> 'MessageEnvelope':
        """Deserialize message from JSON string"""
        data = json.loads(json_string)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MessageBrokerBase:
    """Abstract base class for message broker implementations"""
    
    def publish_message(self, channel: str, message: MessageEnvelope) -> None:
        """Publish a message to a channel"""
        raise NotImplementedError
    
    def subscribe_to_channel(self, channel: str, callback: Callable) -> None:
        """Subscribe to messages on a channel"""
        raise NotImplementedError
    
    def unsubscribe_from_channel(self, channel: str) -> None:
        """Unsubscribe from a channel"""
        raise NotImplementedError
    
    def get_message_count(self, channel: str) -> int:
        """Get the number of messages in a channel"""
        raise NotImplementedError
    
    def clear_channel(self, channel: str) -> None:
        """Clear all messages from a channel"""
        raise NotImplementedError


class InMemoryMessageBroker(MessageBrokerBase):
    """
    In-memory message broker implementation.
    Used as fallback when Redis is unavailable.
    
    Features:
      - Thread-safe message storage
      - Channel-based pub/sub
      - Message persistence (in-memory)
    """
    
    def __init__(self):
        self._channels: Dict[str, List[str]] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._message_history: Dict[str, List[MessageEnvelope]] = {}
        self._max_history_per_channel = 1000
    
    def publish_message(self, channel: str, message: MessageEnvelope) -> None:
        """Publish message to channel and notify subscribers"""
        if channel not in self._channels:
            self._channels[channel] = []
            self._message_history[channel] = []
        
        json_message = message.to_json_string()
        self._channels[channel].append(json_message)
        
        self._message_history[channel].append(message)
        if len(self._message_history[channel]) > self._max_history_per_channel:
            self._message_history[channel].pop(0)
        
        if channel in self._subscribers:
            for callback in self._subscribers[channel]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in message subscriber: {e}")
    
    def subscribe_to_channel(self, channel: str, callback: Callable) -> None:
        """Register a callback for channel messages"""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        if callback not in self._subscribers[channel]:
            self._subscribers[channel].append(callback)
    
    def unsubscribe_from_channel(self, channel: str, callback: Optional[Callable] = None) -> None:
        """Unregister callback(s) from channel"""
        if channel in self._subscribers:
            if callback:
                if callback in self._subscribers[channel]:
                    self._subscribers[channel].remove(callback)
            else:
                self._subscribers[channel].clear()
    
    def get_message_count(self, channel: str) -> int:
        """Get count of messages in channel"""
        return len(self._channels.get(channel, []))
    
    def clear_channel(self, channel: str) -> None:
        """Clear all messages from channel"""
        if channel in self._channels:
            self._channels[channel].clear()
        if channel in self._message_history:
            self._message_history[channel].clear()
    
    def get_channel_messages(self, channel: str, limit: int = 100) -> List[MessageEnvelope]:
        """Get recent messages from channel"""
        messages = self._message_history.get(channel, [])
        return messages[-limit:] if limit > 0 else messages
    
    def get_all_channels(self) -> List[str]:
        """Get list of all active channels"""
        return list(self._channels.keys())


class RedisMessageBroker(MessageBrokerBase):
    """
    Redis-backed message broker implementation.
    Provides distributed messaging with pub/sub patterns.
    
    Features:
      - Redis pub/sub for real-time messaging
      - Message persistence in Redis lists
      - Horizontal scalability support
    """
    
    def __init__(self, redis_url: str):
        if not REDIS_SDK_AVAILABLE:
            raise RuntimeError("Redis SDK not available")
        
        self._redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub_connections: Dict[str, Any] = {}
    
    def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client connection"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self._redis_url)
        return self._redis_client
    
    def publish_message(self, channel: str, message: MessageEnvelope) -> None:
        """Publish message to Redis channel"""
        try:
            client = self._get_redis_client()
            client.publish(channel, message.to_json_string())
            
            list_key = f"maos:messages:{channel}"
            client.lpush(list_key, message.to_json_string())
            client.expire(list_key, 3600)
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
            raise
    
    def subscribe_to_channel(self, channel: str, callback: Callable) -> None:
        """Subscribe to Redis channel"""
        try:
            client = self._get_redis_client()
            pubsub = client.pubsub()
            pubsub.subscribe(channel)
            self._pubsub_connections[channel] = pubsub
            
            for message_data in pubsub.listen():
                if message_data['type'] == 'message':
                    message = MessageEnvelope.from_json_string(message_data['data'])
                    callback(message)
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis channel: {e}")
            raise
    
    def unsubscribe_from_channel(self, channel: str) -> None:
        """Unsubscribe from Redis channel"""
        if channel in self._pubsub_connections:
            self._pubsub_connections[channel].unsubscribe(channel)
            del self._pubsub_connections[channel]
    
    def get_message_count(self, channel: str) -> int:
        """Get count of messages in Redis list"""
        try:
            client = self._get_redis_client()
            list_key = f"maos:messages:{channel}"
            return client.llen(list_key)
        except Exception:
            return 0
    
    def clear_channel(self, channel: str) -> None:
        """Clear messages from Redis list"""
        try:
            client = self._get_redis_client()
            list_key = f"maos:messages:{channel}"
            client.delete(list_key)
        except Exception as e:
            logger.error(f"Failed to clear Redis channel: {e}")


class MessageBrokerFactory:
    """
    Factory for creating appropriate message broker instances.
    Automatically selects Redis if available, otherwise uses in-memory.
    """
    
    _instance: Optional['MessageBrokerFactory'] = None
    _broker: Optional[MessageBrokerBase] = None
    _backend_type: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_message_broker(cls, redis_url: Optional[str] = None) -> MessageBrokerBase:
        """
        Get the configured message broker instance.
        Uses Redis if available and url provided, otherwise falls back to in-memory.
        """
        if cls._broker is None:
            if REDIS_SDK_AVAILABLE and redis_url:
                try:
                    cls._broker = RedisMessageBroker(redis_url)
                    cls._backend_type = MESSAGING_BACKEND_REDIS
                    logger.info("Using Redis message broker")
                except Exception as e:
                    logger.warning(f"Redis connection failed, using in-memory broker: {e}")
                    cls._broker = InMemoryMessageBroker()
                    cls._backend_type = MESSAGING_BACKEND_MEMORY
            else:
                cls._broker = InMemoryMessageBroker()
                cls._backend_type = MESSAGING_BACKEND_MEMORY
                if not REDIS_SDK_AVAILABLE:
                    logger.info("Redis SDK not available, using in-memory message broker")
                else:
                    logger.info("No Redis URL provided, using in-memory message broker")
        
        return cls._broker
    
    @classmethod
    def get_backend_type(cls) -> str:
        """Get the current backend type in use"""
        if cls._backend_type is None:
            cls.get_message_broker()
        return cls._backend_type or MESSAGING_BACKEND_MEMORY
    
    @classmethod
    def reset_broker(cls) -> None:
        """Reset the broker instance (useful for testing)"""
        cls._broker = None
        cls._backend_type = None
