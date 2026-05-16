"""
Orchestrator - The Core of Multi-Agent System
编排器 - 多Agent系统的核心，负责协调、调度和任务分配
"""

from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import asyncio
from datetime import datetime

from agent import Agent, AgentMessage, AgentStatus, MessageType
from registry import AgentRegistry
from task_manager import Task, TaskStatus, TaskPriority, TaskManager


class ExecutionStrategy(Enum):
    """执行策略"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


class Orchestrator:
    """多Agent编排器"""

    def __init__(self, name: str = "main_orchestrator"):
        self.name = name
        self.registry = AgentRegistry()
        self.task_manager = TaskManager()
        self.execution_strategy = ExecutionStrategy.HYBRID
        self.message_history: List[AgentMessage] = []
        self.event_handlers: Dict[str, List[Callable]] = {
            'task_created': [],
            'task_assigned': [],
            'task_completed': [],
            'task_failed': [],
            'agent_registered': [],
            'message_sent': []
        }
        self.max_concurrent_tasks = 5
        self.running = False

    def register_agent(self, agent: Agent) -> bool:
        """注册Agent"""
        success = self.registry.register(agent)
        if success:
            self._emit_event('agent_registered', {'agent': agent})
        return success

    def register_agents(self, agents: List[Agent]) -> Dict[str, bool]:
        """批量注册Agent"""
        results = {}
        for agent in agents:
            results[agent.name] = self.register_agent(agent)
        return results

    def create_task(
        self,
        name: str,
        requirements: List[str],
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        input_data: Any = None,
        dependencies: List[str] = None
    ) -> Task:
        """创建任务"""
        task = self.task_manager.create_task(
            name=name,
            requirements=requirements,
            description=description,
            priority=priority,
            input_data=input_data,
            dependencies=dependencies
        )
        self._emit_event('task_created', {'task': task})
        return task

    def schedule_task(self, task_id: str) -> bool:
        """调度任务 - 分配给合适的Agent"""
        task = self.task_manager.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False

        agent = self.registry.select_best_agent(task.requirements)
        if not agent:
            agent = self.registry.get_available_agents()[0] if self.registry.get_available_agents() else None

        if not agent:
            return False

        task.assigned_agent = agent.name
        agent.update_status(AgentStatus.BUSY)
        self._emit_event('task_assigned', {'task': task, 'agent': agent})
        return True

    def execute_task(self, task: Task) -> Any:
        """执行任务"""
        if not task.assigned_agent:
            if not self.schedule_task(task.id):
                task.mark_failed("No available agent")
                self._emit_event('task_failed', {'task': task, 'error': 'No available agent'})
                return None

        agent = self.registry.get_agent(task.assigned_agent)
        if not agent:
            task.mark_failed("Agent not found")
            self._emit_event('task_failed', {'task': task, 'error': 'Agent not found'})
            return None

        task.mark_running()
        try:
            message = AgentMessage(
                sender=self.name,
                receivers=[agent.name],
                msg_type=MessageType.REQUEST,
                content={'task': task.to_dict(), 'input': task.input_data},
                metadata={'task_id': task.id}
            )

            self._deliver_message(message)
            response = agent.process_message(message)

            result = response.content
            task.mark_completed(result)
            self.task_manager.update_task_status(task.id, TaskStatus.COMPLETED)
            agent.update_status(AgentStatus.IDLE)
            self._emit_event('task_completed', {'task': task, 'result': result})
            return result

        except Exception as e:
            task.mark_failed(str(e))
            self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
            agent.update_status(AgentStatus.ERROR)
            self._emit_event('task_failed', {'task': task, 'error': str(e)})
            return None

    def execute_workflow(self, workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行工作流"""
        results = {}
        task_ids = []

        for step in workflow:
            task = self.create_task(
                name=step.get('name', 'unnamed_step'),
                requirements=step.get('requirements', []),
                description=step.get('description', ''),
                priority=TaskPriority[step.get('priority', 'NORMAL')],
                input_data=step.get('input_data'),
                dependencies=step.get('dependencies', [])
            )
            task_ids.append(task.id)

        if self.execution_strategy == ExecutionStrategy.SEQUENTIAL:
            for task_id in task_ids:
                task = self.task_manager.get_task(task_id)
                result = self.execute_task(task)
                results[task_id] = result

        elif self.execution_strategy == ExecutionStrategy.PARALLEL:
            tasks = [self.task_manager.get_task(tid) for tid in task_ids]
            parallel_results = self._execute_parallel(tasks)
            results = parallel_results

        elif self.execution_strategy == ExecutionStrategy.HYBRID:
            dependency_tasks = {}
            independent_tasks = []

            for task_id in task_ids:
                task = self.task_manager.get_task(task_id)
                if task.dependencies:
                    dependency_tasks[task_id] = task
                else:
                    independent_tasks.append(task)

            for task in independent_tasks:
                result = self.execute_task(task)
                results[task.id] = result

            for task_id, task in dependency_tasks.items():
                result = self.execute_task(task)
                results[task_id] = result

        return results

    def _execute_parallel(self, tasks: List[Task]) -> Dict[str, Any]:
        """并行执行任务"""
        results = {}
        import concurrent.futures

        def execute_wrapper(task):
            return task.id, self.execute_task(task)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as executor:
            futures = {executor.submit(execute_wrapper, task): task for task in tasks}
            for future in concurrent.futures.as_completed(futures):
                task_id, result = future.result()
                results[task_id] = result

        return results

    def send_message(self, message: AgentMessage) -> None:
        """发送消息"""
        self._deliver_message(message)
        self.message_history.append(message)
        self._emit_event('message_sent', {'message': message})

    def broadcast_message(self, content: Any, sender: str = None) -> None:
        """广播消息"""
        message = AgentMessage(
            sender=sender or self.name,
            receivers=[agent.name for agent in self.registry.get_all_agents()],
            msg_type=MessageType.BROADCAST,
            content=content
        )
        self.send_message(message)

    def _deliver_message(self, message: AgentMessage) -> None:
        """投递消息到目标Agent"""
        if message.msg_type == MessageType.BROADCAST:
            for agent in self.registry.get_all_agents():
                agent.receive_message(message)
        else:
            for receiver in message.receivers:
                agent = self.registry.get_agent(receiver)
                if agent:
                    agent.receive_message(message)

    def request_agent_coordination(
        self,
        source_agent: str,
        target_agents: List[str],
        request_content: Any
    ) -> List[AgentMessage]:
        """请求Agent间协调"""
        responses = []
        message = AgentMessage(
            sender=source_agent,
            receivers=target_agents,
            msg_type=MessageType.REQUEST,
            content=request_content
        )

        self._deliver_message(message)

        for agent_name in target_agents:
            agent = self.registry.get_agent(agent_name)
            if agent:
                response = agent.process_message(message)
                responses.append(response)

        return responses

    def on_event(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"Error in event handler: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'orchestrator': self.name,
            'running': self.running,
            'agents': self.registry.get_statistics(),
            'tasks': self.task_manager.get_statistics(),
            'messages_sent': len(self.message_history),
            'execution_strategy': self.execution_strategy.value,
            'max_concurrent_tasks': self.max_concurrent_tasks
        }

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取Agent详细信息"""
        agent = self.registry.get_agent(agent_name)
        if not agent:
            return None

        info = agent.get_info()
        info['tasks'] = [
            task.to_dict() for task in
            self.task_manager.get_tasks_by_agent(agent_name)
        ]
        return info

    def shutdown(self) -> None:
        """关闭编排器"""
        self.running = False
        for agent in self.registry.get_all_agents():
            agent.update_status(AgentStatus.TERMINATED)
