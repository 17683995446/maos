#!/usr/bin/env python3
"""
MAOS 超极端测试套件 v4.0 - 专门发现最微妙的bug
测试类型：
1. 内存泄漏检测（长时间运行）
2. 竞态条件探测（极端并发）
3. 边缘情况（极限值输入）
4. 资源耗尽（大量对象创建）
5. 异常处理（故意制造错误）
6. 性能退化检测（运行时监控）
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

from maos.orchestration.orchestrator import (
    OrchestratorService, AgentRegistry, MessageBroker, EventEmitter,
    OrchestratorEvent, OrchestratorEventType
)
from maos.security.enhanced import JWTToken, OAuth2Server, JWTClaims
from maos.version.v14 import VersionManager, ABTestManager
from maos.analytics.v14 import AnalyticsEngine
from maos.storage.in_memory import InMemoryChatStorage


class ExtremeBugDetector:
    """极端情况Bug探测器"""
    def __init__(self):
        self.bugs = []
        self.warnings = []
        self.performance_data = []
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def record_bug(self, category, severity, description, stack='', details=None):
        bug = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': time.time() - self.start_time,
            'category': category,
            'severity': severity,
            'description': description,
            'stack_trace': stack,
            'details': details or {}
        }
        with self.lock:
            self.bugs.append(bug)
        
        icons = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}
        icon = icons.get(severity, '⚪')
        print(f"{icon} [{severity}] [{bug['elapsed']:.1f}s] {category}: {description[:80]}")
    
    def record_warning(self, category, description):
        warning = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': time.time() - self.start_time,
            'category': category,
            'description': description
        }
        with self.lock:
            self.warnings.append(warning)
        print(f"⚠️  [{warning['elapsed']:.1f}s] {category}: {description[:80]}")
    
    def record_performance(self, phase, operation, duration_ms, iteration):
        data = {
            'phase': phase,
            'operation': operation,
            'duration_ms': duration_ms,
            'iteration': iteration,
            'timestamp': time.time()
        }
        with self.lock:
            self.performance_data.append(data)
    
    def get_summary(self):
        with self.lock:
            return {
                'total_bugs': len(self.bugs),
                'critical': len([b for b in self.bugs if b['severity'] == 'CRITICAL']),
                'high': len([b for b in self.bugs if b['severity'] == 'HIGH']),
                'medium': len([b for b in self.bugs if b['severity'] == 'MEDIUM']),
                'low': len([b for b in self.bugs if b['severity'] == 'LOW']),
                'warnings': len(self.warnings)
            }


def test_1_memory_leak_detector():
    """测试1: 内存泄漏检测器（5分钟）"""
    print("\n" + "="*90)
    print("💾 测试1: 内存泄漏检测器 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    gc.collect()
    process = psutil.Process(os.getpid())
    initial_mem = process.memory_info().rss / 1024 / 1024
    print(f"初始内存: {initial_mem:.2f} MB")
    
    start_time = time.time()
    iteration = 0
    memory_samples = []
    
    while time.time() - start_time < 300:
        iteration += 1
        
        try:
            # 快速创建大量对象
            for i in range(100):
                vm = VersionManager()
                ae = AnalyticsEngine()
                broker = MessageBroker()
                registry = AgentRegistry()
                
                for j in range(10):
                    vm.create_version(f'wf_{iteration}_{i}_{j}', {
                        'data': 'x' * 100,
                        'timestamp': time.time()
                    })
                    ae.record_metric(f'metric_{iteration}_{i}_{j}', j, {'tag': 'test'})
            
            # 每100次采样内存
            if iteration % 100 == 0:
                gc.collect()
                current_mem = process.memory_info().rss / 1024 / 1024
                growth = current_mem - initial_mem
                growth_pct = (growth / initial_mem * 100) if initial_mem > 0 else 0
                
                memory_samples.append({
                    'iteration': iteration,
                    'mem_mb': current_mem,
                    'growth_mb': growth,
                    'growth_pct': growth_pct
                })
                
                elapsed = time.time() - start_time
                print(f"  [{elapsed:.1f}s] 迭代 {iteration}: 内存 {current_mem:.1f}MB (增长 {growth:.1f}MB / {growth_pct:.1f}%)")
                
                # 检查是否有内存泄漏
                if growth_pct > 30:
                    detector.record_bug(
                        'Memory Leak',
                        'HIGH',
                        f'疑似内存泄漏: 增长 {growth:.2f}MB ({growth_pct:.2f}%)',
                        details={'iteration': iteration, 'mem_mb': current_mem}
                    )
                
        except Exception as e:
            detector.record_bug(
                'Memory Test',
                'MEDIUM',
                f'内存测试错误: {str(e)}',
                stack=traceback.format_exc()
            )
    
    # 最终分析
    gc.collect()
    final_mem = process.memory_info().rss / 1024 / 1024
    total_growth = final_mem - initial_mem
    total_growth_pct = (total_growth / initial_mem * 100) if initial_mem > 0 else 0
    
    print(f"\n内存增长: {total_growth:.2f}MB ({total_growth_pct:.2f}%)")
    print(f"迭代次数: {iteration}")
    return detector


def test_2_race_condition_extreme():
    """测试2: 极端竞态条件探测（5分钟）"""
    print("\n" + "="*90)
    print("🔀 测试2: 极端竞态条件探测 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    race_conditions_found = 0
    
    start_time = time.time()
    
    while time.time() - start_time < 300:
        try:
            # 测试1: 共享计数器竞态
            shared = {'counter': 0, 'list': []}
            threads = []
            iterations_per_thread = 10000
            num_threads = 20
            
            def increment_worker():
                for _ in range(iterations_per_thread):
                    shared['counter'] += 1
            
            def append_worker(val):
                for i in range(iterations_per_thread):
                    shared['list'].append(f'{val}_{i}')
            
            # 启动大量并发线程
            for i in range(num_threads):
                t1 = threading.Thread(target=increment_worker)
                t2 = threading.Thread(target=append_worker, args=(i,))
                threads.append(t1)
                threads.append(t2)
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # 验证结果
            expected_counter = iterations_per_thread * num_threads
            actual_counter = shared['counter']
            counter_diff = expected_counter - actual_counter
            
            expected_list_len = iterations_per_thread * num_threads
            actual_list_len = len(shared['list'])
            list_diff = expected_list_len - actual_list_len
            
            if counter_diff != 0:
                race_conditions_found += 1
                detector.record_bug(
                    'Race Condition',
                    'HIGH',
                    f'计数器竞态: 期望 {expected_counter}, 实际 {actual_counter}, 丢失 {counter_diff}',
                    details={'threads': num_threads, 'iterations': iterations_per_thread}
                )
            
            if list_diff != 0:
                race_conditions_found += 1
                detector.record_bug(
                    'Race Condition',
                    'HIGH',
                    f'列表竞态: 期望 {expected_list_len}, 实际 {actual_list_len}, 丢失 {list_diff}',
                    details={'threads': num_threads, 'iterations': iterations_per_thread}
                )
            
            elapsed = time.time() - start_time
            if race_conditions_found > 0 or int(elapsed) % 30 == 0:
                print(f"  [{elapsed:.1f}s] 发现 {race_conditions_found} 个竞态条件")
            
        except Exception as e:
            detector.record_bug(
                'Race Test',
                'MEDIUM',
                f'竞态测试错误: {str(e)}',
                stack=traceback.format_exc()
            )
    
    print(f"总计发现 {race_conditions_found} 个竞态条件")
    return detector


def test_3_edge_case_fuzzing():
    """测试3: 边界情况模糊测试（5分钟）"""
    print("\n" + "="*90)
    print("🎯 测试3: 边界情况模糊测试 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    
    # 生成极端边界情况
    edge_cases = []
    
    # 空值
    edge_cases.extend([
        ('', 'empty_string'),
        (None, 'none_value'),
        ([], 'empty_list'),
        ({}, 'empty_dict'),
        ((None,), 'tuple_with_none'),
    ])
    
    # 巨大值
    edge_cases.extend([
        ('x' * 1000000, 'huge_string'),
        ([i for i in range(100000)], 'huge_list'),
        ({f'key_{i}': f'value_{i}' for i in range(10000)}, 'huge_dict'),
    ])
    
    # 嵌套值
    deep_nested = {}
    current = deep_nested
    for i in range(1000):
        current['level'] = i
        current['next'] = {}
        current = current['next']
    edge_cases.append((deep_nested, 'deep_nested_dict'))
    
    # 特殊字符
    edge_cases.extend([
        ('\x00\x01\x02\x03', 'control_chars'),
        ('<script>alert("XSS")</script>', 'xss'),
        ("'; DROP TABLE users; --", 'sql_injection'),
        ('../../../etc/passwd', 'path_traversal'),
        ('%20%20%20', 'url_encoded'),
    ])
    
    # Unicode和Emoji
    edge_cases.extend([
        ('中文测试', 'chinese'),
        ('👩‍💻🎉🚀', 'emoji'),
        ('🌍' * 1000, 'many_emoji'),
    ])
    
    # 数字边界
    edge_cases.extend([
        (sys.maxsize, 'max_int'),
        (-sys.maxsize - 1, 'min_int'),
        (1e308, 'max_float'),
        (1e-308, 'min_float'),
        (float('inf'), 'infinity'),
        (float('-inf'), '-infinity'),
        (float('nan'), 'nan'),
    ])
    
    start_time = time.time()
    iteration = 0
    
    while time.time() - start_time < 300:
        for test_input, case_name in edge_cases:
            iteration += 1
            
            try:
                # 测试各种模块
                vm = VersionManager()
                vm.create_version(f'fuzz_{iteration}', {'input': test_input, 'type': case_name})
                
                ae = AnalyticsEngine()
                ae.record_metric(f'fuzz_metric_{iteration}', 1, {'value': test_input})
                
            except Exception as e:
                detector.record_bug(
                    'Edge Case',
                    'MEDIUM',
                    f'{case_name} 处理失败: {str(e)}',
                    stack=traceback.format_exc(),
                    details={'input_type': case_name}
                )
        
        if iteration % 1000 == 0:
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.1f}s] 迭代 {iteration}")
    
    print(f"总计执行 {iteration} 个边界测试")
    return detector


def test_4_concurrent_resource_stress():
    """测试4: 并发资源压力测试（5分钟）"""
    print("\n" + "="*90)
    print("⚡ 测试4: 并发资源压力测试 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    
    start_time = time.time()
    total_tasks = 0
    
    def worker(task_id):
        try:
            # 创建各种资源
            brokers = [MessageBroker() for _ in range(10)]
            registries = [AgentRegistry() for _ in range(10)]
            vms = [VersionManager() for _ in range(10)]
            
            for i in range(50):
                for vm in vms:
                    vm.create_version(f'task_{task_id}_wf_{i}', {'data': i})
            
            return True
        except Exception as e:
            detector.record_bug(
                'Concurrent Stress',
                'MEDIUM',
                f'Worker {task_id} 错误: {str(e)}',
                stack=traceback.format_exc()
            )
            return False
    
    while time.time() - start_time < 300:
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(50):
                futures.append(executor.submit(worker, total_tasks + i))
            
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
            
            total_tasks += 50
        
        if total_tasks % 500 == 0:
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.1f}s] 执行 {total_tasks} 个任务")
    
    print(f"总计执行 {total_tasks} 个并发任务")
    return detector


def test_5_error_recovery_extreme():
    """测试5: 极端错误恢复测试（5分钟）"""
    print("\n" + "="*90)
    print("🔧 测试5: 极端错误恢复测试 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    
    start_time = time.time()
    iteration = 0
    
    error_scenarios = [
        ('invalid_dict', {'this_is': 'very_invalid'}),
        ('deep_nested_error', {'a': {'b': {'c': {'d': {}}}}}),
        ('list_with_errors', [1, 'two', None, {'x': 5}]),
    ]
    
    while time.time() - start_time < 300:
        for scenario_name, scenario_data in error_scenarios:
            iteration += 1
            
            try:
                # 故意尝试无效操作
                vm = VersionManager()
                vm.create_version(f'err_{iteration}', scenario_data)
                
                # 尝试更多边缘操作
                ae = AnalyticsEngine()
                ae.record_metric('test_metric', 'not_a_number', scenario_data)
                
            except Exception as e:
                # 这是预期的，但是要确保系统可以恢复
                pass
            
            try:
                # 验证系统在错误后仍然工作
                vm2 = VersionManager()
                vm2.create_version(f'after_err_{iteration}', {'valid': True})
            except Exception as e:
                detector.record_bug(
                    'Error Recovery',
                    'HIGH',
                    f'错误后系统无法恢复: {str(e)}',
                    stack=traceback.format_exc(),
                    details={'scenario': scenario_name}
                )
        
        if iteration % 500 == 0:
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.1f}s] 迭代 {iteration}")
    
    print(f"总计执行 {iteration} 个错误恢复测试")
    return detector


def test_6_chaos_engineering_advanced():
    """测试6: 高级混沌工程测试（5分钟）"""
    print("\n" + "="*90)
    print("🌪️ 测试6: 高级混沌工程测试 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    
    chaos_scenarios = [
        'rapid_object_creation',
        'memory_spike',
        'thread_storm',
        'file_descriptor_spam',
    ]
    
    start_time = time.time()
    chaos_tests = 0
    resilience_score = 0
    
    while time.time() - start_time < 300:
        chaos_tests += 1
        scenario = random.choice(chaos_scenarios)
        
        try:
            if scenario == 'rapid_object_creation':
                objects = []
                for i in range(1000):
                    objects.append(VersionManager())
                    objects.append(AgentRegistry())
                    objects.append(MessageBroker())
                
            elif scenario == 'memory_spike':
                data = ['x' * 100000 for _ in range(1000)]
                
            elif scenario == 'thread_storm':
                def dummy():
                    time.sleep(0.01)
                
                threads = [threading.Thread(target=dummy) for _ in range(200)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
            
            resilience_score += 1
            
        except Exception as e:
            detector.record_bug(
                'Chaos Engineering',
                'MEDIUM',
                f'混沌场景 {scenario} 失败: {str(e)}',
                stack=traceback.format_exc()
            )
        
        if chaos_tests % 100 == 0:
            elapsed = time.time() - start_time
            resilience_pct = (resilience_score / chaos_tests * 100) if chaos_tests > 0 else 0
            print(f"  [{elapsed:.1f}s] 混沌测试 {chaos_tests}, 韧性 {resilience_pct:.0f}%")
    
    print(f"总计执行 {chaos_tests} 个混沌测试, 韧性 {resilience_score}")
    return detector


def test_7_lifecycle_extreme():
    """测试7: 生命周期极端测试（5分钟）"""
    print("\n" + "="*90)
    print("♻️ 测试7: 生命周期极端测试 (5分钟)")
    print("="*90)
    
    detector = ExtremeBugDetector()
    
    start_time = time.time()
    iteration = 0
    
    while time.time() - start_time < 300:
        iteration += 1
        
        try:
            # 快速创建和销毁对象
            for i in range(100):
                vm = VersionManager()
                vm.create_version(f'lifecycle_{iteration}_{i}', {'test': 'data'})
                
                ae = AnalyticsEngine()
                for j in range(5):
                    ae.record_metric(f'lifecycle_{iteration}_{i}_{j}', j, {})
                
                broker = MessageBroker()
                registry = AgentRegistry()
                
                # 不调用cleanup，让Python清理
                del vm
                del ae
                del broker
                del registry
            
            if iteration % 100 == 0:
                gc.collect()
                elapsed = time.time() - start_time
                current_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                print(f"  [{elapsed:.1f}s] 迭代 {iteration}, 内存 {current_mem:.1f}MB")
        
        except Exception as e:
            detector.record_bug(
                'Lifecycle',
                'MEDIUM',
                f'生命周期错误: {str(e)}',
                stack=traceback.format_exc()
            )
    
    print(f"总计执行 {iteration} 个生命周期测试")
    return detector


def run_all_extreme_tests():
    """运行所有极端测试"""
    print("="*90)
    print("🚀 MAOS 超极端测试套件 v4.0")
    print("="*90)
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"目标运行时间: 35分钟")
    print("="*90)
    
    all_detectors = []
    overall_summary = defaultdict(int)
    
    tests = [
        ("内存泄漏检测", test_1_memory_leak_detector),
        ("极端竞态条件", test_2_race_condition_extreme),
        ("边界情况模糊", test_3_edge_case_fuzzing),
        ("并发资源压力", test_4_concurrent_resource_stress),
        ("极端错误恢复", test_5_error_recovery_extreme),
        ("高级混沌工程", test_6_chaos_engineering_advanced),
        ("生命周期极端", test_7_lifecycle_extreme),
    ]
    
    for test_name, test_func in tests:
        try:
            detector = test_func()
            all_detectors.append(detector)
            
            summary = detector.get_summary()
            for key, value in summary.items():
                overall_summary[key] += value
            
            print(f"\n✅ {test_name} 完成")
            print(f"   发现: {summary['total_bugs']} 个bug, {summary['warnings']} 个警告")
            
        except Exception as e:
            print(f"\n❌ {test_name} 执行失败: {str(e)}")
            traceback.print_exc()
    
    # 最终报告
    print("\n" + "="*90)
    print("📊 超极端测试 - 最终报告")
    print("="*90)
    
    print(f"\n🐛 总计发现:")
    print(f"   🔴 CRITICAL: {overall_summary['critical']}")
    print(f"   🟠 HIGH: {overall_summary['high']}")
    print(f"   🟡 MEDIUM: {overall_summary['medium']}")
    print(f"   🔵 LOW: {overall_summary['low']}")
    print(f"   ⚠️  警告: {overall_summary['warnings']}")
    print(f"   总计: {overall_summary['total_bugs']}")
    
    # 计算健康评分
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
    
    # 列出所有发现的bug
    if overall_summary['total_bugs'] > 0:
        print(f"\n📝 所有发现的bug (前20个):")
        bug_count = 0
        for detector in all_detectors:
            for bug in detector.bugs:
                bug_count += 1
                if bug_count > 20:
                    break
                print(f"\n   [{bug_count}] {bug['category']} - {bug['severity']}")
                print(f"       {bug['description']}")
        
        if overall_summary['total_bugs'] > 20:
            print(f"\n   ... 还有 {overall_summary['total_bugs'] - 20} 个bug")
    
    print("\n" + "="*90)
    print("✅ 超极端测试完成")
    print("="*90)
    
    return all_detectors


if __name__ == '__main__':
    run_all_extreme_tests()
