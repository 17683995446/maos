#!/usr/bin/env python3
"""
MAOS System - EXTREME CHAOS & COMPLEX SCENARIO TEST
极端混沌与复杂场景测试 - 深度发现系统潜在问题
"""

import sys
import time
import random
import threading
import gc
import traceback
import os
import signal
import resource
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque

sys.path.insert(0, '/workspace')

# Import all core modules
from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.types import ConversationMessage, ParticipantRole


class ExtremeChaosBugTracker:
    """极端混沌Bug追踪器 - 超详细记录"""
    
    def __init__(self):
        self.bugs = []
        self.warnings = []
        self.operation_log = deque(maxlen=2000)
        self.error_log = deque(maxlen=500)
        self.lock = threading.Lock()
        self.total_operations = 0
        self.error_count = 0
        self.warning_count = 0
        
    def log_operation(self, thread_name, component, operation, status, latency=0):
        """记录操作"""
        with self.lock:
            self.operation_log.append({
                "time": datetime.now(),
                "thread": thread_name,
                "component": component,
                "operation": operation,
                "status": status,
                "latency_ms": latency * 1000
            })
            self.total_operations += 1
    
    def log_error(self, component, severity, message, exception=None):
        """记录错误"""
        with self.lock:
            self.error_count += 1
            err_info = {
                "time": datetime.now(),
                "component": component,
                "severity": severity,
                "message": message,
                "exception_type": type(exception).__name__ if exception else None,
                "exception_str": str(exception) if exception else None,
                "traceback": traceback.format_exc() if exception else None
            }
            self.error_log.append(err_info)
            self.bugs.append(err_info)
            print(f"❌ ERROR [{component}] [{severity}] {message}")
            if exception:
                print(f"   {type(exception).__name__}: {str(exception)}")
    
    def log_warning(self, component, message):
        """记录警告"""
        with self.lock:
            self.warning_count += 1
            warn_info = {
                "time": datetime.now(),
                "component": component,
                "message": message
            }
            self.warnings.append(warn_info)
            print(f"⚠️  WARNING [{component}] {message}")
    
    def summary_report(self):
        """生成摘要报告"""
        with self.lock:
            print("\n" + "=" * 120)
            print("EXTREME CHAOS TEST - SUMMARY REPORT")
            print("=" * 120)
            print(f"Total Operations: {self.total_operations:,}")
            print(f"Total Errors: {self.error_count}")
            print(f"Total Warnings: {self.warning_count}")
            print(f"Error Rate: {self.error_count / max(self.total_operations, 1) * 100:.4f}%")
            
            if self.bugs:
                print("\n" + "-" * 120)
                print("ERROR LIST (Last 20):")
                print("-" * 120)
                for i, bug in enumerate(reversed(self.bugs[-20:])):
                    print(f"\n{i+1}. [{bug['component']}] [{bug['severity']}]")
                    print(f"    Time: {bug['time']}")
                    print(f"    Message: {bug['message']}")
                    if bug['exception_type']:
                        print(f"    {bug['exception_type']}: {bug['exception_str']}")
            
            if self.error_count == 0 and self.warning_count == 0:
                print("\n✅ EXCELLENT! NO BUGS FOUND IN EXTREME CHAOS TEST!")
                return 0
            else:
                return 1


bug_tracker = ExtremeChaosBugTracker()


class ChaosGenerator:
    """混沌场景生成器"""
    
    def __init__(self):
        self.scenarios = [
            "normal",
            "delayed",
            "large",
            "unicode",
            "null",
            "empty",
            "rapid",
            "garbage"
        ]
    
    def random_content(self):
        """生成随机内容"""
        scenario = random.choice(self.scenarios)
        
        if scenario == "normal":
            return f"Normal message {random.randint(1, 1000000)}"
        elif scenario == "delayed":
            time.sleep(random.random() * 0.01)
            return f"Delayed message {random.randint(1, 1000000)}"
        elif scenario == "large":
            return "x" * random.randint(100, 10000)
        elif scenario == "unicode":
            return "".join(random.choice(["🎉", "🎊", "🎁", "🎀", "🎄", "🎅", "🎆", "🎇", "🎈", "🎉", "中文", "日本語", "한국어"]) for _ in range(random.randint(1, 50)))
        elif scenario == "null":
            return None if random.random() < 0.5 else {"text": "Some null test", "data": None}
        elif scenario == "empty":
            return ""
        elif scenario == "rapid":
            return f"Rapid {random.randint(1, 1000000)}"
        else:
            return random.choice([123, 3.14, True, False, [], {}, ["a", 1, None], {"nested": {"deep": "test"}}])
    
    def random_user(self):
        """生成随机用户ID"""
        return f"user_{random.randint(1, 200)}"
    
    def random_session(self):
        """生成随机会话ID"""
        return f"session_{random.randint(1, 50)}"
    
    def random_agent(self):
        """生成随机Agent ID"""
        return f"agent_{random.randint(1, 10)}"


chaos = ChaosGenerator()


def test_extreme_storage_chaos(duration_seconds=120, num_threads=50):
    """极端存储混沌测试"""
    print("\n" + "=" * 120)
    print(f"STORAGE EXTREME CHAOS TEST - {num_threads} threads for {duration_seconds} seconds")
    print("=" * 120)
    
    storage = InMemoryChatStorage()
    stop_event = threading.Event()
    threads = []
    errors = [0]
    lock = threading.Lock()
    operations = [0]
    
    def worker(worker_id):
        thread_name = f"StorageWorker-{worker_id}"
        while not stop_event.is_set():
            try:
                start = time.time()
                user = chaos.random_user()
                session = chaos.random_session()
                agent = chaos.random_agent()
                content = chaos.random_content()
                
                # Random operation
                op = random.choice(["save", "read", "clear", "stats"])
                
                if op == "save":
                    success = storage.save_message(
                        user,
                        {"content": content, "session_id": session, "agent_id": agent, "timestamp": time.time() + random.randint(-100000, 100000)}
                    )
                    if not success:
                        bug_tracker.log_warning("STORAGE", f"Save failed for user {user}")
                
                elif op == "read":
                    conv = storage.get_conversation(user, session, agent)
                    # No problem
                
                elif op == "clear":
                    if random.random() < 0.001:  # Only clear rarely to avoid data loss
                        storage.clear_all()
                
                elif op == "stats":
                    stats = storage.get_stats()
                    # No problem
                
                with lock:
                    operations[0] += 1
                latency = time.time() - start
                bug_tracker.log_operation(thread_name, "STORAGE", op, "success", latency)
                
                # Random sleep to create chaos
                if random.random() < 0.1:
                    time.sleep(random.random() * 0.005)
                
            except Exception as e:
                with lock:
                    errors[0] += 1
                bug_tracker.log_error("STORAGE", "HIGH", f"Worker {worker_id} failed", e)
    
    print(f"Starting {num_threads} workers...")
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    print(f"Running for {duration_seconds} seconds...")
    for _ in range(duration_seconds // 5):
        time.sleep(5)
        with lock:
            print(f"  Progress: {operations[0]:,} operations, {errors[0]} errors")
    
    print("\nStopping workers...")
    stop_event.set()
    
    for t in threads:
        t.join(timeout=10)
    
    print(f"\nDone! Total operations: {operations[0]:,}, Total errors: {errors[0]}")
    return errors[0]


def test_version_chaos(duration_seconds=90, num_threads=30):
    """极端版本管理混沌测试"""
    print("\n" + "=" * 120)
    print(f"VERSION MANAGER EXTREME CHAOS TEST - {num_threads} threads for {duration_seconds} seconds")
    print("=" * 120)
    
    vm = VersionManager()
    stop_event = threading.Event()
    threads = []
    errors = [0]
    lock = threading.Lock()
    operations = [0]
    
    def worker(worker_id):
        thread_name = f"VersionWorker-{worker_id}"
        while not stop_event.is_set():
            try:
                start = time.time()
                wf_id = f"workflow_{random.randint(1, 50)}"
                
                op = random.choice(["create", "list", "get", "latest", "activate"])
                
                if op == "create":
                    vm.create_version(
                        wf_id,
                        {"step": random.randint(1, 1000), "data": chaos.random_content()}
                    )
                
                elif op == "list":
                    vm.list_versions(wf_id)
                
                elif op == "get":
                    versions = vm.list_versions(wf_id)
                    if versions:
                        vm.get_version(random.choice(versions))
                
                elif op == "latest":
                    vm.get_latest_version(wf_id)
                
                elif op == "activate":
                    versions = vm.list_versions(wf_id)
                    if versions:
                        vm.activate_version(random.choice(versions))
                
                with lock:
                    operations[0] += 1
                latency = time.time() - start
                bug_tracker.log_operation(thread_name, "VERSION", op, "success", latency)
                
                if random.random() < 0.1:
                    time.sleep(random.random() * 0.005)
                
            except Exception as e:
                with lock:
                    errors[0] += 1
                bug_tracker.log_error("VERSION", "HIGH", f"Worker {worker_id} failed", e)
    
    print(f"Starting {num_threads} workers...")
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    print(f"Running for {duration_seconds} seconds...")
    for _ in range(duration_seconds // 5):
        time.sleep(5)
        with lock:
            print(f"  Progress: {operations[0]:,} operations, {errors[0]} errors")
    
    print("\nStopping workers...")
    stop_event.set()
    
    for t in threads:
        t.join(timeout=10)
    
    print(f"\nDone! Total operations: {operations[0]:,}, Total errors: {errors[0]}")
    return errors[0]


def test_analytics_chaos(duration_seconds=60, num_threads=40):
    """极端分析引擎混沌测试"""
    print("\n" + "=" * 120)
    print(f"ANALYTICS ENGINE EXTREME CHAOS TEST - {num_threads} threads for {duration_seconds} seconds")
    print("=" * 120)
    
    analytics = AnalyticsEngine()
    stop_event = threading.Event()
    threads = []
    errors = [0]
    lock = threading.Lock()
    operations = [0]
    
    def worker(worker_id):
        thread_name = f"AnalyticsWorker-{worker_id}"
        while not stop_event.is_set():
            try:
                start = time.time()
                metric_name = f"metric_{random.randint(1, 50)}"
                
                value = random.choice([
                    random.random(),
                    0.0,
                    float("inf"),
                    float("-inf"),
                    float("nan"),
                    random.randint(-100000, 100000),
                    random.randint(-1000, 1000) / 100.0
                ])
                
                analytics.record_metric(metric_name, value)
                
                if random.random() < 0.1:
                    analytics.get_summary()
                
                with lock:
                    operations[0] += 1
                latency = time.time() - start
                bug_tracker.log_operation(thread_name, "ANALYTICS", "record", "success", latency)
                
                if random.random() < 0.1:
                    time.sleep(random.random() * 0.003)
                
            except Exception as e:
                with lock:
                    errors[0] += 1
                bug_tracker.log_error("ANALYTICS", "HIGH", f"Worker {worker_id} failed", e)
    
    print(f"Starting {num_threads} workers...")
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    print(f"Running for {duration_seconds} seconds...")
    for _ in range(duration_seconds // 5):
        time.sleep(5)
        with lock:
            print(f"  Progress: {operations[0]:,} operations, {errors[0]} errors")
    
    print("\nStopping workers...")
    stop_event.set()
    
    for t in threads:
        t.join(timeout=10)
    
    print(f"\nDone! Total operations: {operations[0]:,}, Total errors: {errors[0]}")
    return errors[0]


def test_cross_integration_chaos(duration_seconds=180, num_threads=100):
    """跨组件集成极端混沌测试"""
    print("\n" + "=" * 120)
    print(f"CROSS-INTEGRATION EXTREME CHAOS TEST - {num_threads} threads for {duration_seconds} seconds")
    print("=" * 120)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    
    stop_event = threading.Event()
    threads = []
    errors = [0]
    lock = threading.Lock()
    operations = [0]
    
    def worker(worker_id):
        thread_name = f"IntWorker-{worker_id}"
        while not stop_event.is_set():
            try:
                start = time.time()
                
                # Complex operation that uses multiple components
                user = chaos.random_user()
                session = chaos.random_session()
                wf_id = f"workflow_{random.randint(1, 30)}"
                
                # 1. Record metric
                analytics.record_metric(f"ops_for_{user}", float(random.randint(1, 100)))
                
                # 2. Create version
                version = vm.create_version(wf_id, {"user": user, "step": random.randint(1, 100)})
                
                # 3. Save message with version info
                success = storage.save_message(
                    user,
                    {"content": f"Version created: {version.id}", "version_id": version.id, "session_id": session}
                )
                
                # 4. Verify retrieval
                storage.get_conversation(user, session)
                
                # 5. Another metric
                analytics.record_metric("total_transactions", 1.0)
                
                with lock:
                    operations[0] += 1
                latency = time.time() - start
                bug_tracker.log_operation(thread_name, "INTEGRATION", "complex", "success", latency)
                
                if random.random() < 0.15:
                    time.sleep(random.random() * 0.01)
                
            except Exception as e:
                with lock:
                    errors[0] += 1
                bug_tracker.log_error("INTEGRATION", "CRITICAL", f"Worker {worker_id} failed", e)
    
    print(f"Starting {num_threads} workers...")
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    print(f"Running for {duration_seconds} seconds...")
    for i in range(duration_seconds // 10):
        time.sleep(10)
        with lock:
            print(f"  Progress: {operations[0]:,} operations, {errors[0]} errors")
            # Check stats
            stats = storage.get_stats()
            print(f"    Storage stats: {stats}")
            anal_summary = analytics.get_summary()
            print(f"    Analytics stats: {anal_summary['total_metrics']} metrics")
    
    print("\nStopping workers...")
    stop_event.set()
    
    for t in threads:
        t.join(timeout=10)
    
    print(f"\nDone! Total operations: {operations[0]:,}, Total errors: {errors[0]}")
    return errors[0]


def test_extreme_cleanup_chaos():
    """极端清理混沌测试"""
    print("\n" + "=" * 120)
    print("EXTREME CLEANUP & RESOURCE LEAK TEST")
    print("=" * 120)
    
    errors = 0
    
    try:
        for i in range(100):
            # Create and cleanup storage
            storage = InMemoryChatStorage()
            for j in range(100):
                storage.save_message(f"temp_user_{i}", {"content": f"temp_{j}"})
            storage.clear_all()
            del storage
        
        # Do the same for version manager
        for i in range(100):
            vm = VersionManager()
            for j in range(50):
                vm.create_version(f"temp_wf_{i}", {"temp": j})
            vm.cleanup()
            del vm
        
        # And analytics
        for i in range(100):
            analytics = AnalyticsEngine()
            for j in range(50):
                analytics.record_metric(f"temp_metric_{i}", float(j))
            analytics.cleanup()
            del analytics
        
        # Force GC
        gc.collect()
        
        print(f"  Created & destroyed 300 objects, {100*(100+50+50)} operations, no errors")
        
    except Exception as e:
        errors += 1
        bug_tracker.log_error("CLEANUP", "HIGH", "Resource cleanup test failed", e)
    
    print(f"\nExtreme cleanup test complete! Errors: {errors}")
    return errors


def main():
    """主测试函数"""
    print("=" * 120)
    print("MAOS SYSTEM - EXTREME CHAOS & COMPLEX SCENARIO TEST")
    print("=" * 120)
    print(f"Start time: {datetime.now().isoformat()}")
    
    # ======================================================
    # RUN ALL EXTREME TESTS
    # ======================================================
    
    # 1. Extreme storage chaos
    test_extreme_storage_chaos(duration_seconds=30, num_threads=30)
    
    # 2. Extreme version chaos
    test_version_chaos(duration_seconds=20, num_threads=20)
    
    # 3. Extreme analytics chaos
    test_analytics_chaos(duration_seconds=15, num_threads=25)
    
    # 4. Extreme cleanup
    test_extreme_cleanup_chaos()
    
    # 5. Cross-integration (most important)
    test_cross_integration_chaos(duration_seconds=60, num_threads=50)
    
    # ======================================================
    # FINAL REPORT
    # ======================================================
    exit_code = bug_tracker.summary_report()
    
    print("\n" + "=" * 120)
    print(f"End time: {datetime.now().isoformat()}")
    print("=" * 120)
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
