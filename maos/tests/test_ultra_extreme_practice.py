"""
MAOS v14.0 - 超极端真实实践测试套件
目的：发现系统中隐藏的深层缺陷
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import time
import threading
import random
import gc
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import traceback
import weakref
import copy


@dataclass
class DefectFound:
    """发现的缺陷记录"""
    id: str
    severity: str  # critical, high, medium, low
    description: str
    test_case: str
    timestamp: datetime = None
    reproduction_steps: str = ""
    fix_suggestion: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class UltraExtremeTester:
    """超极端测试器"""
    
    def __init__(self):
        self.defects_found: List[DefectFound] = []
        self.operations_executed = 0
        self.errors_encountered = 0
        self.start_time = time.time()
        
    def record_defect(self, defect: DefectFound):
        """记录发现的缺陷"""
        self.defects_found.append(defect)
        print(f"\n⚠️  DEFECT FOUND: [{defect.severity}] {defect.description}")
        print(f"   Test case: {defect.test_case}")
        if defect.fix_suggestion:
            print(f"   Suggestion: {defect.fix_suggestion}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        elapsed = time.time() - self.start_time
        severity_counts = {
            'critical': 0, 'high': 0, 'medium': 0, 'low': 0
        }
        for defect in self.defects_found:
            if defect.severity in severity_counts:
                severity_counts[defect.severity] += 1
        
        return {
            'elapsed_seconds': round(elapsed, 2),
            'operations_executed': self.operations_executed,
            'errors_encountered': self.errors_encountered,
            'defects_found': len(self.defects_found),
            'severity_breakdown': severity_counts
        }


def test_extreme_thread_safety_with_conflicts():
    """测试1：极端线程安全测试 - 故意制造冲突"""
    print("\n" + "="*120)
    print("🔥 TEST 1: EXTREME THREAD SAFETY - CONFLICT GENERATION")
    print("="*120)
    
    from maos.version.v14 import VersionManager, ABTestManager
    
    tester = UltraExtremeTester()
    manager = VersionManager()
    ab_manager = ABTestManager(manager)
    
    # 创建初始数据
    for i in range(50):
        manager.create_version(f"wf-shared-{i}", {"data": i}, f"{i}.0")
    
    # 超极端并发参数
    workers = 200  # 200个并发线程
    operations_per_worker = 2000  # 每个线程2000次操作
    total_operations = workers * operations_per_worker
    
    print(f"\n📊 Test setup:")
    print(f"   Concurrent workers: {workers}")
    print(f"   Operations per worker: {operations_per_worker}")
    print(f"   Total operations: {total_operations}")
    
    errors = []
    error_lock = threading.Lock()
    results_lock = threading.Lock()
    
    # 跟踪状态用于验证
    shared_versions = []
    shared_versions_lock = threading.Lock()
    
    def worker(worker_id: int):
        nonlocal errors
        try:
            for i in range(operations_per_worker):
                wf_idx = random.randint(0, 49)
                wf_id = f"wf-shared-{wf_idx}"
                
                # 高冲突操作
                choice = random.random()
                if choice < 0.3:
                    # 创建版本
                    ver = manager.create_version(wf_id, 
                        {"worker": worker_id, "step": i, 
                         "data": f"test-{worker_id}-{i}"},
                        f"v{worker_id}.{i}")
                    with shared_versions_lock:
                        shared_versions.append(ver.id)
                elif choice < 0.6:
                    # 激活随机版本
                    versions = manager.get_workflow_versions(wf_id)
                    if versions:
                        v_to_activate = random.choice(versions)
                        manager.activate_version(v_to_activate.id)
                elif choice < 0.8:
                    # 读取操作
                    manager.get_workflow_versions(wf_id)
                    manager.get_latest_version(wf_id)
                else:
                    # 版本回滚（如果有）
                    versions = manager.get_workflow_versions(wf_id)
                    if len(versions) > 1:
                        old_version = versions[0]
                        manager.rollback_to_version(wf_id, old_version.id)
                
                with results_lock:
                    tester.operations_executed += 1
                
                if i % 500 == 0:
                    time.sleep(0.0001)  # 增加冲突概率
                    
        except Exception as e:
            with error_lock:
                tester.errors_encountered += 1
                errors.append(f"Worker {worker_id}: {type(e).__name__}: {str(e)}")
    
    print(f"\n⏱️  Starting extreme concurrent execution...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, i) for i in range(workers)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                with error_lock:
                    tester.errors_encountered += 1
                    errors.append(f"Future error: {str(e)}")
    
    elapsed = time.time() - start
    ops_per_sec = total_operations / elapsed
    
    print(f"\n📊 Results:")
    print(f"   Time elapsed: {elapsed:.2f}s")
    print(f"   Operations/sec: {ops_per_sec:.0f}")
    print(f"   Total operations: {tester.operations_executed}")
    print(f"   Errors encountered: {tester.errors_encountered}")
    
    # 验证数据一致性
    print(f"\n🔍 Verifying data consistency after extreme concurrency...")
    consistency_issues = 0
    
    for i in range(50):
        wf_id = f"wf-shared-{i}"
        versions = manager.get_workflow_versions(wf_id)
        
        if not versions:
            continue
            
        # 检查所有版本是否可访问
        for v in versions:
            retrieved = manager.get_version(v.id)
            if not retrieved:
                consistency_issues += 1
    
    if consistency_issues > 0:
        tester.record_defect(DefectFound(
            id="DEF-CONCUR-001",
            severity="critical",
            description=f"Data consistency failures: {consistency_issues} versions missing",
            test_case="test_extreme_thread_safety_with_conflicts",
            reproduction_steps=f"Run {workers} concurrent workers with {operations_per_worker} operations each",
            fix_suggestion="Add proper thread synchronization (locks) to VersionManager methods"
        ))
    
    if tester.errors_encountered > 50:
        tester.record_defect(DefectFound(
            id="DEF-CONCUR-002",
            severity="high",
            description=f"High error rate: {tester.errors_encountered} errors in {total_operations} operations",
            test_case="test_extreme_thread_safety_with_conflicts",
            reproduction_steps=f"Run with {workers} concurrent workers",
            fix_suggestion="Improve error handling and add thread safety mechanisms"
        ))
    
    print(f"\n✅ THREAD SAFETY TEST COMPLETED")
    return tester


def test_deep_memory_leak_detection():
    """测试2：深度内存泄漏检测 - 使用弱引用等高级技术"""
    print("\n" + "="*120)
    print("🧪 TEST 2: ADVANCED MEMORY LEAK DETECTION")
    print("="*120)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.mobile.v14 import MobileAPIManager
    
    tester = UltraExtremeTester()
    
    gc.collect()
    gc.disable()
    
    initial_gc_count = len(gc.get_objects())
    initial_stats = gc.get_stats()
    
    print(f"\n📊 Initial state:")
    print(f"   GC objects: {initial_gc_count}")
    
    # 创建大量对象并尝试检测泄漏
    print(f"\n📝 Creating and managing large number of objects...")
    
    iterations = 5000
    object_refs = []
    weak_refs = []
    
    for i in range(iterations):
        manager = VersionManager()
        engine = AnalyticsEngine()
        mobile = MobileAPIManager()
        
        for j in range(10):
            v = manager.create_version(f"wf-{i}-{j}", {"i": i, "j": j}, f"{j}.0")
            engine.record_metric(f"metric-{i}", float(j))
            if j == 0:
                mobile.register_device(f"user-{i}", f"token-{i}", "ios", "1.0", "17.0")
        
        # 保存对象引用和弱引用
        object_refs.append((manager, engine, mobile))
        weak_refs.append((weakref.ref(manager), weakref.ref(engine), weakref.ref(mobile)))
        
        tester.operations_executed += 1
    
    after_creation = len(gc.get_objects())
    object_growth = after_creation - initial_gc_count
    
    print(f"\n📊 After creation:")
    print(f"   GC objects: {after_creation}")
    print(f"   Growth: +{object_growth}")
    
    # 删除引用
    print(f"\n📝 Removing references and testing object cleanup...")
    
    del object_refs
    
    gc.collect()
    gc.collect()
    gc.collect()
    
    # 检查弱引用
    dead_weak_refs = 0
    alive_weak_refs = 0
    
    for m_ref, e_ref, mob_ref in weak_refs:
        if m_ref() is not None or e_ref() is not None or mob_ref() is not None:
            alive_weak_refs += 1
        else:
            dead_weak_refs += 1
    
    final_objects = len(gc.get_objects())
    leaked_objects = final_objects - initial_gc_count
    
    print(f"\n📊 Final state:")
    print(f"   Final GC objects: {final_objects}")
    print(f"   Leaked objects estimate: {leaked_objects}")
    print(f"   Weak refs alive: {alive_weak_refs} / {len(weak_refs)}")
    
    gc.enable()
    
    # 评估
    if alive_weak_refs > iterations * 0.1:
        tester.record_defect(DefectFound(
            id="DEF-MEM-002",
            severity="high",
            description=f"Significant memory leak detected: {alive_weak_refs} objects not GC'd",
            test_case="test_deep_memory_leak_detection",
            reproduction_steps="Create large number of VersionManager/Engine instances and remove references",
            fix_suggestion="Check for circular references or static caches holding onto objects"
        ))
    
    if leaked_objects > 10000:
        tester.record_defect(DefectFound(
            id="DEF-MEM-003",
            severity="critical",
            description=f"Severe memory growth: {leaked_objects} objects not freed",
            test_case="test_deep_memory_leak_detection",
            reproduction_steps="Create 5000 iterations of objects",
            fix_suggestion="Implement proper cleanup methods or __del__ methods carefully"
        ))
    
    print(f"\n✅ MEMORY LEAK TEST COMPLETED")
    return tester


def test_extreme_edge_cases():
    """测试3：极端边缘情况"""
    print("\n" + "="*120)
    print("⚡ TEST 3: EXTREME EDGE CASES")
    print("="*120)
    
    from maos.version.v14 import VersionManager, ABTestManager
    from maos.analytics.v14 import AnalyticsEngine
    
    tester = UltraExtremeTester()
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    ab_manager = ABTestManager(manager)
    
    print(f"\n📝 Testing edge cases...")
    
    edge_cases = [
        ("Empty workflow ID", lambda: manager.create_version("", {}, "1.0")),
        ("Very long workflow ID", lambda: manager.create_version("a"*1000, {}, "1.0")),
        ("None definition", lambda: manager.create_version("test-none", None, "1.0")),
        ("Very large definition", lambda: manager.create_version("test-large", {f"k{i}": f"v{i}"*1000 for i in range(1000)}, "1.0")),
        ("Invalid version ID for get_version", lambda: manager.get_version("nonexistent-id-123456789")),
        ("Empty metric name", lambda: engine.record_metric("", 0)),
        ("NaN metric value", lambda: engine.record_metric("test-nan", float('nan'))),
        ("Infinity metric value", lambda: engine.record_metric("test-inf", float('inf'))),
        ("Negative metric value", lambda: engine.record_metric("test-negative", -100)),
        ("Empty AB test name", lambda: ab_manager.create_test("", "wf-test", [])),
        ("Empty AB test variants", lambda: ab_manager.create_test("test-empty", "wf-test", [])),
    ]
    
    exceptions = []
    
    for desc, test_func in edge_cases:
        try:
            result = test_func()
            print(f"   ✓ {desc}: handled gracefully")
            tester.operations_executed += 1
        except Exception as e:
            exceptions.append(f"{desc}: {type(e).__name__}: {str(e)}")
            tester.errors_encountered += 1
            print(f"   ⚠️  {desc}: raised {type(e).__name__}")
    
    # 进一步测试 - 测试系统在极端情况后的恢复能力
    print(f"\n📝 Verifying system recovery after edge cases...")
    
    try:
        # 正常操作应继续工作
        v = manager.create_version("recovery-test", {"ok": True}, "1.0")
        manager.activate_version(v.id)
        engine.record_metric("recovery-metric", 42.0)
        
        retrieved = manager.get_version(v.id)
        if not retrieved or retrieved.version != "1.0":
            tester.record_defect(DefectFound(
                id="DEF-EDGE-001",
                severity="high",
                description="System failed to recover properly after edge cases",
                test_case="test_extreme_edge_cases",
                reproduction_steps="Run edge case tests then attempt normal operation",
                fix_suggestion="Ensure edge case errors don't leave system in inconsistent state"
            ))
        else:
            print(f"   ✓ System recovered successfully")
            
    except Exception as e:
        tester.record_defect(DefectFound(
            id="DEF-EDGE-002",
            severity="critical",
            description=f"System crashed during recovery: {str(e)}",
            test_case="test_extreme_edge_cases",
            reproduction_steps="Same as above",
            fix_suggestion="Add try/except blocks and proper state management"
        ))
    
    print(f"\n✅ EDGE CASE TEST COMPLETED")
    return tester


def test_data_consistency_under_chaos():
    """测试4：混乱状态下的数据一致性"""
    print("\n" + "="*120)
    print("🎯 TEST 4: DATA CONSISTENCY UNDER CHAOS")
    print("="*120)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    tester = UltraExtremeTester()
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    
    # 创建初始可验证状态
    initial_state = {}
    for i in range(100):
        wf_id = f"wf-consistent-{i}"
        v = manager.create_version(wf_id, {"id": i, "value": f"initial-{i}"}, f"{i}.0")
        initial_state[wf_id] = v.id
        engine.record_metric(f"metric-{i}", float(i))
        tester.operations_executed += 1
    
    print(f"\n📝 Applying chaotic mixed operations...")
    
    # 应用各种混合操作
    for round in range(10):
        for i in range(100):
            wf_id = f"wf-consistent-{i}"
            
            operation = random.choice([
                "create", "activate", "record_metric",
                "get_versions", "get_latest"
            ])
            
            if operation == "create":
                manager.create_version(wf_id, 
                    {"round": round, "i": i, "random": random.random()},
                    f"{i}.{round}")
            elif operation == "activate":
                versions = manager.get_workflow_versions(wf_id)
                if versions:
                    manager.activate_version(versions[-1].id)
            elif operation == "record_metric":
                engine.record_metric(f"metric-{i}", random.random() * 100)
            elif operation == "get_versions":
                manager.get_workflow_versions(wf_id)
            elif operation == "get_latest":
                manager.get_latest_version(wf_id)
            
            tester.operations_executed += 1
    
    print(f"\n🔍 Verifying final state consistency...")
    
    consistency_failures = 0
    
    for i in range(100):
        wf_id = f"wf-consistent-{i}"
        
        versions = manager.get_workflow_versions(wf_id)
        if not versions:
            consistency_failures += 1
            continue
            
        # 验证所有版本都可访问
        for v in versions:
            retrieved = manager.get_version(v.id)
            if not retrieved:
                consistency_failures += 1
        
        # 验证最新版本可以获取
        latest = manager.get_latest_version(wf_id)
        if not latest:
            consistency_failures += 1
    
    if consistency_failures > 0:
        tester.record_defect(DefectFound(
            id="DEF-CONSIST-001",
            severity="high",
            description=f"Data consistency failures: {consistency_failures} issues",
            test_case="test_data_consistency_under_chaos",
            reproduction_steps="Apply 1000 chaotic mixed operations",
            fix_suggestion="Add transactional semantics or write-ahead logging"
        ))
    else:
        print(f"   ✓ Data consistency preserved")
    
    print(f"\n✅ CONSISTENCY TEST COMPLETED")
    return tester


def test_long_term_stability():
    """测试5：长期稳定性 - 模拟长时间运行"""
    print("\n" + "="*120)
    print("⏰ TEST 5: LONG-TERM STABILITY & PERFORMANCE DEGRADATION")
    print("="*120)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    tester = UltraExtremeTester()
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    
    total_iterations = 100
    ops_per_iteration = 100
    
    print(f"\n📊 Test setup:")
    print(f"   Total iterations: {total_iterations}")
    print(f"   Operations per iteration: {ops_per_iteration}")
    
    iteration_times = []
    iteration_errors = []
    
    for iteration in range(total_iterations):
        start_time = time.time()
        errors = 0
        
        for i in range(ops_per_iteration):
            try:
                wf_id = f"wf-stress-{iteration}-{i % 20}"
                manager.create_version(wf_id, {"iter": iteration, "i": i}, f"{i}.0")
                engine.record_metric(f"stress-{iteration}", float(i))
                manager.get_workflow_versions(wf_id)
            except Exception as e:
                errors += 1
                tester.errors_encountered += 1
            
            tester.operations_executed += 1
        
        elapsed = time.time() - start_time
        iteration_times.append(elapsed)
        iteration_errors.append(errors)
        
        if iteration % 20 == 0:
            print(f"   Iteration {iteration:3d}: {elapsed:.3f}s, {errors} errors")
    
    # 分析性能趋势
    print(f"\n📊 Performance analysis:")
    
    first_half_avg = sum(iteration_times[:total_iterations//2]) / (total_iterations//2)
    second_half_avg = sum(iteration_times[total_iterations//2:]) / (total_iterations//2)
    
    print(f"   First half avg: {first_half_avg:.3f}s")
    print(f"   Second half avg: {second_half_avg:.3f}s")
    
    slowdown_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
    
    print(f"   Slowdown ratio: {slowdown_ratio:.2f}x")
    
    if slowdown_ratio > 2.0:
        tester.record_defect(DefectFound(
            id="DEF-PERF-001",
            severity="medium",
            description=f"Performance degradation detected: {slowdown_ratio:.2f}x slowdown",
            test_case="test_long_term_stability",
            reproduction_steps="Run 100 iterations of 100 operations each",
            fix_suggestion="Check for O(n) or worse algorithms, add cleanup of old data"
        ))
    
    total_errors = sum(iteration_errors)
    if total_errors > total_iterations * ops_per_iteration * 0.01:
        tester.record_defect(DefectFound(
            id="DEF-STAB-001",
            severity="high",
            description=f"Error rate too high: {total_errors} errors in {total_iterations*ops_per_iteration} operations",
            test_case="test_long_term_stability",
            reproduction_steps="Long-running stress test",
            fix_suggestion="Investigate and fix intermittent errors"
        ))
    
    print(f"\n✅ STABILITY TEST COMPLETED")
    return tester


def run_all_ultra_extreme_tests():
    """运行所有超极端测试"""
    print("\n" + "="*120)
    print("🚀 MAOS v14.0 - ULTRA EXTREME REAL-WORLD PRACTICE TESTING")
    print("="*120)
    
    all_testers = []
    
    test_functions = [
        ("Thread Safety", test_extreme_thread_safety_with_conflicts),
        ("Memory Leaks", test_deep_memory_leak_detection),
        ("Edge Cases", test_extreme_edge_cases),
        ("Consistency", test_data_consistency_under_chaos),
        ("Long-term Stability", test_long_term_stability),
    ]
    
    total_start = time.time()
    
    for test_name, test_func in test_functions:
        try:
            tester = test_func()
            all_testers.append((test_name, tester))
        except Exception as e:
            print(f"\n❌ FATAL ERROR IN TEST '{test_name}': {str(e)}")
            traceback.print_exc()
    
    total_elapsed = time.time() - total_start
    
    # 最终摘要
    print("\n" + "="*120)
    print("📊 FINAL ULTRA EXTREME PRACTICE SUMMARY")
    print("="*120)
    
    all_defects = []
    total_ops = 0
    total_errors = 0
    
    for test_name, tester in all_testers:
        all_defects.extend(tester.defects_found)
        total_ops += tester.operations_executed
        total_errors += tester.errors_encountered
        
        summary = tester.get_summary()
        print(f"\n{test_name}:")
        print(f"   Operations: {summary['operations_executed']}")
        print(f"   Errors: {summary['errors_encountered']}")
        print(f"   Defects: {len(tester.defects_found)}")
    
    print(f"\n{'='*120}")
    print(f"📊 OVERALL SUMMARY:")
    print(f"   Total time: {total_elapsed:.2f}s")
    print(f"   Total operations: {total_ops}")
    print(f"   Total errors: {total_errors}")
    print(f"   Total defects found: {len(all_defects)}")
    
    if all_defects:
        print(f"\n⚠️  ALL DEFECTS FOUND:")
        for defect in sorted(all_defects, key=lambda d: ['critical', 'high', 'medium', 'low'].index(d.severity)):
            print(f"\n   [{defect.severity.upper()}] {defect.id}")
            print(f"   Description: {defect.description}")
            if defect.fix_suggestion:
                print(f"   Fix: {defect.fix_suggestion}")
    
    print("\n" + "="*120)
    
    return all_defects


if __name__ == "__main__":
    defects = run_all_ultra_extreme_tests()
    
    if not defects:
        print("\n🎉 NO DEFECTS FOUND! SYSTEM IS EXTREMELY ROBUST!\n")
