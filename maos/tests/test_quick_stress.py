#!/usr/bin/env python3
"""
快速验证版本 - 3分钟测试
"""

import sys
import time
import threading
import gc
import random
from datetime import datetime

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine


def quick_stress_test():
    """快速压力测试 - 3分钟"""
    print("=" * 120)
    print("🚀 QUICK STRESS TEST - 3 MINUTES")
    print("=" * 120)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    
    errors = []
    warnings = []
    total_ops = [0]
    lock = threading.Lock()
    stop_event = threading.Event()
    
    def storage_worker(worker_id):
        users = [f"user_{i}" for i in range(50)]
        sessions = [f"session_{i}" for i in range(20)]
        ops = 0
        
        while not stop_event.is_set():
            try:
                user = random.choice(users)
                session = random.choice(sessions)
                
                # 各种操作
                op = random.choice(["save", "save_and_read", "stats"])
                
                if op == "save":
                    storage.save_message(user, {
                        "content": f"Msg {ops}",
                        "session_id": session,
                        "timestamp": random.choice([time.time(), 0, float('inf') if random.random() < 0.1 else time.time()])
                    })
                elif op == "save_and_read":
                    storage.save_message(user, {"content": f"Msg {ops}", "session_id": session})
                    storage.get_conversation(user, session)
                else:
                    storage.get_stats()
                
                ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                    
            except Exception as e:
                errors.append((worker_id, op, e))
                print(f"[ERROR] Storage worker {worker_id}: {type(e).__name__}: {e}")
        
        with lock:
            total_ops[0] += ops
    
    def version_worker(worker_id):
        workflows = [f"wf_{i}" for i in range(30)]
        ops = 0
        
        while not stop_event.is_set():
            try:
                wf = random.choice(workflows)
                op = random.choice(["create", "list", "get"])
                
                if op == "create":
                    vm.create_version(wf, {"step": ops})
                elif op == "list":
                    vm.list_versions(wf)
                else:
                    versions = vm.list_versions(wf)
                    if versions:
                        vm.get_version(random.choice(versions))
                
                ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                    
            except Exception as e:
                errors.append((worker_id, op, e))
                print(f"[ERROR] Version worker {worker_id}: {type(e).__name__}: {e}")
        
        with lock:
            total_ops[0] += ops
    
    def analytics_worker(worker_id):
        metrics = [f"metric_{i}" for i in range(30)]
        ops = 0
        
        while not stop_event.is_set():
            try:
                metric = random.choice(metrics)
                value = random.choice([
                    random.random(),
                    float('inf'),
                    float('-inf'),
                    float('nan'),
                    0,
                    random.randint(-1000, 1000)
                ])
                
                analytics.record_metric(metric, value)
                ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                    
            except Exception as e:
                errors.append((worker_id, op, e))
                print(f"[ERROR] Analytics worker {worker_id}: {type(e).__name__}: {e}")
        
        with lock:
            total_ops[0] += ops
    
    def integration_worker(worker_id):
        users = [f"user_{i}" for i in range(50)]
        workflows = [f"wf_{i}" for i in range(30)]
        ops = 0
        
        while not stop_event.is_set():
            try:
                user = random.choice(users)
                wf = random.choice(workflows)
                
                # 完整业务流程
                version = vm.create_version(wf, {"user": user})
                storage.save_message(user, {"content": f"Version {version.id}"})
                analytics.record_metric(f"wf_{wf}", 1.0)
                
                ops += 1
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0, 0.002))
                    
            except Exception as e:
                errors.append((worker_id, "integration", e))
                print(f"[ERROR] Integration worker {worker_id}: {type(e).__name__}: {e}")
        
        with lock:
            total_ops[0] += ops
    
    # 启动线程
    print("Starting workers...")
    threads = []
    
    for i in range(30):
        t = threading.Thread(target=storage_worker, args=(i,))
        threads.append(t)
        t.start()
    
    for i in range(20):
        t = threading.Thread(target=version_worker, args=(i,))
        threads.append(t)
        t.start()
    
    for i in range(20):
        t = threading.Thread(target=analytics_worker, args=(i,))
        threads.append(t)
        t.start()
    
    for i in range(15):
        t = threading.Thread(target=integration_worker, args=(i,))
        threads.append(t)
        t.start()
    
    print("Running for 3 minutes...")
    
    # 运行3分钟
    start_time = time.time()
    duration = 180  # 3分钟
    
    while time.time() - start_time < duration:
        time.sleep(10)
        elapsed = time.time() - start_time
        ops = total_ops[0]
        ops_per_sec = ops / max(elapsed, 1)
        print(f"[{elapsed:.0f}s] Ops: {ops:,} ({ops_per_sec:.0f}/s) | Errors: {len(errors)}")
    
    print("\nStopping workers...")
    stop_event.set()
    
    for t in threads:
        t.join(timeout=30)
    
    gc.collect()
    
    end_time = time.time()
    test_duration = end_time - start_time
    
    # 报告
    print("\n" + "=" * 120)
    print("📊 QUICK STRESS TEST RESULTS")
    print("=" * 120)
    
    total_ops_val = total_ops[0]
    ops_per_sec = total_ops_val / max(test_duration, 1)
    
    print(f"\n📈 Operations:")
    print(f"  Total: {total_ops_val:,}")
    print(f"  Duration: {test_duration:.2f}s ({test_duration/60:.1f} min)")
    print(f"  Throughput: {ops_per_sec:.0f} ops/s")
    
    print(f"\n❌ Errors: {len(errors)}")
    if errors:
        print("  Error samples:")
        for i, (worker_id, op, err) in enumerate(errors[:5]):
            print(f"    {i+1}. Worker {worker_id}, Op {op}: {type(err).__name__}: {str(err)[:80]}")
    
    print(f"\n💾 Final Stats:")
    print(f"  Storage: {storage.get_stats()}")
    print(f"  Version: {len(vm.versions)} workflows")
    print(f"  Analytics: {analytics.get_summary()['total_metrics']} metrics")
    
    print("\n" + "=" * 120)
    
    if len(errors) == 0:
        print("✅✅✅ EXCELLENT! ZERO ERRORS IN 3 MINUTE QUICK TEST! ✅✅✅")
        return 0
    else:
        print(f"⚠️  Found {len(errors)} errors!")
        return 1


if __name__ == "__main__":
    exit_code = quick_stress_test()
    sys.exit(exit_code)
