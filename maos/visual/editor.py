"""
MAOS v11.0 - 可视化工作流编辑器核心引擎
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json


class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    AGENT = "agent"
    LLM = "llm"
    API_CALL = "api_call"
    DATA_TRANSFORM = "data_transform"
    LOOP = "loop"
    SUBWORKFLOW = "subworkflow"


class NodeStatus(Enum):
    """节点状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodePosition:
    """节点位置"""
    x: float = 0.0
    y: float = 0.0
    width: float = 180.0
    height: float = 80.0


@dataclass
class NodeConnection:
    """节点连接"""
    id: str
    from_node: str
    to_node: str
    from_port: str = "output"
    to_port: str = "input"
    condition: Optional[str] = None
    description: str = ""


@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str
    type: NodeType
    name: str
    position: NodePosition
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.IDLE
    error: Optional[str] = None
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "position": {
                "x": self.position.x,
                "y": self.position.y,
                "width": self.position.width,
                "height": self.position.height,
            },
            "config": self.config,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status.value,
            "error": self.error,
            "executionTime": self.execution_time,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowNode":
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            name=data["name"],
            position=NodePosition(
                x=data["position"].get("x", 0),
                y=data["position"].get("y", 0),
                width=data["position"].get("width", 180),
                height=data["position"].get("height", 80),
            ),
            config=data.get("config", {}),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            status=NodeStatus(data.get("status", "idle")),
            error=data.get("error"),
            execution_time=data.get("executionTime", 0),
        )


@dataclass
class Workflow:
    """工作流定义"""
    id: str
    name: str
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    connections: List[NodeConnection] = field(default_factory=list)
    version: int = 1
    author: str = "system"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_public: bool = False
    is_template: bool = False

    def add_node(self, node: WorkflowNode) -> "Workflow":
        self.nodes.append(node)
        self.updated_at = datetime.now()
        return self

    def remove_node(self, node_id: str) -> "Workflow":
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.connections = [c for c in self.connections
                           if c.from_node != node_id and c.to_node != node_id]
        self.updated_at = datetime.now()
        return self

    def connect_nodes(self, from_id: str, to_id: str,
                     condition: Optional[str] = None) -> "Workflow":
        connection = NodeConnection(
            id=str(uuid.uuid4()),
            from_node=from_id,
            to_node=to_id,
            condition=condition,
        )
        self.connections.append(connection)
        self.updated_at = datetime.now()
        return self

    def disconnect_nodes(self, from_id: str, to_id: str) -> "Workflow":
        self.connections = [c for c in self.connections
                           if not (c.from_node == from_id and c.to_node == to_id)]
        self.updated_at = datetime.now()
        return self

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_next_nodes(self, node_id: str) -> List[WorkflowNode]:
        next_ids = [c.to_node for c in self.connections if c.from_node == node_id]
        return [n for n in self.nodes if n.id in next_ids]

    def get_previous_nodes(self, node_id: str) -> List[WorkflowNode]:
        prev_ids = [c.from_node for c in self.connections if c.to_node == node_id]
        return [n for n in self.nodes if n.id in prev_ids]

    def validate(self) -> tuple[bool, List[str]]:
        errors = []
        node_ids = {n.id for n in self.nodes}

        # 检查连接
        for conn in self.connections:
            if conn.from_node not in node_ids:
                errors.append(f"Connection source not found: {conn.from_node}")
            if conn.to_node not in node_ids:
                errors.append(f"Connection target not found: {conn.to_node}")

        # 检查是否有开始和结束节点
        has_start = any(n.type == NodeType.START for n in self.nodes)
        has_end = any(n.type == NodeType.END for n in self.nodes)

        if not has_start:
            errors.append("Workflow must have a start node")
        if not has_end:
            errors.append("Workflow must have an end node")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "nodes": [n.to_dict() for n in self.nodes],
            "connections": [
                {
                    "id": c.id,
                    "fromNode": c.from_node,
                    "toNode": c.to_node,
                    "fromPort": c.from_port,
                    "toPort": c.to_port,
                    "condition": c.condition,
                    "description": c.description,
                }
                for c in self.connections
            ],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "isPublic": self.is_public,
            "isTemplate": self.is_template,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Workflow":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=[WorkflowNode.from_dict(n) for n in data.get("nodes", [])],
            connections=[
                NodeConnection(
                    id=c["id"],
                    from_node=c["fromNode"],
                    to_node=c["toNode"],
                    from_port=c.get("fromPort", "output"),
                    to_port=c.get("toPort", "input"),
                    condition=c.get("condition"),
                    description=c.get("description", ""),
                )
                for c in data.get("connections", [])
            ],
            version=data.get("version", 1),
            author=data.get("author", "system"),
            tags=data.get("tags", []),
            is_public=data.get("isPublic", False),
            is_template=data.get("isTemplate", False),
        )


class WorkflowEditor:
    """工作流编辑器"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, Workflow] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        # 简单数据处理模板
        data_template = Workflow(
            id="template-data-processing",
            name="数据处理流程",
            description="从API获取数据并处理",
            is_template=True,
        )

        start_node = WorkflowNode(
            id="start",
            type=NodeType.START,
            name="Start",
            position=NodePosition(x=100, y=200),
        )
        api_node = WorkflowNode(
            id="api-call",
            type=NodeType.API_CALL,
            name="API调用",
            position=NodePosition(x=350, y=200),
            config={"url": "https://api.example.com/data"},
        )
        transform_node = WorkflowNode(
            id="transform",
            type=NodeType.DATA_TRANSFORM,
            name="数据转换",
            position=NodePosition(x=600, y=200),
        )
        end_node = WorkflowNode(
            id="end",
            type=NodeType.END,
            name="End",
            position=NodePosition(x=850, y=200),
        )

        data_template.add_node(start_node)
        data_template.add_node(api_node)
        data_template.add_node(transform_node)
        data_template.add_node(end_node)

        data_template.connect_nodes("start", "api-call")
        data_template.connect_nodes("api-call", "transform")
        data_template.connect_nodes("transform", "end")

        self.templates[data_template.id] = data_template

        # LLM处理模板
        llm_template = Workflow(
            id="template-llm-processing",
            name="LLM处理流程",
            description="使用LLM进行自然语言处理",
            is_template=True,
        )

        start_node = WorkflowNode(
            id="start",
            type=NodeType.START,
            name="Start",
            position=NodePosition(x=100, y=200),
        )
        llm_node = WorkflowNode(
            id="llm",
            type=NodeType.LLM,
            name="LLM处理",
            position=NodePosition(x=350, y=200),
            config={"prompt": "分析以下数据："},
        )
        output_node = WorkflowNode(
            id="output",
            type=NodeType.TASK,
            name="输出结果",
            position=NodePosition(x=600, y=200),
        )
        end_node = WorkflowNode(
            id="end",
            type=NodeType.END,
            name="End",
            position=NodePosition(x=850, y=200),
        )

        llm_template.add_node(start_node)
        llm_template.add_node(llm_node)
        llm_template.add_node(output_node)
        llm_template.add_node(end_node)

        llm_template.connect_nodes("start", "llm")
        llm_template.connect_nodes("llm", "output")
        llm_template.connect_nodes("output", "end")

        self.templates[llm_template.id] = llm_template

    def create_workflow(self, name: str, description: str = "",
                       from_template: Optional[str] = None) -> Workflow:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())

        if from_template and from_template in self.templates:
            template = self.templates[from_template]
            workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
                nodes=[WorkflowNode(
                    id=str(uuid.uuid4()),
                    type=n.type,
                    name=n.name,
                    position=NodePosition(
                        x=n.position.x,
                        y=n.position.y,
                        width=n.position.width,
                        height=n.position.height,
                    ),
                    config=n.config.copy(),
                ) for n in template.nodes],
            )
            for conn in template.connections:
                # 简单复制连接，实际需要更复杂的ID映射
                pass
        else:
            # 创建空白工作流
            workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
            )

            # 添加默认的开始和结束节点
            start_node = WorkflowNode(
                id="start",
                type=NodeType.START,
                name="Start",
                position=NodePosition(x=100, y=200),
            )
            end_node = WorkflowNode(
                id="end",
                type=NodeType.END,
                name="End",
                position=NodePosition(x=700, y=200),
            )
            workflow.add_node(start_node)
            workflow.add_node(end_node)
            workflow.connect_nodes("start", "end")

        self.workflows[workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict]:
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "version": w.version,
                "updatedAt": w.updated_at.isoformat(),
            }
            for w in self.workflows.values()
        ]

    def list_templates(self) -> List[Dict]:
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
            }
            for t in self.templates.values()
        ]


# 节点库
class NodeLibrary:
    """节点库"""

    def __init__(self):
        self.node_types: Dict[NodeType, Dict] = {
            NodeType.START: {
                "name": "开始",
                "description": "工作流开始节点",
                "icon": "▶️",
                "config": {},
                "inputs": [],
                "outputs": ["output"],
            },
            NodeType.END: {
                "name": "结束",
                "description": "工作流结束节点",
                "icon": "⏹️",
                "config": {},
                "inputs": ["input"],
                "outputs": [],
            },
            NodeType.TASK: {
                "name": "任务",
                "description": "执行自定义任务",
                "icon": "📝",
                "config": {"script": "", "timeout": 30},
                "inputs": ["input"],
                "outputs": ["output"],
            },
            NodeType.CONDITION: {
                "name": "条件判断",
                "description": "条件分支",
                "icon": "🔀",
                "config": {"condition": ""},
                "inputs": ["input"],
                "outputs": ["true", "false"],
            },
            NodeType.PARALLEL: {
                "name": "并行执行",
                "description": "并行执行多个任务",
                "icon": "⚡",
                "config": {},
                "inputs": ["input"],
                "outputs": ["output"],
            },
            NodeType.AGENT: {
                "name": "Agent",
                "description": "调用Agent执行任务",
                "icon": "🤖",
                "config": {"agentId": "", "agentConfig": {}},
                "inputs": ["input"],
                "outputs": ["output"],
            },
            NodeType.LLM: {
                "name": "LLM",
                "description": "调用LLM进行处理",
                "icon": "🧠",
                "config": {"prompt": "", "model": "gpt-4"},
                "inputs": ["input"],
                "outputs": ["output"],
            },
            NodeType.API_CALL: {
                "name": "API调用",
                "description": "调用外部API",
                "icon": "🌐",
                "config": {"url": "", "method": "GET", "headers": {}},
                "inputs": ["input"],
                "outputs": ["output"],
            },
            NodeType.DATA_TRANSFORM: {
                "name": "数据转换",
                "description": "转换和处理数据",
                "icon": "🔄",
                "config": {"transform": ""},
                "inputs": ["input"],
                "outputs": ["output"],
            },
            NodeType.LOOP: {
                "name": "循环",
                "description": "循环执行",
                "icon": "🔁",
                "config": {"maxIterations": 100},
                "inputs": ["input"],
                "outputs": ["output"],
            },
        }

    def get_node_types(self) -> List[Dict]:
        """获取所有节点类型"""
        return [
            {
                "type": t.value,
                **self.node_types[t],
            }
            for t in self.node_types
        ]

    def get_node_type(self, node_type: NodeType) -> Optional[Dict]:
        """获取特定节点类型"""
        return self.node_types.get(node_type)
