"""
Conversation Types - 对话消息类型定义
定义多Agent系统中的对话消息结构

设计要点：
- 与Legacy版本的AgentMessage兼容
- 支持流式响应
- 支持多轮对话
- 支持元数据和标签
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class ParticipantRole(Enum):
    """
    参与者角色枚举

    定义对话中不同参与者的角色类型
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"
    TOOL = "tool"
    FUNCTION = "function"


class MessageContentType(Enum):
    """
    消息内容类型枚举

    定义消息内容的不同类型
    """
    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    STREAMING = "streaming"
    ERROR = "error"
    CODE = "code"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class StreamingStatus(Enum):
    """
    流式响应状态枚举

    定义流式响应的不同状态
    """
    START = "start"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class MessageContent:
    """
    消息内容数据类

    表示对话消息的具体内容，支持多种内容类型

    Attributes:
        content_type: 消息内容类型
        text: 文本内容
        image_url: 图片URL
        image_base64: Base64编码的图片
        tool_call: 工具调用信息
        tool_result: 工具执行结果
        function_call: 函数调用信息
        function_result: 函数执行结果
        metadata: 内容的额外元数据
    """
    content_type: MessageContentType = MessageContentType.TEXT
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    tool_call: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    function_call: Optional[Dict[str, Any]] = None
    function_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典

        Returns:
            Dict[str, Any]: 消息内容的字典表示
        """
        return {
            'content_type': self.content_type.value,
            'text': self.text,
            'image_url': self.image_url,
            'image_base64': self.image_base64,
            'tool_call': self.tool_call,
            'tool_result': self.tool_result,
            'function_call': self.function_call,
            'function_result': self.function_result,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageContent':
        """
        从字典反序列化

        Args:
            data: 字典数据

        Returns:
            MessageContent: 消息内容实例
        """
        if 'content_type' in data and isinstance(data['content_type'], str):
            data['content_type'] = MessageContentType(data['content_type'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def create_text(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> 'MessageContent':
        """
        创建文本消息

        Args:
            text: 文本内容
            metadata: 额外元数据

        Returns:
            MessageContent: 文本消息实例
        """
        return cls(content_type=MessageContentType.TEXT, text=text, metadata=metadata or {})

    @classmethod
    def create_image_url(cls, url: str, metadata: Optional[Dict[str, Any]] = None) -> 'MessageContent':
        """
        创建图片URL消息

        Args:
            url: 图片URL
            metadata: 额外元数据

        Returns:
            MessageContent: 图片URL消息实例
        """
        return cls(content_type=MessageContentType.IMAGE_URL, image_url=url, metadata=metadata or {})

    @classmethod
    def create_tool_call(
        cls,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'MessageContent':
        """
        创建工具调用消息

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            tool_id: 工具调用ID
            metadata: 额外元数据

        Returns:
            MessageContent: 工具调用消息实例
        """
        return cls(
            content_type=MessageContentType.TOOL_USE,
            tool_call={
                'id': tool_id or str(uuid.uuid4()),
                'name': tool_name,
                'input': tool_input
            },
            metadata=metadata or {}
        )

    @classmethod
    def create_tool_result(
        cls,
        tool_call_id: str,
        result: Any,
        is_error: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'MessageContent':
        """
        创建工具执行结果消息

        Args:
            tool_call_id: 工具调用ID
            result: 执行结果
            is_error: 是否为错误结果
            metadata: 额外元数据

        Returns:
            MessageContent: 工具结果消息实例
        """
        return cls(
            content_type=MessageContentType.TOOL_RESULT,
            tool_result={
                'tool_use_id': tool_call_id,
                'content': result,
                'is_error': is_error
            },
            metadata=metadata or {}
        )


@dataclass
class ConversationMessage:
    """
    对话消息数据类

    表示对话中的单条消息，支持与Legacy版本的AgentMessage兼容

    Attributes:
        id: 消息唯一标识符
        role: 消息发送者角色
        content: 消息内容（可以是字符串或MessageContent列表）
        sender: 发送者名称
        receivers: 接收者名称列表
        timestamp: 消息时间戳
        metadata: 消息元数据
        tags: 消息标签
        conversation_id: 所属对话ID
        parent_id: 父消息ID（用于多轮对话）
        streaming: 是否为流式响应
        streaming_status: 流式响应状态
        is_final: 是否为最终消息
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: ParticipantRole = ParticipantRole.USER
    content: Union[str, List[MessageContent], MessageContent] = ""
    sender: str = ""
    receivers: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    conversation_id: Optional[str] = None
    parent_id: Optional[str] = None
    streaming: bool = False
    streaming_status: Optional[StreamingStatus] = None
    is_final: bool = True

    def __post_init__(self):
        """初始化后的处理"""
        if isinstance(self.role, str):
            self.role = ParticipantRole(self.role)

    def get_text_content(self) -> str:
        """
        获取文本内容

        Returns:
            str: 文本内容
        """
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            text_parts = []
            for item in self.content:
                if isinstance(item, MessageContent):
                    if item.text:
                        text_parts.append(item.text)
                    elif item.tool_result:
                        text_parts.append(str(item.tool_result.get('content', '')))
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            return '\n'.join(text_parts)
        elif isinstance(self.content, MessageContent):
            return self.content.text or str(self.content.tool_result or '')
        return str(self.content)

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典

        Returns:
            Dict[str, Any]: 消息的字典表示
        """
        content_data = self.content
        if isinstance(self.content, list):
            content_data = [
                msg.to_dict() if isinstance(msg, MessageContent) else msg
                for msg in self.content
            ]
        elif isinstance(self.content, MessageContent):
            content_data = self.content.to_dict()

        return {
            'id': self.id,
            'role': self.role.value,
            'content': content_data,
            'sender': self.sender,
            'receivers': self.receivers,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags,
            'conversation_id': self.conversation_id,
            'parent_id': self.parent_id,
            'streaming': self.streaming,
            'streaming_status': self.streaming_status.value if self.streaming_status else None,
            'is_final': self.is_final
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """
        从字典反序列化

        Args:
            data: 字典数据

        Returns:
            ConversationMessage: 对话消息实例
        """
        data = data.copy()

        if 'role' in data and isinstance(data['role'], str):
            data['role'] = ParticipantRole(data['role'])

        if 'content' in data and isinstance(data['content'], list):
            data['content'] = [
                MessageContent.from_dict(item) if isinstance(item, dict) else item
                for item in data['content']
            ]
        elif 'content' in data and isinstance(data['content'], dict):
            data['content'] = MessageContent.from_dict(data['content'])

        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        if 'streaming_status' in data and data['streaming_status']:
            data['streaming_status'] = StreamingStatus(data['streaming_status'])

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_legacy_format(self) -> Dict[str, Any]:
        """
        转换为Legacy格式（兼容AgentMessage）

        Returns:
            Dict[str, Any]: Legacy格式的消息
        """
        return {
            'id': self.id,
            'sender': self.sender,
            'receivers': self.receivers,
            'msg_type': 'response' if self.role == ParticipantRole.ASSISTANT else 'request',
            'content': self.get_text_content(),
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'reply_to': self.parent_id
        }

    @classmethod
    def from_legacy_format(cls, legacy_data: Dict[str, Any]) -> 'ConversationMessage':
        """
        从Legacy格式转换

        Args:
            legacy_data: Legacy格式的数据

        Returns:
            ConversationMessage: 对话消息实例
        """
        msg_type = legacy_data.get('msg_type', 'request')
        role = ParticipantRole.USER if msg_type == 'request' else ParticipantRole.ASSISTANT

        return cls(
            id=legacy_data.get('id', str(uuid.uuid4())),
            role=role,
            content=legacy_data.get('content', ''),
            sender=legacy_data.get('sender', ''),
            receivers=legacy_data.get('receivers', []),
            timestamp=datetime.fromisoformat(legacy_data['timestamp']) if 'timestamp' in legacy_data else datetime.now(),
            metadata=legacy_data.get('metadata', {}),
            parent_id=legacy_data.get('reply_to')
        )


@dataclass
class StreamingChunk:
    """
    流式响应数据块

    表示流式响应中的单个数据块

    Attributes:
        message_id: 所属消息ID
        chunk_index: 块索引
        content: 块内容
        is_final: 是否为最后一个块
        status: 流状态
        timestamp: 块时间戳
        metadata: 额外元数据
    """
    message_id: str
    chunk_index: int
    content: str = ""
    is_final: bool = False
    status: StreamingStatus = StreamingStatus.IN_PROGRESS
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典

        Returns:
            Dict[str, Any]: 块数据的字典表示
        """
        return {
            'message_id': self.message_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'is_final': self.is_final,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ConversationTurn:
    """
    对话回合

    表示多轮对话中的一个完整回合（用户输入 + Agent响应）

    Attributes:
        id: 回合唯一标识符
        conversation_id: 所属对话ID
        user_message: 用户消息
        assistant_message: Agent响应消息
        tool_calls: 工具调用列表
        tool_results: 工具执行结果列表
        timestamp: 回合时间戳
        duration_ms: 响应耗时（毫秒）
        metadata: 额外元数据
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    user_message: Optional[ConversationMessage] = None
    assistant_message: Optional[ConversationMessage] = None
    tool_calls: List[ConversationMessage] = field(default_factory=list)
    tool_results: List[ConversationMessage] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_all_messages(self) -> List[ConversationMessage]:
        """
        获取回合中的所有消息

        Returns:
            List[ConversationMessage]: 所有消息列表
        """
        messages = []
        if self.user_message:
            messages.append(self.user_message)
        messages.extend(self.tool_calls)
        messages.extend(self.tool_results)
        if self.assistant_message:
            messages.append(self.assistant_message)
        return messages

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典

        Returns:
            Dict[str, Any]: 回合数据的字典表示
        """
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_message': self.user_message.to_dict() if self.user_message else None,
            'assistant_message': self.assistant_message.to_dict() if self.assistant_message else None,
            'tool_calls': [msg.to_dict() for msg in self.tool_calls],
            'tool_results': [msg.to_dict() for msg in self.tool_results],
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms,
            'metadata': self.metadata
        }


@dataclass
class ConversationContext:
    """
    对话上下文

    存储和管理多轮对话的上下文信息

    Attributes:
        conversation_id: 对话唯一标识符
        messages: 消息历史
        turns: 对话回合列表
        current_turn_index: 当前回合索引
        metadata: 对话元数据
        tags: 对话标签
        created_at: 创建时间
        updated_at: 最后更新时间
        system_prompt: 系统提示
        max_turns: 最大回合数
    """
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ConversationMessage] = field(default_factory=list)
    turns: List[ConversationTurn] = field(default_factory=list)
    current_turn_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    system_prompt: Optional[str] = None
    max_turns: Optional[int] = None

    def add_message(self, message: ConversationMessage) -> None:
        """
        添加消息到上下文

        Args:
            message: 要添加的消息
        """
        message.conversation_id = self.conversation_id
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages_by_role(
        self,
        role: ParticipantRole,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        获取指定角色的消息

        Args:
            role: 角色类型
            limit: 返回数量限制

        Returns:
            List[ConversationMessage]: 消息列表
        """
        messages = [msg for msg in self.messages if msg.role == role]
        if limit:
            messages = messages[-limit:]
        return messages

    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        """
        获取最近的消息

        Args:
            count: 消息数量

        Returns:
            List[ConversationMessage]: 最近的消息列表
        """
        return self.messages[-count:] if count > 0 else self.messages

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典

        Returns:
            Dict[str, Any]: 上下文数据的字典表示
        """
        return {
            'conversation_id': self.conversation_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'turns': [turn.to_dict() for turn in self.turns],
            'current_turn_index': self.current_turn_index,
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'system_prompt': self.system_prompt,
            'max_turns': self.max_turns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """
        从字典反序列化

        Args:
            data: 字典数据

        Returns:
            ConversationContext: 对话上下文实例
        """
        data = data.copy()

        if 'messages' in data:
            data['messages'] = [
                ConversationMessage.from_dict(msg) if isinstance(msg, dict) else msg
                for msg in data['messages']
            ]

        if 'turns' in data:
            data['turns'] = [
                ConversationTurn(**turn) if isinstance(turn, dict) else turn
                for turn in data['turns']
            ]

        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])

        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


type StreamingCallback = Callable[[StreamingChunk], None]

type MessageHandler = Callable[[ConversationMessage], Optional[ConversationMessage]]

type ContentFormatter = Callable[[MessageContent], str]
