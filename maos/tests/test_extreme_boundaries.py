#!/usr/bin/env python3
"""
极端边界条件测试 - 专门针对潜在问题
"""

import sys
import time
import random
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class BugTracker:
    def __init__(self):
        self.bugs = []
        self.lock = threading.Lock()
    
    def add_bug(self, category, severity, description, stack_trace=""):
        with self.lock:
            self.bugs.append({
                "category": category,
                "severity": severity,
                "description": description,
                "stack_trace": stack_trace,
                "timestamp": datetime.now().isoformat()
            })
            print(f"🐛 [{severity}] [{category}] {description}")
    
    def summary(self):
        with self.lock:
            stats = {
                "total": len(self.bugs),
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            }
            for bug in self.bugs:
                stats[bug["severity"]] += 1
            return stats


def test_extreme_latency_simulation(bug_tracker):
    """测试高延迟场景下的系统表现"""
    print(f"\n{'='*80}")
    print(f"测试: 高延迟场景模拟")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    errors = 0
    
    try:
        for i in range(1000):
            try:
                # 模拟延迟
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.001, 0.01))
                
                storage.save_message(f"user_{i%50}", {"data": i})
                
            except Exception as e:
                errors += 1
                bug_tracker.add_bug(
                    category="Latency",
                    severity="MEDIUM",
                    description=f"延迟场景错误 #{i}: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
        
        print(f"完成! 成功: {1000-errors}, 失败: {errors}")
        
    except Exception as e:
        bug_tracker.add_bug(
            category="Latency",
            severity="HIGH",
            description=f"延迟场景测试失败: {type(e).__name__}",
            stack_trace=traceback.format_exc()
        )


def test_large_concurrent_reads_writes(bug_tracker):
    """测试大量并发读写操作"""
    print(f"\n{'='*80}")
    print(f"测试: 大量并发读写 (500 线程混合操作)")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    errors = []
    lock = threading.Lock()
    success_count = 0
    
    def writer(thread_id):
        nonlocal success_count
        try:
            for i in range(100):
                user_id = f"user_{thread_id%20}"
                storage.save_message(user_id, {"data": i})
                with lock:
                    success_count += 1
        except Exception as e:
            with lock:
                errors.append(f"Writer {thread_id}: {type(e).__name__}")
                bug_tracker.add_bug(
                    category="ConcurrentRW",
                    severity="HIGH",
                    description=f"写入线程错误: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
    
    def reader(thread_id):
        try:
            for i in range(100):
                user_id = f"user_{thread_id%20}"
                storage.get_conversation(user_id)
        except Exception as e:
            with lock:
                errors.append(f"Reader {thread_id}: {type(e).__name__}")
                bug_tracker.add_bug(
                    category="ConcurrentRW",
                    severity="HIGH",
                    description=f"读取线程错误: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=500) as executor:
        futures = []
        for i in range(250):
            futures.append(executor.submit(writer, i))
        for i in range(250, 500):
            futures.append(executor.submit(reader, i))
        
        for future in as_completed(futures):
            future.result()
    
    elapsed = time.time() - start_time
    print(f"完成! 成功写入: {success_count}, 错误: {len(errors)}")
    print(f"总耗时: {elapsed:.2f}s")


def test_empty_and_null_values(bug_tracker):
    """测试空值和 None 处理"""
    print(f"\n{'='*80}")
    print(f"测试: 空值和 None 处理")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    analytics = AnalyticsEngine()
    errors = 0
    
    test_cases = [
        ({"content": ""}, "空字符串内容"),
        ({"content": None}, "None 内容"),
        ({}, "空字典"),
        ({"x": None, "y": ""}, "混合空值"),
        ({"content": "x"*1000000}, "超长字符串"),
    ]
    
    for i, (data, description) in enumerate(test_cases):
        try:
            storage.save_message(f"test_{i}", data)
            
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="EmptyValues",
                severity="MEDIUM",
                description=f"空值处理错误 ({description}): {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    # 测试 Analytics Engine 的 None 值
    try:
        analytics.record_metric("test_none", None)
    except Exception as e:
        errors += 1
        bug_tracker.add_bug(
            category="EmptyValues",
            severity="MEDIUM",
            description=f"Analytics None 值错误: {type(e).__name__}",
            stack_trace=traceback.format_exc()
        )
    
    print(f"完成! 测试数: {len(test_cases)+1}, 错误: {errors}")


def test_edge_datetimes(bug_tracker):
    """测试边界日期时间"""
    print(f"\n{'='*80}")
    print(f"测试: 边界日期时间")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    errors = 0
    
    # 避免使用 datetime.min 和 datetime.max，因为它们的 timestamp() 会抛出错误
    edge_dates = [
        datetime(1970, 1, 1),
        datetime(9999, 12, 31),
        datetime.now() - timedelta(days=365*100),
        datetime.now() + timedelta(days=365*100),
    ]
    
    # 手动测试极端时间戳
    edge_timestamps = [
        0.0,  # 1970-01-01
        -100000000000.0,  # 极端过去
        100000000000.0,  # 极端未来
    ]
    
    # 测试 datetime 对象
    for i, dt in enumerate(edge_dates):
        try:
            storage.save_message(f"date_test_{i}", {"timestamp": dt.timestamp()})
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="EdgeDates",
                severity="MEDIUM",
                description=f"日期时间处理错误: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    # 测试极端时间戳
    for i, ts in enumerate(edge_timestamps):
        try:
            storage.save_message(f"ts_test_{i}", {"timestamp": ts})
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="EdgeDates",
                severity="MEDIUM",
                description=f"时间戳处理错误: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    print(f"完成! 测试数: {len(edge_dates)+len(edge_timestamps)}, 错误: {errors}")


def test_version_manager_overflow(bug_tracker):
    """测试版本管理器在大量版本下的表现"""
    print(f"\n{'='*80}")
    print(f"测试: 版本管理器大量版本 (50,000 个版本)")
    print(f"{'='*80}")
    
    vm = VersionManager()
    errors = 0
    start_time = time.time()
    
    version_ids = []
    for i in range(50000):
        try:
            version = vm.create_version("overload_wf", {"step": i})
            version_ids.append(version.id)
            
            if i % 5000 == 0:
                progress = (i / 50000) * 100
                print(f"进度: {progress:.0f}% ({i}/50000)")
        
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="VersionOverflow",
                severity="HIGH",
                description=f"版本创建错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    # 测试查找旧版本
    print("\n测试查找旧版本...")
    lookup_errors = 0
    for i in range(1000):
        try:
            idx = random.randint(0, len(version_ids)-1)
            vm.get_version(version_ids[idx])
        except Exception as e:
            lookup_errors += 1
            bug_tracker.add_bug(
                category="VersionOverflow",
                severity="MEDIUM",
                description=f"版本查找错误: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    elapsed = time.time() - start_time
    print(f"完成! 创建成功: {50000-errors}, 失败: {errors}")
    print(f"查找成功: {1000-lookup_errors}, 失败: {lookup_errors}")
    print(f"总耗时: {elapsed:.2f}s")


def test_broker_message_overflow(bug_tracker):
    """测试消息代理在大量消息下的表现"""
    print(f"\n{'='*80}")
    print(f"测试: 消息代理消息积压 (500,000 条消息)")
    print(f"{'='*80}")
    
    broker = MessageBroker(max_messages=1000000)
    errors = 0
    start_time = time.time()
    
    for i in range(500000):
        try:
            broker.publish({"id": i, "type": "test"})
            
            if i % 50000 == 0:
                progress = (i / 500000) * 100
                print(f"进度: {progress:.0f}% ({i}/500000)")
        
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="BrokerOverflow",
                severity="HIGH",
                description=f"消息发布错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    elapsed = time.time() - start_time
    print(f"完成! 成功: {500000-errors}, 失败: {errors}")
    print(f"总耗时: {elapsed:.2f}s")


def test_analytics_metric_types(bug_tracker):
    """测试分析引擎处理不同类型的指标"""
    print(f"\n{'='*80}")
    print(f"测试: 分析引擎处理多样指标类型")
    print(f"{'='*80}")
    
    analytics = AnalyticsEngine()
    errors = 0
    
    test_values = [
        0.0, 1.0, -1.0, 1000000.0, 0.000001,
        float('inf'), float('-inf'), float('nan'),
    ]
    
    for value in test_values:
        try:
            analytics.record_metric("type_test", value)
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="AnalyticsTypes",
                severity="MEDIUM",
                description=f"指标类型处理错误 ({value}): {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    # 测试获取摘要
    try:
        summary = analytics.get_summary()
        print(f"获取摘要成功: {summary['total_metrics']} 个指标")
    except Exception as e:
        errors += 1
        bug_tracker.add_bug(
            category="AnalyticsTypes",
            severity="HIGH",
            description=f"获取摘要错误: {type(e).__name__}",
            stack_trace=traceback.format_exc()
        )
    
    print(f"完成! 测试数: {len(test_values)+1}, 错误: {errors}")


def test_storage_consistency_check(bug_tracker):
    """测试存储数据一致性"""
    print(f"\n{'='*80}")
    print(f"测试: 存储数据一致性验证")
    print(f"{'='*80}")
    
    storage = InMemoryChatStorage()
    inconsistencies = 0
    
    # 写入已知数据
    expected = {}
    for i in range(1000):
        data = {"index": i, "value": str(i)}
        storage.save_message(f"consistency_user_{i%10}", data)
        expected[f"consistency_user_{i%10}"] = expected.get(f"consistency_user_{i%10}", 0) + 1
    
    # 验证数据完整性
    for user_id, expected_count in expected.items():
        try:
            messages = storage.get_conversation(user_id)
            if len(messages) != expected_count:
                inconsistencies += 1
                bug_tracker.add_bug(
                    category="Consistency",
                    severity="HIGH",
                    description=f"数据不一致: 用户 {user_id}, 期望 {expected_count}, 实际 {len(messages)}"
                )
        except Exception as e:
            inconsistencies += 1
            bug_tracker.add_bug(
                category="Consistency",
                severity="HIGH",
                description=f"数据验证错误: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    print(f"完成! 用户数: {len(expected)}, 不一致数: {inconsistencies}")


def test_rapid_gc_cycles(bug_tracker):
    """测试频繁 GC 下的系统表现"""
    print(f"\n{'='*80}")
    print(f"测试: 频繁 GC 下的系统表现")
    print(f"{'='*80}")
    
    import gc
    errors = 0
    
    for i in range(100):
        try:
            # 每次都创建新实例
            storage = InMemoryChatStorage()
            vm = VersionManager()
            analytics = AnalyticsEngine()
            broker = MessageBroker()
            
            # 执行操作
            for j in range(10):
                storage.save_message(f"user_{j}", {"data": j})
                vm.create_version(f"wf_{j}", {"step": j})
                analytics.record_metric("test", float(j))
                broker.publish({"id": j})
            
            # 显式 GC
            del storage, vm, analytics, broker
            gc.collect()
            
            if i % 20 == 0:
                print(f"进度: {(i/100)*100:.0f}% ({i}/100)")
        
        except Exception as e:
            errors += 1
            bug_tracker.add_bug(
                category="GCStress",
                severity="MEDIUM",
                description=f"GC 压力测试错误 #{i}: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
    
    print(f"完成! 轮数: 100, 错误: {errors}")


def run_all_tests():
    print("="*80)
    print("MAOS 极端边界条件测试 v4.0")
    print("="*80)
    
    bug_tracker = BugTracker()
    
    try:
        test_extreme_latency_simulation(bug_tracker)
        test_large_concurrent_reads_writes(bug_tracker)
        test_empty_and_null_values(bug_tracker)
        test_edge_datetimes(bug_tracker)
        test_version_manager_overflow(bug_tracker)
        test_broker_message_overflow(bug_tracker)
        test_analytics_metric_types(bug_tracker)
        test_storage_consistency_check(bug_tracker)
        test_rapid_gc_cycles(bug_tracker)
        
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
        print(f"\nBug 详情:")
        for bug in bug_tracker.bugs:
            print(f"\n  [{bug['severity']}] [{bug['category']}]")
            print(f"  {bug['description']}")


if __name__ == "__main__":
    run_all_tests()
