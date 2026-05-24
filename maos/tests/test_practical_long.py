#!/usr/bin/env python3
"""
MAOS 超长时间测试套件 v3.0 (实用版)
运行时间: 10分钟
包含7个深度测试阶段，发现系统潜在问题
"""

import threading
import time
import random
import sys
import gc
import traceback
from datetime import datetime
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


class BugTracker:
    """Bug追踪器"""
    def __init__(self):
        self.bugs = []
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def record(self, category, severity, description, stack=''):
        bug = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': time.time() - self.start_time,
            'category': category,
            'severity': severity,
            'description': description,
            'stack': stack
        }
        with self.lock:
            self.bugs.append(bug)
        
        icons = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}
        icon = icons.get(severity, '⚪')
        print(f"{icon} [{severity}] [{bug['elapsed']:.1f}s] {category}: {description[:80]}")
    
    def summary(self):
        with self.lock:
            return {
                'total': len(self.bugs),
                'critical': len([b for b in self.bugs if b['severity'] == 'CRITICAL']),
                'high': len([b for b in self.bugs if b['severity'] == 'HIGH']),
                'medium': len([b for b in self.bugs if b['severity'] == 'MEDIUM']),
                'low': len([b for b in self.bugs if b['severity'] == 'LOW'])
            }


def run_tests():
    """运行所有测试"""
    tracker = BugTracker()
    start_time = time.time()
    
    print("="*90)
    print("🚀 MAOS 超长时间极限测试 v3.0 (实用版)")
    print("="*90)
    print(f"开始: {datetime.now().isoformat()}")
    print(f"目标: 10分钟深度测试")
    print("="*90)
    
    # 阶段1: 连续运行 (2分钟)
    print("\n⏱️ 阶段1: 连续运行测试 (2分钟)")
    ops1, errs1 = 0, 0
    t1_start = time.time()
    while time.time() - t1_start < 120:
        try:
            registry = AgentRegistry()
            broker = MessageBroker()
            vm = VersionManager()
            ae = AnalyticsEngine()
            
            registry.register({'id': f'agent_{ops1}', 'name': f'Agent {ops1}'})
            broker.publish({'channel': 'test', 'data': ops1})
            vm.create_version(f'wf_{ops1}', {'data': ops1})
            ae.record_metric('test', ops1, {'tag': 'continuous'})
            
            ops1 += 4
            if ops1 % 5000 == 0:
                print(f"  [{time.time()-t1_start:.1f}s] 操作: {ops1}, 错误: {errs1}")
        except Exception as e:
            errs1 += 1
            tracker.record('Continuous', 'MEDIUM', f'运行错误: {str(e)}', traceback.format_exc())
    print(f"  完成: {ops1} 操作, {errs1} 错误")
    
    # 阶段2: 并发压力 (2分钟)
    print("\n⚡阶段2: 并发压力测试 (2分钟)")
    ops2, errs2 = 0, 0
    t2_start = time.time()
    
    while time.time() - t2_start < 120:
        def worker(wid):
            local_ops, local_errs = 0, 0
            for i in range(50):
                try:
                    vm = VersionManager()
                    vm.create_version(f'wf_{wid}_{i}', {'data': i})
                    local_ops += 1
                except:
                    local_errs += 1
            return local_ops, local_errs
        
        with ThreadPoolExecutor(max_workers=30) as executor:
            results = [executor.submit(worker, i).result() for i in range(30)]
            for o, e in results:
                ops2 += o
                errs2 += e
        
        if ops2 % 5000 < 100:
            print(f"  [{time.time()-t2_start:.1f}s] 操作: {ops2}, 错误: {errs2}")
    print(f"  完成: {ops2} 操作, {errs2} 错误")
    
    # 阶段3: 内存压力 (2分钟)
    print("\n💾阶段3: 内存压力测试 (2分钟)")
    ops3, errs3 = 0, 0
    t3_start = time.time()
    gc.collect()
    init_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    
    while time.time() - t3_start < 120:
        try:
            for i in range(50):
                vm = VersionManager()
                vm.create_version(f'mem_wf_{ops3}', {'data': 'x' * 1000, 'ts': time.time()})
                ops3 += 1
        except Exception as e:
            errs3 += 1
            tracker.record('Memory', 'MEDIUM', f'内存错误: {str(e)}', traceback.format_exc())
        
        if ops3 % 2000 == 0:
            gc.collect()
            curr_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            growth = curr_mem - init_mem
            growth_pct = (growth / init_mem * 100) if init_mem > 0 else 0
            print(f"  [{time.time()-t3_start:.1f}s] 操作: {ops3}, 内存: {curr_mem:.1f}MB, 增长: {growth:.1f}MB ({growth_pct:.1f}%)")
            
            if growth_pct > 40:
                tracker.record('Memory Leak', 'HIGH', f'疑似泄漏: {growth:.1f}MB ({growth_pct:.1f}%)', f'op:{ops3}')
    
    gc.collect()
    final_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    print(f"  完成: {ops3} 操作, {errs3} 错误")
    print(f"  内存: {init_mem:.1f}MB -> {final_mem:.1f}MB (增长 {final_mem-init_mem:.1f}MB)")
    
    # 阶段4: 竞态条件 (2分钟)
    print("\n🔀阶段4: 竞态条件探测 (2分钟)")
    races_found = 0
    ops4 = 0
    t4_start = time.time()
    
    while time.time() - t4_start < 120:
        shared = {'counter': 0}
        threads = []
        
        for _ in range(10):
            def inc():
                for _ in range(5000):
                    shared['counter'] += 1
            threads.append(threading.Thread(target=inc))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        ops4 += 50000
        expected = 50000
        actual = shared['counter']
        lost = expected - actual
        
        if lost > 0:
            races_found += 1
            tracker.record('Race Condition', 'HIGH', f'计数器竞态: 丢失 {lost}', f'期望{expected} 实际{actual}')
        
        if races_found > 0 or ops4 % 200000 < 1000:
            print(f"  [{time.time()-t4_start:.1f}s] 操作: {ops4}, 竞态: {races_found}")
    print(f"  完成: {ops4} 操作, {races_found} 个竞态条件")
    
    # 阶段5: 边界条件 (1分钟)
    print("\n🎯阶段5: 边界条件探测 (1分钟)")
    ops5, errs5 = 0, 0
    t5_start = time.time()
    
    edge_cases = [
        ('', '空字符串'), (None, 'None'), ({}, '空字典'), ([], '空列表'),
        ({'deep': {'nested': 'value'}}, '深层嵌套'),
        ('<script>alert(1)</script>', 'XSS'),
        ("'; DROP TABLE; --", 'SQL注入'),
        ('中文测试', 'Unicode'),
    ]
    
    while time.time() - t5_start < 60:
        test_input, desc = random.choice(edge_cases)
        try:
            vm = VersionManager()
            vm.create_version(f'edge_{ops5}', {'input': test_input, 'type': desc})
            ops5 += 1
        except Exception as e:
            errs5 += 1
            tracker.record('Edge Case', 'MEDIUM', f'{desc} 失败: {str(e)}', traceback.format_exc())
    print(f"  完成: {ops5} 操作, {errs5} 错误")
    
    # 阶段6: 系统集成 (1分钟)
    print("\n🔗阶段6: 系统集成测试 (1分钟)")
    ops6, errs6 = 0, 0
    t6_start = time.time()
    
    while time.time() - t6_start < 60:
        try:
            orch = OrchestratorService()
            for i in range(5):
                orch.register_agent({'id': f'int_{i}', 'name': f'Agent {i}'})
            task = orch.create_task({'id': f'task_{ops6}', 'name': f'Task {ops6}'})
            orch.assign_task_to_agent(task, 'int_0')
            orch.broadcast_message({'type': 'test', 'data': ops6})
            ops6 += 1
        except Exception as e:
            errs6 += 1
            tracker.record('Integration', 'HIGH', f'集成错误: {str(e)}', traceback.format_exc())
    print(f"  完成: {ops6} 操作, {errs6} 错误")
    
    # 阶段7: 混沌工程 (1分钟)
    print("\n🌪️阶段7: 混沌工程测试 (1分钟)")
    chaos_tests, resilience = 0, 0
    t7_start = time.time()
    
    while time.time() - t7_start < 60:
        chaos_tests += 1
        try:
            scenario = random.choice(['rapid', 'memory', 'threads', 'recursion'])
            
            if scenario == 'rapid':
                [VersionManager() for _ in range(100)]
            elif scenario == 'memory':
                {'x' * 100000 for _ in range(10)}
            elif scenario == 'threads':
                threads = [threading.Thread(target=lambda: time.sleep(0.01)) for _ in range(50)]
                [t.start() for t in threads]
                [t.join() for t in threads]
            elif scenario == 'recursion':
                def rec(d): return rec(d+1) if d < 100 else d
                rec(0)
            
            resilience += 1
        except Exception as e:
            tracker.record('Chaos', 'MEDIUM', f'混沌场景失败: {str(e)}', '')
        
        if chaos_tests % 50 == 0:
            print(f"  [{time.time()-t7_start:.1f}s] 混沌: {chaos_tests}, 韧性: {resilience}")
    
    print(f"  完成: {chaos_tests} 测试, 韧性: {resilience} ({resilience/chaos_tests*100:.0f}%)")
    
    # 最终报告
    total_duration = time.time() - start_time
    total_ops = ops1 + ops2 + ops3 + ops4 + ops5 + ops6
    total_errors = errs1 + errs2 + errs3 + errs6
    
    print("\n" + "="*90)
    print("📊 MAOS 超长时间极限测试 - 最终报告")
    print("="*90)
    
    print(f"\n⏱️  总耗时: {total_duration:.2f}秒 ({total_duration/60:.2f}分钟)")
    print(f"🧮 总操作: {total_ops:,}")
    
    summary = tracker.summary()
    print(f"\n🐛 Bug统计:")
    print(f"   总计: {summary['total']}")
    print(f"   🔴 CRITICAL: {summary['critical']}")
    print(f"   🟠 HIGH: {summary['high']}")
    print(f"   🟡 MEDIUM: {summary['medium']}")
    print(f"   🔵 LOW: {summary['low']}")
    
    gc.collect()
    final_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    print(f"\n💾 内存: {final_mem:.1f}MB")
    
    health = 100 - summary['critical']*20 - summary['high']*10 - summary['medium']*5
    health = max(0, health)
    
    status = "🌟优秀" if health>=90 else "✅良好" if health>=70 else "⚠️一般" if health>=50 else "❌需改进"
    print(f"\n🏥 健康评分: {health}/100 - {status}")
    
    if tracker.bugs:
        print(f"\n📝 详细Bug (前10个):")
        for i, b in enumerate(tracker.bugs[:10], 1):
            print(f"   [{i}] {b['category']} - {b['severity']}: {b['description'][:60]}")
    
    print("\n" + "="*90)
    print("✅ 测试完成")
    print("="*90)


if __name__ == '__main__':
    run_tests()
