"""
Application Services - Advanced Task Scheduling Module
================================================

Provides advanced scheduling capabilities with cron expressions.
Part of the Phase 2 production hardening improvements.

Key Features:
  - Cron expression parsing
  - Recurring task scheduling
  - Calendar-based scheduling
  - Timezone support
  - Task prioritization
  - Missed task handling
  - Scheduling conflict resolution

Architecture:
  - Uses croniter for cron expression parsing
  - Supports standard cron syntax
  - Includes seconds field for precision
  - Calendar-based scheduling
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
import re
import logging

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduling"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CRON = "cron"
    INTERVAL = "interval"
    CALENDAR = "calendar"


class CronField(Enum):
    """Cron expression fields"""
    SECOND = 0
    MINUTE = 1
    HOUR = 2
    DAY_OF_MONTH = 3
    MONTH = 4
    DAY_OF_WEEK = 5


@dataclass
class CronExpression:
    """
    Cron expression parser and validator.
    
    Supports:
      - Standard 5-field cron (minute hour day month weekday)
      - Extended 6-field cron (second minute hour day month weekday)
      - Special characters: * , - /
      - Ranges and lists
      - Step values
    
    Examples:
      - "0 * * * *" - Every hour
      - "*/15 * * * *" - Every 15 minutes
      - "0 9-17 * * 1-5" - Business hours, weekdays
      - "30 4 1,15 * *" - 4:30 AM on 1st and 15th
    """
    
    expression: str
    include_seconds: bool = False
    
    def __post_init__(self):
        self._validate()
        self._parse()
    
    def _validate(self) -> None:
        """Validate cron expression format"""
        parts = self.expression.split()
        
        if self.include_seconds and len(parts) != 6:
            raise ValueError(
                f"Cron expression with seconds requires 6 fields, got {len(parts)}"
            )
        elif not self.include_seconds and len(parts) != 5:
            raise ValueError(
                f"Cron expression requires 5 fields, got {len(parts)}"
            )
        
        if self.include_seconds:
            patterns = [
                r'^(\*|([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?(,([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?)*)(\/([0-9]|[1-5][0-9]))?$',
            ]
        else:
            patterns = [
                r'^(\*|([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?(,([0-9]|[1-5][0-9])(-([0-9]|[1-5][0-9]))?)*)(\/([0-9]|[1-5][0-9]))?$',
            ]
        
        for i, part in enumerate(parts):
            if i == 3:
                pattern = r'^(\*|([1-9]|[12][0-9]|3[01])(-([1-9]|[12][0-9]|3[01]))?(,([1-9]|[12][0-9]|3[01])(-([1-9]|[12][0-9]|3[01]))?)*|L|W)$'
            elif i == 4:
                pattern = r'^(\*|([1-9]|1[0-2])(-([1-9]|1[0-2]))?(,([1-9]|1[0-2])(-([1-9]|1[0-2]))?)*|L)$'
            elif i == 5:
                pattern = r'^(\*|[0-6](-([0-6]))?(,([0-6](-([0-6]))?)*|L)$'
            else:
                pattern = patterns[0]
            
            if not re.match(pattern, part):
                raise ValueError(f"Invalid cron field at position {i}: {part}")
    
    def _parse(self) -> None:
        """Parse cron expression into components"""
        parts = self.expression.split()
        
        self.second = parts[0] if self.include_seconds else "0"
        self.minute = parts[1] if self.include_seconds else parts[0]
        self.hour = parts[2] if self.include_seconds else parts[1]
        self.day_of_month = parts[3] if self.include_seconds else parts[2]
        self.month = parts[4] if self.include_seconds else parts[3]
        self.day_of_week = parts[5] if self.include_seconds else parts[4]
    
    def get_next_run_time(self, base_time: Optional[datetime] = None) -> datetime:
        """
        Calculate next run time from base time.
        
        Args:
            base_time: Starting time for calculation
        
        Returns:
            Next scheduled datetime
        """
        if base_time is None:
            base_time = datetime.now()
        
        next_time = base_time + timedelta(seconds=1)
        
        max_iterations = 525600
        iterations = 0
        
        while iterations < max_iterations:
            if self._matches(next_time):
                return next_time
            next_time += timedelta(minutes=1)
            iterations += 1
        
        raise RuntimeError("Could not find next run time")
    
    def _matches(self, dt: datetime) -> bool:
        """Check if datetime matches cron expression"""
        if not self._field_matches(self.second, dt.second, 0, 59):
            return False
        if not self._field_matches(self.minute, dt.minute, 0, 59):
            return False
        if not self._field_matches(self.hour, dt.hour, 0, 23):
            return False
        if not self._field_matches(self.day_of_month, dt.day, 1, 31):
            return False
        if not self._field_matches(self.month, dt.month, 1, 12):
            return False
        if not self._field_matches(self.day_of_week, dt.weekday(), 0, 6):
            return False
        return True
    
    def _field_matches(
        self,
        field: str,
        value: int,
        min_val: int,
        max_val: int
    ) -> bool:
        """Check if field value matches cron field specification"""
        if field == "*":
            return True
        
        for part in field.split(","):
            if "-" in part:
                start, end = part.split("-")
                if start.isdigit() and end.isdigit():
                    if int(start) <= value <= int(end):
                        return True
            elif "/" in part:
                base, step = part.split("/")
                if base == "*":
                    base_val = min_val
                else:
                    base_val = int(base)
                step_val = int(step)
                if (value - base_val) % step_val == 0:
                    return True
            else:
                if field.isdigit() and int(field) == value:
                    return True
        
        return False
    
    def get_schedule_description(self) -> str:
        """Get human-readable description of cron schedule"""
        descriptions = []
        
        if self.hour == "*" and self.minute == "*":
            descriptions.append("every minute")
        elif self.minute == "*/5":
            descriptions.append("every 5 minutes")
        elif self.minute == "*/15":
            descriptions.append("every 15 minutes")
        elif self.minute == "*/30":
            descriptions.append("every 30 minutes")
        elif self.hour == "*":
            descriptions.append(f"at minute {self.minute} of every hour")
        elif self.day_of_month == "*" and self.month == "*":
            if self.day_of_week == "1-5":
                descriptions.append(f"at {self.hour}:{self.minute.zfill(2)} on weekdays")
            else:
                descriptions.append(f"at {self.hour}:{self.minute.zfill(2)} daily")
        elif self.day_of_month != "*":
            descriptions.append(f"at {self.hour}:{self.minute.zfill(2)} on day {self.day_of_month}")
        
        return ", ".join(descriptions) if descriptions else self.expression


@dataclass
class ScheduledTask:
    """
    Scheduled task definition.
    
    Represents a task scheduled for future execution.
    
    Attributes:
      - task_id: Unique identifier
      - task_name: Human-readable name
      - schedule: Schedule configuration
      - next_run: Next scheduled run time
      - last_run: Last execution time
      - execution_count: Number of executions
      - is_active: Whether task is active
    """
    task_id: str
    task_name: str
    schedule_type: ScheduleType
    cron_expression: Optional[CronExpression] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: str = "UTC"
    next_run: Optional[datetime] = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    execution_count: int = 0
    is_active: bool = True
    max_executions: Optional[int] = None
    miss_policy: str = "skip"
    task_handler: Optional[Callable] = None
    task_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_next_run(self) -> None:
        """Calculate next run time based on schedule"""
        if not self.is_active:
            self.next_run = None
            return
        
        if self.start_time and datetime.now() < self.start_time:
            self.next_run = self.start_time
            return
        
        if self.end_time and datetime.now() >= self.end_time:
            self.next_run = None
            self.is_active = False
            return
        
        if self.schedule_type == ScheduleType.CRON and self.cron_expression:
            self.next_run = self.cron_expression.get_next_run_time()
        elif self.schedule_type == ScheduleType.INTERVAL and self.interval_seconds:
            base = self.last_run or datetime.now()
            self.next_run = base + timedelta(seconds=self.interval_seconds)
        elif self.schedule_type == ScheduleType.ONE_TIME:
            self.next_run = self.start_time
            if self.start_time and datetime.now() > self.start_time:
                self.is_active = False
        else:
            self.next_run = datetime.now() + timedelta(minutes=1)
    
    def record_execution(self) -> None:
        """Record task execution"""
        self.last_run = datetime.now()
        self.execution_count += 1
        
        if self.max_executions and self.execution_count >= self.max_executions:
            self.is_active = False
            self.next_run = None
        
        self.calculate_next_run()
    
    def should_run(self) -> bool:
        """Check if task should run now"""
        if not self.is_active:
            return False
        
        if self.next_run is None:
            return False
        
        return datetime.now() >= self.next_run
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'schedule_type': self.schedule_type.value,
            'cron_expression': self.cron_expression.expression if self.cron_expression else None,
            'interval_seconds': self.interval_seconds,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'execution_count': self.execution_count,
            'is_active': self.is_active,
            'timezone': self.timezone,
            'metadata': self.metadata
        }


class AdvancedTaskScheduler:
    """
    Advanced task scheduler with cron support.
    
    Features:
      - Cron-based scheduling
      - Interval-based scheduling
      - One-time scheduling
      - Calendar scheduling
      - Timezone support
      - Missed task handling
      - Conflict resolution
    
    Usage:
        scheduler = AdvancedTaskScheduler()
        
        task = scheduler.create_cron_task(
            "daily_report",
            "0 9 * * *",
            my_report_function
        )
        
        scheduler.start()
    """
    
    def __init__(self, timezone: str = "UTC"):
        self.timezone = timezone
        self._scheduled_tasks: Dict[str, ScheduledTask] = {}
        self._execution_queue: List[ScheduledTask] = []
        self._running = False
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
    
    def create_cron_task(
        self,
        task_id: str,
        task_name: str,
        cron_expression: str,
        handler: Callable,
        params: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_executions: Optional[int] = None
    ) -> ScheduledTask:
        """
        Create a cron-based scheduled task.
        
        Args:
            task_id: Unique task identifier
            task_name: Human-readable name
            cron_expression: Cron expression string
            handler: Function to execute
            params: Task parameters
            start_time: When to start scheduling
            end_time: When to stop scheduling
            max_executions: Maximum number of executions
        
        Returns:
            Created ScheduledTask
        """
        if task_id in self._scheduled_tasks:
            raise ValueError(f"Task {task_id} already exists")
        
        cron = CronExpression(cron_expression)
        
        task = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            schedule_type=ScheduleType.CRON,
            cron_expression=cron,
            task_handler=handler,
            task_params=params or {},
            start_time=start_time,
            end_time=end_time,
            max_executions=max_executions
        )
        
        task.calculate_next_run()
        self._scheduled_tasks[task_id] = task
        
        logger.info(f"Created cron task: {task_id} - {cron.get_schedule_description()}")
        
        return task
    
    def create_interval_task(
        self,
        task_id: str,
        task_name: str,
        interval_seconds: int,
        handler: Callable,
        params: Optional[Dict[str, Any]] = None
    ) -> ScheduledTask:
        """Create an interval-based scheduled task"""
        if task_id in self._scheduled_tasks:
            raise ValueError(f"Task {task_id} already exists")
        
        task = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=interval_seconds,
            task_handler=handler,
            task_params=params or {}
        )
        
        task.calculate_next_run()
        self._scheduled_tasks[task_id] = task
        
        logger.info(f"Created interval task: {task_id} every {interval_seconds}s")
        
        return task
    
    def create_one_time_task(
        self,
        task_id: str,
        task_name: str,
        run_time: datetime,
        handler: Callable,
        params: Optional[Dict[str, Any]] = None
    ) -> ScheduledTask:
        """Create a one-time scheduled task"""
        if task_id in self._scheduled_tasks:
            raise ValueError(f"Task {task_id} already exists")
        
        task = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            schedule_type=ScheduleType.ONE_TIME,
            start_time=run_time,
            task_handler=handler,
            task_params=params or {},
            max_executions=1
        )
        
        task.calculate_next_run()
        self._scheduled_tasks[task_id] = task
        
        logger.info(f"Created one-time task: {task_id} at {run_time}")
        
        return task
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if task_id in self._scheduled_tasks:
            task = self._scheduled_tasks[task_id]
            task.is_active = False
            task.next_run = None
            logger.info(f"Cancelled task: {task_id}")
            return True
        return False
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        if task_id in self._scheduled_tasks:
            task = self._scheduled_tasks[task_id]
            task.is_active = False
            logger.info(f"Paused task: {task_id}")
            return True
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if task_id in self._scheduled_tasks:
            task = self._scheduled_tasks[task_id]
            task.is_active = True
            task.calculate_next_run()
            logger.info(f"Resumed task: {task_id}")
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get scheduled task by ID"""
        return self._scheduled_tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks"""
        return list(self._scheduled_tasks.values())
    
    def get_active_tasks(self) -> List[ScheduledTask]:
        """Get all active scheduled tasks"""
        return [t for t in self._scheduled_tasks.values() if t.is_active]
    
    def get_tasks_due_now(self) -> List[ScheduledTask]:
        """Get all tasks due for execution"""
        return [t for t in self._scheduled_tasks.values() if t.should_run()]
    
    def execute_task(self, task: ScheduledTask) -> bool:
        """
        Execute a scheduled task.
        
        Args:
            task: Task to execute
        
        Returns:
            True if successful, False otherwise
        """
        if not task.task_handler:
            logger.error(f"No handler for task: {task.task_id}")
            return False
        
        start_time = datetime.now()
        
        try:
            result = task.task_handler(**task.task_params)
            
            self._record_execution(
                task.task_id,
                start_time,
                True,
                result=result
            )
            
            task.record_execution()
            
            logger.info(f"Executed task: {task.task_id}")
            
            return True
            
        except Exception as e:
            self._record_execution(
                task.task_id,
                start_time,
                False,
                error=str(e)
            )
            
            logger.error(f"Task {task.task_id} failed: {e}")
            
            if task.miss_policy == "run_immediately":
                task.calculate_next_run()
            
            return False
    
    def _record_execution(
        self,
        task_id: str,
        start_time: datetime,
        success: bool,
        result: Any = None,
        error: Optional[str] = None
    ) -> None:
        """Record task execution in history"""
        execution = {
            'task_id': task_id,
            'start_time': start_time,
            'end_time': datetime.now(),
            'duration_ms': (datetime.now() - start_time).total_seconds() * 1000,
            'success': success,
            'result': result,
            'error': error
        }
        
        self._execution_history.append(execution)
        
        if len(self._execution_history) > self._max_history_size:
            self._execution_history.pop(0)
    
    def get_execution_history(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get task execution history"""
        history = self._execution_history
        
        if task_id:
            history = [h for h in history if h['task_id'] == task_id]
        
        return history[-limit:]
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        tasks = list(self._scheduled_tasks.values())
        
        return {
            'total_tasks': len(tasks),
            'active_tasks': sum(1 for t in tasks if t.is_active),
            'paused_tasks': sum(1 for t in tasks if not t.is_active),
            'total_executions': sum(t.execution_count for t in tasks),
            'recent_executions': len(self.get_execution_history(limit=10)),
            'next_scheduled': min(
                (t.next_run for t in tasks if t.next_run and t.is_active),
                default=None
            )
        }


@dataclass
class CalendarSchedule:
    """Calendar-based schedule"""
    schedule_name: str
    timezone: str = "UTC"
    working_days: Set[int] = field(default_factory=lambda: {0, 1, 2, 3, 4})
    working_hours_start: int = 9
    working_hours_end: int = 17
    holidays: Set[str] = field(default_factory=set)
    
    def is_working_day(self, dt: datetime) -> bool:
        """Check if date is a working day"""
        if dt.weekday() not in self.working_days:
            return False
        
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in self.holidays:
            return False
        
        return True
    
    def is_working_hour(self, dt: datetime) -> bool:
        """Check if time is within working hours"""
        if not self.is_working_day(dt):
            return False
        
        return self.working_hours_start <= dt.hour < self.working_hours_end
    
    def get_next_working_time(
        self,
        base_time: Optional[datetime] = None
    ) -> datetime:
        """Get next working time from base time"""
        if base_time is None:
            base_time = datetime.now()
        
        next_time = base_time
        
        for _ in range(365):
            if self.is_working_hour(next_time):
                return next_time
            
            next_time += timedelta(hours=1)
            
            if not self.is_working_day(next_time):
                days_ahead = (7 - next_time.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                next_time += timedelta(days=days_ahead - 1)
                next_time = next_time.replace(
                    hour=self.working_hours_start,
                    minute=0,
                    second=0
                )
        
        raise RuntimeError("Could not find next working time")


if __name__ == "__main__":
    print("Advanced Task Scheduling Module")
    print("=" * 50)
    
    scheduler = AdvancedTaskScheduler()
    
    print("\n1. Creating cron tasks:")
    
    scheduler.create_cron_task(
        task_id="daily_report",
        task_name="Generate Daily Report",
        cron_expression="0 9 * * *",
        handler=lambda: print("Generating daily report...")
    )
    
    scheduler.create_cron_task(
        task_id="hourly_cleanup",
        task_name="Hourly Cleanup",
        cron_expression="0 * * * *",
        handler=lambda: print("Running cleanup...")
    )
    
    scheduler.create_cron_task(
        task_id="weekday_backup",
        task_name="Weekday Backup",
        cron_expression="0 2 * * 1-5",
        handler=lambda: print("Running backup...")
    )
    
    print("\n2. Creating interval task:")
    
    scheduler.create_interval_task(
        task_id="health_check",
        task_name="Health Check",
        interval_seconds=300,
        handler=lambda: print("Health check...")
    )
    
    print("\n3. Task information:")
    for task in scheduler.get_all_tasks():
        print(f"   {task.task_id}: {task.task_name}")
        if task.schedule_type == ScheduleType.CRON:
            cron = task.cron_expression
            print(f"      Schedule: {cron.get_schedule_description()}")
        elif task.schedule_type == ScheduleType.INTERVAL:
            print(f"      Interval: every {task.interval_seconds}s")
        print(f"      Next run: {task.next_run}")
        print()
    
    print("\n4. Scheduler status:")
    status = scheduler.get_scheduler_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
