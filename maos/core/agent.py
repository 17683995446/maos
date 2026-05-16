"""
MAOS Core Agent Module
MAOS系统的核心Agent模块

提供Agent基类、消息类型、状态管理和事件系统。
融合了Legacy版本的简洁设计和AWS Agent Squad的现代架构。

主要特性：
- 异步消息处理
- 消息队列管理
- 状态机管理
- 能力注册系统
- 事件发射机制
- 流式响应支持
"""

from __future__ import annotations

import asyncio
import re
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Callable,
    Deque,
    Dict,
    List,
    Optional,
    TypeAlias,
    Union,
)
from uuid import UUID

from .callbacks import AgentCallbacks


class AgentStatus(Enum):
    """
    Agent生命周期状态枚举

    状态转换：
    IDLE -> BUSY (开始处理任务)
    BUSY -> IDLE (任务完成)
    BUSY -> ERROR (处理失败)
    ERROR -> IDLE (错误恢复)
    IDLE -> TERMINATED (关闭)
    """

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class MessageType(Enum):
    """
    Agent间通信消息类型枚举

    支持的消息类型：
    - REQUEST: 请求消息，需要响应
    - RESPONSE: 响应消息
    - BROADCAST: 广播消息，发送给所有Agent
    - HEARTBEAT: 心跳消息，用于健康检查
    - ERROR: 错误消息
    - STREAM: 流式消息片段
    """

    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    STREAM = "stream"


@dataclass
class AgentMessage:
    """
    Agent间通信消息数据类

    包含消息的完整元数据，用于Agent间的异步通信。
    支持序列化/反序列化，便于消息持久化和传输。

    属性：
        id: 消息唯一标识符
        sender: 发送者名称
        receivers: 接收者名称列表
        msg_type: 消息类型
        content: 消息内容
        metadata: 附加元数据
        timestamp: 消息时间戳
        reply_to: 关联的原始消息ID
        correlation_id: 关联ID，用于追踪相关消息
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receivers: List[str] = field(default_factory=list)
    msg_type: MessageType = MessageType.REQUEST
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典

        返回：
            包含所有消息字段的字典
        """
        return {
            'id': self.id,
            'sender': self.sender,
            'receivers': self.receivers,
            'msg_type': self.msg_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'reply_to': self.reply_to,
            'correlation_id': self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """
        从字典反序列化

        参数：
            data: 消息数据字典

        返回：
            AgentMessage实例
        """
        data = data.copy()
        data['msg_type'] = MessageType(data.get('msg_type', 'request'))
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def create_response(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AgentMessage':
        """
        创建响应消息

        参数：
            content: 响应内容
            metadata: 可选的附加元数据

        返回：
            新的AgentMessage实例作为响应
        """
        return AgentMessage(
            sender=self.sender,
            receivers=[self.sender] if self.sender else [],
            msg_type=MessageType.RESPONSE,
            content=content,
            reply_to=self.id,
            correlation_id=self.correlation_id,
            metadata=metadata or {}
        )


AgentParamsType: TypeAlias = Dict[str, Any]


@dataclass
class AgentStreamResponse:
    """
    流式响应数据类

    用于表示Agent的流式输出片段，包含文本、思考过程和最终消息。

    属性：
        text: 当前流中的文本片段
        thinking: 思考过程片段（如果支持）
        final_message: 流完成时的完整消息
        final_thinking: 最终思考内容
    """

    text: str = ""
    thinking: Optional[str] = ""
    final_message: Optional[Any] = None
    final_thinking: Optional[str] = None


@dataclass
class AgentProcessingResult:
    """
    Agent处理结果元数据

    包含一次Agent处理会话的完整元数据信息。

    属性：
        user_input: 用户原始输入
        agent_id: Agent唯一标识
        agent_name: Agent显示名称
        user_id: 用户标识
        session_id: 会话标识
        additional_params: 附加参数
        start_time: 处理开始时间
        end_time: 处理结束时间
        error: 错误信息（如果有）
    """

    user_input: str
    agent_id: str
    agent_name: str
    user_id: str
    session_id: str
    additional_params: AgentParamsType = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class AgentResponse:
    """
    Agent完整响应数据类

    包含Agent处理的完整输出和元数据。

    属性：
        metadata: 处理元数据
        output: 实际输出内容
        streaming: 是否为流式响应
    """

    metadata: AgentProcessingResult
    output: Union[str, AgentStreamResponse, Any]
    streaming: bool


@dataclass
class AgentEvent:
    """
    Agent事件数据类

    用于封装Agent系统中的事件。
    """

    event_type: str
    agent_name: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


EventHandler: TypeAlias = Callable[[AgentEvent], Any]


@dataclass
class AgentOptions:
    """
    Agent配置选项

    定义创建Agent实例时的配置参数。

    属性：
        name: Agent显示名称
        description: Agent功能描述
        capabilities: Agent能力列表
        save_chat: 是否保存对话历史
        callbacks: 回调处理器实例
        log_debug_trace: 是否启用调试追踪
        max_queue_size: 消息队列最大长度
        processing_timeout: 处理超时时间（秒）
    """

    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    save_chat: bool = True
    callbacks: Optional[AgentCallbacks] = None
    log_debug_trace: Optional[bool] = False
    max_queue_size: int = 1000
    processing_timeout: Optional[float] = None


class Agent(ABC):
    """
    Agent抽象基类

    定义所有Agent必须实现的接口和提供的基础功能。
    支持异步消息处理、事件系统、流式响应等现代特性。

    子类必须实现：
        - process_request(): 处理用户请求的核心方法
        - _process_message_impl(): 具体的消息处理逻辑

    示例：
        class MyAgent(Agent):
            def __init__(self):
                super().__init__(AgentOptions(
                    name="my_agent",
                    description="我的自定义Agent",
                    capabilities=["analysis", "reporting"]
                ))

            async def process_request(self, ...):
                # 实现具体逻辑
                pass
    """

    def __init__(self, options: AgentOptions):
        """
        初始化Agent实例

        参数：
            options: Agent配置选项
        """
        self.name = options.name
        self.id = self.generate_key_from_name(options.name)
        self.description = options.description
        self.capabilities: List[str] = list(options.capabilities)
        self.status: AgentStatus = AgentStatus.IDLE
        self.save_chat = options.save_chat
        self.callbacks = (
            options.callbacks if options.callbacks is not None else AgentCallbacks()
        )
        self.log_debug_trace = options.log_debug_trace

        self.message_queue: Deque[AgentMessage] = deque(maxlen=options.max_queue_size)
        self.processing_timeout = options.processing_timeout

        self._event_handlers: Dict[str, List[EventHandler]] = {
            'message_received': [],
            'message_processed': [],
            'status_changed': [],
            'error': [],
            'task_started': [],
            'task_completed': [],
        }

        self._lock = asyncio.Lock()
        self._processing = False

    @staticmethod
    def generate_key_from_name(name: str) -> str:
        """
        从显示名称生成标准化的唯一键

        参数：
            name: Agent显示名称

        返回：
            小写、连字符分隔的键名
        """
        key = re.sub(r"[^a-zA-Z0-9\s-]", "", name)
        key = re.sub(r"\s+", "-", key)
        return key.lower()

    def is_streaming_enabled(self) -> bool:
        """
        检查是否启用了流式响应

        返回：
            如果支持流式响应返回True
        """
        return False

    def has_capability(self, capability: str) -> bool:
        """
        检查Agent是否具有指定能力

        参数：
            capability: 能力标识符

        返回：
            是否具有该能力
        """
        return capability in self.capabilities

    def add_capability(self, capability: str) -> None:
        """
        添加能力

        参数：
            capability: 能力标识符
        """
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def remove_capability(self, capability: str) -> None:
        """
        移除能力

        参数：
            capability: 能力标识符
        """
        if capability in self.capabilities:
            self.capabilities.remove(capability)

    def can_handle_task(self, task_requirements: List[str]) -> bool:
        """
        检查Agent是否能处理任务

        参数：
            task_requirements: 任务需求列表

        返回：
            是否具备所有必需能力
        """
        return all(self.has_capability(req) for req in task_requirements)

    def update_status(self, status: AgentStatus) -> None:
        """
        更新Agent状态

        参数：
            status: 新的状态值
        """
        if self.status != status:
            old_status = self.status
            self.status = status
            self._emit_event('status_changed', {
                'old_status': old_status.value,
                'new_status': status.value,
                'agent': self.name
            })

    def on_event(self, event_type: str, handler: EventHandler) -> None:
        """
        注册事件处理器

        参数：
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].append(handler)

    def off_event(self, event_type: str, handler: EventHandler) -> None:
        """
        取消注册事件处理器

        参数：
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        发射事件

        参数：
            event_type: 事件类型
            data: 事件数据
        """
        if event_type in self._event_handlers:
            event = AgentEvent(
                event_type=event_type,
                agent_name=self.name,
                data=data
            )
            for handler in self._event_handlers[event_type]:
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        asyncio.create_task(result)
                except Exception as e:
                    self.log_error(f"Error in event handler: {e}")

    async def send_message(self, message: AgentMessage) -> None:
        """
        发送消息到队列

        参数：
            message: 要发送的消息
        """
        message.sender = self.name
        async with self._lock:
            self.message_queue.append(message)
        self._emit_event('message_received', {'message': message.to_dict()})

    def receive_message(self, message: AgentMessage) -> None:
        """
        接收消息到队列

        参数：
            message: 接收到的消息
        """
        self.message_queue.append(message)
        self._emit_event('message_received', {'message': message.to_dict()})

    async def process_message_async(self, message: AgentMessage) -> AgentMessage:
        """
        异步处理单条消息

        参数：
            message: 要处理的消息

        返回：
            响应消息
        """
        self.update_status(AgentStatus.BUSY)
        self._emit_event('task_started', {'message_id': message.id})

        try:
            tracking_info = await self.callbacks.on_agent_start(
                agent_name=self.name,
                payload_input=message.content,
                messages=[message.to_dict()],
                metadata={'message_id': message.id}
            )

            if self.processing_timeout:
                response = await asyncio.wait_for(
                    self._process_message_impl(message),
                    timeout=self.processing_timeout
                )
            else:
                response = await self._process_message_impl(message)

            await self.callbacks.on_agent_end(
                agent_name=self.name,
                response=response.content if isinstance(response, AgentMessage) else response,
                messages=[message.to_dict()],
                metadata={'message_id': message.id, 'agent_tracking_info': tracking_info}
            )

            self._emit_event('message_processed', {
                'message_id': message.id,
                'response': response.to_dict() if isinstance(response, AgentMessage) else None
            })

            return response

        except asyncio.TimeoutError:
            error_response = message.create_response(
                content=f"处理超时 (timeout={self.processing_timeout}s)",
                metadata={'error': 'timeout'}
            )
            await self._handle_error(
                Exception("Processing timeout"),
                {'message': message.to_dict()}
            )
            return error_response

        except Exception as e:
            error_response = message.create_response(
                content=f"处理错误: {str(e)}",
                metadata={'error': str(e)}
            )
            await self._handle_error(e, {'message': message.to_dict()})
            return error_response

        finally:
            self.update_status(AgentStatus.IDLE)
            self._emit_event('task_completed', {'message_id': message.id})

    @abstractmethod
    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        """
        具体的消息处理实现（子类必须实现）

        参数：
            message: 要处理的消息

        返回：
            响应消息
        """
        pass

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """
        处理单条消息的同步入口

        参数：
            message: 要处理的消息

        返回：
            响应消息
        """
        return await self.process_message_async(message)

    async def process_message_batch(
        self,
        messages: List[AgentMessage],
        parallel: bool = False
    ) -> List[AgentMessage]:
        """
        批量处理消息

        参数：
            messages: 消息列表
            parallel: 是否并行处理

        返回：
            响应消息列表
        """
        if parallel:
            tasks = [self.process_message_async(msg) for msg in messages]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for msg in messages:
                result = await self.process_message_async(msg)
                results.append(result)
            return results

    async def stream_response(
        self,
        message: AgentMessage
    ) -> AsyncGenerator[AgentStreamResponse, None]:
        """
        流式处理消息并产生响应片段

        参数：
            message: 要处理的消息

        生成：
            AgentStreamResponse: 流式响应片段

        注意：
            子类应重写此方法以提供真正的流式响应
        """
        response = await self.process_message_async(message)
        yield AgentStreamResponse(
            final_message=response.content,
            text=""
        )

    async def _handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """
        处理错误

        参数：
            error: 异常对象
            context: 错误上下文
        """
        self.update_status(AgentStatus.ERROR)
        self._emit_event('error', {
            'error': str(error),
            'context': context
        })
        await self.callbacks.on_error(
            self.name,
            error,
            context
        )

    def get_queue_size(self) -> int:
        """
        获取消息队列当前大小

        返回：
            队列中的消息数量
        """
        return len(self.message_queue)

    def clear_queue(self) -> None:
        """清空消息队列"""
        self.message_queue.clear()

    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息

        返回：
            包含Agent状态和配置的字典
        """
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'capabilities': self.capabilities,
            'status': self.status.value,
            'queue_size': self.get_queue_size(),
            'streaming_enabled': self.is_streaming_enabled(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        返回：
            健康状态信息
        """
        return {
            'agent_name': self.name,
            'agent_id': self.id,
            'status': self.status.value,
            'queue_size': self.get_queue_size(),
            'healthy': self.status != AgentStatus.ERROR,
        }

    def log_debug(self, message: str, data: Any = None) -> None:
        """
        输出调试日志

        参数：
            message: 日志消息
            data: 附加数据
        """
        if self.log_debug_trace:
            prefix = f"[{self.name}]"
            if data:
                print(f"{prefix} {message} | Data: {data}")
            else:
                print(f"{prefix} {message}")

    def log_error(self, message: str, data: Any = None) -> None:
        """
        输出错误日志

        参数：
            message: 错误消息
            data: 附加数据
        """
        prefix = f"[{self.name}] ERROR"
        if data:
            print(f"{prefix} {message} | Data: {data}")
        else:
            print(f"{prefix} {message}")

    @abstractmethod
    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[Any],
        additional_params: Optional[AgentParamsType] = None,
    ) -> Union[Any, AsyncIterable[Any]]:
        """
        处理用户请求（子类必须实现）

        参数：
            input_text: 用户输入文本
            user_id: 用户标识符
            session_id: 会话标识符
            chat_history: 对话历史
            additional_params: 附加参数

        返回：
            完整响应消息或异步迭代器（流式响应）
        """
        pass

    async def shutdown(self) -> None:
        """优雅关闭Agent"""
        self.update_status(AgentStatus.TERMINATED)
        self.clear_queue()
        for event_type in self._event_handlers:
            self._event_handlers[event_type].clear()
