#!/usr/bin/env python3
"""
简化但更有效的混沌测试 - 实时输出进度
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
    
    def add(self, category, severity, desc):
        key = f"{category}:{desc}"
        with self.lock:
            self.counter[key] += 1
            self.bugs.append({
                "time": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "desc": desc,
                "count": self.counter[key],
            })
            print(f"🐛 [{severity}] [{category}] {desc} (x{self.counter[key]})")
    
    def summary(self):
        with self.lock:
            return {
                "total": sum(self.counter.values()),
                "unique": len(self.counter),
                "bugs": self.bugs[-10:],
            }


bug_tracker = BugTracker()


def test_concurrent_storage():
    """并发存储测试"""
    print("\n" + "="*80)
    print("1. 测试: 极端并发存储 (500线程×200操作)")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    success = 0
    lock = threading.Lock()
    
    def worker(i):
        nonlocal errors, success
        try:
            user_id = f"user_{i}"
            for j in range(200):
                storage.save_message(user_id, {"content": f"msg_{i}_{j}", "seq": j})
                with lock:
                    success += 1
                if random.random() < 0.1:
                    storage.get_conversation(user_id)
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("ConcurrentStorage", "HIGH", f"错误: {type(e).__name__}")
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=500) as ex:
        list(ex.map(worker, range(500)))
    
    print(f"完成! 成功: {success}, 错误: {errors}, 时间: {time.time()-start:.1f}s")
    return success, errors


def test_version_torture():
    """版本管理器酷刑测试"""
    print("\n" + "="*80)
    print("2. 测试: 版本管理器酷刑 (10万次操作)")
    print("="*80)
    
    vm = VersionManager()
    errors = 0
    version_ids = []
    
    start = time.time()
    for i in range(100000):
        try:
            wf = f"wf_{random.randint(0,99)}"
            ver = vm.create_version(wf, {"step": i})
            
            if random.random() < 0.3:
                version_ids.append(ver.id)
            
            if random.random() < 0.2 and version_ids:
                vm.get_version(random.choice(version_ids))
            
            if random.random() < 0.1:
                vm.list_versions(wf)
            
            if random.random() < 0.01:
                version_ids.clear()
            
            if i % 10000 == 0:
                print(f"  进度: {i}/100000")
        
        except Exception as e:
            errors += 1
            bug_tracker.add("VersionTorture", "HIGH", f"错误: {type(e).__name__}")
    
    print(f"完成! 错误: {errors}, 时间: {time.time()-start:.1f}s")
    return errors


def test_broker_flood():
    """消息代理洪水测试"""
    print("\n" + "="*80)
    print("3. 测试: 消息代理洪水 (100万条消息)")
    print("="*80)
    
    broker = MessageBroker()
    errors = 0
    start = time.time()
    
    for i in range(1000000):
        try:
            broker.publish({
                "id": i,
                "type": "test",
                "data": random.randint(0, 10000),
            })
            
            if i % 100 == 0:
                broker.receive()
            
            if i % 100000 == 0:
                print(f"  进度: {i}/1000000")
        
        except Exception as e:
            errors += 1
            bug_tracker.add("BrokerFlood", "MEDIUM", f"错误: {type(e).__name__}")
    
    elapsed = time.time() - start
    print(f"完成! 错误: {errors}, 时间: {elapsed:.1f}s, 吞吐量: {1000000/elapsed:.0f}msg/s")
    return errors


def test_rapid_gc_cycles():
    """快速GC循环测试"""
    print("\n" + "="*80)
    print("4. 测试: 快速创建删除和GC (5000次循环)")
    print("="*80)
    
    errors = 0
    start = time.time()
    
    for i in range(5000):
        try:
            # 创建
            storage = InMemoryChatStorage()
            vm = VersionManager()
            analytics = AnalyticsEngine()
            broker = MessageBroker()
            
            # 使用
            storage.save_message("temp", {"content": "temp"})
            vm.create_version("temp", {"step": 1})
            analytics.record_metric("temp", 1.0)
            broker.publish({"type": "temp"})
            
            # 删除并GC
            del storage, vm, analytics, broker
            gc.collect()
            
            if i % 500 == 0:
                print(f"  进度: {i}/5000")
        
        except Exception as e:
            errors += 1
            bug_tracker.add("RapidGC", "MEDIUM", f"错误: {type(e).__name__}")
    
    print(f"完成! 错误: {errors}, 时间: {time.time()-start:.1f}s")
    return errors


def test_mixed_workload(duration_sec):
    """混合工作负载测试"""
    print("\n" + "="*80)
    print(f"5. 测试: 混合工作负载 ({duration_sec}秒)")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    broker = MessageBroker()
    
    success = 0
    errors = 0
    lock = threading.Lock()
    should_stop = threading.Event()
    
    def worker(worker_id):
        nonlocal success, errors
        user_id = f"user_{worker_id}"
        wf_id = f"wf_{worker_id}"
        
        while not should_stop.is_set():
            try:
                choice = random.random()
                
                if choice < 0.35:
                    # 存储操作
                    storage.save_message(user_id, {"content": f"msg_{worker_id}_{success}"})
                    if random.random() < 0.1:
                        storage.get_conversation(user_id)
                
                elif choice < 0.65:
                    # 版本管理
                    ver = vm.create_version(wf_id, {"step": success})
                    if random.random() < 0.1:
                        vm.get_version(ver.id)
                    if random.random() < 0.05:
                        vm.list_versions(wf_id)
                
                elif choice < 0.85:
                    # 分析
                    metric = random.choice(["cpu", "mem", "latency", "throughput"])
                    analytics.record_metric(metric, random.uniform(0, 100))
                    if random.random() < 0.05:
                        analytics.get_summary()
                
                else:
                    # 消息
                    broker.publish({"type": "event", "source": worker_id})
                    if random.random() < 0.1:
                        broker.receive()
                
                with lock:
                    success += 1
                
                # 偶尔注入小延迟模拟真实场景
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.001, 0.01))
            
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add("MixedWorkload", "HIGH", f"错误: {type(e).__name__}")
    
    def stop_after():
        time.sleep(duration_sec)
        should_stop.set()
        print("\n  时间到，正在停止工作线程...")
    
    threading.Thread(target=stop_after, daemon=True).start()
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=200) as ex:
        list(ex.map(worker, range(200)))
    
    elapsed = time.time() - start
    print(f"完成! 成功: {success}, 错误: {errors}, 时间: {elapsed:.1f}s")
    print(f"吞吐量: {success/elapsed:.0f}ops/s")
    return success, errors


def main():
    print("="*80)
    print("MAOS 深度混沌测试 v5.0 (简化实时版)")
    print("="*80)
    
    # 运行所有测试
    test_concurrent_storage()
    test_version_torture()
    test_broker_flood()
    test_rapid_gc_cycles()
    test_mixed_workload(90)  # 90秒
    
    # 总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    summary = bug_tracker.summary()
    print(f"总Bug数: {summary['total']}")
    print(f"唯一Bug: {summary['unique']}")
    
    if summary['bugs']:
        print("\n最近Bug:")
        for bug in summary['bugs']:
            print(f"  {bug['time']} [{bug['severity']}] [{bug['category']}] {bug['desc']} (x{bug['count']})")
    
    if summary['total'] == 0:
        print("\n✅ 所有测试通过，无 Bug 发现!")
    else:
        print(f"\n⚠️  共发现 {summary['total']} 个问题!")


if __name__ == "__main__":
    main()
