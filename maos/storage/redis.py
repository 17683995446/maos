"""
MAOS Redis存储实现

基于Redis的分布式存储实现，适合生产环境。
支持连接池管理、持久化、TTL过期、分布式部署等功能。

特点：
- 高性能
- 数据持久化
- TTL自动过期
- 连接池管理
- 分布式支持
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
)

if TYPE_CHECKING:
    from ..types import ConversationMessage

from .base import (
    ChatStorage,
    ChatStorageConfig,
    SessionInfo,
    StorageError,
)

logger = logging.getLogger(__name__)

_REDIS_AVAILABLE = False
_redis_error_msg: Optional[str] = None

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool as RedisConnectionPool
    from redis.asyncio import Redis as RedisClient
    _REDIS_AVAILABLE = True
except ImportError as e:
    _redis_error_msg = str(e)
    _REDIS_AVAILABLE = False


if _REDIS_AVAILABLE:
    class RedisChatStorage(ChatStorage):
        def __init__(
            self,
            host: str = "localhost",
            port: int = 6379,
            db: int = 0,
            password: Optional[str] = None,
            key_prefix: str = "maos:chat:",
            session_key_prefix: str = "maos:session:",
            max_connections: int = 50,
            socket_timeout: float = 5.0,
            socket_connect_timeout: float = 5.0,
            config: Optional[ChatStorageConfig] = None,
            decode_responses: bool = True,
        ):
            super().__init__(config)
            self.host = host
            self.port = port
            self.db = db
            self.password = password
            self.key_prefix = key_prefix
            self.session_key_prefix = session_key_prefix
            self.max_connections = max_connections
            self.socket_timeout = socket_timeout
            self.socket_connect_timeout = socket_connect_timeout
            self.decode_responses = decode_responses

            self._pool: Optional[RedisConnectionPool] = None
            self._client: Optional[RedisClient] = None

        async def initialize(self) -> None:
            try:
                self._pool = RedisConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    max_connections=self.max_connections,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_connect_timeout,
                    decode_responses=self.decode_responses,
                )
                self._client = RedisClient(connection_pool=self._pool)
                await self._client.ping()
                await super().initialize()
                logger.info(
                    f"RedisChatStorage initialized: {self.host}:{self.port}/{self.db}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Redis connection: {e}")
                raise StorageError(
                    message=f"Failed to connect to Redis: {e}",
                    operation="initialize",
                    cause=e
                )

        async def close(self) -> None:
            if self._client:
                await self._client.aclose()
                self._client = None
            if self._pool:
                await self._pool.disconnect()
                self._pool = None
            await super().close()
            logger.info("RedisChatStorage closed")

        def _get_chat_key(self, user_id: str, session_id: str, agent_id: str) -> str:
            return f"{self.key_prefix}{user_id}#{session_id}#{agent_id}"

        def _get_session_key(self, user_id: str, session_id: str) -> str:
            return f"{self.session_key_prefix}{user_id}#{session_id}"

        def _get_user_sessions_pattern(self, user_id: str) -> str:
            return f"{self.session_key_prefix}{user_id}#*"

        async def save_chat_message(
            self,
            user_id: str,
            session_id: str,
            agent_id: str,
            new_message: "ConversationMessage",
            max_history_size: Optional[int] = None
        ) -> bool:
            from ..types import ParticipantRole

            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="save_chat_message"
                )

            try:
                key = self._get_chat_key(user_id, session_id, agent_id)
                existing = await self.fetch_chat(user_id, session_id, agent_id)

                if self.is_same_role_as_last_message(existing, new_message):
                    logger.debug(
                        f"Consecutive {new_message.role.value} message detected "
                        f"for agent {agent_id}. Skipping."
                    )
                    return True

                message_dict = self._message_to_dict(new_message)
                serialized = json.dumps(message_dict, default=str)

                pipe = self._client.pipeline()
                pipe.rpush(key, serialized)
                pipe.ltrim(key, -self._get_max_size(max_history_size), -1)

                if self.config.ttl_seconds:
                    pipe.expire(key, self.config.ttl_seconds)

                await pipe.execute()

                await self._update_session(user_id, session_id)

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
            new_messages: List["ConversationMessage"],
            max_history_size: Optional[int] = None
        ) -> bool:
            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="save_chat_messages"
                )

            try:
                key = self._get_chat_key(user_id, session_id, agent_id)
                serialized_messages = [
                    json.dumps(self._message_to_dict(msg), default=str)
                    for msg in new_messages
                ]

                pipe = self._client.pipeline()
                pipe.rpush(key, *serialized_messages)
                pipe.ltrim(key, -self._get_max_size(max_history_size), -1)

                if self.config.ttl_seconds:
                    pipe.expire(key, self.config.ttl_seconds)

                await pipe.execute()

                await self._update_session(user_id, session_id)

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
        ) -> List["ConversationMessage"]:
            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="fetch_chat"
                )

            try:
                key = self._get_chat_key(user_id, session_id, agent_id)

                if max_history_size is not None:
                    effective_max_size = max_history_size
                else:
                    effective_max_size = self.config.max_history_size

                if effective_max_size:
                    start = -effective_max_size
                else:
                    start = 0

                raw_messages = await self._client.lrange(key, start, -1)

                messages = []
                for raw in raw_messages:
                    try:
                        data = json.loads(raw)
                        messages.append(self._dict_to_message(data))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode message: {e}")
                        continue

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
        ) -> List["ConversationMessage"]:
            from ..types import ParticipantRole

            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="fetch_all_chats"
                )

            try:
                pattern = f"{self.key_prefix}{user_id}#{session_id}#*"
                all_messages: List[Dict[str, Any]] = []

                async for key in self._client.scan_iter(match=pattern):
                    raw_messages = await self._client.lrange(key, 0, -1)
                    agent_id = key.split('#')[-1]

                    for raw in raw_messages:
                        try:
                            data = json.loads(raw)
                            data['agent_id'] = agent_id
                            all_messages.append(data)
                        except json.JSONDecodeError:
                            continue

                all_messages.sort(key=lambda x: x.get('timestamp', ''))

                result = []
                for msg_data in all_messages:
                    agent_id = msg_data.pop('agent_id', None)
                    content = msg_data.get('content', [])

                    if isinstance(content, list) and len(content) > 0:
                        if msg_data.get('role') == ParticipantRole.ASSISTANT.value:
                            text_content = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
                            content = [{'text': f"[{agent_id}] {text_content}"}]

                    result.append(self._dict_to_message(msg_data))

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
            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="delete_chat"
                )

            try:
                pipe = self._client.pipeline()

                if agent_id:
                    key = self._get_chat_key(user_id, session_id, agent_id)
                    pipe.delete(key)
                else:
                    pattern = f"{self.key_prefix}{user_id}#{session_id}#*"
                    async for key in self._client.scan_iter(match=pattern):
                        pipe.delete(key)

                session_key = self._get_session_key(user_id, session_id)
                pipe.delete(session_key)

                await pipe.execute()
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
            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="list_sessions"
                )

            try:
                pattern = self._get_user_sessions_pattern(user_id)
                sessions = []

                async for key in self._client.scan_iter(match=pattern):
                    raw_data = await self._client.get(key)
                    if raw_data:
                        try:
                            data = json.loads(raw_data)
                            session_info = SessionInfo.from_dict(data)
                            if active_only and not session_info.active:
                                continue
                            sessions.append(session_info)
                        except json.JSONDecodeError:
                            continue

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
            if not self._client:
                raise StorageError(
                    message="Storage not initialized",
                    operation="get_session_info"
                )

            try:
                key = self._get_session_key(user_id, session_id)
                raw_data = await self._client.get(key)

                if raw_data:
                    data = json.loads(raw_data)
                    return SessionInfo.from_dict(data)
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
            session_id: str
        ) -> None:
            try:
                session_key = self._get_session_key(user_id, session_id)
                now = datetime.now()

                existing = await self.get_session_info(user_id, session_id)

                if existing:
                    session_data = existing.to_dict()
                    session_data['updated_at'] = now.isoformat()
                    session_data['message_count'] = existing.message_count + 1
                else:
                    session_data = {
                        'user_id': user_id,
                        'session_id': session_id,
                        'created_at': now.isoformat(),
                        'updated_at': now.isoformat(),
                        'message_count': 1,
                        'metadata': {},
                        'active': True,
                    }

                serialized = json.dumps(session_data, default=str)
                await self._client.set(
                    session_key,
                    serialized,
                    ex=self.config.ttl_seconds if self.config.ttl_seconds else 86400 * 30
                )

            except Exception as e:
                logger.warning(f"Failed to update session: {e}")

        def _get_max_size(self, max_history_size: Optional[int]) -> int:
            effective_max_size = max_history_size or self.config.max_history_size
            return effective_max_size if effective_max_size else 1000

        def _message_to_dict(self, message: "ConversationMessage") -> Dict[str, Any]:
            return message.to_dict()

        def _dict_to_message(self, data: Dict[str, Any]) -> "ConversationMessage":
            return ConversationMessage.from_dict(data)

        async def health_check(self) -> Dict[str, Any]:
            base_health = await super().health_check()

            if not self._client:
                return {
                    **base_health,
                    'healthy': False,
                    'error': 'Not connected',
                }

            try:
                await self._client.ping()
                info = await self._client.info('memory')

                return {
                    **base_health,
                    'healthy': True,
                    'used_memory': info.get('used_memory_human', 'unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                }
            except Exception as e:
                return {
                    **base_health,
                    'healthy': False,
                    'error': str(e),
                }

        async def get_stats(self) -> Dict[str, Any]:
            if not self._client:
                return {'error': 'Not connected'}

            try:
                pattern = f"{self.key_prefix}*"
                count = 0
                async for _ in self._client.scan_iter(match=pattern):
                    count += 1

                return {
                    'conversation_keys': count,
                }
            except Exception as e:
                return {'error': str(e)}


def get_redis_error_message() -> Optional[str]:
    return _redis_error_msg


def is_redis_available() -> bool:
    return _REDIS_AVAILABLE
