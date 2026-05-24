#!/usr/bin/env python3
"""
MAOS 超长时间深度混沌测试框架 v7.0
可持续运行数小时，包含真实业务流程和极端混乱场景
遵循慢工出细活原则 - 深入发现和修复问题
"""

import sys
import os
import time
import random
import threading
import gc
import traceback
import uuid
import weakref
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class SystemMetrics:
    """系统指标监控"""
    
    def __init__(self):
        self.process = None
        try:
            import psutil
            self.process = psutil.Process(os.getpid())
        except ImportError:
            print("⚠️  psutil 不可用，无法监控系统指标")
        
        self.start_memory = 0
        self.start_time = time.time()
        self.peak_memory = 0
        self.samples = []
        self.lock = threading.Lock()
    
    def sample(self, label: str = ""):
        """采样系统指标"""
        if not self.process:
            return
        
        try:
            mem_mb = self.process.memory_info().rss / 1024 / 1024
            cpu = self.process.cpu_percent(0.01)
            num_threads = self.process.num_threads()
            
            with self.lock:
                self.samples.append({
                    "timestamp": datetime.now().isoformat(),
                    "label": label,
                    "memory_mb": mem_mb,
                    "cpu_percent": cpu,
                    "threads": num_threads
                })
                
                if mem_mb > self.peak_memory:
                    self.peak_memory = mem_mb
        except Exception:
            pass
    
    def get_summary(self):
        """获取监控摘要"""
        with self.lock:
            if not self.samples:
                return {"duration_sec": time.time() - self.start_time}
            
            last_sample = self.samples[-1]
            return {
                "duration_sec": time.time() - self.start_time,
                "samples": len(self.samples),
                "start_memory_mb": self.samples[0]["memory_mb"],
                "current_memory_mb": last_sample["memory_mb"],
                "peak_memory_mb": self.peak_memory,
                "memory_growth_mb": last_sample["memory_mb"] - self.samples[0]["memory_mb"],
                "current_cpu": last_sample["cpu_percent"],
                "current_threads": last_sample["threads"]
            }


class BugTracker:
    """高级 Bug 追踪器 - 支持去重、分类、统计"""
    
    def __init__(self):
        self.bugs = []
        self.bug_counter = Counter()
        self.category_counter = Counter()
        self.lock = threading.Lock()
        self.first_occurrence = {}
    
    def add_bug(self, category: str, severity: str, description: str, stack_trace: str = ""):
        """记录 Bug"""
        bug_key = f"{category}:{description[:200]}"
        
        with self.lock:
            if bug_key not in self.first_occurrence:
                self.first_occurrence[bug_key] = datetime.now().isoformat()
            
            self.bug_counter[bug_key] += 1
            self.category_counter[category] += 1
            
            bug = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "description": description,
                "stack_trace": stack_trace,
                "count": self.bug_counter[bug_key],
                "first_occurrence": self.first_occurrence[bug_key]
            }
            self.bugs.append(bug)
            
            # 只在第一次或间隔时打印
            if self.bug_counter[bug_key] == 1 or self.bug_counter[bug_key] % 100 == 0:
                print(f"🐛 [{severity}] [{category}] {description} (x{self.bug_counter[bug_key]})")
    
    def get_summary(self):
        """获取 Bug 摘要"""
        with self.lock:
            return {
                "total_bugs": sum(self.bug_counter.values()),
                "unique_bugs": len(self.bug_counter),
                "categories": dict(self.category_counter),
                "bugs": self.bugs[-50:]  # 最近50个
            }
    
    def export_report(self, filename: str):
        """导出详细报告"""
        with self.lock:
            import json
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": self.get_summary(),
                "all_bugs": self.bugs
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📋 报告已导出: {filename}")


class ChaosEngine:
    """混沌引擎 - 产生真实的混乱场景"""
    
    def __init__(self, bug_tracker: BugTracker):
        self.bug_tracker = bug_tracker
        self.enabled = True
        self.chaos_stats = defaultdict(int)
        self.lock = threading.Lock()
    
    def maybe_inject_chaos(self, probability: float = 0.03):
        """随机注入混沌"""
        if not self.enabled or random.random() > probability:
            return
        
        chaos_types = [
            ("random_delay", self._chaos_random_delay),
            ("high_latency", self._chaos_high_latency),
            ("memory_pressure", self._chaos_memory_pressure),
            ("cpu_spike", self._chaos_cpu_spike),
            ("gc_trigger", self._chaos_gc),
            ("lock_contention", self._chaos_lock_contention),
        ]
        
        name, func = random.choice(chaos_types)
        try:
            func()
            with self.lock:
                self.chaos_stats[name] += 1
        except Exception as e:
            self.bug_tracker.add_bug(
                "ChaosInjection",
                "LOW",
                f"混沌注入失败: {name} - {type(e).__name__}",
                traceback.format_exc()
            )
    
    def _chaos_random_delay(self):
        """随机延迟 1-100ms"""
        delay = random.uniform(0.001, 0.1)
        time.sleep(delay)
    
    def _chaos_high_latency(self):
        """高延迟 100-500ms"""
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
    
    def _chaos_memory_pressure(self):
        """内存压力 - 临时分配大量内存"""
        size = random.randint(1, 10) * 1024 * 1024
        _temp_data = bytearray(size)
        time.sleep(0.01)
        del _temp_data
    
    def _chaos_cpu_spike(self):
        """CPU 尖峰 - 短暂繁忙"""
        for _ in range(10000):
            _ = random.random() * random.random()
    
    def _chaos_gc(self):
        """强制触发 GC"""
        gc.collect()
    
    def _chaos_lock_contention(self):
        """模拟锁竞争"""
        with threading.Lock():
            time.sleep(random.uniform(0.0001, 0.001))
    
    def get_chaos_stats(self):
        """获取混沌统计"""
        with self.lock:
            return dict(self.chaos_stats)


class RealBusinessWorkflow:
    """模拟真实业务流程"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.user_id = f"user_{workflow_id.split('_')[1]}"
    
    def execute(self, storage: InMemoryChatStorage, version_manager: VersionManager, analytics: AnalyticsEngine, broker: MessageBroker):
        """执行业务流程"""
        # 1. 创建版本
        version = version_manager.create_version(
            f"workflow_{self.workflow_id}",
            {"step": "init", "time": time.time()}
        )
        
        # 2. 记录分析数据
        analytics.record_metric("workflow_start", 1.0, metadata={"workflow": self.workflow_id})
        
        # 3. 保存消息
        storage.save_message(self.user_id, {
            "type": "workflow_start",
            "workflow_id": self.workflow_id,
            "version": version.id
        })
        
        # 4. 执行几个步骤
        for step in range(random.randint(2, 10)):
            analytics.record_metric(f"step_{step}", step * 1.0)
            storage.save_message(self.user_id, {"type": "step", "step": step})
            broker.publish({"type": "step_update", "workflow": self.workflow_id, "step": step})
        
        # 5. 创建新版本
        final_version = version_manager.create_version(
            f"workflow_{self.workflow_id}",
            {"step": "complete", "time": time.time()}
        )
        
        # 6. 记录完成
        analytics.record_metric("workflow_complete", 1.0)
        storage.save_message(self.user_id, {
            "type": "workflow_complete",
            "version": final_version.id
        })
        
        return True


class LongDurationTest:
    """超长时间测试控制器"""
    
    def __init__(self, duration_hours: float = 0.5, num_threads: int = 300):
        self.duration_hours = duration_hours
        self.num_threads = num_threads
        self.stop_event = threading.Event()
        
        self.bug_tracker = BugTracker()
        self.chaos_engine = ChaosEngine(self.bug_tracker)
        self.metrics = SystemMetrics()
        
        self.operation_counts = defaultdict(int)
        self.count_lock = threading.Lock()
        
        # 共享资源
        self.storage = InMemoryChatStorage()
        self.version_manager = VersionManager()
        self.analytics = AnalyticsEngine()
        self.broker = MessageBroker()
    
    def worker_thread(self, worker_id: int):
        """工作线程 - 持续执行各种操作"""
        while not self.stop_event.is_set():
            try:
                # 随机选择操作类型
                action_type = random.choice([
                    "workflow", "message", "version", "analytics", 
                    "mixed", "query"
                ])
                
                if action_type == "workflow":
                    self._do_workflow_operation(worker_id)
                elif action_type == "message":
                    self._do_message_operation(worker_id)
                elif action_type == "version":
                    self._do_version_operation(worker_id)
                elif action_type == "analytics":
                    self._do_analytics_operation(worker_id)
                elif action_type == "mixed":
                    self._do_mixed_operation(worker_id)
                else:
                    self._do_query_operation(worker_id)
                
                # 可能注入混沌
                self.chaos_engine.maybe_inject_chaos(0.05)
                
                with self.count_lock:
                    self.operation_counts[action_type] += 1
                
            except Exception as e:
                with self.count_lock:
                    self.operation_counts["errors"] += 1
                self.bug_tracker.add_bug(
                    f"Worker{worker_id}Error",
                    "HIGH",
                    f"工作线程异常: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    def _do_workflow_operation(self, worker_id: int):
        """执行工作流操作"""
        workflow = RealBusinessWorkflow(f"wf_{worker_id}_{uuid.uuid4().hex[:8]}")
        workflow.execute(self.storage, self.version_manager, self.analytics, self.broker)
    
    def _do_message_operation(self, worker_id: int):
        """执行消息操作"""
        user_id = f"user_{worker_id}_{random.randint(0, 50)}"
        msg_count = random.randint(1, 10)
        
        for i in range(msg_count):
            self.storage.save_message(user_id, {
                "content": f"msg_{worker_id}_{i}",
                "type": random.choice(["chat", "notification", "alert"]),
                "priority": random.randint(1, 10)
            })
            
            if random.random() < 0.2:
                self.broker.publish({
                    "type": "message",
                    "from": user_id,
                    "index": i
                })
    
    def _do_version_operation(self, worker_id: int):
        """执行版本操作"""
        wf_id = f"version_test_{worker_id % 50}"
        
        if random.random() < 0.7:
            # 创建版本
            version = self.version_manager.create_version(
                wf_id,
                {"v": random.randint(0, 1000), "time": time.time()}
            )
            
            if random.random() < 0.3:
                # 尝试获取刚创建的版本
                self.version_manager.get_version(version.id)
        else:
            # 列出版本
            self.version_manager.list_versions(wf_id)
    
    def _do_analytics_operation(self, worker_id: int):
        """执行分析操作"""
        metrics = ["latency", "throughput", "error_rate", "cpu", "memory", "active_users"]
        
        for i in range(random.randint(1, 10)):
            metric = random.choice(metrics)
            value = random.uniform(0, 100)
            self.analytics.record_metric(
                metric, 
                value,
                metadata={"worker": worker_id, "i": i}
            )
        
        if random.random() < 0.1:
            self.analytics.get_summary()
    
    def _do_mixed_operation(self, worker_id: int):
        """混合操作"""
        # 混合各种操作
        self._do_message_operation(worker_id)
        if random.random() < 0.5:
            self._do_analytics_operation(worker_id)
        if random.random() < 0.3:
            self._do_version_operation(worker_id)
    
    def _do_query_operation(self, worker_id: int):
        """查询操作"""
        # 查询消息
        user_id = f"user_{random.randint(0, self.num_threads)}"
        self.storage.get_conversation(user_id)
        
        # 查询版本
        wf_id = f"version_test_{random.randint(0, 50)}"
        self.version_manager.list_versions(wf_id)
        
        # 查询分析摘要
        if random.random() < 0.3:
            self.analytics.get_summary()
        
        # 接收消息
        if random.random() < 0.2:
            self.broker.receive()
    
    def monitor_thread(self):
        """监控线程"""
        start_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                # 采样
                self.metrics.sample()
                
                # 打印进度
                elapsed = time.time() - start_time
                remaining = max(0, (self.duration_hours * 3600) - elapsed)
                
                with self.count_lock:
                    total_ops = sum(self.operation_counts.values())
                    ops_by_type = dict(self.operation_counts)
                
                bug_summary = self.bug_tracker.get_summary()
                
                print(f"\n{'='*80}")
                print(f"⏱️  运行时间: {elapsed/60:.1f}分钟 | 剩余: {remaining/60:.1f}分钟")
                print(f"📊 总操作: {total_ops}")
                print(f"   按类型: {ops_by_type}")
                print(f"🐛 Bug统计: {bug_summary['total_bugs']} 总, {bug_summary['unique_bugs']} 唯一")
                print(f"🌪️  混沌统计: {self.chaos_engine.get_chaos_stats()}")
                
                metric_summary = self.metrics.get_summary()
                print(f"💾 内存: {metric_summary.get('current_memory_mb', 0):.1f}MB (峰值: {metric_summary.get('peak_memory_mb', 0):.1f}MB)")
                
            except Exception as e:
                print(f"⚠️  监控线程错误: {e}")
            
            time.sleep(30)
    
    def run(self):
        """运行超长时间测试"""
        print("="*80)
        print(f"MAOS 超长时间深度混沌测试 v7.0")
        print(f"计划运行时间: {self.duration_hours:.2f}小时 | 线程数: {self.num_threads}")
        print("="*80)
        
        # 启动监控
        monitor_thread = threading.Thread(target=self.monitor_thread, daemon=True)
        monitor_thread.start()
        
        # 启动定时停止
        def stop_after():
            time.sleep(self.duration_hours * 3600)
            self.stop_event.set()
            print("\n⏰ 时间到，正在停止所有线程...")
        
        threading.Thread(target=stop_after, daemon=True).start()
        
        # 启动工作线程
        print(f"\n🚀 启动 {self.num_threads} 个工作线程...")
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self.worker_thread, i) for i in range(self.num_threads)]
            
            # 等待所有线程完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.bug_tracker.add_bug(
                        "WorkerCrash",
                        "CRITICAL",
                        f"工作线程崩溃: {type(e).__name__}",
                        traceback.format_exc()
                    )
        
        self._generate_final_report()
    
    def _generate_final_report(self):
        """生成最终报告"""
        print("\n" + "="*80)
        print("📋 最终测试报告")
        print("="*80)
        
        # 操作统计
        with self.count_lock:
            total_ops = sum(self.operation_counts.values())
            print(f"\n📊 总操作数: {total_ops}")
            print(f"   详细: {dict(self.operation_counts)}")
        
        # 系统指标
        metric_summary = self.metrics.get_summary()
        print(f"\n💾 系统指标:")
        for key, value in metric_summary.items():
            print(f"   {key}: {value}")
        
        # Bug 统计
        bug_summary = self.bug_tracker.get_summary()
        print(f"\n🐛 Bug 统计:")
        print(f"   总 Bug: {bug_summary['total_bugs']}")
        print(f"   唯一 Bug: {bug_summary['unique_bugs']}")
        print(f"   按分类: {bug_summary.get('categories', {})}")
        
        # 导出报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"/workspace/maos/tests/chaos_report_{timestamp}.json"
        self.bug_tracker.export_report(report_file)
        
        if bug_summary['total_bugs'] == 0:
            print("\n✅ 恭喜！系统完美通过超长时间混沌测试，未发现任何 Bug！")
        else:
            print(f"\n⚠️  发现 {bug_summary['total_bugs']} 个 Bug，需要进行修复。")


def main():
    """主函数"""
    # 设置为1小时测试，实际生产可设置更长
    test = LongDurationTest(duration_hours=0.25, num_threads=300)
    test.run()


if __name__ == "__main__":
    main()
