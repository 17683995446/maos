"""
MAOS v13.0 - Enhanced Workflow Engine (State Machines)
增强型工作流引擎（状态机）
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio


class WorkflowState(Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class StepState(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    handler: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    state: StepState = StepState.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3


@dataclass
class StateTransition:
    """状态转换"""
    from_state: WorkflowState
    to_state: WorkflowState
    trigger: str
    action: Optional[Callable] = None


@dataclass
class WorkflowExecutionLog:
    """工作流执行日志"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    level: str = "info"
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateMachineWorkflow:
    """状态机工作流"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0"
    state: WorkflowState = WorkflowState.CREATED
    steps: List[WorkflowStep] = field(default_factory=list)
    transitions: List[StateTransition] = field(default_factory=list)
    logs: List[WorkflowExecutionLog] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, name: str, handler: Callable = None, dependencies: List[str] = None, description: str = "") -> WorkflowStep:
        """添加步骤"""
        step = WorkflowStep(
            name=name,
            handler=handler,
            dependencies=dependencies or [],
            description=description
        )
        self.steps.append(step)
        return step

    def add_transition(self, from_state: WorkflowState, to_state: WorkflowState, trigger: str, action: Callable = None) -> None:
        """添加状态转换"""
        transition = StateTransition(from_state, to_state, trigger, action)
        self.transitions.append(transition)

    def add_log(self, message: str, level: str = "info", data: Dict[str, Any] = None) -> None:
        """添加日志"""
        self.logs.append(WorkflowExecutionLog(
            message=message,
            level=level,
            data=data or {}
        ))

    def get_step_by_name(self, name: str) -> Optional[WorkflowStep]:
        """通过名称获取步骤"""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_ready_steps(self) -> List[WorkflowStep]:
        """获取准备就绪的步骤"""
        ready = []
        for step in self.steps:
            if step.state != StepState.PENDING:
                continue
            # 检查依赖是否都已完成
            all_deps_completed = True
            for dep_name in step.dependencies:
                dep_step = self.get_step_by_name(dep_name)
                if not dep_step or dep_step.state != StepState.COMPLETED:
                    all_deps_completed = False
                    break
            if all_deps_completed:
                ready.append(step)
        return ready


class StateMachineEngine:
    """状态机引擎"""

    def __init__(self):
        self._workflows: Dict[str, StateMachineWorkflow] = {}
        self._persistence: Dict[str, Dict] = {}  # 简单的持久化存储

    def create_workflow(self, name: str, description: str = "", version: str = "1.0") -> StateMachineWorkflow:
        """创建工作流"""
        workflow = StateMachineWorkflow(
            name=name,
            description=description,
            version=version
        )
        self._workflows[workflow.id] = workflow
        self._persist(workflow)
        print(f"📝 Workflow created: {name} ({workflow.id})")
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[StateMachineWorkflow]:
        """获取工作流"""
        return self._workflows.get(workflow_id)

    def _persist(self, workflow: StateMachineWorkflow) -> None:
        """持久化工作流"""
        self._persistence[workflow.id] = {
            "id": workflow.id,
            "state": workflow.state.value,
            "data": {
                "input": workflow.input_data,
                "output": workflow.output_data
            },
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "state": step.state.value,
                    "result": step.result,
                    "error": step.error
                }
                for step in workflow.steps
            ],
            "updated_at": datetime.now().isoformat()
        }

    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None) -> StateMachineWorkflow:
        """执行工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")
        
        if workflow.state not in [WorkflowState.CREATED, WorkflowState.PAUSED, WorkflowState.FAILED]:
            raise ValueError(f"Cannot execute workflow in state: {workflow.state}")
        
        workflow.input_data = input_data or {}
        workflow.state = WorkflowState.RUNNING
        workflow.started_at = datetime.now()
        workflow.add_log("Workflow started", "info", {"input": workflow.input_data})
        self._persist(workflow)
        
        print(f"🚀 Executing workflow: {workflow.name}")
        
        try:
            while workflow.state == WorkflowState.RUNNING:
                ready_steps = workflow.get_ready_steps()
                if not ready_steps:
                    # 检查是否所有步骤都已完成或失败
                    all_processed = all(
                        step.state in [StepState.COMPLETED, StepState.FAILED, StepState.SKIPPED]
                        for step in workflow.steps
                    )
                    if all_processed:
                        has_failed = any(step.state == StepState.FAILED for step in workflow.steps)
                        if has_failed:
                            workflow.state = WorkflowState.FAILED
                            workflow.error = "One or more steps failed"
                        else:
                            workflow.state = WorkflowState.COMPLETED
                        break
                    await asyncio.sleep(0.1)
                    continue
                
                # 执行就绪的步骤
                tasks = [self._execute_step(workflow, step) for step in ready_steps]
                await asyncio.gather(*tasks)
                self._persist(workflow)
            
            if workflow.state == WorkflowState.COMPLETED:
                workflow.completed_at = datetime.now()
                workflow.add_log("Workflow completed successfully", "info", {"output": workflow.output_data})
                print(f"✅ Workflow completed: {workflow.name}")
            
            self._persist(workflow)
            
        except Exception as e:
            workflow.state = WorkflowState.FAILED
            workflow.error = str(e)
            workflow.add_log(f"Workflow failed: {str(e)}", "error")
            self._persist(workflow)
            print(f"❌ Workflow failed: {workflow.name} - {str(e)}")
        
        return workflow

    async def _execute_step(self, workflow: StateMachineWorkflow, step: WorkflowStep) -> None:
        """执行步骤"""
        step.state = StepState.RUNNING
        step.started_at = datetime.now()
        workflow.add_log(f"Step started: {step.name}", "info")
        
        try:
            if step.handler:
                if asyncio.iscoroutinefunction(step.handler):
                    result = await step.handler(workflow.input_data)
                else:
                    result = step.handler(workflow.input_data)
                step.result = result
                workflow.output_data[step.name] = result
                step.state = StepState.COMPLETED
            else:
                # 没有处理器，标记为完成
                step.state = StepState.COMPLETED
            
            step.completed_at = datetime.now()
            workflow.add_log(f"Step completed: {step.name}", "info", {"result": step.result})
            
        except Exception as e:
            step.retries += 1
            if step.retries < step.max_retries:
                step.state = StepState.PENDING
                workflow.add_log(f"Step failed, retrying ({step.retries}/{step.max_retries}): {step.name}", "warning", {"error": str(e)})
            else:
                step.state = StepState.FAILED
                step.error = str(e)
                workflow.add_log(f"Step failed: {step.name}", "error", {"error": str(e)})

    async def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.state != WorkflowState.RUNNING:
            return False
        
        workflow.state = WorkflowState.PAUSED
        workflow.paused_at = datetime.now()
        workflow.add_log("Workflow paused", "info")
        self._persist(workflow)
        print(f"⏸️ Workflow paused: {workflow.name}")
        return True

    async def resume_workflow(self, workflow_id: str) -> bool:
        """恢复工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.state != WorkflowState.PAUSED:
            return False
        
        workflow.state = WorkflowState.RUNNING
        workflow.add_log("Workflow resumed", "info")
        self._persist(workflow)
        print(f"▶️ Workflow resumed: {workflow.name}")
        
        # 继续执行（不调用execute_workflow，因为会检查状态，而是直接继续执行逻辑）
        try:
            while workflow.state == WorkflowState.RUNNING:
                ready_steps = workflow.get_ready_steps()
                if not ready_steps:
                    # 检查是否所有步骤都已完成或失败
                    all_processed = all(
                        step.state in [StepState.COMPLETED, StepState.FAILED, StepState.SKIPPED]
                        for step in workflow.steps
                    )
                    if all_processed:
                        has_failed = any(step.state == StepState.FAILED for step in workflow.steps)
                        if has_failed:
                            workflow.state = WorkflowState.FAILED
                            workflow.error = "One or more steps failed"
                        else:
                            workflow.state = WorkflowState.COMPLETED
                        break
                    await asyncio.sleep(0.1)
                    continue
                
                # 执行就绪的步骤
                tasks = [self._execute_step(workflow, step) for step in ready_steps]
                await asyncio.gather(*tasks)
                self._persist(workflow)
            
            if workflow.state == WorkflowState.COMPLETED:
                workflow.completed_at = datetime.now()
                workflow.add_log("Workflow completed successfully", "info", {"output": workflow.output_data})
                print(f"✅ Workflow completed: {workflow.name}")
            
            self._persist(workflow)
            
        except Exception as e:
            workflow.state = WorkflowState.FAILED
            workflow.error = str(e)
            workflow.add_log(f"Workflow failed: {str(e)}", "error")
            self._persist(workflow)
            print(f"❌ Workflow failed: {workflow.name} - {str(e)}")
            
        return True

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.state in [WorkflowState.COMPLETED, WorkflowState.CANCELLED]:
            return False
        
        workflow.state = WorkflowState.CANCELLED
        workflow.add_log("Workflow cancelled", "warning")
        self._persist(workflow)
        print(f"🛑 Workflow cancelled: {workflow.name}")
        return True

    def get_workflow_history(self, workflow_id: str) -> List[WorkflowExecutionLog]:
        """获取工作流历史"""
        workflow = self.get_workflow(workflow_id)
        return workflow.logs if workflow else []
