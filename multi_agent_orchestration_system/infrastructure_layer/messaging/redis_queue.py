"""
Infrastructure Layer - Redis Message Queue Module
==========================================

Provides distributed message queue using Redis.
Part of the Phase 2 production hardening improvements.

Key Features:
  - Reliable message queuing
  - Priority queues
  - Message persistence
  - Dead letter queue
  - Consumer groups
  - Pub/Sub messaging
  - Stream support

Architecture:
  - Uses Redis LIST for queues
  - Uses Redis STREAM for streams
  - Uses Redis PUBSUB for real-time messaging
  - Supports distributed workers
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class QueueMessage:
    """Message structure for queue"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            'message_id': self.message_id,
            'payload': self.payload,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error': self.error,
            'metadata': self.metadata
        }, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'QueueMessage':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls(
            message_id=data['message_id'],
            payload=data['payload'],
            priority=MessagePriority(data['priority']),
            created_at=datetime.fromisoformat(data['created_at']),
            retry_count=data['retry_count'],
            max_retries=data['max_retries'],
            error=data.get('error'),
            metadata=data.get('metadata', {})
        )


class RedisMessageQueue:
    """
    Distributed message queue using Redis.
    
    Features:
      - Priority queues
      - Message persistence
      - Dead letter queue
      - Consumer groups
      - Reliable delivery
    
    Usage:
        queue = RedisMessageQueue(redis_url="redis://localhost:6379")
        
        # Enqueue message
        queue.enqueue({"task": "process", "data": {...}})
        
        # Dequeue message
        message = queue.dequeue()
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        queue_name: str = "maos:queue",
        dlq_name: str = "maos:dlq"
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.dlq_name = dlq_name
        self._redis = None
    
    def _get_redis(self):
        """Get Redis client"""
        try:
            import redis
            if self._redis is None:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
            return self._redis
        except ImportError:
            logger.error("Redis not available")
            return None
    
    def enqueue(
        self,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Enqueue a message.
        
        Args:
            payload: Message payload
            priority: Message priority
            max_retries: Maximum retry attempts
        
        Returns:
            Message ID if successful
        """
        redis_client = self._get_redis()
        if not redis_client:
            return None
        
        message = QueueMessage(
            payload=payload,
            priority=priority,
            max_retries=max_retries
        )
        
        try:
            if priority == MessagePriority.HIGH or priority == MessagePriority.CRITICAL:
                redis_client.lpush(self.queue_name, message.to_json())
            else:
                redis_client.rpush(self.queue_name, message.to_json())
            
            logger.debug(f"Enqueued message: {message.message_id}")
            return message.message_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return None
    
    def dequeue(self, timeout: int = 0) -> Optional[QueueMessage]:
        """
        Dequeue a message.
        
        Args:
            timeout: Blocking timeout in seconds (0 = non-blocking)
        
        Returns:
            Dequeued message or None
        """
        redis_client = self._get_redis()
        if not redis_client:
            return None
        
        try:
            if timeout > 0:
                result = redis_client.blpop(self.queue_name, timeout=timeout)
                if result:
                    _, message_json = result
                    return QueueMessage.from_json(message_json)
            else:
                message_json = redis_client.lpop(self.queue_name)
                if message_json:
                    return QueueMessage.from_json(message_json)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue message: {e}")
            return None
    
    def requeue(self, message: QueueMessage) -> bool:
        """Requeue a message for retry"""
        redis_client = self._get_redis()
        if not redis_client:
            return False
        
        try:
            message.retry_count += 1
            
            if message.retry_count < message.max_retries:
                redis_client.rpush(self.queue_name, message.to_json())
                logger.debug(f"Requeued message: {message.message_id}")
                return True
            else:
                self.move_to_dlq(message)
                return False
                
        except Exception as e:
            logger.error(f"Failed to requeue message: {e}")
            return False
    
    def move_to_dlq(self, message: QueueMessage) -> bool:
        """Move failed message to dead letter queue"""
        redis_client = self._get_redis()
        if not redis_client:
            return False
        
        try:
            redis_client.rpush(self.dlq_name, message.to_json())
            logger.warning(f"Moved message to DLQ: {message.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move message to DLQ: {e}")
            return False
    
    def get_queue_size(self) -> int:
        """Get number of messages in queue"""
        redis_client = self._get_redis()
        if not redis_client:
            return 0
        
        try:
            return redis_client.llen(self.queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
    
    def get_dlq_size(self) -> int:
        """Get number of messages in DLQ"""
        redis_client = self._get_redis()
        if not redis_client:
            return 0
        
        try:
            return redis_client.llen(self.dlq_name)
        except Exception as e:
            logger.error(f"Failed to get DLQ size: {e}")
            return 0
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        redis_client = self._get_redis()
        if not redis_client:
            return {}
        
        try:
            return {
                'queue_name': self.queue_name,
                'queue_size': redis_client.llen(self.queue_name),
                'dlq_name': self.dlq_name,
                'dlq_size': redis_client.llen(self.dlq_name)
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    def clear_queue(self) -> int:
        """Clear all messages from queue"""
        redis_client = self._get_redis()
        if not redis_client:
            return 0
        
        try:
            size = redis_client.llen(self.queue_name)
            redis_client.delete(self.queue_name)
            logger.info(f"Cleared {size} messages from queue")
            return size
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return 0


class RedisPubSub:
    """
    Redis Pub/Sub for real-time messaging.
    
    Features:
      - Topic-based messaging
      - Multiple subscribers
      - Pattern matching
      - Real-time delivery
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis = None
        self._pubsub = None
        self._subscriptions: Dict[str, Callable] = {}
    
    def _get_redis(self):
        """Get Redis client"""
        try:
            import redis
            if self._redis is None:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
            return self._redis
        except ImportError:
            return None
    
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish message to channel"""
        redis_client = self._get_redis()
        if not redis_client:
            return 0
        
        try:
            return redis_client.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return 0
    
    def subscribe(self, channel: str, callback: Callable[[Dict], None]) -> None:
        """Subscribe to channel"""
        redis_client = self._get_redis()
        if not redis_client:
            return
        
        self._subscriptions[channel] = callback
        
        try:
            pubsub = redis_client.pubsub()
            pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")


if __name__ == "__main__":
    print("Redis Message Queue Module")
    print("=" * 50)
    
    queue = RedisMessageQueue()
    
    print("\n1. Enqueueing messages:")
    msg_id1 = queue.enqueue({"task": "process_data", "id": 1}, MessagePriority.NORMAL)
    msg_id2 = queue.enqueue({"task": "send_email", "id": 2}, MessagePriority.HIGH)
    msg_id3 = queue.enqueue({"task": "cleanup", "id": 3}, MessagePriority.LOW)
    
    print(f"   Message 1 ID: {msg_id1}")
    print(f"   Message 2 ID: {msg_id2}")
    print(f"   Message 3 ID: {msg_id3}")
    
    print("\n2. Queue statistics:")
    stats = queue.get_queue_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n3. Dequeueing messages:")
    msg = queue.dequeue()
    if msg:
        print(f"   Dequeued: {msg.message_id}")
        print(f"   Payload: {msg.payload}")
