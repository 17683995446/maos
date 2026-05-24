#!/usr/bin/env python3
"""
MAOS 超长时间真实实践测试套件 v3.0
修复版 - 使用正确的 API
"""

import threading
import time
import random
import sys
import gc
import traceback
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

sys.path.insert(0, '/workspace')

from maos.orchestration.orchestrator import (
    OrchestratorService, AgentRegistry, MessageBroker, EventEmitter
)
from maos.security.enhanced import JWTToken, OAuth2Server, JWTClaims
from maos.version.v14 import VersionManager, ABTestManager
from maos.analytics.v14 import AnalyticsEngine
from maos.storage.in_memory import InMemoryChatStorage


class BugTracker:
    def __init__(self):
        self.bugs: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def add_bug(self, category: str, severity: str, description: str, 
                stack_trace: str = ""):
        bug = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'severity': severity,
            'description': description,
            'stack_trace': stack_trace
        }
        with self.lock:
            self.bugs.append(bug)
        print(f"🐛 发现 Bug [{severity}]: {description}")


class UltraLongRealPracticeTest:
    """超长时间真实实践测试 - 修复版"""
    
    def __init__(self):
        self.bug_tracker = BugTracker()
        self.test_results: List[Dict] = []
        self.start_time = time.time()
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("🚀 MAOS 超长时间真实实践测试 v3.0 (修复版)")
        print("目的：发现系统在长时间真实运行时的 bug 和缺陷")
        print("=" * 80)
        
        test_cases = [
            ("测试 1: 连续运行测试", self.test_continuous_run),
            ("测试 2: 并发压力测试", self.test_concurrent_stress),
            ("测试 3: 内存泄漏检测", self.test_memory_leak),
            ("测试 4: 边界条件测试", self.test_edge_cases),
            ("测试 5: 竞态条件测试", self.test_race_conditions),
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
                self.bug_tracker.add_bug(
                    'Test Failure',
                    'HIGH',
                    f'{test_name} 失败: {str(e)}',
                    traceback.format_exc()
                )
            
            self.test_results.append(test_result)
        
        self.print_final_report()
    
    def test_continuous_run(self) -> Dict:
        """测试 1: 连续运行测试"""
        print("📊 测试连续运行...")
        
        result = {
            'name': '连续运行测试',
            'operations': 0,
            'errors': 0
        }
        
        # 测试 5 分钟
        end_time = time.time() + 300
        
        while time.time() < end_time:
            try:
                storage = InMemoryChatStorage()
                version_mgr = VersionManager()
                analytics = AnalyticsEngine()
                broker = MessageBroker()
                
                result['operations'] += 4
                
            except Exception as e:
                result['errors'] += 1
                self.bug_tracker.add_bug(
                    'Runtime Error',
                    'MEDIUM',
                    f'连续运行错误: {str(e)}',
                    traceback.format_exc()
                )
        
        return result
    
    def test_concurrent_stress(self) -> Dict:
        """测试 2: 并发压力测试"""
        print("📊 测试并发压力...")
        
        result = {
            'name': '并发压力测试',
            'successful': 0,
            'failed': 0
        }
        
        def worker(worker_id: int):
            try:
                storage = InMemoryChatStorage()
                for i in range(10):
                    vm = VersionManager()
                    vm.create_version(f'wf_{worker_id}_{i}', {'data': i})
                return True
            except Exception as e:
                self.bug_tracker.add_bug(
                    'Concurrency',
                    'HIGH',
                    f'并发 worker {worker_id} 失败: {str(e)}',
                    traceback.format_exc()
                )
                return False
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(worker, i) for i in range(100)]
            for future in as_completed(futures):
                if future.result():
                    result['successful'] += 1
                else:
                    result['failed'] += 1
        
        print(f"  成功: {result['successful']}, 失败: {result['failed']}")
        return result
    
    def test_memory_leak(self) -> Dict:
        """测试 3: 内存泄漏检测"""
        print("📊 检测内存泄漏...")
        
        result = {
            'name': '内存泄漏检测',
            'initial_memory_mb': 0,
            'final_memory_mb': 0,
            'leaks_detected': []
        }
        
        gc.collect()
        time.sleep(1)
        
        initial_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        result['initial_memory_mb'] = initial_mem
        
        # 执行操作
        for i in range(5000):
            try:
                vm = VersionManager()
                vm.create_version(f'wf_{i}', {'data': 'x' * 100})
                
                if i % 1000 == 0:
                    gc.collect()
                    current_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                    growth = current_mem - initial_mem
                    growth_pct = (growth / initial_mem * 100) if initial_mem > 0 else 0
                    
                    if growth_pct > 20:
                        result['leaks_detected'].append({
                            'iteration': i,
                            'growth_percent': growth_pct
                        })
                        self.bug_tracker.add_bug(
                            'Memory Leak',
                            'HIGH',
                            f'内存增长超过 20%: {growth_pct:.2f}%',
                            f'迭代 {i}, 当前内存 {current_mem:.2f}MB'
                        )
                    
                    print(f"  迭代 {i}: 内存增长 {growth:.2f}MB ({growth_pct:.2f}%)")
                    
            except Exception as e:
                self.bug_tracker.add_bug(
                    'Memory Error',
                    'MEDIUM',
                    f'内存测试错误: {str(e)}',
                    traceback.format_exc()
                )
        
        gc.collect()
        time.sleep(1)
        
        final_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        result['final_memory_mb'] = final_mem
        
        return result
    
    def test_edge_cases(self) -> Dict:
        """测试 4: 边界条件测试"""
        print("📊 测试边界条件...")
        
        result = {
            'name': '边界条件测试',
            'passed': 0,
            'failed': 0
        }
        
        edge_cases = [
            ('', '空字符串'),
            (None, 'None值'),
            ({}, '空字典'),
            ('x' * 100000, '超长字符串'),
        ]
        
        for test_input, description in edge_cases:
            try:
                vm = VersionManager()
                vm.create_version('edge_test', {'input': test_input})
                result['passed'] += 1
            except Exception as e:
                result['failed'] += 1
                self.bug_tracker.add_bug(
                    'Edge Case',
                    'MEDIUM',
                    f'{description} 处理失败: {str(e)}',
                    traceback.format_exc()
                )
        
        print(f"  通过: {result['passed']}, 失败: {result['failed']}")
        return result
    
    def test_race_conditions(self) -> Dict:
        """测试 5: 竞态条件测试"""
        print("📊 测试竞态条件...")
        
        result = {
            'name': '竞态条件测试',
            'race_conditions_found': 0
        }
        
        counter = {'value': 0}
        iterations = 10000
        
        def increment():
            for _ in range(iterations):
                counter['value'] += 1
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        expected = iterations * 10
        actual = counter['value']
        
        if actual != expected:
            result['race_conditions_found'] += 1
            self.bug_tracker.add_bug(
                'Race Condition',
                'HIGH',
                f'计数器竞态: 期望 {expected}, 实际 {actual}',
                f'丢失更新: {expected - actual}'
            )
        
        print(f"  发现竞态条件: {result['race_conditions_found']}")
        return result
    
    def print_final_report(self):
        """打印最终报告"""
        print("\n" + "=" * 80)
        print("📋 MAOS 超长时间真实实践测试 - 最终报告")
        print("=" * 80)
        
        total_duration = time.time() - self.start_time
        print(f"\n⏱️  总耗时: {total_duration:.2f} 秒")
        
        print("\n🐛 Bug 发现统计:")
        print(f"  总计: {len(self.bug_tracker.bugs)}")
        for bug in self.bug_tracker.bugs:
            print(f"  - [{bug['severity']}] {bug['category']}: {bug['description']}")
        
        print("\n🧪 测试结果:")
        for r in self.test_results:
            status_icon = "✅" if r['status'] == 'PASSED' else "❌"
            print(f"  {status_icon} {r['name']}: {r['status']} ({r.get('duration', 0):.2f}秒)")
        
        print("\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)


def main():
    """主函数"""
    print("🚀 启动 MAOS 超长时间真实实践测试...\n")
    
    test = UltraLongRealPracticeTest()
    test.run_all_tests()


if __name__ == '__main__':
    main()
