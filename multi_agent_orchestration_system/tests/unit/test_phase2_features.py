"""
Unit Tests - Phase 2 Advanced Features
====================================

Tests for WebSocket, distributed tracing, advanced scheduling, caching, and Redis queue.
"""

import unittest
from datetime import datetime, timedelta

try:
    from multi_agent_orchestration_system.infrastructure_layer.websocket import (
        WebSocketEventType,
        WebSocketMessage,
        WebSocketConnectionState,
        ClientSession,
        WebSocketAuthenticationManager,
        WebSocketEventBroadcaster,
        WebSocketMessageHandler
    )
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

try:
    from multi_agent_orchestration_system.infrastructure_layer.tracing import (
        DistributedTracer,
        Span,
        SpanAttributes,
        SpanContext,
        TracingMetrics
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

try:
    from multi_agent_orchestration_system.application_services.scheduling.advanced_scheduler import (
        CronExpression,
        ScheduledTask,
        AdvancedTaskScheduler,
        ScheduleType
    )
    SCHEDULING_AVAILABLE = True
except ImportError:
    SCHEDULING_AVAILABLE = False

try:
    from multi_agent_orchestration_system.application_services.cache.task_result_cache import (
        TaskResultCache,
        CacheEntry,
        CacheInvalidationStrategy
    )
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class TestWebSocketMessage(unittest.TestCase):
    """Test WebSocket message functionality"""
    
    def test_message_creation(self):
        """Test message creation"""
        if not WEBSOCKET_AVAILABLE:
            self.skipTest("WebSocket module not available")
        
        message = WebSocketMessage(
            event_type=WebSocketEventType.TASK_CREATED,
            payload={'task_id': '123', 'task_name': 'Test Task'}
        )
        
        self.assertIsNotNone(message.message_id)
        self.assertEqual(message.event_type, WebSocketEventType.TASK_CREATED)
        self.assertIn('task_id', message.payload)
    
    def test_message_serialization(self):
        """Test message JSON serialization"""
        if not WEBSOCKET_AVAILABLE:
            self.skipTest("WebSocket module not available")
        
        message = WebSocketMessage(
            event_type=WebSocketEventType.AGENT_REGISTERED,
            payload={'agent_name': 'test_agent'}
        )
        
        json_str = message.to_json()
        self.assertIsInstance(json_str, str)
        
        restored = WebSocketMessage.from_json(json_str)
        self.assertEqual(restored.event_type, message.event_type)
        self.assertEqual(restored.payload, message.payload)


class TestClientSession(unittest.TestCase):
    """Test WebSocket client session"""
    
    def test_session_creation(self):
        """Test session creation"""
        if not WEBSOCKET_AVAILABLE:
            self.skipTest("WebSocket module not available")
        
        session = ClientSession(
            client_id="test-client-1",
            user_id="user123",
            username="testuser"
        )
        
        self.assertEqual(session.client_id, "test-client-1")
        self.assertEqual(session.user_id, "user123")
        self.assertTrue(session.is_active())
    
    def test_session_subscription(self):
        """Test event subscription"""
        if not WEBSOCKET_AVAILABLE:
            self.skipTest("WebSocket module not available")
        
        session = ClientSession(client_id="test-client-2")
        session.subscribe_to_event(WebSocketEventType.TASK_COMPLETED)
        
        self.assertIn(WebSocketEventType.TASK_COMPLETED, session.subscriptions)


class TestWebSocketAuthentication(unittest.TestCase):
    """Test WebSocket authentication"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not WEBSOCKET_AVAILABLE:
            self.skipTest("WebSocket module not available")
        self.auth_manager = WebSocketAuthenticationManager()
    
    def test_session_creation(self):
        """Test session creation"""
        session = self.auth_manager.create_session(
            client_id="client-1",
            user_id="user-1",
            username="testuser"
        )
        
        self.assertIsNotNone(session)
        self.assertEqual(session.username, "testuser")
    
    def test_session_retrieval(self):
        """Test session retrieval"""
        self.auth_manager.create_session(
            client_id="client-2",
            username="testuser2"
        )
        
        session = self.auth_manager.get_session("client-2")
        self.assertIsNotNone(session)
    
    def test_session_closure(self):
        """Test session closure"""
        self.auth_manager.create_session(
            client_id="client-3",
            username="testuser3"
        )
        
        result = self.auth_manager.close_session("client-3")
        self.assertTrue(result)
        
        session = self.auth_manager.get_session("client-3")
        self.assertIsNone(session)


class TestWebSocketBroadcaster(unittest.TestCase):
    """Test WebSocket event broadcaster"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not WEBSOCKET_AVAILABLE:
            self.skipTest("WebSocket module not available")
        self.broadcaster = WebSocketEventBroadcaster()
    
    def test_subscribe_unsubscribe(self):
        """Test subscription management"""
        asyncio = __import__('asyncio')
        
        async def test():
            await self.broadcaster.subscribe("client-1", WebSocketEventType.TASK_CREATED)
            count = self.broadcaster.get_subscriber_count(WebSocketEventType.TASK_CREATED)
            self.assertEqual(count, 1)
            
            await self.broadcaster.unsubscribe("client-1", WebSocketEventType.TASK_CREATED)
            count = self.broadcaster.get_subscriber_count(WebSocketEventType.TASK_CREATED)
            self.assertEqual(count, 0)
        
        asyncio.run(test())


class TestDistributedTracer(unittest.TestCase):
    """Test distributed tracing"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not TRACING_AVAILABLE:
            self.skipTest("Tracing module not available")
        self.tracer = DistributedTracer(
            service_name="test-service",
            service_version="1.0.0"
        )
    
    def test_span_creation(self):
        """Test span creation"""
        with self.tracer.start_span("test_operation") as span:
            self.assertIsNotNone(span)
            self.assertEqual(span.name, "test_operation")
            self.assertIsNotNone(span.trace_id)
            self.assertIsNotNone(span.span_id)
    
    def test_span_attributes(self):
        """Test span attributes"""
        with self.tracer.start_span("test_operation") as span:
            span.set_attribute("key1", "value1")
            span.set_attribute("key2", 123)
            
            self.assertEqual(span.attributes.custom_attributes['key1'], "value1")
            self.assertEqual(span.attributes.custom_attributes['key2'], 123)
    
    def test_span_events(self):
        """Test span events"""
        with self.tracer.start_span("test_operation") as span:
            span.add_event("event1", {"detail": "test"})
            
            self.assertEqual(len(span.events), 1)
            self.assertEqual(span.events[0].name, "event1")
    
    def test_child_span(self):
        """Test child span creation"""
        with self.tracer.start_span("parent_operation") as parent:
            parent_span_id = parent.span_id
            
            with self.tracer.create_child_span(parent, "child_operation") as child:
                self.assertEqual(child.parent_span_id, parent_span_id)
                self.assertEqual(child.trace_id, parent.trace_id)


class TestTracingMetrics(unittest.TestCase):
    """Test tracing metrics"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not TRACING_AVAILABLE:
            self.skipTest("Tracing module not available")
        self.metrics = TracingMetrics()
    
    def test_metrics_recording(self):
        """Test metrics recording"""
        self.metrics.increment_span_count("OK")
        self.metrics.increment_span_count("OK")
        self.metrics.increment_span_count("ERROR")
        
        self.assertEqual(self.metrics.total_spans, 3)
        self.assertEqual(self.metrics.ok_spans, 2)
        self.assertEqual(self.metrics.error_spans, 1)
    
    def test_error_rate(self):
        """Test error rate calculation"""
        self.metrics.increment_span_count("OK")
        self.metrics.increment_span_count("ERROR")
        
        error_rate = self.metrics.get_error_rate()
        self.assertAlmostEqual(error_rate, 0.5, places=1)


class TestCronExpression(unittest.TestCase):
    """Test cron expression parsing"""
    
    def test_cron_expression_creation(self):
        """Test cron expression creation"""
        if not SCHEDULING_AVAILABLE:
            self.skipTest("Scheduling module not available")
        
        cron = CronExpression("0 * * * *")
        
        self.assertEqual(cron.minute, "0")
        self.assertEqual(cron.hour, "*")
    
    def test_cron_expression_with_seconds(self):
        """Test cron expression with seconds"""
        if not SCHEDULING_AVAILABLE:
            self.skipTest("Scheduling module not available")
        
        cron = CronExpression("30 * * * * *", include_seconds=True)
        
        self.assertEqual(cron.second, "30")
    
    def test_invalid_cron_expression(self):
        """Test invalid cron expression"""
        if not SCHEDULING_AVAILABLE:
            self.skipTest("Scheduling module not available")
        
        with self.assertRaises(ValueError):
            CronExpression("invalid cron")


class TestScheduledTask(unittest.TestCase):
    """Test scheduled task"""
    
    def test_task_creation(self):
        """Test task creation"""
        if not SCHEDULING_AVAILABLE:
            self.skipTest("Scheduling module not available")
        
        task = ScheduledTask(
            task_id="test-task",
            task_name="Test Task",
            schedule_type=ScheduleType.ONE_TIME,
            start_time=datetime.now()
        )
        
        self.assertEqual(task.task_id, "test-task")
        self.assertTrue(task.is_active)
    
    def test_task_execution_recording(self):
        """Test task execution recording"""
        if not SCHEDULING_AVAILABLE:
            self.skipTest("Scheduling module not available")
        
        task = ScheduledTask(
            task_id="test-task-2",
            task_name="Test Task 2",
            schedule_type=ScheduleType.ONE_TIME,
            start_time=datetime.now(),
            max_executions=2
        )
        
        task.record_execution()
        self.assertEqual(task.execution_count, 1)
        
        task.record_execution()
        self.assertEqual(task.execution_count, 2)
        self.assertFalse(task.is_active)


class TestAdvancedTaskScheduler(unittest.TestCase):
    """Test advanced task scheduler"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not SCHEDULING_AVAILABLE:
            self.skipTest("Scheduling module not available")
        self.scheduler = AdvancedTaskScheduler()
    
    def test_cron_task_creation(self):
        """Test cron task creation"""
        task = self.scheduler.create_cron_task(
            task_id="cron-task-1",
            task_name="Cron Task",
            cron_expression="0 * * * *",
            handler=lambda: None
        )
        
        self.assertIsNotNone(task)
        self.assertEqual(task.schedule_type, ScheduleType.CRON)
    
    def test_interval_task_creation(self):
        """Test interval task creation"""
        task = self.scheduler.create_interval_task(
            task_id="interval-task-1",
            task_name="Interval Task",
            interval_seconds=60,
            handler=lambda: None
        )
        
        self.assertIsNotNone(task)
        self.assertEqual(task.schedule_type, ScheduleType.INTERVAL)
    
    def test_task_cancellation(self):
        """Test task cancellation"""
        self.scheduler.create_cron_task(
            task_id="cancel-task",
            task_name="Cancel Task",
            cron_expression="0 * * * *",
            handler=lambda: None
        )
        
        result = self.scheduler.cancel_task("cancel-task")
        self.assertTrue(result)
        
        task = self.scheduler.get_task("cancel-task")
        self.assertFalse(task.is_active)
    
    def test_scheduler_status(self):
        """Test scheduler status"""
        self.scheduler.create_cron_task(
            task_id="status-task",
            task_name="Status Task",
            cron_expression="0 * * * *",
            handler=lambda: None
        )
        
        status = self.scheduler.get_scheduler_status()
        
        self.assertIn('total_tasks', status)
        self.assertIn('active_tasks', status)


class TestTaskResultCache(unittest.TestCase):
    """Test task result caching"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not CACHE_AVAILABLE:
            self.skipTest("Cache module not available")
        self.cache = TaskResultCache(max_size=100)
    
    def test_cache_set_get(self):
        """Test cache set and get"""
        self.cache.set("key1", {"result": "value1"})
        result = self.cache.get("key1")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['result'], "value1")
    
    def test_cache_miss(self):
        """Test cache miss"""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        self.cache.set("key2", {"data": "test"})
        self.assertIsNotNone(self.cache.get("key2"))
        
        self.cache.invalidate("key2")
        self.assertIsNone(self.cache.get("key2"))
    
    def test_cache_statistics(self):
        """Test cache statistics"""
        self.cache.set("key3", {"data": "test"})
        self.cache.get("key3")
        self.cache.get("nonexistent")
        
        stats = self.cache.get_statistics()
        
        self.assertIn('hit_count', stats)
        self.assertIn('miss_count', stats)
        self.assertIn('hit_rate', stats)
    
    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        cache = TaskResultCache(default_ttl=1)
        cache.set("key4", {"data": "test"})
        
        import time
        time.sleep(1.1)
        
        result = cache.get("key4")
        self.assertIsNone(result)
    
    def test_cache_eviction(self):
        """Test cache eviction with LRU"""
        cache = TaskResultCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        cache.get("key1")
        
        cache.set("key4", "value4")
        
        self.assertIsNone(cache.get("key2"))


class TestCacheEntry(unittest.TestCase):
    """Test cache entry"""
    
    def test_entry_creation(self):
        """Test entry creation"""
        if not CACHE_AVAILABLE:
            self.skipTest("Cache module not available")
        
        entry = CacheEntry(
            key="test-key",
            value={"data": "test"}
        )
        
        self.assertEqual(entry.key, "test-key")
        self.assertEqual(entry.access_count, 0)
        self.assertFalse(entry.compressed)
    
    def test_entry_access_update(self):
        """Test entry access tracking"""
        if not CACHE_AVAILABLE:
            self.skipTest("Cache module not available")
        
        entry = CacheEntry(key="test-key", value="test")
        entry.update_access()
        
        self.assertEqual(entry.access_count, 1)
    
    def test_entry_expiration(self):
        """Test entry TTL expiration"""
        if not CACHE_AVAILABLE:
            self.skipTest("Cache module not available")
        
        entry = CacheEntry(
            key="test-key",
            value="test",
            ttl_seconds=1
        )
        
        self.assertFalse(entry.is_expired())
        
        import time
        time.sleep(1.1)
        
        self.assertTrue(entry.is_expired())


if __name__ == '__main__':
    unittest.main()
