"""
MAOS v7.0 - WebSocket实时通信
支持实时任务更新和Agent协作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from typing import Dict, Set, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid


class EventType(Enum):
    """事件类型"""
    # 任务事件
    TASK_CREATED = "task:created"
    TASK_STARTED = "task:started"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"
    TASK_CANCELLED = "task:cancelled"
    
    # Agent事件
    AGENT_REGISTERED = "agent:registered"
    AGENT_UNREGISTERED = "agent:unregistered"
    AGENT_STATUS_CHANGED = "agent:status_changed"
    
    # 系统事件
    SYSTEM_READY = "system:ready"
    SYSTEM_ERROR = "system:error"
    METRIC_UPDATE = "metric:update"
    
    # 消息事件
    MESSAGE_RECEIVED = "message:received"
    MESSAGE_SENT = "message:sent"


@dataclass
class WebSocketMessage:
    """WebSocket消息"""
    event_type: str
    data: Dict[str, Any]
    timestamp: str = None
    message_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        data = json.loads(json_str)
        return cls(**data)


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self):
        self._connections: Dict[str, Set] = {
            "global": set(),
            "tasks": set(),
            "agents": set(),
            "metrics": set(),
        }
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket, channel: str = "global") -> str:
        """连接"""
        async with self._lock:
            conn_id = str(uuid.uuid4())
            if channel not in self._connections:
                self._connections[channel] = set()
            self._connections[channel].add((conn_id, websocket))
            self._connections["global"].add((conn_id, websocket))
            return conn_id
    
    async def disconnect(self, conn_id: str, websocket, channel: str = None):
        """断开连接"""
        async with self._lock:
            for ch_name, connections in self._connections.items():
                if channel is None or ch_name == channel:
                    to_remove = [(cid, ws) for cid, ws in connections if cid == conn_id]
                    for item in to_remove:
                        connections.discard(item)
    
    async def broadcast(
        self,
        message: WebSocketMessage,
        channel: str = "global"
    ):
        """广播消息"""
        connections = self._connections.get(channel, set())
        connections.update(self._connections.get("global", set()))
        
        disconnected = []
        
        for conn_id, websocket in connections:
            try:
                await websocket.send_text(message.to_json())
            except Exception:
                disconnected.append((conn_id, websocket))
        
        # 清理断开的连接
        for conn_id, websocket in disconnected:
            await self.disconnect(conn_id, websocket)
    
    def get_connection_count(self, channel: str = None) -> int:
        """获取连接数"""
        if channel:
            return len(self._connections.get(channel, set()))
        return sum(len(conns) for conns in self._connections.values())


class EventBus:
    """事件总线"""
    
    def __init__(self):
        self._handlers: Dict[str, list] = {}
        self._connection_manager = ConnectionManager()
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """订阅事件"""
        async with self._lock:
            if event_type.value not in self._handlers:
                self._handlers[event_type.value] = []
            self._handlers[event_type.value].append(handler)
    
    async def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """取消订阅"""
        async with self._lock:
            if event_type.value in self._handlers:
                try:
                    self._handlers[event_type.value].remove(handler)
                except ValueError:
                    pass
    
    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        broadcast: bool = True
    ):
        """发布事件"""
        message = WebSocketMessage(
            event_type=event_type.value,
            data=data
        )
        
        # 调用处理器
        handlers = self._handlers.get(event_type.value, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        # 广播
        if broadcast:
            await self._connection_manager.broadcast(message, event_type.value.split(":")[0])
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return self._connection_manager.get_connection_count()


class WebSocketServer:
    """WebSocket服务器"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.connection_manager = ConnectionManager()
    
    async def handle_connection(self, websocket, channel: str = "global"):
        """处理WebSocket连接"""
        conn_id = await self.connection_manager.connect(websocket, channel)
        
        # 发送欢迎消息
        welcome = WebSocketMessage(
            event_type="connection:established",
            data={
                "conn_id": conn_id,
                "channel": channel,
                "message": "Connected to MAOS WebSocket server"
            }
        )
        await websocket.send_text(welcome.to_json())
        
        # 监听消息
        try:
            async for message_text in websocket:
                await self._handle_message(message_text, websocket, conn_id)
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await self.connection_manager.disconnect(conn_id, websocket, channel)
    
    async def _handle_message(
        self,
        message_text: str,
        websocket,
        conn_id: str
    ):
        """处理收到的消息"""
        try:
            message = WebSocketMessage.from_json(message_text)
            
            # 根据事件类型处理
            if message.event_type == "ping":
                pong = WebSocketMessage(
                    event_type="pong",
                    data={"timestamp": datetime.now().isoformat()}
                )
                await websocket.send_text(pong.to_json())
            
            elif message.event_type == "subscribe":
                # 订阅频道
                channel = message.data.get("channel")
                if channel:
                    await self.connection_manager.connect(websocket, channel)
                    ack = WebSocketMessage(
                        event_type="subscribed",
                        data={"channel": channel}
                    )
                    await websocket.send_text(ack.to_json())
            
            elif message.event_type == "task:create":
                # 创建任务
                await self.event_bus.publish(
                    EventType.TASK_CREATED,
                    message.data,
                    broadcast=True
                )
            
            elif message.event_type == "message:send":
                # 发送消息
                await self.event_bus.publish(
                    EventType.MESSAGE_RECEIVED,
                    message.data,
                    broadcast=True
                )
            
        except Exception as e:
            error = WebSocketMessage(
                event_type="error",
                data={"message": str(e)}
            )
            await websocket.send_text(error.to_json())


# 全局实例
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取事件总线"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
