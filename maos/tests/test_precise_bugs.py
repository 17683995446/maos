#!/usr/bin/env python3
"""
精准边界测试 - 寻找并修复真实问题
"""
import sys
sys.path.insert(0, '/workspace')

import time
import random
import threading
import gc
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import Counter

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class BugTracker:
    def __init__(self):
        self.bugs = []
        self.counter = Counter()
        self.lock = threading.Lock()
    
    def add(self, category, severity, desc, stack=""):
        key = f"{category}:{desc[:100]}"
        with self.lock:
            self.counter[key] += 1
            self.bugs.append({
                "time": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "desc": desc,
                "stack": stack,
                "count": self.counter[key],
            })
            print(f"🐛 [{severity}] [{category}] {desc} (x{self.counter[key]})")
    
    def summary(self):
        with self.lock:
            return {
                "total": sum(self.counter.values()),
                "unique": len(self.counter),
                "bugs": self.bugs[-20:],
            }


bug_tracker = BugTracker()


def test_analytics_nan_inf_values():
    """测试分析引擎处理特殊值"""
    print("\n" + "="*80)
    print("测试1: AnalyticsEngine处理NaN/Inf值")
    print("="*80)
    
    analytics = AnalyticsEngine()
    errors = 0
    
    special_values = [
        float('nan'),
        float('inf'),
        float('-inf'),
    ]
    
    for value in special_values:
        try:
            analytics.record_metric("test_special", value)
            summary = analytics.get_summary()
            print(f"  ✓ {value} 记录成功")
        except Exception as e:
            errors += 1
            bug_tracker.add(
                "AnalyticsSpecialValues",
                "HIGH",
                f"处理{value}失败: {type(e).__name__}",
                traceback.format_exc()
            )
    
    # 验证
    try:
        data = analytics.get_all_metrics()
        summary = analytics.get_summary()
        print(f"  ✓ get_all_metrics 成功")
        print(f"  ✓ get_summary 成功")
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "AnalyticsSummary",
            "HIGH",
            f"获取摘要失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    print(f"完成! 错误: {errors}")
    return errors


def test_version_edge_case_retrievals():
    """测试版本管理器的边界检索"""
    print("\n" + "="*80)
    print("测试2: VersionManager边界检索")
    print("="*80)
    
    vm = VersionManager()
    errors = 0
    
    # 测试空情况
    try:
        v = vm.get_version("nonexistent_id")
        print(f"  ✓ 获取不存在的ID: {v}")
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "VersionNonexistent",
            "MEDIUM",
            f"获取不存在ID失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    try:
        versions = vm.list_versions("nonexistent_workflow")
        print(f"  ✓ 列出不存在的workflow: {versions}")
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "VersionListNonexistent",
            "MEDIUM",
            f"列出不存在workflow失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    # 测试删除后
    try:
        ver = vm.create_version("test_wf", {"test": 1})
        ver_id = ver.id
        
        # 模拟删除 - 我们没有直接删除方法，但可以看看获取和列表
        vm.get_version(ver_id)
        versions = vm.list_versions("test_wf")
        print(f"  ✓ 正常检索: ID={ver_id}, 列表={len(versions)}个版本")
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "VersionNormalOps",
            "MEDIUM",
            f"正常操作失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    print(f"完成! 错误: {errors}")
    return errors


def test_broker_extreme_load():
    """测试消息代理在极端负载下的稳定性"""
    print("\n" + "="*80)
    print("测试3: MessageBroker极端负载")
    print("="*80)
    
    broker = MessageBroker(max_messages=50000)
    errors = 0
    
    # 测试大量小消息
    print("  测试大量小消息...")
    start = time.time()
    for i in range(50000):
        try:
            broker.publish({"type": "test", "i": i})
        except Exception as e:
            errors += 1
            if errors < 10:
                bug_tracker.add(
                    "BrokerLoadSmall",
                    "MEDIUM",
                    f"小消息发布失败{i}: {type(e).__name__}",
                    traceback.format_exc()
                )
    elapsed = time.time() - start
    print(f"  完成 50000条: {elapsed:.2f}秒, 错误={errors}")
    
    # 测试超大消息
    print("  测试超大消息...")
    big_msg = {"type": "big", "data": "x" * 1000000}  # 1MB数据
    for i in range(100):
        try:
            broker.publish(big_msg)
        except Exception as e:
            errors += 1
            if errors < 20:
                bug_tracker.add(
                    "BrokerLoadBig",
                    "MEDIUM",
                    f"大消息发布失败{i}: {type(e).__name__}",
                    traceback.format_exc()
                )
    print(f"  完成 100条大消息")
    
    # 测试检索
    print("  测试检索...")
    try:
        msg = broker.receive()
        msgs = broker.get_messages()
        print(f"  ✓ receive成功: {msg is not None}")
        print(f"  ✓ get_messages成功: {len(msgs)}条")
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "BrokerRetrieve",
            "HIGH",
            f"检索消息失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    print(f"完成! 总错误: {errors}")
    return errors


def test_storage_concurrent_read_write():
    """测试存储的并发读写 - 更精确的竞争条件"""
    print("\n" + "="*80)
    print("测试4: InMemoryChatStorage并发读写竞争")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    success_count = 0
    lock = threading.Lock()
    
    # 所有线程竞争同一个用户
    target_user = "hot_user"
    
    def writer(worker_id):
        nonlocal errors, success_count
        for i in range(1000):
            try:
                storage.save_message(target_user, {"from": worker_id, "seq": i})
                with lock:
                    success_count += 1
            except Exception as e:
                with lock:
                    errors += 1
                if errors < 20:
                    bug_tracker.add(
                        "StorageConcurrentWrite",
                        "HIGH",
                        f"并发写入失败: {type(e).__name__}",
                        traceback.format_exc()
                    )
    
    def reader(worker_id):
        nonlocal errors
        for i in range(1000):
            try:
                _ = storage.get_conversation(target_user)
            except Exception as e:
                with lock:
                    errors += 1
                if errors < 20:
                    bug_tracker.add(
                        "StorageConcurrentRead",
                        "HIGH",
                        f"并发读取失败: {type(e).__name__}",
                        trace.format_exc()
                    )
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=200) as ex:
        futures = []
        for i in range(100):
            futures.append(ex.submit(writer, i))
        for i in range(100):
            futures.append(ex.submit(reader, i))
        for f in futures:
            f.result()
    elapsed = time.time() - start
    
    # 验证一致性
    messages = storage.get_conversation(target_user)
    print(f"完成! 成功={success_count}, 错误={errors}, 时间={elapsed:.2f}秒")
    print(f"最终消息数: {len(messages)}")
    
    return errors


def test_rapid_create_destroy_with_state():
    """测试快速创建销毁并验证状态正确性"""
    print("\n" + "="*80)
    print("测试5: 快速创建销毁与状态验证")
    print("="*80)
    
    errors = 0
    
    def cycle():
        storage = InMemoryChatStorage()
        vm = VersionManager()
        analytics = AnalyticsEngine()
        broker = MessageBroker()
        
        # 使用它们
        storage.save_message("user", {"data": 1})
        vm.create_version("wf", {"step": 1})
        analytics.record_metric("x", 1.0)
        broker.publish({"type": "test"})
        
        # 验证状态
        conv = storage.get_conversation("user")
        versions = vm.list_versions("wf")
        summary = analytics.get_summary()
        msg = broker.receive()
        
        if not conv:
            nonlocal errors
            errors += 1
            bug_tracker.add(
                "RapidStateLost",
                "MEDIUM",
                "存储状态丢失",
                "",
            )
        
        # 删除
        del storage, vm, analytics, broker
        gc.collect()
    
    start = time.time()
    for i in range(1000):
        try:
            cycle()
            if i % 100 == 0:
                print(f"  进度: {i}/1000")
        except Exception as e:
            errors += 1
            bug_tracker.add(
                "RapidCycleError",
                "HIGH",
                f"循环失败{i}: {type(e).__name__}",
                traceback.format_exc()
            )
    
    elapsed = time.time() - start
    print(f"完成! 1000次循环, 错误={errors}, 时间={elapsed:.2f}秒")
    return errors


def test_timestamp_edge_cases():
    """测试时间戳边界"""
    print("\n" + "="*80)
    print("测试6: 极端时间戳处理")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    
    # 直接测试我们的save_message方法
    # 使用一个小的测试来验证我们的时间戳处理
    try:
        # 正常时间戳
        storage.save_message("test", {"timestamp": time.time()})
        print("  ✓ 正常时间戳")
        
        # 超大时间戳
        storage.save_message("test", {"timestamp": 9999999999999.9})
        print("  ✓ 超大时间戳")
        
        # 超小时间戳
        storage.save_message("test", {"timestamp": -9999999999999.9})
        print("  ✓ 超小时间戳")
        
        # 0
        storage.save_message("test", {"timestamp": 0.0})
        print("  ✓ 0时间戳")
        
        # None - 应该被我们的代码处理
        storage.save_message("test", {"timestamp": None})
        print("  ✓ None时间戳")
        
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "TimestampEdge",
            "MEDIUM",
            f"时间戳处理失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    print(f"完成! 错误: {errors}")
    return errors


def main():
    print("="*80)
    print("MAOS 精准边界测试 - 寻找真实问题")
    print("="*80)
    
    test_analytics_nan_inf_values()
    test_version_edge_case_retrievals()
    test_broker_extreme_load()
    test_storage_concurrent_read_write()
    test_rapid_create_destroy_with_state()
    test_timestamp_edge_cases()
    
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    summary = bug_tracker.summary()
    print(f"总Bug数: {summary['total']}")
    print(f"唯一Bug: {summary['unique']}")
    
    if summary['bugs']:
        print("\n发现的Bug:")
        for bug in summary['bugs']:
            print(f"\n  [{bug['severity']}] [{bug['category']}] {bug['desc']} (x{bug['count']})")
            if bug['stack']:
                print(f"    {bug['stack'][:200]}...")
    
    if summary['total'] == 0:
        print("\n✅ 所有测试通过！")
    else:
        print(f"\n⚠️ 发现 {summary['total']} 个问题需要修复。")


if __name__ == "__main__":
    main()
