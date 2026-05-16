"""
MAOS Storage Module - 存储抽象层

提供统一的聊天存储接口，支持多种存储后端。

主要组件：
- ChatStorage: 存储抽象基类
- InMemoryChatStorage: 内存存储实现
- RedisChatStorage: Redis存储实现（需要redis包）
- StorageFactory: 存储工厂类
- SessionInfo: 会话信息数据类
- ChatStorageConfig: 存储配置类

使用示例：
    # 使用内存存储
    from maos.storage import InMemoryChatStorage, StorageFactory

    storage = InMemoryChatStorage()
    await storage.initialize()

    await storage.save_chat_message(
        user_id="user1",
        session_id="session1",
        agent_id="agent1",
        new_message=ConversationMessage(role=ParticipantRole.USER, content="Hello")
    )

    messages = await storage.fetch_chat("user1", "session1", "agent1")

    # 使用工厂创建存储
    storage = StorageFactory.create("memory")
    storage = StorageFactory.create("redis", host="localhost", port=6379)
"""

from .base import (
    ChatStorage,
    ChatStorageConfig,
    SessionInfo,
    StorageError,
    StorageFactory,
    StorageNotAvailableError,
    StorageConnectionError,
    StorageSerializationError,
)

from .in_memory import InMemoryChatStorage

StorageFactory.register('memory', InMemoryChatStorage)
StorageFactory.register('in_memory', InMemoryChatStorage)

_REDIS_AVAILABLE = False
_RedisChatStorage = None

try:
    from .redis import RedisChatStorage as _RedisChatStorage
    _REDIS_AVAILABLE = True
except ImportError:
    _RedisChatStorage = None

if _REDIS_AVAILABLE and _RedisChatStorage is not None:
    StorageFactory.register('redis', _RedisChatStorage)

__all__ = [
    'ChatStorage',
    'ChatStorageConfig',
    'SessionInfo',
    'StorageError',
    'StorageNotAvailableError',
    'StorageConnectionError',
    'StorageSerializationError',
    'StorageFactory',
    'InMemoryChatStorage',
    'is_redis_available',
    'get_redis_error_message',
]

if _REDIS_AVAILABLE and _RedisChatStorage is not None:
    __all__.append('RedisChatStorage')

__version__ = '1.0.0'


def is_redis_available() -> bool:
    from .redis import is_redis_available as _is_available
    return _is_available()


def get_redis_error_message() -> str:
    from .redis import get_redis_error_message as _get_error
    return _get_error() or ""
