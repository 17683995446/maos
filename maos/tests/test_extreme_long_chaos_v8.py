#!/usr/bin/env python3
"""
超长时间极端混乱混沌测试 - 持续运行，发现深层问题
包含详细日志监控
"""

import sys
import os
import time
import random
import threading
import gc
import traceback
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque

sys.path.insert(0, '/workspace')

# 使用稳定版存储组件 - 添加详细日志
from maos.storage.in_memory import InMemoryChatStorage as DebugInMemoryChatStorage
DEBUG_MODE = True
print(f"[INFO] 稳定版存储组件已加载")
print(f"[INFO] 启用详细监控日志")

from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class ExtremeBugTracker:
    """极端Bug追踪器 - 详细记录问题"""
    
    def __init__(self):
        self.bugs = []
        self.lock = threading.Lock()
        self.error_counts = defaultdict(int)
        self.operation_log = deque(maxlen=10000)  # 记录最近10000次操作
        self.error_log = deque(maxlen=1000)  # 记录最近1000个错误
    
    def log_operation(self, thread_name, operation, status):
        """记录操作日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "thread": thread_name,
            "operation": operation,
            "status": status
        }
        with self.lock:
            self.operation_log.append(entry)
    
    def add_bug(self, category, severity, desc, stack=""):
        """添加Bug"""
        with self.lock:
            bug_id = f"{category}:{severity}:{desc[:50]}"
            self.error_counts[bug_id] += 1
            
            if self.error_counts[bug_id] <= 3:  # 最多记录3次，避免刷屏
                bug = {
                    "time": datetime.now().isoformat(),
                    "category": category,
                    "severity": severity,
                    "desc": desc,
                    "stack": stack[:1000] if stack else ""
                }
                self.bugs.append(bug)
                self.error_log.append(bug)
                
                print(f"🐛 [{severity}] [{category}] {desc[:80]}")
                
                # 保存到文件
                try:
                    with open('/tmp/maos_bugs_detected.json', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(bug, ensure_ascii=False) + '\n')
                except:
                    pass
    
    def get_summary(self):
        """获取摘要"""
        with self.lock:
            return {
                "total_bugs": len(self.bugs),
                "unique_errors": len(self.error_counts),
                "bugs": self.bugs[-50:],  # 最新的50个bug
                "operation_count": len(self.operation_log)
            }
    
    def save_full_report(self):
        """保存完整报告"""
        with self.lock:
            report = {
                "summary": self.get_summary(),
                "bugs": self.bugs,
                "error_counts": dict(self.error_counts),
                "recent_operations": list(self.operation_log)[-500:],
                "recent_errors": list(self.error_log)
            }
        with open('/tmp/maos_extreme_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report


bug_tracker = ExtremeBugTracker()


class ChaosEngine:
    """极端混乱引擎"""
    
    def __init__(self):
        self.chaos_mode = True
        self.modes = [
            "normal",
            "delayed",
            "duplicate",
            "empty",
            "null",
            "corrupted",
            "huge",
            "unicode",
            "timestamp_error",
            "session_mismatch"
        ]
    
    def get_chaos_mode(self):
        """获取随机混乱模式"""
        return random.choice(self.modes)
    
    def apply_chaos(self, base_data, mode=None):
        """应用混乱效果"""
        if not mode:
            mode = self.get_chaos_mode()
        
        data = dict(base_data)  # 复制
        
        if mode == "normal":
            return data
        
        elif mode == "delayed":
            time.sleep(random.random() * 0.01)
            return data
        
        elif mode == "duplicate":
            # 重复字段
            data["duplicate_field"] = "duplicated"
            data["duplicate_field2"] = "duplicated again"
            return data
        
        elif mode == "empty":
            data["content"] = ""
            return data
        
        elif mode == "null":
            data["content"] = None
            data["id"] = None
            return data
        
        elif mode == "corrupted":
            # 损坏数据
            data["content"] = "\x00\x01\x02\x03\x04\x05"
            return data
        
        elif mode == "huge":
            data["content"] = "HUGE_" * 10000
            return data
        
        elif mode == "unicode":
            data["content"] = "🎉🎊🎁🎀🎄🎅🎆🎇🎈🎉" * 500
            return data
        
        elif mode == "timestamp_error":
            data["timestamp"] = random.choice([
                -1000000000000,
                1000000000000000000,
                float('inf'),
                float('-inf'),
                "invalid"
            ])
            return data
        
        elif mode == "session_mismatch":
            data["session_id"] = f"wrong_session_{random.randint(1, 1000)}"
            return data
        
        return data


chaos_engine = ChaosEngine()


def test_extreme_long_time(duration_hours=2, max_threads=500):
    """超长时间极端测试"""
    
    print("\n" + "="*100)
    print(f"🚀 MAOS 超长时间极端混乱混沌测试 - 持续运行 {duration_hours} 小时")
    print("="*100)
    print(f"[INFO] 测试开始时间: {datetime.now().isoformat()}")
    print(f"[INFO] 最大线程数: {max_threads}")
    print(f"[INFO] 调试模式: {'ON' if DEBUG_MODE else 'OFF'}")
    
    if DEBUG_MODE:
        print(f"[INFO] 调试日志: /tmp/maos_debug_storage.log")
    
    # 初始化组件
    storage = DebugInMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    broker = MessageBroker(max_messages=50000)
    
    print(f"[INFO] 组件初始化完成")
    
    # 统计
    stats = {
        "total_operations": 0,
        "storage_ops": 0,
        "version_ops": 0,
        "analytics_ops": 0,
        "broker_ops": 0,
        "errors": 0,
        "start_time": time.time(),
        "last_report": time.time()
    }
    stats_lock = threading.Lock()
    running = True
    
    def worker(worker_id):
        """工作线程 - 混合所有组件"""
        thread_name = f"Worker-{worker_id}"
        
        try:
            while running:
                # 随机选择操作
                op_choice = random.choice([
                    "storage_save",
                    "storage_read",
                    "storage_stats",
                    "version_create",
                    "version_read",
                    "version_list",
                    "analyze_record",
                    "analyze_summary",
                    "broker_publish",
                    "broker_receive",
                    "clear_random",
                    "gc_collect"
                ])
                
                user_id = f"user_{worker_id % 200}"
                session_id = f"session_{worker_id % 20}"
                agent_id = f"agent_{worker_id % 5}"
                workflow_id = f"workflow_{worker_id % 100}"
                
                try:
                    if op_choice == "storage_save":
                        # 存储保存操作 - 带混乱
                        base_msg = {
                            "content": f"msg_{worker_id}_{random.randint(1, 1000000)}",
                            "id": f"id_{worker_id}_{time.time()}",
                            "session_id": session_id,
                            "agent_id": agent_id,
                            "timestamp": time.time()
                        }
                        chaos_msg = chaos_engine.apply_chaos(base_msg)
                        success = storage.save_message(user_id, chaos_msg)
                        if success:
                            with stats_lock:
                                stats["storage_ops"] += 1
                        bug_tracker.log_operation(thread_name, "storage_save", "success" if success else "failed")
                    
                    elif op_choice == "storage_read":
                        # 存储读取
                        conv = storage.get_conversation(user_id, session_id, agent_id)
                        with stats_lock:
                            stats["storage_ops"] += 1
                        bug_tracker.log_operation(thread_name, "storage_read", "success")
                    
                    elif op_choice == "storage_stats":
                        # 存储统计
                        stats_data = storage.get_stats()
                        with stats_lock:
                            stats["storage_ops"] += 1
                        bug_tracker.log_operation(thread_name, "storage_stats", "success")
                    
                    elif op_choice == "version_create":
                        # 版本创建
                        version_data = {
                            "step": random.randint(1, 1000),
                            "worker": worker_id,
                            "time": time.time()
                        }
                        version = vm.create_version(workflow_id, version_data)
                        with stats_lock:
                            stats["version_ops"] += 1
                        bug_tracker.log_operation(thread_name, "version_create", "success")
                    
                    elif op_choice == "version_read":
                        # 版本读取
                        versions = vm.list_versions(workflow_id)
                        if versions:
                            vm.get_version(random.choice(versions))
                        with stats_lock:
                            stats["version_ops"] += 1
                        bug_tracker.log_operation(thread_name, "version_read", "success")
                    
                    elif op_choice == "version_list":
                        # 版本列表
                        versions = vm.list_versions(workflow_id)
                        with stats_lock:
                            stats["version_ops"] += 1
                        bug_tracker.log_operation(thread_name, "version_list", "success")
                    
                    elif op_choice == "analyze_record":
                        # 分析记录
                        metric_name = f"metric_{worker_id % 50}_{random.randint(1, 100)}"
                        metric_value = random.uniform(-10000, 10000)
                        analytics.record_metric(metric_name, metric_value)
                        with stats_lock:
                            stats["analytics_ops"] += 1
                        bug_tracker.log_operation(thread_name, "analyze_record", "success")
                    
                    elif op_choice == "analyze_summary":
                        # 分析摘要
                        summary = analytics.get_summary()
                        with stats_lock:
                            stats["analytics_ops"] += 1
                        bug_tracker.log_operation(thread_name, "analyze_summary", "success")
                    
                    elif op_choice == "broker_publish":
                        # 消息代理发布
                        broker.publish({
                            "type": random.choice(["event", "log", "alert", "data"]),
                            "from": thread_name,
                            "id": random.randint(1, 1000000),
                            "payload": "data" * (random.randint(10, 200))
                        })
                        with stats_lock:
                            stats["broker_ops"] += 1
                        bug_tracker.log_operation(thread_name, "broker_publish", "success")
                    
                    elif op_choice == "broker_receive":
                        # 消息代理接收
                        msg = broker.receive()
                        with stats_lock:
                            stats["broker_ops"] += 1
                        bug_tracker.log_operation(thread_name, "broker_receive", "success")
                    
                    elif op_choice == "clear_random":
                        # 随机清理
                        if random.random() < 0.001:  # 0.1% 概率
                            try:
                                storage.clear_all()
                                vm.cleanup()
                            except:
                                pass
                        with stats_lock:
                            stats["storage_ops"] += 1
                        bug_tracker.log_operation(thread_name, "clear_random", "success")
                    
                    elif op_choice == "gc_collect":
                        # 主动GC
                        if random.random() < 0.005:  # 0.5% 概率
                            gc.collect()
                        bug_tracker.log_operation(thread_name, "gc_collect", "success")
                    
                    # 更新总操作数
                    with stats_lock:
                        stats["total_operations"] += 1
                    
                    # 随机延迟
                    if random.random() < 0.1:
                        time.sleep(random.random() * 0.001)
                
                except Exception as e:
                    with stats_lock:
                        stats["errors"] += 1
                    
                    bug_tracker.add_bug(
                        f"Worker_{worker_id}",
                        "HIGH",
                        f"线程操作错误: {type(e).__name__}",
                        traceback.format_exc()
                    )
                    bug_tracker.log_operation(thread_name, op_choice, "error")
        
        except Exception as e:
            with stats_lock:
                stats["errors"] += 1
            bug_tracker.add_bug(
                "Worker_Critical",
                "CRITICAL",
                f"线程崩溃: {type(e).__name__}",
                traceback.format_exc()
            )
    
    def report_thread():
        """报告线程 - 定期输出状态"""
        while running:
            now = time.time()
            elapsed = now - stats["start_time"]
            since_report = now - stats["last_report"]
            
            if since_report >= 10.0:  # 每10秒报告
                with stats_lock:
                    total_ops = stats["total_operations"]
                    ops_per_sec = total_ops / elapsed if elapsed > 0 else 0
                
                summary = bug_tracker.get_summary()
                
                print(f"\n--- 状态报告 [{datetime.now().isoformat()}] ---")
                print(f"运行时间: {elapsed / 60:.1f} 分钟")
                print(f"总操作数: {total_ops:,}")
                print(f"操作速度: {ops_per_sec:.0f} ops/s")
                print(f"存储操作: {stats['storage_ops']:,}")
                print(f"版本操作: {stats['version_ops']:,}")
                print(f"分析操作: {stats['analytics_ops']:,}")
                print(f"代理操作: {stats['broker_ops']:,}")
                print(f"检测到Bug: {summary['total_bugs']}")
                print(f"唯一错误: {summary['unique_errors']}")
                print(f"最近操作: {len(summary.get('bugs', []))}")
                
                stats["last_report"] = now
                
                # 保存进度
                try:
                    bug_tracker.save_full_report()
                except:
                    pass
            
            time.sleep(1)
    
    # 启动线程
    threads = []
    report_thread_obj = threading.Thread(target=report_thread, daemon=True)
    report_thread_obj.start()
    
    for i in range(max_threads):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        threads.append(t)
        t.start()
        if i % 50 == 0:
            print(f"[INFO] 已启动 {i+1}/{max_threads} 个工作线程")
    
    print(f"[INFO] 所有工作线程已启动，开始持续运行 {duration_hours} 小时")
    
    # 持续运行
    end_time = time.time() + (duration_hours * 3600)
    
    try:
        while time.time() < end_time:
            time.sleep(10)
            
            # 检查是否有新bug
            summary = bug_tracker.get_summary()
            if summary["total_bugs"] > 0:
                print(f"\n⚠️  警告: 检测到 {summary['total_bugs']} 个问题!")
        
        print(f"\n[INFO] 测试持续时间已到，准备停止...")
    except KeyboardInterrupt:
        print(f"\n[INFO] 用户中断，准备停止...")
    finally:
        running = False
        
        # 等待所有线程结束
        for t in threads:
            t.join(timeout=5.0)
        
        report_thread_obj.join(timeout=2.0)
    
    # 最终报告
    final_elapsed = time.time() - stats["start_time"]
    final_summary = bug_tracker.get_summary()
    
    print("\n" + "="*100)
    print("📊 超长时间极端测试 最终报告")
    print("="*100)
    print(f"总运行时间: {final_elapsed / 60:.1f} 分钟")
    print(f"总操作数: {stats['total_operations']:,}")
    print(f"平均速度: {stats['total_operations'] / final_elapsed:.0f} ops/s")
    print(f"存储操作: {stats['storage_ops']:,}")
    print(f"版本操作: {stats['version_ops']:,}")
    print(f"分析操作: {stats['analytics_ops']:,}")
    print(f"代理操作: {stats['broker_ops']:,}")
    print(f"总错误: {stats['errors']}")
    print(f"检测到Bug: {final_summary['total_bugs']}")
    print(f"唯一错误: {final_summary['unique_errors']}")
    
    # 保存完整报告
    report = bug_tracker.save_full_report()
    print(f"\n📄 完整报告已保存: /tmp/maos_extreme_test_report.json")
    print(f"📄 调试日志: /tmp/maos_debug_storage.log")
    
    if final_summary['total_bugs'] == 0:
        print("\n✅ 完美! 超长时间极端测试通过 - 零Bug!")
    else:
        print(f"\n⚠️  发现 {final_summary['total_bugs']} 个问题需要检查!")
        print(f"\n最近发现的问题:")
        for bug in final_summary['bugs'][-10:]:
            print(f"\n  [{bug['severity']}] [{bug['category']}]")
            print(f"    {bug['desc']}")
    
    return final_summary['total_bugs']


def test_extreme_mixed_concurrency():
    """极端混合并发测试"""
    
    print("\n" + "="*100)
    print("🚀 极端混合并发测试 - 3000线程同时操作")
    print("="*100)
    
    storage = DebugInMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    
    errors = 0
    lock = threading.Lock()
    operations = 0
    start_time = time.time()
    
    def mixed_worker(worker_id):
        nonlocal errors, operations
        
        for i in range(100):
            try:
                # 随机混合操作
                op = random.choice(["save", "read", "create_version", "record_metric"])
                
                user_id = f"user_{worker_id % 50}"
                workflow_id = f"wf_{worker_id % 20}"
                
                if op == "save":
                    success = storage.save_message(user_id, {
                        "content": f"msg_{worker_id}_{i}",
                        "session_id": f"sess_{i % 10}",
                        "timestamp": time.time() + random.randint(-1000000, 1000000)
                    })
                    if not success:
                        with lock:
                            errors += 1
                
                elif op == "read":
                    storage.get_conversation(user_id)
                
                elif op == "create_version":
                    vm.create_version(workflow_id, {"step": i, "worker": worker_id})
                
                elif op == "record_metric":
                    analytics.record_metric(f"m_{worker_id}", float(i))
                
                with lock:
                    operations += 1
            
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add_bug(
                    "MixedConcurrency",
                    "CRITICAL",
                    f"混合并发错误: {type(e).__name__}",
                    traceback.format_exc()
                )
    
    print("[INFO] 启动 3000 个并发线程...")
    threads = []
    for i in range(3000):
        t = threading.Thread(target=mixed_worker, args=(i,), daemon=True)
        threads.append(t)
        t.start()
    
    print("[INFO] 所有线程启动完成，等待完成...")
    for t in threads:
        t.join(timeout=300.0)
    
    elapsed = time.time() - start_time
    
    print(f"\n[INFO] 完成!")
    print(f"总操作数: {operations:,}")
    print(f"总错误: {errors}")
    print(f"吞吐量: {operations/elapsed:.0f} ops/s")
    print(f"运行时间: {elapsed:.2f}秒")
    
    return errors


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MAOS 超长时间极端混乱混沌测试")
    parser.add_argument("--duration", type=float, default=0.1, help="测试持续时间（小时，默认0.1小时=6分钟）")
    parser.add_argument("--threads", type=int, default=500, help="最大线程数（默认500）")
    parser.add_argument("--mode", type=str, choices=["long", "mixed"], default="long", help="测试模式")
    
    args = parser.parse_args()
    
    if args.mode == "long":
        test_extreme_long_time(duration_hours=args.duration, max_threads=args.threads)
    elif args.mode == "mixed":
        test_extreme_mixed_concurrency()
