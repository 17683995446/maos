#!/usr/bin/env python3
"""
极端边界条件混沌测试 - 探索系统极限
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
from collections import defaultdict

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class ExtremeBugTracker:
    def __init__(self):
        self.bugs = []
        self.lock = threading.Lock()
        self.error_counts = defaultdict(int)
    
    def add(self, category, severity, desc, stack=""):
        with self.lock:
            bug_id = f"{category}:{severity}:{desc[:50]}"
            if self.error_counts[bug_id] > 0:
                return  # 避免重复
            self.error_counts[bug_id] += 1
            
            self.bugs.append({
                "time": datetime.now().isoformat(),
                "category": category,
                "severity": severity,
                "desc": desc,
                "stack": stack[:500] if stack else ""
            })
            print(f"🐛 [{severity}] [{category}] {desc[:100]}")
    
    def summary(self):
        with self.lock:
            return {
                "total": len(self.bugs),
                "bugs": self.bugs[-50:]
            }


bug_tracker = ExtremeBugTracker()


def test_extreme_race_conditions():
    """极端竞态条件测试 - 读写锁冲突"""
    print("\n" + "="*80)
    print("测试1: 极端竞态条件 - 读写锁冲突")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    ops = [0, 0, 0]  # read, write, delete
    lock = threading.Lock()
    
    def reader(i):
        nonlocal ops
        for _ in range(1000):
            try:
                storage.get_conversation(f"user_{i % 100}")
                with lock:
                    ops[0] += 1
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add("RaceCondition", "CRITICAL", 
                    f"读取竞态失败: {type(e).__name__}", traceback.format_exc())
    
    def writer(i):
        nonlocal ops
        for _ in range(500):
            try:
                storage.save_message(f"user_{i % 100}", {
                    "content": f"msg_{i}_{random.randint(1, 10000)}",
                    "session_id": f"session_{i % 50}"
                })
                with lock:
                    ops[1] += 1
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add("RaceCondition", "CRITICAL",
                    f"写入竞态失败: {type(e).__name__}", traceback.format_exc())
    
    def cleaner(i):
        nonlocal ops
        for _ in range(100):
            try:
                storage.clear_all()
                with lock:
                    ops[2] += 1
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add("RaceCondition", "CRITICAL",
                    f"清理竞态失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    threads = []
    for i in range(500):
        threads.append(threading.Thread(target=reader, args=(i,)))
        threads.append(threading.Thread(target=writer, args=(i,)))
        if i % 5 == 0:
            threads.append(threading.Thread(target=cleaner, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    print(f"完成! 读={ops[0]}, 写={ops[1]}, 删={ops[2]}, 错误={errors}")
    print(f"总操作: {sum(ops)}, 错误率: {errors/max(sum(ops),1)*100:.4f}%")
    return errors


def test_extreme_data_corruption():
    """极端数据损坏测试"""
    print("\n" + "="*80)
    print("测试2: 极端数据损坏测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    errors = 0
    
    # 构造各种损坏数据
    corrupt_data = [
        {"content": None},
        {"content": 12345},
        {"content": {"nested": {"deep": {"value": "test"}}}},
        {"content": [1, 2, 3, "string", None, {"obj": True}]},
        {"content": "x" * 1000000},  # 1MB
        {"content": ""},
        {"content": "🎉" * 10000},  # emoji
        {"content": "\x00\x01\x02\xff"},  # binary
        {"id": None, "content": "no_id"},
        {"content": "valid"},  # 缺失其他字段
    ]
    
    for i, data in enumerate(corrupt_data):
        try:
            storage.save_message("corrupt_user", data)
            
            # 验证不会导致系统崩溃
            storage.get_conversation("corrupt_user")
            storage.get_stats()
            
        except Exception as e:
            errors += 1
            bug_tracker.add("DataCorruption", "HIGH",
                f"损坏数据{i}导致异常: {type(e).__name__}: {str(e)[:50]}",
                traceback.format_exc())
    
    print(f"完成! 测试了 {len(corrupt_data)} 种损坏数据, 错误={errors}")
    return errors


def test_extreme_recursive_depth():
    """极端递归深度测试"""
    print("\n" + "="*80)
    print("测试3: 极端递归深度测试")
    print("="*80)
    
    errors = 0
    
    # 测试嵌套数据结构
    def create_deep_nested(depth):
        if depth <= 0:
            return {"value": "leaf"}
        return {"level": depth, "child": create_deep_nested(depth - 1)}
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    
    # 测试不同深度
    depths = [10, 50, 100, 500, 1000]
    
    for depth in depths:
        try:
            nested = create_deep_nested(depth)
            storage.save_message("deep_user", {"content": str(nested)})
            
            # 版本管理测试
            version = vm.create_version(f"deep_wf_{depth}", {"nested": nested})
            
            if depth == max(depths):
                print(f"  ✓ 深度 {depth} 成功")
                
        except RecursionError:
            bug_tracker.add("RecursiveDepth", "MEDIUM",
                f"递归深度 {depth} 导致 RecursionError")
            errors += 1
        except Exception as e:
            errors += 1
            bug_tracker.add("RecursiveDepth", "HIGH",
                f"递归深度 {depth} 失败: {type(e).__name__}",
                traceback.format_exc())
    
    print(f"完成! 错误={errors}")
    return errors


def test_extreme_time_warps():
    """极端时间扭曲测试"""
    print("\n" + "="*80)
    print("测试4: 极端时间扭曲测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    errors = 0
    
    # 各种极端时间戳
    extreme_times = [
        0,  # 1970-01-01
        -1,  # 过去
        2147483647,  # 2038问题
        2**40,  # 遥远的未来
        -2**40,  # 遥远的过去
        time.time(),  # 现在
        time.time() + 1000000000,  # 未来
        time.time() - 1000000000,  # 过去
    ]
    
    for i, ts in enumerate(extreme_times):
        try:
            storage.save_message("time_user", {
                "content": f"time_test_{i}",
                "timestamp": ts
            })
        except Exception as e:
            errors += 1
            bug_tracker.add("TimeWarp", "HIGH",
                f"极端时间戳 {ts} 失败: {type(e).__name__}",
                traceback.format_exc())
    
    print(f"完成! 测试了 {len(extreme_times)} 种极端时间, 错误={errors}")
    return errors


def test_extreme_memory_pressure():
    """极端内存压力测试"""
    print("\n" + "="*80)
    print("测试5: 极端内存压力测试")
    print("="*80)
    
    try:
        import psutil
        process = psutil.Process()
        initial_mem = process.memory_info().rss / 1024 / 1024
        print(f"  初始内存: {initial_mem:.2f}MB")
    except:
        process = None
        print("  ⚠️  无法监控内存")
    
    errors = 0
    storage = InMemoryChatStorage()
    
    # 分配大量数据
    for i in range(10000):
        try:
            msg = {
                "content": "x" * 10000,  # 10KB per message
                "metadata": {"key": "value"} * 100
            }
            storage.save_message("mem_user", msg)
            
            if i % 1000 == 0:
                if process:
                    mem = process.memory_info().rss / 1024 / 1024
                    print(f"    消息 {i}: {mem:.2f}MB")
                    
        except MemoryError:
            errors += 1
            bug_tracker.add("MemoryPressure", "CRITICAL",
                f"内存压力测试 {i} 导致 MemoryError")
            break
        except Exception as e:
            errors += 1
            if errors < 10:
                bug_tracker.add("MemoryPressure", "HIGH",
                    f"内存压力测试 {i} 失败: {type(e).__name__}",
                    traceback.format_exc())
    
    if process:
        final_mem = process.memory_info().rss / 1024 / 1024
        print(f"  最终内存: {final_mem:.2f}MB (增长: {final_mem - initial_mem:.2f}MB)")
    
    print(f"完成! 错误={errors}")
    return errors


def test_extreme_concurrent_versions():
    """极端并发版本管理"""
    print("\n" + "="*80)
    print("测试6: 极端并发版本管理")
    print("="*80)
    
    vm = VersionManager()
    errors = 0
    lock = threading.Lock()
    ops = [0]
    
    def version_spammer(i):
        nonlocal errors
        for j in range(1000):
            try:
                # 随机操作
                op = random.choice(['create', 'get', 'list', 'delete'])
                
                wf_id = f"spam_wf_{i % 100}"
                
                if op == 'create':
                    v = vm.create_version(wf_id, {"spam": f"{i}_{j}"})
                elif op == 'get':
                    versions = vm.list_versions(wf_id)
                    if versions:
                        v = vm.get_version(random.choice(versions).id)
                elif op == 'list':
                    vm.list_versions(wf_id)
                else:  # delete
                    versions = vm.list_versions(wf_id)
                    if versions:
                        vm.delete_version(random.choice(versions).id)
                
                with lock:
                    ops[0] += 1
                    
            except Exception as e:
                with lock:
                    errors += 1
                bug_tracker.add("ConcurrentVersions", "HIGH",
                    f"版本并发失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=500) as ex:
        list(ex.map(version_spammer, range(500)))
    elapsed = time.time() - start
    
    print(f"完成! 操作={ops[0]}, 错误={errors}, 时间={elapsed:.2f}秒")
    print(f"吞吐量: {ops[0]/elapsed:.0f} ops/s")
    return errors


def test_extreme_signal_handling():
    """极端信号处理测试"""
    print("\n" + "="*80)
    print("测试7: 极端信号处理测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    
    def signal_handler(signum, frame):
        bug_tracker.add("SignalHandling", "CRITICAL",
            f"收到信号 {signum}, 尝试在信号处理中操作存储")
    
    old_handler = signal.signal(signal.SIGUSR1, signal_handler)
    
    try:
        # 在不同线程中发送信号
        def trigger_signal():
            time.sleep(0.1)
            os.kill(os.getpid(), signal.SIGUSR1)
        
        t = threading.Thread(target=trigger_signal)
        t.start()
        
        # 同时进行存储操作
        for i in range(1000):
            storage.save_message("signal_user", {"content": f"sig_{i}"})
        
        t.join()
        
    except Exception as e:
        bug_tracker.add("SignalHandling", "HIGH",
            f"信号测试失败: {type(e).__name__}", traceback.format_exc())
    finally:
        signal.signal(signal.SIGUSR1, old_handler)
    
    print("完成!")
    return 0


def test_extreme_resource_limits():
    """极端资源限制测试"""
    print("\n" + "="*80)
    print("测试8: 极端资源限制测试")
    print("="*80)
    
    errors = 0
    
    # 尝试设置资源限制
    try:
        # 限制最大文件描述符
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        print(f"  当前限制: soft={soft}, hard={hard}")
        
        # 尝试缩小限制
        if hard > 100:
            resource.setrlimit(resource.RLIMIT_NOFILE, (100, hard))
            print(f"  设置限制: soft=100, hard={hard}")
            
            # 测试在限制下运行
            storage = InMemoryChatStorage()
            for i in range(10000):
                try:
                    storage.save_message("limit_user", {"content": f"lim_{i}"})
                except Exception as e:
                    errors += 1
                    bug_tracker.add("ResourceLimit", "HIGH",
                        f"资源限制下失败: {type(e).__name__}", traceback.format_exc())
            
            # 恢复限制
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
            
    except Exception as e:
        bug_tracker.add("ResourceLimit", "MEDIUM",
            f"资源限制测试失败: {type(e).__name__}", traceback.format_exc())
    
    print(f"完成! 错误={errors}")
    return errors


def test_extreme_unicode_edge_cases():
    """极端Unicode边界测试"""
    print("\n" + "="*80)
    print("测试9: 极端Unicode边界测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    errors = 0
    
    # 各种Unicode边界情况
    unicode_cases = [
        ("emoji", "🎉🔥💯🚀⚡🎊🎁🎄🎅🎃🎉"),
        ("control", "\x00\x01\x02\x03\n\r\t"),
        ("bidi", "\u202b\u202c\u200e\u200f"),
        ("surrogate", "\ud800\udc00\ud800\udc01"),
        ("combining", "a\u0300\u0301\u0302"),
        ("normalization", "café vs café"),
        ("east_asian", "中文日本語한국어"),
        ("mixed", "Hello 世界 🌍 🎉"),
    ]
    
    for name, text in unicode_cases:
        try:
            storage.save_message("unicode_user", {"content": text})
            
            # 验证
            conv = storage.get_conversation("unicode_user")
            assert len(conv) > 0, "消息丢失"
            
            print(f"  ✓ {name} 成功")
        except Exception as e:
            errors += 1
            bug_tracker.add("UnicodeEdge", "HIGH",
                f"Unicode测试 {name} 失败: {type(e).__name__}",
                traceback.format_exc())
    
    print(f"完成! 错误={errors}")
    return errors


def test_extreme_threading_starvation():
    """极端线程饥饿测试"""
    print("\n" + "="*80)
    print("测试10: 极端线程饥饿测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    lock = threading.Lock()
    ops = [0]
    start_times = []
    
    def starved_writer(i):
        start = time.time()
        with lock:
            start_times.append((i, start))
        
        # 长时间持有锁
        for _ in range(100):
            storage.save_message("starve_user", {"content": f"w_{i}"})
        
        with lock:
            ops[0] += 1
    
    def starved_reader(i):
        start = time.time()
        # 等待写入者
        time.sleep(0.01)
        
        try:
            for _ in range(50):
                storage.get_conversation("starve_user")
            
            with lock:
                ops[0] += 1
        except Exception as e:
            bug_tracker.add("ThreadStarvation", "MEDIUM",
                f"读者线程 {i} 超时", str(e))
    
    # 启动饥饿场景
    threads = []
    for i in range(100):
        threads.append(threading.Thread(target=starved_writer, args=(i,)))
    for i in range(200):
        threads.append(threading.Thread(target=starved_reader, args=(i,)))
    
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start
    
    print(f"完成! 操作={ops[0]}, 时间={elapsed:.2f}秒")
    return 0


def test_extreme_analytics_corner_cases():
    """极端分析引擎角落案例"""
    print("\n" + "="*80)
    print("测试11: 极端分析引擎角落案例")
    print("="*80)
    
    analytics = AnalyticsEngine()
    errors = 0
    
    # 各种边界情况
    test_cases = [
        ("nan", float('nan')),
        ("inf", float('inf')),
        ("neg_inf", float('-inf')),
        ("zero", 0.0),
        ("neg_zero", -0.0),
        ("very_small", 1e-300),
        ("very_large", 1e300),
        ("huge_negative", -1e300),
    ]
    
    for name, value in test_cases:
        try:
            analytics.record_metric(f"corner_{name}", value)
            summary = analytics.get_summary()
        except Exception as e:
            errors += 1
            bug_tracker.add("AnalyticsCorner", "HIGH",
                f"分析角落案例 {name}={value} 失败: {type(e).__name__}",
                traceback.format_exc())
    
    print(f"完成! 错误={errors}")
    return errors


def test_extreme_broker_chaos():
    """极端消息代理混乱测试"""
    print("\n" + "="*80)
    print("测试12: 极端消息代理混乱测试")
    print("="*80)
    
    broker = MessageBroker(max_messages=1000)  # 小队列
    errors = 0
    lock = threading.Lock()
    
    def publisher(i):
        nonlocal errors
        for j in range(500):
            try:
                broker.publish({
                    "id": f"{i}_{j}",
                    "data": "x" * 1000
                })
            except Exception as e:
                with lock:
                    errors += 1
                if errors < 20:
                    bug_tracker.add("BrokerChaos", "HIGH",
                        f"发布失败: {type(e).__name__}", traceback.format_exc())
    
    def consumer(i):
        nonlocal errors
        for _ in range(500):
            try:
                msg = broker.receive()
            except Exception as e:
                with lock:
                    errors += 1
    
    start = time.time()
    threads = []
    for i in range(100):
        threads.append(threading.Thread(target=publisher, args=(i,)))
        threads.append(threading.Thread(target=consumer, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start
    
    print(f"完成! 错误={errors}, 时间={elapsed:.2f}秒")
    return errors


def main():
    print("="*80)
    print("MAOS 极端边界条件混沌测试 - 探索系统极限")
    print("="*80)
    
    start_time = time.time()
    
    test_extreme_race_conditions()
    test_extreme_data_corruption()
    test_extreme_recursive_depth()
    test_extreme_time_warps()
    test_extreme_memory_pressure()
    test_extreme_concurrent_versions()
    test_extreme_signal_handling()
    test_extreme_resource_limits()
    test_extreme_unicode_edge_cases()
    test_extreme_threading_starvation()
    test_extreme_analytics_corner_cases()
    test_extreme_broker_chaos()
    
    total_time = time.time() - start_time
    
    summary = bug_tracker.summary()
    
    print("\n" + "="*80)
    print("📋 极端测试总结")
    print("="*80)
    print(f"总Bug数: {summary['total']}")
    print(f"总测试时间: {total_time:.2f}秒")
    
    if summary['bugs']:
        print("\n发现的Bug (按严重程度):")
        
        # 按严重程度分组
        by_severity = defaultdict(list)
        for bug in summary['bugs']:
            by_severity[bug['severity']].append(bug)
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in by_severity:
                print(f"\n  [{severity}] ({len(by_severity[severity])}个):")
                for bug in by_severity[severity][:5]:
                    print(f"    - [{bug['category']}] {bug['desc'][:80]}")
                    if bug.get('stack'):
                        print(f"      堆栈: {bug['stack'][:150]}...")
    
    if summary['total'] == 0:
        print("\n✅ 所有极端测试通过！系统边界处理完美！")
    else:
        print(f"\n⚠️  发现 {summary['total']} 个Bug需要修复！")
    
    return summary['total']


if __name__ == "__main__":
    exit(main())
