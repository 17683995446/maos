"""
Unit Tests - Infrastructure Layer
=================================

Tests for monitoring, persistence, and messaging infrastructure.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from multi_agent_orchestration_system.infrastructure_layer.observability import (
    PrometheusMetricsCollector,
    StructuredLogger,
    HealthCheckEndpoint,
    PerformanceTracker
)


class TestPrometheusMetricsCollector(unittest.TestCase):
    """Test Prometheus metrics collection"""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector can be initialized"""
        collector = PrometheusMetricsCollector()
        self.assertIsNotNone(collector)
    
    def test_task_created_recording(self):
        """Test recording task creation"""
        collector = PrometheusMetricsCollector()
        collector.record_task_created(task_type='data_cleaning', priority='high')
    
    def test_task_completed_recording(self):
        """Test recording task completion"""
        collector = PrometheusMetricsCollector()
        collector.record_task_completed(
            task_type='analysis',
            status='success',
            duration_seconds=1.5
        )
    
    def test_agent_count_recording(self):
        """Test recording agent count"""
        collector = PrometheusMetricsCollector()
        collector.set_agents_count(5)
    
    def test_message_sent_recording(self):
        """Test recording message sent"""
        collector = PrometheusMetricsCollector()
        collector.record_message_sent(message_type='task_request')


class TestStructuredLogger(unittest.TestCase):
    """Test structured logging"""
    
    def test_logger_configuration(self):
        """Test logger can be configured"""
        StructuredLogger.configure(log_level='INFO', log_format='console')
        self.assertTrue(StructuredLogger._configured)
    
    def test_get_logger(self):
        """Test getting logger instance"""
        StructuredLogger.configure()
        logger = StructuredLogger.get_logger('test_component')
        self.assertIsNotNone(logger)


class TestHealthCheckEndpoint(unittest.TestCase):
    """Test health check functionality"""
    
    def test_liveness_check(self):
        """Test liveness probe"""
        health = HealthCheckEndpoint()
        result = health.check_liveness()
        
        self.assertEqual(result['status'], 'alive')
        self.assertIn('uptime_seconds', result)
        self.assertIn('timestamp', result)
    
    def test_readiness_check_without_checks(self):
        """Test readiness probe with no registered checks"""
        health = HealthCheckEndpoint()
        result = health.check_readiness()
        
        self.assertEqual(result['status'], 'ready')
        self.assertIn('checks', result)
    
    def test_readiness_check_with_healthy_check(self):
        """Test readiness probe with healthy check"""
        health = HealthCheckEndpoint()
        health.register_check('test_component', lambda: (True, 'OK'))
        
        result = health.check_readiness()
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['checks']['test_component']['healthy'])
    
    def test_readiness_check_with_unhealthy_check(self):
        """Test readiness probe with unhealthy check"""
        health = HealthCheckEndpoint()
        health.register_check('test_component', lambda: (False, 'Error'))
        
        result = health.check_readiness()
        self.assertEqual(result['status'], 'not_ready')
        self.assertFalse(result['checks']['test_component']['healthy'])
    
    def test_detailed_status(self):
        """Test detailed status endpoint"""
        health = HealthCheckEndpoint()
        health.register_check('test', lambda: (True, 'OK'))
        
        status = health.get_detailed_status()
        self.assertIn('liveness', status)
        self.assertIn('readiness', status)
        self.assertIn('overall_status', status)


class TestPerformanceTracker(unittest.TestCase):
    """Test performance tracking"""
    
    def test_tracker_initialization(self):
        """Test tracker can be initialized"""
        tracker = PerformanceTracker()
        self.assertIsNotNone(tracker)
    
    def test_track_execution_time_decorator(self):
        """Test execution time tracking decorator"""
        tracker = PerformanceTracker()
        
        @tracker.track_execution_time('test_operation')
        def sample_function():
            return 42
        
        result = sample_function()
        self.assertEqual(result, 42)
    
    def test_track_block_context_manager(self):
        """Test block tracking context manager"""
        tracker = PerformanceTracker()
        
        with tracker.track_block('test_block'):
            data = {'key': 'value'}
        
        self.assertEqual(data['key'], 'value')


class TestInMemoryCache(unittest.TestCase):
    """Test in-memory cache fallback"""
    
    def test_cache_set_and_get(self):
        """Test basic cache operations"""
        from multi_agent_orchestration_system.infrastructure_layer.persistence.cache_manager import InMemoryCacheFallback
        
        cache = InMemoryCacheFallback()
        
        cache.set('key1', 'value1')
        result = cache.get('key1')
        
        self.assertEqual(result, 'value1')
    
    def test_cache_get_nonexistent(self):
        """Test getting non-existent key"""
        from multi_agent_orchestration_system.infrastructure_layer.persistence.cache_manager import InMemoryCacheFallback
        
        cache = InMemoryCacheFallback()
        result = cache.get('nonexistent')
        
        self.assertIsNone(result)
    
    def test_cache_delete(self):
        """Test cache deletion"""
        from multi_agent_orchestration_system.infrastructure_layer.persistence.cache_manager import InMemoryCacheFallback
        
        cache = InMemoryCacheFallback()
        
        cache.set('key1', 'value1')
        cache.delete('key1')
        result = cache.get('key1')
        
        self.assertIsNone(result)
    
    def test_cache_with_ttl(self):
        """Test cache with TTL"""
        from multi_agent_orchestration_system.infrastructure_layer.persistence.cache_manager import InMemoryCacheFallback
        import time
        
        cache = InMemoryCacheFallback()
        
        cache.set('key1', 'value1', ttl_seconds=1)
        result = cache.get('key1')
        
        self.assertEqual(result, 'value1')


class TestMessageEnvelope(unittest.TestCase):
    """Test message envelope functionality"""
    
    def test_message_creation(self):
        """Test creating message envelope"""
        from multi_agent_orchestration_system.infrastructure_layer.messaging import MessageEnvelope
        
        message = MessageEnvelope(
            message_id='msg-123',
            sender_name='agent1',
            receiver_names=['agent2'],
            message_type='task_request',
            payload={'data': 'test'}
        )
        
        self.assertEqual(message.sender_name, 'agent1')
        self.assertEqual(message.receiver_names, ['agent2'])
    
    def test_message_serialization(self):
        """Test message JSON serialization"""
        from multi_agent_orchestration_system.infrastructure_layer.messaging import MessageEnvelope
        
        message = MessageEnvelope(
            message_id='msg-123',
            sender_name='agent1',
            receiver_names=['agent2'],
            message_type='task_request',
            payload={'data': 'test'}
        )
        
        json_str = message.to_json_string()
        self.assertIsInstance(json_str, str)
        
        parsed = json.loads(json_str)
        self.assertEqual(parsed['message_id'], 'msg-123')


class TestInMemoryMessageBroker(unittest.TestCase):
    """Test in-memory message broker"""
    
    def test_message_publish_and_subscribe(self):
        """Test publish/subscribe pattern"""
        from multi_agent_orchestration_system.infrastructure_layer.messaging import (
            InMemoryMessageBroker,
            MessageEnvelope
        )
        
        broker = InMemoryMessageBroker()
        received_messages = []
        
        def callback(message):
            received_messages.append(message)
        
        broker.subscribe_to_channel('test_channel', callback)
        
        message = MessageEnvelope(
            message_id='msg-1',
            sender_name='agent1',
            receiver_names=['agent2'],
            message_type='task_request',
            payload={'data': 'test'}
        )
        
        broker.publish_message('test_channel', message)
        
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0].message_id, 'msg-1')
    
    def test_channel_message_count(self):
        """Test getting channel message count"""
        from multi_agent_orchestration_system.infrastructure_layer.messaging import (
            InMemoryMessageBroker,
            MessageEnvelope
        )
        
        broker = InMemoryMessageBroker()
        
        message = MessageEnvelope(
            message_id='msg-1',
            sender_name='agent1',
            receiver_names=['agent2'],
            message_type='task_request',
            payload={'data': 'test'}
        )
        
        broker.publish_message('test_channel', message)
        broker.publish_message('test_channel', message)
        
        count = broker.get_message_count('test_channel')
        self.assertEqual(count, 2)
    
    def test_clear_channel(self):
        """Test clearing channel messages"""
        from multi_agent_orchestration_system.infrastructure_layer.messaging import (
            InMemoryMessageBroker,
            MessageEnvelope
        )
        
        broker = InMemoryMessageBroker()
        
        message = MessageEnvelope(
            message_id='msg-1',
            sender_name='agent1',
            receiver_names=['agent2'],
            message_type='task_request',
            payload={'data': 'test'}
        )
        
        broker.publish_message('test_channel', message)
        broker.clear_channel('test_channel')
        
        count = broker.get_message_count('test_channel')
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()
