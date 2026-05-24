#!/usr/bin/env python3
"""
跨组件集成混沌测试 - 测试组件交互
"""

import sys
import time
import random
import threading
import gc
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.orchestration.orchestrator import MessageBroker


class IntegrationBugTracker:
    def __init__(self):
        self.bugs = []
        self.lock = threading.Lock()
        self.error_counts = defaultdict(int)
    
    def add(self, category, severity, desc, stack=""):
        with self.lock:
            bug_id = f"{category}:{severity}:{desc[:50]}"
            self.error_counts[bug_id] += 1
            if self.error_counts[bug_id] == 1:  # 只记录第一次
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
                "bugs": self.bugs
            }


bug_tracker = IntegrationBugTracker()


def test_storage_analytics_integration():
    """存储与分析引擎集成测试"""
    print("\n" + "="*80)
    print("测试1: 存储与分析引擎集成")
    print("="*80)
    
    storage = InMemoryChatStorage()
    analytics = AnalyticsEngine()
    errors = 0
    ops = [0]
    lock = threading.Lock()
    
    def worker(i):
        try:
            # 保存消息
            storage.save_message(f"user_{i % 100}", {
                "content": f"test_{i}",
                "session_id": f"session_{i % 10}"
            })
            
            # 记录分析指标
            analytics.record_metric("messages_per_user", 1.0)
            
            # 偶尔查询
            if random.random() < 0.1:
                storage.get_conversation(f"user_{i % 100}")
                analytics.get_summary()
            
            with lock:
                ops[0] += 1
                
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("StorageAnalytics", "HIGH",
                f"存储-分析集成失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=200) as ex:
        list(ex.map(worker, range(50000)))
    elapsed = time.time() - start
    
    print(f"完成! 操作={ops[0]}, 错误={errors}, 吞吐量={ops[0]/elapsed:.0f} ops/s")
    return errors


def test_version_storage_integration():
    """版本管理与存储集成"""
    print("\n" + "="*80)
    print("测试2: 版本管理与存储集成")
    print("="*80)
    
    vm = VersionManager()
    storage = InMemoryChatStorage()
    errors = 0
    lock = threading.Lock()
    ops = [0]
    
    def worker(i):
        try:
            # 创建版本
            version = vm.create_version(f"wf_{i % 50}", {
                "step": i,
                "user_id": f"user_{i % 100}"
            })
            
            # 保存版本信息到存储
            storage.save_message(f"user_{i % 100}", {
                "content": f"version_created: {version.id}",
                "version_id": version.id
            })
            
            # 获取版本并验证
            retrieved = vm.get_version(version.id)
            assert retrieved is not None, "版本丢失"
            
            # 列出版本
            version_ids = vm.list_versions(f"wf_{i % 50}")
            assert version.id in version_ids, "版本ID不匹配"
            
            with lock:
                ops[0] += 1
                
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("VersionStorage", "HIGH",
                f"版本-存储集成失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=200) as ex:
        list(ex.map(worker, range(30000)))
    elapsed = time.time() - start
    
    print(f"完成! 操作={ops[0]}, 错误={errors}, 吞吐量={ops[0]/elapsed:.0f} ops/s")
    return errors


def test_broker_analytics_integration():
    """消息代理与分析集成"""
    print("\n" + "="*80)
    print("测试3: 消息代理与分析集成")
    print("="*80)
    
    broker = MessageBroker(max_messages=50000)
    analytics = AnalyticsEngine()
    errors = 0
    lock = threading.Lock()
    ops = [0]
    
    def publisher(i):
        try:
            broker.publish({
                "type": "event",
                "id": i,
                "data": f"msg_{i}"
            })
            
            # 记录指标
            analytics.record_metric("published_messages", 1.0)
            
            with lock:
                ops[0] += 1
                
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("BrokerAnalytics", "HIGH",
                f"代理-分析发布失败: {type(e).__name__}", traceback.format_exc())
    
    def consumer(i):
        try:
            msg = broker.receive()
            if msg:
                analytics.record_metric("consumed_messages", 1.0)
                analytics.record_metric("processing_time", random.random())
        except Exception as e:
            with lock:
                errors += 1
    
    start = time.time()
    threads = []
    for i in range(100):
        threads.append(threading.Thread(target=publisher, args=(i,)))
    for i in range(50):
        threads.append(threading.Thread(target=consumer, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start
    
    print(f"完成! 操作={ops[0]}, 错误={errors}, 吞吐量={ops[0]/elapsed:.0f} ops/s")
    return errors


def test_all_components_chaos():
    """全组件混沌测试"""
    print("\n" + "="*80)
    print("测试4: 全组件混沌测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    analytics = AnalyticsEngine()
    broker = MessageBroker(max_messages=10000)
    
    errors = 0
    lock = threading.Lock()
    ops = defaultdict(int)
    
    def chaos_worker(i):
        try:
            op = random.choice(['save', 'version', 'analyze', 'publish', 'read'])
            
            if op == 'save':
                storage.save_message(f"user_{i % 200}", {
                    "content": f"msg_{i}",
                    "session_id": f"sess_{i % 20}"
                })
                ops['save'] += 1
                
            elif op == 'version':
                version = vm.create_version(f"wf_{i % 100}", {
                    "worker": i,
                    "data": random.randint(1, 1000)
                })
                storage.save_message(f"user_{i % 200}", {
                    "content": f"version: {version.id}"
                })
                ops['version'] += 1
                
            elif op == 'analyze':
                analytics.record_metric(
                    f"metric_{i % 50}",
                    random.random() * 100
                )
                ops['analyze'] += 1
                
            elif op == 'publish':
                broker.publish({
                    "worker": i,
                    "data": f"event_{i}"
                })
                ops['publish'] += 1
                
            else:  # read
                storage.get_conversation(f"user_{i % 200}")
                analytics.get_summary()
                vm.list_versions(f"wf_{i % 100}")
                ops['read'] += 1
            
            # 偶尔触发GC
            if random.random() < 0.001:
                gc.collect()
                
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("AllComponents", "CRITICAL",
                f"全组件混沌失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=300) as ex:
        list(ex.map(chaos_worker, range(100000)))
    elapsed = time.time() - start
    
    print(f"完成! 总操作={sum(ops.values())}, 错误={errors}")
    print(f"  保存={ops['save']}, 版本={ops['version']}, "
          f"分析={ops['analyze']}, 发布={ops['publish']}, 读取={ops['read']}")
    print(f"吞吐量: {sum(ops.values())/elapsed:.0f} ops/s")
    return errors


def test_resource_contention():
    """资源竞争测试"""
    print("\n" + "="*80)
    print("测试5: 资源竞争测试")
    print("="*80)
    
    # 所有组件共享资源
    shared_storage = InMemoryChatStorage()
    shared_vm = VersionManager()
    shared_analytics = AnalyticsEngine()
    shared_broker = MessageBroker(max_messages=5000)
    
    errors = 0
    lock = threading.Lock()
    
    def resource_hog(i):
        try:
            # 模拟真实场景：读取-处理-写入循环
            user_id = f"user_{i % 50}"
            
            # 读取
            conv = shared_storage.get_conversation(user_id)
            versions = shared_vm.list_versions(f"wf_{i % 20}")
            
            # 处理
            result = {
                "conversations": len(conv),
                "versions": len(versions),
                "worker": i
            }
            
            # 写入
            shared_storage.save_message(user_id, {
                "content": f"processed_{i}",
                "result": result
            })
            
            vm_version = shared_vm.create_version(f"wf_{i % 20}", result)
            shared_analytics.record_metric(f"worker_{i % 10}_processed", 1.0)
            shared_broker.publish({"type": "processed", "worker": i, "result": result})
            
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("ResourceContention", "HIGH",
                f"资源竞争失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=500) as ex:
        list(ex.map(resource_hog, range(50000)))
    elapsed = time.time() - start
    
    print(f"完成! 错误={errors}, 吞吐量={50000/elapsed:.0f} ops/s")
    return errors


def test_state_consistency():
    """状态一致性测试"""
    print("\n" + "="*80)
    print("测试6: 状态一致性测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    errors = 0
    
    # 多线程同时操作同一用户
    user_id = "consistency_user"
    
    def writer(i):
        nonlocal errors
        try:
            for j in range(100):
                storage.save_message(user_id, {
                    "content": f"w{i}_{j}",
                    "seq": j,
                    "writer": i
                })
        except Exception as e:
            errors += 1
            bug_tracker.add("StateConsistency", "CRITICAL",
                f"写入一致性失败: {type(e).__name__}", traceback.format_exc())
    
    threads = []
    for i in range(50):
        threads.append(threading.Thread(target=writer, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 验证
    conv = storage.get_conversation(user_id)
    print(f"  预期消息数: 5000")
    print(f"  实际消息数: {len(conv)}")
    
    # 检查是否有丢失
    if len(conv) != 5000:
        errors += 1
        bug_tracker.add("StateConsistency", "MEDIUM",
            f"消息丢失: 预期5000, 实际{len(conv)}")
    
    print(f"完成! 错误={errors}")
    return errors


def test_error_recovery():
    """错误恢复测试"""
    print("\n" + "="*80)
    print("测试7: 错误恢复测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    vm = VersionManager()
    errors = 0
    lock = threading.Lock()
    recovery_count = [0]
    
    def recovery_test(i):
        try:
            # 正常操作
            storage.save_message(f"user_{i}", {"content": "normal"})
            version = vm.create_version(f"wf_{i}", {"step": 1})
            
            # 触发可能失败的操作
            try:
                # 模拟错误场景
                if random.random() < 0.1:
                    raise RuntimeError("Simulated error")
            except RuntimeError:
                pass
            
            # 恢复后继续操作
            storage.save_message(f"user_{i}", {"content": "recovered"})
            vm.create_version(f"wf_{i}", {"step": 2})
            
            with lock:
                recovery_count[0] += 1
                
        except Exception as e:
            with lock:
                errors += 1
            bug_tracker.add("ErrorRecovery", "HIGH",
                f"错误恢复失败: {type(e).__name__}", traceback.format_exc())
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=200) as ex:
        list(ex.map(recovery_test, range(10000)))
    elapsed = time.time() - start
    
    print(f"完成! 恢复成功={recovery_count[0]}, 错误={errors}")
    return errors


def test_performance_regression():
    """性能回归测试"""
    print("\n" + "="*80)
    print("测试8: 性能回归测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    
    # 测试吞吐量
    start = time.time()
    for i in range(10000):
        storage.save_message(f"user_{i % 1000}", {"content": f"perf_{i}"})
    elapsed = time.time() - start
    
    throughput = 10000 / elapsed
    print(f"  存储吞吐量: {throughput:.0f} ops/s")
    
    if throughput < 1000:
        bug_tracker.add("PerformanceRegression", "MEDIUM",
            f"存储吞吐量过低: {throughput:.0f} ops/s")
        errors = 1
    else:
        print("  ✓ 性能正常")
        errors = 0
    
    return errors


def main():
    print("="*80)
    print("MAOS 跨组件集成混沌测试")
    print("="*80)
    
    start_time = time.time()
    
    test_storage_analytics_integration()
    test_version_storage_integration()
    test_broker_analytics_integration()
    test_all_components_chaos()
    test_resource_contention()
    test_state_consistency()
    test_error_recovery()
    test_performance_regression()
    
    total_time = time.time() - start_time
    
    summary = bug_tracker.summary()
    
    print("\n" + "="*80)
    print("📋 集成测试总结")
    print("="*80)
    print(f"总Bug数: {summary['total']}")
    print(f"总测试时间: {total_time:.2f}秒")
    
    if summary['bugs']:
        print("\n发现的Bug:")
        for bug in summary['bugs']:
            print(f"\n  [{bug['severity']}] [{bug['category']}]")
            print(f"    {bug['desc'][:100]}")
    
    if summary['total'] == 0:
        print("\n✅ 所有集成测试通过！组件协作完美！")
    else:
        print(f"\n⚠️  发现 {summary['total']} 个集成问题！")
    
    return summary['total']


if __name__ == "__main__":
    main()
