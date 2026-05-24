#!/usr/bin/env python3
"""
高压力专项测试 - 快速发现系统问题
"""

import sys
import time
import random
import threading
import gc
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class BugTracker:
    def __init__(self):
        self.bugs = []
        self.lock = threading.Lock()
    
    def add(self, category, severity, desc, stack=""):
        with self.lock:
            self.bugs.append({
                "time": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "desc": desc,
                "stack": stack
            })
            print(f"🐛 [{severity}] [{category}] {desc}")
    
    def summary(self):
        with self.lock:
            return {
                "total": len(self.bugs),
                "bugs": self.bugs[-20:]
            }


bug_tracker = BugTracker()


def test_ultra_concurrent_storage():
    """超级并发存储测试 - 1000线程同时写同一个用户"""
    print("\n" + "="*80)
    print("测试1: 超级并发存储 - 1000线程竞争同一个用户")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    success = 0
    lock = threading.Lock()
    
    target_user = "hot_hot_user"
    
    def worker(i):
        nonlocal errors, success
        for j in range(500):
            try:
                storage.save_message(target_user, {
                    "from": f"thread_{i}",
                    "seq": j
                })
                with lock:
                    success += 1
                
                if random.random() < 0.1:
                    storage.get_conversation(target_user)
                    
            except Exception as e:
                with lock:
                    errors += 1
                if errors < 20:
                    bug_tracker.add(
                        "UltraConcurrentStorage",
                        "CRITICAL",
                        f"超级并发存储失败: {type(e).__name__}",
                        traceback.format_exc()
                    )
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=1000) as ex:
        list(ex.map(worker, range(1000)))
    elapsed = time.time() - start
    
    final_messages = storage.get_conversation(target_user)
    print(f"完成! 成功={success}, 错误={errors}, 时间={elapsed:.2f}秒")
    print(f"最终消息数: {len(final_messages)}")
    print(f"吞吐量: {success/elapsed:.0f} ops/s")
    
    return errors


def test_version_avalanche():
    """版本雪崩测试 - 短时间内创建大量版本"""
    print("\n" + "="*80)
    print("测试2: 版本雪崩 - 大量版本创建")
    print("="*80)
    
    vm = VersionManager()
    errors = 0
    success = 0
    
    start = time.time()
    for i in range(200000):
        try:
            wf_id = f"wf_{i % 1000}"
            version = vm.create_version(wf_id, {"v": i})
            
            if random.random() < 0.01:
                vm.get_version(version.id)
                
            if random.random() < 0.005:
                vm.list_versions(wf_id)
                
            success += 1
            
            if i % 20000 == 0:
                print(f"  进度: {i}/200000")
                
        except Exception as e:
            errors += 1
            if errors < 20:
                bug_tracker.add(
                    "VersionAvalanche",
                    "HIGH",
                    f"版本创建失败{i}: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    elapsed = time.time() - start
    print(f"完成! 成功={success}, 错误={errors}, 时间={elapsed:.2f}秒")
    print(f"吞吐量: {success/elapsed:.0f} versions/s")
    
    return errors


def test_memory_leak_detection():
    """内存泄漏检测 - 快速创建删除大量对象"""
    print("\n" + "="*80)
    print("测试3: 内存泄漏检测")
    print("="*80)
    
    errors = 0
    
    # 初始采样
    import gc
    gc.collect()
    
    try:
        import psutil
        process = psutil.Process()
        initial_mem = process.memory_info().rss / 1024 / 1024
        print(f"  初始内存: {initial_mem:.2f}MB")
    except:
        process = None
        initial_mem = 0
        print("  ⚠️  无法监控内存")
    
    for cycle in range(5):
        print(f"  循环 {cycle+1}/5...")
        
        # 创建大量对象
        objects = []
        for i in range(10000):
            storage = InMemoryChatStorage()
            vm = VersionManager()
            analytics = AnalyticsEngine()
            broker = MessageBroker()
            
            storage.save_message("user", {"data": i})
            vm.create_version("wf", {"step": i})
            analytics.record_metric("x", float(i))
            broker.publish({"id": i})
            
            objects.extend([storage, vm, analytics, broker])
        
        # 快速删除并GC
        del objects
        gc.collect()
        gc.collect()
        time.sleep(0.1)
        
        if process:
            current_mem = process.memory_info().rss / 1024 / 1024
            print(f"    内存: {current_mem:.2f}MB (增长: {current_mem - initial_mem:.2f}MB)")
            
            # 检测泄漏
            if current_mem - initial_mem > 50:
                bug_tracker.add(
                    "MemoryLeak",
                    "HIGH",
                    f"可能的内存泄漏: 增长{(current_mem - initial_mem):.2f}MB"
                )
                errors += 1
    
    print("完成!")
    return errors


def test_analytics_flood():
    """分析引擎洪水测试 - 大量不同指标"""
    print("\n" + "="*80)
    print("测试4: 分析引擎洪水 - 大量指标记录")
    print("="*80)
    
    analytics = AnalyticsEngine()
    errors = 0
    success = 0
    
    metric_names = [f"metric_{i}" for i in range(1000)]
    
    start = time.time()
    for i in range(200000):
        try:
            metric = random.choice(metric_names)
            value = random.uniform(0, 100)
            analytics.record_metric(
                metric, 
                value,
                metadata={"iteration": i}
            )
            
            if random.random() < 0.01:
                analytics.get_summary()
                
            success += 1
            
            if i % 20000 == 0:
                print(f"  进度: {i}/200000")
                
        except Exception as e:
            errors += 1
            if errors < 20:
                bug_tracker.add(
                    "AnalyticsFlood",
                    "HIGH",
                    f"分析记录失败{i}: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    elapsed = time.time() - start
    summary = analytics.get_summary()
    print(f"完成! 成功={success}, 错误={errors}, 时间={elapsed:.2f}秒")
    print(f"总指标数: {summary.get('total_metrics', 'N/A')}")
    print(f"吞吐量: {success/elapsed:.0f} metrics/s")
    
    return errors


def test_broker_flood():
    """消息代理洪水测试"""
    print("\n" + "="*80)
    print("测试5: 消息代理洪水 - 百万级消息")
    print("="*80)
    
    broker = MessageBroker(max_messages=200000)
    errors = 0
    success = 0
    
    start = time.time()
    for i in range(1000000):
        try:
            msg = {
                "type": random.choice(["event", "log", "alert", "notification"]),
                "id": i,
                "data": {"payload": "x" * random.randint(10, 200)}
            }
            broker.publish(msg)
            
            if random.random() < 0.05:
                broker.receive()
                
            success += 1
            
            if i % 100000 == 0:
                print(f"  进度: {i}/1000000")
                
        except Exception as e:
            errors += 1
            if errors < 20:
                bug_tracker.add(
                    "BrokerFlood",
                    "MEDIUM",
                    f"消息发布失败{i}: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    elapsed = time.time() - start
    print(f"完成! 成功={success}, 错误={errors}, 时间={elapsed:.2f}秒")
    print(f"吞吐量: {success/elapsed:.0f} msg/s")
    
    return errors


def main():
    print("="*80)
    print("MAOS 高压力专项测试 - 快速发现问题")
    print("="*80)
    
    test_ultra_concurrent_storage()
    test_version_avalanche()
    test_memory_leak_detection()
    test_analytics_flood()
    test_broker_flood()
    
    summary = bug_tracker.summary()
    
    print("\n" + "="*80)
    print("📋 测试总结")
    print("="*80)
    print(f"总Bug数: {summary['total']}")
    
    if summary['bugs']:
        print("\n发现的Bug:")
        for bug in summary['bugs']:
            print(f"\n  [{bug['severity']}] [{bug['category']}] {bug['desc']}")
            if bug.get('stack'):
                print(f"    {bug['stack'][:300]}...")
    
    if summary['total'] == 0:
        print("\n✅ 所有测试通过！未发现Bug！")
    else:
        print(f"\n⚠️  发现 {summary['total']} 个Bug！")


if __name__ == "__main__":
    main()
