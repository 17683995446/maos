#!/usr/bin/env python3
"""
MAOS 第一性原理深度测试套件 v5.0
从最基本的组件开始，质疑一切假设
核心原则：
1. 从零开始测试每个基础组件
2. 测试最底层的并发原语
3. 验证最核心的资源管理
4. 检查最关键的错误处理
"""

import threading
import time
import random
import sys
import gc
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import psutil
import os

sys.path.insert(0, '/workspace')


class FirstPrinciplesBugTracker:
    """基于第一性原理的Bug追踪器"""
    def __init__(self):
        self.bugs = []
        self.assumptions_validated = []
        self.assumptions_failed = []
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def record_bug(self, component, severity, description, assumption, stack=''):
        bug = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': time.time() - self.start_time,
            'component': component,
            'severity': severity,
            'description': description,
            'failed_assumption': assumption,
            'stack': stack
        }
        with self.lock:
            self.bugs.append(bug)
            self.assumptions_failed.append(assumption)
        
        icons = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}
        icon = icons.get(severity, '⚪')
        print(f"{icon} [{severity}] [{bug['elapsed']:.1f}s] {component}")
        print(f"   假设失败: {assumption}")
        print(f"   问题: {description[:60]}")
    
    def record_validation(self, component, assumption):
        with self.lock:
            self.assumptions_validated.append(assumption)
        print(f"✅ [{component}] 假设验证通过: {assumption}")
    
    def get_summary(self):
        with self.lock:
            return {
                'total_bugs': len(self.bugs),
                'critical': len([b for b in self.bugs if b['severity'] == 'CRITICAL']),
                'high': len([b for b in self.bugs if b['severity'] == 'HIGH']),
                'medium': len([b for b in self.bugs if b['severity'] == 'MEDIUM']),
                'low': len([b for b in self.bugs if b['severity'] == 'LOW']),
                'assumptions_validated': len(self.assumptions_validated),
                'assumptions_failed': len(self.assumptions_failed)
            }


def test_data_structures_fundamentals():
    """测试1: 数据结构基础测试（从第一性原理）"""
    print("\n" + "="*90)
    print("🔬 测试1: 数据结构基础测试（第一性原理）")
    print("="*90)
    
    tracker = FirstPrinciplesBugTracker()
    
    # 从最基础的假设开始测试
    assumptions_to_test = [
        ("字典的键值对操作是原子的", test_dict_atomicity),
        ("列表的append操作是线程安全的", test_list_append),
        ("集合的add操作是正确的", test_set_operations),
        ("字典的删除操作不会导致死锁", test_dict_deletion),
    ]
    
    for assumption_name, test_func in assumptions_to_test:
        try:
            result = test_func()
            if result['passed']:
                tracker.record_validation("DataStructures", assumption_name)
            else:
                tracker.record_bug(
                    "DataStructures",
                    result['severity'],
                    result['description'],
                    assumption_name,
                    result.get('stack', '')
                )
        except Exception as e:
            tracker.record_bug(
                "DataStructures",
                "HIGH",
                f"测试本身失败: {str(e)}",
                assumption_name,
                traceback.format_exc()
            )
    
    return tracker


def test_dict_atomicity():
    """测试假设：字典的键值对操作是原子的"""
    shared_dict = {}
    iterations = 100000
    num_threads = 20
    
    def writer(thread_id):
        for i in range(iterations):
            shared_dict[f'key_{thread_id}_{i}'] = f'value_{i}'
    
    def reader():
        for _ in range(iterations):
            _ = shared_dict.get('some_key')
    
    threads = []
    for i in range(num_threads):
        threads.append(threading.Thread(target=writer, args=(i,)))
        threads.append(threading.Thread(target=reader))
    
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start
    
    # 验证数据完整性
    expected_keys = num_threads * iterations
    actual_keys = len(shared_dict)
    data_loss_pct = ((expected_keys - actual_keys) / expected_keys * 100) if expected_keys > 0 else 0
    
    if data_loss_pct > 0:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'数据丢失: {data_loss_pct:.2f}% (期望{expected_keys}, 实际{actual_keys})'
        }
    
    return {'passed': True}


def test_list_append():
    """测试假设：列表的append操作是正确的"""
    shared_list = []
    iterations = 100000
    num_threads = 20
    
    def appender(thread_id):
        for i in range(iterations):
            shared_list.append((thread_id, i))
    
    threads = [threading.Thread(target=appender, args=(i,)) for i in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    expected_length = num_threads * iterations
    actual_length = len(shared_list)
    
    if actual_length != expected_length:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'列表长度不一致: 期望{expected_length}, 实际{actual_length}'
        }
    
    return {'passed': True}


def test_set_operations():
    """测试假设：集合的add操作是正确的"""
    shared_set = set()
    iterations = 100000
    num_threads = 20
    
    def adder(thread_id):
        for i in range(iterations):
            shared_set.add(f'{thread_id}_{i}')
    
    threads = [threading.Thread(target=adder, args=(i,)) for i in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    expected_size = num_threads * iterations
    actual_size = len(shared_set)
    
    if actual_size != expected_size:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'集合大小不一致: 期望{expected_size}, 实际{actual_size}'
        }
    
    return {'passed': True}


def test_dict_deletion():
    """测试假设：字典的删除操作不会导致问题"""
    shared_dict = {f'key_{i}': i for i in range(100000)}
    errors = []
    num_threads = 20
    
    def deleter(thread_id):
        try:
            for i in range(100000):
                key = f'key_{i}'
                if key in shared_dict:
                    del shared_dict[key]
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=deleter, args=(i,)) for i in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    if errors:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'删除操作出现{len(errors)}个错误'
        }
    
    return {'passed': True}


def test_maos_core_components():
    """测试2: MAOS核心组件基础测试"""
    print("\n" + "="*90)
    print("🔧 测试2: MAOS核心组件基础测试")
    print("="*90)
    
    # 导入必要的模块
    try:
        from maos.orchestration.orchestrator import (
            OrchestratorService, AgentRegistry, MessageBroker, EventEmitter,
            OrchestratorEvent, OrchestratorEventType
        )
        from maos.version.v14 import VersionManager, ABTestManager
        from maos.analytics.v14 import AnalyticsEngine
        import_success = True
    except ImportError as e:
        import_success = False
        print(f"⚠️  导入失败: {str(e)}")
        # 返回一个空的tracker
        tracker = FirstPrinciplesBugTracker()
        tracker.record_bug(
            "Import",
            "HIGH",
            f"无法导入MAOS核心组件: {str(e)}",
            "所有MAOS核心组件可用"
        )
        return tracker
    
    tracker = FirstPrinciplesBugTracker()
    
    # 测试核心假设
    core_tests = [
        ("AgentRegistry的register操作是线程安全的", 
         lambda: test_agent_registry_thread_safety()),
        ("MessageBroker的消息传递不丢失", 
         lambda: test_message_broker_reliability()),
        ("EventEmitter的事件广播不遗漏", 
         lambda: test_event_emitter_reliability()),
        ("VersionManager的版本管理是正确的", 
         lambda: test_version_manager_correctness()),
    ]
    
    for assumption_name, test_func in core_tests:
        try:
            result = test_func()
            if result['passed']:
                tracker.record_validation("MAOSCore", assumption_name)
            else:
                tracker.record_bug(
                    "MAOSCore",
                    result['severity'],
                    result['description'],
                    assumption_name,
                    result.get('stack', '')
                )
        except Exception as e:
            tracker.record_bug(
                "MAOSCore",
                "HIGH",
                f"核心组件测试失败: {str(e)}",
                assumption_name,
                traceback.format_exc()
            )
    
    return tracker


def test_agent_registry_thread_safety():
    """测试AgentRegistry的线程安全性"""
    registry = AgentRegistry()
    num_threads = 50
    iterations = 10000
    
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    def register_worker(thread_id):
        for i in range(iterations):
            agent = MockAgent(f'agent_{thread_id}_{i}')
            registry.register(agent)
    
    threads = [threading.Thread(target=register_worker, args=(i,)) for i in range(num_threads)]
    
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start
    
    # 验证结果
    total_agents = num_threads * iterations
    registered_agents = len(registry.get_all_agents())
    
    if registered_agents != total_agents:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'Agent注册不一致: 期望{total_agents}, 实际{registered_agents}'
        }
    
    return {'passed': True}


def test_message_broker_reliability():
    """测试MessageBroker的消息可靠性"""
    broker = MessageBroker()
    num_threads = 50
    iterations = 1000
    received_messages = []
    lock = threading.Lock()
    
    def publisher(thread_id):
        for i in range(iterations):
            msg = {'thread': thread_id, 'seq': i}
            broker.publish(msg)
    
    def subscriber():
        while len(received_messages) < num_threads * iterations:
            msg = broker.receive(timeout=0.001)
            if msg:
                with lock:
                    received_messages.append(msg)
    
    # 启动发布者
    pub_threads = [threading.Thread(target=publisher, args=(i,)) for i in range(num_threads)]
    for t in pub_threads:
        t.start()
    
    # 启动订阅者
    sub_threads = [threading.Thread(target=subscriber) for _ in range(5)]
    for t in sub_threads:
        t.start()
    
    for t in pub_threads:
        t.join()
    
    time.sleep(0.5)  # 等待剩余消息
    
    for t in sub_threads:
        t.join()
    
    expected = num_threads * iterations
    actual = len(received_messages)
    
    if actual < expected:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'消息丢失: 期望{expected}, 实际{actual}'
        }
    
    return {'passed': True}


def test_event_emitter_reliability():
    """测试EventEmitter的事件可靠性"""
    emitter = EventEmitter()
    num_threads = 30
    iterations = 1000
    events_received = []
    lock = threading.Lock()
    
    def event_handler(event):
        with lock:
            events_received.append(event)
    
    emitter.on(OrchestratorEventType.SYSTEM_ERROR, event_handler)
    
    def event_emitter(thread_id):
        for i in range(iterations):
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.SYSTEM_ERROR,
                data={'thread': thread_id, 'seq': i}
            )
            emitter.emit(event)
    
    threads = [threading.Thread(target=event_emitter, args=(i,)) for i in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    expected = num_threads * iterations
    actual = len(events_received)
    
    if actual != expected:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'事件丢失: 期望{expected}, 实际{actual}'
        }
    
    return {'passed': True}


def test_version_manager_correctness():
    """测试VersionManager的正确性"""
    vm = VersionManager()
    num_threads = 30
    iterations = 1000
    version_errors = []
    lock = threading.Lock()
    
    def version_creator(thread_id):
        for i in range(iterations):
            workflow_id = f'wf_{thread_id}'
            version_data = {
                'thread': thread_id,
                'seq': i,
                'timestamp': time.time()
            }
            try:
                vm.create_version(workflow_id, version_data)
                
                # 尝试获取最新版本
                versions = vm.list_versions(workflow_id)
                if not versions:
                    with lock:
                        version_errors.append(f'Thread {thread_id}: No versions for {workflow_id}')
                
            except Exception as e:
                with lock:
                    version_errors.append(f'Thread {thread_id}: {str(e)}')
    
    threads = [threading.Thread(target=version_creator, args=(i,)) for i in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    if version_errors:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'版本管理出现{len(version_errors)}个错误'
        }
    
    return {'passed': True}


def test_resource_management_fundamentals():
    """测试3: 资源管理基础测试"""
    print("\n" + "="*90)
    print("💾 测试3: 资源管理基础测试（第一性原理）")
    print("="*90)
    
    from maos.analytics.v14 import AnalyticsEngine
    
    tracker = FirstPrinciplesBugTracker()
    
    gc.collect()
    process = psutil.Process(os.getpid())
    initial_mem = process.memory_info().rss / 1024 / 1024
    
    assumptions = [
        ("大量对象创建不会导致内存泄漏", test_memory_leak),
        ("资源清理是及时的", test_resource_cleanup),
        ("内存增长是可控的", test_memory_growth),
    ]
    
    for assumption_name, test_func in assumptions:
        try:
            result = test_func()
            if result['passed']:
                tracker.record_validation("ResourceMgmt", assumption_name)
            else:
                tracker.record_bug(
                    "ResourceMgmt",
                    result['severity'],
                    result['description'],
                    assumption_name,
                    result.get('stack', '')
                )
        except Exception as e:
            tracker.record_bug(
                "ResourceMgmt",
                "HIGH",
                f"资源管理测试失败: {str(e)}",
                assumption_name,
                traceback.format_exc()
            )
    
    return tracker


def test_memory_leak():
    """测试假设：大量对象创建不会导致内存泄漏"""
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.orchestration.orchestrator import AgentRegistry, MessageBroker
    
    gc.collect()
    time.sleep(0.1)
    
    process = psutil.Process(os.getpid())
    initial_mem = process.memory_info().rss / 1024 / 1024
    
    # 创建大量对象
    for i in range(10000):
        vm = VersionManager()
        vm.create_version(f'wf_{i}', {'data': f'content_{i}'})
        
        ae = AnalyticsEngine()
        ae.record_metric(f'metric_{i}', i, {'tag': 'test'})
        
        registry = AgentRegistry()
        broker = MessageBroker()
    
    gc.collect()
    time.sleep(0.1)
    
    final_mem = process.memory_info().rss / 1024 / 1024
    growth = final_mem - initial_mem
    growth_pct = (growth / initial_mem * 100) if initial_mem > 0 else 0
    
    if growth_pct > 50:  # 超过50%认为有问题
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'内存增长过高: {growth:.2f}MB ({growth_pct:.2f}%)'
        }
    
    return {'passed': True}


def test_resource_cleanup():
    """测试假设：资源清理是及时的"""
    from maos.orchestration.orchestrator import AgentRegistry
    
    registry = AgentRegistry()
    
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    # 添加一些agent
    for i in range(100):
        registry.register(MockAgent(f'agent_{i}'))
    
    initial_count = len(registry.get_all_agents())
    
    # 调用清理
    registry.cleanup()
    
    # 验证清理
    after_count = len(registry.get_all_agents())
    
    if after_count != 0:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'清理后仍有{after_count}个对象'
        }
    
    return {'passed': True}


def test_memory_growth():
    """测试假设：内存增长是可控的"""
    from maos.version.v14 import VersionManager
    
    gc.collect()
    process = psutil.Process(os.getpid())
    
    samples = []
    
    for i in range(1000):
        vm = VersionManager()
        vm.create_version(f'wf_{i}', {'data': 'x' * 100})
        
        if i % 100 == 0:
            gc.collect()
            mem = process.memory_info().rss / 1024 / 1024
            samples.append(mem)
    
    if len(samples) >= 2:
        growth = samples[-1] - samples[0]
        growth_pct = (growth / samples[0] * 100) if samples[0] > 0 else 0
        
        if growth_pct > 30:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'description': f'内存增长不可控: {growth:.2f}MB ({growth_pct:.2f}%)'
            }
    
    return {'passed': True}


def test_concurrency_primitives():
    """测试4: 并发原语测试"""
    print("\n" + "="*90)
    print("🔀 测试4: 并发原语测试（第一性原理）")
    print("="*90)
    
    tracker = FirstPrinciplesBugTracker()
    
    assumptions = [
        ("Lock机制可以防止竞态条件", test_lock_effectiveness),
        ("RLock可以重入", test_rlock_reentrancy),
        ("Barrier可以同步线程", test_barrier_sync),
        ("Condition可以正确等待和通知", test_condition_signal),
        ("Semaphore可以限制并发", test_semaphore_limit),
    ]
    
    for assumption_name, test_func in assumptions:
        try:
            result = test_func()
            if result['passed']:
                tracker.record_validation("Concurrency", assumption_name)
            else:
                tracker.record_bug(
                    "Concurrency",
                    result['severity'],
                    result['description'],
                    assumption_name,
                    result.get('stack', '')
                )
        except Exception as e:
            tracker.record_bug(
                "Concurrency",
                "HIGH",
                f"并发原语测试失败: {str(e)}",
                assumption_name,
                traceback.format_exc()
            )
    
    return tracker


def test_lock_effectiveness():
    """测试假设：Lock机制可以防止竞态条件"""
    counter = {'value': 0}
    lock = threading.Lock()
    iterations = 100000
    num_threads = 20
    
    def increment_with_lock():
        for _ in range(iterations):
            with lock:
                counter['value'] += 1
    
    threads = [threading.Thread(target=increment_with_lock) for _ in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    expected = iterations * num_threads
    actual = counter['value']
    
    if actual != expected:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'Lock无效: 期望{expected}, 实际{actual}'
        }
    
    return {'passed': True}


def test_rlock_reentrancy():
    """测试假设：RLock可以重入"""
    rlock = threading.RLock()
    errors = []
    
    def recursive_worker(depth):
        if depth == 0:
            return
        with rlock:
            if depth == 10:
                try:
                    with rlock:
                        errors.append(f'Deep reentrant at depth {depth}')
                except:
                    pass
            recursive_worker(depth - 1)
    
    try:
        with rlock:
            recursive_worker(10)
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'RLock重入失败: {str(e)}'
        }
    
    return {'passed': True}


def test_barrier_sync():
    """测试假设：Barrier可以同步线程"""
    barrier = threading.Barrier(10)
    results = []
    lock = threading.Lock()
    
    def worker(worker_id):
        barrier.wait()  # 等待所有线程
        with lock:
            results.append(worker_id)
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    if len(results) != 10:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'Barrier同步失败: 只有{len(results)}个线程完成'
        }
    
    return {'passed': True}


def test_condition_signal():
    """测试假设：Condition可以正确等待和通知"""
    condition = threading.Condition()
    flag = {'set': False}
    lock = threading.Lock()
    
    def waiter():
        with lock:
            while not flag['set']:
                condition.wait(timeout=1)
        return flag['set']
    
    def notifier():
        time.sleep(0.1)
        with condition:
            flag['set'] = True
            condition.notify()
    
    t1 = threading.Thread(target=waiter)
    t2 = threading.Thread(target=notifier)
    
    t1.start()
    t2.start()
    
    t1.join(timeout=2)
    t2.join()
    
    if not flag['set']:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': 'Condition信号未正确传递'
        }
    
    return {'passed': True}


def test_semaphore_limit():
    """测试假设：Semaphore可以限制并发"""
    semaphore = threading.Semaphore(5)
    active = {'count': 0, 'max': 0}
    lock = threading.Lock()
    
    def worker():
        with semaphore:
            with lock:
                active['count'] += 1
                active['max'] = max(active['max'], active['count'])
            
            time.sleep(0.01)
            
            with lock:
                active['count'] -= 1
    
    threads = [threading.Thread(target=worker) for _ in range(20)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    if active['max'] > 5:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': f'Semaphore限制失效: 最大并发{active["max"]}'
        }
    
    return {'passed': True}


def test_error_handling_fundamentals():
    """测试5: 错误处理基础测试"""
    print("\n" + "="*90)
    print("⚠️ 测试5: 错误处理基础测试（第一性原理）")
    print("="*90)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    tracker = FirstPrinciplesBugTracker()
    
    assumptions = [
        ("无效输入会被正确处理", test_invalid_input_handling),
        ("异常不会导致系统崩溃", test_exception_isolation),
        ("错误后系统可以继续工作", test_recovery_after_error),
    ]
    
    for assumption_name, test_func in assumptions:
        try:
            result = test_func()
            if result['passed']:
                tracker.record_validation("ErrorHandling", assumption_name)
            else:
                tracker.record_bug(
                    "ErrorHandling",
                    result['severity'],
                    result['description'],
                    assumption_name,
                    result.get('stack', '')
                )
        except Exception as e:
            tracker.record_bug(
                "ErrorHandling",
                "HIGH",
                f"错误处理测试失败: {str(e)}",
                assumption_name,
                traceback.format_exc()
            )
    
    return tracker


def test_invalid_input_handling():
    """测试假设：无效输入会被正确处理"""
    from maos.version.v14 import VersionManager
    
    vm = VersionManager()
    invalid_inputs = [
        None,
        '',
        {'nested': {'deep': 'value'}},
        [],
        123,
        'x' * 1000000,
    ]
    
    errors = []
    for invalid_input in invalid_inputs:
        try:
            vm.create_version('test_wf', invalid_input)
        except Exception as e:
            errors.append(str(e))
    
    # 验证系统仍然工作
    try:
        vm.create_version('recovery_test', {'valid': True})
    except:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': '无效输入后系统无法恢复'
        }
    
    return {'passed': True}


def test_exception_isolation():
    """测试假设：异常不会导致系统崩溃"""
    from maos.analytics.v14 import AnalyticsEngine
    
    ae = AnalyticsEngine()
    
    # 故意制造错误
    try:
        ae.record_metric(None, None, None)
    except:
        pass
    
    try:
        ae.record_metric('', float('nan'), {})
    except:
        pass
    
    # 验证系统仍然工作
    try:
        ae.record_metric('recovery', 1, {})
        summary = ae.get_summary()
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'异常后系统崩溃: {str(e)}'
        }
    
    return {'passed': True}


def test_recovery_after_error():
    """测试假设：错误后系统可以继续工作"""
    from maos.orchestration.orchestrator import AgentRegistry
    
    registry = AgentRegistry()
    
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    # 先正常工作
    registry.register(MockAgent('normal_agent'))
    
    # 尝试无效操作
    try:
        registry.register(None)  # 应该失败
    except:
        pass
    
    # 验证系统仍然工作
    try:
        registry.register(MockAgent('after_error_agent'))
        agents = registry.get_all_agents()
        
        if len(agents) != 2:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'description': f'错误恢复后agent数量不正确: {len(agents)}'
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': f'错误后系统无法恢复: {str(e)}'
        }
    
    return {'passed': True}


def run_all_first_principles_tests():
    """运行所有第一性原理测试"""
    print("="*90)
    print("🚀 MAOS 第一性原理深度测试 v5.0")
    print("="*90)
    print(f"开始时间: {datetime.now().isoformat()}")
    print("核心原则：从零开始，质疑一切假设")
    print("="*90)
    
    all_trackers = []
    overall_summary = defaultdict(int)
    
    tests = [
        ("数据结构基础", test_data_structures_fundamentals),
        ("MAOS核心组件", test_maos_core_components),
        ("资源管理基础", test_resource_management_fundamentals),
        ("并发原语", test_concurrency_primitives),
        ("错误处理基础", test_error_handling_fundamentals),
    ]
    
    for test_name, test_func in tests:
        try:
            tracker = test_func()
            all_trackers.append(tracker)
            
            summary = tracker.get_summary()
            for key, value in summary.items():
                overall_summary[key] += value
            
            print(f"\n✅ {test_name} 完成")
            print(f"   假设验证通过: {summary['assumptions_validated']}")
            print(f"   假设失败: {summary['assumptions_failed']}")
            print(f"   发现Bug: {summary['total_bugs']}")
            
        except Exception as e:
            print(f"\n❌ {test_name} 执行失败: {str(e)}")
            traceback.print_exc()
    
    # 最终报告
    print("\n" + "="*90)
    print("📊 第一性原理测试 - 最终报告")
    print("="*90)
    
    print(f"\n📝 假设验证结果:")
    print(f"   ✅ 验证通过: {overall_summary['assumptions_validated']}")
    print(f"   ❌ 验证失败: {overall_summary['assumptions_failed']}")
    
    print(f"\n🐛 Bug发现统计:")
    print(f"   总计: {overall_summary['total_bugs']}")
    print(f"   🔴 CRITICAL: {overall_summary['critical']}")
    print(f"   🟠 HIGH: {overall_summary['high']}")
    print(f"   🟡 MEDIUM: {overall_summary['medium']}")
    print(f"   🔵 LOW: {overall_summary['low']}")
    
    # 健康评分
    health_score = 100
    health_score -= overall_summary['critical'] * 20
    health_score -= overall_summary['high'] * 10
    health_score -= overall_summary['medium'] * 5
    health_score -= overall_summary['low'] * 1
    health_score = max(0, health_score)
    
    print(f"\n🏥 系统健康评分: {health_score}/100")
    
    if health_score >= 90:
        status = "🌟 优秀"
    elif health_score >= 70:
        status = "✅ 良好"
    elif health_score >= 50:
        status = "⚠️ 一般"
    else:
        status = "❌ 需改进"
    
    print(f"   状态: {status}")
    
    # 列出所有失败的假设
    if overall_summary['assumptions_failed'] > 0:
        print(f"\n❌ 失败的假设:")
        for tracker in all_trackers:
            for bug in tracker.bugs:
                print(f"   - {bug['failed_assumption']}")
                print(f"     组件: {bug['component']}")
                print(f"     问题: {bug['description'][:60]}")
    
    print("\n" + "="*90)
    print("✅ 第一性原理测试完成")
    print("="*90)
    
    return all_trackers


if __name__ == '__main__':
    run_all_first_principles_tests()
