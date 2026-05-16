"""
Agent Base Class and Communication Messages
Agent基类和通信消息定义
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Agent间通信消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receivers: List[str] = field(default_factory=list)
    msg_type: MessageType = MessageType.REQUEST
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'id': self.id,
            'sender': self.sender,
            'receivers': self.receivers,
            'msg_type': self.msg_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'reply_to': self.reply_to
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """从字典反序列化"""
        data = data.copy()
        data['msg_type'] = MessageType(data.get('msg_type', 'request'))
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Agent:
    """Agent基类"""
    name: str
    capabilities: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    message_queue: List[AgentMessage] = field(default_factory=list)
    message_handler: Optional[Callable] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Agent name cannot be empty")

    def send_message(self, message: AgentMessage) -> None:
        """发送消息"""
        message.sender = self.name
        self.message_queue.append(message)

    def receive_message(self, message: AgentMessage) -> None:
        """接收消息"""
        self.message_queue.append(message)
        if self.message_handler:
            self.message_handler(self, message)

    def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理消息 - 子类重写实现具体逻辑"""
        response = AgentMessage(
            sender=self.name,
            receivers=[message.sender] if message.sender else [],
            msg_type=MessageType.RESPONSE,
            content=f"Default response from {self.name}",
            reply_to=message.id,
            metadata={'status': 'processed'}
        )
        return response

    def has_capability(self, capability: str) -> bool:
        """检查是否具有某能力"""
        return capability in self.capabilities

    def can_handle_task(self, task_requirements: List[str]) -> bool:
        """检查是否能处理任务"""
        return all(self.has_capability(req) for req in task_requirements)

    def update_status(self, status: AgentStatus) -> None:
        """更新状态"""
        self.status = status

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            'name': self.name,
            'capabilities': self.capabilities,
            'status': self.status.value,
            'message_queue_size': len(self.message_queue)
        }

    def clear_queue(self) -> None:
        """清空消息队列"""
        self.message_queue.clear()
