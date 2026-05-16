"""
Task Manager Module for MAOS
任务管理器 - 负责任务创建、调度、状态追踪和生命周期管理
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio
from collections import defaultdict


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    input_data: Any = None
    output_data: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    result_handler: Optional[Callable] = field(default=None, repr=False)
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'requirements': self.requirements,
            'priority': self.priority.value,
            'status': self.status.value,
            'assigned_agent': self.assigned_agent,
            'dependencies': self.dependencies,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典反序列化"""
        data = data.copy()
        priority_val = data.get('priority')
        if isinstance(priority_val, int):
            data['priority'] = TaskPriority(priority_val)
        elif isinstance(priority_val, str):
            data['priority'] = TaskPriority[priority_val.upper()]
        
        status_val = data.get('status')
        if isinstance(status_val, str):
            data['status'] = TaskStatus(status_val)
        
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'started_at' in data and isinstance(data.get('started_at'), str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if 'completed_at' in data and isinstance(data.get('completed_at'), str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        return cls(**{k: v for k, v in data.items() if k in [f.name for f in cls.__dataclass_fields__.values()]})

    def mark_running(self) -> None:
        """标记为运行中"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, output_data: Any = None) -> None:
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if output_data is not None:
            self.output_data = output_data

    def mark_failed(self, error: str) -> None:
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def mark_cancelled(self) -> None:
        """标记为取消"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED

    def increment_retry(self) -> None:
        """增加重试次数"""
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.error = None

    def get_duration(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def is_terminal(self) -> bool:
        """检查是否为终态"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


class TaskEventHandler:
    """任务事件处理器"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def on(self, event: str, handler: Callable) -> None:
        """注册事件处理器"""
        self._handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """注销事件处理器"""
        if event in self._handlers:
            self._handlers[event].remove(handler)
    
    async def emit_async(self, event: str, data: Dict[str, Any]) -> None:
        """异步触发事件"""
        for handler in self._handlers.get(event, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                print(f"Error in event handler for {event}: {e}")
    
    def emit(self, event: str, data: Dict[str, Any]) -> None:
        """同步触发事件"""
        for handler in self._handlers.get(event, []):
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler for {event}: {e}")


class TaskManager:
    """任务管理器 - 负责任务的创建、调度、追踪和管理"""
    
    def __init__(self, max_concurrent: int = 10):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self.event_handler = TaskEventHandler()
        self.max_concurrent = max_concurrent
        try:
            self._lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None
        except RuntimeError:
            self._lock = None
    
    def create_task(
        self,
        name: str,
        requirements: List[str],
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        input_data: Any = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None,
        max_retries: int = 3
    ) -> Task:
        """创建新任务"""
        task = Task(
            name=name,
            description=description,
            requirements=requirements,
            priority=priority,
            input_data=input_data,
            dependencies=dependencies or [],
            metadata=metadata or {},
            max_retries=max_retries
        )
        self.tasks[task.id] = task
        self.task_queue.append(task)
        self._sort_queue()
        self.event_handler.emit('task_created', {'task': task})
        return task
    
    async def create_task_async(
        self,
        name: str,
        requirements: List[str],
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        input_data: Any = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None,
        max_retries: int = 3
    ) -> Task:
        """异步创建新任务"""
        if self._lock:
            async with self._lock:
                return self.create_task(
                    name=name,
                    requirements=requirements,
                    description=description,
                    priority=priority,
                    input_data=input_data,
                    dependencies=dependencies,
                    metadata=metadata,
                    max_retries=max_retries
                )
        return self.create_task(
            name=name,
            requirements=requirements,
            description=description,
            priority=priority,
            input_data=input_data,
            dependencies=dependencies,
            metadata=metadata,
            max_retries=max_retries
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> List[Task]:
        """获取待处理任务"""
        return [t for t in self.task_queue if t.status == TaskStatus.PENDING and t.id in self.tasks]

    def get_running_tasks(self) -> List[Task]:
        """获取运行中任务"""
        return list(self.running_tasks.values())

    def get_all_queue_tasks(self) -> List[Task]:
        """获取所有队列中的任务"""
        return self.task_queue

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务"""
        return [t for t in self.tasks.values() if t.status == status]

    def get_tasks_by_agent(self, agent_name: str) -> List[Task]:
        """获取分配给某Agent的任务"""
        return [t for t in self.tasks.values() if t.assigned_agent == agent_name]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """根据优先级获取任务"""
        return [t for t in self.tasks.values() if t.priority == priority]

    def assign_task(self, task_id: str, agent_name: str) -> bool:
        """分配任务给Agent"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.assigned_agent = agent_name
            self.event_handler.emit('task_assigned', {'task': task, 'agent': agent_name})
            return True
        return False

    async def assign_task_async(self, task_id: str, agent_name: str) -> bool:
        """异步分配任务给Agent"""
        if self._lock:
            async with self._lock:
                return self.assign_task(task_id, agent_name)
        return self.assign_task(task_id, agent_name)

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        old_status = task.status
        task.status = status
        
        if status == TaskStatus.RUNNING:
            self.running_tasks[task_id] = task
            self.event_handler.emit('task_started', {'task': task})
        elif old_status == TaskStatus.RUNNING and task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        if status == TaskStatus.COMPLETED:
            if task not in self.completed_tasks:
                self.completed_tasks.append(task)
            self.event_handler.emit('task_completed', {'task': task})
        elif status == TaskStatus.FAILED:
            if task not in self.failed_tasks:
                self.failed_tasks.append(task)
            self.event_handler.emit('task_failed', {'task': task})
        
        if status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]:
            self.task_queue = [t for t in self.task_queue if t.id != task_id]

        return True

    async def update_task_status_async(self, task_id: str, status: TaskStatus) -> bool:
        """异步更新任务状态"""
        if self._lock:
            async with self._lock:
                return self.update_task_status(task_id, status)
        return self.update_task_status(task_id, status)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.mark_cancelled()
            self.event_handler.emit('task_cancelled', {'task': task})
            return True
        return False

    async def cancel_task_async(self, task_id: str) -> bool:
        """异步取消任务"""
        if self._lock:
            async with self._lock:
                return self.cancel_task(task_id)
        return self.cancel_task(task_id)

    def retry_task(self, task_id: str) -> bool:
        """重试失败的任务"""
        task = self.tasks.get(task_id)
        if task and task.can_retry():
            task.increment_retry()
            self.event_handler.emit('task_retried', {'task': task})
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total': len(self.tasks),
            'pending': len(self.get_pending_tasks()),
            'running': len(self.running_tasks),
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks),
            'cancelled': len(self.get_tasks_by_status(TaskStatus.CANCELLED)),
            'max_concurrent': self.max_concurrent,
            'by_priority': {
                priority.name: len(self.get_tasks_by_priority(priority))
                for priority in TaskPriority
            }
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        completed_with_duration = [
            t.get_duration() for t in self.completed_tasks 
            if t.get_duration() is not None
        ]
        
        failed_with_duration = [
            t.get_duration() for t in self.failed_tasks 
            if t.get_duration() is not None
        ]
        
        avg_duration = sum(completed_with_duration) / len(completed_with_duration) if completed_with_duration else 0
        avg_failed_duration = sum(failed_with_duration) / len(failed_with_duration) if failed_with_duration else 0
        
        return {
            'total_completed': len(self.completed_tasks),
            'total_failed': len(self.failed_tasks),
            'avg_completion_time': avg_duration,
            'avg_failure_time': avg_failed_duration,
            'success_rate': len(self.completed_tasks) / len(self.tasks) if self.tasks else 0,
            'total_retries': sum(t.retry_count for t in self.tasks.values())
        }

    def clear_completed(self) -> None:
        """清除已完成任务记录"""
        self.completed_tasks.clear()
        self.failed_tasks.clear()

    def clear_all_tasks(self) -> None:
        """清除所有任务"""
        self.tasks.clear()
        self.task_queue.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.running_tasks.clear()

    def _sort_queue(self) -> None:
        """按优先级排序任务队列"""
        self.task_queue.sort(key=lambda t: (-t.priority.value, t.created_at))

    def get_ready_tasks(self) -> List[Task]:
        """获取可执行的任务（依赖已满足）"""
        ready = []
        for task in self.get_pending_tasks():
            if not task.dependencies:
                ready.append(task)
            else:
                deps_completed = all(
                    self.tasks.get(dep_id) and 
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if deps_completed:
                    ready.append(task)
        return ready

    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """获取依赖指定任务的所有任务"""
        return [
            task for task in self.tasks.values()
            if task_id in task.dependencies
        ]

    def can_execute_task(self, task: Task) -> bool:
        """检查任务是否可以执行"""
        if task.status != TaskStatus.PENDING:
            return False
        
        if len(self.running_tasks) >= self.max_concurrent:
            return False
        
        if not task.dependencies:
            return True
        
        return all(
            self.tasks.get(dep_id) and 
            self.tasks[dep_id].status == TaskStatus.COMPLETED
            for dep_id in task.dependencies
        )

    def get_execution_order(self) -> List[str]:
        """获取任务的拓扑排序执行顺序"""
        visited = set()
        order = []
        
        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    visit(dep_id)
                order.append(task_id)
        
        for task_id in self.tasks:
            visit(task_id)
        
        return order
