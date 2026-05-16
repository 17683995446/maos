"""
MAOS v5.0 - 完整测试套件
单元测试和集成测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    duration: float
    error: str = ""


class TestSuite:
    """测试套件"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.total_time = 0
    
    def add_result(self, result: TestResult):
        """添加结果"""
        self.results.append(result)
    
    def print_summary(self):
        """打印摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "=" * 80)
        print("  MAOS v5.0 - Test Suite Results")
        print("=" * 80)
        print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ❌ {r.name}")
                    if r.error:
                        print(f"     {r.error[:100]}")
        
        print("\n" + "=" * 80)
        return failed == 0


async def test_core_modules():
    """测试核心模块"""
    suite = TestSuite()
    
    # Test 1: 配置系统
    print("\n📋 Testing Configuration System...")
    start = time.time()
    try:
        from maos.config import MAOSConfig, get_config
        config = MAOSConfig()
        assert config.system_name == "MAOS"
        suite.add_result(TestResult("Configuration", True, time.time() - start))
        print("   ✅ Configuration OK")
    except Exception as e:
        suite.add_result(TestResult("Configuration", False, time.time() - start, str(e)))
        print(f"   ❌ Configuration failed: {e}")
    
    # Test 2: LLM模块
    print("\n📋 Testing LLM Module...")
    start = time.time()
    try:
        from maos.llm import LLMClient, ChatMessage
        client = LLMClient()
        suite.add_result(TestResult("LLM Client", True, time.time() - start))
        print("   ✅ LLM Client OK")
    except Exception as e:
        suite.add_result(TestResult("LLM Client", False, time.time() - start, str(e)))
        print(f"   ❌ LLM Client failed: {e}")
    
    # Test 3: Orchestrator
    print("\n📋 Testing Orchestrator...")
    start = time.time()
    try:
        from maos.orchestration import OrchestratorService, TaskManager, TaskPriority
        manager = TaskManager()
        task = manager.create_task("Test Task", requirements=["test"], priority=TaskPriority.NORMAL)
        assert task.name == "Test Task"
        suite.add_result(TestResult("Orchestrator", True, time.time() - start))
        print("   ✅ Orchestrator OK")
    except Exception as e:
        suite.add_result(TestResult("Orchestrator", False, time.time() - start, str(e)))
        print(f"   ❌ Orchestrator failed: {e}")
    
    # Test 4: 监控系统
    print("\n📋 Testing Monitoring System...")
    start = time.time()
    try:
        from maos.monitoring import get_monitoring_system, get_logger
        monitor = get_monitoring_system()
        logger = get_logger("test")
        suite.add_result(TestResult("Monitoring", True, time.time() - start))
        print("   ✅ Monitoring OK")
    except Exception as e:
        suite.add_result(TestResult("Monitoring", False, time.time() - start, str(e)))
        print(f"   ❌ Monitoring failed: {e}")
    
    # Test 5: 安全模块
    print("\n📋 Testing Security Module...")
    start = time.time()
    try:
        from maos.security import get_auth
        auth = get_auth()
        key_id, full_key = auth.create_api_key("Test Key", ["read", "write"])
        assert key_id.startswith("mk_")
        suite.add_result(TestResult("Security", True, time.time() - start))
        print("   ✅ Security OK")
    except Exception as e:
        suite.add_result(TestResult("Security", False, time.time() - start, str(e)))
        print(f"   ❌ Security failed: {e}")
    
    # Test 6: 性能监控
    print("\n📋 Testing Performance Decorators...")
    start = time.time()
    try:
        from maos.performance import timed
        @timed(log_duration=False, record_metrics=False)
        def test_func():
            return 42
        
        result = test_func()
        assert result == 42
        suite.add_result(TestResult("Performance", True, time.time() - start))
        print("   ✅ Performance OK")
    except Exception as e:
        suite.add_result(TestResult("Performance", False, time.time() - start, str(e)))
        print(f"   ❌ Performance failed: {e}")
    
    return suite


async def test_integration():
    """集成测试"""
    suite = TestSuite()
    
    print("\n" + "=" * 80)
    print("  Integration Tests")
    print("=" * 80)
    
    # Test 1: 完整工作流
    print("\n📋 Testing Complete Workflow...")
    start = time.time()
    try:
        from maos.orchestration import OrchestratorService, TaskPriority
        from maos.monitoring import get_logger
        
        orchestrator = OrchestratorService(name="TestOrch")
        logger = get_logger("workflow.test")
        
        # 创建任务
        task1 = orchestrator.create_task(
            name="Task 1",
            requirements=["task1"],
            priority=TaskPriority.HIGH
        )
        
        task2 = orchestrator.create_task(
            name="Task 2",
            requirements=["task2"],
            priority=TaskPriority.NORMAL,
            dependencies=[task1.id]
        )
        
        # 记录日志
        logger.info("Workflow created", task_count=2)
        
        stats = orchestrator.get_statistics()
        assert stats['total'] == 2
        
        suite.add_result(TestResult("Complete Workflow", True, time.time() - start))
        print("   ✅ Complete Workflow OK")
    except Exception as e:
        suite.add_result(TestResult("Complete Workflow", False, time.time() - start, str(e)))
        print(f"   ❌ Complete Workflow failed: {e}")
    
    return suite


async def main():
    """运行所有测试"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║         MAOS v5.0 - Complete Test Suite                               ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    # 单元测试
    unit_suite = await test_core_modules()
    
    # 集成测试
    integration_suite = await test_integration()
    
    # 打印所有结果
    print("\n" + "=" * 80)
    print("  Overall Results")
    print("=" * 80)
    
    unit_suite.print_summary()
    integration_suite.print_summary()
    
    all_results = unit_suite.results + integration_suite.results
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    
    print(f"\n🎯 Total: {total} tests, {passed} passed, {total - passed} failed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())
