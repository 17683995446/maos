#!/usr/bin/env python3
"""
MAOS 深度真实实践测试 v3.0
Multi-Agent Orchestration System - 极限真实运行测试
目的：发现系统在长时间运行时的真实 bug 和缺陷

测试策略：
1. 高并发压力测试 - 模拟大量并发操作
2. 边界条件测试 - 测试极限情况
3. 数据一致性测试 - 验证数据完整性
4. 异常恢复测试 - 测试错误处理
5. 资源泄漏测试 - 检测内存和线程泄漏
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
    EventEmitter, OrchestratorEventType, OrchestratorEvent
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


class DeepRealPracticeTest:
    """深度真实实践测试"""
    
    def __init__(self):
        self.bug_tracker = BugTracker()
        self.resource_monitor = ResourceMonitor()
        self.errors_count = 0
        self.operations_count = 0
    
    def test_concurrent_storage_operations(self, num_threads=50, operations_per_thread=100):
        """测试并发存储操作"""
        print(f"\n{'='*60}")
        print(f"测试并发存储操作: {num_threads} 线程, 每线程 {operations_per_thread} 操作")
        print(f"{'='*60}")
        
        storage = InMemoryChatStorage()
        errors = []
        
        def worker(thread_id):
            thread_errors = []
            for i in range(operations_per_thread):
                try:
                    user_id = f'user_{thread_id}'
                    message = {
                        'content': f'message_{i}',
                        'seq': i,
                        'timestamp': time.time()
                    }
                    
                    result = storage.save_message(user_id, message)
                    if not result:
                        thread_errors.append(f"Thread {thread_id}: save_message returned False")
                    
                    messages = storage.get_conversation(user_id)
                    if len(messages) == 0:
                        thread_errors.append(f"Thread {thread_id}: get_conversation returned empty list")
                    
                except Exception as e:
                    thread_errors.append(f"Thread {thread_id}: {type(e).__name__}: {e}")
                    tb = traceback.format_exc()
                    self.bug_tracker.add_bug(
                        category='Storage',
                        severity='HIGH',
                        description=f"并发存储操作错误: {type(e).__name__}: {e}",
                        stack_trace=tb
                    )
            
            return thread_errors
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                errors.extend(future.result())
        
        print(f"总错误数: {len(errors)}")
        if errors:
            for error in errors[:10]:
                print(f"  - {error}")
            print(f"  ... 还有 {len(errors) - 10} 个错误")
        
        return len(errors)
    
    def test_version_manager_edge_cases(self):
        """测试版本管理器边界情况"""
        print(f"\n{'='*60}")
        print(f"测试版本管理器边界情况")
        print(f"{'='*60}")
        
        vm = VersionManager()
        errors = []
        
        test_cases = [
            ('empty_workflow', []),
            ('workflow_with_no_versions', ['v1', 'v2', 'v3']),
            ('workflow_with_special_chars', ['v-1.0.0', 'v_2_0_0']),
            ('workflow_with_unicode', ['版本1', '版本2']),
        ]
        
        for workflow_name, versions in test_cases:
            try:
                created_version_ids = []
                for version in versions:
                    workflow_version = vm.create_version(workflow_name, {'version': version})
                    created_version_ids.append(workflow_version.id)
                
                retrieved_versions = vm.list_versions(workflow_name)
                if len(retrieved_versions) != len(versions):
                    errors.append(f"{workflow_name}: 期望 {len(versions)} 个版本, 实际 {len(retrieved_versions)}")
                
                for version_id in created_version_ids:
                    vm.get_version(version_id)
                
                print(f"  ✓ {workflow_name}: {len(versions)} 个版本")
                
            except Exception as e:
                errors.append(f"{workflow_name}: {type(e).__name__}: {e}")
                tb = traceback.format_exc()
                self.bug_tracker.add_bug(
                    category='VersionManager',
                    severity='HIGH',
                    description=f"版本管理器错误: {type(e).__name__}: {e}",
                    stack_trace=tb
                )
        
        print(f"总错误数: {len(errors)}")
        return len(errors)
    
    def test_analytics_engine_data_integrity(self, num_metrics=1000):
        """测试分析引擎数据完整性"""
        print(f"\n{'='*60}")
        print(f"测试分析引擎数据完整性: {num_metrics} 个指标")
        print(f"{'='*60}")
        
        ae = AnalyticsEngine()
        errors = []
        
        metric_names = [
            'cpu_usage', 'memory_usage', 'request_count', 'error_rate',
            'response_time', 'throughput', 'active_users', 'session_duration'
        ]
        
        for i in range(num_metrics):
            try:
                metric_name = random.choice(metric_names)
                value = random.uniform(0, 100)
                ae.record_metric(metric_name, value, None, {'iteration': i})
                
                if i % 100 == 0:
                    summary = ae.get_summary()
                    if summary['total_metrics'] != i + 1:
                        errors.append(f"Iteration {i}: 期望 {i+1} 个指标, 实际 {summary['total_metrics']}")
            
            except Exception as e:
                errors.append(f"Iteration {i}: {type(e).__name__}: {e}")
                tb = traceback.format_exc()
                self.bug_tracker.add_bug(
                    category='Analytics',
                    severity='MEDIUM',
                    description=f"分析引擎错误: {type(e).__name__}: {e}",
                    stack_trace=tb
                )
        
        summary = ae.get_summary()
        print(f"记录了 {summary['total_metrics']} 个指标")
        print(f"总错误数: {len(errors)}")
        
        if errors:
            for error in errors[:10]:
                print(f"  - {error}")
        
        return len(errors)
    
    def test_message_broker_reliability(self, num_messages=1000):
        """测试消息代理可靠性"""
        print(f"\n{'='*60}")
        print(f"测试消息代理可靠性: {num_messages} 条消息")
        print(f"{'='*60}")
        
        broker = MessageBroker(max_messages=2000)
        errors = []
        
        topics = ['topic_a', 'topic_b', 'topic_c']
        
        def message_handler(msg):
            pass
        
        for topic in topics:
            broker.subscribe(topic, message_handler)
        
        for i in range(num_messages):
            try:
                msg_type = random.choice(topics)
                message = {
                    'id': i,
                    'type': msg_type,
                    'data': f'message_{i}',
                    'timestamp': time.time()
                }
                
                broker.publish(message)
                
                received = broker.receive(msg_type, timeout=0.1)
                
            except Exception as e:
                errors.append(f"Message {i}: {type(e).__name__}: {e}")
                tb = traceback.format_exc()
                self.bug_tracker.add_bug(
                    category='MessageBroker',
                    severity='MEDIUM',
                    description=f"消息代理错误: {type(e).__name__}: {e}",
                    stack_trace=tb
                )
        
        print(f"总错误数: {len(errors)}")
        if errors:
            for error in errors[:10]:
                print(f"  - {error}")
        
        return len(errors)
    
    def test_mobile_api_session_management(self, num_sessions=100):
        """测试移动 API 会话管理"""
        print(f"\n{'='*60}")
        print(f"测试移动 API 会话管理: {num_sessions} 个会话")
        print(f"{'='*60}")
        
        mobile_manager = MobileAPIManager()
        errors = []
        
        for i in range(num_sessions):
            try:
                user_id = f'user_{i}'
                
                session = mobile_manager.create_session(
                    user_id=user_id,
                    device_id=f'device_{i}'
                )
                
                session_id = session.token
                
                retrieved_session = mobile_manager.validate_session(session_id)
                if not retrieved_session:
                    errors.append(f"Session {session_id}: 无法验证会话")
            
            except Exception as e:
                errors.append(f"Session {i}: {type(e).__name__}: {e}")
                tb = traceback.format_exc()
                self.bug_tracker.add_bug(
                    category='MobileAPI',
                    severity='MEDIUM',
                    description=f"移动 API 错误: {type(e).__name__}: {e}",
                    stack_trace=tb
                )
        
        print(f"总错误数: {len(errors)}")
        if errors:
            for error in errors[:10]:
                print(f"  - {error}")
        
        return len(errors)
    
    def test_security_token_operations(self, num_tokens=100):
        """测试安全令牌操作"""
        print(f"\n{'='*60}")
        print(f"测试安全令牌操作: {num_tokens} 个令牌")
        print(f"{'='*60}")
        
        oauth_server = OAuth2Server(jwt_secret='test_secret_key')
        jwt_token = oauth_server.jwt_token
        errors = []
        created_tokens = []
        
        for i in range(num_tokens):
            try:
                user_id = f'user_{i}'
                
                claims = JWTClaims(
                    sub=user_id,
                    roles=['user'],
                    permissions=['read', 'write']
                )
                token_string = jwt_token.create_token(claims)
                created_tokens.append((user_id, token_string))
                
                verified_claims = jwt_token.verify_token(token_string)
                if not verified_claims:
                    errors.append(f"Token {i}: 验证失败")
                
                if verified_claims and verified_claims.sub != user_id:
                    errors.append(f"Token {i}: 用户 ID 不匹配")
            
            except Exception as e:
                errors.append(f"Token {i}: {type(e).__name__}: {e}")
                tb = traceback.format_exc()
                self.bug_tracker.add_bug(
                    category='Security',
                    severity='HIGH',
                    description=f"安全令牌错误: {type(e).__name__}: {e}",
                    stack_trace=tb
                )
        
        print(f"总错误数: {len(errors)}")
        if errors:
            for error in errors[:10]:
                print(f"  - {error}")
        
        return len(errors)
    
    def test_resource_leak_detection(self):
        """测试资源泄漏检测"""
        print(f"\n{'='*60}")
        print(f"测试资源泄漏检测")
        print(f"{'='*60}")
        
        initial_memory = self.resource_monitor.process.memory_info().rss / 1024 / 1024
        
        storages = []
        for i in range(100):
            storage = InMemoryChatStorage()
            for j in range(100):
                storage.save_message(f'user_{j}', {'content': f'msg_{j}'})
            storages.append(storage)
        
        gc.collect()
        final_memory = self.resource_monitor.process.memory_info().rss / 1024 / 1024
        
        memory_growth = final_memory - initial_memory
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_growth:.2f} MB")
        
        del storages
        gc.collect()
        
        after_cleanup_memory = self.resource_monitor.process.memory_info().rss / 1024 / 1024
        memory_released = final_memory - after_cleanup_memory
        print(f"清理后内存: {after_cleanup_memory:.2f} MB")
        print(f"释放内存: {memory_released:.2f} MB")
        
        if memory_growth > 50:
            self.bug_tracker.add_bug(
                category='Memory',
                severity='HIGH',
                description=f"检测到内存泄漏: 增长 {memory_growth:.2f} MB"
            )
            print(f"⚠️ 警告: 检测到可能的内存泄漏")
        
        return 0
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("MAOS 深度真实实践测试 v3.0")
        print("="*80)
        
        start_time = time.time()
        
        test_results = {
            'concurrent_storage': self.test_concurrent_storage_operations(),
            'version_manager': self.test_version_manager_edge_cases(),
            'analytics_engine': self.test_analytics_engine_data_integrity(),
            'message_broker': self.test_message_broker_reliability(),
            'mobile_api': self.test_mobile_api_session_management(),
            'security': self.test_security_token_operations(),
            'resource_leak': self.test_resource_leak_detection()
        }
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("测试结果汇总")
        print("="*80)
        
        total_errors = 0
        for test_name, errors in test_results.items():
            status = "✓ 通过" if errors == 0 else f"✗ {errors} 个错误"
            print(f"  {test_name:25s}: {status}")
            total_errors += errors
        
        print(f"\n总错误数: {total_errors}")
        print(f"总运行时间: {elapsed_time:.2f} 秒")
        
        resource_stats = self.resource_monitor.get_stats()
        print(f"\n资源使用情况:")
        print(f"  内存增长: {resource_stats['memory_growth_mb']:.2f} MB ({resource_stats['memory_growth_percent']:.2f}%)")
        print(f"  峰值内存: {resource_stats['peak_memory_mb']:.2f} MB")
        print(f"  平均 CPU: {resource_stats['avg_cpu_percent']:.2f}%")
        
        bug_summary = self.bug_tracker.summary()
        print(f"\nBug 统计:")
        print(f"  总数: {bug_summary['total']}")
        print(f"  严重: {bug_summary['critical']}")
        print(f"  高: {bug_summary['high']}")
        print(f"  中: {bug_summary['medium']}")
        print(f"  低: {bug_summary['low']}")
        
        if bug_summary['total'] > 0:
            print(f"\n🐛 Bug 详情:")
            for bug in self.bug_tracker.bugs[:10]:
                print(f"  [{bug['severity']}] {bug['description']}")
        
        print("\n" + "="*80)
        print("测试完成!")
        print("="*80)
        
        return total_errors


if __name__ == '__main__':
    tester = DeepRealPracticeTest()
    total_errors = tester.run_all_tests()
    sys.exit(0 if total_errors == 0 else 1)
