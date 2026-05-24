#!/usr/bin/env python3
"""
MAOS - 超长时间持续压力测试 v2.0
Super Long Duration Stress Test v2.0
目标：10分钟+ 持续压力，100+线程，更多混沌因素
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
import weakref
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import tracemalloc
import psutil

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine


class UltraLongStressTest:
    """超长时间持续压力测试"""
    
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
            "error_count": 0,
            "warning_count": 0,
            "start_time": None,
            "last_check_time": None,
            "memory_peak_mb": 0,
            "cpu_percent": 0
        }
        
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        tracemalloc.start()
    
    def _monitor_resources(self):
        """监控资源使用"""
        process = psutil.Process()
        while not self.stop_event.is_set():
            try:
                # 监控内存
                mem_info = process.memory_info()
                mem_mb = mem_info.rss / 1024 / 1024
                
                with self.lock:
                    self.stats["memory_peak_mb"] = max(self.stats["memory_peak_mb"], mem_mb)
                    self.stats["cpu_percent"] = process.cpu_percent(interval=1)
                
                # 触发GC
                if random.random() < 0.05:  # 5% chance
                    gc.collect()
                
                time.sleep(5)
                
            except Exception as e:
                print(f"[MONITOR ERROR] {type(e).__name__}: {e}")
                time.sleep(5)
    
    def log_error(self, component, operation, error):
        """记录错误"""
        with self.lock:
            self.errors.append({
                "time": datetime.now(),
                "component": component,
                "operation": operation,
                "error_type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            })
            self.stats["error_count"] += 1
            print(f"[ERROR] [{component}] [{operation}] {type(error).__name__}: {str(error)}")
    
    def log_warning(self, component, message):
        """记录警告"""
        with self.lock:
            self.warnings.append({
                "time": datetime.now(),
                "component": component,
                "message": message
            })
            self.stats["warning_count"] += 1
    
    def worker_storage(self, worker_id, duration_seconds):
        """存储工作线程"""
        thread_name = f"Storage-{worker_id}"
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        # 随机选择用户和会话
        users = [f"user_{i}" for i in range(100)]
        sessions = [f"session_{i}" for i in range(30)]
        agents = [f"agent_{i}" for i in range(10)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                # 随机操作组合
                op_type = random.choice([
                    "save_only",
                    "save_and_read",
                    "save_read_stats",
                    "save_with_timestamp",
                    "save_with_special_content"
                ])
                
                user = random.choice(users)
                session = random.choice(sessions)
                agent = random.choice(agents)
                
                if op_type == "save_only":
                    self.storage.save_message(
                        user,
                        {"content": f"Msg {local_ops}", "session_id": session, "agent_id": agent}
                    )
                
                elif op_type == "save_and_read":
                    self.storage.save_message(
                        user,
                        {"content": f"Msg {local_ops}", "session_id": session, "agent_id": agent}
                    )
                    self.storage.get_conversation(user, session, agent)
                
                elif op_type == "save_read_stats":
                    self.storage.save_message(
                        user,
                        {"content": f"Msg {local_ops}", "session_id": session, "agent_id": agent}
                    )
                    self.storage.get_conversation(user, session, agent)
                    self.storage.get_stats()
                
                elif op_type == "save_with_timestamp":
                    # 随机时间戳
                    ts = random.choice([
                        time.time(),
                        time.time() - random.randint(0, 86400*365),
                        time.time() + random.randint(0, 86400*30),
                        random.uniform(-1e10, 1e10),
                        0,
                        float('inf') if random.random() < 0.1 else time.time()
                    ])
                    self.storage.save_message(
                        user,
                        {"content": f"Msg {local_ops}", "session_id": session, "agent_id": agent, "timestamp": ts}
                    )
                
                elif op_type == "save_with_special_content":
                    # 特殊内容
                    content = random.choice([
                        "",  # 空
                        None,  # None
                        "x" * random.randint(1, 50000),  # 大内容
                        "🎉🎊🎁🎀🎄🎅🎆🎇🎈" * 10,  # Unicode
                        "\x00\x01\x02\x03\x04",  # 控制字符
                        "中文日本語한국어" * 20,  # 多语言
                        {"nested": {"deep": [1, 2, None, {"a": "b"}]}},  # 嵌套字典
                    ])
                    self.storage.save_message(
                        user,
                        {"content": content, "session_id": session, "agent_id": agent}
                    )
                
                local_ops += 1
                
                # 随机小延迟
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                
            except Exception as e:
                self.log_error("STORAGE", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["storage_ops"] += local_ops
            self.stats["total_operations"] += local_ops
    
    def worker_version(self, worker_id, duration_seconds):
        """版本管理工作线程"""
        thread_name = f"Version-{worker_id}"
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        workflows = [f"workflow_{i}" for i in range(50)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                op_type = random.choice(["create", "list", "get", "latest", "activate"])
                wf_id = random.choice(workflows)
                
                if op_type == "create":
                    self.vm.create_version(
                        wf_id,
                        {
                            "step": random.randint(1, 1000),
                            "data": f"Version data {local_ops}",
                            "metadata": {"created_by": thread_name, "timestamp": time.time()}
                        }
                    )
                
                elif op_type == "list":
                    self.vm.list_versions(wf_id)
                
                elif op_type == "get":
                    versions = self.vm.list_versions(wf_id)
                    if versions:
                        self.vm.get_version(random.choice(versions))
                
                elif op_type == "latest":
                    self.vm.get_latest_version(wf_id)
                
                elif op_type == "activate":
                    versions = self.vm.list_versions(wf_id)
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
    
    def worker_analytics(self, worker_id, duration_seconds):
        """分析引擎工作线程"""
        thread_name = f"Analytics-{worker_id}"
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        metrics = [f"metric_{i}" for i in range(50)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                op_type = random.choice(["record", "record_and_summary"])
                metric = random.choice(metrics)
                
                # 随机值
                value = random.choice([
                    random.random(),
                    0.0,
                    float("inf"),
                    float("-inf"),
                    float("nan"),
                    random.randint(-1000000, 1000000),
                    random.randint(-1000, 1000) / 100.0,
                    1e20,
                    -1e20,
                    None
                ])
                
                self.analytics.record_metric(metric, value)
                
                if op_type == "record_and_summary" and random.random() < 0.3:
                    self.analytics.get_summary()
                
                local_ops += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.001))
                
            except Exception as e:
                self.log_error("ANALYTICS", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["analytics_ops"] += local_ops
            self.stats["total_operations"] += local_ops
    
    def worker_integration(self, worker_id, duration_seconds):
        """集成工作线程 - 跨组件操作"""
        thread_name = f"Integration-{worker_id}"
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        users = [f"user_{i}" for i in range(100)]
        workflows = [f"workflow_{i}" for i in range(50)]
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                user = random.choice(users)
                session = f"session_{random.randint(0, 30)}"
                agent = f"agent_{random.randint(0, 10)}"
                wf_id = random.choice(workflows)
                
                # 完整的业务流程
                # 1. 创建版本
                version = self.vm.create_version(wf_id, {
                    "user": user,
                    "session": session,
                    "step": random.randint(1, 100)
                })
                
                # 2. 保存消息
                self.storage.save_message(
                    user,
                    {
                        "content": f"Processing version {version.id}",
                        "session_id": session,
                        "agent_id": agent,
                        "version_id": version.id
                    }
                )
                
                # 3. 记录指标
                self.analytics.record_metric(f"workflow_{wf_id}", 1.0)
                self.analytics.record_metric(f"user_{user}", 1.0)
                
                # 4. 检索验证
                conv = self.storage.get_conversation(user, session, agent)
                versions = self.vm.list_versions(wf_id)
                
                local_ops += 1
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0, 0.002))
                
            except Exception as e:
                self.log_error("INTEGRATION", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["total_operations"] += local_ops
    
    def worker_chaos(self, worker_id, duration_seconds):
        """混沌工作线程 - 各种极端操作"""
        thread_name = f"Chaos-{worker_id}"
        end_time = time.time() + duration_seconds
        local_ops = 0
        
        while time.time() < end_time and not self.stop_event.is_set():
            try:
                # 随机选择操作类型
                chaos_type = random.choice([
                    "rapid_create_destroy",
                    "memory_pressure",
                    "nested_operations",
                    "concurrent_clear",
                    "race_condition",
                    "extreme_data"
                ])
                
                if chaos_type == "rapid_create_destroy":
                    # 快速创建和销毁
                    for _ in range(random.randint(10, 50)):
                        temp_storage = InMemoryChatStorage()
                        for i in range(10):
                            temp_storage.save_message("temp", {"content": f"temp_{i}"})
                        del temp_storage
                        local_ops += 10
                
                elif chaos_type == "memory_pressure":
                    # 内存压力
                    data = []
                    for _ in range(random.randint(100, 1000)):
                        data.append("x" * random.randint(100, 1000))
                    self.storage.save_message(
                        "memory_test",
                        {"content": f"Data size: {len(data)}", "session_id": "memory"}
                    )
                    del data
                    local_ops += 1
                
                elif chaos_type == "nested_operations":
                    # 嵌套操作
                    for _ in range(5):
                        user = f"nested_user_{random.randint(1, 10)}"
                        for i in range(10):
                            self.storage.save_message(user, {"content": f"Nested {i}"})
                        for i in range(5):
                            self.storage.get_conversation(user)
                        local_ops += 15
                
                elif chaos_type == "concurrent_clear":
                    # 并发清理（低概率）
                    if random.random() < 0.01:
                        self.storage.clear_all()
                        self.vm.cleanup()
                        self.analytics.cleanup()
                        local_ops += 1
                
                elif chaos_type == "race_condition":
                    # 竞态条件测试
                    users = [f"race_user_{i}" for i in range(10)]
                    user = random.choice(users)
                    threads = []
                    for i in range(10):
                        def rapid_save(n):
                            for j in range(5):
                                self.storage.save_message(user, {"content": f"Race {n}_{j}"})
                        t = threading.Thread(target=rapid_save, args=(i,))
                        threads.append(t)
                        t.start()
                    for t in threads:
                        t.join()
                    local_ops += 50
                
                elif chaos_type == "extreme_data":
                    # 极端数据
                    extreme_content = random.choice([
                        "x" * 100000,  # 100KB
                        "\x00" * 10000,  # 空字节
                        "文" * 50000,  # 中文
                        None,
                        {"deep": {"nested": {"data": "x" * 10000}}},
                    ])
                    self.storage.save_message("extreme", {"content": extreme_content})
                    local_ops += 1
                
                # 随机延迟
                time.sleep(random.uniform(0, 0.01))
                
            except Exception as e:
                self.log_error("CHAOS", f"worker-{worker_id}", e)
        
        with self.lock:
            self.stats["total_operations"] += local_ops
    
    def run_test(self, duration_seconds=600, num_storage_workers=30, num_version_workers=20, 
                 num_analytics_workers=20, num_integration_workers=15, num_chaos_workers=15):
        """运行超长时间压力测试"""
        
        print("=" * 120)
        print("🚀 MAOS ULTRA LONG DURATION STRESS TEST v2.0")
        print("=" * 120)
        print(f"Duration: {duration_seconds} seconds ({duration_seconds/60:.1f} minutes)")
        print(f"Workers: Storage={num_storage_workers}, Version={num_version_workers}, "
              f"Analytics={num_analytics_workers}, Integration={num_integration_workers}, Chaos={num_chaos_workers}")
        print(f"Total Workers: {num_storage_workers + num_version_workers + num_analytics_workers + num_integration_workers + num_chaos_workers}")
        print()
        
        self.stats["start_time"] = datetime.now()
        
        threads = []
        
        # 启动存储工作线程
        print(f"Starting {num_storage_workers} storage workers...")
        for i in range(num_storage_workers):
            t = threading.Thread(target=self.worker_storage, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动版本管理工作线程
        print(f"Starting {num_version_workers} version workers...")
        for i in range(num_version_workers):
            t = threading.Thread(target=self.worker_version, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动分析引擎工作线程
        print(f"Starting {num_analytics_workers} analytics workers...")
        for i in range(num_analytics_workers):
            t = threading.Thread(target=self.worker_analytics, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动集成工作线程
        print(f"Starting {num_integration_workers} integration workers...")
        for i in range(num_integration_workers):
            t = threading.Thread(target=self.worker_integration, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 启动混沌工作线程
        print(f"Starting {num_chaos_workers} chaos workers...")
        for i in range(num_chaos_workers):
            t = threading.Thread(target=self.worker_chaos, args=(i, duration_seconds))
            threads.append(t)
            t.start()
        
        # 监控进度
        print("\nRunning test...")
        start_time = time.time()
        last_update = start_time
        
        while time.time() - start_time < duration_seconds:
            time.sleep(10)  # 每10秒更新一次
            
            elapsed = time.time() - start_time
            with self.lock:
                total_ops = self.stats["total_operations"]
                errors = self.stats["error_count"]
                warnings = self.stats["warning_count"]
                memory_mb = self.stats["memory_peak_mb"]
                ops_per_sec = total_ops / max(elapsed, 1)
            
            # 获取当前快照内存
            snapshot = tracemalloc.take_snapshot()
            current_mem = sum(stat.size for stat in snapshot.statistics('lineno')) / 1024 / 1024
            
            print(f"[{elapsed:.0f}s / {duration_seconds}s] "
                  f"Ops: {total_ops:,} ({ops_per_sec:.0f}/s) | "
                  f"Errors: {errors} | Warnings: {warnings} | "
                  f"Memory: {memory_mb:.1f}MB (current: {current_mem:.1f}MB)")
        
        # 停止测试
        print("\nStopping test...")
        self.stop_event.set()
        
        # 等待所有线程结束
        for t in threads:
            t.join(timeout=30)
        
        # 最终GC
        gc.collect()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 打印最终结果
        self.print_final_report(duration)
    
    def print_final_report(self, duration):
        """打印最终报告"""
        print("\n" + "=" * 120)
        print("📊 FINAL REPORT - ULTRA LONG DURATION STRESS TEST")
        print("=" * 120)
        
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
        
        print(f"\n❌ ERRORS:")
        print(f"  Total Errors: {stats['error_count']}")
        if self.errors:
            print(f"  Error Rate: {stats['error_count'] / max(total_ops, 1) * 100:.6f}%")
            print("\n  Error Details:")
            for i, err in enumerate(self.errors[:10], 1):
                print(f"    {i}. [{err['component']}] [{err['operation']}]")
                print(f"       {err['error_type']}: {err['message'][:100]}")
        
        print(f"\n⚠️  WARNINGS:")
        print(f"  Total Warnings: {stats['warning_count']}")
        if self.warnings:
            for i, warn in enumerate(self.warnings[:5], 1):
                print(f"    {i}. [{warn['component']}] {warn['message']}")
        
        print(f"\n💾 RESOURCE USAGE:")
        print(f"  Peak Memory: {stats['memory_peak_mb']:.2f} MB")
        
        # 内存快照
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        print(f"  Top Memory Allocation:")
        for stat in top_stats[:5]:
            print(f"    {stat.size / 1024:.1f} KB: {stat}")
        
        # 存储统计
        storage_stats = self.storage.get_stats()
        print(f"\n💬 STORAGE:")
        print(f"  Conversations: {storage_stats.get('conversation_count', 0):,}")
        print(f"  Sessions: {storage_stats.get('session_count', 0):,}")
        print(f"  Total Messages: {storage_stats.get('total_messages', 0):,}")
        
        # 版本统计
        print(f"\n📝 VERSION MANAGER:")
        print(f"  Workflows: {len(self.vm.versions)}")
        
        # 分析统计
        analytics_summary = self.analytics.get_summary()
        print(f"\n📊 ANALYTICS:")
        print(f"  Total Metrics: {analytics_summary.get('total_metrics', 0):,}")
        
        print("\n" + "=" * 120)
        
        if stats["error_count"] == 0:
            print("✅✅✅ EXCELLENT! ZERO ERRORS IN ULTRA LONG DURATION TEST! ✅✅✅")
            print(f"System handled {total_ops:,} operations in {duration/60:.1f} minutes with 0 errors!")
            return 0
        else:
            print(f"⚠️  Found {stats['error_count']} errors during test!")
            return 1


def main():
    """主函数"""
    print("=" * 120)
    print("🚀 MAOS ULTRA LONG DURATION STRESS TEST v2.0")
    print("测试目标：10分钟持续压力，100+线程，更多混沌因素")
    print("=" * 120)
    print()
    
    test = UltraLongStressTest()
    
    # 运行10分钟压力测试
    exit_code = test.run_test(
        duration_seconds=600,  # 10分钟
        num_storage_workers=30,
        num_version_workers=20,
        num_analytics_workers=20,
        num_integration_workers=15,
        num_chaos_workers=15
    )
    
    print("\n" + "=" * 120)
    print(f"Test completed at: {datetime.now().isoformat()}")
    print("=" * 120)
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
