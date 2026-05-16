"""
Application Services - Task Scheduling Module
==========================================

Manages task lifecycle, scheduling, and execution.
Provides enterprise-grade task management with support for:
  - Task creation and persistence
  - Priority-based scheduling
  - Dependency management
  - Retry policies and timeouts
  - Dead letter queues

Components:
  - TaskDefinition: Task data model
  - TaskLifecycleState: Task state machine
  - TaskSchedulingPolicy: Scheduling strategies
  - TaskSchedulerService: Core scheduling engine
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid


class TaskLifecycleState(Enum):
    """
    Task lifecycle states for state machine transitions.
    Tasks move through these states during execution.
    """
    PENDING_CREATION = "pending_creation"
    CREATED = "created"
    QUEUED_FOR_SCHEDULING = "queued_for_scheduling"
    ASSIGNED_TO_AGENT = "assigned_to_agent"
    RUNNING_EXECUTION = "running_execution"
    COMPLETED_SUCCESS = "completed_success"
    COMPLETED_FAILURE = "completed_failure"
    CANCELLED_BY_USER = "cancelled_by_user"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    RETRY_SCHEDULED = "retry_scheduled"


class TaskPriorityLevel(Enum):
    """Task priority levels for scheduling decisions"""
    LOWEST = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    CRITICAL = 5
    URGENT = 6


@dataclass
class TaskDependency:
    """
    Represents a dependency relationship between tasks.
    A task can only start after all its dependencies are satisfied.
    """
    dependency_task_id: str
    dependency_type: str = "finish_to_start"
    satisfied: bool = False
    satisfied_at: Optional[datetime] = None
    
    def satisfy(self) -> None:
        """Mark dependency as satisfied"""
        self.satisfied = True
        self.satisfied_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'dependency_task_id': self.dependency_task_id,
            'dependency_type': self.dependency_type,
            'satisfied': self.satisfied,
            'satisfied_at': self.satisfied_at.isoformat() if self.satisfied_at else None
        }


@dataclass
class TaskRetryConfiguration:
    """
    Configuration for task retry behavior.
    Supports exponential backoff and custom retry policies.
    """
    max_retry_attempts: int = 3
    initial_retry_delay_seconds: int = 10
    max_retry_delay_seconds: int = 300
    backoff_multiplier: float = 2.0
    retry_on_timeout: bool = True
    retry_on_failure: bool = True
    exponential_backoff_enabled: bool = True
    
    def calculate_next_retry_delay(self, current_attempt: int) -> int:
        """Calculate delay for next retry attempt using exponential backoff"""
        if not self.exponential_backoff_enabled:
            return self.initial_retry_delay_seconds
        
        delay = int(self.initial_retry_delay_seconds * (self.backoff_multiplier ** (current_attempt - 1)))
        return min(delay, self.max_retry_delay_seconds)


@dataclass
class TaskDefinition:
    """
    Core task data model representing a unit of work to be executed by an agent.
    
    Key Attributes:
      - task_id: Unique identifier
      - task_name: Human-readable name
      - required_capabilities: Agent capabilities needed
      - priority: Scheduling priority
      - dependencies: Tasks that must complete first
      - retry_config: Retry behavior configuration
      - timeout: Maximum execution time
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    task_description: str = ""
    required_capabilities: List[str] = field(default_factory=list)
    priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL
    lifecycle_state: TaskLifecycleState = TaskLifecycleState.PENDING_CREATION
    assigned_agent_name: Optional[str] = None
    task_dependencies: List[TaskDependency] = field(default_factory=list)
    input_data: Any = None
    output_data: Any = None
    error_message: Optional[str] = None
    created_timestamp: datetime = field(default_factory=datetime.now)
    queued_timestamp: Optional[datetime] = None
    started_timestamp: Optional[datetime] = None
    completed_timestamp: Optional[datetime] = None
    task_metadata: Dict[str, Any] = field(default_factory=dict)
    retry_configuration: TaskRetryConfiguration = field(default_factory=TaskRetryConfiguration)
    current_retry_attempt: int = 0
    maximum_execution_timeout_seconds: int = 300
    tags: List[str] = field(default_factory=list)
    
    def get_duration_seconds(self) -> Optional[float]:
        """Calculate task execution duration in seconds"""
        if self.started_timestamp and self.completed_timestamp:
            return (self.completed_timestamp - self.started_timestamp).total_seconds()
        elif self.started_timestamp:
            return (datetime.now() - self.started_timestamp).total_seconds()
        return None
    
    def are_dependencies_satisfied(self) -> bool:
        """Check if all task dependencies are satisfied"""
        if not self.task_dependencies:
            return True
        return all(dep.satisfied for dep in self.task_dependencies)
    
    def has_unmet_dependencies(self) -> bool:
        """Check if task has any unmet dependencies"""
        return not self.are_dependencies_satisfied()
    
    def get_unmet_dependencies(self) -> List[TaskDependency]:
        """Get list of unsatisfied dependencies"""
        return [dep for dep in self.task_dependencies if not dep.satisfied]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dictionary"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'task_description': self.task_description,
            'required_capabilities': self.required_capabilities,
            'priority': self.priority.value,
            'lifecycle_state': self.lifecycle_state.value,
            'assigned_agent_name': self.assigned_agent_name,
            'dependencies': [dep.to_dict() for dep in self.task_dependencies],
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'created_timestamp': self.created_timestamp.isoformat(),
            'queued_timestamp': self.queued_timestamp.isoformat() if self.queued_timestamp else None,
            'started_timestamp': self.started_timestamp.isoformat() if self.started_timestamp else None,
            'completed_timestamp': self.completed_timestamp.isoformat() if self.completed_timestamp else None,
            'task_metadata': self.task_metadata,
            'retry_configuration': {
                'max_retry_attempts': self.retry_configuration.max_retry_attempts,
                'initial_retry_delay_seconds': self.retry_configuration.initial_retry_delay_seconds,
                'max_retry_delay_seconds': self.retry_configuration.max_retry_delay_seconds,
                'backoff_multiplier': self.retry_configuration.backoff_multiplier
            },
            'current_retry_attempt': self.current_retry_attempt,
            'maximum_execution_timeout_seconds': self.maximum_execution_timeout_seconds,
            'execution_duration_seconds': self.get_duration_seconds(),
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, task_dict: Dict[str, Any]) -> 'TaskDefinition':
        """Deserialize task from dictionary"""
        task_dict = task_dict.copy()
        task_dict['lifecycle_state'] = TaskLifecycleState(task_dict.get('lifecycle_state', 'pending_creation'))
        task_dict['priority'] = TaskPriorityLevel(task_dict.get('priority', 3))
        
        for ts_field in ['created_timestamp', 'queued_timestamp', 'started_timestamp', 'completed_timestamp']:
            if task_dict.get(ts_field) and isinstance(task_dict[ts_field], str):
                task_dict[ts_field] = datetime.fromisoformat(task_dict[ts_field])
        
        retry_config_dict = task_dict.get('retry_configuration', {})
        task_dict['retry_configuration'] = TaskRetryConfiguration(**retry_config_dict)
        
        dependencies = []
        for dep_dict in task_dict.get('dependencies', []):
            dep = TaskDependency(**dep_dict)
            if dep.satisfied_at and isinstance(dep.satisfied_at, str):
                dep.satisfied_at = datetime.fromisoformat(dep.satisfied_at)
            dependencies.append(dep)
        task_dict['task_dependencies'] = dependencies
        
        return cls(**{k: v for k, v in task_dict.items() if k in cls.__dataclass_fields__})


class TaskSchedulerService:
    """
    Core task scheduling engine that manages task lifecycle and scheduling.
    
    Features:
      - Priority-based task queue management
      - Dependency resolution and tracking
      - Agent capability matching
      - Retry and timeout handling
      - Dead letter queue for failed tasks
    
    Architecture:
      - Maintains task registry for all tasks
      - Separate queues for each priority level
      - Ready queue for tasks with satisfied dependencies
      - Dead letter queue for failed tasks
    """
    
    def __init__(self):
        self.task_registry: Dict[str, TaskDefinition] = {}
        self.task_queues_by_priority: Dict[TaskPriorityLevel, List[TaskDefinition]] = {
            priority: [] for priority in TaskPriorityLevel
        }
        self.dead_letter_queue: List[TaskDefinition] = []
        self.retry_pending_queue: List[TaskDefinition] = []
        self.state_change_callbacks: List[Callable[[TaskDefinition, TaskLifecycleState, TaskLifecycleState]]] = []
    
    def register_task_creation_callback(
        self,
        callback: Callable[[TaskDefinition, TaskLifecycleState, TaskLifecycleState]]
    ) -> None:
        """Register callback for task state changes"""
        self.state_change_callbacks.append(callback)
    
    def _notify_state_change(
        self,
        task: TaskDefinition,
        old_state: TaskLifecycleState,
        new_state: TaskLifecycleState
    ) -> None:
        """Notify all registered callbacks of state change"""
        for callback in self.state_change_callbacks:
            try:
                callback(task, old_state, new_state)
            except Exception:
                pass
    
    def create_new_task(
        self,
        task_name: str,
        required_capabilities: List[str],
        task_description: str = "",
        priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL,
        input_data: Any = None,
        dependency_task_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> TaskDefinition:
        """Create and register a new task"""
        task = TaskDefinition(
            task_name=task_name,
            task_description=task_description,
            required_capabilities=required_capabilities,
            priority=priority,
            input_data=input_data,
            tags=tags or []
        )
        
        if dependency_task_ids:
            for dep_id in dependency_task_ids:
                task.task_dependencies.append(
                    TaskDependency(dependency_task_id=dep_id)
                )
        
        self.task_registry[task.task_id] = task
        self._transition_task_state(task, TaskLifecycleState.CREATED)
        
        return task
    
    def enqueue_task_for_scheduling(self, task_id: str) -> bool:
        """Add task to appropriate priority queue"""
        task = self.task_registry.get(task_id)
        if not task:
            return False
        
        if task.lifecycle_state not in [TaskLifecycleState.CREATED, TaskLifecycleState.QUEUED_FOR_SCHEDULING]:
            return False
        
        self.task_queues_by_priority[task.priority].append(task)
        task.queued_timestamp = datetime.now()
        self._transition_task_state(task, TaskLifecycleState.QUEUED_FOR_SCHEDULING)
        
        return True
    
    def assign_task_to_agent(self, task_id: str, agent_name: str) -> bool:
        """Assign task to a specific agent"""
        task = self.task_registry.get(task_id)
        if not task:
            return False
        
        if task.has_unmet_dependencies():
            return False
        
        task.assigned_agent_name = agent_name
        self._transition_task_state(task, TaskLifecycleState.ASSIGNED_TO_AGENT)
        
        return True
    
    def start_task_execution(self, task_id: str) -> bool:
        """Mark task as running"""
        task = self.task_registry.get(task_id)
        if not task:
            return False
        
        if not task.assigned_agent_name:
            return False
        
        task.started_timestamp = datetime.now()
        self._transition_task_state(task, TaskLifecycleState.RUNNING_EXECUTION)
        
        return True
    
    def complete_task_successfully(self, task_id: str, output_data: Any = None) -> bool:
        """Mark task as successfully completed"""
        task = self.task_registry.get(task_id)
        if not task:
            return False
        
        task.output_data = output_data
        task.completed_timestamp = datetime.now()
        
        self._satisfy_all_dependent_tasks(task_id)
        self._transition_task_state(task, TaskLifecycleState.COMPLETED_SUCCESS)
        
        return True
    
    def fail_task_execution(self, task_id: str, error_message: str) -> bool:
        """Mark task as failed and handle retry logic"""
        task = self.task_registry.get(task_id)
        if not task:
            return False
        
        task.error_message = error_message
        task.completed_timestamp = datetime.now()
        
        if task.current_retry_attempt < task.retry_configuration.max_retry_attempts:
            task.current_retry_attempt += 1
            retry_delay = task.retry_configuration.calculate_next_retry_delay(task.current_retry_attempt)
            
            self._transition_task_state(task, TaskLifecycleState.RETRY_SCHEDULED)
            self.retry_pending_queue.append((task, retry_delay))
            
            return True
        
        self._transition_task_state(task, TaskLifecycleState.COMPLETED_FAILURE)
        self.dead_letter_queue.append(task)
        
        return False
    
    def cancel_task_execution(self, task_id: str) -> bool:
        """Cancel a task"""
        task = self.task_registry.get(task_id)
        if not task:
            return False
        
        if task.lifecycle_state in [TaskLifecycleState.COMPLETED_SUCCESS, TaskLifecycleState.COMPLETED_FAILURE]:
            return False
        
        task.completed_timestamp = datetime.now()
        self._transition_task_state(task, TaskLifecycleState.CANCELLED_BY_USER)
        
        return True
    
    def _transition_task_state(
        self,
        task: TaskDefinition,
        new_state: TaskLifecycleState
    ) -> None:
        """Transition task to new state and notify callbacks"""
        old_state = task.lifecycle_state
        task.lifecycle_state = new_state
        self._notify_state_change(task, old_state, new_state)
    
    def _satisfy_all_dependent_tasks(self, completed_task_id: str) -> None:
        """Satisfy dependencies for tasks waiting on completed task"""
        for task in self.task_registry.values():
            for dependency in task.task_dependencies:
                if dependency.dependency_task_id == completed_task_id:
                    dependency.satisfy()
    
    def get_ready_tasks_for_scheduling(self) -> List[TaskDefinition]:
        """Get tasks with satisfied dependencies ready for agent assignment"""
        ready_tasks = []
        
        for priority_level in TaskPriorityLevel:
            queue = self.task_queues_by_priority[priority_level]
            for task in queue[:]:
                if task.lifecycle_state == TaskLifecycleState.QUEUED_FOR_SCHEDULING:
                    if task.are_dependencies_satisfied():
                        ready_tasks.append(task)
        
        ready_tasks.sort(key=lambda t: (-t.priority.value, t.created_timestamp))
        return ready_tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[TaskDefinition]:
        """Retrieve task by ID"""
        return self.task_registry.get(task_id)
    
    def get_tasks_by_state(self, state: TaskLifecycleState) -> List[TaskDefinition]:
        """Get all tasks in a specific state"""
        return [t for t in self.task_registry.values() if t.lifecycle_state == state]
    
    def get_tasks_by_agent(self, agent_name: str) -> List[TaskDefinition]:
        """Get all tasks assigned to a specific agent"""
        return [
            t for t in self.task_registry.values()
            if t.assigned_agent_name == agent_name
        ]
    
    def get_dead_letter_tasks(self) -> List[TaskDefinition]:
        """Get tasks that have permanently failed"""
        return self.dead_letter_queue.copy()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive scheduling statistics"""
        stats = {
            'total_tasks': len(self.task_registry),
            'tasks_by_state': {},
            'tasks_by_priority': {},
            'dead_letter_queue_size': len(self.dead_letter_queue),
            'retry_pending_count': len(self.retry_pending_queue)
        }
        
        for state in TaskLifecycleState:
            stats['tasks_by_state'][state.value] = len(self.get_tasks_by_state(state))
        
        for priority in TaskPriorityLevel:
            stats['tasks_by_priority'][priority.name] = len(
                self.task_queues_by_priority[priority]
            )
        
        return stats
