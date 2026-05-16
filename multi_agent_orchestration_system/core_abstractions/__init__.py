"""
Core Abstractions Module
=====================

Contains fundamental abstractions and base classes used throughout the system.
This module is framework-agnostic and provides the building blocks for the entire platform.

Components:
  - BaseAgent: Abstract base class for all agents
  - AgentMessage: Message format for agent communication
  - AgentStatus: Agent lifecycle states
  - MessageType: Types of messages in the system
  - AgentMetadata: Agent descriptive information
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class AgentOperationalStatus(Enum):
    """
    Enumeration of possible agent operational states.
    Agents transition through these states during their lifecycle.
    """
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"
    OFFLINE = "offline"


class AgentMessageType(Enum):
    """
    Types of messages that agents can send and receive.
    Different message types trigger different processing behaviors.
    """
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    ERROR_NOTIFICATION = "error_notification"
    STATUS_UPDATE = "status_update"
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"


@dataclass
class AgentMessagePayload:
    """
    Container for agent message data and metadata.
    Provides serialization support for distributed communication.
    """
    data_content: Any
    content_type: str = "application/json"
    encoding: str = "utf-8"
    compression: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary representation"""
        return {
            'data_content': self.data_content,
            'content_type': self.content_type,
            'encoding': self.encoding,
            'compression': self.compression,
            'custom_headers': self.custom_headers
        }


@dataclass
class AgentMessage:
    """
    Standardized message format for inter-agent communication.
    Supports request-response patterns, broadcasts, and pub/sub messaging.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_agent_name: str = ""
    receiver_agent_names: List[str] = field(default_factory=list)
    message_type: AgentMessageType = AgentMessageType.TASK_REQUEST
    payload: Optional[AgentMessagePayload] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_timestamp: datetime = field(default_factory=datetime.now)
    correlation_message_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize message to dictionary for transmission"""
        return {
            'message_id': self.message_id,
            'sender_agent_name': self.sender_agent_name,
            'receiver_agent_names': self.receiver_agent_names,
            'message_type': self.message_type.value,
            'payload': self.payload.to_dict() if self.payload else None,
            'metadata': self.metadata,
            'created_timestamp': self.created_timestamp.isoformat(),
            'correlation_message_id': self.correlation_message_id,
            'reply_to_message_id': self.reply_to_message_id
        }
    
    @classmethod
    def from_dict(cls, message_dict: Dict[str, Any]) -> 'AgentMessage':
        """Deserialize message from dictionary"""
        message_dict = message_dict.copy()
        message_dict['message_type'] = AgentMessageType(message_dict.get('message_type', 'task_request'))
        
        if 'created_timestamp' in message_dict and isinstance(message_dict['created_timestamp'], str):
            message_dict['created_timestamp'] = datetime.fromisoformat(message_dict['created_timestamp'])
        
        if message_dict.get('payload'):
            message_dict['payload'] = AgentMessagePayload(**message_dict['payload'])
        
        return cls(**message_dict)
    
    def create_response(self, response_data: Any) -> 'AgentMessage':
        """Create a response message for this message"""
        return AgentMessage(
            sender_agent_name=self.sender_agent_name,
            receiver_agent_names=[self.sender_agent_name] if self.sender_agent_name else [],
            message_type=AgentMessageType.TASK_RESPONSE,
            payload=AgentMessagePayload(data_content=response_data),
            correlation_message_id=self.message_id,
            reply_to_message_id=self.message_id
        )


@dataclass
class AgentCapabilities:
    """
    Container for agent capabilities and skills.
    Used for agent matching and task assignment.
    """
    capability_list: List[str] = field(default_factory=list)
    capability_versions: Dict[str, str] = field(default_factory=dict)
    supported_message_types: List[AgentMessageType] = field(default_factory=list)
    max_concurrent_tasks: int = 1
    estimated_processing_speed: float = 1.0
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability"""
        return capability_name in self.capability_list
    
    def has_all_capabilities(self, required_capabilities: List[str]) -> bool:
        """Check if agent has all required capabilities"""
        return all(self.has_capability(cap) for cap in required_capabilities)
    
    def get_capability_count(self) -> int:
        """Get total number of capabilities"""
        return len(self.capability_list)


def create_default_agent_capabilities() -> AgentCapabilities:
    """Factory function for default AgentCapabilities"""
    return AgentCapabilities(capability_list=[])


@dataclass
class AgentMetadata:
    """
    Descriptive metadata about an agent.
    Used for agent discovery and management.
    """
    agent_name: str
    agent_description: str = ""
    capabilities: AgentCapabilities = field(default_factory=create_default_agent_capabilities)
    agent_version: str = "1.0.0"
    owner_team: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            'agent_name': self.agent_name,
            'agent_description': self.agent_description,
            'capabilities': {
                'capability_list': self.capabilities.capability_list,
                'capability_versions': self.capabilities.capability_versions,
                'supported_message_types': [mt.value for mt in self.capabilities.supported_message_types],
                'max_concurrent_tasks': self.capabilities.max_concurrent_tasks,
                'estimated_processing_speed': self.capabilities.estimated_processing_speed
            },
            'agent_version': self.agent_version,
            'owner_team': self.owner_team,
            'tags': self.tags,
            'custom_properties': self.custom_properties
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Provides core functionality for agent lifecycle, messaging, and task processing.
    
    Subclasses must implement:
      - process_task_request(): Handle incoming task requests
      - get_agent_capabilities(): Return agent's capabilities
    
    Key Features:
      - Message queue management
      - Status tracking
      - Heartbeat mechanism
      - Capability-based matching
    """
    
    def __init__(
        self,
        agent_name: str,
        agent_description: str = "",
        capability_list: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        if not agent_name or not agent_name.strip():
            raise ValueError("Agent name cannot be empty or whitespace")
        
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_status = AgentOperationalStatus.IDLE
        self.message_queue: List[AgentMessage] = []
        self.capabilities = AgentCapabilities(
            capability_list=capability_list or [],
            supported_message_types=[AgentMessageType.TASK_REQUEST, AgentMessageType.HEARTBEAT]
        )
        self.metadata = AgentMetadata(
            agent_name=agent_name,
            agent_description=agent_description,
            capabilities=self.capabilities,
            custom_properties=metadata or {}
        )
        self.last_heartbeat_timestamp = datetime.now()
        self.message_handler_registry: Dict[AgentMessageType, Callable] = {}
        self._register_default_message_handlers()
    
    def _register_default_message_handlers(self) -> None:
        """Register default handlers for standard message types"""
        self.register_message_handler(AgentMessageType.HEARTBEAT, self._handle_heartbeat_message)
        self.register_message_handler(AgentMessageType.STATUS_UPDATE, self._handle_status_update_message)
    
    def register_message_handler(
        self,
        message_type: AgentMessageType,
        handler: Callable[[AgentMessage], Optional[AgentMessage]]
    ) -> None:
        """Register a custom handler for a specific message type"""
        self.message_handler_registry[message_type] = handler
    
    def _handle_heartbeat_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Default handler for heartbeat messages"""
        self.last_heartbeat_timestamp = datetime.now()
        return AgentMessage(
            sender_agent_name=self.agent_name,
            receiver_agent_names=[message.sender_agent_name],
            message_type=AgentMessageType.TASK_RESPONSE,
            payload=AgentMessagePayload(data_content={
                'status': self.agent_status.value,
                'timestamp': self.last_heartbeat_timestamp.isoformat()
            }),
            reply_to_message_id=message.message_id
        )
    
    def _handle_status_update_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Default handler for status update messages"""
        if message.payload and isinstance(message.payload.data_content, dict):
            new_status = message.payload.data_content.get('status')
            if new_status:
                self.update_agent_status(AgentOperationalStatus(new_status))
        return None
    
    def update_agent_status(self, new_status: AgentOperationalStatus) -> None:
        """Update the agent's operational status"""
        old_status = self.agent_status
        self.agent_status = new_status
        self.last_heartbeat_timestamp = datetime.now()
    
    def send_message(self, message: AgentMessage) -> None:
        """
        Send a message (adds to queue for processing).
        In distributed mode, this would publish to message broker.
        """
        message.sender_agent_name = self.agent_name
        self.message_queue.append(message)
    
    def receive_message(self, message: AgentMessage) -> None:
        """Receive an incoming message"""
        self.message_queue.append(message)
    
    def process_next_message(self) -> Optional[AgentMessage]:
        """
        Process the next message in the queue.
        Returns response message if applicable.
        """
        if not self.message_queue:
            return None
        
        message = self.message_queue.pop(0)
        
        handler = self.message_handler_registry.get(message.message_type)
        if handler:
            return handler(message)
        
        return self.process_task_request(message)
    
    def process_task_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process an incoming task request message.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process_task_request")
    
    def get_agent_capabilities(self) -> AgentCapabilities:
        """Return the agent's capabilities"""
        return self.capabilities
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information"""
        return {
            **self.metadata.to_dict(),
            'current_status': self.agent_status.value,
            'message_queue_size': len(self.message_queue),
            'last_heartbeat': self.last_heartbeat_timestamp.isoformat()
        }
    
    def clear_message_queue(self) -> None:
        """Clear all pending messages from queue"""
        self.message_queue.clear()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.agent_name}' status='{self.agent_status.value}'>"
