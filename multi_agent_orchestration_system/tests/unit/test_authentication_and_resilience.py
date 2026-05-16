"""
Unit Tests - Authentication and Resilience
==========================================

Tests for JWT authentication, RBAC, circuit breaker, and resilience patterns.
"""

import unittest
from datetime import datetime, timedelta

try:
    from multi_agent_orchestration_system.infrastructure_layer.authentication import (
        JWTAuthenticationService,
        RoleBasedAccessControl,
        RateLimitMiddleware,
        AuthenticationConfiguration,
        UserAccount,
        UserRole,
        Permission,
        ROLE_PERMISSIONS,
        get_default_admin_user
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

try:
    from multi_agent_orchestration_system.infrastructure_layer.resilience import (
        CircuitBreaker,
        CircuitBreakerConfiguration,
        CircuitBreakerOpenError,
        DeadLetterQueueHandler,
        RetryPolicy,
        BulkheadIsolation,
        CircuitState
    )
    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False


class TestUserAccount(unittest.TestCase):
    """Test user account model"""
    
    def test_user_creation(self):
        """Test user account creation"""
        user = UserAccount(username="testuser", role=UserRole.DEVELOPER)
        
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, UserRole.DEVELOPER)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
    
    def test_permission_checking(self):
        """Test permission checking"""
        user = UserAccount(
            username="testuser",
            role=UserRole.VIEWER,
            permissions={Permission.TASK_CREATE}
        )
        
        self.assertTrue(user.has_permission(Permission.TASK_READ))
        self.assertTrue(user.has_permission(Permission.TASK_CREATE))
        self.assertFalse(user.has_permission(Permission.AGENT_DELETE))
    
    def test_superuser_permissions(self):
        """Test superuser has all permissions"""
        user = UserAccount(
            username="admin",
            role=UserRole.GUEST,
            is_superuser=True
        )
        
        self.assertTrue(user.has_permission(Permission.ADMIN_MANAGE_USERS))
        self.assertTrue(user.has_permission(Permission.AGENT_DELETE))


class TestRolePermissions(unittest.TestCase):
    """Test role-based permissions"""
    
    def test_admin_permissions(self):
        """Test admin has all permissions"""
        admin = UserAccount(username="admin", role=UserRole.ADMIN)
        
        self.assertTrue(admin.has_all_permissions(list(Permission)))
    
    def test_viewer_limited_permissions(self):
        """Test viewer has limited permissions"""
        viewer = UserAccount(username="viewer", role=UserRole.VIEWER)
        
        self.assertTrue(viewer.has_permission(Permission.AGENT_READ))
        self.assertFalse(viewer.has_permission(Permission.AGENT_DELETE))
        self.assertFalse(viewer.has_permission(Permission.TASK_DELETE))


class TestJWTAuthentication(unittest.TestCase):
    """Test JWT authentication service"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class fixtures"""
        if not AUTH_AVAILABLE:
            raise unittest.SkipTest("JWT library not available")
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = AuthenticationConfiguration(
            jwt_secret_key="test-secret-key",
            access_token_expire_minutes=30
        )
        self.auth_service = JWTAuthenticationService(self.config)
        self.admin = get_default_admin_user()
    
    def test_create_access_token(self):
        """Test access token creation"""
        token = self.auth_service.create_access_token(self.admin)
        
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 50)
    
    def test_verify_valid_token(self):
        """Test verifying valid token"""
        if not AUTH_AVAILABLE:
            self.skipTest("JWT library not available")
        
        token = self.auth_service.create_access_token(self.admin)
        payload = self.auth_service.verify_token(token)
        
        self.assertIsNotNone(payload)
        self.assertEqual(payload.username, "admin")
        self.assertEqual(payload.role, "admin")
    
    def test_revoke_token(self):
        """Test token revocation"""
        if not AUTH_AVAILABLE:
            self.skipTest("JWT library not available")
        
        token = self.auth_service.create_access_token(self.admin)
        self.auth_service.revoke_token(token)
        
        payload = self.auth_service.verify_token(token)
        self.assertIsNone(payload)


class TestRoleBasedAccessControl(unittest.TestCase):
    """Test RBAC service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rbac = RoleBasedAccessControl()
        self.admin = get_default_admin_user()
        self.viewer = UserAccount(username="viewer", role=UserRole.VIEWER)
    
    def test_permission_check(self):
        """Test permission checking"""
        self.assertTrue(
            self.rbac.check_permission(self.admin, Permission.AGENT_CREATE)
        )
        self.assertFalse(
            self.rbac.check_permission(self.viewer, Permission.AGENT_DELETE)
        )
    
    def test_grant_permission(self):
        """Test granting permission"""
        self.rbac.grant_permission(self.viewer, Permission.TASK_CREATE)
        
        self.assertTrue(self.viewer.has_permission(Permission.TASK_CREATE))
    
    def test_revoke_permission(self):
        """Test revoking permission"""
        user = UserAccount(
            username="dev",
            role=UserRole.DEVELOPER,
            permissions={Permission.TASK_DELETE}
        )
        self.rbac.revoke_permission(user, Permission.TASK_DELETE)
        
        self.assertFalse(user.has_permission(Permission.TASK_DELETE))
    
    def test_get_user_permissions(self):
        """Test getting user permissions"""
        permissions = self.rbac.get_user_permissions(self.viewer)
        
        self.assertIn(Permission.AGENT_READ, permissions)
        self.assertNotIn(Permission.AGENT_DELETE, permissions)


class TestRateLimitMiddleware(unittest.TestCase):
    """Test rate limiting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.limiter = RateLimitMiddleware(requests_per_minute=10, burst_size=3)
    
    def test_rate_limit_allows_requests(self):
        """Test rate limit allows requests within limit"""
        for i in range(3):
            self.assertTrue(self.limiter.check_rate_limit("user1"))
    
    def test_rate_limit_per_user(self):
        """Test rate limit is per user"""
        for i in range(3):
            self.assertTrue(self.limiter.check_rate_limit("user_a"))
        
        for i in range(3):
            self.assertTrue(self.limiter.check_rate_limit("user_b"))
    
    def test_rate_limit_blocks_excess(self):
        """Test rate limit blocks excess requests"""
        for i in range(10):
            self.limiter.check_rate_limit("user2")
        
        self.assertFalse(self.limiter.check_rate_limit("user2"))
    
    def test_rate_limit_burst(self):
        """Test rate limit burst allowance"""
        for i in range(3):
            self.assertTrue(self.limiter.check_rate_limit("user3"))
        
        self.assertFalse(self.limiter.check_rate_limit("user3"))
    
    def test_get_remaining_requests(self):
        """Test getting remaining requests"""
        self.limiter.check_rate_limit("user4")
        self.limiter.check_rate_limit("user4")
        
        remaining = self.limiter.get_remaining_requests("user4")
        self.assertEqual(remaining, 8)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CircuitBreakerConfiguration(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0
        )
        self.circuit = CircuitBreaker("test-service", self.config)
    
    def test_circuit_starts_closed(self):
        """Test circuit starts in closed state"""
        self.assertEqual(self.circuit.state, CircuitState.CLOSED)
    
    def test_circuit_records_success(self):
        """Test circuit records successful calls"""
        with self.circuit:
            pass
        
        self.assertEqual(self.circuit.state, CircuitState.CLOSED)
    
    def test_circuit_opens_after_failures(self):
        """Test circuit opens after threshold failures"""
        for i in range(3):
            try:
                with self.circuit:
                    raise ConnectionError("Connection failed")
            except ConnectionError:
                pass
        
        self.assertEqual(self.circuit.state, CircuitState.OPEN)
    
    def test_circuit_rejects_when_open(self):
        """Test circuit rejects calls when open"""
        for i in range(3):
            try:
                with self.circuit:
                    raise ConnectionError("Connection failed")
            except ConnectionError:
                pass
        
        with self.assertRaises(CircuitBreakerOpenError):
            with self.circuit:
                pass
    
    def test_circuit_statistics(self):
        """Test circuit statistics"""
        stats = self.circuit.get_statistics()
        
        self.assertIn('name', stats)
        self.assertIn('state', stats)
        self.assertIn('total_calls', stats)
    
    def test_circuit_reset(self):
        """Test circuit manual reset"""
        for i in range(3):
            try:
                with self.circuit:
                    raise ConnectionError("Failed")
            except ConnectionError:
                pass
        
        self.circuit.reset()
        
        self.assertEqual(self.circuit.state, CircuitState.CLOSED)
        self.assertEqual(self.circuit._failure_count, 0)


class TestDeadLetterQueue(unittest.TestCase):
    """Test dead letter queue"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dlq = DeadLetterQueueHandler(max_retries=3)
    
    def test_add_failed_task(self):
        """Test adding failed task to DLQ"""
        task = self.dlq.add_failed_task(
            task_id="task-1",
            task_name="Process Order",
            payload={"order_id": 123},
            error_message="Timeout"
        )
        
        self.assertEqual(self.dlq.get_queue_size(), 1)
        self.assertEqual(task.task_id, "task-1")
        self.assertEqual(task.current_attempt, 0)
    
    def test_should_retry(self):
        """Test retry decision"""
        task = self.dlq.add_failed_task(
            task_id="task-1",
            task_name="Process Order",
            payload={"order_id": 123},
            error_message="Timeout"
        )
        
        self.assertTrue(self.dlq.should_retry(task))
    
    def test_max_retries_exceeded(self):
        """Test max retries exceeded"""
        task = self.dlq.add_failed_task(
            task_id="task-1",
            task_name="Process Order",
            payload={"order_id": 123},
            error_message="Timeout"
        )
        
        task.current_attempt = 3
        
        self.assertFalse(self.dlq.should_retry(task))
    
    def test_remove_task(self):
        """Test removing task from DLQ"""
        task = self.dlq.add_failed_task(
            task_id="task-1",
            task_name="Process Order",
            payload={"order_id": 123},
            error_message="Timeout"
        )
        
        result = self.dlq.remove_task("task-1")
        
        self.assertTrue(result)
        self.assertEqual(self.dlq.get_queue_size(), 0)
    
    def test_resurrect_task(self):
        """Test resurrecting task"""
        task = self.dlq.add_failed_task(
            task_id="task-1",
            task_name="Process Order",
            payload={"order_id": 123},
            error_message="Timeout"
        )
        
        resurrected = self.dlq.resurrect_task("task-1")
        
        self.assertIsNotNone(resurrected)
        self.assertEqual(self.dlq.get_queue_size(), 0)
        self.assertTrue(resurrected.metadata.get('resurrected'))
    
    def test_get_statistics(self):
        """Test DLQ statistics"""
        self.dlq.add_failed_task("task-1", "Task 1", {}, "Error 1")
        self.dlq.add_failed_task("task-2", "Task 2", {}, "Error 2")
        
        stats = self.dlq.get_statistics()
        
        self.assertEqual(stats['total_tasks'], 2)
        self.assertIn('ready_for_retry', stats)


class TestRetryPolicy(unittest.TestCase):
    """Test retry policy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.retry = RetryPolicy(
            max_attempts=3,
            base_delay=0.01,
            max_delay=0.1
        )
    
    def test_should_retry_within_attempts(self):
        """Test should retry within attempt limit"""
        self.assertTrue(
            self.retry.should_retry(Exception("Error"), attempt=1)
        )
        self.assertTrue(
            self.retry.should_retry(Exception("Error"), attempt=2)
        )
    
    def test_should_not_retry_exceeded(self):
        """Test should not retry when exceeded"""
        self.assertFalse(
            self.retry.should_retry(Exception("Error"), attempt=3)
        )
    
    def test_get_delay(self):
        """Test retry delay calculation"""
        delay1 = self.retry.get_delay(1)
        delay2 = self.retry.get_delay(2)
        
        self.assertGreater(delay2, delay1)
        self.assertLessEqual(delay2, self.retry.max_delay)


class TestBulkheadIsolation(unittest.TestCase):
    """Test bulkhead isolation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bulkhead = BulkheadIsolation(max_concurrent=2)
    
    def test_acquire_release(self):
        """Test acquire and release"""
        with self.bulkhead:
            stats = self.bulkhead.get_stats()
            self.assertEqual(stats['active_count'], 1)
        
        stats = self.bulkhead.get_stats()
        self.assertEqual(stats['active_count'], 0)
    
    def test_max_concurrent(self):
        """Test max concurrent limit"""
        with self.bulkhead:
            with self.bulkhead:
                with self.assertRaises(RuntimeError):
                    with self.bulkhead:
                        pass
    
    def test_statistics(self):
        """Test bulkhead statistics"""
        stats = self.bulkhead.get_stats()
        
        self.assertIn('max_concurrent', stats)
        self.assertIn('active_count', stats)
        self.assertIn('available', stats)


if __name__ == '__main__':
    unittest.main()
