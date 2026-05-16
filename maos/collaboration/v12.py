"""
MAOS v12.0 - 实时协作引擎
WebSocket通信与CRDT同步
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import json


class CollaborationEventType(Enum):
    """协作事件类型"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CURSOR_MOVED = "cursor_moved"
    TEXT_CHANGED = "text_changed"
    NODE_ADDED = "node_added"
    NODE_REMOVED = "node_removed"
    NODE_MOVED = "node_moved"
    NODE_CONFIG_CHANGED = "node_config_changed"
    EDGE_ADDED = "edge_added"
    EDGE_REMOVED = "edge_removed"
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    SELECTION_CHANGED = "selection_changed"


@dataclass
class Collaborator:
    """协作者"""
    id: str
    name: str
    avatar_url: str
    color: str
    cursor: Dict[str, Any] = field(default_factory=dict)
    selection: List[str] = field(default_factory=list)
    is_active: bool = True
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class Comment:
    """评论"""
    id: str
    author_id: str
    author_name: str
    text: str
    position: Dict[str, Any]
    node_id: Optional[str]
    reply_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved: bool = False
    reactions: Dict[str, Set[str]] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    workflow_id: str
    owner_id: str
    collaborators: Dict[str, Collaborator]
    comments: List[Comment]
    event_log: List[Dict]
    created_at: datetime
    is_active: bool = True


class Operation:
    """操作（CRDT用）"""

    def __init__(self, id: str, op_type: str, data: Any, timestamp: int, user_id: str):
        self.id = id
        self.type = op_type
        self.data = data
        self.timestamp = timestamp
        self.user_id = user_id

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
        }


class CRDTDocument:
    """CRDT文档"""

    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.operations: List[Operation] = []
        self.current_state: Dict[str, Any] = {}
        self.vector_clock: Dict[str, int] = {}

    def apply_operation(self, op: Operation):
        """应用操作"""
        self.operations.append(op)

        # 更新向量时钟
        if op.user_id not in self.vector_clock:
            self.vector_clock[op.user_id] = 0
        self.vector_clock[op.user_id] = max(self.vector_clock[op.user_id], op.timestamp)

        # 合并状态
        self._merge_state(op)

    def _merge_state(self, op: Operation):
        """合并操作到状态（简化的CRDT逻辑）"""
        if op.type == "set":
            key = op.data.get("key")
            value = op.data.get("value")
            if key:
                # LWW: Last Write Wins
                existing = self.current_state.get(key, {"timestamp": 0, "value": None})
                if op.timestamp > existing.get("timestamp", 0):
                    self.current_state[key] = {"timestamp": op.timestamp, "value": value}

        elif op.type == "list_append":
            key = op.data.get("key")
            item = op.data.get("item")
            if key and key not in self.current_state:
                self.current_state[key] = {"type": "list", "items": []}
            if key and item:
                items = self.current_state[key].get("items", [])
                items.append(item)
                self.current_state[key]["items"] = items

    def create_operation(self, op_type: str, data: Any, user_id: str) -> Operation:
        """创建操作"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return Operation(str(uuid.uuid4()), op_type, data, timestamp, user_id)

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_state

    def get_operations_since(self, since_timestamp: int) -> List[Operation]:
        """获取指定时间之后的操作"""
        return [op for op in self.operations if op.timestamp > since_timestamp]


class CollaborationManager:
    """协作管理器"""

    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.documents: Dict[str, CRDTDocument] = {}
        self.connections: Dict[str, asyncio.Queue] = {}

    def create_session(self, workflow_id: str, owner_id: str, owner_name: str) -> str:
        """创建协作会话"""
        session_id = str(uuid.uuid4())

        owner = Collaborator(
            id=owner_id,
            name=owner_name,
            avatar_url=f"https://avatar.maos.io/{owner_id}",
            color="#667eea",
        )

        session = CollaborationSession(
            session_id=session_id,
            workflow_id=workflow_id,
            owner_id=owner_id,
            collaborators={owner_id: owner},
            comments=[],
            event_log=[],
            created_at=datetime.now(),
        )

        self.sessions[session_id] = session
        self.documents[session_id] = CRDTDocument(session_id)

        self._log_event(session, {
            "type": CollaborationEventType.USER_JOINED,
            "user_id": owner_id,
            "user_name": owner_name,
        })

        return session_id

    def join_session(self, session_id: str, user_id: str, user_name: str) -> Optional[str]:
        """加入会话"""
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return None

        colors = ["#667eea", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
        used_colors = {c.color for c in session.collaborators.values()}
        available_colors = [c for c in colors if c not in used_colors]
        color = available_colors[0] if available_colors else colors[0]

        collaborator = Collaborator(
            id=user_id,
            name=user_name,
            avatar_url=f"https://avatar.maos.io/{user_id}",
            color=color,
        )

        session.collaborators[user_id] = collaborator
        self._log_event(session, {
            "type": CollaborationEventType.USER_JOINED,
            "user_id": user_id,
            "user_name": user_name,
        })

        return session_id

    def leave_session(self, session_id: str, user_id: str):
        """离开会话"""
        session = self.sessions.get(session_id)
        if not session:
            return

        if user_id in session.collaborators:
            session.collaborators[user_id].is_active = False
            self._log_event(session, {
                "type": CollaborationEventType.USER_LEFT,
                "user_id": user_id,
            })

    def move_cursor(self, session_id: str, user_id: str, position: Dict[str, Any]):
        """移动光标"""
        session = self.sessions.get(session_id)
        if not session or user_id not in session.collaborators:
            return

        session.collaborators[user_id].cursor = position
        self._log_event(session, {
            "type": CollaborationEventType.CURSOR_MOVED,
            "user_id": user_id,
            "position": position,
        })

    def add_node(self, session_id: str, user_id: str, node_data: Dict[str, Any]):
        """添加节点"""
        session = self.sessions.get(session_id)
        if not session or user_id not in session.collaborators:
            return

        doc = self.documents[session_id]
        op = doc.create_operation("node_add", node_data, user_id)
        doc.apply_operation(op)

        self._log_event(session, {
            "type": CollaborationEventType.NODE_ADDED,
            "user_id": user_id,
            "node_data": node_data,
        })

    def add_comment(self, session_id: str, user_id: str, text: str, node_id: Optional[str], position: Dict[str, Any]):
        """添加评论"""
        session = self.sessions.get(session_id)
        if not session or user_id not in session.collaborators:
            return

        comment = Comment(
            id=str(uuid.uuid4()),
            author_id=user_id,
            author_name=session.collaborators[user_id].name,
            text=text,
            position=position,
            node_id=node_id,
            reply_to=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        session.comments.append(comment)
        self._log_event(session, {
            "type": CollaborationEventType.COMMENT_ADDED,
            "comment_id": comment.id,
            "user_id": user_id,
            "text": text,
            "node_id": node_id,
        })

    def get_collaborators(self, session_id: str) -> List[Dict]:
        """获取协作者列表"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return [{
            "id": c.id,
            "name": c.name,
            "avatar_url": c.avatar_url,
            "color": c.color,
            "cursor": c.cursor,
            "is_active": c.is_active,
        } for c in session.collaborators.values() if c.is_active]

    def get_comments(self, session_id: str) -> List[Dict]:
        """获取评论列表"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return [{
            "id": c.id,
            "author_id": c.author_id,
            "author_name": c.author_name,
            "text": c.text,
            "node_id": c.node_id,
            "position": c.position,
            "created_at": c.created_at.isoformat(),
            "resolved": c.resolved,
        } for c in session.comments]

    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """获取会话状态"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        doc = self.documents[session_id]
        return {
            "session_id": session.session_id,
            "workflow_id": session.workflow_id,
            "collaborators": self.get_collaborators(session_id),
            "comments": self.get_comments(session_id),
            "state": doc.get_state(),
            "created_at": session.created_at.isoformat(),
        }

    def _log_event(self, session: CollaborationSession, event: Dict):
        """记录事件"""
        session.event_log.append({
            **event,
            "timestamp": datetime.now().isoformat(),
        })
        if len(session.event_log) > 1000:
            session.event_log = session.event_log[-1000:]


class WebSocketManager:
    """WebSocket连接管理器（模拟）"""

    def __init__(self):
        self.clients: Dict[str, Dict] = {}

    async def connect_client(self, client_id: str, session_id: str):
        """连接客户端"""
        self.clients[client_id] = {
            "session_id": session_id,
            "connected_at": datetime.now(),
        }
        print(f"🔌 客户端 {client_id} 已连接到会话 {session_id}")

    async def disconnect_client(self, client_id: str):
        """断开客户端"""
        if client_id in self.clients:
            del self.clients[client_id]
            print(f"🔌 客户端 {client_id} 已断开连接")

    async def broadcast(self, session_id: str, message: Dict):
        """广播消息给会话中的所有人"""
        print(f"📢 广播消息到会话 {session_id}: {message}")
