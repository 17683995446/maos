"""
Infrastructure Layer - Observability Module
=========================================

Provides comprehensive monitoring, metrics, and structured logging capabilities.
Built on industry-standard open-source tools for enterprise observability.

Key Components:
  - PrometheusMetricsCollector: Prometheus metrics collection and exposition
  - StructuredLogger: structlog-based structured logging
  - HealthCheckEndpoint: Application health checks
  - PerformanceTracker: Performance monitoring utilities

Architecture:
  - Prometheus: Metrics collection and exposition (pull-based)
  - structlog: Structured JSON logging for ELK/Loki integration
  - Health endpoints: Kubernetes-ready liveness/readiness probes
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import structlog
    from pythonjsonlogger import jsonlogger
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


class PrometheusMetricsCollector:
    """
    Prometheus metrics collector with pre-defined metrics for MAOS system.
    
    Exposed Metrics:
      - maos_tasks_total: Total number of tasks created
      - maos_tasks_completed: Tasks completed by status
      - maos_tasks_duration_seconds: Task execution duration histogram
      - maos_agents_registered: Number of registered agents
      - maos_agents_status: Current agent status gauge
      - maos_messages_sent: Messages sent by type
      - maos_workflows_executed: Workflows executed counter
    
    Usage:
      collector = PrometheusMetricsCollector()
      collector.record_task_created(task_type='data_cleaning', priority='high')
      metrics_output = collector.get_metrics()
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized and PROMETHEUS_AVAILABLE:
            self._setup_metrics()
            self._initialized = True
    
    def _setup_metrics(self):
        """Initialize all Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.registry = CollectorRegistry()
        
        self.tasks_created_counter = Counter(
            'maos_tasks_created_total',
            'Total number of tasks created',
            ['task_type', 'priority'],
            registry=self.registry
        )
        
        self.tasks_completed_counter = Counter(
            'maos_tasks_completed_total',
            'Tasks completed by status',
            ['task_type', 'status'],
            registry=self.registry
        )
        
        self.tasks_duration_histogram = Histogram(
            'maos_tasks_duration_seconds',
            'Task execution duration in seconds',
            ['task_type'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
            registry=self.registry
        )
        
        self.agents_registered_gauge = Gauge(
            'maos_agents_registered',
            'Number of registered agents',
            registry=self.registry
        )
        
        self.agents_status_gauge = Gauge(
            'maos_agents_status',
            'Current agent status (1=active, 0=inactive)',
            ['agent_name', 'status'],
            registry=self.registry
        )
        
        self.messages_sent_counter = Counter(
            'maos_messages_sent_total',
            'Messages sent by type',
            ['message_type'],
            registry=self.registry
        )
        
        self.workflows_executed_counter = Counter(
            'maos_workflows_executed_total',
            'Workflows executed',
            ['status'],
            registry=self.registry
        )
        
        self.system_uptime_gauge = Gauge(
            'maos_system_uptime_seconds',
            'System uptime in seconds',
            registry=self.registry
        )
        
        self.system_info = Info(
            'maos_system',
            'System information',
            registry=self.registry
        )
        
        self.system_info.info({
            'version': '2.0.0',
            'framework': 'multi_agent_orchestration_system'
        })
    
    def record_task_created(self, task_type: str, priority: str) -> None:
        """Record a task creation event"""
        if PROMETHEUS_AVAILABLE:
            self.tasks_created_counter.labels(task_type=task_type, priority=priority).inc()
    
    def record_task_completed(self, task_type: str, status: str, duration_seconds: float) -> None:
        """Record task completion with duration"""
        if PROMETHEUS_AVAILABLE:
            self.tasks_completed_counter.labels(task_type=task_type, status=status).inc()
            self.tasks_duration_histogram.labels(task_type=task_type).observe(duration_seconds)
    
    def record_task_failed(self, task_type: str, error_type: str) -> None:
        """Record task failure"""
        if PROMETHEUS_AVAILABLE:
            self.tasks_completed_counter.labels(task_type=task_type, status='failed').inc()
    
    def set_agents_count(self, count: int) -> None:
        """Update registered agents count"""
        if PROMETHEUS_AVAILABLE:
            self.agents_registered_gauge.set(count)
    
    def update_agent_status(self, agent_name: str, status: str, is_active: bool = True) -> None:
        """Update individual agent status"""
        if PROMETHEUS_AVAILABLE:
            self.agents_status_gauge.labels(
                agent_name=agent_name,
                status=status
            ).set(1 if is_active else 0)
    
    def record_message_sent(self, message_type: str) -> None:
        """Record message sent event"""
        if PROMETHEUS_AVAILABLE:
            self.messages_sent_counter.labels(message_type=message_type).inc()
    
    def record_workflow_executed(self, status: str) -> None:
        """Record workflow execution event"""
        if PROMETHEUS_AVAILABLE:
            self.workflows_executed_counter.labels(status=status).inc()
    
    def update_system_uptime(self, uptime_seconds: float) -> None:
        """Update system uptime metric"""
        if PROMETHEUS_AVAILABLE:
            self.system_uptime_gauge.set(uptime_seconds)
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics output"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry)
        return b""
    
    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)"""
        if PROMETHEUS_AVAILABLE:
            self._setup_metrics()


class StructuredLogger:
    """
    Structured JSON logger using structlog for enterprise logging.
    
    Features:
      - JSON output for ELK/Loki integration
      - Contextual logging with request IDs
      - Log level filtering
      - Custom processors for business events
    
    Usage:
      logger = StructuredLogger.get_logger("my_component")
      logger.info("task_completed", task_id="123", duration=1.5)
    """
    
    _configured = False
    _loggers = {}
    
    @classmethod
    def configure(
        cls,
        log_level: str = "INFO",
        log_format: str = "json",
        service_name: str = "multi_agent_orchestration_system"
    ) -> None:
        """
        Configure structured logging globally.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_format: Output format (json, console)
            service_name: Service identifier for log correlation
        """
        if not STRUCTLOG_AVAILABLE:
            logging.basicConfig(level=log_level)
            cls._configured = True
            return
        
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]
        
        if log_format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, log_level.upper()),
        )
        
        cls._loggers['service'] = structlog.get_logger(service_name)
        cls._configured = True
    
    @classmethod
    def get_logger(cls, component_name: str):
        """Get a logger instance for a specific component"""
        if not cls._configured:
            cls.configure()
        
        if component_name not in cls._loggers:
            if STRUCTLOG_AVAILABLE:
                cls._loggers[component_name] = structlog.get_logger(component_name)
            else:
                cls._loggers[component_name] = logging.getLogger(component_name)
        
        return cls._loggers[component_name]


class HealthCheckEndpoint:
    """
    Health check endpoint handler for Kubernetes/container orchestration.
    
    Provides:
      - Liveness probe: Is the process alive?
      - Readiness probe: Can it accept traffic?
      - Detailed health status with component checks
    """
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], tuple[bool, str]]] = {}
        self.start_time = datetime.now()
    
    def register_check(self, name: str, check_function: Callable[[], tuple[bool, str]]) -> None:
        """
        Register a health check function.
        
        Args:
            name: Check identifier
            check_function: Function returning (is_healthy, message)
        """
        self.checks[name] = check_function
    
    def check_liveness(self) -> Dict[str, Any]:
        """Liveness probe - is the process running?"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            'status': 'alive',
            'uptime_seconds': uptime,
            'timestamp': datetime.now().isoformat()
        }
    
    def check_readiness(self) -> Dict[str, Any]:
        """Readiness probe - can it accept traffic?"""
        results = {
            'status': 'ready',
            'checks': {},
            'timestamp': datetime.now().isoformat()
        }
        
        all_healthy = True
        for check_name, check_func in self.checks.items():
            try:
                is_healthy, message = check_func()
                results['checks'][check_name] = {
                    'healthy': is_healthy,
                    'message': message
                }
                if not is_healthy:
                    all_healthy = False
            except Exception as error:
                results['checks'][check_name] = {
                    'healthy': False,
                    'message': f'Check failed: {str(error)}'
                }
                all_healthy = False
        
        results['status'] = 'ready' if all_healthy else 'not_ready'
        return results
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed system status including all checks"""
        readiness = self.check_readiness()
        liveness = self.check_liveness()
        
        return {
            'liveness': liveness,
            'readiness': readiness,
            'overall_status': 'healthy' if readiness['status'] == 'ready' else 'unhealthy',
            'components_registered': len(self.checks)
        }


class PerformanceTracker:
    """
    Performance tracking utilities for monitoring execution times.
    
    Features:
      - Function execution time tracking
      - Context manager for timing blocks
      - Automatic metric recording
    """
    
    def __init__(self, metrics_collector: Optional[PrometheusMetricsCollector] = None):
        self.metrics_collector = metrics_collector or PrometheusMetricsCollector()
    
    def track_execution_time(self, operation_name: str):
        """
        Decorator to track function execution time.
        
        Usage:
          @tracker.track_execution_time('data_processing')
          def process_data():
              ...
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.metrics_collector.record_task_completed(
                        task_type=operation_name,
                        status='success',
                        duration_seconds=duration
                    )
                    return result
                except Exception as error:
                    duration = time.time() - start_time
                    self.metrics_collector.record_task_failed(
                        task_type=operation_name,
                        error_type=type(error).__name__
                    )
                    raise
            return wrapper
        return decorator
    
    @contextmanager
    def track_block(self, block_name: str):
        """
        Context manager for tracking execution time of code blocks.
        
        Usage:
          with tracker.track_block('data_transformation'):
              transform_data()
        """
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.metrics_collector.record_task_completed(
                task_type=block_name,
                status='success',
                duration_seconds=duration
            )
        except Exception as error:
            duration = time.time() - start_time
            self.metrics_collector.record_task_failed(
                task_type=block_name,
                error_type=type(error).__name__
            )
            raise


def get_metrics_collector() -> PrometheusMetricsCollector:
    """Get singleton metrics collector instance"""
    return PrometheusMetricsCollector()


def get_logger(component_name: str):
    """Get structured logger for component"""
    return StructuredLogger.get_logger(component_name)


def setup_observability(log_level: str = "INFO") -> None:
    """
    Setup complete observability stack.
    
    Args:
        log_level: Logging level
    """
    StructuredLogger.configure(log_level=log_level)
    get_logger("observability").info("Observability stack initialized")
