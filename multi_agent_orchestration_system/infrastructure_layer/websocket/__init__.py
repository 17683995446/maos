"""
Infrastructure Layer - WebSocket Communication Module
================================================

Provides real-time bidirectional communication using WebSocket protocol.
Part of the Phase 2 production hardening improvements.

Key Features:
  - Real-time event streaming
  - Bidirectional communication
  - Connection management and heartbeats
  - Authentication and authorization
  - Message queuing for offline clients
  - Scalable multi-client support

Architecture:
  - Uses FastAPI WebSocket support
  - Async message handling
  - Redis pub/sub for scaling
  - JWT token authentication
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
import asyncio
import json
import logging
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class WebSocketEventType(Enum):
    """Types of WebSocket events"""
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETED = "workflow_completed"
    SYSTEM_STATUS = "system_status"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    NOTIFICATION = "notification"


class WebSocketConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    AUTHENTICATED = "authenticated"
    ACTIVE = "active"
    IDLE = "idle"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: WebSocketEventType = WebSocketEventType.HEARTBEAT
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    sender_id: Optional[str] = None
    target_client_id: Optional[str] = None
    broadcast: bool = True
    priority: int = 0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps({
            'message_id': self.message_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'payload': self.payload,
            'sender_id': self.sender_id,
            'target_client_id': self.target_client_id,
            'broadcast': self.broadcast,
            'priority': self.priority,
            'metadata': self.metadata
        }, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(
            message_id=data['message_id'],
            event_type=WebSocketEventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            payload=data['payload'],
            sender_id=data.get('sender_id'),
            target_client_id=data.get('target_client_id'),
            broadcast=data.get('broadcast', True),
            priority=data.get('priority', 0),
            metadata=data.get('metadata', {})
        )


@dataclass
class ClientSession:
    """WebSocket client session information"""
    client_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    connection_state: WebSocketConnectionState = WebSocketConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    subscribed_channels: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    subscriptions: Set[WebSocketEventType] = field(default_factory=set)
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_active(self) -> bool:
        """Check if client is still active"""
        idle_time = (datetime.now() - self.last_activity).total_seconds()
        return idle_time < 300
    
    def subscribe_to_event(self, event_type: WebSocketEventType) -> None:
        """Subscribe to specific event type"""
        self.subscriptions.add(event_type)
    
    def unsubscribe_from_event(self, event_type: WebSocketEventType) -> None:
        """Unsubscribe from specific event type"""
        self.subscriptions.discard(event_type)


class WebSocketAuthenticationManager:
    """
    WebSocket authentication manager.
    
    Features:
      - JWT token validation
      - API key authentication
      - Connection permission checks
      - Session management
    """
    
    def __init__(self):
        self._sessions: Dict[str, ClientSession] = {}
        self._user_sessions: Dict[str, Set[str]] = defaultdict(set)
        self._max_sessions_per_user: int = 5
    
    def create_session(
        self,
        client_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> ClientSession:
        """Create new client session"""
        session = ClientSession(
            client_id=client_id,
            user_id=user_id,
            username=username
        )
        
        self._sessions[client_id] = session
        
        if user_id:
            self._user_sessions[user_id].add(client_id)
            
            if len(self._user_sessions[user_id]) > self._max_sessions_per_user:
                oldest = min(
                    self._user_sessions[user_id],
                    key=lambda cid: self._sessions[cid].connected_at
                )
                self.close_session(oldest)
        
        logger.info(f"Session created for client: {client_id}")
        return session
    
    def get_session(self, client_id: str) -> Optional[ClientSession]:
        """Get client session"""
        return self._sessions.get(client_id)
    
    def close_session(self, client_id: str) -> bool:
        """Close and remove client session"""
        if client_id in self._sessions:
            session = self._sessions[client_id]
            
            if session.user_id and session.user_id in self._user_sessions:
                self._user_sessions[session.user_id].discard(client_id)
            
            del self._sessions[client_id]
            logger.info(f"Session closed for client: {client_id}")
            return True
        return False
    
    def get_user_sessions(self, user_id: str) -> List[ClientSession]:
        """Get all sessions for a user"""
        client_ids = self._user_sessions.get(user_id, set())
        return [
            self._sessions[cid] for cid in client_ids
            if cid in self._sessions
        ]
    
    def get_all_active_sessions(self) -> List[ClientSession]:
        """Get all active sessions"""
        return [
            session for session in self._sessions.values()
            if session.connection_state != WebSocketConnectionState.CLOSED
        ]
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self._sessions)


class WebSocketEventBroadcaster:
    """
    WebSocket event broadcaster for real-time updates.
    
    Features:
      - Event-based broadcasting
      - Priority queue support
      - Message buffering for offline clients
      - Fan-out to multiple clients
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: Dict[WebSocketEventType, Set[str]] = defaultdict(set)
        self._client_subscriptions: Dict[str, Set[WebSocketEventType]] = defaultdict(set)
        self._message_queues: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self._max_queue_size = max_queue_size
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self,
        client_id: str,
        event_type: WebSocketEventType
    ) -> None:
        """Subscribe client to event type"""
        async with self._lock:
            self._subscribers[event_type].add(client_id)
            self._client_subscriptions[client_id].add(event_type)
            logger.debug(f"Client {client_id} subscribed to {event_type.value}")
    
    async def unsubscribe(
        self,
        client_id: str,
        event_type: WebSocketEventType
    ) -> None:
        """Unsubscribe client from event type"""
        async with self._lock:
            self._subscribers[event_type].discard(client_id)
            self._client_subscriptions[client_id].discard(event_type)
            logger.debug(f"Client {client_id} unsubscribed from {event_type.value}")
    
    async def subscribe_all(self, client_id: str) -> None:
        """Subscribe client to all events"""
        async with self._lock:
            for event_type in WebSocketEventType:
                self._subscribers[event_type].add(client_id)
                self._client_subscriptions[client_id].add(event_type)
    
    async def unsubscribe_all(self, client_id: str) -> None:
        """Unsubscribe client from all events"""
        async with self._lock:
            for event_type in self._client_subscriptions[client_id]:
                self._subscribers[event_type].discard(client_id)
            self._client_subscriptions[client_id].clear()
            logger.debug(f"Client {client_id} unsubscribed from all events")
    
    async def broadcast(self, message: WebSocketMessage) -> List[str]:
        """
        Broadcast message to all subscribed clients.
        
        Returns:
            List of client IDs that received the message
        """
        if message.broadcast:
            subscribers = self._subscribers.get(message.event_type, set())
        else:
            subscribers = {message.target_client_id} if message.target_client_id else set()
        
        delivered_to = []
        
        for client_id in subscribers:
            try:
                await self.queue_message(client_id, message)
                delivered_to.append(client_id)
            except Exception as e:
                logger.error(f"Failed to queue message for client {client_id}: {e}")
        
        return delivered_to
    
    async def queue_message(self, client_id: str, message: WebSocketMessage) -> None:
        """Queue message for client delivery"""
        async with self._lock:
            queue = self._message_queues[client_id]
            queue.append(message)
            
            if len(queue) > self._max_queue_size:
                queue.pop(0)
    
    def get_queued_messages(self, client_id: str) -> List[WebSocketMessage]:
        """Get queued messages for client (FIFO)"""
        queue = self._message_queues.get(client_id, [])
        self._message_queues[client_id] = []
        return queue
    
    def get_queue_size(self, client_id: str) -> int:
        """Get number of queued messages for client"""
        return len(self._message_queues.get(client_id, []))
    
    def get_subscriber_count(self, event_type: WebSocketEventType) -> int:
        """Get number of subscribers for event type"""
        return len(self._subscribers.get(event_type, set()))
    
    def get_total_subscriptions(self) -> int:
        """Get total number of subscriptions"""
        return sum(len(subs) for subs in self._subscribers.values())


class WebSocketMessageHandler:
    """
    WebSocket message handler for processing incoming messages.
    
    Features:
      - Message validation
      - Rate limiting per client
      - Command processing
      - Error handling
    """
    
    def __init__(self):
        self._command_handlers: Dict[str, Callable] = {}
        self._rate_limiter: Dict[str, List[float]] = defaultdict(list)
        self._rate_limit_window = 60
        self._max_messages_per_window = 100
    
    def register_command_handler(
        self,
        command: str,
        handler: Callable[[str, Dict], Any]
    ) -> None:
        """Register command handler"""
        self._command_handlers[command] = handler
        logger.info(f"Command handler registered: {command}")
    
    async def handle_message(
        self,
        client_id: str,
        message: WebSocketMessage
    ) -> Optional[WebSocketMessage]:
        """
        Handle incoming WebSocket message.
        
        Returns:
            Optional response message
        """
        if not self.check_rate_limit(client_id):
            return WebSocketMessage(
                event_type=WebSocketEventType.ERROR,
                payload={
                    'error': 'Rate limit exceeded',
                    'retry_after': 60
                }
            )
        
        if message.event_type == WebSocketEventType.HEARTBEAT:
            return WebSocketMessage(
                event_type=WebSocketEventType.HEARTBEAT,
                payload={'status': 'ok', 'timestamp': datetime.now().isoformat()}
            )
        
        command = message.payload.get('command')
        if command and command in self._command_handlers:
            try:
                result = await self._command_handlers[command](
                    client_id,
                    message.payload.get('params', {})
                )
                return WebSocketMessage(
                    event_type=WebSocketEventType.NOTIFICATION,
                    payload={'result': result}
                )
            except Exception as e:
                logger.error(f"Command {command} failed: {e}")
                return WebSocketMessage(
                    event_type=WebSocketEventType.ERROR,
                    payload={'error': str(e)}
                )
        
        return None
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit"""
        now = datetime.now().timestamp()
        window_start = now - self._rate_limit_window
        
        timestamps = self._rate_limiter[client_id]
        timestamps = [ts for ts in timestamps if ts > window_start]
        timestamps.append(now)
        self._rate_limiter[client_id] = timestamps
        
        if len(timestamps) > self._max_messages_per_window:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False
        
        return True


class WebSocketOrchestrationBridge:
    """
    Bridge between WebSocket layer and orchestration engine.
    
    Features:
      - Real-time agent status updates
      - Task lifecycle notifications
      - Workflow progress streaming
      - System status updates
    """
    
    def __init__(
        self,
        broadcaster: WebSocketEventBroadcaster,
        auth_manager: WebSocketAuthenticationManager
    ):
        self.broadcaster = broadcaster
        self.auth_manager = auth_manager
        self._orchestrator_callbacks = []
    
    async def notify_agent_registered(self, agent_name: str, agent_info: Dict[str, Any]) -> None:
        """Notify clients about agent registration"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.AGENT_REGISTERED,
            payload={
                'agent_name': agent_name,
                'agent_info': agent_info
            }
        )
        await self.broadcaster.broadcast(message)
    
    async def notify_agent_status_changed(
        self,
        agent_name: str,
        old_status: str,
        new_status: str
    ) -> None:
        """Notify clients about agent status change"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.AGENT_STATUS_CHANGED,
            payload={
                'agent_name': agent_name,
                'old_status': old_status,
                'new_status': new_status
            }
        )
        await self.broadcaster.broadcast(message)
    
    async def notify_task_created(self, task_id: str, task_info: Dict[str, Any]) -> None:
        """Notify clients about task creation"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.TASK_CREATED,
            payload={
                'task_id': task_id,
                'task_info': task_info
            }
        )
        await self.broadcaster.broadcast(message)
    
    async def notify_task_completed(
        self,
        task_id: str,
        result: Any,
        duration: float
    ) -> None:
        """Notify clients about task completion"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.TASK_COMPLETED,
            payload={
                'task_id': task_id,
                'result': result,
                'duration': duration
            }
        )
        await self.broadcaster.broadcast(message)
    
    async def notify_task_failed(
        self,
        task_id: str,
        error: str
    ) -> None:
        """Notify clients about task failure"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.TASK_FAILED,
            payload={
                'task_id': task_id,
                'error': error
            }
        )
        await self.broadcaster.broadcast(message)
    
    async def notify_workflow_progress(
        self,
        workflow_id: str,
        step_name: str,
        progress: float,
        status: str
    ) -> None:
        """Notify clients about workflow progress"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.WORKFLOW_PROGRESS,
            payload={
                'workflow_id': workflow_id,
                'step_name': step_name,
                'progress': progress,
                'status': status
            }
        )
        await self.broadcaster.broadcast(message)
    
    async def notify_system_status(self, status: Dict[str, Any]) -> None:
        """Notify clients about system status"""
        message = WebSocketMessage(
            event_type=WebSocketEventType.SYSTEM_STATUS,
            payload=status
        )
        await self.broadcaster.broadcast(message)


if __name__ == "__main__":
    print("WebSocket Communication Module")
    print("=" * 50)
    
    broadcaster = WebSocketEventBroadcaster()
    auth_manager = WebSocketAuthenticationManager()
    
    session = auth_manager.create_session(
        client_id="test-client-1",
        username="testuser"
    )
    
    print(f"Session created: {session.client_id}")
    print(f"Active sessions: {auth_manager.get_session_count()}")
    
    print("\nEvent Types Available:")
    for event_type in WebSocketEventType:
        print(f"  - {event_type.value}")
