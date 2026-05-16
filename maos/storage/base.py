"""
MAOS存储抽象层 - 基类定义

基于AWS Agent Squad的存储设计，提供统一的存储接口抽象。

主要特性：
- 异步存储操作
- 完整的类型注解
- 错误处理和回退机制
- 会话和消息管理
- 可选的TTL支持
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    TypeVar,
)

if TYPE_CHECKING:
    from ..types import ConversationMessage

T = TypeVar('T')

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """存储操作基础异常"""

    def __init__(self, message: str, operation: str = "", cause: Optional[Exception] = None):
        self.message = message
        self.operation = operation
        self.cause = cause
        super().__init__(self.message)

    def __str__(self) -> str:
        base_msg = f"StorageError: {self.message}"
        if self.operation:
            base_msg += f" (operation: {self.operation})"
        if self.cause:
            base_msg += f" - Caused by: {self.cause}"
        return base_msg


class StorageNotAvailableError(StorageError):
    """存储不可用异常"""
    pass


class StorageConnectionError(StorageError):
    """存储连接错误"""
    pass


class StorageSerializationError(StorageError):
    """数据序列化错误"""
    pass


@dataclass
class SessionInfo:
    """
    会话信息数据类

    存储会话的元数据信息

    Attributes:
        user_id: 用户标识符
        session_id: 会话标识符
        created_at: 会话创建时间
        updated_at: 最后更新时间
        message_count: 消息数量
        metadata: 会话元数据
        active: 会话是否活跃
    """
    user_id: str
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.message_count,
            'metadata': self.metadata,
            'active': self.active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """从字典反序列化"""
        data = data.copy()
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ChatStorageConfig:
    """
    存储配置数据类

    定义存储层的通用配置选项

    Attributes:
        max_history_size: 最大历史消息数量
        ttl_seconds: TTL生存时间（秒）
        enable_compression: 是否启用压缩
        enable_encryption: 是否启用加密
        retry_attempts: 重试次数
        retry_delay: 重试延迟（秒）
    """
    max_history_size: Optional[int] = None
    ttl_seconds: Optional[int] = None
    enable_compression: bool = False
    enable_encryption: bool = False
    retry_attempts: int = 3
    retry_delay: float = 0.1


class ChatStorage(ABC):
    """
    聊天存储抽象基类

    定义所有存储实现必须遵循的接口。
    支持异步操作、错误处理、会话管理等功能。

    必需实现的方法：
        - save_chat_message(): 保存单条消息
        - fetch_chat(): 获取聊天历史
        - fetch_all_chats(): 获取所有聊天记录

    可选实现的方法：
        - delete_chat(): 删除聊天记录
        - list_sessions(): 列出会话
        - save_chat_messages(): 批量保存消息
        - get_session_info(): 获取会话信息

    示例：
        class MyStorage(ChatStorage):
            async def save_chat_message(self, ...):
                # 实现保存逻辑
                pass

            async def fetch_chat(self, ...):
                # 实现获取逻辑
                pass

            async def fetch_all_chats(self, ...):
                # 实现获取所有聊天逻辑
                pass
    """

    def __init__(self, config: Optional[ChatStorageConfig] = None):
        """
        初始化存储实例

        Args:
            config: 存储配置
        """
        self.config = config or ChatStorageConfig()
        self._initialized = False

    async def initialize(self) -> None:
        """
        初始化存储连接

        异步初始化方法，子类可重写以实现自定义初始化逻辑。
        默认实现将_initialized设为True。
        """
        self._initialized = True

    async def close(self) -> None:
        """
        关闭存储连接

        异步关闭方法，子类可重写以实现资源清理。
        """
        self._initialized = False

    @staticmethod
    def generate_key(user_id: str, session_id: str, agent_id: Optional[str] = None) -> str:
        """
        生成存储键

        Args:
            user_id: 用户标识符
            session_id: 会话标识符
            agent_id: Agent标识符（可选）

        Returns:
            格式化的存储键
        """
        if agent_id:
            return f"{user_id}#{session_id}#{agent_id}"
        return f"{user_id}#{session_id}"

    @staticmethod
    def parse_key(key: str) -> Dict[str, str]:
        """
        解析存储键

        Args:
            key: 存储键

        Returns:
            包含user_id, session_id, agent_id的字典
        """
        parts = key.split('#')
        result = {
            'user_id': parts[0] if len(parts) > 0 else '',
            'session_id': parts[1] if len(parts) > 1 else '',
            'agent_id': parts[2] if len(parts) > 2 else None,
        }
        return result

    def is_same_role_as_last_message(
        self,
        conversation: List["ConversationMessage"],
        new_message: "ConversationMessage"
    ) -> bool:
        """
        检查新消息是否与对话中最后一条消息角色相同

        用于检测连续消息以优化存储。

        Args:
            conversation: 现有对话
            new_message: 新消息

        Returns:
            如果角色相同返回True
        """
        if not conversation:
            return False
        return conversation[-1].role == new_message.role

    def trim_conversation(
        self,
        conversation: List["ConversationMessage"],
        max_history_size: Optional[int] = None
    ) -> List["ConversationMessage"]:
        """
        裁剪对话到指定大小

        确保max_history_size为偶数以保持完整的问答对。

        Args:
            conversation: 要裁剪的对话
            max_history_size: 最大消息数量

        Returns:
            裁剪后的对话
        """
        effective_max_size = max_history_size or self.config.max_history_size
        if effective_max_size is None:
            return conversation

        if effective_max_size % 2 == 0:
            adjusted_max_size = effective_max_size
        else:
            adjusted_max_size = effective_max_size - 1

        return conversation[-adjusted_max_size:] if len(conversation) > adjusted_max_size else conversation

    def message_to_dict(self, message: "ConversationMessage") -> Dict[str, Any]:
        """
        将消息转换为字典

        Args:
            message: 消息对象

        Returns:
            消息的字典表示
        """
        return message.to_dict()

    def dict_to_message(self, data: Dict[str, Any]) -> "ConversationMessage":
        """
        将字典转换为消息

        Args:
            data: 字典数据

        Returns:
            ConversationMessage实例
        """
        return ConversationMessage.from_dict(data)

    @abstractmethod
    async def save_chat_message(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        new_message: "ConversationMessage",
        max_history_size: Optional[int] = None
    ) -> bool:
        """
        保存单条聊天消息

        Args:
            user_id: 用户标识符
            session_id: 会话标识符
            agent_id: Agent标识符
            new_message: 要保存的消息
            max_history_size: 最大历史消息数量

        Returns:
            保存成功返回True

        Raises:
            StorageError: 保存失败时抛出
        """

    @abstractmethod
    async def fetch_chat(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        max_history_size: Optional[int] = None
    ) -> List["ConversationMessage"]:
        """
        获取指定Agent的聊天历史

        Args:
            user_id: 用户标识符
            session_id: 会话标识符
            agent_id: Agent标识符
            max_history_size: 最大返回消息数量

        Returns:
            消息列表

        Raises:
            StorageError: 获取失败时抛出
        """

    @abstractmethod
    async def fetch_all_chats(
        self,
        user_id: str,
        session_id: str
    ) -> List["ConversationMessage"]:
        """
        获取用户会话的所有聊天记录

        合并所有Agent的消息并按时间排序。

        Args:
            user_id: 用户标识符
            session_id: 会话标识符

        Returns:
            按时间排序的所有消息列表

        Raises:
            StorageError: 获取失败时抛出
        """

    async def save_chat_messages(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        new_messages: List["ConversationMessage"],
        max_history_size: Optional[int] = None
    ) -> bool:
        """
        批量保存聊天消息

        默认实现循环调用save_chat_message，子类可优化实现。

        Args:
            user_id: 用户标识符
            session_id: 会话标识符
            agent_id: Agent标识符
            new_messages: 要保存的消息列表
            max_history_size: 最大历史消息数量

        Returns:
            保存成功返回True

        Raises:
            StorageError: 保存失败时抛出
        """
        for message in new_messages:
            success = await self.save_chat_message(
                user_id, session_id, agent_id, message, max_history_size
            )
            if not success:
                return False
        return True

    async def delete_chat(
        self,
        user_id: str,
        session_id: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """
        删除聊天记录

        可选实现，子类可重写。

        Args:
            user_id: 用户标识符
            session_id: 会话标识符
            agent_id: Agent标识符（可选，为None时删除所有Agent的聊天）

        Returns:
            删除成功返回True

        Raises:
            StorageError: 删除失败时抛出
        """
        raise NotImplementedError("delete_chat is not implemented for this storage backend")

    async def list_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[SessionInfo]:
        """
        列出用户的所有会话

        可选实现，子类可重写。

        Args:
            user_id: 用户标识符
            active_only: 是否只返回活跃会话

        Returns:
            会话信息列表

        Raises:
            StorageError: 获取失败时抛出
        """
        raise NotImplementedError("list_sessions is not implemented for this storage backend")

    async def get_session_info(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[SessionInfo]:
        """
        获取会话信息

        可选实现，子类可重写。

        Args:
            user_id: 用户标识符
            session_id: 会话标识符

        Returns:
            会话信息，不存在返回None

        Raises:
            StorageError: 获取失败时抛出
        """
        raise NotImplementedError("get_session_info is not implemented for this storage backend")

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息字典
        """
        return {
            'storage_type': self.__class__.__name__,
            'initialized': self._initialized,
            'healthy': self._initialized,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(config={self.config})>"


class StorageFactory:
    """
    存储工厂类

    提供统一的存储实例创建接口
    """

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, storage_class: type) -> None:
        """
        注册存储实现

        Args:
            name: 存储类型名称
            storage_class: 存储类
        """
        cls._registry[name] = storage_class

    @classmethod
    def create(cls, name: str, **kwargs) -> ChatStorage:
        """
        创建存储实例

        Args:
            name: 存储类型名称
            **kwargs: 传递给存储类的参数

        Returns:
            存储实例

        Raises:
            ValueError: 未知存储类型时抛出
        """
        if name not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise ValueError(
                f"Unknown storage type: {name}. Available: {available}"
            )
        return cls._registry[name](**kwargs)

    @classmethod
    def available_storages(cls) -> List[str]:
        """
        获取可用的存储类型

        Returns:
            可用存储类型名称列表
        """
        return list(cls._registry.keys())
