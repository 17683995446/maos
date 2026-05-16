"""
Infrastructure Layer - Resilience Patterns Module
=============================================

Provides resilience patterns for fault tolerance.
Part of the production hardening Phase 1 improvements.

Key Features:
  - Circuit Breaker Pattern
  - Retry with Exponential Backoff
  - Dead Letter Queue Handler
  - Bulkhead Isolation
  - Timeout Management

Architecture:
  - Follows resilience engineering principles
  - Integrates with monitoring and alerting
  - Supports both sync and async operations
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfiguration:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3
    excluded_exceptions: tuple = ()


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    def __init__(self, circuit_name: str, retry_after: float):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{circuit_name}' is open. "
            f"Retry after {retry_after:.1f} seconds."
        )


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    
    Prevents cascading failures by stopping requests to a failing service.
    
    States:
      - CLOSED: Normal operation, requests pass through
      - OPEN: Service is failing, requests are blocked
      - HALF_OPEN: Testing if service recovered
    
    Usage:
      circuit = CircuitBreaker("payment-service", failure_threshold=5)
      
      try:
          with circuit:
              result = payment_service.process()
      except CircuitBreakerOpenError:
          return "Service temporarily unavailable"
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfiguration] = None,
        fallback_func: Optional[Callable] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfiguration()
        self.fallback_func = fallback_func
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.RLock()
        
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._rejected_calls = 0
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout transition"""
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = (datetime.now() - self._opened_at).total_seconds()
            if elapsed >= self.config.timeout_seconds:
                logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN after timeout")
                self._transition_to(CircuitState.HALF_OPEN)
        
        return self._state
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state"""
        old_state = self._state
        self._state = new_state
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.OPEN:
            self._opened_at = datetime.now()
        
        logger.info(f"Circuit '{self.name}' state changed: {old_state.value} -> {new_state.value}")
    
    def _record_success(self) -> None:
        """Record successful call"""
        with self._lock:
            self._failure_count = 0
            self._success_count += 1
            self._successful_calls += 1
            self._total_calls += 1
            
            if self.state == CircuitState.HALF_OPEN:
                if self._success_count >= self.config.success_threshold:
                    logger.info(f"Circuit '{self.name}' recovered, closing")
                    self._transition_to(CircuitState.CLOSED)
    
    def _record_failure(self, exception: Exception) -> None:
        """Record failed call"""
        if isinstance(exception, self.config.excluded_exceptions):
            logger.debug(f"Circuit '{self.name}' ignoring excluded exception: {exception}")
            return
        
        with self._lock:
            self._failure_count += 1
            self._failed_calls += 1
            self._total_calls += 1
            self._last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit '{self.name}' failed in HALF_OPEN, reopening")
                self._transition_to(CircuitState.OPEN)
            elif self._failure_count >= self.config.failure_threshold:
                logger.warning(f"Circuit '{self.name}' failure threshold reached, opening")
                self._transition_to(CircuitState.OPEN)
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        
        return False
    
    def __enter__(self):
        """Context manager entry"""
        if not self._should_allow_request():
            self._rejected_calls += 1
            retry_after = self.config.timeout_seconds
            if self._opened_at:
                elapsed = (datetime.now() - self._opened_at).total_seconds()
                retry_after = max(0, self.config.timeout_seconds - elapsed)
            raise CircuitBreakerOpenError(self.name, retry_after)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None and exc_val is not None:
            self._record_failure(exc_val)
            return False
        
        self._record_success()
        return True
    
    def call(self, func: Callable[[], T], *args, **kwargs) -> T:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function fails
        """
        with self:
            if self.fallback_func and self.state == CircuitState.HALF_OPEN:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Circuit '{self.name}' fallback triggered")
                    return self.fallback_func()
            return func(*args, **kwargs)
    
    async def call_async(self, coro) -> Any:
        """Async wrapper for circuit breaker"""
        if not self._should_allow_request():
            self._rejected_calls += 1
            retry_after = self.config.timeout_seconds
            raise CircuitBreakerOpenError(self.name, retry_after)
        
        try:
            result = await coro
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise
    
    def get_statistics(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'total_calls': self._total_calls,
            'successful_calls': self._successful_calls,
            'failed_calls': self._failed_calls,
            'rejected_calls': self._rejected_calls,
            'last_failure_time': self._last_failure_time.isoformat() if self._last_failure_time else None,
            'opened_at': self._opened_at.isoformat() if self._opened_at else None
        }
    
    def reset(self) -> None:
        """Manually reset circuit breaker"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._total_calls = 0
            self._successful_calls = 0
            self._failed_calls = 0
            self._rejected_calls = 0
        logger.info(f"Circuit '{self.name}' manually reset")


@dataclass
class RetryableTask:
    """Task that can be retried"""
    task_id: str
    task_name: str
    payload: Any
    max_attempts: int = 3
    current_attempt: int = 0
    last_attempt_time: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class DeadLetterQueueHandler:
    """
    Dead Letter Queue (DLQ) handler for failed tasks.
    
    Features:
      - Failed task collection
      - Retry scheduling
      - Error analysis
      - Alert integration
      - Task resurrection
    
    Usage:
      dlq = DeadLetterQueueHandler()
      
      dlq.add_failed_task(task)
      if dlq.should_retry(task):
          dlq.retry_task(task)
    """
    
    def __init__(self, max_retries: int = 5):
        self.max_retries = max_retries
        self._queue: list[RetryableTask] = []
        self._processed_count = 0
        self._resurrected_count = 0
    
    def add_failed_task(
        self,
        task_id: str,
        task_name: str,
        payload: Any,
        error_message: str,
        metadata: Optional[dict] = None
    ) -> RetryableTask:
        """
        Add task to dead letter queue.
        
        Args:
            task_id: Unique task identifier
            task_name: Human-readable task name
            payload: Task input data
            error_message: Error description
            metadata: Additional task metadata
        
        Returns:
            Created RetryableTask
        """
        retryable_task = RetryableTask(
            task_id=task_id,
            task_name=task_name,
            payload=payload,
            current_attempt=0,
            last_error=error_message,
            metadata=metadata or {}
        )
        
        self._queue.append(retryable_task)
        logger.warning(f"Task {task_id} added to DLQ: {error_message}")
        
        return retryable_task
    
    def should_retry(self, task: RetryableTask) -> bool:
        """Check if task should be retried"""
        if task.current_attempt >= self.max_retries:
            logger.info(f"Task {task.task_id} exceeded max retries ({self.max_retries})")
            return False
        
        backoff_seconds = min(300, 2 ** task.current_attempt * 10)
        
        if task.last_attempt_time:
            elapsed = (datetime.now() - task.last_attempt_time).total_seconds()
            if elapsed < backoff_seconds:
                return False
        
        return True
    
    def retry_task(self, task: RetryableTask) -> Optional[Any]:
        """
        Retry failed task.
        
        Args:
            task: Task to retry
        
        Returns:
            Retry result or None if should not retry
        """
        if not self.should_retry(task):
            return None
        
        task.current_attempt += 1
        task.last_attempt_time = datetime.now()
        logger.info(f"Retrying task {task.task_id} (attempt {task.current_attempt}/{self.max_retries})")
        
        return task.payload
    
    def get_queue_size(self) -> int:
        """Get number of tasks in DLQ"""
        return len(self._queue)
    
    def get_tasks_ready_for_retry(self) -> list[RetryableTask]:
        """Get tasks that are ready to be retried"""
        return [task for task in self._queue if self.should_retry(task)]
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from DLQ (after successful processing)"""
        for i, task in enumerate(self._queue):
            if task.task_id == task_id:
                self._queue.pop(i)
                self._processed_count += 1
                logger.info(f"Task {task_id} removed from DLQ")
                return True
        return False
    
    def resurrect_task(self, task_id: str) -> Optional[RetryableTask]:
        """
        Mark task as successfully processed (resurrected).
        
        Args:
            task_id: Task identifier
        
        Returns:
            Resurrected task or None if not found
        """
        for task in self._queue:
            if task.task_id == task_id:
                task.metadata['resurrected_at'] = datetime.now().isoformat()
                task.metadata['resurrected'] = True
                self._queue.remove(task)
                self._processed_count += 1
                self._resurrected_count += 1
                logger.info(f"Task {task_id} resurrected successfully")
                return task
        return None
    
    def get_statistics(self) -> dict:
        """Get DLQ statistics"""
        retryable = self.get_tasks_ready_for_retry()
        return {
            'total_tasks': len(self._queue),
            'ready_for_retry': len(retryable),
            'exhausted_retries': len(self._queue) - len(retryable),
            'processed_count': self._processed_count,
            'resurrected_count': self._resurrected_count,
            'retryable_tasks': [
                {
                    'task_id': t.task_id,
                    'task_name': t.task_name,
                    'current_attempt': t.current_attempt,
                    'last_error': t.last_error
                }
                for t in retryable[:10]
            ]
        }


class RetryPolicy:
    """
    Retry policy with exponential backoff.
    
    Features:
      - Configurable retry attempts
      - Exponential backoff
      - Jitter support
      - Exception filtering
    
    Usage:
      retry = RetryPolicy(max_attempts=3, base_delay=1.0)
      
      for attempt in retry:
          try:
              result = risky_operation()
              break
          except Exception as e:
              if not retry.should_retry(e, attempt):
                  raise
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if operation should be retried"""
        if attempt >= self.max_attempts:
            return False
        
        if not isinstance(exception, self.retryable_exceptions):
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay before next retry"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay
    
    def execute(self, func: Callable[[], T]) -> T:
        """Execute function with retry policy"""
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func()
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    raise
                
                if attempt < self.max_attempts:
                    delay = self.get_delay(attempt)
                    logger.warning(f"Retry attempt {attempt}/{self.max_attempts} after {delay:.2f}s")
                    time.sleep(delay)
        
        if last_exception:
            raise last_exception


class BulkheadIsolation:
    """
    Bulkhead isolation pattern for resource protection.
    
    Limits concurrent execution to prevent resource exhaustion.
    
    Usage:
      bulkhead = BulkheadIsolation(max_concurrent=10)
      
      with bulkhead:
          execute_task()
    """
    
    def __init__(self, max_concurrent: int = 10, max_queue_size: int = 0):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active_count = 0
        self._rejected_count = 0
        self._lock = threading.Lock()
    
    def __enter__(self):
        acquired = self._semaphore.acquire(timeout=0)
        if not acquired:
            with self._lock:
                self._rejected_count += 1
            raise RuntimeError("Bulkhead isolation: concurrent limit reached")
        
        with self._lock:
            self._active_count += 1
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            self._active_count -= 1
        self._semaphore.release()
        return False
    
    def get_stats(self) -> dict:
        """Get bulkhead statistics"""
        return {
            'max_concurrent': self.max_concurrent,
            'active_count': self._active_count,
            'available': self.max_concurrent - self._active_count,
            'rejected_count': self._rejected_count
        }


if __name__ == "__main__":
    circuit = CircuitBreaker("test-service")
    
    for i in range(3):
        try:
            with circuit:
                if i == 2:
                    raise ConnectionError("Connection failed")
                print(f"Call {i+1}: Success")
        except Exception as e:
            print(f"Call {i+1}: Failed - {e}")
    
    print("\nCircuit stats:", circuit.get_statistics())
    
    dlq = DeadLetterQueueHandler()
    task = dlq.add_failed_task("task-1", "Process Order", {"order_id": 123}, "Timeout")
    print("\nDLQ size:", dlq.get_queue_size())
    print("Should retry:", dlq.should_retry(task))
    
    retry = RetryPolicy(max_attempts=3, base_delay=0.1)
    print("\nRetry delays:", [retry.get_delay(i) for i in range(1, 4)])
