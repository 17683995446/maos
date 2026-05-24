#!/usr/bin/env python3
"""
MAOS 超长时间极限测试套件 v3.0
运行时间：至少1小时
目标：发现系统在长时间真实运行时的所有潜在bug
"""

import threading
import time
import random
import sys
import gc
import traceback
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
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


class UltraLongBugTracker:
    """超长时间Bug追踪器"""
    def __init__(self):
        self.bugs: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def record_bug(self, category: str, severity: str, description: str, 
                   stack_trace: str = ""):
        bug = {
            'timestamp': datetime.now().isoformat(),
            'timestamp_unix': time.time(),
            'category': category,
            'severity': severity,
            'description': description,
            'stack_trace': stack_trace
        }
        with self.lock:
            self.bugs.append(bug)
        
        icons = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}
        icon = icons.get(severity, '⚪')
        elapsed = time.time() - start_time
        print(f"{icon} [{severity}] [{elapsed:.1f}s] {category}: {description[:100]}")
    
    def get_summary(self) -> Dict[str, int]:
        with self.lock:
            return {
                'total': len(self.bugs),
                'critical': len([b for b in self.bugs if b['severity'] == 'CRITICAL']),
                'high': len([b for b in self.bugs if b['severity'] == 'HIGH']),
                'medium': len([b for b in self.bugs if b['severity'] == 'MEDIUM']),
                'low': len([b for b in self.bugs if b['severity'] == 'LOW']),
                'warnings': len(self.warnings)
            }


# 全局变量
start_time = time.time()
bug_tracker = UltraLongBugTracker()


class TestPhase:
    """测试阶段"""
    def __init__(self, name: str, duration_seconds: int, test_func: callable):
        self.name = name
        self.duration_seconds = duration_seconds
        self.test_func = test_func
        self.start_time = 0
        self.end_time = 0
        self.operations = 0
        self.errors = 0


def phase1_continuous_operation():
    """阶段1: 连续运行测试 - 20分钟"""
    print(f"\n{'='*90}")
    print(f"⏱️  阶段1: 连续运行测试 (20分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("连续运行测试", 1200, phase1_continuous_operation)
    phase.start_time = time.time()
    
    operations = 0
    errors = 0
    
    # 运行20分钟
    while time.time() - phase.start_time < 1200:
        try:
            # 创建各种组件
            registry = AgentRegistry()
            broker = MessageBroker()
            emitter = EventEmitter()
            vm = VersionManager()
            ae = AnalyticsEngine()
            
            # 执行操作
            registry.register({
                'id': f'agent_{operations}',
                'name': f'Agent {operations}',
                'type': 'test'
            })
            
            broker.publish({'channel': 'test', 'data': operations})
            
            vm.create_version(f'wf_{operations}', {'data': operations})
            ae.record_metric('test_metric', operations, {'tag': 'continuous'})
            
            operations += 4
            
            # 每10000次报告一次
            if operations % 10000 == 0:
                elapsed = time.time() - phase.start_time
                print(f"  [{elapsed:.1f}s] 操作: {operations}, 错误: {errors}")
        
        except Exception as e:
            errors += 1
            bug_tracker.record_bug(
                'Continuous Operation',
                'MEDIUM',
                f'连续运行错误 (op {operations}): {str(e)}',
                traceback.format_exc()
            )
    
    phase.end_time = time.time()
    phase.operations = operations
    phase.errors = errors
    
    print(f"  完成: {operations} 操作, {errors} 错误, 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def phase2_concurrent_stress():
    """阶段2: 并发压力测试 - 15分钟"""
    print(f"\n{'='*90}")
    print(f"⚡ 阶段2: 并发压力测试 (15分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("并发压力测试", 900, phase2_concurrent_stress)
    phase.start_time = time.time()
    
    total_operations = 0
    total_errors = 0
    
    # 持续运行15分钟
    while time.time() - phase.start_time < 900:
        try:
            def worker(worker_id):
                ops = 0
                errs = 0
                for i in range(100):
                    try:
                        vm = VersionManager()
                        vm.create_version(f'wf_{worker_id}_{i}', {'data': i})
                        ops += 1
                    except Exception as e:
                        errs += 1
                        bug_tracker.record_bug(
                            'Concurrent Stress',
                            'MEDIUM',
                            f'并发worker {worker_id} 错误: {str(e)}',
                            traceback.format_exc()
                        )
                return ops, errs
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(worker, i) for i in range(50)]
                results = [f.result() for f in as_completed(futures)]
                
                for ops, errs in results:
                    total_operations += ops
                    total_errors += errs
            
            elapsed = time.time() - phase.start_time
            print(f"  [{elapsed:.1f}s] 总操作: {total_operations}, 总错误: {total_errors}")
        
        except Exception as e:
            total_errors += 1
            bug_tracker.record_bug(
                'Concurrent Stress',
                'HIGH',
                f'并发压力测试主循环错误: {str(e)}',
                traceback.format_exc()
            )
    
    phase.end_time = time.time()
    phase.operations = total_operations
    phase.errors = total_errors
    
    print(f"  完成: {total_operations} 操作, {total_errors} 错误, 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def phase3_memory_pressure():
    """阶段3: 内存压力测试 - 10分钟"""
    print(f"\n{'='*90}")
    print(f"💾 阶段3: 内存压力测试 (10分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("内存压力测试", 600, phase3_memory_pressure)
    phase.start_time = time.time()
    
    gc.collect()
    initial_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    print(f"  初始内存: {initial_mem:.2f} MB")
    
    operations = 0
    errors = 0
    leak_suspected = False
    
    # 运行10分钟
    while time.time() - phase.start_time < 600:
        try:
            for i in range(100):
                vm = VersionManager()
                vm.create_version(f'wf_mem_{operations}', {
                    'data': 'x' * 1000,
                    'timestamp': time.time()
                })
                operations += 1
            
            # 每1000次检查内存
            if operations % 1000 == 0:
                gc.collect()
                current_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                growth = current_mem - initial_mem
                growth_pct = (growth / initial_mem * 100) if initial_mem > 0 else 0
                
                elapsed = time.time() - phase.start_time
                print(f"  [{elapsed:.1f}s] 操作: {operations}, 内存: {current_mem:.2f}MB, 增长: {growth:.2f}MB ({growth_pct:.2f}%)")
                
                # 如果增长超过50%认为有内存泄漏
                if growth_pct > 50 and not leak_suspected:
                    leak_suspected = True
                    bug_tracker.record_bug(
                        'Memory Leak',
                        'HIGH',
                        f'疑似内存泄漏: 增长 {growth:.2f}MB ({growth_pct:.2f}%)',
                        f'操作数: {operations}'
                    )
        
        except Exception as e:
            errors += 1
            bug_tracker.record_bug(
                'Memory Pressure',
                'MEDIUM',
                f'内存压力测试错误: {str(e)}',
                traceback.format_exc()
            )
    
    gc.collect()
    final_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    growth = final_mem - initial_mem
    growth_pct = (growth / initial_mem * 100) if initial_mem > 0 else 0
    
    phase.end_time = time.time()
    phase.operations = operations
    phase.errors = errors
    
    print(f"  完成: {operations} 操作, {errors} 错误")
    print(f"  初始内存: {initial_mem:.2f}MB, 最终内存: {final_mem:.2f}MB")
    print(f"  增长: {growth:.2f}MB ({growth_pct:.2f}%), 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def phase4_race_condition_probing():
    """阶段4: 竞态条件探测 - 10分钟"""
    print(f"\n{'='*90}")
    print(f"🔀 阶段4: 竞态条件探测 (10分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("竞态条件探测", 600, phase4_race_condition_probing)
    phase.start_time = time.time()
    
    race_conditions_found = 0
    operations = 0
    
    # 运行10分钟
    while time.time() - phase.start_time < 600:
        try:
            # 测试各种共享资源的竞态条件
            shared_data = {'counter': 0, 'list': []}
            lock = threading.Lock()
            iterations = 10000
            
            def increment_counter():
                for _ in range(iterations):
                    shared_data['counter'] += 1
            
            def append_list(value):
                for i in range(iterations):
                    shared_data['list'].append(value + i)
            
            # 启动多个线程同时修改
            threads = []
            for i in range(10):
                threads.append(threading.Thread(target=increment_counter))
                threads.append(threading.Thread(target=append_list, args=(i,)))
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            operations += iterations * 10 * 2
            
            # 检查数据一致性
            expected_counter = iterations * 10
            actual_counter = shared_data['counter']
            lost = expected_counter - actual_counter
            
            if lost > 0:
                race_conditions_found += 1
                bug_tracker.record_bug(
                    'Race Condition',
                    'HIGH',
                    f'计数器竞态: 期望 {expected_counter}, 实际 {actual_counter}, 丢失 {lost}',
                    f'线程数: 20, 迭代: {iterations}'
                )
            
            elapsed = time.time() - phase.start_time
            if race_conditions_found > 0 or operations % 100000 < 1000:
                print(f"  [{elapsed:.1f}s] 操作: {operations}, 竞态: {race_conditions_found}")
        
        except Exception as e:
            bug_tracker.record_bug(
                'Race Condition Probe',
                'MEDIUM',
                f'竞态探测错误: {str(e)}',
                traceback.format_exc()
            )
    
    phase.end_time = time.time()
    phase.operations = operations
    
    print(f"  完成: {operations} 操作, 发现 {race_conditions_found} 个竞态条件, 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def phase5_edge_case_probing():
    """阶段5: 边界条件探测 - 5分钟"""
    print(f"\n{'='*90}")
    print(f"🎯 阶段5: 边界条件探测 (5分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("边界条件探测", 300, phase5_edge_case_probing)
    phase.start_time = time.time()
    
    operations = 0
    errors = 0
    
    edge_cases = [
        ('', '空字符串'),
        (None, 'None值'),
        ({}, '空字典'),
        ([], '空列表'),
        ({'nested': {'deep': 'value'}}, '深层嵌套'),
        ([1, 2, 3] * 10000, '大列表'),
        ({f'key_{i}': f'value_{i}' for i in range(10000)}, '大字典'),
        ('\x00\x01\x02', '控制字符'),
        ('<script>alert(1)</script>', 'XSS尝试'),
        ("'; DROP TABLE users; --", 'SQL注入'),
        ('中文测试', 'Unicode'),
        ('🎉' * 1000, 'Emoji大文本'),
    ]
    
    # 运行5分钟或遍历所有边界情况多次
    start = time.time()
    case_index = 0
    
    while time.time() - phase.start_time < 300:
        try:
            test_input, description = edge_cases[case_index % len(edge_cases)]
            case_index += 1
            
            vm = VersionManager()
            vm.create_version(f'edge_test_{operations}', {
                'input': test_input,
                'type': description
            })
            
            operations += 1
        
        except Exception as e:
            errors += 1
            bug_tracker.record_bug(
                'Edge Case',
                'MEDIUM',
                f'{description} 处理失败: {str(e)}',
                traceback.format_exc()
            )
    
    phase.end_time = time.time()
    phase.operations = operations
    phase.errors = errors
    
    print(f"  完成: {operations} 操作, {errors} 错误, 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def phase6_system_integration():
    """阶段6: 系统集成测试 - 5分钟"""
    print(f"\n{'='*90}")
    print(f"🔗 阶段6: 系统集成测试 (5分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("系统集成测试", 300, phase6_system_integration)
    phase.start_time = time.time()
    
    operations = 0
    errors = 0
    
    # 运行5分钟
    while time.time() - phase.start_time < 300:
        try:
            # 创建完整的系统交互
            orchestrator = OrchestratorService()
            
            # 注册多个Agent
            for i in range(10):
                orchestrator.register_agent({
                    'id': f'int_agent_{i}',
                    'name': f'Integrated Agent {i}',
                    'type': 'integration_test',
                    'capabilities': ['test']
                })
            
            # 创建工作流
            workflow_id = f'workflow_{operations}'
            task = orchestrator.create_task({
                'id': workflow_id,
                'name': f'Task {workflow_id}',
                'priority': 1
            })
            
            # 分配任务
            orchestrator.assign_task_to_agent(task, 'int_agent_0')
            
            # 发布消息
            orchestrator.broadcast_message({
                'type': 'test',
                'data': operations
            })
            
            operations += 1
            
            if operations % 1000 == 0:
                elapsed = time.time() - phase.start_time
                print(f"  [{elapsed:.1f}s] 操作: {operations}, 错误: {errors}")
        
        except Exception as e:
            errors += 1
            bug_tracker.record_bug(
                'System Integration',
                'HIGH',
                f'系统集成错误: {str(e)}',
                traceback.format_exc()
            )
    
    phase.end_time = time.time()
    phase.operations = operations
    phase.errors = errors
    
    print(f"  完成: {operations} 操作, {errors} 错误, 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def phase7_chaos_testing():
    """阶段7: 混沌工程测试 - 5分钟"""
    print(f"\n{'='*90}")
    print(f"🌪️ 阶段7: 混沌工程测试 (5分钟)")
    print(f"{'='*90}")
    
    phase = TestPhase("混沌工程测试", 300, phase7_chaos_testing)
    phase.start_time = time.time()
    
    chaos_tests = 0
    resilience_score = 0
    
    # 运行5分钟
    while time.time() - phase.start_time < 300:
        chaos_tests += 1
        
        try:
            # 随机触发一些"混沌"场景
            scenario = random.choice([
                'rapid_creation',
                'memory_spike',
                'thread_storm',
                'deep_recursion'
            ])
            
            if scenario == 'rapid_creation':
                # 快速创建大量对象
                objects = [VersionManager() for _ in range(100)]
                
            elif scenario == 'memory_spike':
                # 内存峰值
                data = {'x' * 100000 for _ in range(10)}
                
            elif scenario == 'thread_storm':
                # 线程风暴
                def dummy():
                    time.sleep(0.01)
                
                threads = [threading.Thread(target=dummy) for _ in range(100)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                
            elif scenario == 'deep_recursion':
                # 深层递归
                def recurse(depth):
                    if depth > 100:
                        return depth
                    return recurse(depth + 1)
                
                recurse(0)
            
            resilience_score += 1
            
        except Exception as e:
            bug_tracker.record_bug(
                'Chaos Engineering',
                'MEDIUM',
                f'混沌场景 {scenario} 失败: {str(e)}',
                traceback.format_exc()
            )
        
        if chaos_tests % 100 == 0:
            elapsed = time.time() - phase.start_time
            print(f"  [{elapsed:.1f}s] 混沌测试: {chaos_tests}, 韧性得分: {resilience_score}")
    
    phase.end_time = time.time()
    phase.operations = chaos_tests
    
    resilience_pct = (resilience_score / chaos_tests * 100) if chaos_tests > 0 else 0
    print(f"  完成: {chaos_tests} 混沌测试, 韧性得分: {resilience_score} ({resilience_pct:.1f}%), 耗时 {phase.end_time - phase.start_time:.1f}s")
    return phase


def run_all_phases():
    """运行所有测试阶段"""
    print("="*90)
    print("🚀 MAOS 超长时间极限测试套件 v3.0")
    print("="*90)
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"目标运行时间: 60分钟+")
    print("="*90)
    
    phases = [
        phase1_continuous_operation,
        phase2_concurrent_stress,
        phase3_memory_pressure,
        phase4_race_condition_probing,
        phase5_edge_case_probing,
        phase6_system_integration,
        phase7_chaos_testing,
    ]
    
    results = []
    
    for phase_func in phases:
        phase_result = phase_func()
        results.append(phase_result)
    
    print_final_report(results)


def print_final_report(results: List[TestPhase]):
    """打印最终报告"""
    total_duration = time.time() - start_time
    
    print("\n" + "="*90)
    print("📊 MAOS 超长时间极限测试 - 最终报告")
    print("="*90)
    
    print(f"\n⏱️  总运行时间: {total_duration:.2f} 秒 ({total_duration/60:.2f} 分钟)")
    print(f"结束时间: {datetime.now().isoformat()}")
    
    # Bug统计
    summary = bug_tracker.get_summary()
    print(f"\n🐛 Bug 发现统计:")
    print(f"   总计: {summary['total']}")
    print(f"   🔴 CRITICAL: {summary['critical']}")
    print(f"   🟠 HIGH: {summary['high']}")
    print(f"   🟡 MEDIUM: {summary['medium']}")
    print(f"   🔵 LOW: {summary['low']}")
    
    # 阶段结果
    print(f"\n📋 测试阶段结果:")
    total_operations = 0
    total_errors = 0
    
    for i, result in enumerate(results, 1):
        total_operations += result.operations
        total_errors += result.errors
        
        duration = result.end_time - result.start_time if result.end_time > 0 else 0
        
        print(f"\n   阶段{i}: {result.name}")
        print(f"      操作: {result.operations:,}")
        print(f"      错误: {result.errors}")
        print(f"      耗时: {duration:.1f}s ({duration/60:.1f}min)")
    
    print(f"\n   总计: {total_operations:,} 操作, {total_errors} 错误")
    
    # 资源使用
    gc.collect()
    time.sleep(1)
    final_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    
    print(f"\n💾 资源使用:")
    print(f"   最终内存: {final_mem:.2f} MB")
    print(f"   CPU使用: {psutil.Process(os.getpid()).cpu_percent():.1f}%")
    print(f"   线程数: {threading.active_count()}")
    
    # 健康评分
    health_score = 100
    health_score -= summary['critical'] * 20
    health_score -= summary['high'] * 10
    health_score -= summary['medium'] * 5
    health_score -= summary['low'] * 1
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
    
    # 详细Bug列表
    if bug_tracker.bugs:
        print(f"\n📝 详细Bug列表 (前20个):")
        for i, bug in enumerate(bug_tracker.bugs[:20], 1):
            print(f"\n   [{i}] {bug['category']} - {bug['severity']}")
            print(f"       {bug['description']}")
            print(f"       时间: {bug['timestamp']}")
    
    print("\n" + "="*90)
    print("✅ 超长时间极限测试完成")
    print("="*90)


if __name__ == '__main__':
    run_all_phases()
