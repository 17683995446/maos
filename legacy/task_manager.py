"""
Task Management Module
任务管理模块 - 负责任务的创建、调度、状态追踪
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


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
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典反序列化"""
        data = data.copy()
        data['priority'] = TaskPriority(data.get('priority', 2))
        data['status'] = TaskStatus(data.get('status', 'pending'))
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'started_at' in data and isinstance(data.get('started_at'), str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if 'completed_at' in data and isinstance(data.get('completed_at'), str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)

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

    def get_duration(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []

    def create_task(
        self,
        name: str,
        requirements: List[str],
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        input_data: Any = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """创建新任务"""
        task = Task(
            name=name,
            description=description,
            requirements=requirements,
            priority=priority,
            input_data=input_data,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        self.tasks[task.id] = task
        self.task_queue.append(task)
        self._sort_queue()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> List[Task]:
        """获取待处理任务"""
        return [t for t in self.task_queue if t.status == TaskStatus.PENDING and t.id in self.tasks]

    def get_all_queue_tasks(self) -> List[Task]:
        """获取所有队列中的任务（包括已完成的）"""
        return self.task_queue

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务"""
        return [t for t in self.tasks.values() if t.status == status]

    def get_tasks_by_agent(self, agent_name: str) -> List[Task]:
        """获取分配给某Agent的任务"""
        return [t for t in self.tasks.values() if t.assigned_agent == agent_name]

    def assign_task(self, task_id: str, agent_name: str) -> bool:
        """分配任务给Agent"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.assigned_agent = agent_name
            return True
        return False

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = status
        if status == TaskStatus.COMPLETED:
            self.completed_tasks.append(task)
        elif status == TaskStatus.FAILED:
            self.failed_tasks.append(task)
        elif status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            self.task_queue = [t for t in self.task_queue if t.id != task_id]

        return True

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.mark_cancelled()
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total': len(self.tasks),
            'pending': len(self.get_pending_tasks()),
            'running': len(self.get_tasks_by_status(TaskStatus.RUNNING)),
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks),
            'cancelled': len(self.get_tasks_by_status(TaskStatus.CANCELLED))
        }

    def clear_completed(self) -> None:
        """清除已完成任务"""
        self.completed_tasks.clear()
        self.failed_tasks.clear()

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
