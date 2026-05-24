"""
MAOS内存存储实现

基于字典的内存存储实现，适合开发和测试环境。
支持会话管理、消息历史、自动清理等功能。

特点：
- 快速读写
- 会话隔离
- 自动过期清理
- 线程安全（asyncio锁）
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from ..types import ConversationMessage, ParticipantRole
from .base import (
    ChatStorage,
    ChatStorageConfig,
    SessionInfo,
    StorageError,
)

logger = logging.getLogger(__name__)


class InMemoryChatStorage(ChatStorage):
    """
    内存聊天存储

    使用内存字典存储聊天记录，适合：
    - 开发环境
    - 测试环境
    - 单实例部署
    - 小规模数据量

    Attributes:
        conversations: 存储对话的字典
        sessions: 存储会话信息的字典
        _lock: 异步锁，用于线程安全
        _cleanup_task: 清理任务
        _auto_cleanup: 是否启用自动清理
        _cleanup_interval: 清理间隔（秒）
        _entry_ttl: 条目TTL（秒）
    """

    def __init__(
        self,
        config: Optional[ChatStorageConfig] = None,
        auto_cleanup: bool = True,
        cleanup_interval: int = 300,
        entry_ttl: Optional[int] = None,
    ):
        """
        初始化内存存储

        Args:
            config: 存储配置
            auto_cleanup: 是否启用自动清理
            cleanup_interval: 清理间隔（秒）
            entry_ttl: 条目TTL（秒），None表示不过期
        """
        super().__init__(config)
        self.conversations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()  # 线程锁，用于同步操作
        self._cleanup_task: Optional[asyncio.Task] = None
        self._auto_cleanup = auto_cleanup
        self._cleanup_interval = cleanup_interval
        self._entry_ttl = entry_ttl
        self._entry_access_times: Dict[str, float] = {}

    async def initialize(self) -> None:
        """初始化存储，启动自动清理任务"""
        await super().initialize()
        if self._auto_cleanup and self._entry_ttl is not None:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
            logger.info("InMemoryChatStorage initialized with auto-cleanup")

    async def close(self) -> None:
        """关闭存储，停止清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await super().close()
        logger.info("InMemoryChatStorage closed")

    async def _auto_cleanup_loop(self) -> None:
        """自动清理循环"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            清理的条目数量
        """
        if self._entry_ttl is None:
            return 0

        current_time = time.time()
        expired_keys = []
        removed_count = 0

        async with self._lock:
            for key, access_time in list(self._entry_access_times.items()):
                if current_time - access_time > self._entry_ttl:
                    expired_keys.append(key)
                    removed_count += 1

            for key in expired_keys:
                if key in self.conversations:
                    del self.conversations[key]
                if key in self._entry_access_times:
                    del self._entry_access_times[key]

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired entries")

        return removed_count

    def _update_access_time(self, key: str) -> None:
        """更新访问时间"""
        if self._entry_ttl is not None:
            self._entry_access_times[key] = time.time()

    async def save_chat_message(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        new_message: ConversationMessage,
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
        try:
            key = self.generate_key(user_id, session_id, agent_id)
            conversation = self.conversations[key]

            async with self._lock:
                if self.is_same_role_as_last_message(
                    self._dict_to_messages(conversation), new_message
                ):
                    logger.debug(
                        f"Consecutive {new_message.role.value} message detected "
                        f"for agent {agent_id}. Skipping."
                    )
                    return True

                message_dict = {
                    'role': new_message.role.value,
                    'content': self._serialize_content(new_message.content),
                    'timestamp': new_message.timestamp.isoformat(),
                    'id': new_message.id,
                }

                conversation.append(message_dict)
                conversation = self._trim_conversation_internal(conversation, max_history_size)
                self.conversations[key] = conversation
                self._update_access_time(key)

                await self._update_session(user_id, session_id, len(conversation))

            return True

        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            raise StorageError(
                message=f"Failed to save message: {e}",
                operation="save_chat_message",
                cause=e
            )

    async def save_chat_messages(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        new_messages: List[ConversationMessage],
        max_history_size: Optional[int] = None
    ) -> bool:
        """
        批量保存聊天消息

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
        try:
            key = self.generate_key(user_id, session_id, agent_id)

            async with self._lock:
                conversation = self.conversations[key]

                for new_message in new_messages:
                    message_dict = {
                        'role': new_message.role.value,
                        'content': self._serialize_content(new_message.content),
                        'timestamp': new_message.timestamp.isoformat(),
                        'id': new_message.id,
                    }
                    conversation.append(message_dict)

                conversation = self._trim_conversation_internal(conversation, max_history_size)
                self.conversations[key] = conversation
                self._update_access_time(key)

                await self._update_session(user_id, session_id, len(conversation))

            return True

        except Exception as e:
            logger.error(f"Error saving chat messages: {e}")
            raise StorageError(
                message=f"Failed to save messages: {e}",
                operation="save_chat_messages",
                cause=e
            )

    async def fetch_chat(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        max_history_size: Optional[int] = None
    ) -> List[ConversationMessage]:
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
        try:
            key = self.generate_key(user_id, session_id, agent_id)

            async with self._lock:
                conversation = self.conversations.get(key, [])
                self._update_access_time(key)

                messages = self._dict_to_messages(conversation)
                if max_history_size is not None:
                    messages = self.trim_conversation(messages, max_history_size)

            return messages

        except Exception as e:
            logger.error(f"Error fetching chat: {e}")
            raise StorageError(
                message=f"Failed to fetch chat: {e}",
                operation="fetch_chat",
                cause=e
            )

    async def fetch_all_chats(
        self,
        user_id: str,
        session_id: str
    ) -> List[ConversationMessage]:
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
        try:
            prefix = f"{user_id}#{session_id}#"
            all_messages: List[Dict[str, Any]] = []

            async with self._lock:
                for key, messages in self.conversations.items():
                    if key.startswith(prefix):
                        for msg in messages:
                            msg_copy = msg.copy()
                            msg_copy['agent_id'] = key.split('#')[-1]
                            all_messages.append(msg_copy)

                all_messages.sort(key=lambda x: x.get('timestamp', ''))

            result = []
            for msg in all_messages:
                agent_id = msg.pop('agent_id', None)
                content = msg['content']

                if isinstance(content, list) and len(content) > 0:
                    if msg['role'] == ParticipantRole.ASSISTANT.value:
                        text_content = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
                        content = [{'text': f"[{agent_id}] {text_content}"}]

                message = ConversationMessage(
                    id=msg.get('id', ''),
                    role=ParticipantRole(msg['role']),
                    content=content,
                    timestamp=datetime.fromisoformat(msg['timestamp']),
                )
                result.append(message)

            return result

        except Exception as e:
            logger.error(f"Error fetching all chats: {e}")
            raise StorageError(
                message=f"Failed to fetch all chats: {e}",
                operation="fetch_all_chats",
                cause=e
            )

    async def delete_chat(
        self,
        user_id: str,
        session_id: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """
        删除聊天记录

        Args:
            user_id: 用户标识符
            session_id: 会话标识符
            agent_id: Agent标识符（可选，为None时删除所有Agent的聊天）

        Returns:
            删除成功返回True

        Raises:
            StorageError: 删除失败时抛出
        """
        try:
            async with self._lock:
                if agent_id:
                    key = self.generate_key(user_id, session_id, agent_id)
                    if key in self.conversations:
                        del self.conversations[key]
                    if key in self._entry_access_times:
                        del self._entry_access_times[key]
                else:
                    prefix = f"{user_id}#{session_id}#"
                    keys_to_delete = [k for k in self.conversations.keys() if k.startswith(prefix)]
                    for key in keys_to_delete:
                        del self.conversations[key]
                        if key in self._entry_access_times:
                            del self._entry_access_times[key]

                session_key = f"{user_id}#{session_id}"
                if session_key in self.sessions:
                    del self.sessions[session_key]

            return True

        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            raise StorageError(
                message=f"Failed to delete chat: {e}",
                operation="delete_chat",
                cause=e
            )

    async def list_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[SessionInfo]:
        """
        列出用户的所有会话

        Args:
            user_id: 用户标识符
            active_only: 是否只返回活跃会话

        Returns:
            会话信息列表

        Raises:
            StorageError: 获取失败时抛出
        """
        try:
            prefix = f"{user_id}#"
            sessions = []

            async with self._lock:
                for key, session_data in self.sessions.items():
                    if key.startswith(prefix):
                        session_info = SessionInfo.from_dict(session_data)
                        if active_only and not session_info.active:
                            continue
                        sessions.append(session_info)

            sessions.sort(key=lambda x: x.updated_at, reverse=True)
            return sessions

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            raise StorageError(
                message=f"Failed to list sessions: {e}",
                operation="list_sessions",
                cause=e
            )

    async def get_session_info(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[SessionInfo]:
        """
        获取会话信息

        Args:
            user_id: 用户标识符
            session_id: 会话标识符

        Returns:
            会话信息，不存在返回None

        Raises:
            StorageError: 获取失败时抛出
        """
        try:
            session_key = f"{user_id}#{session_id}"

            async with self._lock:
                session_data = self.sessions.get(session_key)

            if session_data:
                return SessionInfo.from_dict(session_data)
            return None

        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            raise StorageError(
                message=f"Failed to get session info: {e}",
                operation="get_session_info",
                cause=e
            )

    async def _update_session(
        self,
        user_id: str,
        session_id: str,
        message_count: int
    ) -> None:
        """更新会话信息"""
        session_key = f"{user_id}#{session_id}"
        now = datetime.now()

        if session_key in self.sessions:
            self.sessions[session_key]['updated_at'] = now.isoformat()
            self.sessions[session_key]['message_count'] = message_count
        else:
            self.sessions[session_key] = {
                'user_id': user_id,
                'session_id': session_id,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat(),
                'message_count': message_count,
                'metadata': {},
                'active': True,
            }

    def _dict_to_messages(
        self,
        messages_dict: List[Dict[str, Any]]
    ) -> List[ConversationMessage]:
        """将字典列表转换为消息对象列表"""
        messages = []
        for msg in messages_dict:
            try:
                role = ParticipantRole(msg['role']) if isinstance(msg['role'], str) else msg['role']
                message = ConversationMessage(
                    id=msg.get('id', ''),
                    role=role,
                    content=msg.get('content', ''),
                    timestamp=datetime.fromisoformat(msg['timestamp']) if isinstance(msg['timestamp'], str) else msg['timestamp'],
                )
                messages.append(message)
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing message: {e}")
                continue
        return messages

    def _serialize_content(
        self,
        content: Any
    ) -> Any:
        """序列化消息内容"""
        if isinstance(content, list):
            return [
                item.to_dict() if hasattr(item, 'to_dict') else item
                for item in content
            ]
        elif hasattr(content, 'to_dict'):
            return content.to_dict()
        return content

    def _trim_conversation_internal(
        self,
        conversation: List[Dict[str, Any]],
        max_history_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """内部裁剪方法，直接操作字典列表"""
        effective_max_size = max_history_size or self.config.max_history_size
        if effective_max_size is None:
            return conversation

        if effective_max_size % 2 == 0:
            adjusted_max_size = effective_max_size
        else:
            adjusted_max_size = effective_max_size - 1

        if len(conversation) > adjusted_max_size:
            return conversation[-adjusted_max_size:]
        return conversation

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        base_health = await super().health_check()
        async with self._lock:
            return {
                **base_health,
                'conversation_count': len(self.conversations),
                'session_count': len(self.sessions),
                'auto_cleanup': self._auto_cleanup,
                'entry_ttl': self._entry_ttl,
            }

    def clear_all(self) -> None:
        """清空所有数据（谨慎使用）"""
        self.conversations.clear()
        self.sessions.clear()
        self._entry_access_times.clear()
        logger.info("All in-memory storage cleared")

    def save_message(self, user_id: str, message: Dict[str, Any], skip_consecutive_check: bool = True) -> bool:
        """
        同步保存单条消息（线程安全版本）

        Args:
            user_id: 用户标识符
            message: 包含消息内容的字典
            skip_consecutive_check: 是否跳过连续相同角色消息的检查

        Returns:
            保存成功返回True

        Note:
            直接使用threading.Lock，在多线程环境中安全
        """
        try:
            session_id = message.get('session_id', 'default')
            agent_id = message.get('agent_id', 'default')

            content = message.get('content', '')
            msg_id = message.get('id', f'msg_{int(time.time() * 1000000)}')
            timestamp_str = message.get('timestamp')
            
            # 处理时间戳 - 更健壮的方式
            if timestamp_str:
                if isinstance(timestamp_str, (int, float)):
                    try:
                        # 检查时间戳是否在合理范围内
                        # 合理范围：从 1970-01-01 到 未来 100 年
                        current_time = time.time()
                        min_timestamp = 0
                        max_timestamp = current_time + (100 * 365 * 24 * 60 * 60)
                        
                        if min_timestamp <= timestamp_str <= max_timestamp:
                            timestamp = datetime.fromtimestamp(timestamp_str)
                        else:
                            timestamp = datetime.now()
                    except (ValueError, OSError, OverflowError, OSError):
                        # 捕获所有可能的时间戳错误
                        timestamp = datetime.now()
                elif isinstance(timestamp_str, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            # 构造消息字典
            message_dict = {
                'role': 'user',
                'content': content if isinstance(content, list) else [{'text': content}],
                'timestamp': timestamp.isoformat(),
                'id': msg_id,
            }

            # 使用线程锁保护操作（线程安全）
            with self._thread_lock:
                key = self.generate_key(user_id, session_id, agent_id)
                conversation = self.conversations[key]
                
                # 保存消息
                conversation.append(message_dict)
                self.conversations[key] = conversation
                
                # 更新访问时间
                self._entry_access_times[key] = time.time()
                
                # 更新会话信息（使用正确的 # 分隔符，与其他地方保持一致）
                session_key = f"{user_id}#{session_id}"
                self.sessions[session_key] = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'message_count': len(conversation),
                    'metadata': {},
                    'active': True,
                }
                
                return True

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False

    def get_conversation(self, user_id: str, session_id: str = 'default', 
                        agent_id: str = 'default') -> List[Dict[str, Any]]:
        """
        获取对话记录（简化接口）

        Args:
            user_id: 用户标识符
            session_id: 会话标识符（默认 'default'）
            agent_id: Agent标识符（默认 'default'）

        Returns:
            消息字典列表
        """
        key = self.generate_key(user_id, session_id, agent_id)
        return list(self.conversations.get(key, []))

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息（线程安全）"""
        with self._thread_lock:
            return {
                'conversation_count': len(self.conversations),
                'session_count': len(self.sessions),
                'total_messages': sum(len(msgs) for msgs in list(self.conversations.values())),
                'auto_cleanup': self._auto_cleanup,
                'entry_ttl': self._entry_ttl,
            }
