#!/usr/bin/env python3
"""
MAOS - 第二阶段：超大规模并发测试
Phase 2: Ultra-Large-Scale Concurrency Testing
目标：200+线程、1000万+操作、长时间持续压力
"""

import sys
import time
import random
import threading
import gc
import traceback
from datetime import datetime, timedelta
from collections import defaultdict, deque

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine


class UltraLargeScaleConcurrencyTest:
    """超大规模并发测试"""
    
    def __init__(self):
        self.storage = InMemoryChatStorage()
        self.vm = VersionManager()
        self.analytics = AnalyticsEngine()
        
        self.errors = []
        self.warnings = []
        self.stats = {
            "total_operations": 0,
            "storage_ops": 0,
            "version_ops": 0,
            "analytics_ops": 0,
            "integration_ops": 0,
            "error_count": 0,
            "start_time": None,
            "memory_peak_mb": 0,
            "threads_active": 0
        }
        
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # 监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def _monitor_resources(self):
        """资源监控"""
        import psutil
        import tracemalloc
        
        process = psutil.Process()
        tracemalloc.start()
        
        while not self.stop_event.is_set():
            try:
                mem_info = process.memory_info()
                mem_mb = mem_info.rss / 1024 / 1024
                
                snapshot = tracemalloc.take_snapshot()
                current_mb = sum(stat.size for stat in snapshot.statistics('lineno')) / 1024 / 1024
                
                with self.lock:
                    self.stats["memory_peak_mb"] = max(self.stats["memory_peak_mb"], mem_mb)
                    self.stats["threads_active"] = threading.active_count()
                
                if random.random() < 0.1:
                    gc.collect()
                
                time.sleep(5)
                
            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
                time.sleep(5)
    
    def log_error(self, component, operation, error):
        """记录错误"""
        with self.lock:
            self.errors.append({
                "timestamp": datetime.now(),
                "component": component,
                "operation": operation,
                "error_type": type(error).__name__,
                "message": str(error)
            })
            self.stats["error_count"] += 1
    
    def worker_storage_massive(self, worker_id, duration_seconds):
        """大规模存储工作线程"""
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        users = [f"user_{i}" for i in range(500)]
        sessions = [f"session_{i}" for i in range(200)]
        agents = [f"agent_{i}" for i in range(50)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                user = random.choice(users)
                session = random.choice(sessions)
                agent = random.choice(agents)
                
                op = random.choice(["save", "save_and_read", "save_with_stats"])
                
                if op == "save":
                    self.storage.save_message(user, {
                        "content": f"Msg {local_ops} from worker {worker_id}",
                        "session_id": session,
                        "agent_id": agent,
                        "timestamp": time.time() + random.randint(-100000, 100000)
                    })
                
                elif op == "save_and_read":
                    self.storage.save_message(user, {
                        "content": f"Msg {local_ops}",
                        "session_id": session,
                        "agent_id": agent
                    })
                    self.storage.get_conversation(user, session, agent)
                
                elif op == "save_with_stats":
                    self.storage.save_message(user, {
                        "content": f"Msg {local_ops}",
                        "session_id": session,
                        "agent_id": agent
                    })
                    self.storage.get_conversation(user, session, agent)
                    self.storage.get_stats()
                
                local_ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                
            except Exception as e:
                self.log_error("STORAGE", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["storage_ops"] += local_ops
            self.stats["total_operations"] += local_ops
    
    def worker_version_massive(self, worker_id, duration_seconds):
        """大规模版本管理工作线程"""
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        workflows = [f"workflow_{i}" for i in range(300)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                wf = random.choice(workflows)
                
                op = random.choice(["create", "list", "get", "latest", "activate"])
                
                if op == "create":
                    self.vm.create_version(wf, {
                        "step": local_ops,
                        "worker": worker_id,
                        "timestamp": time.time()
                    })
                
                elif op == "list":
                    self.vm.list_versions(wf)
                
                elif op == "get":
                    versions = self.vm.list_versions(wf)
                    if versions:
                        self.vm.get_version(random.choice(versions))
                
                elif op == "latest":
                    self.vm.get_latest_version(wf)
                
                elif op == "activate":
                    versions = self.vm.list_versions(wf)
                    if versions:
                        self.vm.activate_version(random.choice(versions))
                
                local_ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                
            except Exception as e:
                self.log_error("VERSION", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["version_ops"] += local_ops
            self.stats["total_operations"] += local_ops
    
    def worker_analytics_massive(self, worker_id, duration_seconds):
        """大规模分析引擎工作线程"""
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        metrics = [f"metric_{i}" for i in range(300)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                metric = random.choice(metrics)
                
                value = random.choice([
                    random.random(),
                    0.0,
                    float("inf"),
                    float("-inf"),
                    float("nan"),
                    random.randint(-1000000, 1000000),
                    1e20,
                    -1e20
                ])
                
                self.analytics.record_metric(metric, value)
                
                if random.random() < 0.2:
                    self.analytics.get_summary()
                
                local_ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                
            except Exception as e:
                self.log_error("ANALYTICS", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["analytics_ops"] += local_ops
            self.stats["total_operations"] += local_ops
    
    def worker_integration_massive(self, worker_id, duration_seconds):
        """大规模集成工作线程"""
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        users = [f"user_{i}" for i in range(500)]
        workflows = [f"workflow_{i}" for i in range(300)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                user = random.choice(users)
                wf = random.choice(workflows)
                session = f"session_{random.randint(0, 200)}"
                agent = f"agent_{random.randint(0, 50)}"
                
                # 完整业务流程
                version = self.vm.create_version(wf, {
                    "user": user,
                    "session": session,
                    "worker": worker_id
                })
                
                self.storage.save_message(user, {
                    "content": f"Processing version {version.id}",
                    "session_id": session,
                    "agent_id": agent,
                    "version_id": version.id
                })
                
                self.analytics.record_metric(f"workflow_{wf}", 1.0)
                self.analytics.record_metric(f"user_{user}", 1.0)
                
                # 验证
                conv = self.storage.get_conversation(user, session, agent)
                versions = self.vm.list_versions(wf)
                
                local_ops += 1
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0, 0.002))
                
            except Exception as e:
                self.log_error("INTEGRATION", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["integration_ops"] += local_ops
            self.stats["total_operations"] += local_ops
    
    def run_test(self, duration_seconds=300, num_storage=80, num_version=50, 
                 num_analytics=40, num_integration=30):
        """运行超大规模并发测试"""
        
        print("=" * 140)
        print("🚀 第二阶段：超大规模并发测试")
        print("=" * 140)
        print(f"Duration: {duration_seconds} seconds ({duration_seconds/60:.1f} minutes)")
        print(f"Workers: Storage={num_storage}, Version={num_version}, "
              f"Analytics={num_analytics}, Integration={num_integration}")
        print(f"Total Workers: {num_storage + num_version + num_analytics + num_integration}")
        print()
        
        self.stats["start_time"] = datetime.now()
        
        threads = []
        
        # 启动存储工作线程
        print(f"Starting {num_storage} storage workers...")
        for i in range(num_storage):
            t = threading.Thread(target=self.worker_storage_massive, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动版本管理工作线程
        print(f"Starting {num_version} version workers...")
        for i in range(num_version):
            t = threading.Thread(target=self.worker_version_massive, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动分析引擎工作线程
        print(f"Starting {num_analytics} analytics workers...")
        for i in range(num_analytics):
            t = threading.Thread(target=self.worker_analytics_massive, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动集成工作线程
        print(f"Starting {num_integration} integration workers...")
        for i in range(num_integration):
            t = threading.Thread(target=self.worker_integration_massive, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 监控进度
        print("\nRunning test...")
        start_time = time.time()
        last_update = start_time
        
        while time.time() - start_time < duration_seconds:
            time.sleep(15)  # 每15秒更新一次
            
            elapsed = time.time() - start_time
            with self.lock:
                total_ops = self.stats["total_operations"]
                errors = self.stats["error_count"]
                memory_mb = self.stats["memory_peak_mb"]
                ops_per_sec = total_ops / max(elapsed, 1)
            
            print(f"[{elapsed:.0f}s / {duration_seconds}s] "
                  f"Ops: {total_ops:,} ({ops_per_sec:.0f}/s) | "
                  f"Errors: {errors} | "
                  f"Memory: {memory_mb:.1f}MB")
        
        # 停止测试
        print("\nStopping test...")
        self.stop_event.set()
        
        # 等待所有线程结束
        for t in threads:
            t.join(timeout=30)
        
        gc.collect()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 打印最终结果
        self.print_final_report(duration)
    
    def print_final_report(self, duration):
        """打印最终报告"""
        print("\n" + "=" * 140)
        print("📊 第二阶段测试报告 - 超大规模并发")
        print("=" * 140)
        
        with self.lock:
            stats = self.stats.copy()
        
        total_ops = stats["total_operations"]
        ops_per_sec = total_ops / max(duration, 1)
        
        print(f"\n📈 OPERATIONS:")
        print(f"  Total Operations: {total_ops:,}")
        print(f"  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"  Throughput: {ops_per_sec:.2f} ops/s")
        print(f"  Storage Ops: {stats['storage_ops']:,}")
        print(f"  Version Ops: {stats['version_ops']:,}")
        print(f"  Analytics Ops: {stats['analytics_ops']:,}")
        print(f"  Integration Ops: {stats['integration_ops']:,}")
        
        print(f"\n❌ ERRORS:")
        print(f"  Total Errors: {stats['error_count']}")
        if self.errors:
            print(f"  Error Rate: {stats['error_count'] / max(total_ops, 1) * 100:.6f}%")
            print("\n  Error Details:")
            for i, err in enumerate(self.errors[:10], 1):
                print(f"    {i}. [{err['component']}] [{err['operation']}]")
                print(f"       {err['error_type']}: {err['message'][:100]}")
        
        print(f"\n💾 RESOURCE USAGE:")
        print(f"  Peak Memory: {stats['memory_peak_mb']:.2f} MB")
        
        # 存储统计
        storage_stats = self.storage.get_stats()
        print(f"\n💬 STORAGE:")
        print(f"  Conversations: {storage_stats.get('conversation_count', 0):,}")
        print(f"  Sessions: {storage_stats.get('session_count', 0):,}")
        print(f"  Total Messages: {storage_stats.get('total_messages', 0):,}")
        
        # 版本统计
        print(f"\n📝 VERSION MANAGER:")
        print(f"  Workflows: {len(self.vm.versions) if hasattr(self.vm, 'versions') else 'N/A'}")
        
        # 分析统计
        analytics_summary = self.analytics.get_summary()
        print(f"\n📊 ANALYTICS:")
        print(f"  Total Metrics: {analytics_summary.get('total_metrics', 0):,}")
        
        print("\n" + "=" * 140)
        
        if stats["error_count"] == 0:
            print("✅✅✅ EXCELLENT! ZERO ERRORS IN ULTRA-LARGE-SCALE TEST! ✅✅✅")
            print(f"System handled {total_ops:,} operations with {ops_per_sec:.0f} ops/s throughput!")
            return 0
        else:
            print(f"⚠️  Found {stats['error_count']} errors during test!")
            return 1


def main():
    """主函数"""
    print("=" * 140)
    print("🚀 MAOS 第二阶段：超大规模并发测试")
    print("测试目标：200线程、300秒持续压力、1000万+操作")
    print("=" * 140)
    print()
    
    test = UltraLargeScaleConcurrencyTest()
    
    # 运行5分钟超大规模测试
    exit_code = test.run_test(
        duration_seconds=300,  # 5分钟
        num_storage=80,
        num_version=50,
        num_analytics=40,
        num_integration=30
    )
    
    print("\n" + "=" * 140)
    print(f"Test completed at: {datetime.now().isoformat()}")
    print("=" * 140)
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
