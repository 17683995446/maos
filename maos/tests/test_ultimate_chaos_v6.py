#!/usr/bin/env python3
"""
终极混乱测试 - 寻找系统的极限
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
from collections import Counter, defaultdict

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


def test_massive_shared_state():
    """测试多个线程共享同一个实例的极端情况"""
    print("\n" + "="*80)
    print("1. 测试: 极端共享状态 (1000线程竞争同一资源)")
    print("="*80)
    
    storage = InMemoryChatStorage()
    analytics = AnalyticsEngine()
    vm = VersionManager()
    broker = MessageBroker()
    
    errors = 0
    success = 0
    lock = threading.Lock()
    
    def worker(i):
        nonlocal errors, success
        user_id = f"shared_user_{i % 50}"  # 只使用50个用户，增加竞争
        wf_id = f"shared_wf_{i % 10}"
        
        for _ in range(500):
            try:
                choice = random.random()
                
                if choice < 0.25:
                    # 存储操作 - 高竞争
                    storage.save_message(user_id, {
                        "content": f"from_{i}",
                        "thread": i,
                        "time": time.time(),
                    })
                    if random.random() < 0.3:
                        storage.get_conversation(user_id)
                
                elif choice < 0.5:
                    # 版本管理 - 极高竞争
                    ver = vm.create_version(wf_id, {
                        "step": random.randint(0, 1000),
                        "from_thread": i,
                    })
                    if random.random() < 0.2:
                        vm.get_version(ver.id)
                    if random.random() < 0.1:
                        vm.list_versions(wf_id)
                
                elif choice < 0.75:
                    # 分析 - 高竞争
                    metric = random.choice(["a", "b", "c", "d", "e"])
                    analytics.record_metric(
                        metric,
                        random.uniform(0, 100),
                        metadata={"thread": i}
                    )
                    if random.random() < 0.1:
                        analytics.get_summary()
                
                else:
                    # 消息代理 - 极高竞争
                    broker.publish({
                        "from": i,
                        "type": random.choice(["event", "log", "alert"]),
                    })
                    if random.random() < 0.15:
                        broker.receive()
                
                with lock:
                    success += 1
                
                # 随机延迟，增加混乱
                if random.random() < 0.02:
                    time.sleep(random.uniform(0.001, 0.02))
            
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add(
                    "MassiveContention",
                    "HIGH",
                    f"错误: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=1000) as ex:
        futures = [ex.submit(worker, i) for i in range(1000)]
        for f in as_completed(futures):
            f.result()
    
    print(f"完成! 成功: {success}, 错误: {errors}, 时间: {time.time()-start:.1f}s")
    print(f"吞吐量: {success/(time.time()-start):.0f}ops/s")
    return success, errors


def test_extreme_data_sizes():
    """测试极端数据大小"""
    print("\n" + "="*80)
    print("2. 测试: 极端数据大小")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    
    test_cases = [
        ("空", {}),
        ("微", {"x": "x"}),
        ("小", {f"k_{i}": f"v_{i}" for i in range(100)}),
        ("中", {f"k_{i}": f"v_{i}" for i in range(1000)}),
        ("大", {"data": "x" * 100000}),
        ("超大", {"data": "x" * 1000000}),
        ("混合", {f"key_{i}": ("x" * random.randint(1, 10000)) for i in range(100)}),
    ]
    
    for name, data in test_cases:
        try:
            print(f"  测试: {name}")
            for i in range(100):
                storage.save_message(f"user_{i}", data)
            print(f"  ✓ 成功")
        except Exception as e:
            errors += 1
            bug_tracker.add(
                "ExtremeData",
                "HIGH",
                f"{name}数据失败: {type(e).__name__}",
                traceback.format_exc()
            )
    
    print(f"完成! 错误: {errors}")
    return errors


def test_temporal_anomalies():
    """测试时间异常情况"""
    print("\n" + "="*80)
    print("3. 测试: 时间异常")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    
    edge_timestamps = [
        0,  # 1970-01-01
        1,
        -1,
        -100000000000,
        100000000000,
        253402300800,  # 9999年
        9999999999999,
    ]
    
    for ts in edge_timestamps:
        try:
            storage.save_message("time_test", {"timestamp": ts})
        except Exception as e:
            errors += 1
            bug_tracker.add(
                "TemporalAnomaly",
                "MEDIUM",
                f"时间戳{ts}失败: {type(e).__name__}",
                traceback.format_exc()
            )
    
    print(f"完成! 错误: {errors}")
    return errors


def test_interleaved_operations():
    """测试极度交错的操作模式"""
    print("\n" + "="*80)
    print("4. 测试: 极度交错操作模式")
    print("="*80)
    
    errors = 0
    
    def pattern1():
        storage = InMemoryChatStorage()
        for i in range(1000):
            storage.save_message("p1", {"i": i})
            storage.get_conversation("p1")
    
    def pattern2():
        vm = VersionManager()
        for i in range(1000):
            ver = vm.create_version("p2", {"i": i})
            vm.get_version(ver.id)
    
    def pattern3():
        analytics = AnalyticsEngine()
        for i in range(1000):
            analytics.record_metric("x", float(i))
            analytics.get_summary()
    
    def pattern4():
        broker = MessageBroker()
        for i in range(1000):
            broker.publish({"i": i})
            broker.receive()
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [
            ex.submit(pattern1),
            ex.submit(pattern2),
            ex.submit(pattern3),
            ex.submit(pattern4),
        ]
        for f in futures:
            try:
                f.result()
            except Exception as e:
                errors += 1
                bug_tracker.add(
                    "InterleavedOps",
                    "MEDIUM",
                    f"交错操作失败: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    print(f"完成! 错误: {errors}, 时间: {time.time()-start:.1f}s")
    return errors


def test_rapid_state_fluctuation():
    """测试快速状态波动"""
    print("\n" + "="*80)
    print("5. 测试: 快速状态波动")
    print("="*80)
    
    errors = 0
    
    def fluctuator(i):
        try:
            for _ in range(1000):
                # 快速创建和删除实例
                storage = InMemoryChatStorage()
                vm = VersionManager()
                analytics = AnalyticsEngine()
                broker = MessageBroker()
                
                # 使用一次
                storage.save_message("temp", {"x": 1})
                vm.create_version("temp", {"x": 1})
                analytics.record_metric("temp", 1.0)
                broker.publish({"x": 1})
                
                # 删除并GC
                del storage, vm, analytics, broker
                gc.collect()
                
        except Exception as e:
            bug_tracker.add(
                "RapidFluctuation",
                "MEDIUM",
                f"波动失败: {type(e).__name__}",
                traceback.format_exc()
            )
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=100) as ex:
        list(ex.map(fluctuator, range(100)))
    
    print(f"完成! 错误: {errors}, 时间: {time.time()-start:.1f}s")
    return errors


def test_extreme_retrieval_patterns():
    """测试极端的检索模式"""
    print("\n" + "="*80)
    print("6. 测试: 极端检索模式")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    errors = 0
    
    # 先填充数据
    all_version_ids = []
    for i in range(10000):
        storage.save_message(f"user_{i}", {"data": i})
        ver = vm.create_version(f"wf_{i}", {"data": i})
        all_version_ids.append(ver.id)
    
    # 然后极端模式检索
    try:
        # 随机大量读取
        print("  随机读取...")
        for _ in range(10000):
            storage.get_conversation(f"user_{random.randint(0, 9999)}")
        
        # 顺序大量读取
        print("  顺序读取...")
        for i in range(10000):
            storage.get_conversation(f"user_{i}")
        
        # 混合随机版本操作
        print("  随机版本操作...")
        for _ in range(10000):
            if random.random() < 0.5:
                vm.get_version(random.choice(all_version_ids))
            else:
                vm.list_versions(f"wf_{random.randint(0, 9999)}")
        
        print("  ✓ 成功")
    except Exception as e:
        errors += 1
        bug_tracker.add(
            "ExtremeRetrieval",
            "HIGH",
            f"检索失败: {type(e).__name__}",
            traceback.format_exc()
        )
    
    print(f"完成! 错误: {errors}")
    return errors


def test_long_running_sustained_load():
    """长时间持续负载测试"""
    print("\n" + "="*80)
    print("7. 测试: 长时间持续负载 (120秒)")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    broker = MessageBroker()
    
    success = 0
    errors = 0
    lock = threading.Lock()
    should_stop = threading.Event()
    
    def worker(i):
        nonlocal success, errors
        user_id = f"user_{i}"
        wf_id = f"wf_{i}"
        
        while not should_stop.is_set():
            try:
                # 混合操作
                storage.save_message(user_id, {"t": time.time(), "i": i})
                ver = vm.create_version(wf_id, {"t": time.time(), "i": i})
                analytics.record_metric("m", float(i))
                broker.publish({"i": i})
                
                # 偶尔读取
                if random.random() < 0.05:
                    storage.get_conversation(user_id)
                    vm.get_version(ver.id)
                    analytics.get_summary()
                    broker.receive()
                
                with lock:
                    success += 1
                
                # 随机小延迟
                time.sleep(random.uniform(0, 0.002))
            
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add(
                    "LongSustained",
                    "HIGH",
                    f"持续负载失败: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    def stop_after():
        time.sleep(120)
        should_stop.set()
        print("\n  时间到，正在停止...")
    
    threading.Thread(target=stop_after, daemon=True).start()
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=200) as ex:
        list(ex.map(worker, range(200)))
    
    elapsed = time.time() - start
    print(f"完成! 成功: {success}, 错误: {errors}")
    print(f"吞吐量: {success/elapsed:.0f}ops/s")
    return success, errors


def main():
    print("="*80)
    print("MAOS 终极混乱测试 - 寻找系统极限")
    print("="*80)
    
    # 运行所有测试
    test_massive_shared_state()
    test_extreme_data_sizes()
    test_temporal_anomalies()
    test_interleaved_operations()
    test_rapid_state_fluctuation()
    test_extreme_retrieval_patterns()
    test_long_running_sustained_load()
    
    # 总结
    print("\n" + "="*80)
    print("📊 终极测试总结")
    print("="*80)
    
    summary = bug_tracker.summary()
    print(f"总Bug数: {summary['total']}")
    print(f"唯一Bug: {summary['unique']}")
    
    if summary['bugs']:
        print("\n最近Bug:")
        for bug in summary['bugs']:
            print(f"\n  {bug['time']}")
            print(f"  [{bug['severity']}] [{bug['category']}] {bug['desc']} (x{bug['count']})")
    
    if summary['total'] == 0:
        print("\n✅ 恭喜! 系统通过了所有终极混乱测试!")
    else:
        print(f"\n⚠️  发现 {summary['total']} 个问题需要修复!")


if __name__ == "__main__":
    main()
