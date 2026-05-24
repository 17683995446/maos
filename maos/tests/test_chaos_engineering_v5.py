#!/usr/bin/env python3
"""
MAOS 超高级混沌工程测试框架 v5.0
Multi-Agent Orchestration System - 超大规模真实实践测试

特点：
- 超长时间运行（支持配置小时级测试）
- 超大规模并发（支持千级线程）
- 超复杂业务流程（多个组件深度混合）
- 超混乱场景（延迟波动、故障注入、资源竞争）
- 全面监控（内存、CPU、GC、锁竞争）
"""

import threading
import time
import random
import sys
import gc
import traceback
import os
import uuid
import json
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from collections import defaultdict, Counter

sys.path.insert(0, '/workspace')

from maos.orchestration.orchestrator import MessageBroker
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.storage.in_memory import InMemoryChatStorage


class ChaosEngine:
    """混沌引擎 - 产生各种故障和混乱"""
    
    def __init__(self, bug_tracker: 'BugTracker'):
        self.bug_tracker = bug_tracker
        self.enabled = True
        self.chaos_types = [
            ("random_delay", self._chaos_random_delay),
            ("high_latency", self._chaos_high_latency),
            ("spiky_load", self._chaos_spiky_load),
            ("memory_thrashing", self._chaos_memory_thrashing),
            ("gc_stress", self._chaos_gc_stress),
            ("lock_contention", self._chaos_lock_contention),
        ]
        self._chaos_lock = threading.Lock()
        self._contention_lock = threading.Lock()
        self._chaos_stats = Counter()
        
    def maybe_inject_chaos(self, probability: float = 0.05) -> bool:
        """随机注入混沌"""
        if not self.enabled or random.random() > probability:
            return False
        
        chaos_name, chaos_func = random.choice(self.chaos_types)
        try:
            chaos_func()
            with self._chaos_lock:
                self._chaos_stats[chaos_name] += 1
            return True
        except Exception as e:
            self.bug_tracker.add_bug(
                category="ChaosInjection",
                severity="LOW",
                description=f"混沌注入失败: {chaos_name}",
                stack_trace=traceback.format_exc()
            )
            return False
    
    def _chaos_random_delay(self):
        """随机延迟：1-100ms"""
        delay = random.uniform(0.001, 0.1)
        time.sleep(delay)
    
    def _chaos_high_latency(self):
        """高延迟：100-500ms"""
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
    
    def _chaos_spiky_load(self):
        """尖峰负载：短暂的CPU密集操作"""
        result = 0
        for i in range(10000):
            result += (i * i) % random.randint(1, 100)
        return result
    
    def _chaos_memory_thrashing(self):
        """内存颠簸：快速创建和销毁大对象"""
        size = random.randint(1, 10) * 1024 * 1024
        _temp_data = bytearray(size)
        time.sleep(0.001)
        del _temp_data
    
    def _chaos_gc_stress(self):
        """GC压力：强制触发垃圾回收"""
        gc.collect()
    
    def _chaos_lock_contention(self):
        """锁竞争：模拟高并发锁等待"""
        with self._contention_lock:
            time.sleep(random.uniform(0.0001, 0.01))
    
    def get_chaos_stats(self) -> Dict[str, int]:
        """获取混沌统计"""
        with self._chaos_lock:
            return dict(self._chaos_stats)


class BugTracker:
    """高级Bug追踪器 - 支持重复Bug归类"""
    
    def __init__(self):
        self.bugs: List[Dict[str, Any]] = []
        self.bug_counts: Counter = Counter()
        self.lock = threading.Lock()
        
    def add_bug(self, category: str, severity: str, description: str, 
                stack_trace: str = "", test_context: Dict[str, Any] = None):
        bug_id = str(uuid.uuid4())[:8]
        bug_key = f"{category}:{description[:100]}"
        
        with self.lock:
            self.bug_counts[bug_key] += 1
            bug = {
                "id": bug_id,
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "description": description,
                "stack_trace": stack_trace,
                "test_context": test_context or {},
                "count": self.bug_counts[bug_key],
            }
            self.bugs.append(bug)
            print(f"🐛 [BUG-{bug_id}] [{severity}] [{category}] {description}")
    
    def summary(self) -> Dict[str, Any]:
        """获取完整摘要"""
        with self.lock:
            stats = {
                "total": sum(self.bug_counts.values()),
                "unique": len(self.bug_counts),
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            }
            for bug in self.bugs:
                severity = bug["severity"].lower()
                if "critical" in severity:
                    stats["critical"] += 1
                elif "high" in severity:
                    stats["high"] += 1
                elif "medium" in severity:
                    stats["medium"] += 1
                else:
                    stats["low"] += 1
            return stats
    
    def export_report(self, filepath: str):
        """导出详细报告"""
        with self.lock:
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": self.summary(),
                "top_bugs": sorted(
                    [{"key": k, "count": v} for k, v in self.bug_counts.items()],
                    key=lambda x: x["count"],
                    reverse=True
                )[:10],
                "all_bugs": self.bugs
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📊 报告已导出: {filepath}")


class ResourceMonitor:
    """详细资源监控器"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = datetime.now()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.start_memory
        self.samples: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def sample(self, label: str = ""):
        """采样资源使用"""
        try:
            mem_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.01)
            num_threads = self.process.num_threads()
            
            sample = {
                "timestamp": datetime.now().isoformat(),
                "label": label,
                "memory_mb": mem_mb,
                "cpu_percent": cpu_percent,
                "num_threads": num_threads,
            }
            
            with self.lock:
                self.samples.append(sample)
                if mem_mb > self.peak_memory:
                    self.peak_memory = mem_mb
        except Exception:
            pass
            
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            if not self.samples:
                return {
                    "duration": 0,
                    "samples": 0,
                    "start_memory_mb": self.start_memory,
                    "peak_memory_mb": self.peak_memory,
                    "current_memory_mb": self.start_memory,
                }
            
            mem_values = [s["memory_mb"] for s in self.samples]
            cpu_values = [s["cpu_percent"] for s in self.samples]
            
            return {
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "samples_count": len(self.samples),
                "start_memory_mb": self.start_memory,
                "current_memory_mb": mem_values[-1],
                "peak_memory_mb": self.peak_memory,
                "memory_growth_mb": mem_values[-1] - self.start_memory,
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
                "max_cpu_percent": max(cpu_values),
            }


try:
    import psutil
except ImportError:
    class psutil:
        class Process:
            def __init__(self, pid):
                pass
            def memory_info(self):
                class MemInfo:
                    rss = 0
                return MemInfo()
            def cpu_percent(self, interval):
                return 0
            def num_threads(self):
                return 1


class DeepChaosTest:
    """深度混沌工程测试"""
    
    def __init__(self, duration_seconds: int = 300, num_threads: int = 200, enable_chaos: bool = True):
        self.duration_seconds = duration_seconds
        self.num_threads = num_threads
        self.enable_chaos = enable_chaos
        
        self.bug_tracker = BugTracker()
        self.chaos_engine = ChaosEngine(self.bug_tracker)
        self.resource_monitor = ResourceMonitor()
        
        self.stats = {
            "operations_total": 0,
            "operations_success": 0,
            "operations_failed": 0,
            "start_time": None,
            "end_time": None,
        }
        
        self.should_stop = threading.Event()
        
    def test_mixed_workload(self, worker_id: int):
        """混合工作负载测试：多个组件深度混合使用"""
        storage = InMemoryChatStorage()
        vm = VersionManager()
        analytics = AnalyticsEngine()
        broker = MessageBroker()
        
        user_id = f"user_{worker_id}"
        wf_id = f"workflow_{worker_id}"
        
        local_success = 0
        local_failed = 0
        
        while not self.should_stop.is_set():
            try:
                # 混合操作1：存储操作
                if random.random() < 0.4:
                    msg_id = f"msg_{worker_id}_{uuid.uuid4().hex[:8]}"
                    msg_data = {
                        "content": f"content_{msg_id}",
                        "id": msg_id,
                        "timestamp": time.time(),
                        "metadata": {"worker": worker_id, "batch": local_success}
                    }
                    storage.save_message(user_id, msg_data)
                    
                    # 偶尔读取验证
                    if random.random() < 0.1:
                        _ = storage.get_conversation(user_id)
                
                # 混合操作2：版本管理
                elif random.random() < 0.3:
                    version = vm.create_version(wf_id, {
                        "step": local_success,
                        "worker": worker_id,
                        "data": random.randint(0, 1000000)
                    })
                    
                    # 偶尔读取版本
                    if random.random() < 0.1:
                        vm.get_version(version.id)
                    if random.random() < 0.05:
                        vm.list_versions(wf_id)
                
                # 混合操作3：分析记录
                elif random.random() < 0.2:
                    metric_name = random.choice([
                        "cpu_usage", "memory_usage", "request_latency",
                        "throughput", "error_rate", "active_sessions"
                    ])
                    analytics.record_metric(
                        metric_name,
                        random.uniform(0, 100),
                        metadata={"worker": worker_id, "batch": local_success}
                    )
                    
                    # 偶尔获取摘要
                    if random.random() < 0.05:
                        analytics.get_summary()
                
                # 混合操作4：消息代理
                else:
                    msg = {
                        "type": random.choice(["event", "command", "notification", "log"]),
                        "source": f"worker_{worker_id}",
                        "data": {"value": random.randint(0, 10000)},
                    }
                    broker.publish(msg)
                    
                    # 偶尔接收
                    if random.random() < 0.1:
                        broker.receive()
                
                # 注入混沌
                if self.enable_chaos:
                    self.chaos_engine.maybe_inject_chaos(probability=0.08)
                
                local_success += 1
                
            except Exception as e:
                local_failed += 1
                self.bug_tracker.add_bug(
                    category="MixedWorkload",
                    severity="HIGH",
                    description=f"混合工作负载错误: {type(e).__name__}",
                    stack_trace=traceback.format_exc(),
                    test_context={"worker": worker_id, "success": local_success}
                )
        
        with threading.Lock():
            self.stats["operations_total"] += local_success + local_failed
            self.stats["operations_success"] += local_success
            self.stats["operations_failed"] += local_failed
    
    def test_extreme_concurrent_storage(self):
        """极端并发存储测试"""
        print(f"\n{'='*80}")
        print(f"测试: 极端并发存储 (1000个用户同时写入)")
        print(f"{'='*80}")
        
        storage = InMemoryChatStorage()
        success_count = 0
        errors = []
        lock = threading.Lock()
        
        def writer(user_idx):
            nonlocal success_count
            try:
                user_id = f"user_{user_idx}"
                for i in range(100):
                    storage.save_message(user_id, {
                        "content": f"msg_{user_idx}_{i}",
                        "seq": i,
                    })
                    with lock:
                        success_count += 1
            except Exception as e:
                with lock:
                    errors.append(str(e))
                self.bug_tracker.add_bug(
                    category="ExtremeConcurrency",
                    severity="CRITICAL",
                    description=f"极端并发写入失败",
                    stack_trace=traceback.format_exc()
                )
        
        with ThreadPoolExecutor(max_workers=1000) as executor:
            futures = [executor.submit(writer, i) for i in range(1000)]
            for future in as_completed(futures):
                try:
                    future.result(timeout=60)
                except TimeoutError:
                    self.bug_tracker.add_bug(
                        category="Timeout",
                        severity="HIGH",
                        description="写入操作超时"
                    )
                except Exception:
                    pass
        
        print(f"完成! 成功写入: {success_count}, 错误: {len(errors)}")
    
    def test_version_torture(self):
        """版本管理器酷刑测试"""
        print(f"\n{'='*80}")
        print(f"测试: 版本管理器酷刑测试")
        print(f"{'='*80}")
        
        vm = VersionManager()
        errors = 0
        version_ids = []
        
        for i in range(100000):
            try:
                if self.should_stop.is_set():
                    break
                
                wf_id = f"workflow_{random.randint(0, 99)}"
                version = vm.create_version(wf_id, {
                    "step": i,
                    "timestamp": time.time(),
                    "data": {k: v for k, v in [(f"key_{j}", f"val_{j}") for j in range(20)]}
                })
                
                if random.random() < 0.3:
                    version_ids.append(version.id)
                
                if random.random() < 0.2 and version_ids:
                    vid = random.choice(version_ids)
                    vm.get_version(vid)
                
                if random.random() < 0.1:
                    vm.list_versions(wf_id)
                
                if random.random() < 0.01:
                    version_ids.clear()
                
                if i % 10000 == 0:
                    print(f"进度: {i}/100000")
                
            except Exception as e:
                errors += 1
                self.bug_tracker.add_bug(
                    category="VersionTorture",
                    severity="HIGH",
                    description=f"版本操作失败: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
        
        print(f"完成! 错误数: {errors}")
    
    def test_broker_flood(self):
        """消息代理洪水测试"""
        print(f"\n{'='*80}")
        print(f"测试: 消息代理洪水测试 (100万条消息)")
        print(f"{'='*80}")
        
        broker = MessageBroker()
        errors = 0
        
        start_time = time.time()
        for i in range(1000000):
            try:
                broker.publish({
                    "id": i,
                    "type": "flood_msg",
                    "priority": random.randint(0, 10),
                    "content": "x" * random.randint(10, 1000)
                })
                
                if i % 100 == 0:
                    broker.receive()
                
                if i % 100000 == 0:
                    progress = i / 1000000 * 100
                    print(f"进度: {progress:.0f}% ({i}/1000000)")
                
            except Exception as e:
                errors += 1
                self.bug_tracker.add_bug(
                    category="BrokerFlood",
                    severity="MEDIUM",
                    description=f"消息发布失败: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
        
        elapsed = time.time() - start_time
        print(f"完成! 时间: {elapsed:.2f}s, 吞吐量: {1000000/elapsed:.0f}msg/s, 错误: {errors}")
    
    def test_rapid_creation_deletion(self):
        """快速创建删除测试"""
        print(f"\n{'='*80}")
        print(f"测试: 快速创建删除测试")
        print(f"{'='*80}")
        
        errors = 0
        for i in range(5000):
            try:
                # 快速创建组件实例
                storage = InMemoryChatStorage()
                vm = VersionManager()
                analytics = AnalyticsEngine()
                broker = MessageBroker()
                
                # 使用它们
                storage.save_message("temp", {"content": "temp"})
                vm.create_version("temp", {"step": 1})
                analytics.record_metric("temp", 1.0)
                broker.publish({"type": "temp"})
                
                # 显式删除并GC
                del storage, vm, analytics, broker
                gc.collect()
                
                if i % 500 == 0:
                    self.resource_monitor.sample(f"rapid_cycle_{i}")
                    
            except Exception as e:
                errors += 1
                self.bug_tracker.add_bug(
                    category="RapidCreation",
                    severity="MEDIUM",
                    description=f"快速创建删除失败: {type(e).__name__}",
                    stack_trace=traceback.format_exc()
                )
        
        print(f"完成! 循环: 5000, 错误: {errors}")
    
    def resource_monitor_loop(self):
        """资源监控循环"""
        while not self.should_stop.is_set():
            try:
                self.resource_monitor.sample("monitor_loop")
            except Exception:
                pass
            time.sleep(1)
    
    def run(self):
        """运行完整的深度混沌测试"""
        print("="*80)
        print("MAOS 超高级混沌工程测试 v5.0")
        print(f"计划运行时间: {self.duration_seconds} 秒")
        print("="*80)
        
        self.stats["start_time"] = datetime.now().isoformat()
        
        # 启动资源监控
        monitor_thread = threading.Thread(target=self.resource_monitor_loop, daemon=True)
        monitor_thread.start()
        
        try:
            # 测试1：极端并发存储
            self.test_extreme_concurrent_storage()
            
            # 测试2：版本管理器酷刑测试
            self.test_version_torture()
            
            # 测试3：消息代理洪水测试
            self.test_broker_flood()
            
            # 测试4：快速创建删除测试
            self.test_rapid_creation_deletion()
            
            # 测试5：混合工作负载（长时间运行）
            print(f"\n{'='*80}")
            print(f"测试: 混合工作负载 (多组件深度混合, {self.duration_seconds}秒)")
            print(f"{'='*80}")
            
            self.should_stop.clear()
            
            def stop_after_duration():
                time.sleep(self.duration_seconds)
                self.should_stop.set()
                print(f"\n⏱️  已达到计划运行时间，正在停止工作线程...")
            
            timer_thread = threading.Thread(target=stop_after_duration, daemon=True)
            timer_thread.start()
            
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                futures = [executor.submit(self.test_mixed_workload, i) for i in range(self.num_threads)]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.bug_tracker.add_bug(
                            category="WorkerFailure",
                            severity="CRITICAL",
                            description=f"工作线程异常退出",
                            stack_trace=traceback.format_exc()
                        )
            
        except Exception as e:
            self.bug_tracker.add_bug(
                category="TestFramework",
                severity="CRITICAL",
                description=f"测试框架严重错误: {type(e).__name__}",
                stack_trace=traceback.format_exc()
            )
        finally:
            self.should_stop.set()
            self.stats["end_time"] = datetime.now().isoformat()
            self.resource_monitor.sample("test_end")
            
            # 生成报告
            self._generate_final_report()
    
    def _generate_final_report(self):
        """生成最终报告"""
        print("\n" + "="*80)
        print("📊 最终测试报告")
        print("="*80)
        
        # 操作统计
        print("\n📈 操作统计:")
        total_ops = self.stats["operations_total"]
        success_ops = self.stats["operations_success"]
        fail_ops = self.stats["operations_failed"]
        print(f"  总操作: {total_ops}")
        print(f"  成功: {success_ops}")
        print(f"  失败: {fail_ops}")
        if total_ops > 0:
            print(f"  成功率: {success_ops / total_ops * 100:.2f}%")
        
        # 混沌统计
        chaos_stats = self.chaos_engine.get_chaos_stats()
        if chaos_stats:
            print(f"\n🌪️  混沌统计:")
            for chaos_type, count in chaos_stats.items():
                print(f"  {chaos_type}: {count} 次")
        
        # 资源统计
        resource_stats = self.resource_monitor.get_stats()
        print(f"\n💾 资源使用:")
        print(f"  持续时间: {resource_stats.get('duration_seconds', 0):.1f} 秒")
        print(f"  初始内存: {resource_stats.get('start_memory_mb', 0):.2f} MB")
        print(f"  当前内存: {resource_stats.get('current_memory_mb', 0):.2f} MB")
        print(f"  峰值内存: {resource_stats.get('peak_memory_mb', 0):.2f} MB")
        print(f"  内存增长: {resource_stats.get('memory_growth_mb', 0):.2f} MB")
        print(f"  平均CPU: {resource_stats.get('avg_cpu_percent', 0):.2f}%")
        
        # Bug统计
        bug_summary = self.bug_tracker.summary()
        print(f"\n🐛 Bug 统计:")
        print(f"  总Bug数: {bug_summary['total']}")
        print(f"  唯一Bug: {bug_summary['unique']}")
        print(f"  CRITICAL: {bug_summary['critical']}")
        print(f"  HIGH: {bug_summary['high']}")
        print(f"  MEDIUM: {bug_summary['medium']}")
        print(f"  LOW: {bug_summary['low']}")
        
        # 导出详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bug_report_path = f"/workspace/maos/tests/chaos_bug_report_{timestamp}.json"
        self.bug_tracker.export_report(bug_report_path)
        
        # 总结
        total_bugs = bug_summary['total']
        if total_bugs == 0:
            print("\n✅ 恭喜! 所有测试通过，无 Bug 发现!")
        else:
            print(f"\n⚠️  发现 {total_bugs} 个问题，请查看详细报告。")


if __name__ == "__main__":
    # 运行配置（为演示设置较短时间，实际可设置更长）
    test = DeepChaosTest(
        duration_seconds=120,  # 2分钟
        num_threads=200,
        enable_chaos=True
    )
    test.run()
