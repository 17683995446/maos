"""
MAOS v8.0 - Agent协作协议
Multi-Agent协作框架和通信协议
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import uuid


class CollaborationState(Enum):
    """协作状态"""
    IDLE = "idle"
    NEGOTIATING = "negotiating"
    EXECUTING = "executing"
    SYNCHRONIZING = "synchronizing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(Enum):
    """消息类型"""
    TASK_ANNOUNCE = "task_announce"
    BID_OFFER = "bid_offer"
    BID_ACCEPT = "bid_accept"
    BID_REJECT = "bid_reject"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    STATUS_UPDATE = "status_update"
    RESULT_SHARE = "result_share"
    COORDINATION_REQUEST = "coordination_request"


@dataclass
class CollaborationMessage:
    """协作消息"""
    message_id: str
    sender_id: str
    receiver_id: Optional[str] = None
    message_type: MessageType = MessageType.STATUS_UPDATE
    content: Any = None
    timestamp: float = field(default_factory=time.time)
    ttl: int = 60
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CollaborationMessage':
        return cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            timestamp=data["timestamp"]
        )


@dataclass
class TaskContract:
    """Agent协作契约"""
    contract_id: str
    task_id: str
    coordinator_id: str
    participant_ids: List[str]
    task_requirements: List[str]
    roles: Dict[str, str]
    start_time: Optional[float] = None
    deadline: Optional[float] = None
    state: CollaborationState = CollaborationState.IDLE


class CollaboratingAgent:
    """可协作的Agent"""
    
    def __init__(self, agent_id: str, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.state = CollaborationState.IDLE
        self.message_queue: deque = deque()
        self.known_agents: Set[str] = set()
        self.active_contracts: Dict[str, TaskContract] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.data_store: Dict[str, Any] = {}
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type].append(handler)
    
    def discover_agent(self, other_agent_id: str):
        """发现其他Agent"""
        self.known_agents.add(other_agent_id)
    
    def send_message(self, message: CollaborationMessage, bus: 'CollaborationBus'):
        """发送消息到协作总线"""
        bus.send_message(message)
    
    def receive_message(self, message: CollaborationMessage):
        """接收消息"""
        self.message_queue.append(message)
    
    async def process_messages(self):
        """处理收到的消息"""
        while self.message_queue:
            message = self.message_queue.popleft()
            handlers = self.message_handlers.get(message.message_type, [])
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
    
    def submit_bid(self, task_id: str, bus: 'CollaborationBus', price: float = 1.0, capability_score: float = 0.8):
        """提交竞标"""
        message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            message_type=MessageType.BID_OFFER,
            content={
                "task_id": task_id,
                "price": price,
                "capability_score": capability_score
            }
        )
        bus.send_message(message)
    
    def share_result(self, task_id: str, result: Any, bus: 'CollaborationBus'):
        """分享结果"""
        message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            message_type=MessageType.RESULT_SHARE,
            content={
                "task_id": task_id,
                "result": result
            }
        )
        bus.send_message(message)


class CollaborationBus:
    """协作消息总线"""
    
    def __init__(self):
        self.agents: Dict[str, CollaboratingAgent] = {}
        self.undelivered_messages: deque = deque()
        self.delivery_history: List[Dict] = []
        self.message_count = 0
    
    def register_agent(self, agent: CollaboratingAgent):
        """注册Agent到总线"""
        self.agents[agent.agent_id] = agent
        print(f"🤝 Agent {agent.agent_id} registered on bus")
    
    def send_message(self, message: CollaborationMessage):
        """发送消息"""
        self.message_count += 1
        
        if message.receiver_id:
            # 点对点消息
            if message.receiver_id in self.agents:
                self.agents[message.receiver_id].receive_message(message)
                self._record_delivery(message, "direct")
            else:
                self.undelivered_messages.append(message)
        else:
            # 广播消息
            for agent_id, agent in self.agents.items():
                if agent_id != message.sender_id:
                    agent.receive_message(message)
            self._record_delivery(message, "broadcast")
    
    def _record_delivery(self, message: CollaborationMessage, delivery_type: str):
        """记录消息投递"""
        self.delivery_history.append({
            "message_id": message.message_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "type": delivery_type,
            "timestamp": time.time()
        })
    
    async def process_all_agents(self):
        """处理所有Agent的消息"""
        tasks = [agent.process_messages() for agent in self.agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict:
        """获取总线统计"""
        return {
            "registered_agents": len(self.agents),
            "total_messages": self.message_count,
            "undelivered_messages": len(self.undelivered_messages),
            "delivery_history_count": len(self.delivery_history)
        }


class CollaborativeOrchestrator:
    """多Agent协作编排器"""
    
    def __init__(self):
        self.bus = CollaborationBus()
        self.contracts: Dict[str, TaskContract] = {}
        self.active_tasks: Dict[str, Dict] = {}
    
    def create_collaboration(self, task_id: str, requirements: List[str]) -> TaskContract:
        """创建协作任务"""
        contract = TaskContract(
            contract_id=str(uuid.uuid4()),
            task_id=task_id,
            coordinator_id="coordinator",
            participant_ids=[],
            task_requirements=requirements,
            roles={}
        )
        self.contracts[contract.contract_id] = contract
        return contract
    
    def announce_task(self, contract: TaskContract):
        """广播任务公告"""
        announce_message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            sender_id="coordinator",
            message_type=MessageType.TASK_ANNOUNCE,
            content={
                "contract_id": contract.contract_id,
                "task_id": contract.task_id,
                "requirements": contract.task_requirements
            }
        )
        self.bus.send_message(announce_message)
    
    def collect_bids(self, contract_id: str) -> List[Dict]:
        """收集竞标（简化版）"""
        contract = self.contracts.get(contract_id)
        if not contract:
            return []
        
        bids = []
        for agent_id, agent in self.bus.agents.items():
            bid = {
                "agent_id": agent_id,
                "capabilities": agent.capabilities,
                "score": len(agent.capabilities)
            }
            bids.append(bid)
        
        # 选择最高评分的Agent
        bids.sort(key=lambda x: x["score"], reverse=True)
        selected_bids = bids[:3]
        
        return selected_bids
    
    def form_collaboration(self, contract: TaskContract, selected_agents: List[str]):
        """形成协作团队"""
        contract.participant_ids = selected_agents
        contract.state = CollaborationState.EXECUTING
        
        for i, agent_id in enumerate(selected_agents):
            contract.roles[agent_id] = f"role_{i+1}"
        
        # 通知选中的Agent
        for agent_id in selected_agents:
            accept_msg = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                sender_id="coordinator",
                receiver_id=agent_id,
                message_type=MessageType.BID_ACCEPT,
                content={
                    "contract_id": contract.contract_id,
                    "role": contract.roles[agent_id]
                }
            )
            self.bus.send_message(accept_msg)
        
        print(f"🤝 Formed collaboration with agents: {selected_agents}")
