#!/usr/bin/env python3
"""
简化版深度真实实践测试 - 确保能正常运行
"""

import threading
import time
import random
import sys
import gc
import traceback
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

sys.path.insert(0, '/workspace')

from maos.orchestration.orchestrator import MessageBroker
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.storage.in_memory import InMemoryChatStorage


class BugTracker:
    """Bug 追踪器"""
    def __init__(self):
        self.bugs: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def add_bug(self, category: str, severity: str, description: str, stack_trace: str = ""):
        with self.lock:
            self.bugs.append({
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "description": description,
                "stack_trace": stack_trace
            })
            print(f"🐛 发现 Bug [{severity}] [{category}]: {description}")
    
    def summary(self) -> Dict[str, int]:
        with self.lock:
            result = {
                "total": len(self.bugs),
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            }
            for bug in self.bugs:
                result[bug["severity"]] += 1
            return result


def test_concurrent_storage(bug_tracker: BugTracker):
    """并发存储测试"""
    print(f"\n{'='*80}")
    print(f"测试: 并发存储 (100 线程 × 1000 操作)")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    errors = []
    success_count = 0
    lock = threading.Lock()
    
    def worker(worker_id):
        nonlocal success_count
        local_errors = []
        for i in range(1000):
            try:
                user_id = f"user_{worker_id}_{i % 10}"
                storage.save_message(user_id, {"content": f"message_{worker_id}_{i}"})
                
                if i % 100 == 0:
                    messages = storage.get_conversation(user_id)
                
                with lock:
                    success_count += 1
                    
            except Exception as e:
                local_errors.append(f"Worker {worker_id}: {type(e).__name__}: {e}")
                bug_tracker.add_bug(
                    category="ConcurrentStorage",
                    severity="HIGH",
                    description=f"并发存储错误: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
        return local_errors
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(worker, i) for i in range(100)]
        for future in as_completed(futures):
            errors.extend(future.result())
    
    elapsed = time.time() - start_time
    
    print(f"完成! 成功: {success_count}, 失败: {len(errors)}")
    print(f"总耗时: {elapsed:.2f}s, 吞吐量: {(success_count + len(errors))/elapsed:.2f} ops/s")


def test_large_data(bug_tracker: BugTracker):
    """大数量测试"""
    print(f"\n{'='*80}")
    print(f"测试: 大量数据 (100,000 条消息)")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    errors = 0
    
    start_time = time.time()
    
    for i in range(100000):
        try:
            if i % 10000 == 0:
                progress = (i / 100000) * 100
                print(f"进度: {progress:.0f}% ({i}/100000)")
            
            user_id = f"user_{i % 100}"
            storage.save_message(user_id, {"content": f"msg_{i}", "index": i})
            
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="LargeData",
                severity="HIGH",
                description=f"大数量测试错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    elapsed = time.time() - start_time
    
    print(f"完成! 成功: {100000 - errors}, 失败: {errors}")
    print(f"总耗时: {elapsed:.2f}s, 吞吐量: {(100000)/elapsed:.2f} ops/s")


def test_version_manager_stress(bug_tracker: BugTracker):
    """版本管理器压力测试"""
    print(f"\n{'='*80}")
    print(f"测试: 版本管理器压力 (10,000 个版本)")
    print(f"{'='*80}")
    
    vm = VersionManager()
    errors = 0
    
    start_time = time.time()
    
    for i in range(10000):
        try:
            if i % 1000 == 0:
                progress = (i / 10000) * 100
                print(f"进度: {progress:.0f}% ({i}/10000)")
            
            wf_id = f"workflow_{i % 100}"
            version = vm.create_version(wf_id, {"step": i})
            
            if i % 100 == 0:
                vm.get_version(version.id)
                vm.list_versions(wf_id)
            
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="VersionManager",
                severity="HIGH",
                description=f"版本管理器错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    elapsed = time.time() - start_time
    
    print(f"完成! 成功: {10000 - errors}, 失败: {errors}")
    print(f"总耗时: {elapsed:.2f}s, 吞吐量: {(10000)/elapsed:.2f} ops/s")


def test_analytics_stress(bug_tracker: BugTracker):
    """分析引擎压力测试"""
    print(f"\n{'='*80}")
    print(f"测试: 分析引擎压力 (100,000 个指标)")
    print(f"{'='*80}")
    
    analytics = AnalyticsEngine()
    errors = 0
    
    metric_names = ["cpu", "memory", "latency", "throughput", "error_rate"]
    
    start_time = time.time()
    
    for i in range(100000):
        try:
            if i % 10000 == 0:
                progress = (i / 100000) * 100
                print(f"进度: {progress:.0f}% ({i}/100000)")
            
            metric_name = random.choice(metric_names)
            value = random.uniform(0, 100)
            analytics.record_metric(metric_name, value)
            
            if i % 1000 == 0:
                analytics.get_summary()
            
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="Analytics",
                severity="MEDIUM",
                description=f"分析引擎错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    elapsed = time.time() - start_time
    
    summary = analytics.get_summary()
    print(f"完成! 成功: {100000 - errors}, 失败: {errors}")
    print(f"记录指标数: {summary['total_metrics']}")
    print(f"总耗时: {elapsed:.2f}s, 吞吐量: {(100000)/elapsed:.2f} ops/s")


def test_broker_stress(bug_tracker: BugTracker):
    """消息代理压力测试"""
    print(f"\n{'='*80}")
    print(f"测试: 消息代理压力 (100,000 条消息)")
    print(f"{'='*80}")
    
    broker = MessageBroker()
    errors = 0
    
    start_time = time.time()
    
    for i in range(100000):
        try:
            if i % 10000 == 0:
                progress = (i / 100000) * 100
                print(f"进度: {progress:.0f}% ({i}/100000)")
            
            msg = {"id": i, "type": "test", "data": f"msg_{i}"}
            broker.publish(msg)
            
            if i % 100 == 0:
                broker.receive()
            
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="MessageBroker",
                severity="MEDIUM",
                description=f"消息代理错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    elapsed = time.time() - start_time
    
    print(f"完成! 成功: {100000 - errors}, 失败: {errors}")
    print(f"总耗时: {elapsed:.2f}s, 吞吐量: {(100000)/elapsed:.2f} ops/s")


def test_memory_stability(bug_tracker: BugTracker):
    """内存稳定性测试"""
    print(f"\n{'='*80}")
    print(f"测试: 内存稳定性 (100 轮操作)")
    print(f"{'='*80}")
    
    for i in range(100):
        try:
            # 创建大量对象
            storage = InMemoryChatStorage()
            vm = VersionManager()
            analytics = AnalyticsEngine()
            broker = MessageBroker()
            
            # 执行操作
            for j in range(100):
                storage.save_message(f"user_{j}", {"data": j})
                vm.create_version(f"wf_{j}", {"step": j})
                analytics.record_metric("test", float(j))
                broker.publish({"id": j})
            
            # 显式删除
            del storage, vm, analytics, broker
            gc.collect()
            
            if i % 10 == 0:
                print(f"进度: {(i/100)*100:.0f}% ({i}/100)")
            
        except Exception as e:
            bug_tracker.add_bug(
                category="MemoryStability",
                severity="HIGH",
                description=f"内存稳定性错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )


def run_all_tests():
    """运行所有测试"""
    print("="*80)
    print("MAOS 深度真实实践测试 - 简化版 v4.0")
    print("="*80)
    
    bug_tracker = BugTracker()
    
    try:
        # 测试 1: 并发存储
        test_concurrent_storage(bug_tracker)
        
        # 测试 2: 大数量
        test_large_data(bug_tracker)
        
        # 测试 3: 版本管理器压力
        test_version_manager_stress(bug_tracker)
        
        # 测试 4: 分析引擎压力
        test_analytics_stress(bug_tracker)
        
        # 测试 5: 消息代理压力
        test_broker_stress(bug_tracker)
        
        # 测试 6: 内存稳定性
        test_memory_stability(bug_tracker)
        
    except Exception as e:
        bug_tracker.add_bug(
            category="TestFramework",
            severity="CRITICAL",
            description=f"测试框架异常: {type(e).__name__}: {e}",
            stack_trace=traceback.format_exc()
        )
    
    # 生成报告
    print("\n" + "="*80)
    print("测试报告")
    print("="*80)
    
    bug_summary = bug_tracker.summary()
    print(f"\nBug 统计:")
    print(f"  总 Bug 数: {bug_summary['total']}")
    print(f"  严重 (CRITICAL): {bug_summary['CRITICAL']}")
    print(f"  高 (HIGH): {bug_summary['HIGH']}")
    print(f"  中 (MEDIUM): {bug_summary['MEDIUM']}")
    print(f"  低 (LOW): {bug_summary['LOW']}")
    
    if bug_tracker.bugs:
        print(f"\nBug 详情 (前10):")
        for bug in bug_tracker.bugs[:10]:
            print(f"\n  [{bug['severity']}] [{bug['category']}]")
            print(f"  {bug['description']}")


if __name__ == "__main__":
    run_all_tests()
