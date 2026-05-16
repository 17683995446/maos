"""
Orchestrator Service Module for MAOS
编排器核心 - 负责任务编排、Agent协调、工作流执行和系统监控
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable, AsyncIterable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import time
from collections import defaultdict
import uuid


class ExecutionStrategy(Enum):
    """执行策略枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


class OrchestratorEventType(Enum):
    """编排器事件类型"""
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    TASK_RETRIED = "task_retried"
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    SYSTEM_ERROR = "system_error"


@dataclass
class OrchestratorEvent:
    """编排器事件"""
    event_type: OrchestratorEventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "orchestrator"


@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    name: str
    requirements: List[str] = field(default_factory=list)
    description: str = ""
    priority: int = 2
    input_mapping: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    agent_selection: Optional[str] = None


@dataclass
class Workflow:
    """工作流定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    strategy: ExecutionStrategy = ExecutionStrategy.HYBRID
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventEmitter:
    """事件发射器"""
    
    def __init__(self):
        self._listeners: Dict[OrchestratorEventType, List[Callable]] = defaultdict(list)
        self._async_listeners: Dict[OrchestratorEventType, List[Callable]] = defaultdict(list)
    
    def on(self, event_type: OrchestratorEventType, handler: Callable) -> None:
        """注册同步事件监听器"""
        if asyncio.iscoroutinefunction(handler):
            self._async_listeners[event_type].append(handler)
        else:
            self._listeners[event_type].append(handler)
    
    def off(self, event_type: OrchestratorEventType, handler: Callable) -> None:
        """注销事件监听器"""
        if handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)
        if handler in self._async_listeners[event_type]:
            self._async_listeners[event_type].remove(handler)
    
    async def emit_async(self, event: OrchestratorEvent) -> None:
        """异步触发事件"""
        for handler in self._listeners[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in sync event handler: {e}")
        
        for handler in self._async_listeners[event.event_type]:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in async event handler: {e}")
    
    def emit(self, event: OrchestratorEvent) -> None:
        """同步触发事件"""
        for handler in self._listeners[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")


class AgentRegistry:
    """Agent注册表"""
    
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._capabilities: Dict[str, List[str]] = {}
        self._status: Dict[str, str] = {}
    
    def register(self, agent: Any) -> bool:
        """注册Agent"""
        if not hasattr(agent, 'name'):
            return False
        
        self._agents[agent.name] = agent
        self._capabilities[agent.name] = getattr(agent, 'capabilities', [])
        self._status[agent.name] = getattr(agent, 'status', 'idle')
        return True
    
    def unregister(self, agent_name: str) -> bool:
        """注销Agent"""
        if agent_name in self._agents:
            del self._agents[agent_name]
            if agent_name in self._capabilities:
                del self._capabilities[agent_name]
            if agent_name in self._status:
                del self._status[agent_name]
            return True
        return False
    
    def get_agent(self, name: str) -> Optional[Any]:
        """获取Agent"""
        return self._agents.get(name)
    
    def get_all_agents(self) -> List[Any]:
        """获取所有Agent"""
        return list(self._agents.values())
    
    def get_available_agents(self) -> List[Any]:
        """获取可用Agent"""
        return [
            agent for agent in self._agents.values()
            if getattr(agent, 'status', 'busy') != 'busy'
        ]
    
    def select_best_agent(self, requirements: List[str]) -> Optional[Any]:
        """选择最佳Agent"""
        if not requirements:
            return self.get_available_agents()[0] if self.get_available_agents() else None
        
        scored_agents = []
        for agent_name, capabilities in self._capabilities.items():
            score = sum(1 for req in requirements if req in capabilities)
            if score > 0 and self._status.get(agent_name) != 'busy':
                scored_agents.append((score, self._agents[agent_name]))
        
        if scored_agents:
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            return scored_agents[0][1]
        
        return self.get_available_agents()[0] if self.get_available_agents() else None
    
    def update_agent_status(self, agent_name: str, status: str) -> bool:
        """更新Agent状态"""
        if agent_name in self._agents:
            self._status[agent_name] = status
            if hasattr(self._agents[agent_name], 'status'):
                self._agents[agent_name].status = status
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        status_counts = defaultdict(int)
        for status in self._status.values():
            status_counts[status] += 1
        
        return {
            'total': len(self._agents),
            'by_status': dict(status_counts),
            'capabilities': self._capabilities.copy()
        }


class MessageBroker:
    """消息代理"""
    
    def __init__(self):
        self._messages: List[Dict[str, Any]] = []
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def publish(self, message: Dict[str, Any]) -> None:
        """发布消息"""
        message['timestamp'] = datetime.now().isoformat()
        message['id'] = str(uuid.uuid4())
        self._messages.append(message)
        
        for subscriber in self._subscribers.get(message.get('type', 'default'), []):
            try:
                subscriber(message)
            except Exception as e:
                print(f"Error in message subscriber: {e}")
    
    def subscribe(self, msg_type: str, handler: Callable) -> None:
        """订阅消息"""
        self._subscribers[msg_type].append(handler)
    
    def unsubscribe(self, msg_type: str, handler: Callable) -> None:
        """取消订阅"""
        if handler in self._subscribers[msg_type]:
            self._subscribers[msg_type].remove(handler)
    
    def get_messages(self, msg_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取消息历史"""
        if msg_type:
            return [m for m in self._messages if m.get('type') == msg_type][-limit:]
        return self._messages[-limit:]


class OrchestratorService:
    """编排器服务核心类"""
    
    def __init__(
        self,
        name: str = "maos_orchestrator",
        max_concurrent_tasks: int = 10,
        execution_strategy: ExecutionStrategy = ExecutionStrategy.HYBRID,
        enable_streaming: bool = True
    ):
        self.name = name
        self.agent_registry = AgentRegistry()
        self.message_broker = MessageBroker()
        self.event_emitter = EventEmitter()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.execution_strategy = execution_strategy
        self.enable_streaming = enable_streaming
        self.running = False
        self._execution_times: Dict[str, float] = {}
        self._task_manager = None
        self._lock = asyncio.Lock()
        self._workflow_tasks: Dict[str, List[str]] = {}
    
    def set_task_manager(self, task_manager: Any) -> None:
        """设置任务管理器"""
        self._task_manager = task_manager
    
    def _safe_emit_async(self, event: OrchestratorEvent) -> None:
        """安全地异步触发事件，如果没有运行的事件循环则静默忽略"""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.event_emitter.emit_async(event))
        except RuntimeError:
            pass

    def register_agent(self, agent: Any) -> bool:
        """注册Agent"""
        success = self.agent_registry.register(agent)
        if success:
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.AGENT_REGISTERED,
                data={'agent_name': agent.name, 'agent': agent}
            )
            self.event_emitter.emit(event)
            self._safe_emit_async(event)
        return success
    
    def register_agents(self, agents: List[Any]) -> Dict[str, bool]:
        """批量注册Agent"""
        results = {}
        for agent in agents:
            results[agent.name] = self.register_agent(agent)
        return results
    
    def unregister_agent(self, agent_name: str) -> bool:
        """注销Agent"""
        success = self.agent_registry.unregister(agent_name)
        if success:
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.AGENT_UNREGISTERED,
                data={'agent_name': agent_name}
            )
            self.event_emitter.emit(event)
            self._safe_emit_async(event)
        return success
    
    def on_event(self, event_type: OrchestratorEventType, handler: Callable) -> None:
        """注册事件处理器"""
        self.event_emitter.on(event_type, handler)
    
    def off_event(self, event_type: OrchestratorEventType, handler: Callable) -> None:
        """注销事件处理器"""
        self.event_emitter.off(event_type, handler)
    
    async def create_task_async(
        self,
        name: str,
        requirements: List[str],
        description: str = "",
        priority: Any = None,
        input_data: Any = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """异步创建任务"""
        from maos.orchestration.task_manager import TaskPriority, Task
        
        if self._task_manager:
            if hasattr(self._task_manager, 'create_task_async'):
                task = await self._task_manager.create_task_async(
                    name=name,
                    requirements=requirements,
                    description=description,
                    priority=priority or TaskPriority.NORMAL,
                    input_data=input_data,
                    dependencies=dependencies,
                    metadata=metadata
                )
            else:
                task = self._task_manager.create_task(
                    name=name,
                    requirements=requirements,
                    description=description,
                    priority=priority or TaskPriority.NORMAL,
                    input_data=input_data,
                    dependencies=dependencies,
                    metadata=metadata
                )
            
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.TASK_CREATED,
                data={'task': task}
            )
            await self.event_emitter.emit_async(event)
            return task
        return None
    
    def create_task(
        self,
        name: str,
        requirements: List[str],
        description: str = "",
        priority: Any = None,
        input_data: Any = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """同步创建任务"""
        from maos.orchestration.task_manager import TaskPriority, Task
        
        if self._task_manager:
            task = self._task_manager.create_task(
                name=name,
                requirements=requirements,
                description=description,
                priority=priority or TaskPriority.NORMAL,
                input_data=input_data,
                dependencies=dependencies,
                metadata=metadata
            )
            
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.TASK_CREATED,
                data={'task': task}
            )
            self.event_emitter.emit(event)
            return task
        return None
    
    def assign_task_to_agent(self, task: Any, agent_name: str) -> bool:
        """分配任务给Agent"""
        if not task or not agent_name:
            return False
        
        agent = self.agent_registry.get_agent(agent_name)
        if not agent:
            return False
        
        if hasattr(task, 'assigned_agent'):
            task.assigned_agent = agent_name
        
        if hasattr(self._task_manager, 'assign_task'):
            self._task_manager.assign_task(task.id, agent_name)
        
        self.agent_registry.update_agent_status(agent_name, 'busy')
        
        event = OrchestratorEvent(
            event_type=OrchestratorEventType.TASK_ASSIGNED,
            data={'task': task, 'agent_name': agent_name}
        )
        self.event_emitter.emit(event)
        self._safe_emit_async(event)
        
        return True
    
    async def execute_task_async(self, task: Any) -> Any:
        """异步执行任务"""
        if not task:
            return None
        
        if not getattr(task, 'assigned_agent', None):
            agent = self.agent_registry.select_best_agent(getattr(task, 'requirements', []))
            if agent:
                self.assign_task_to_agent(task, agent.name)
            else:
                if hasattr(task, 'mark_failed'):
                    task.mark_failed("No available agent")
                event = OrchestratorEvent(
                    event_type=OrchestratorEventType.TASK_FAILED,
                    data={'task': task, 'error': 'No available agent'}
                )
                await self.event_emitter.emit_async(event)
                return None
        
        agent = self.agent_registry.get_agent(task.assigned_agent)
        if not agent:
            if hasattr(task, 'mark_failed'):
                task.mark_failed("Agent not found")
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.TASK_FAILED,
                data={'task': task, 'error': 'Agent not found'}
            )
            await self.event_emitter.emit_async(event)
            return None
        
        start_time = time.time()
        
        if hasattr(task, 'mark_running'):
            task.mark_running()
        
        event = OrchestratorEvent(
            event_type=OrchestratorEventType.TASK_STARTED,
            data={'task': task, 'agent': agent}
        )
        await self.event_emitter.emit_async(event)
        
        try:
            result = None
            if hasattr(agent, 'process_task'):
                result = await agent.process_task(task)
            elif hasattr(agent, 'execute'):
                result = await agent.execute(getattr(task, 'input_data', None))
            elif hasattr(agent, '__call__'):
                result = await agent(getattr(task, 'input_data', None))
            
            if hasattr(task, 'mark_completed'):
                task.mark_completed(result)
            
            self.agent_registry.update_agent_status(agent.name, 'idle')
            
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.TASK_COMPLETED,
                data={'task': task, 'result': result, 'agent': agent}
            )
            await self.event_emitter.emit_async(event)
            
            self._execution_times[f"task_{task.id}"] = time.time() - start_time
            
            return result
            
        except Exception as e:
            if hasattr(task, 'mark_failed'):
                task.mark_failed(str(e))
            
            self.agent_registry.update_agent_status(agent.name, 'error')
            
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.TASK_FAILED,
                data={'task': task, 'error': str(e), 'agent': agent}
            )
            await self.event_emitter.emit_async(event)
            
            return None
    
    async def execute_workflow_async(
        self,
        workflow: Workflow,
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """异步执行工作流"""
        if not self._task_manager:
            return {'error': 'No task manager configured'}
        
        workflow_id = workflow.id
        self._workflow_tasks[workflow_id] = []
        
        event = OrchestratorEvent(
            event_type=OrchestratorEventType.WORKFLOW_STARTED,
            data={'workflow': workflow, 'input_data': input_data}
        )
        await self.event_emitter.emit_async(event)
        
        results = {}
        task_map = {}
        
        try:
            for step in workflow.steps:
                mapped_input = input_data.copy() if input_data else {}
                for target, source in step.input_mapping.items():
                    if source in input_data:
                        mapped_input[target] = input_data[source]
                
                dependencies = []
                for dep_name in step.dependencies:
                    if dep_name in task_map:
                        dependencies.append(task_map[dep_name].id)
                
                task = await self.create_task_async(
                    name=step.name,
                    requirements=step.requirements,
                    description=step.description,
                    priority=self._get_priority_from_int(step.priority),
                    input_data=mapped_input,
                    dependencies=dependencies
                )
                
                if task:
                    task_map[step.name] = task
                    self._workflow_tasks[workflow_id].append(task.id)
            
            if workflow.strategy == ExecutionStrategy.SEQUENTIAL:
                for step in workflow.steps:
                    task = task_map.get(step.name)
                    if task:
                        result = await self.execute_task_async(task)
                        results[step.name] = result
            
            elif workflow.strategy == ExecutionStrategy.PARALLEL:
                tasks_to_execute = [
                    self.execute_task_async(task_map[step.name])
                    for step in workflow.steps if step.name in task_map
                ]
                parallel_results = await asyncio.gather(*tasks_to_execute, return_exceptions=True)
                for step, result in zip(workflow.steps, parallel_results):
                    if isinstance(result, Exception):
                        results[step.name] = {'error': str(result)}
                    else:
                        results[step.name] = result
            
            elif workflow.strategy == ExecutionStrategy.HYBRID:
                ready_tasks = []
                completed_names = set()
                
                for step in workflow.steps:
                    if not step.dependencies or all(dep in completed_names for dep in step.dependencies):
                        task = task_map.get(step.name)
                        if task:
                            ready_tasks.append(self.execute_and_track(task, step.name, results, completed_names))
                
                if ready_tasks:
                    await asyncio.gather(*ready_tasks, return_exceptions=True)
            
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.WORKFLOW_COMPLETED,
                data={'workflow': workflow, 'results': results}
            )
            await self.event_emitter.emit_async(event)
            
            return results
            
        except Exception as e:
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.WORKFLOW_FAILED,
                data={'workflow': workflow, 'error': str(e)}
            )
            await self.event_emitter.emit_async(event)
            return {'error': str(e)}
    
    async def execute_and_track(
        self,
        task: Any,
        step_name: str,
        results: Dict[str, Any],
        completed_names: set
    ) -> Any:
        """执行并跟踪任务"""
        result = await self.execute_task_async(task)
        results[step_name] = result
        completed_names.add(step_name)
        return result
    
    def execute_workflow(
        self,
        workflow: Workflow,
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """同步执行工作流"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self.execute_workflow_async(workflow, input_data))
                return {'status': 'started', 'workflow_id': workflow.id}
            else:
                return loop.run_until_complete(self.execute_workflow_async(workflow, input_data))
        except RuntimeError:
            return asyncio.run(self.execute_workflow_async(workflow, input_data))
    
    def broadcast_message(
        self,
        content: Any,
        sender: str = None,
        msg_type: str = "broadcast"
    ) -> None:
        """广播消息"""
        message = {
            'type': msg_type,
            'sender': sender or self.name,
            'content': content,
            'receivers': [agent.name for agent in self.agent_registry.get_all_agents()]
        }
        self.message_broker.publish(message)
        
        event = OrchestratorEvent(
            event_type=OrchestratorEventType.MESSAGE_SENT,
            data={'message': message, 'broadcast': True}
        )
        self.event_emitter.emit(event)
        self._safe_emit_async(event)
    
    def send_message(
        self,
        receiver: str,
        content: Any,
        sender: str = None,
        msg_type: str = "direct"
    ) -> bool:
        """发送消息"""
        agent = self.agent_registry.get_agent(receiver)
        if not agent:
            return False
        
        message = {
            'type': msg_type,
            'sender': sender or self.name,
            'receiver': receiver,
            'content': content
        }
        self.message_broker.publish(message)
        
        event = OrchestratorEvent(
            event_type=OrchestratorEventType.MESSAGE_SENT,
            data={'message': message, 'broadcast': False}
        )
        self.event_emitter.emit(event)
        self._safe_emit_async(event)
        
        return True
    
    async def stream_response(
        self,
        task: Any,
        callback: Callable[[Any], Awaitable[None]]
    ) -> AsyncIterable[Any]:
        """流式响应生成器"""
        if not self.enable_streaming:
            result = await self.execute_task_async(task)
            yield {'type': 'final', 'data': result}
            return
        
        agent = self.agent_registry.get_agent(getattr(task, 'assigned_agent', None))
        if not agent:
            yield {'type': 'error', 'data': 'No agent assigned'}
            return
        
        try:
            if hasattr(agent, 'stream_process'):
                async for chunk in agent.stream_process(task):
                    await callback(chunk)
                    yield {'type': 'chunk', 'data': chunk}
            else:
                result = await self.execute_task_async(task)
                yield {'type': 'final', 'data': result}
                
        except Exception as e:
            yield {'type': 'error', 'data': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'name': self.name,
            'running': self.running,
            'execution_strategy': self.execution_strategy.value,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'enable_streaming': self.enable_streaming,
            'agents': self.agent_registry.get_statistics(),
            'messages_count': len(self.message_broker._messages)
        }
        
        if self._task_manager:
            status['tasks'] = self._task_manager.get_statistics()
            status['performance'] = self._task_manager.get_performance_metrics()
        
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'system': self.get_system_status(),
            'execution_times': self._execution_times.copy(),
            'workflows': {
                wf_id: len(tasks) 
                for wf_id, tasks in self._workflow_tasks.items()
            }
        }
    
    async def start(self) -> None:
        """启动编排器"""
        self.running = True
        print(f"Orchestrator '{self.name}' started")
    
    async def stop(self) -> None:
        """停止编排器"""
        self.running = False
        for agent in self.agent_registry.get_all_agents():
            self.agent_registry.update_agent_status(agent.name, 'stopped')
        print(f"Orchestrator '{self.name}' stopped")
    
    def shutdown(self) -> None:
        """关闭编排器"""
        self.running = False
        for agent in self.agent_registry.get_all_agents():
            self.agent_registry.update_agent_status(agent.name, 'terminated')
    
    @staticmethod
    def _get_priority_from_int(priority: int):
        """将整数优先级转换为TaskPriority枚举"""
        from maos.orchestration.task_manager import TaskPriority
        priority_map = {
            1: TaskPriority.LOW,
            2: TaskPriority.NORMAL,
            3: TaskPriority.HIGH,
            4: TaskPriority.URGENT
        }
        return priority_map.get(priority, TaskPriority.NORMAL)
