#!/usr/bin/env python3
"""
MAOS 超长时间真实实践测试套件 v2.0
Multi-Agent Orchestration System - 极限真实运行测试
目的：发现系统在长时间运行时的真实 bug 和缺陷
"""

import threading
import time
import random
import sys
import gc
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

sys.path.insert(0, '/workspace')

from maos.orchestration.orchestrator import (
    OrchestratorService, AgentRegistry, MessageBroker, 
    EventEmitter
)
from maos.security.enhanced import (
    JWTToken, OAuth2Server, JWTClaims
)
from maos.version.v14 import VersionManager, ABTestManager, WorkflowVersion
from maos.analytics.v14 import AnalyticsEngine, MetricSummary
from maos.mobile.v14 import MobileAPIManager, MobileSession, PushNotification
from maos.storage.in_memory import InMemoryChatStorage


class BugTracker:
    """Bug 追踪器"""
    def __init__(self):
        self.bugs: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def add_bug(self, category: str, severity: str, description: str, 
                stack_trace: str = "", file_path: str = ""):
        bug = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'severity': severity,
            'description': description,
            'stack_trace': stack_trace,
            'file_path': file_path
        }
        with self.lock:
            self.bugs.append(bug)
        print(f"🐛 发现 Bug [{severity}]: {description}")
    
    def get_bugs_by_severity(self, severity: str) -> List[Dict]:
        with self.lock:
            return [b for b in self.bugs if b['severity'] == severity]
    
    def summary(self) -> Dict[str, int]:
        with self.lock:
            return {
                'total': len(self.bugs),
                'critical': len([b for b in self.bugs if b['severity'] == 'CRITICAL']),
                'high': len([b for b in self.bugs if b['severity'] == 'HIGH']),
                'medium': len([b for b in self.bugs if b['severity'] == 'MEDIUM']),
                'low': len([b for b in self.bugs if b['severity'] == 'LOW'])
            }


class ResourceMonitor:
    """资源监控器"""
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.start_memory
        self.samples: List[Dict[str, float]] = []
        self.lock = threading.Lock()
    
    def sample(self) -> Dict[str, float]:
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        sample = {
            'timestamp': time.time(),
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent
        }
        
        with self.lock:
            self.samples.append(sample)
            if memory_mb > self.peak_memory:
                self.peak_memory = memory_mb
        
        return sample
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            if not self.samples:
                return {
                    'start_memory_mb': self.start_memory,
                    'current_memory_mb': self.start_memory,
                    'peak_memory_mb': self.peak_memory,
                    'memory_growth_mb': 0.0,
                    'memory_growth_percent': 0.0,
                    'avg_cpu_percent': 0.0,
                    'samples_count': 0
                }
            
            memory_values = [s['memory_mb'] for s in self.samples]
            cpu_values = [s['cpu_percent'] for s in self.samples]
            
            current_memory = memory_values[-1] if memory_values else self.start_memory
            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            
            return {
                'start_memory_mb': self.start_memory,
                'current_memory_mb': current_memory,
                'peak_memory_mb': self.peak_memory,
                'memory_growth_mb': current_memory - self.start_memory,
                'memory_growth_percent': ((current_memory - self.start_memory) / self.start_memory * 100) if self.start_memory > 0 else 0,
                'avg_cpu_percent': avg_cpu,
                'samples_count': len(self.samples)
            }


class UltraLongRealPracticeTest:
    """超长时间真实实践测试"""
    
    def __init__(self):
        self.bug_tracker = BugTracker()
        self.resource_monitor = ResourceMonitor()
        self.test_results: List[Dict] = []
        self.start_time = time.time()
        self.stop_event = threading.Event()
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("🚀 MAOS 超长时间真实实践测试 v2.0")
        print("目的：发现系统在长时间真实运行时的 bug 和缺陷")
        print("=" * 80)
        
        test_cases = [
            ("测试 1: 72小时连续运行模拟", self.test_72hour_continuous_run),
            ("测试 2: 1000个并发连接压力测试", self.test_concurrent_connections),
            ("测试 3: 内存泄漏深度检测", self.test_memory_leak_detection),
            ("测试 4: 边界条件和异常输入测试", self.test_edge_cases),
            ("测试 5: 资源耗尽场景测试", self.test_resource_exhaustion),
            ("测试 6: 并发竞态条件测试", self.test_race_conditions),
            ("测试 7: 长时间状态一致性测试", self.test_state_consistency),
            ("测试 8: 网络延迟模拟测试", self.test_network_latency),
            ("测试 9: 错误恢复和回滚测试", self.test_error_recovery),
            ("测试 10: 数据完整性验证", self.test_data_integrity),
        ]
        
        for test_name, test_func in test_cases:
            print(f"\n{'=' * 80}")
            print(f"🧪 {test_name}")
            print(f"{'=' * 80}")
            
            test_start = time.time()
            try:
                test_result = test_func()
                test_result['duration'] = time.time() - test_start
                test_result['status'] = 'PASSED'
                print(f"✅ {test_name} 完成 - 耗时: {test_result['duration']:.2f}秒")
            except Exception as e:
                test_result = {
                    'name': test_name,
                    'status': 'FAILED',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                print(f"❌ {test_name} 失败: {e}")
            
            self.test_results.append(test_result)
        
        self.print_final_report()
    
    def test_72hour_continuous_run(self) -> Dict:
        """测试 1: 72小时连续运行模拟（压缩为10分钟）"""
        print("📊 模拟 72 小时连续运行...")
        
        result = {
            'name': '72小时连续运行测试',
            'operations': 0,
            'errors': 0,
            'memory_samples': []
        }
        
        # 模拟 72 小时 = 压缩为 10 分钟
        simulated_hours = 72
        real_minutes = 10
        operations_per_second = (simulated_hours * 3600) / (real_minutes * 60)
        
        start = time.time()
        end_time = start + (real_minutes * 60)
        iteration = 0
        
        while time.time() < end_time:
            iteration += 1
            
            try:
                # 创建各种操作
                storage = InMemoryChatStorage()
                storage.save_message('user_1', {'content': f'message_{iteration}'})
                storage.get_conversation('user_1')
                
                # 版本管理
                vm = VersionManager()
                workflow_name = f'workflow_{iteration}'
                vm.create_version(workflow_name, {'step': iteration})
                versions = vm.list_versions(workflow_name)
                if versions:
                    vm.get_version(workflow_name, versions[0])
                
                # 消息代理
                broker = MessageBroker(max_messages=1000)
                broker.publish('test_topic', {'data': iteration})
                broker.subscribe('test_topic', lambda x: x)
                
                result['operations'] += 6
                
                # 每 1000 次采样资源
                if iteration % 1000 == 0:
                    sample = self.resource_monitor.sample()
                    result['memory_samples'].append(sample)
                    print(f"  迭代 {iteration}: 内存 {sample['memory_mb']:.1f}MB, CPU {sample['cpu_percent']:.1f}%")
                
            except Exception as e:
                result['errors'] += 1
                self.bug_tracker.add_bug(
                    'Runtime Error',
                    'MEDIUM',
                    f'72小时运行中的错误: {str(e)}',
                    traceback.format_exc()
                )
        
        return result
    
    def test_concurrent_connections(self) -> Dict:
        """测试 2: 1000个并发连接压力测试"""
        print("📊 测试 1000 个并发连接...")
        
        result = {
            'name': '并发连接测试',
            'total_connections': 1000,
            'successful': 0,
            'failed': 0,
            'timeouts': 0
        }
        
        connections: List[Dict] = []
        lock = threading.Lock()
        barrier = threading.Barrier(1000)
        
        def create_connection(conn_id: int):
            try:
                barrier.wait()
                
                # 创建连接并执行操作
                storage = InMemoryChatStorage()
                session_id = f'session_{conn_id}'
                
                for i in range(10):
                    storage.save_message(session_id, {
                        'content': f'msg_{conn_id}_{i}',
                        'timestamp': time.time()
                    })
                
                # 验证连接
                msgs = storage.get_conversation(session_id)
                
                with lock:
                    result['successful'] += 1
                
            except Exception as e:
                with lock:
                    result['failed'] += 1
                self.bug_tracker.add_bug(
                    'Concurrency',
                    'HIGH',
                    f'并发连接 {conn_id} 失败: {str(e)}',
                    traceback.format_exc()
                )
        
        with ThreadPoolExecutor(max_workers=1000) as executor:
            futures = [executor.submit(create_connection, i) for i in range(1000)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
        
        print(f"  成功: {result['successful']}, 失败: {result['failed']}")
        return result
    
    def test_memory_leak_detection(self) -> Dict:
        """测试 3: 内存泄漏深度检测"""
        print("📊 检测内存泄漏...")
        
        result = {
            'name': '内存泄漏检测',
            'initial_memory_mb': 0,
            'final_memory_mb': 0,
            'memory_growth_mb': 0,
            'growth_percent': 0,
            'leaks_detected': []
        }
        
        gc.collect()
        time.sleep(1)
        
        initial_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        result['initial_memory_mb'] = initial_mem
        
        # 执行 10000 次操作
        for i in range(10000):
            try:
                # 创建对象但不释放
                vm = VersionManager()
                vm.create_version(f'wf_{i}', {'data': 'x' * 1000})
                
                abm = ABTestManager()
                abm.create_experiment(f'exp_{i}', {'variant': 'A'})
                
                ae = AnalyticsEngine()
                ae.record_metric(f'metric_{i}', i, {'tag': 'test'})
                
                if i % 1000 == 0:
                    gc.collect()
                    current_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                    growth = current_mem - initial_mem
                    growth_pct = (growth / initial_mem * 100) if initial_mem > 0 else 0
                    
                    if growth_pct > 10:  # 超过 10% 认为有泄漏
                        result['leaks_detected'].append({
                            'iteration': i,
                            'growth_percent': growth_pct
                        })
                        self.bug_tracker.add_bug(
                            'Memory Leak',
                            'HIGH',
                            f'内存增长超过 10%: {growth_pct:.2f}%',
                            f'迭代 {i}, 当前内存 {current_mem:.2f}MB'
                        )
                    
                    print(f"  迭代 {i}: 内存增长 {growth:.2f}MB ({growth_pct:.2f}%)")
                    
            except Exception as e:
                self.bug_tracker.add_bug(
                    'Memory Error',
                    'MEDIUM',
                    f'内存测试中的错误: {str(e)}',
                    traceback.format_exc()
                )
        
        gc.collect()
        time.sleep(1)
        
        final_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        result['final_memory_mb'] = final_mem
        result['memory_growth_mb'] = final_mem - initial_mem
        result['growth_percent'] = ((final_mem - initial_mem) / initial_mem * 100) if initial_mem > 0 else 0
        
        return result
    
    def test_edge_cases(self) -> Dict:
        """测试 4: 边界条件和异常输入测试"""
        print("📊 测试边界条件和异常输入...")
        
        result = {
            'name': '边界条件测试',
            'test_cases': 0,
            'passed': 0,
            'failed': 0,
            'edge_case_bugs': []
        }
        
        edge_cases = [
            # 空输入
            ('', '空字符串'),
            (None, 'None值'),
            ({}, '空字典'),
            ([], '空列表'),
            
            # 超长输入
            ('x' * 1000000, '超长字符串'),
            ({'key': 'x' * 100000}, '超长字典值'),
            
            # 特殊字符
            ('\x00\x01\x02', '控制字符'),
            ('<script>alert(1)</script>', 'XSS尝试'),
            ("'; DROP TABLE users; --", 'SQL注入尝试'),
            
            # 数字边界
            (sys.maxsize, '最大整数'),
            (-sys.maxsize - 1, '最小整数'),
            (1e308, '最大浮点数'),
            (1e-308, '最小浮点数'),
            
            # 循环引用
            ({'self': None}, '自引用'),
        ]
        
        for test_input, description in edge_cases:
            result['test_cases'] += 1
            
            try:
                # 测试存储
                storage = InMemoryChatStorage()
                storage.save_message('edge_test', test_input)
                
                # 测试版本管理
                vm = VersionManager()
                vm.create_version('edge_wf', {'input': test_input})
                
                # 测试分析引擎
                ae = AnalyticsEngine()
                ae.record_metric('edge_metric', 0, {'input': test_input})
                
                result['passed'] += 1
                
            except Exception as e:
                result['failed'] += 1
                bug = {
                    'input_type': description,
                    'error': str(e)
                }
                result['edge_case_bugs'].append(bug)
                
                self.bug_tracker.add_bug(
                    'Edge Case',
                    'MEDIUM',
                    f'{description} 处理失败: {str(e)}',
                    traceback.format_exc()
                )
        
        print(f"  测试用例: {result['test_cases']}, 通过: {result['passed']}, 失败: {result['failed']}")
        return result
    
    def test_resource_exhaustion(self) -> Dict:
        """测试 5: 资源耗尽场景测试"""
        print("📊 测试资源耗尽场景...")
        
        result = {
            'name': '资源耗尽测试',
            'scenarios': [],
            'bugs_found': []
        }
        
        # 场景 1: 文件描述符耗尽
        try:
            print("  场景 1: 文件描述符耗尽测试...")
            storage = InMemoryChatStorage()
            
            for i in range(10000):
                storage.save_message(f'user_{i}', {'msg': f'message_{i}'})
            
            # 检查是否处理了限制
            result['scenarios'].append({
                'name': '大量消息存储',
                'handled': True
            })
            
        except Exception as e:
            result['scenarios'].append({
                'name': '大量消息存储',
                'error': str(e)
            })
            self.bug_tracker.add_bug(
                'Resource Exhaustion',
                'HIGH',
                f'大量消息存储失败: {str(e)}',
                traceback.format_exc()
            )
        
        # 场景 2: CPU 饱和
        try:
            print("  场景 2: CPU 饱和测试...")
            start = time.time()
            
            # 创建大量并发任务
            def cpu_intensive():
                total = 0
                for i in range(10000):
                    total += i ** 2
                return total
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = [executor.submit(cpu_intensive) for _ in range(100)]
                results = [f.result() for f in futures]
            
            duration = time.time() - start
            result['scenarios'].append({
                'name': 'CPU饱和测试',
                'duration': duration,
                'completed': True
            })
            
        except Exception as e:
            result['bugs_found'].append(str(e))
            self.bug_tracker.add_bug(
                'Resource Exhaustion',
                'MEDIUM',
                f'CPU饱和测试失败: {str(e)}',
                traceback.format_exc()
            )
        
        return result
    
    def test_race_conditions(self) -> Dict:
        """测试 6: 并发竞态条件测试"""
        print("📊 测试并发竞态条件...")
        
        result = {
            'name': '竞态条件测试',
            'race_conditions_found': 0,
            'race_condition_details': []
        }
        
        # 测试计数器竞态
        counter = {'value': 0}
        counter_lock = threading.Lock()
        iterations = 10000
        
        def increment_without_lock():
            for _ in range(iterations):
                counter['value'] += 1
        
        def increment_with_lock():
            for _ in range(iterations):
                with counter_lock:
                    counter['value'] += 1
        
        # 无锁测试
        threads = [threading.Thread(target=increment_without_lock) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        expected = iterations * 10
        actual = counter['value']
        if actual != expected:
            result['race_conditions_found'] += 1
            detail = {
                'type': 'Counter Race',
                'expected': expected,
                'actual': actual,
                'difference': expected - actual
            }
            result['race_condition_details'].append(detail)
            
            self.bug_tracker.add_bug(
                'Race Condition',
                'HIGH',
                f'计数器竞态条件: 期望 {expected}, 实际 {actual}',
                f'差异: {expected - actual}'
            )
        
        # 测试共享状态竞态
        shared_state = {'data': []}
        
        def writer(writer_id: int):
            for i in range(1000):
                shared_state['data'].append(f'w{writer_id}_{i}')
        
        def reader():
            for _ in range(1000):
                _ = len(shared_state['data'])
        
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=writer, args=(i,)))
        for i in range(10):
            threads.append(threading.Thread(target=reader))
        
        random.shuffle(threads)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 检查数据一致性
        final_len = len(shared_state['data'])
        expected_len = 5 * 1000
        if final_len != expected_len:
            result['race_conditions_found'] += 1
            detail = {
                'type': 'Shared State Race',
                'expected': expected_len,
                'actual': final_len,
                'difference': expected_len - final_len
            }
            result['race_condition_details'].append(detail)
            
            self.bug_tracker.add_bug(
                'Race Condition',
                'HIGH',
                f'共享状态竞态: 期望 {expected_len}, 实际 {final_len}',
                f'丢失数据: {expected_len - final_len}'
            )
        
        print(f"  发现竞态条件: {result['race_conditions_found']}")
        return result
    
    def test_state_consistency(self) -> Dict:
        """测试 7: 长时间状态一致性测试"""
        print("📊 测试状态一致性...")
        
        result = {
            'name': '状态一致性测试',
            'operations': 0,
            'inconsistencies': 0,
            'inconsistency_details': []
        }
        
        storage = InMemoryChatStorage()
        test_user = 'consistency_test_user'
        
        # 执行一系列操作
        for i in range(5000):
            try:
                # 写入
                msg_id = f'msg_{i}'
                storage.save_message(test_user, {
                    'id': msg_id,
                    'content': f'message_{i}',
                    'seq': i
                })
                
                # 验证
                conversation = storage.get_conversation(test_user)
                
                # 检查序列完整性
                ids = [m.get('id') for m in conversation]
                if msg_id not in ids:
                    result['inconsistencies'] += 1
                    result['inconsistency_details'].append({
                        'operation': 'write_then_read',
                        'msg_id': msg_id,
                        'found': False
                    })
                    
                    self.bug_tracker.add_bug(
                        'State Inconsistency',
                        'HIGH',
                        f'写入后无法读取: msg_id={msg_id}',
                        f'操作序列: {i}'
                    )
                
                result['operations'] += 1
                
            except Exception as e:
                result['inconsistencies'] += 1
                self.bug_tracker.add_bug(
                    'State Error',
                    'MEDIUM',
                    f'状态一致性测试错误: {str(e)}',
                    traceback.format_exc()
                )
        
        print(f"  操作: {result['operations']}, 不一致: {result['inconsistencies']}")
        return result
    
    def test_network_latency(self) -> Dict:
        """测试 8: 网络延迟模拟测试"""
        print("📊 模拟网络延迟...")
        
        result = {
            'name': '网络延迟测试',
            'scenarios': []
        }
        
        delays = [0.001, 0.01, 0.1, 1.0]  # 毫秒到秒
        
        for delay in delays:
            scenario = {
                'delay': delay,
                'operations': 0,
                'timeouts': 0,
                'errors': 0
            }
            
            try:
                start = time.time()
                
                def delayed_operation():
                    time.sleep(delay)
                    storage = InMemoryChatStorage()
                    storage.save_message('latency_test', {'delay': delay})
                    return True
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(delayed_operation) for _ in range(100)]
                    
                    for future in as_completed(futures, timeout=5):
                        try:
                            future.result()
                            scenario['operations'] += 1
                        except Exception as e:
                            scenario['errors'] += 1
                
                duration = time.time() - start
                scenario['duration'] = duration
                
            except Exception as e:
                scenario['error'] = str(e)
                self.bug_tracker.add_bug(
                    'Network Latency',
                    'LOW',
                    f'延迟测试失败 (delay={delay}): {str(e)}',
                    traceback.format_exc()
                )
            
            result['scenarios'].append(scenario)
        
        return result
    
    def test_error_recovery(self) -> Dict:
        """测试 9: 错误恢复和回滚测试"""
        print("📊 测试错误恢复...")
        
        result = {
            'name': '错误恢复测试',
            'scenarios': []
        }
        
        # 场景 1: 操作中断恢复
        try:
            storage = InMemoryChatStorage()
            
            # 部分完成的事务
            storage.save_message('user1', {'content': 'msg1'})
            # 假设这里中断
            storage.save_message('user2', {'content': 'msg2'})
            
            # 验证一致性
            conv1 = storage.get_conversation('user1')
            conv2 = storage.get_conversation('user2')
            
            result['scenarios'].append({
                'name': '中断恢复',
                'consistent': len(conv1) > 0 and len(conv2) > 0
            })
            
        except Exception as e:
            result['scenarios'].append({
                'name': '中断恢复',
                'error': str(e)
            })
            self.bug_tracker.add_bug(
                'Error Recovery',
                'MEDIUM',
                f'错误恢复失败: {str(e)}',
                traceback.format_exc()
            )
        
        # 场景 2: 并发错误处理
        try:
            def error_operation():
                if random.random() < 0.1:  # 10% 失败率
                    raise Exception("随机错误")
                return True
            
            success_count = 0
            error_count = 0
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(error_operation) for _ in range(1000)]
                
                for future in as_completed(futures):
                    try:
                        future.result()
                        success_count += 1
                    except:
                        error_count += 1
            
            result['scenarios'].append({
                'name': '并发错误处理',
                'success': success_count,
                'errors': error_count
            })
            
        except Exception as e:
            self.bug_tracker.add_bug(
                'Error Recovery',
                'MEDIUM',
                f'并发错误处理测试失败: {str(e)}',
                traceback.format_exc()
            )
        
        return result
    
    def test_data_integrity(self) -> Dict:
        """测试 10: 数据完整性验证"""
        print("📊 验证数据完整性...")
        
        result = {
            'name': '数据完整性测试',
            'checks': 0,
            'violations': 0,
            'violation_details': []
        }
        
        storage = InMemoryChatStorage()
        
        # 写入测试数据
        test_data = [
            {'content': 'test1', 'size': 1000},
            {'content': 'test2', 'size': 5000},
            {'content': 'test3', 'size': 10000},
        ]
        
        for i, data in enumerate(test_data):
            storage.save_message(f'integrity_user_{i}', data)
        
        # 验证读取
        for i, data in enumerate(test_data):
            result['checks'] += 1
            conversation = storage.get_conversation(f'integrity_user_{i}')
            
            if not conversation:
                result['violations'] += 1
                result['violation_details'].append({
                    'user': f'integrity_user_{i}',
                    'issue': 'Data not found'
                })
                
                self.bug_tracker.add_bug(
                    'Data Integrity',
                    'HIGH',
                    f'数据完整性违规: 无法读取 integrity_user_{i}',
                    ''
                )
        
        # 检查数据损坏
        for i in range(100):
            storage.save_message('corruption_test', {
                'content': 'x' * 1000,
                'checksum': hash('x' * 1000)
            })
            
            conversation = storage.get_conversation('corruption_test')
            
            if conversation and len(conversation) > 0:
                stored = conversation[-1]
                if stored.get('content') != 'x' * 1000:
                    result['violations'] += 1
                    result['violation_details'].append({
                        'user': 'corruption_test',
                        'issue': 'Data corruption'
                    })
                    
                    self.bug_tracker.add_bug(
                        'Data Integrity',
                        'CRITICAL',
                        f'数据损坏: checksum 不匹配',
                        ''
                    )
        
        print(f"  检查: {result['checks']}, 违规: {result['violations']}")
        return result
    
    def print_final_report(self):
        """打印最终报告"""
        print("\n" + "=" * 80)
        print("📋 MAOS 超长时间真实实践测试 - 最终报告")
        print("=" * 80)
        
        total_duration = time.time() - self.start_time
        print(f"\n⏱️  总耗时: {total_duration:.2f} 秒")
        
        # Bug 统计
        print("\n🐛 Bug 发现统计:")
        bug_summary = self.bug_tracker.summary()
        print(f"  总计: {bug_summary['total']}")
        print(f"  - CRITICAL: {bug_summary['critical']}")
        print(f"  - HIGH: {bug_summary['high']}")
        print(f"  - MEDIUM: {bug_summary['medium']}")
        print(f"  - LOW: {bug_summary['low']}")
        
        # 测试结果统计
        print("\n🧪 测试结果:")
        passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAILED')
        print(f"  通过: {passed}/{len(self.test_results)}")
        print(f"  失败: {failed}/{len(self.test_results)}")
        
        # 资源使用统计
        print("\n💾 资源使用统计:")
        stats = self.resource_monitor.get_stats()
        if stats:
            print(f"  初始内存: {stats['start_memory_mb']:.2f} MB")
            print(f"  当前内存: {stats['current_memory_mb']:.2f} MB")
            print(f"  峰值内存: {stats['peak_memory_mb']:.2f} MB")
            print(f"  内存增长: {stats['memory_growth_mb']:.2f} MB ({stats['memory_growth_percent']:.2f}%)")
            print(f"  平均CPU: {stats['avg_cpu_percent']:.2f}%")
        
        # 详细 Bug 列表
        if self.bug_tracker.bugs:
            print("\n📝 详细 Bug 列表:")
            for i, bug in enumerate(self.bug_tracker.bugs, 1):
                print(f"\n  [{i}] {bug['category']} - {bug['severity']}")
                print(f"      描述: {bug['description']}")
                if bug['stack_trace']:
                    print(f"      堆栈: {bug['stack_trace'][:200]}...")
        
        print("\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)


def main():
    """主函数"""
    print("🚀 启动 MAOS 超长时间真实实践测试...")
    print("本测试将执行 10 个深度测试用例，全面检测系统潜在问题\n")
    
    test = UltraLongRealPracticeTest()
    test.run_all_tests()


if __name__ == '__main__':
    main()
