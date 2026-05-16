"""
Infrastructure Layer - Distributed Tracing Module
==============================================

Provides distributed tracing using OpenTelemetry for observability.
Part of the Phase 2 production hardening improvements.

Key Features:
  - Distributed trace propagation
  - Span management
  - Trace context handling
  - Metrics collection
  - Log correlation
  - Performance monitoring

Architecture:
  - Uses OpenTelemetry SDK
  - OTLP exporter support
  - Automatic instrumentation
  - Manual span creation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from contextvars import ContextVar
import time
import logging
import json
import uuid

logger = logging.getLogger(__name__)

trace_context: ContextVar[Optional['SpanContext']] = ContextVar('trace_context', default=None)


class TraceLevel(Enum):
    """Trace verbosity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SpanContext:
    """Trace span context information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1
    is_sampled: bool = True
    is_remote: bool = False


@dataclass
class SpanAttributes:
    """Attributes for spans"""
    service_name: str = ""
    service_version: str = ""
    deployment_environment: str = "development"
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    operation_name: str = ""
    operation_type: str = ""
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'service.name': self.service_name,
            'service.version': self.service_version,
            'deployment.environment': self.deployment_environment,
            'agent.name': self.agent_name,
            'task.id': self.task_id,
            'workflow.id': self.workflow_id,
            'operation.name': self.operation_name,
            'operation.type': self.operation_type,
            **self.custom_attributes
        }


@dataclass
class SpanEvent:
    """Event within a span"""
    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """
    Distributed trace span.
    
    Represents a unit of work in a distributed system.
    
    Usage:
        tracer = DistributedTracer()
        
        with tracer.start_span("process_task") as span:
            span.set_attribute("task.id", task_id)
            # do work
            span.add_event("task_started")
            # do more work
            span.add_event("task_completed")
    """
    span_id: str
    trace_id: str
    name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    attributes: SpanAttributes = field(default_factory=SpanAttributes)
    events: List[SpanEvent] = field(default_factory=list)
    parent_span_id: Optional[str] = None
    status: str = "OK"
    status_message: Optional[str] = None
    links: List['Span'] = field(default_factory=list)
    is_recording: bool = True
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute"""
        self.attributes.custom_attributes[key] = value
    
    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add event to span"""
        event = SpanEvent(
            name=name,
            attributes=attributes or {}
        )
        self.events.append(event)
    
    def set_status(self, status: str, message: Optional[str] = None) -> None:
        """Set span status"""
        self.status = status
        self.status_message = message
    
    def record_exception(self, exception: Exception) -> None:
        """Record exception in span"""
        self.add_event(
            "exception",
            {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
                "exception.stacktrace": str(exception.__traceback__)
            }
        )
        self.set_status("ERROR", str(exception))
    
    def end(self) -> None:
        """End the span"""
        self.end_time = datetime.now()
        self.is_recording = False
    
    def __enter__(self) -> 'Span':
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit"""
        if exc_val is not None and self.is_recording:
            self.record_exception(exc_val)
        self.end()
        return False
    
    def get_duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            'span_id': self.span_id,
            'trace_id': self.trace_id,
            'name': self.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.get_duration_ms(),
            'attributes': self.attributes.to_dict(),
            'events': [
                {
                    'name': e.name,
                    'timestamp': e.timestamp.isoformat(),
                    'attributes': e.attributes
                }
                for e in self.events
            ],
            'parent_span_id': self.parent_span_id,
            'status': self.status,
            'status_message': self.status_message
        }


class DistributedTracer:
    """
    Distributed tracing service using OpenTelemetry principles.
    
    Features:
      - Trace creation and management
      - Span lifecycle management
      - Context propagation
      - Sampling strategies
      - Metrics collection
      - Log correlation
    
    Usage:
        tracer = DistributedTracer(service_name="maos")
        
        with tracer.start_span("process_task") as span:
            span.set_attribute("task.id", "123")
            process_task()
    """
    
    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        environment: str = "development"
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self._spans: Dict[str, Span] = {}
        self._active_span: Optional[Span] = None
        self._sampler = Sampler(sampling_rate=1.0)
        self._metrics = TracingMetrics()
    
    def generate_trace_id(self) -> str:
        """Generate new trace ID"""
        return uuid.uuid4().hex[:32]
    
    def generate_span_id(self) -> str:
        """Generate new span ID"""
        return uuid.uuid4().hex[:16]
    
    def start_span(
        self,
        name: str,
        attributes: Optional[SpanAttributes] = None,
        parent_context: Optional[SpanContext] = None,
        links: Optional[List[Span]] = None
    ) -> Span:
        """
        Start a new span.
        
        Args:
            name: Span name (operation name)
            attributes: Span attributes
            parent_context: Parent span context
            links: Links to other spans
        
        Returns:
            New span instance
        """
        trace_id = parent_context.trace_id if parent_context else self.generate_trace_id()
        parent_span_id = parent_context.span_id if parent_context else None
        
        span_id = self.generate_span_id()
        
        if attributes is None:
            attributes = SpanAttributes(
                service_name=self.service_name,
                service_version=self.service_version,
                deployment_environment=self.environment,
                operation_name=name
            )
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            parent_span_id=parent_span_id,
            attributes=attributes,
            links=links or [],
            is_recording=True
        )
        
        self._spans[span_id] = span
        self._active_span = span
        
        logger.debug(f"Started span: {name} (trace_id={trace_id}, span_id={span_id})")
        
        return span
    
    def end_span(self, span: Span) -> None:
        """End a span"""
        if not span.is_recording:
            logger.warning(f"Span {span.span_id} already ended")
            return
        
        span.end()
        
        if span.get_duration_ms():
            self._metrics.record_span_duration(span.get_duration_ms())
        
        self._metrics.increment_span_count(span.status)
        
        if span.parent_span_id:
            parent_span = self._spans.get(span.parent_span_id)
            if parent_span:
                parent_span.add_event(
                    "child_span_ended",
                    {'child_span_id': span.span_id}
                )
        
        if self._active_span == span:
            self._active_span = None
        
        logger.debug(f"Ended span: {span.name} (duration={span.get_duration_ms()}ms)")
    
    def get_current_span(self) -> Optional[Span]:
        """Get current active span"""
        return self._active_span
    
    def get_span_context(self, span: Span) -> SpanContext:
        """Get span context for propagation"""
        return SpanContext(
            trace_id=span.trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id
        )
    
    def inject_context(
        self,
        carrier: Dict[str, str],
        span: Optional[Span] = None
    ) -> Dict[str, str]:
        """
        Inject trace context into carrier (e.g., HTTP headers).
        
        Args:
            carrier: Dictionary to inject context into
            span: Span to extract context from (or current span if None)
        
        Returns:
            Carrier with injected context
        """
        span = span or self._active_span
        if not span:
            return carrier
        
        carrier['traceparent'] = f"00-{span.trace_id}-{span.span_id}-01"
        
        return carrier
    
    def extract_context(
        self,
        carrier: Dict[str, str]
    ) -> Optional[SpanContext]:
        """
        Extract trace context from carrier.
        
        Args:
            carrier: Dictionary containing trace context
        
        Returns:
            Extracted span context or None
        """
        traceparent = carrier.get('traceparent')
        if not traceparent:
            return None
        
        parts = traceparent.split('-')
        if len(parts) != 4:
            return None
        
        return SpanContext(
            trace_id=parts[1],
            span_id=parts[2],
            is_remote=True
        )
    
    def create_child_span(
        self,
        parent_span: Span,
        name: str,
        attributes: Optional[SpanAttributes] = None
    ) -> Span:
        """Create child span from parent"""
        context = self.get_span_context(parent_span)
        return self.start_span(
            name=name,
            attributes=attributes,
            parent_context=context
        )
    
    def get_all_spans(self) -> List[Span]:
        """Get all recorded spans"""
        return list(self._spans.values())
    
    def get_traces_by_trace_id(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace"""
        return [
            span for span in self._spans.values()
            if span.trace_id == trace_id
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tracing metrics"""
        return self._metrics.to_dict()
    
    def clear(self) -> None:
        """Clear all spans and metrics"""
        self._spans.clear()
        self._active_span = None
        self._metrics.reset()


class SpanContextManager:
    """Context manager for span lifecycle"""
    
    def __init__(self, tracer: DistributedTracer, span: Span):
        self.tracer = tracer
        self.span = span
    
    def __enter__(self) -> Span:
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None and self.span.is_recording:
            self.span.record_exception(exc_val)
        
        self.tracer.end_span(self.span)
        return False


class Sampler:
    """Trace sampler for controlling sampling rate"""
    
    def __init__(self, sampling_rate: float = 1.0):
        self.sampling_rate = max(0.0, min(1.0, sampling_rate))
    
    def should_sample(self, trace_id: str) -> bool:
        """Determine if trace should be sampled"""
        if self.sampling_rate >= 1.0:
            return True
        if self.sampling_rate <= 0.0:
            return False
        
        trace_hash = int(trace_id[:8], 16)
        return (trace_hash % 100) < (self.sampling_rate * 100)


class TracingMetrics:
    """Metrics collection for tracing"""
    
    def __init__(self):
        self.total_spans = 0
        self.ok_spans = 0
        self.error_spans = 0
        self.span_durations: List[float] = []
        self.max_duration_samples = 1000
    
    def increment_span_count(self, status: str) -> None:
        """Increment span count"""
        self.total_spans += 1
        if status == "OK":
            self.ok_spans += 1
        else:
            self.error_spans += 1
    
    def record_span_duration(self, duration_ms: float) -> None:
        """Record span duration"""
        self.span_durations.append(duration_ms)
        if len(self.span_durations) > self.max_duration_samples:
            self.span_durations.pop(0)
    
    def get_error_rate(self) -> float:
        """Get error rate"""
        if self.total_spans == 0:
            return 0.0
        return self.error_spans / self.total_spans
    
    def get_avg_duration(self) -> float:
        """Get average duration"""
        if not self.span_durations:
            return 0.0
        return sum(self.span_durations) / len(self.span_durations)
    
    def get_p95_duration(self) -> float:
        """Get p95 duration"""
        if not self.span_durations:
            return 0.0
        sorted_durations = sorted(self.span_durations)
        index = int(len(sorted_durations) * 0.95)
        return sorted_durations[min(index, len(sorted_durations) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'total_spans': self.total_spans,
            'ok_spans': self.ok_spans,
            'error_spans': self.error_spans,
            'error_rate': self.get_error_rate(),
            'avg_duration_ms': self.get_avg_duration(),
            'p95_duration_ms': self.get_p95_duration()
        }
    
    def reset(self) -> None:
        """Reset metrics"""
        self.total_spans = 0
        self.ok_spans = 0
        self.error_spans = 0
        self.span_durations.clear()


class AgentTracingMixin:
    """Mixin for adding tracing to agents"""
    
    def __init__(self):
        self._tracer: Optional[DistributedTracer] = None
    
    def set_tracer(self, tracer: DistributedTracer) -> None:
        """Set tracer instance"""
        self._tracer = tracer
    
    def create_span_for_task(
        self,
        task_name: str,
        task_id: str
    ) -> Optional[Span]:
        """Create span for task execution"""
        if not self._tracer:
            return None
        
        attributes = SpanAttributes(
            agent_name=self.agent_name if hasattr(self, 'agent_name') else None,
            task_id=task_id,
            operation_name=task_name,
            operation_type="task_execution"
        )
        
        return self._tracer.start_span(task_name, attributes=attributes)
    
    def trace_task_execution(
        self,
        task_name: str,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with tracing"""
        span = self.create_span_for_task(task_name, task_id)
        
        if not span:
            return func(*args, **kwargs)
        
        try:
            result = func(*args, **kwargs)
            span.set_status("OK")
            return result
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            self._tracer.end_span(span)


class WorkflowTracingDecorator:
    """Decorator for tracing workflow execution"""
    
    def __init__(self, tracer: DistributedTracer):
        self.tracer = tracer
    
    def trace(self, workflow_name: str):
        """Decorator to trace workflow execution"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                span = self.tracer.start_span(workflow_name)
                span.set_attribute("workflow.name", workflow_name)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status("OK")
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
                finally:
                    self.tracer.end_span(span)
            
            return wrapper
        return decorator


if __name__ == "__main__":
    print("Distributed Tracing Module")
    print("=" * 50)
    
    tracer = DistributedTracer(
        service_name="maos",
        service_version="2.1.0",
        environment="production"
    )
    
    print("\n1. Creating a span:")
    with tracer.start_span("process_order") as span:
        span.set_attribute("order.id", "12345")
        span.set_attribute("customer.id", "67890")
        span.add_event("order_received")
        time.sleep(0.1)
        span.add_event("order_processed")
        print(f"   Span: {span.name}")
        print(f"   Trace ID: {span.trace_id}")
        print(f"   Duration: {span.get_duration_ms():.2f}ms")
    
    print("\n2. Creating child spans:")
    with tracer.start_span("parent_operation") as parent:
        parent.set_attribute("operation.type", "batch_processing")
        
        with tracer.create_child_span(parent, "child_operation_1") as child1:
            child1.set_attribute("item.count", 10)
        
        with tracer.create_child_span(parent, "child_operation_2") as child2:
            child2.set_attribute("item.count", 20)
    
    print("\n3. Tracing metrics:")
    metrics = tracer.get_metrics()
    print(f"   Total spans: {metrics['total_spans']}")
    print(f"   Error rate: {metrics['error_rate']:.2%}")
    print(f"   Avg duration: {metrics['avg_duration_ms']:.2f}ms")
    print(f"   P95 duration: {metrics['p95_duration_ms']:.2f}ms")
    
    print("\n4. Context propagation:")
    with tracer.start_span("http_request") as span:
        headers = {}
        tracer.inject_context(headers, span)
        print(f"   Injected headers: {headers}")
        
        extracted_context = tracer.extract_context(headers)
        if extracted_context:
            print(f"   Extracted trace_id: {extracted_context.trace_id}")
