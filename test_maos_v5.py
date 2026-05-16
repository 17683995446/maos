"""
MAOS v5.0 - 完整的测试套件
包含单元测试、集成测试和性能基准测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass

import pytest


# 测试结果数据类
@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    duration: float
    error: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class MAOSTestSuite:
    """MAOS 测试套件"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def run_test(self, name: str, test_func, is_async: bool = False) -> TestResult:
        """运行单个测试"""
        start = time.time()
        error = ""
        passed = True
        
        try:
            if is_async:
                asyncio.run(test_func())
            else:
                test_func()
        except Exception as e:
            passed = False
            error = str(e)
            import traceback
            error += "\n" + traceback.format_exc()
        
        duration = time.time() - start
        result = TestResult(
            name=name,
            passed=passed,
            duration=duration,
            error=error
        )
        self.results.append(result)
        return result
    
    def print_summary(self) -> None:
        """打印测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_duration = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("MAOS v5.0 - Test Suite Results".center(80))
        print("=" * 80)
        print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed} | Duration: {total_duration:.2f}s")
        print("-" * 80)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.name} ({result.duration:.3f}s)")
            if not result.passed:
                print(f"   Error: {result.error[:200]}...")
        
        print("-" * 80)
        print(f"Overall: {'✅ All tests passed' if failed == 0 else '❌ Some tests failed'}")
        print("=" * 80 + "\n")
        
        return failed == 0


# 实际测试函数
def test_config_system() -> None:
    """测试配置系统"""
    from maos.config import MAOSConfig, get_config, set_config
    
    # 测试默认配置
    config = MAOSConfig()
    assert config.system_name == "MAOS"
    assert config.system_version == "5.0.0"
    assert config.debug is False
    
    # 测试配置转换
    config_dict = config.to_dict()
    assert "system_name" in config_dict
    assert "max_concurrent_tasks" in config_dict
    
    # 测试全局配置
    config2 = MAOSConfig(debug=True)
    set_config(config2)
    retrieved = get_config()
    assert retrieved.debug is True


def test_performance_decorators() -> None:
    """测试性能装饰器"""
    from maos.performance import (
        timed,
        retry,
        get_performance_metrics,
        get_all_performance_metrics,
        print_performance_summary
    )
    
    # 测试timed装饰器
    @timed(log_duration=False, record_metrics=False)
    def test_function(x: int) -> int:
        time.sleep(0.01)
        return x * 2
    
    result = test_function(5)
    assert result == 10
    
    metrics = get_performance_metrics("test_function")
    assert metrics is not None
    assert metrics.call_count == 1
    
    # 测试retry装饰器
    attempt_count = 0
    
    @retry(max_attempts=3, delay=0.01)
    def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ValueError("Temporary error")
        return "success"
    
    result = flaky_function()
    assert result == "success"
    assert attempt_count == 2


def test_core_agent() -> None:
    """测试核心Agent"""
    from maos.core import Agent, AgentMessage, AgentStatus, MessageType
    
    class SimpleAgent(Agent):
        def __init__(self):
            super().__init__("test-agent", capabilities=["basic"])
        
        async def process_request(self, input_text, user_id, session_id, chat_history=None, **kwargs):
            yield f"Processed: {input_text}"
    
    agent = SimpleAgent()
    assert agent.agent_id == "test-agent"
    assert "basic" in agent.capabilities


def test_storage() -> None:
    """测试存储系统"""
    from maos.storage import InMemoryChatStorage, ChatStorageConfig
    from maos.types import ConversationMessage
    
    config = ChatStorageConfig(ttl_seconds=3600)
    storage = InMemoryChatStorage(config)
    
    # 测试存储消息
    message = ConversationMessage(
        role="user",
        content="Hello"
    )
    storage.add_message("session-1", message)
    
    # 测试获取消息
    messages = storage.get_messages("session-1")
    assert len(messages) == 1
    assert messages[0].content == "Hello"


def test_analytics() -> None:
    """测试分析系统"""
    from maos.analytics import AnalyticsEngine, CostAttributionEngine
    
    analytics = AnalyticsEngine()
    analytics.record_metric("test.metric", 42.0, {"tag": "test"})
    
    summary = analytics.get_summary()
    assert "test.metric" in summary


def test_multi_tenancy() -> None:
    """测试多租户"""
    from maos.multi_tenancy import TenantManagementService, Tenant
    
    service = TenantManagementService()
    tenant = Tenant(
        id="tenant-1",
        name="Test Tenant",
        isolation_strategy="SHARED_ROW"
    )
    service.register_tenant(tenant)
    
    retrieved = service.get_tenant("tenant-1")
    assert retrieved is not None
    assert retrieved.name == "Test Tenant"


def test_orchestration() -> None:
    """测试编排系统"""
    from maos.orchestration import TaskManager, Task, TaskPriority, TaskStatus
    
    manager = TaskManager()
    
    task = manager.create_task(
        name="Test Task",
        description="Test Task Description",
        priority=TaskPriority.NORMAL,
        requirements=[]
    )
    
    pending = manager.get_pending_tasks()
    assert len(pending) > 0


# 性能基准测试
def benchmark_task_throughput() -> Dict[str, Any]:
    """任务吞吐量基准测试"""
    from maos.orchestration import TaskManager, TaskPriority
    
    manager = TaskManager()
    start = time.time()
    
    # 提交100个任务
    for i in range(100):
        manager.create_task(
            name=f"Benchmark Task {i}",
            description=f"Benchmark Task {i}",
            priority=TaskPriority.LOW,
            requirements=[]
        )
    
    duration = time.time() - start
    throughput = 100 / duration if duration > 0 else 0
    
    return {
        "tasks": 100,
        "duration": duration,
        "throughput": throughput
    }


# 主测试运行器
def run_all_tests() -> bool:
    """运行所有测试"""
    print("🚀 MAOS v5.0 - Starting Comprehensive Test Suite...\n")
    
    suite = MAOSTestSuite()
    
    # 单元测试
    suite.run_test("Configuration System", test_config_system)
    suite.run_test("Performance Decorators", test_performance_decorators)
    suite.run_test("Core Agent System", test_core_agent)
    suite.run_test("Storage System", test_storage)
    suite.run_test("Analytics Engine", test_analytics)
    suite.run_test("Multi-Tenancy", test_multi_tenancy)
    suite.run_test("Orchestration", test_orchestration)
    
    # 基准测试
    print("\n📊 Running Performance Benchmarks...")
    benchmark_result = benchmark_task_throughput()
    print(f"   Task Throughput: {benchmark_result['throughput']:.2f} tasks/s")
    
    # 打印性能摘要
    from maos.performance import print_performance_summary
    print_performance_summary()
    
    # 打印测试摘要
    return suite.print_summary()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
