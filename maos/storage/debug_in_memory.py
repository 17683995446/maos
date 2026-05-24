#!/usr/bin/env python3
"""
带详细日志的InMemoryChatStorage调试版本 - 用于发现深层问题
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

# 配置详细日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建文件处理器
file_handler = logging.FileHandler('/tmp/maos_debug_storage.log', mode='w')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(funcName)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


from ..types import ConversationMessage, ParticipantRole
from .base import (
    ChatStorage,
    ChatStorageConfig,
    SessionInfo,
    StorageError,
)


class DebugInMemoryChatStorage(ChatStorage):
    """带详细日志的内存聊天存储 - 线程安全版本"""
    
    def __init__(
        self,
        config: Optional[ChatStorageConfig] = None,
        auto_cleanup: bool = True,
        cleanup_interval: int = 300,
        entry_ttl: Optional[int] = None,
    ):
        logger.debug(f"[DEBUG] __init__ 开始 - config={config}, auto_cleanup={auto_cleanup}, cleanup_interval={cleanup_interval}, entry_ttl={entry_ttl}")
        super().__init__(config)
        logger.debug(f"[DEBUG] __init__: super().__init__ 完成")
        
        self.conversations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        logger.debug(f"[DEBUG] __init__: conversations 初始化完成")
        
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.debug(f"[DEBUG] __init__: sessions 初始化完成")
        
        self._lock = asyncio.Lock()
        logger.debug(f"[DEBUG] __init__: asyncio.Lock 创建完成")
        
        self._thread_lock = threading.Lock()  # 线程锁，用于同步操作
        logger.debug(f"[DEBUG] __init__: threading.Lock 创建完成")
        
        self._cleanup_task: Optional[asyncio.Task] = None
        logger.debug(f"[DEBUG] __init__: _cleanup_task 初始化完成")
        
        self._auto_cleanup = auto_cleanup
        self._cleanup_interval = cleanup_interval
        self._entry_ttl = entry_ttl
        logger.debug(f"[DEBUG] __init__: 清理配置设置完成 - auto_cleanup={auto_cleanup}")
        
        self._entry_access_times: Dict[str, float] = {}
        logger.debug(f"[DEBUG] __init__: _entry_access_times 初始化完成")
        
        self._operation_count = 0
        logger.debug(f"[DEBUG] __init__: _operation_count 初始化完成")
        
        logger.debug(f"[DEBUG] __init__ 完成 - DebugInMemoryChatStorage 实例创建成功")
    
    async def initialize(self) -> None:
        logger.debug(f"[DEBUG] initialize 开始")
        await super().initialize()
        if self._auto_cleanup and self._entry_ttl is not None:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
            logger.debug(f"[DEBUG] initialize: _cleanup_task 创建并启动")
        logger.debug(f"[DEBUG] initialize 完成")
    
    async def close(self) -> None:
        logger.debug(f"[DEBUG] close 开始")
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.debug(f"[DEBUG] close: _cleanup_task 取消成功")
        await super().close()
        logger.debug(f"[DEBUG] close 完成")
    
    def generate_key(self, user_id: str, session_id: str, agent_id: str) -> str:
        key = f"{user_id}:{session_id}:{agent_id}"
        logger.debug(f"[DEBUG] generate_key: user_id={user_id}, session_id={session_id}, agent_id={agent_id} -> key={key}")
        return key
    
    def _update_access_time(self, key: str) -> None:
        self._entry_access_times[key] = time.time()
        logger.debug(f"[DEBUG] _update_access_time: key={key}, access_time={self._entry_access_times[key]}")
    
    async def _update_session(self, user_id: str, session_id: str, message_count: int) -> None:
        session_key = f"{user_id}:{session_id}"
        self.sessions[session_key] = {
            'user_id': user_id,
            'session_id': session_id,
            'last_updated': datetime.now().isoformat(),
            'message_count': message_count
        }
        logger.debug(f"[DEBUG] _update_session: session_key={session_key}, message_count={message_count}")
    
    async def _auto_cleanup_loop(self) -> None:
        logger.debug(f"[DEBUG] _auto_cleanup_loop 开始")
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                logger.debug(f"[DEBUG] _auto_cleanup_loop: 执行清理")
            except asyncio.CancelledError:
                logger.debug(f"[DEBUG] _auto_cleanup_loop: 任务取消")
                break
            except Exception as e:
                logger.error(f"[DEBUG] _auto_cleanup_loop: 错误 - {type(e).__name__}: {str(e)}")
                break
    
    async def save_chat_message(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        new_message: ConversationMessage,
        max_history_size: Optional[int] = None,
    ) -> bool:
        logger.debug(f"[DEBUG] save_chat_message 开始 - user_id={user_id}, session_id={session_id}, agent_id={agent_id}, message.id={new_message.id}")
        try:
            async with self._lock:
                key = self.generate_key(user_id, session_id, agent_id)
                conversation = self.conversations[key]
                
                message_dict = {
                    'role': new_message.role.value,
                    'content': self._serialize_content(new_message.content),
                    'timestamp': new_message.timestamp.isoformat(),
                    'id': new_message.id,
                }
                
                conversation.append(message_dict)
                
                # 裁剪到指定大小
                if max_history_size:
                    conversation = self.trim_conversation(conversation, max_history_size)
                
                self.conversations[key] = conversation
                self._update_access_time(key)
                await self._update_session(user_id, session_id, len(conversation))
                logger.debug(f"[DEBUG] save_chat_message: 成功保存 - conversation_len={len(conversation)}")
                return True
        except Exception as e:
            logger.error(f"[DEBUG] save_chat_message: 错误 - {type(e).__name__}: {str(e)}", exc_info=True)
            return False
    
    async def fetch_chat(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        max_history_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        logger.debug(f"[DEBUG] fetch_chat 开始 - user_id={user_id}, session_id={session_id}, agent_id={agent_id}, max_history_size={max_history_size}")
        try:
            async with self._lock:
                key = self.generate_key(user_id, session_id, agent_id)
                messages = list(self.conversations.get(key, []))
                
                if max_history_size:
                    messages = self.trim_conversation(messages, max_history_size)
                
                self._update_access_time(key)
                logger.debug(f"[DEBUG] fetch_chat: 成功 - 消息数={len(messages)}")
                return messages
        except Exception as e:
            logger.error(f"[DEBUG] fetch_chat: 错误 - {type(e).__name__}: {str(e)}", exc_info=True)
            return []
    
    async def fetch_all_chats(
        self,
        user_id: str,
        session_id: str,
    ) -> List[Dict[str, Any]]:
        logger.debug(f"[DEBUG] fetch_all_chats 开始 - user_id={user_id}, session_id={session_id}")
        try:
            async with self._lock:
                all_messages = []
                
                # 收集所有Agent的消息
                for key in self.conversations.keys():
                    key_parts = self.parse_key(key)
                    if key_parts['user_id'] == user_id and key_parts['session_id'] == session_id:
                        all_messages.extend(self.conversations[key])
                
                # 按时间排序
                all_messages.sort(key=lambda msg: msg.get('timestamp', ''))
                
                logger.debug(f"[DEBUG] fetch_all_chats: 成功 - 总消息数={len(all_messages)}")
                return all_messages
        except Exception as e:
            logger.error(f"[DEBUG] fetch_all_chats: 错误 - {type(e).__name__}: {str(e)}", exc_info=True)
            return []
    
    async def get_session_info(
        self,
        user_id: str,
        session_id: str,
    ) -> Optional[SessionInfo]:
        logger.debug(f"[DEBUG] get_session_info 开始 - user_id={user_id}, session_id={session_id}")
        try:
            async with self._lock:
                session_key = f"{user_id}:{session_id}"
                if session_key in self.sessions:
                    data = self.sessions[session_key]
                    logger.debug(f"[DEBUG] get_session_info: 成功 - data={data}")
                    return SessionInfo(
                        user_id=data['user_id'],
                        session_id=data['session_id'],
                        agent_id=data.get('agent_id', 'default'),
                        last_updated=datetime.fromisoformat(data['last_updated']),
                        message_count=data['message_count']
                    )
                else:
                    logger.debug(f"[DEBUG] get_session_info: 会话不存在")
                    return None
        except Exception as e:
            logger.error(f"[DEBUG] get_session_info: 错误 - {type(e).__name__}: {str(e)}", exc_info=True)
            return None
    
    async def list_sessions(
        self,
        user_id: str,
    ) -> List[str]:
        logger.debug(f"[DEBUG] list_sessions 开始 - user_id={user_id}")
        try:
            async with self._lock:
                sessions = [
                    sid.split(':')[1]
                    for sid in self.sessions.keys()
                    if sid.startswith(f"{user_id}:")
                ]
                logger.debug(f"[DEBUG] list_sessions: 成功 - 会话数={len(sessions)}")
                return sessions
        except Exception as e:
            logger.error(f"[DEBUG] list_sessions: 错误 - {type(e).__name__}: {str(e)}", exc_info=True)
            return []
    
    async def delete_conversation(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
    ) -> bool:
        logger.debug(f"[DEBUG] delete_conversation 开始 - user_id={user_id}, session_id={session_id}, agent_id={agent_id}")
        try:
            async with self._lock:
                key = self.generate_key(user_id, session_id, agent_id)
                if key in self.conversations:
                    del self.conversations[key]
                    session_key = f"{user_id}:{session_id}"
                    if session_key in self.sessions:
                        del self.sessions[session_key]
                    if key in self._entry_access_times:
                        del self._entry_access_times[key]
                    logger.debug(f"[DEBUG] delete_conversation: 成功删除")
                    return True
                return False
        except Exception as e:
            logger.error(f"[DEBUG] delete_conversation: 错误 - {type(e).__name__}: {str(e)}", exc_info=True)
            return False
    
    def clear_all(self) -> None:
        logger.debug(f"[DEBUG] clear_all 开始")
        with self._thread_lock:
            self.conversations.clear()
            logger.debug(f"[DEBUG] clear_all: conversations 清空")
            self.sessions.clear()
            logger.debug(f"[DEBUG] clear_all: sessions 清空")
            self._entry_access_times.clear()
            logger.debug(f"[DEBUG] clear_all: _entry_access_times 清空")
        logger.debug(f"[DEBUG] clear_all 完成")
    
    def _serialize_content(self, content: Any) -> Any:
        logger.debug(f"[DEBUG] _serialize_content 开始 - content_type={type(content)}")
        return content
    
    def save_message(self, user_id: str, message: Dict[str, Any], skip_consecutive_check: bool = True) -> bool:
        """
        同步保存单条消息（线程安全版本，带详细日志）
        """
        logger.debug(f"[DEBUG] save_message 开始 - user_id={user_id}, message.keys()={list(message.keys())}, skip_consecutive_check={skip_consecutive_check}")
        self._operation_count += 1
        
        try:
            logger.debug(f"[DEBUG] save_message: 第{self._operation_count}次操作")
            
            session_id = message.get('session_id', 'default')
            logger.debug(f"[DEBUG] save_message: session_id={session_id}")
            
            agent_id = message.get('agent_id', 'default')
            logger.debug(f"[DEBUG] save_message: agent_id={agent_id}")
            
            content = message.get('content', '')
            logger.debug(f"[DEBUG] save_message: content={content[:50] if isinstance(content, str) else type(content)}")
            
            msg_id = message.get('id', f'msg_{int(time.time() * 1000000)}')
            logger.debug(f"[DEBUG] save_message: msg_id={msg_id}")
            
            timestamp_str = message.get('timestamp')
            logger.debug(f"[DEBUG] save_message: timestamp_str={timestamp_str}")
            
            # 处理时间戳
            if timestamp_str:
                logger.debug(f"[DEBUG] save_message: 处理时间戳")
                if isinstance(timestamp_str, (int, float)):
                    try:
                        timestamp = datetime.fromtimestamp(timestamp_str)
                        logger.debug(f"[DEBUG] save_message: 时间戳转换成功 - {timestamp}")
                    except (ValueError, OSError):
                        logger.warning(f"[DEBUG] save_message: 时间戳转换失败，使用当前时间")
                        timestamp = datetime.now()
                else:
                    logger.debug(f"[DEBUG] save_message: timestamp_str不是数字，使用当前时间")
                    timestamp = datetime.now()
            else:
                logger.debug(f"[DEBUG] save_message: timestamp_str为空，使用当前时间")
                timestamp = datetime.now()
            
            # 构造消息字典
            logger.debug(f"[DEBUG] save_message: 构造消息字典")
            message_dict = {
                'role': 'user',
                'content': content if isinstance(content, list) else [{'text': content}],
                'timestamp': timestamp.isoformat(),
                'id': msg_id,
            }
            logger.debug(f"[DEBUG] save_message: message_dict构造完成")
            
            # 使用线程锁保护操作（线程安全）
            logger.debug(f"[DEBUG] save_message: 准备获取线程锁")
            with self._thread_lock:
                logger.debug(f"[DEBUG] save_message: 获取线程锁成功")
                
                key = self.generate_key(user_id, session_id, agent_id)
                logger.debug(f"[DEBUG] save_message: key={key}")
                
                conversation = self.conversations[key]
                logger.debug(f"[DEBUG] save_message: 读取conversation - 原长度={len(conversation)}")
                
                # 保存消息
                conversation.append(message_dict)
                logger.debug(f"[DEBUG] save_message: 添加消息到conversation - 新长度={len(conversation)}")
                
                self.conversations[key] = conversation
                logger.debug(f"[DEBUG] save_message: 重新赋值conversations[key]")
                
                # 更新访问时间
                self._update_access_time(key)
                logger.debug(f"[DEBUG] save_message: 更新访问时间完成")
                
                # 更新会话信息（同步版本，避免async）
                session_key = f"{user_id}:{session_id}"
                logger.debug(f"[DEBUG] save_message: session_key={session_key}")
                
                self.sessions[session_key] = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'last_updated': datetime.now().isoformat(),
                    'message_count': len(conversation),
                    'agent_id': agent_id
                }
                logger.debug(f"[DEBUG] save_message: 会话信息更新完成 - message_count={len(conversation)}")
                
                logger.debug(f"[DEBUG] save_message: 准备释放线程锁")
            
            logger.debug(f"[DEBUG] save_message: 线程锁已释放")
            logger.debug(f"[DEBUG] save_message 成功完成 - 第{self._operation_count}次操作")
            return True
            
        except Exception as e:
            logger.error(f"[DEBUG] save_message 错误 - 第{self._operation_count}次操作 - {type(e).__name__}: {str(e)}", exc_info=True)
            return False
    
    def get_conversation(self, user_id: str, session_id: str = 'default', 
                       agent_id: str = 'default') -> List[Dict[str, Any]]:
        """获取对话记录（简化接口，带详细日志）"""
        logger.debug(f"[DEBUG] get_conversation 开始 - user_id={user_id}, session_id={session_id}, agent_id={agent_id}")
        key = self.generate_key(user_id, session_id, agent_id)
        result = list(self.conversations.get(key, []))
        logger.debug(f"[DEBUG] get_conversation 完成 - key={key}, result_len={len(result)}")
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息（带详细日志）"""
        logger.debug(f"[DEBUG] get_stats 开始")
        stats = {
            'conversation_count': len(self.conversations),
            'session_count': len(self.sessions),
            'total_messages': sum(len(msgs) for msgs in self.conversations.values()),
            'auto_cleanup': self._auto_cleanup,
            'entry_ttl': self._entry_ttl,
            'operation_count': self._operation_count,
        }
        logger.debug(f"[DEBUG] get_stats 完成 - stats={stats}")
        return stats
