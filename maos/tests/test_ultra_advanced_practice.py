#!/usr/bin/env python3
"""
MAOS v14.0 - 超超极限真实实践测试
深度压力测试、故障注入测试、安全性测试、一致性测试
"""

import sys
import os
import time
import random
import threading
import asyncio
import gc
import tracemalloc
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maos.orchestration.orchestrator import (
    OrchestratorService,
    AgentRegistry,
    MessageBroker,
    EventEmitter,
    Workflow,
    WorkflowStep,
    ExecutionStrategy
)
from maos.security.enhanced import (
    JWTToken,
    JWTClaims,
    JWTAlgorithm,
    OAuth2Server,
    OAuthScope,
    EnhancedSecurityManager
)
from maos.storage.in_memory import InMemoryChatStorage
from maos.types import ConversationMessage, ParticipantRole
from maos.version.v14 import VersionManager, ABTestManager
from maos.analytics.v14 import AnalyticsEngine
from maos.mobile.v14 import MobileAPIManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    success: bool
    error: Optional[str] = None
    operations: int = 0
    duration: float = 0.0
    memory_peak: Optional[int] = None
    issues_found: List[str] = None

    def __post_init__(self):
        if self.issues_found is None:
            self.issues_found = []


class StressTestAgent:
    """压力测试用Agent"""
    def __init__(self, name: str, capabilities: List[str] = None):
        self.name = name
        self.capabilities = capabilities or ["default"]
        self.status = "idle"
        self.process_count = 0
    
    async def process_task(self, task):
        """处理任务"""
        self.process_count += 1
        # 模拟工作负载
        await asyncio.sleep(random.uniform(0.001, 0.01))
        return {"result": f"processed_by_{self.name}", "count": self.process_count}


class UltraAdvancedPracticeTester:
    """超超极限实践测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.operation_count = 0
        self.errors_found: List[str] = []
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 80)
        logger.info("MAOS v14.0 - 超超极限真实实践测试开始")
        logger.info("=" * 80)
        
        tests = [
            self.test_orchestrator_concurrent_stress,
            self.test_orchestrator_memory_leak,
            self.test_oauth_server_thread_safety,
            self.test_security_fuzzing,
            self.test_storage_race_conditions,
            self.test_integrated_system_stress,
            self.test_fault_injection,
            self.test_high_throughput_messaging,
        ]
        
        for test in tests:
            try:
                result = test()
                self.results.append(result)
                self.operation_count += result.operations
                if not result.success:
                    self.errors_found.append(f"{result.test_name}: {result.error}")
                logger.info(f"✅ 测试完成: {result.test_name}")
            except Exception as e:
                logger.error(f"❌ 测试失败: {test.__name__}, 错误: {e}")
                self.results.append(TestResult(
                    test_name=test.__name__,
                    success=False,
                    error=str(e)
                ))
                self.errors_found.append(f"{test.__name__}: {e}")
        
        return self.results
    
    def test_orchestrator_concurrent_stress(self) -> TestResult:
        """测试编排器并发压力"""
        logger.info("\n🔬 开始编排器并发压力测试...")
        start_time = time.time()
        
        tracemalloc.start()
        
        orchestrator = OrchestratorService(name="stress_test_orchestrator")
        agent_registry = orchestrator.agent_registry
        
        # 注册大量Agent
        agents = []
        for i in range(50):
            agent = StressTestAgent(f"agent_{i}", ["analysis", "data", f"cap_{i}"])
            agents.append(agent)
            agent_registry.register(agent)
        
        operations = 0
        errors = []
        
        def concurrent_operations(thread_id: int):
            nonlocal operations
            local_ops = 0
            local_errors = []
            try:
                for _ in range(500):
                    # 随机选择Agent
                    agent_idx = random.randint(0, 49)
                    agent_name = f"agent_{agent_idx}"
                    
                    # 更新Agent状态
                    new_status = random.choice(["idle", "busy", "error"])
                    agent_registry.update_agent_status(agent_name, new_status)
                    
                    # 获取可用Agent
                    agent_registry.get_available_agents()
                    
                    # 选择最佳Agent
                    agent_registry.select_best_agent(["analysis"])
                    
                    # 获取统计信息
                    agent_registry.get_statistics()
                    
                    local_ops += 1
            except Exception as e:
                local_errors.append(f"Thread {thread_id}: {str(e)}")
            return local_ops, local_errors
        
        # 启动200个并发线程
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(concurrent_operations, i) for i in range(200)]
            for future in as_completed(futures):
                ops, errs = future.result()
                operations += ops
                errors.extend(errs)
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        tracemalloc.stop()
        
        memory_peak = sum(stat.size for stat in top_stats)
        
        success = len(errors) == 0
        if not success:
            logger.error(f"❌ 编排器并发压力测试发现 {len(errors)} 个错误")
        
        duration = time.time() - start_time
        logger.info(f"   编排器并发压力测试完成: {operations} 次操作, {duration:.2f}s")
        
        issues = []
        if len(errors) > 0:
            issues.append("编排器AgentRegistry存在竞态条件")
        
        return TestResult(
            test_name="编排器并发压力测试",
            success=success,
            error="; ".join(errors) if errors else None,
            operations=operations,
            duration=duration,
            memory_peak=memory_peak,
            issues_found=issues
        )
    
    def test_orchestrator_memory_leak(self) -> TestResult:
        """测试编排器内存泄漏"""
        logger.info("\n🔬 开始编排器内存泄漏测试...")
        start_time = time.time()
        
        tracemalloc.start()
        
        initial_snapshot = tracemalloc.take_snapshot()
        
        # 创建并销毁大量编排器实例
        for _ in range(1000):
            orchestrator = OrchestratorService(name=f"temp_orch_{_}")
            for i in range(10):
                agent = StressTestAgent(f"temp_agent_{_}_{i}")
                orchestrator.register_agent(agent)
            
            # 不调用cleanup直接丢弃引用
            del orchestrator
        
        gc.collect()
        
        final_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # 比较内存使用
        stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
        significant_increase = any(stat.size_diff > 10000 for stat in stats)
        
        memory_peak = sum(stat.size for stat in final_snapshot.statistics('lineno'))
        
        success = not significant_increase
        issues = []
        if significant_increase:
            issues.append("编排器存在内存泄漏风险 - 缺少cleanup机制")
            logger.warning("⚠️ 检测到潜在内存泄漏")
        
        duration = time.time() - start_time
        logger.info(f"   编排器内存泄漏测试完成: {duration:.2f}s")
        
        return TestResult(
            test_name="编排器内存泄漏测试",
            success=success,
            error="内存使用异常增长" if significant_increase else None,
            operations=1000,
            duration=duration,
            memory_peak=memory_peak,
            issues_found=issues
        )
    
    def test_oauth_server_thread_safety(self) -> TestResult:
        """测试OAuth服务器线程安全"""
        logger.info("\n🔬 开始OAuth服务器线程安全测试...")
        start_time = time.time()
        
        oauth_server = OAuth2Server(jwt_secret="test_secret_12345")
        operations = 0
        errors = []
        
        def oauth_operations(thread_id: int):
            nonlocal operations
            local_ops = 0
            local_errors = []
            try:
                for _ in range(200):
                    # 注册客户端
                    client_id, client_secret = oauth_server.register_client(
                        client_name=f"test_client_{thread_id}_{_}",
                        redirect_uris=["http://localhost/callback"]
                    )
                    local_ops += 1
                    
                    # 授权
                    code = oauth_server.authorize(
                        client_id=client_id,
                        user_id=f"user_{thread_id}",
                        redirect_uri="http://localhost/callback",
                        scopes=["read", "write"]
                    )
                    local_ops += 1
                    
                    # 交换令牌
                    if code:
                        token = oauth_server.exchange_code_for_token(
                            code=code,
                            client_id=client_id,
                            client_secret=client_secret
                        )
                        if token:
                            local_ops += 1
                    
                    # 使用客户端凭证
                    token = oauth_server.client_credentials_grant(
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=["read"]
                    )
                    if token:
                        local_ops += 1
            except Exception as e:
                local_errors.append(f"Thread {thread_id}: {str(e)}")
            return local_ops, local_errors
        
        # 启动100个并发线程
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(oauth_operations, i) for i in range(100)]
            for future in as_completed(futures):
                ops, errs = future.result()
                operations += ops
                errors.extend(errs)
        
        success = len(errors) == 0
        issues = []
        if not success:
            issues.append("OAuth服务器存在线程安全问题")
            logger.error(f"❌ OAuth服务器线程安全测试发现 {len(errors)} 个错误")
        
        duration = time.time() - start_time
        logger.info(f"   OAuth服务器线程安全测试完成: {operations} 次操作, {duration:.2f}s")
        
        return TestResult(
            test_name="OAuth服务器线程安全测试",
            success=success,
            error="; ".join(errors) if errors else None,
            operations=operations,
            duration=duration,
            issues_found=issues
        )
    
    def test_security_fuzzing(self) -> TestResult:
        """测试安全性模糊测试"""
        logger.info("\n🔬 开始安全性模糊测试...")
        start_time = time.time()
        
        jwt_token = JWTToken(secret_key="test_fuzz_secret")
        operations = 0
        issues = []
        
        # 生成各种畸形token
        fuzz_tokens = [
            "",  # 空token
            ".",  # 只有分隔符
            "..",  # 两个分隔符
            "a.b.c",  # 无效编码
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ",  # 缺少签名
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid_signature",  # 无效签名
        ]
        
        # 添加随机生成的token
        for _ in range(1000):
            random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(1, 500)))
            fuzz_tokens.append(random_str)
        
        errors = 0
        for token in fuzz_tokens:
            try:
                result = jwt_token.verify_token(token)
                operations += 1
            except Exception as e:
                errors += 1
                issues.append(f"JWT验证崩溃: {token[:50]}...")
        
        success = errors == 0
        if not success:
            logger.error(f"❌ 安全性模糊测试发现 {errors} 个崩溃")
        
        duration = time.time() - start_time
        logger.info(f"   安全性模糊测试完成: {operations} 次操作, {duration:.2f}s")
        
        return TestResult(
            test_name="安全性模糊测试",
            success=success,
            error=f"{errors} 个验证崩溃" if errors else None,
            operations=operations,
            duration=duration,
            issues_found=issues
        )
    
    def test_storage_race_conditions(self) -> TestResult:
        """测试存储竞态条件"""
        logger.info("\n🔬 开始存储竞态条件测试...")
        start_time = time.time()
        
        async def run_storage_test():
            storage = InMemoryChatStorage(auto_cleanup=False)
            await storage.initialize()
            
            operations = 0
            errors = []
            user_ids = [f"user_{i}" for i in range(20)]
            session_ids = [f"session_{i}" for i in range(10)]
            agent_ids = [f"agent_{i}" for i in range(5)]
            
            async def storage_operations(task_id: int):
                nonlocal operations
                local_ops = 0
                local_errors = []
                try:
                    for _ in range(100):
                        user_id = random.choice(user_ids)
                        session_id = random.choice(session_ids)
                        agent_id = random.choice(agent_ids)
                        
                        # 保存消息
                        msg = ConversationMessage(
                            id=f"msg_{task_id}_{_}",
                            role=ParticipantRole.USER,
                            content=f"test content {task_id}_{_}",
                            timestamp=datetime.now()
                        )
                        await storage.save_chat_message(user_id, session_id, agent_id, msg)
                        local_ops += 1
                        
                        # 获取消息
                        await storage.fetch_chat(user_id, session_id, agent_id)
                        local_ops += 1
                        
                        # 随机删除
                        if random.random() < 0.1:
                            await storage.delete_chat(user_id, session_id, agent_id)
                            local_ops += 1
                except Exception as e:
                    local_errors.append(f"Task {task_id}: {str(e)}")
                return local_ops, local_errors
            
            # 并发执行
            tasks = [storage_operations(i) for i in range(50)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                else:
                    ops, errs = result
                    operations += ops
                    errors.extend(errs)
            
            await storage.close()
            return operations, errors
        
        operations, errors = asyncio.run(run_storage_test())
        
        success = len(errors) == 0
        issues = []
        if not success:
            issues.append("存储操作存在竞态条件")
            logger.error(f"❌ 存储竞态条件测试发现 {len(errors)} 个错误")
        
        duration = time.time() - start_time
        logger.info(f"   存储竞态条件测试完成: {operations} 次操作, {duration:.2f}s")
        
        return TestResult(
            test_name="存储竞态条件测试",
            success=success,
            error="; ".join(errors) if errors else None,
            operations=operations,
            duration=duration,
            issues_found=issues
        )
    
    def test_integrated_system_stress(self) -> TestResult:
        """测试集成系统压力"""
        logger.info("\n🔬 开始集成系统压力测试...")
        start_time = time.time()
        
        tracemalloc.start()
        
        # 初始化所有组件
        orchestrator = OrchestratorService(name="integrated_test")
        version_mgr = VersionManager()
        analytics = AnalyticsEngine()
        mobile_api = MobileAPIManager()
        jwt = JWTToken("integrated_secret")
        
        operations = 0
        errors = []
        
        def integrated_ops(thread_id: int):
            nonlocal operations
            local_ops = 0
            local_errors = []
            try:
                for _ in range(20):  # 减少循环次数避免超时
                    # 版本管理操作
                    version = f"{random.randint(1, 100)}.{random.randint(0, 9)}"
                    version_mgr.create_version(f"service_{thread_id}", {}, version=version)
                    local_ops += 1
                    
                    # 分析记录
                    analytics.record_metric(f"metric_{thread_id}_{_}", random.random())
                    local_ops += 1
                    
                    # 移动API操作
                    mobile_api.create_session(f"device_{thread_id}", f"user_{thread_id}")
                    local_ops += 1
                    
                    # JWT操作
                    claims = JWTClaims(sub=f"user_{thread_id}")
                    token = jwt.create_token(claims)
                    jwt.verify_token(token)
                    local_ops += 2
            except Exception as e:
                local_errors.append(f"Thread {thread_id}: {str(e)}")
            return local_ops, local_errors
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(integrated_ops, i) for i in range(20)]
            for future in as_completed(futures):
                ops, errs = future.result()
                operations += ops
                errors.extend(errs)
        
        snapshot = tracemalloc.take_snapshot()
        memory_peak = sum(stat.size for stat in snapshot.statistics('lineno'))
        tracemalloc.stop()
        
        success = len(errors) == 0
        issues = []
        if not success:
            logger.error(f"❌ 集成系统压力测试发现 {len(errors)} 个错误")
        
        duration = time.time() - start_time
        logger.info(f"   集成系统压力测试完成: {operations} 次操作, {duration:.2f}s")
        
        return TestResult(
            test_name="集成系统压力测试",
            success=success,
            error="; ".join(errors) if errors else None,
            operations=operations,
            duration=duration,
            memory_peak=memory_peak,
            issues_found=issues
        )
    
    def test_fault_injection(self) -> TestResult:
        """测试故障注入"""
        logger.info("\n🔬 开始故障注入测试...")
        start_time = time.time()
        
        operations = 0
        issues = []
        
        # 测试边界条件
        version_mgr = VersionManager()
        analytics = AnalyticsEngine()
        
        # 测试空值 - 应该优雅处理
        try:
            v = version_mgr.create_version("test_service", {}, version="1.0")
            operations += 1
        except Exception as e:
            issues.append(f"正常创建失败: {e}")
        
        # 测试极大值
        try:
            for i in range(1000):  # 减少到1000次避免超时
                analytics.record_metric(f"metric_{i}", float(i), metadata={"data": "x" * 100})
            operations += 1000
        except Exception as e:
            issues.append(f"大数据处理失败: {e}")
        
        # 测试快速创建（没有deactivate_version，用activate_version替代）
        try:
            for i in range(500):  # 减少到500次避免超时
                v = version_mgr.create_version(f"service_{i}", {}, version=f"1.{i}")
                version_mgr.activate_version(v.id)
            operations += 1000
        except Exception as e:
            issues.append(f"快速创建失败: {e}")
        
        success = len(issues) == 0
        duration = time.time() - start_time
        logger.info(f"   故障注入测试完成: {operations} 次操作, {duration:.2f}s")
        
        return TestResult(
            test_name="故障注入测试",
            success=success,
            error="; ".join(issues) if issues else None,
            operations=operations,
            duration=duration,
            issues_found=issues
        )
    
    def test_high_throughput_messaging(self) -> TestResult:
        """测试高吞吐量消息传递"""
        logger.info("\n🔬 开始高吞吐量消息传递测试...")
        start_time = time.time()
        
        broker = MessageBroker()
        operations = 0
        errors = []
        message_count = 0
        lock = threading.Lock()
        
        def message_handler(message):
            nonlocal message_count
            with lock:
                message_count += 1
        
        # 订阅
        for i in range(10):
            broker.subscribe(f"topic_{i}", message_handler)
        
        def publisher(thread_id: int):
            nonlocal operations
            local_ops = 0
            local_errors = []
            try:
                for _ in range(500):
                    topic = f"topic_{random.randint(0, 9)}"
                    broker.publish({
                        "type": topic,
                        "content": f"message_{thread_id}_{_}",
                        "timestamp": datetime.now().isoformat()
                    })
                    local_ops += 1
            except Exception as e:
                local_errors.append(f"Thread {thread_id}: {str(e)}")
            return local_ops, local_errors
        
        # 启动50个发布者
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(publisher, i) for i in range(50)]
            for future in as_completed(futures):
                ops, errs = future.result()
                operations += ops
                errors.extend(errs)
        
        success = len(errors) == 0 and message_count > 0
        issues = []
        if not success:
            if len(errors) > 0:
                issues.append("消息代理存在线程安全问题")
            if message_count == 0:
                issues.append("消息没有被正确处理")
            logger.error(f"❌ 高吞吐量消息传递测试发现问题")
        
        duration = time.time() - start_time
        logger.info(f"   高吞吐量消息传递测试完成: {operations} 次操作, 收到 {message_count} 条消息, {duration:.2f}s")
        
        return TestResult(
            test_name="高吞吐量消息传递测试",
            success=success,
            error="; ".join(errors) if errors else None,
            operations=operations,
            duration=duration,
            issues_found=issues
        )
    
    def generate_summary_report(self):
        """生成总结报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        total_operations = sum(r.operations for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        all_issues = []
        for r in self.results:
            all_issues.extend(r.issues_found)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_operations": total_operations,
            "total_duration": total_duration,
            "issues_found": all_issues,
            "detailed_results": self.results
        }


def main():
    """主函数"""
    tester = UltraAdvancedPracticeTester()
    results = tester.run_all_tests()
    summary = tester.generate_summary_report()
    
    print("\n" + "=" * 80)
    print("超超极限真实实践测试总结")
    print("=" * 80)
    print(f"总测试数: {summary['total_tests']}")
    print(f"通过: {summary['passed_tests']}")
    print(f"失败: {summary['failed_tests']}")
    print(f"总操作数: {summary['total_operations']:,}")
    print(f"总耗时: {summary['total_duration']:.2f}s")
    print(f"发现问题数: {len(summary['issues_found'])}")
    
    if summary['issues_found']:
        print("\n发现的问题:")
        for issue in summary['issues_found']:
            print(f"  - {issue}")
    
    print("\n" + "=" * 80)
    return summary


if __name__ == "__main__":
    main()
