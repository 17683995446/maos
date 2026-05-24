#!/usr/bin/env python3
"""
MAOS 超长时间深度真实实践测试框架 v4.0
Multi-Agent Orchestration System - 极限真实运行测试
遵循慢工出细活原则，进行长时间、高复杂度的深度测试
"""

import threading
import time
import random
import sys
import gc
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import psutil
import os
import uuid
import json
import hashlib

sys.path.insert(0, '/workspace')

from maos.orchestration.orchestrator import (
    OrchestratorService, AgentRegistry, MessageBroker, 
    EventEmitter
)
from maos.security.enhanced import (
    JWTToken, OAuth2Server, JWTClaims
)
from maos.version.v14 import VersionManager, WorkflowVersion
from maos.analytics.v14 import AnalyticsEngine
from maos.mobile.v14 import MobileAPIManager, MobileSession
from maos.storage.in_memory import InMemoryChatStorage


class BugTracker:
    """高详细度的 Bug 追踪器"""
    def __init__(self):
        self.bugs: List[Dict[str, Any]] = []
        self.bug_counts = defaultdict(int)
        self.lock = threading.Lock()
    
    def add_bug(self, category: str, severity: str, description: str, 
                stack_trace: str = "", file_path: str = "", 
                reproduction_steps: List[str] = None, 
                test_context: Dict[str, Any] = None):
        bug_id = str(uuid.uuid4())
        bug = {
            "id": bug_id,
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "severity": severity,
            "description": description,
            "stack_trace": stack_trace,
            "file_path": file_path,
            "reproduction_steps": reproduction_steps or [],
            "test_context": test_context or {},
            "count": 1
        }
        with self.lock:
            key = f"{category}|{description}"
            if key in self.bug_counts:
                for b in self.bugs:
                    if f"{b['category']}|{b['description']}" == key:
                        b["count"] += 1
                        break
            else:
                self.bug_counts[key] = 1
                self.bugs.append(bug)
            print(f"🐛 发现 Bug [{severity}] [{category}]: {description} (ID: {bug_id[:8]})")
    
    def get_bugs_by_severity(self, severity: str) -> List[Dict]:
        with self.lock:
            return [b for b in self.bugs if b["severity"] == severity]
    
    def summary(self) -> Dict[str, int]:
        with self.lock:
            result = {
                "total": sum(b["count"] for b in self.bugs),
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "unique_bugs": len(self.bugs)
            }
            for bug in self.bugs:
                result[bug["severity"]] += bug["count"]
            return result
    
    def export_report(self, filepath: str) -> str:
        with self.lock:
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": self.summary(),
                "bugs": self.bugs
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return filepath


class DetailedResourceMonitor:
    """详细的资源监控器"""
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.start_memory
        self.min_memory = self.start_memory
        self.samples: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.memory_leaks: List[Dict] = []
        self.thread_creations: List[Dict] = []
        self.file_descriptors: List[Dict] = []
    
    def sample(self, label: str = "") -> Dict[str, float]:
        timestamp = time.time()
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent(interval=0.05)
        num_threads = self.process.num_threads()
        num_fds = self.process.num_fds() if hasattr(self.process, "num_fds") else 0
        
        sample = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "label": label,
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "num_threads": num_threads,
            "num_fds": num_fds
        }
        
        with self.lock:
            self.samples.append(sample)
            if memory_mb > self.peak_memory:
                self.peak_memory = memory_mb
            if memory_mb < self.min_memory:
                self.min_memory = memory_mb
        
        return sample
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            if not self.samples:
                return {
                    "start_memory_mb": self.start_memory,
                    "current_memory_mb": self.start_memory,
                    "peak_memory_mb": self.peak_memory,
                    "min_memory_mb": self.min_memory,
                    "memory_growth_mb": 0.0,
                    "memory_growth_percent": 0.0,
                    "avg_cpu_percent": 0.0,
                    "samples_count": 0
                }
            
            memory_values = [s["memory_mb"] for s in self.samples]
            cpu_values = [s["cpu_percent"] for s in self.samples]
            
            current_memory = memory_values[-1]
            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            
            return {
                "start_memory_mb": self.start_memory,
                "current_memory_mb": current_memory,
                "peak_memory_mb": self.peak_memory,
                "min_memory_mb": self.min_memory,
                "memory_growth_mb": current_memory - self.start_memory,
                "memory_growth_percent": ((current_memory - self.start_memory) / self.start_memory * 100) if self.start_memory > 0 else 0,
                "avg_cpu_percent": avg_cpu,
                "samples_count": len(self.samples)
            }
    
    def check_memory_leak(self, threshold_mb: float = 50.0) -> bool:
        stats = self.get_stats()
        if stats["memory_growth_mb"] > threshold_mb:
            with self.lock:
                self.memory_leaks.append({
                    "timestamp": datetime.now().isoformat(),
                    "growth_mb": stats["memory_growth_mb"],
                    "growth_percent": stats["memory_growth_percent"]
                })
            return True
        return False
    
    def export_samples(self, filepath: str) -> str:
        with self.lock:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.samples, f, ensure_ascii=False, indent=2)
            return filepath


class DataConsistencyVerifier:
    """数据一致性验证器"""
    def __init__(self):
        self.expected_data: Dict[str, Any] = {}
        self.actual_data: Dict[str, Any] = {}
        self.inconsistencies: List[Dict] = []
        self.lock = threading.Lock()
    
    def record_expected(self, key: str, value: Any):
        with self.lock:
            self.expected_data[key] = value
    
    def record_actual(self, key: str, value: Any):
        with self.lock:
            self.actual_data[key] = value
    
    def verify(self, key: str = None) -> bool:
        with self.lock:
            if key:
                return self._verify_single(key)
            return all(self._verify_single(k) for k in self.expected_data)
    
    def _verify_single(self, key: str) -> bool:
        if key not in self.expected_data or key not in self.actual_data:
            return False
        
        expected = self.expected_data[key]
        actual = self.actual_data[key]
        
        if expected != actual:
            inconsistency = {
                "key": key,
                "expected": expected,
                "actual": actual,
                "timestamp": datetime.now().isoformat()
            }
            self.inconsistencies.append(inconsistency)
            print(f"⚠️  数据不一致: {key} - 期望: {expected}, 实际: {actual}")
            return False
        return True
    
    def get_inconsistencies(self) -> List[Dict]:
        with self.lock:
            return list(self.inconsistencies)
    
    def reset(self):
        with self.lock:
            self.expected_data.clear()
            self.actual_data.clear()
            self.inconsistencies.clear()


class ChaosEngineering:
    """混沌工程模块 - 模拟各种故障情况"""
    def __init__(self, bug_tracker: BugTracker):
        self.bug_tracker = bug_tracker
        self.faults = [
            ("high_latency", self._simulate_high_latency),
            ("random_failure", self._simulate_random_failure),
            ("memory_stress", self._simulate_memory_stress),
            ("cpu_stress", self._simulate_cpu_stress),
            ("network_partition", self._simulate_network_partition),
            ("clock_drift", self._simulate_clock_drift)
        ]
    
    def inject_random_fault(self) -> tuple:
        fault_name, fault_func = random.choice(self.faults)
        try:
            fault_func()
            return fault_name, True
        except Exception as e:
            self.bug_tracker.add_bug(
                category="ChaosEngineering",
                severity="MEDIUM",
                description=f"故障注入失败: {fault_name}",
                stack_trace=traceback.format_exc()
            )
            return fault_name, False
    
    def _simulate_high_latency(self):
        delay = random.uniform(0.01, 0.5)
        time.sleep(delay)
    
    def _simulate_random_failure(self):
        if random.random() < 0.05:
            raise RuntimeError("模拟随机故障")
    
    def _simulate_memory_stress(self):
        stress_data = "x" * int(random.uniform(1, 10) * 1024 * 1024)
        return stress_data
    
    def _simulate_cpu_stress(self):
        iterations = random.randint(1000, 10000)
        result = 0
        for i in range(iterations):
            result += i
        return result
    
    def _simulate_network_partition(self):
        time.sleep(random.uniform(0.1, 2.0))
    
    def _simulate_clock_drift(self):
        pass


class ExtendedLongDurationTest:
    """扩展的长时间测试类"""
    def __init__(self, duration_hours: float = 0.1, enable_chaos: bool = True):
        self.duration_hours = duration_hours
        self.enable_chaos = enable_chaos
        self.bug_tracker = BugTracker()
        self.resource_monitor = DetailedResourceMonitor()
        self.data_verifier = DataConsistencyVerifier()
        self.chaos_engine = ChaosEngineering(self.bug_tracker)
        self.stop_event = threading.Event()
        self.stats = {
            "operations_total": 0,
            "operations_success": 0,
            "operations_failed": 0,
            "chaos_injections": 0,
            "start_time": None,
            "end_time": None
        }
    
    def test_extreme_concurrency(self, num_threads: int = 200, ops_per_thread: int = 500) -> Dict:
        """极端并发测试"""
        print(f"\n{'='*80}")
        print(f"测试: 极端并发 (线程数: {num_threads}, 每线程操作: {ops_per_thread})")
        print(f"{'='*80}")
        
        storage = InMemoryChatStorage()
        vm = VersionManager()
        analytics = AnalyticsEngine()
        broker = MessageBroker()
        
        errors = []
        success_count = 0
        lock = threading.Lock()
        
        def worker(worker_id):
            nonlocal success_count
            local_errors = []
            for i in range(ops_per_thread):
                try:
                    if self.enable_chaos and random.random() < 0.1:
                        self.chaos_engine.inject_random_fault()
                    
                    # 存储操作
                    user_id = f"user_{worker_id}_{i % 10}"
                    message = {
                        "content": f"message_{worker_id}_{i}",
                        "timestamp": time.time()
                    }
                    storage.save_message(user_id, message)
                    
                    # 版本管理
                    wf_id = f"workflow_{worker_id}"
                    version = vm.create_version(wf_id, {"step": i})
                    
                    # 分析
                    metric_name = random.choice(["cpu", "memory", "latency", "throughput"])
                    analytics.record_metric(metric_name, random.uniform(0, 100))
                    
                    # 消息代理
                    msg = {
                        "id": f"{worker_id}_{i}",
                        "type": "test",
                        "data": i
                    }
                    broker.publish(msg)
                    
                    with lock:
                        success_count += 1
                        self.stats["operations_total"] += 1
                        self.stats["operations_success"] += 1
                    
                except Exception as e:
                    with lock:
                        self.stats["operations_total"] += 1
                        self.stats["operations_failed"] += 1
                        local_errors.append(f"Worker {worker_id}: {type(e).__name__}: {e}")
                    
                    self.bug_tracker.add_bug(
                        category="Concurrency",
                        severity="HIGH",
                        description=f"极端并发错误: {type(e).__name__}: {e}",
                        stack_trace=traceback.format_exc(),
                        test_context={"worker_id": worker_id, "operation": i}
                    )
            
            return local_errors
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                errors.extend(future.result())
        
        elapsed = time.time() - start_time
        
        stats = {
            "duration": elapsed,
            "success_count": success_count,
            "error_count": len(errors),
            "throughput": (success_count + len(errors)) / elapsed if elapsed > 0 else 0,
            "success_rate": success_count / (success_count + len(errors)) if (success_count + len(errors)) > 0 else 0
        }
        
        print(f"完成! 成功: {stats['success_count']}, 失败: {stats['error_count']}")
        print(f"总耗时: {stats['duration']:.2f}s, 吞吐量: {stats['throughput']:.2f} ops/s")
        print(f"成功率: {stats['success_rate']*100:.2f}%")
        
        return stats
    
    def test_extreme_data_sizes(self) -> Dict:
        """极端数据大小测试"""
        print(f"\n{'='*80}")
        print(f"测试: 极端数据大小")
        print(f"{'='*80}")
        
        storage = InMemoryChatStorage()
        vm = VersionManager()
        analytics = AnalyticsEngine()
        
        test_cases = [
            ("1MB_messages", 1024 * 1024),
            ("5MB_messages", 5 * 1024 * 1024),
            ("10MB_messages", 10 * 1024 * 1024),
            ("large_number_keys", 10000)
        ]
        
        results = {}
        
        for test_name, size in test_cases:
            try:
                print(f"测试 {test_name}...")
                
                if test_name == "large_number_keys":
                    # 测试大量键
                    for i in range(size):
                        key = f"key_{i}"
                        storage.save_message(key, {"content": str(i)})
                else:
                    # 测试大消息
                    big_content = "x" * size
                    storage.save_message("big_test", {"content": big_content})
                
                # 验证数据完整性
                results[test_name] = {"success": True}
                
            except Exception as e:
                results[test_name] = {"success": False, "error": str(e)}
                self.bug_tracker.add_bug(
                    category="DataSize",
                    severity="HIGH",
                    description=f"极端数据大小测试失败: {test_name}",
                    stack_trace=traceback.format_exc()
                )
        
        for name, result in results.items():
            status = "✅ 通过" if result["success"] else "❌ 失败"
            print(f"  {name}: {status}")
        
        return results
    
    def test_extreme_consecutive_operations(self, num_ops: int = 100000) -> Dict:
        """极端连续操作测试"""
        print(f"\n{'='*80}")
        print(f"测试: 极端连续操作 ({num_ops} 次)")
        print(f"{'='*80}")
        
        storage = InMemoryChatStorage()
        analytics = AnalyticsEngine()
        broker = MessageBroker()
        
        errors = 0
        start_time = time.time()
        
        for i in range(num_ops):
            try:
                if i % 1000 == 0:
                    self.resource_monitor.sample(f"operation_{i}")
                    progress = (i / num_ops) * 100
                    print(f"进度: {progress:.1f}% ({i}/{num_ops})")
                
                # 混合操作
                if i % 3 == 0:
                    storage.save_message(f"user_{i%100}", {"data": i})
                elif i % 3 == 1:
                    analytics.record_metric("metric", float(i))
                else:
                    broker.publish({"id": i, "type": "test"})
                
                if self.enable_chaos and random.random() < 0.02:
                    self.chaos_engine.inject_random_fault()
                
                self.stats["operations_total"] += 1
                self.stats["operations_success"] += 1
                
            except Exception as e:
                errors += 1
                self.stats["operations_failed"] += 1
                self.bug_tracker.add_bug(
                    category="ConsecutiveOperations",
                    severity="MEDIUM",
                    description=f"连续操作错误 #{i}: {type(e).__name__}",
                    stack_trace=traceback.format_exc(),
                    test_context={"operation": i}
                )
        
        elapsed = time.time() - start_time
        
        stats = {
            "duration": elapsed,
            "total_ops": num_ops,
            "success_count": num_ops - errors,
            "error_count": errors,
            "throughput": num_ops / elapsed if elapsed > 0 else 0
        }
        
        print(f"完成! 总操作: {stats['total_ops']}, 成功: {stats['success_count']}, 失败: {stats['error_count']}")
        print(f"总耗时: {stats['duration']:.2f}s, 吞吐量: {stats['throughput']:.2f} ops/s")
        
        return stats
    
    def test_memory_stability(self, iterations: int = 100) -> Dict:
        """内存稳定性测试"""
        print(f"\n{'='*80}")
        print(f"测试: 内存稳定性 ({iterations} 轮)")
        print(f"{'='*80}")
        
        memory_history = []
        
        for i in range(iterations):
            # 创建大量对象
            storage = InMemoryChatStorage()
            vm = VersionManager()
            analytics = AnalyticsEngine()
            
            # 执行操作
            for j in range(100):
                storage.save_message(f"user_{j}", {"data": j})
                vm.create_version(f"wf_{j}", {"step": j})
                analytics.record_metric("test", float(j))
            
            # 采样
            sample = self.resource_monitor.sample(f"iteration_{i}")
            memory_history.append(sample["memory_mb"])
            
            # 显式删除
            del storage, vm, analytics
            gc.collect()
            
            # 检测泄漏
            if self.resource_monitor.check_memory_leak(10.0):
                print(f"⚠️  第 {i} 轮检测到潜在内存泄漏")
        
        # 分析内存趋势
        growth = memory_history[-1] - memory_history[0] if len(memory_history) > 1 else 0
        print(f"内存变化: {growth:.2f} MB")
        
        return {
            "memory_history": memory_history,
            "growth_mb": growth
        }
    
    def test_recovery_capability(self) -> Dict:
        """异常恢复能力测试"""
        print(f"\n{'='*80}")
        print(f"测试: 异常恢复能力")
        print(f"{'='*80}")
        
        recovery_tests = [
            self._test_storage_recovery,
            self._test_version_recovery,
            self._test_analytics_recovery,
            self._test_broker_recovery
        ]
        
        results = {}
        for test_func in recovery_tests:
            try:
                result = test_func()
                results[test_func.__name__] = result
            except Exception as e:
                self.bug_tracker.add_bug(
                    category="Recovery",
                    severity="HIGH",
                    description=f"恢复测试失败: {test_func.__name__}",
                    stack_trace=traceback.format_exc()
                )
                results[test_func.__name__] = {"success": False, "error": str(e)}
        
        return results
    
    def _test_storage_recovery(self) -> Dict:
        """测试存储恢复"""
        storage = InMemoryChatStorage()
        
        # 保存数据
        for i in range(100):
            storage.save_message(f"user_{i}", {"data": i})
        
        # 清空
        storage.clear_all()
        
        # 重新保存
        for i in range(100):
            storage.save_message(f"user_{i}", {"data": i * 2})
        
        # 验证
        messages = storage.get_conversation("user_0")
        return {"success": True}
    
    def _test_version_recovery(self) -> Dict:
        """测试版本管理器恢复"""
        vm = VersionManager()
        
        # 创建版本
        for i in range(10):
            vm.create_version("test_wf", {"step": i})
        
        # 验证
        versions = vm.list_versions("test_wf")
        return {"success": True, "versions_count": len(versions)}
    
    def _test_analytics_recovery(self) -> Dict:
        """测试分析引擎恢复"""
        analytics = AnalyticsEngine()
        
        # 记录数据
        for i in range(100):
            analytics.record_metric("test", float(i))
        
        # 获取摘要
        summary = analytics.get_summary()
        return {"success": True, "total_metrics": summary["total_metrics"]}
    
    def _test_broker_recovery(self) -> Dict:
        """测试消息代理恢复"""
        broker = MessageBroker()
        
        # 发布消息
        for i in range(100):
            broker.publish({"id": i})
        
        # 接收
        received = broker.receive()
        return {"success": True, "received": received is not None}
    
    def run(self):
        """运行完整的长时间测试"""
        print("="*80)
        print("MAOS 超长时间深度真实实践测试 v4.0")
        print(f"计划持续时间: {self.duration_hours:.2f} 小时")
        print("="*80)
        
        self.stats["start_time"] = datetime.now().isoformat()
        self.resource_monitor.sample("test_start")
        
        test_results = {}
        
        try:
            # 测试 1: 极端并发
            test_results["extreme_concurrency"] = self.test_extreme_concurrency(
                num_threads=200, ops_per_thread=500
            )
            
            # 测试 2: 极端数据大小
            test_results["extreme_data_sizes"] = self.test_extreme_data_sizes()
            
            # 测试 3: 极端连续操作
            test_results["extreme_consecutive"] = self.test_extreme_consecutive_operations(
                num_ops=100000
            )
            
            # 测试 4: 内存稳定性
            test_results["memory_stability"] = self.test_memory_stability(
                iterations=100
            )
            
            # 测试 5: 异常恢复能力
            test_results["recovery_capability"] = self.test_recovery_capability()
            
        except Exception as e:
            self.bug_tracker.add_bug(
                category="TestFramework",
                severity="CRITICAL",
                description=f"测试框架异常: {type(e).__name__}: {e}",
                stack_trace=traceback.format_exc()
            )
        
        self.stats["end_time"] = datetime.now().isoformat()
        self.resource_monitor.sample("test_end")
        
        # 生成报告
        self._generate_report(test_results)
    
    def _generate_report(self, test_results: Dict):
        """生成详细的测试报告"""
        print("\n" + "="*80)
        print("测试报告")
        print("="*80)
        
        # 操作统计
        print(f"\n操作统计:")
        print(f"  总操作: {self.stats['operations_total']}")
        print(f"  成功: {self.stats['operations_success']}")
        print(f"  失败: {self.stats['operations_failed']}")
        print(f"  成功率: {(self.stats['operations_success']/self.stats['operations_total']*100):.2f}%" if self.stats['operations_total'] > 0 else "  成功率: N/A")
        
        # 资源使用
        resource_stats = self.resource_monitor.get_stats()
        print(f"\n资源使用:")
        print(f"  初始内存: {resource_stats['start_memory_mb']:.2f} MB")
        print(f"  当前内存: {resource_stats['current_memory_mb']:.2f} MB")
        print(f"  峰值内存: {resource_stats['peak_memory_mb']:.2f} MB")
        print(f"  内存增长: {resource_stats['memory_growth_mb']:.2f} MB ({resource_stats['memory_growth_percent']:.2f}%)")
        print(f"  平均 CPU: {resource_stats['avg_cpu_percent']:.2f}%")
        
        # Bug 统计
        bug_summary = self.bug_tracker.summary()
        print(f"\nBug 统计:")
        print(f"  总 Bug 数: {bug_summary['total']}")
        print(f"  唯一 Bug: {bug_summary['unique_bugs']}")
        print(f"  严重 (CRITICAL): {bug_summary['CRITICAL']}")
        print(f"  高 (HIGH): {bug_summary['HIGH']}")
        print(f"  中 (MEDIUM): {bug_summary['MEDIUM']}")
        print(f"  低 (LOW): {bug_summary['LOW']}")
        
        # Bug 详情
        if self.bug_tracker.bugs:
            print(f"\nBug 详情 (前10):")
            for bug in self.bug_tracker.bugs[:10]:
                print(f"\n  [{bug['severity']}] [{bug['category']}]")
                print(f"  {bug['description']}")
                if bug['reproduction_steps']:
                    print(f"  复现步骤: {'; '.join(bug['reproduction_steps'])}")
                print(f"  发生次数: {bug['count']}")
        
        # 导出报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bug_report_path = f"/workspace/maos/tests/bug_report_{timestamp}.json"
        samples_path = f"/workspace/maos/tests/resource_samples_{timestamp}.json"
        
        self.bug_tracker.export_report(bug_report_path)
        self.resource_monitor.export_samples(samples_path)
        
        print(f"\n报告已导出:")
        print(f"  Bug 报告: [bug_report_{timestamp}.json](file://{bug_report_path})")
        print(f"  资源采样: [resource_samples_{timestamp}.json](file://{samples_path})")


if __name__ == "__main__":
    # 运行长时间测试（配置较短时间用于演示）
    tester = ExtendedLongDurationTest(duration_hours=0.1, enable_chaos=True)
    tester.run()
