"""
MAOS v9.0 - 高级工作流引擎
复杂工作流编排和执行
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import asyncio


class NodeType(Enum):
    """工作流节点类型"""
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    SEQUENCE = "sequence"
    LOOP = "loop"
    SUBWORKFLOW = "subworkflow"
    START = "start"
    END = "end"
    INPUT = "input"
    OUTPUT = "output"


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    node_type: NodeType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})
    retry_count: int = 0
    timeout: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "config": self.config,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "position": self.position
        }


@dataclass
class WorkflowEdge:
    """工作流边"""
    edge_id: str
    source_node: str
    target_node: str
    condition: Optional[str] = None
    label: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "edge_id": self.edge_id,
            "source": self.source_node,
            "target": self.target_node,
            "condition": self.condition,
            "label": self.label
        }


@dataclass
class WorkflowExecution:
    """工作流执行"""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_node: Optional[str] = None
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_node": self.current_node,
            "outputs": self.node_outputs
        }


class Workflow:
    """工作流定义"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str = ""
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.input_schema: Dict[str, Any] = {}
        self.output_schema: Dict[str, Any] = {}
        self.version: int = 1
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.created_by: str = "system"
        self.is_active: bool = True
    
    def add_node(self, node: WorkflowNode):
        """添加节点"""
        self.nodes[node.node_id] = node
        self.updated_at = datetime.now()
    
    def add_edge(self, edge: WorkflowEdge):
        """添加边"""
        self.edges.append(edge)
        self.updated_at = datetime.now()
    
    def get_start_node(self) -> Optional[WorkflowNode]:
        """获取开始节点"""
        for node in self.nodes.values():
            if node.node_type == NodeType.START:
                return node
        return None
    
    def get_end_nodes(self) -> List[WorkflowNode]:
        """获取结束节点"""
        return [node for node in self.nodes.values() if node.node_type == NodeType.END]
    
    def get_next_nodes(self, node_id: str) -> List[str]:
        """获取后续节点"""
        next_nodes = []
        for edge in self.edges:
            if edge.source_node == node_id:
                next_nodes.append(edge.target_node)
        return next_nodes
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证工作流"""
        errors = []
        
        # 检查开始节点
        start_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.START]
        if not start_nodes:
            errors.append("工作流必须有开始节点")
        
        # 检查结束节点
        end_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.END]
        if not end_nodes:
            errors.append("工作流必须有结束节点")
        
        # 检查孤立节点
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.source_node)
            connected_nodes.add(edge.target_node)
        
        for node_id, node in self.nodes.items():
            if node_id not in connected_nodes and node.node_type not in [NodeType.START, NodeType.END]:
                errors.append(f"节点 {node.name} 未连接到工作流")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.node_handlers: Dict[NodeType, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理器"""
        self.node_handlers[NodeType.TASK] = self._handle_task_node
        self.node_handlers[NodeType.CONDITION] = self._handle_condition_node
        self.node_handlers[NodeType.PARALLEL] = self._handle_parallel_node
        self.node_handlers[NodeType.SEQUENCE] = self._handle_sequence_node
    
    def register_workflow(self, workflow: Workflow) -> str:
        """注册工作流"""
        valid, errors = workflow.validate()
        if not valid:
            raise ValueError(f"工作流验证失败: {', '.join(errors)}")
        
        self.workflows[workflow.workflow_id] = workflow
        return workflow.workflow_id
    
    async def execute(self, workflow_id: str, input_data: Dict[str, Any] = None) -> str:
        """执行工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        # 创建执行实例
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        self.executions[execution.execution_id] = execution
        
        # 执行工作流
        try:
            await self._execute_workflow(workflow, execution, input_data or {})
            execution.status = ExecutionStatus.COMPLETED
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
        
        execution.completed_at = datetime.now()
        return execution.execution_id
    
    async def _execute_workflow(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        input_data: Dict[str, Any]
    ):
        """执行工作流"""
        execution.node_outputs["_input"] = input_data
        
        # 获取开始节点
        current_node = workflow.get_start_node()
        if not current_node:
            raise ValueError("工作流没有开始节点")
        
        # 执行直到结束
        while current_node and current_node.node_type != NodeType.END:
            execution.current_node = current_node.node_id
            
            # 执行当前节点
            handler = self.node_handlers.get(current_node.node_type)
            if handler:
                await handler(workflow, execution, current_node)
            
            # 获取下一个节点
            next_nodes = workflow.get_next_nodes(current_node.node_id)
            if not next_nodes:
                break
            
            # 简化处理：取第一个后续节点
            next_node_id = next_nodes[0]
            current_node = workflow.nodes.get(next_node_id)
        
        execution.current_node = None
    
    async def _handle_task_node(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        node: WorkflowNode
    ):
        """处理任务节点"""
        # 模拟任务执行
        task_config = node.config
        task_name = task_config.get("name", node.name)
        
        # 获取输入
        inputs = execution.node_outputs.get("_input", {})
        for input_name in node.inputs:
            if input_name in execution.node_outputs:
                inputs[input_name] = execution.node_outputs[input_name]
        
        # 执行任务（模拟）
        result = {
            "status": "completed",
            "output": f"Task '{task_name}' executed successfully"
        }
        
        # 保存输出
        execution.node_outputs[node.node_id] = result
        
        # 如果有输出映射
        if "output_key" in task_config:
            execution.node_outputs[task_config["output_key"]] = result["output"]
    
    async def _handle_condition_node(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        node: WorkflowNode
    ):
        """处理条件节点"""
        condition = node.config.get("condition", "true")
        # 简化：总是执行第一条分支
        execution.node_outputs[node.node_id] = {"condition_result": True}
    
    async def _handle_parallel_node(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        node: WorkflowNode
    ):
        """处理并行节点"""
        # 获取所有并行分支
        branches = workflow.get_next_nodes(node.node_id)
        
        # 并行执行（简化）
        results = []
        for branch_id in branches:
            results.append({"branch": branch_id, "status": "completed"})
        
        execution.node_outputs[node.node_id] = {"parallel_results": results}
    
    async def _handle_sequence_node(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        node: WorkflowNode
    ):
        """处理序列节点"""
        execution.node_outputs[node.node_id] = {"sequence_processed": True}
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态"""
        return self.executions.get(execution_id)
    
    def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        return [w.to_dict() for w in self.workflows.values()]
    
    def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict]:
        """列出执行记录"""
        executions = self.executions.values()
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        return [e.to_dict() for e in executions]


# 工作流DSL解析器
class WorkflowDSLParser:
    """工作流DSL解析器"""
    
    @staticmethod
    def from_dict(data: Dict) -> Workflow:
        """从字典创建工作流"""
        workflow = Workflow(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", "")
        )
        
        # 解析节点
        for node_data in data.get("nodes", []):
            node = WorkflowNode(
                node_id=node_data["node_id"],
                node_type=NodeType(node_data["node_type"]),
                name=node_data["name"],
                config=node_data.get("config", {}),
                inputs=node_data.get("inputs", []),
                outputs=node_data.get("outputs", []),
                position=node_data.get("position", {"x": 0, "y": 0})
            )
            workflow.add_node(node)
        
        # 解析边
        for edge_data in data.get("edges", []):
            edge = WorkflowEdge(
                edge_id=edge_data["edge_id"],
                source_node=edge_data["source"],
                target_node=edge_data["target"],
                condition=edge_data.get("condition"),
                label=edge_data.get("label")
            )
            workflow.add_edge(edge)
        
        return workflow
    
    @staticmethod
    def from_yaml(yaml_str: str) -> Workflow:
        """从YAML字符串创建工作流（简化版）"""
        # 简化实现
        import yaml
        data = yaml.safe_load(yaml_str)
        return WorkflowDSLParser.from_dict(data)
