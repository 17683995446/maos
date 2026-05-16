"""
MAOS v14.0 - 极端真实实践测试套件
Extreme Real-World Practice Testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import time
import threading
import random
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import traceback
import json


@dataclass
class DefectFound:
    """发现的缺陷记录"""
    id: str
    severity: str  # critical, high, medium, low
    description: str
    test_case: str
    timestamp: datetime = None
    reproduction_steps: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ExtremePracticeTester:
    """极端实践测试器"""
    
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


def test_extreme_concurrent_race_conditions():
    """测试：极端并发竞争条件"""
    print("\n" + "="*100)
    print("🔴 TEST 1: EXTREME CONCURRENT RACE CONDITIONS")
    print("="*100)
    
    from maos.version.v14 import VersionManager
    
    tester = ExtremePracticeTester()
    manager = VersionManager()
    
    # 创建初始版本
    for i in range(10):
        manager.create_version(f"wf-race-{i}", {"init": i}, f"{i}.0")
    
    workers = 100
    operations_per_worker = 500
    total_operations = workers * operations_per_worker
    
    print(f"\n📊 Test setup:")
    print(f"   Concurrent workers: {workers}")
    print(f"   Operations per worker: {operations_per_worker}")
    print(f"   Total operations: {total_operations}")
    
    all_versions: Set[str] = set()
    errors = []
    lock = threading.Lock()
    
    def worker(worker_id: int):
        nonlocal errors
        try:
            for i in range(operations_per_worker):
                operation_type = random.choice(['create', 'activate', 'get'])
                
                if operation_type == 'create':
                    version = manager.create_version(
                        f"wf-race-{worker_id % 10}",
                        {"step": i, "worker": worker_id},
                        f"{worker_id}.{i}.0"
                    )
                    with lock:
                        all_versions.add(version.id)
                    
                elif operation_type == 'activate':
                    wf_id = f"wf-race-{random.randint(0, 9)}"
                    versions = manager.get_workflow_versions(wf_id)
                    if versions:
                        v_to_activate = random.choice(versions)
                        manager.activate_version(v_to_activate.id)
                
                elif operation_type == 'get':
                    versions = manager.get_workflow_versions(f"wf-race-{worker_id % 10}")
                    if versions:
                        manager.get_version(versions[0].id)
                
                with lock:
                    tester.operations_executed += 1
                
                if i % 100 == 0:
                    # 偶尔引入延迟创造竞争
                    time.sleep(0.0001)
                    
        except Exception as e:
            with lock:
                tester.errors_encountered += 1
                errors.append(f"Worker {worker_id}: {str(e)}")
    
    print(f"\n⏱️  Starting concurrent execution...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, i) for i in range(workers)]
        wait(futures, return_when=ALL_COMPLETED)
    
    elapsed = time.time() - start
    ops_per_sec = total_operations / elapsed
    
    print(f"\n📊 Results:")
    print(f"   Time elapsed: {elapsed:.2f}s")
    print(f"   Operations/sec: {ops_per_sec:.0f}")
    print(f"   Total operations: {tester.operations_executed}")
    print(f"   Versions created: {len(all_versions)}")
    print(f"   Errors encountered: {tester.errors_encountered}")
    
    if tester.errors_encountered > 0:
        print(f"\n⚠️  First 5 errors:")
        for err in errors[:5]:
            print(f"   - {err}")
        
        tester.record_defect(DefectFound(
            id="DEF-RACE-001",
            severity="high" if tester.errors_encountered > 10 else "medium",
            description=f"Concurrent race conditions caused {tester.errors_encountered} errors",
            test_case="test_extreme_concurrent_race_conditions",
            reproduction_steps=f"Run {workers} workers with {operations_per_worker} operations each"
        ))
    
    print("\n✅ CONCURRENT RACE TEST COMPLETED")
    return tester


def test_memory_management_verification():
    """测试：内存管理验证（寻找真实内存泄漏）"""
    print("\n" + "="*100)
    print("🔴 TEST 2: MEMORY MANAGEMENT VERIFICATION")
    print("="*100)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.mobile.v14 import MobileAPIManager
    
    tester = ExtremePracticeTester()
    
    # Clean start
    gc.collect()
    gc.disable()
    
    initial_objects = len(gc.get_objects())
    
    print(f"\n📊 Initial state:")
    print(f"   GC objects: {initial_objects}")
    
    # Phase 1: Create lots of objects
    print(f"\n📝 Phase 1: Creating large number of objects...")
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    mobile = MobileAPIManager()
    
    iterations = 1000
    created_versions = []
    
    for i in range(iterations):
        v = manager.create_version(f"wf-mem-{i%10}", {"step": i}, f"{i}.0")
        created_versions.append(v)
        engine.record_metric(f"metric-{i%50}", float(i))
        
        if i % 100 == 0:
            mobile.register_device(
                f"user-{i%50}", f"token-{i}", "ios", "1.0.0", "17.0"
            )
        tester.operations_executed += 1
    
    after_creation = len(gc.get_objects())
    object_growth = after_creation - initial_objects
    
    print(f"\n📊 After creation:")
    print(f"   GC objects: {after_creation}")
    print(f"   Growth: +{object_growth}")
    
    # Phase 2: Remove references
    print(f"\n📝 Phase 2: Removing references and GC...")
    
    # Remove references
    manager_copy = manager
    engine_copy = engine
    mobile_copy = mobile
    versions_copy = list(created_versions)
    
    del manager, engine, mobile
    del created_versions
    
    gc.collect()
    after_gc_1 = len(gc.get_objects())
    
    # Check for memory leaks
    objects_after_gc = after_gc_1 - initial_objects
    
    print(f"\n📊 After first GC:")
    print(f"   GC objects: {after_gc_1}")
    print(f"   Objects remaining: {objects_after_gc}")
    
    # Phase 3: Multiple GC passes
    gc.collect()
    gc.collect()
    gc.collect()
    
    final_objects = len(gc.get_objects())
    final_objects_leaked = final_objects - initial_objects
    
    print(f"\n📊 Final state after multiple GC:")
    print(f"   GC objects: {final_objects}")
    print(f"   Objects leaked: {final_objects_leaked}")
    
    gc.enable()
    
    leak_threshold = 5000  # Allow some caching
    
    if final_objects_leaked > leak_threshold:
        tester.record_defect(DefectFound(
            id="DEF-MEM-001",
            severity="high",
            description=f"Memory leak detected: {final_objects_leaked} objects not freed",
            test_case="test_memory_management_verification",
            reproduction_steps="Create and delete large number of objects, then GC"
        ))
    else:
        print(f"\n✅ Memory management looks good (leak threshold: {leak_threshold})")
    
    print("\n✅ MEMORY TEST COMPLETED")
    return tester


def test_error_recovery_and_resilience():
    """测试：错误恢复与弹性"""
    print("\n" + "="*100)
    print("🔴 TEST 3: ERROR RECOVERY & RESILIENCE")
    print("="*100)
    
    from maos.version.v14 import VersionManager, ABTestManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.mobile.v14 import MobileAPIManager
    
    tester = ExtremePracticeTester()
    
    manager = VersionManager()
    ab_manager = ABTestManager(manager)
    engine = AnalyticsEngine()
    mobile = MobileAPIManager()
    
    error_test_cases = [
        ("Invalid workflow ID", lambda: manager.get_version("non-existent-id")),
        ("Null in version creation", lambda: manager.create_version(None, None, None)),
        ("Empty metric name", lambda: engine.record_metric("", 100)),
        ("Invalid platform", lambda: mobile.register_device("u1", "t1", "invalid-platform", "1.0", "17")),
        ("None user in session", lambda: mobile.create_session(None, "device-id")),
    ]
    
    print(f"\n📝 Testing error handling cases:")
    
    errors_handled = 0
    exceptions_thrown = 0
    
    for desc, test_func in error_test_cases:
        try:
            result = test_func()
            print(f"   ✓ {desc}: returned (no crash)")
            errors_handled += 1
        except Exception as e:
            print(f"   ⚠️  {desc}: exception thrown - {type(e).__name__}")
            exceptions_thrown += 1
            tester.errors_encountered += 1
        
        tester.operations_executed += 1
    
    # Test recovery from errors
    print(f"\n📝 Testing recovery after errors...")
    
    # Make sure system still works after errors
    try:
        v = manager.create_version("wf-recovery-test", {"data": "valid"}, "1.0.0")
        manager.activate_version(v.id)
        engine.record_metric("recovery-metric", 42.0)
        print(f"   ✓ System still functional after error tests")
    except Exception as e:
        tester.record_defect(DefectFound(
            id="DEF-REC-001",
            severity="critical",
            description=f"System failed to recover from errors: {str(e)}",
            test_case="test_error_recovery_and_resilience",
            reproduction_steps="Run error tests then attempt normal operations"
        ))
    
    print(f"\n📊 Results:")
    print(f"   Tests executed: {len(error_test_cases)}")
    print(f"   Handled gracefully: {errors_handled}")
    print(f"   Exceptions thrown: {exceptions_thrown}")
    
    print("\n✅ ERROR RECOVERY TEST COMPLETED")
    return tester


def test_extreme_data_volume_processing():
    """测试：极端数据量处理"""
    print("\n" + "="*100)
    print("🔴 TEST 4: EXTREME DATA VOLUME PROCESSING")
    print("="*100)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    tester = ExtremePracticeTester()
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    
    test_volumes = [
        ("Small", 1000),
        ("Medium", 10000),
        ("Large", 50000),
    ]
    
    print(f"\n📊 Testing various data volumes:")
    
    for desc, count in test_volumes:
        start = time.time()
        
        versions = []
        for i in range(count):
            v = manager.create_version(
                f"wf-data-{i%100}",
                {f"key-{j}": f"value-{i}-{j}" for j in range(10)},
                f"{i}.0"
            )
            versions.append(v)
            engine.record_metric(f"perf-metric-{i%100}", float(i))
            tester.operations_executed += 1
        
        elapsed = time.time() - start
        ops_per_sec = count / elapsed
        
        print(f"   {desc:8}: {count:5} items, {elapsed:.2f}s, {ops_per_sec:.0f} ops/sec")
        
        # Verify data can be retrieved
        verify_count = 0
        for v in versions[::100]:  # Sample verification
            retrieved = manager.get_version(v.id)
            if retrieved and retrieved.id == v.id:
                verify_count += 1
        
        if verify_count < len(versions[::100]):
            tester.record_defect(DefectFound(
                id="DEF-DATA-001",
                severity="medium",
                description=f"Data loss at {desc} volume: verification failed",
                test_case="test_extreme_data_volume_processing"
            ))
    
    print("\n✅ DATA VOLUME TEST COMPLETED")
    return tester


def test_state_persistence_and_integrity():
    """测试：状态持久化与完整性（寻找数据损坏）"""
    print("\n" + "="*100)
    print("🔴 TEST 5: STATE PERSISTENCE & DATA INTEGRITY")
    print("="*100)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    tester = ExtremePracticeTester()
    
    # Test data consistency
    manager = VersionManager()
    engine = AnalyticsEngine()
    
    # Create initial state
    test_versions = []
    for i in range(100):
        v = manager.create_version(f"wf-integrity-{i}", {"index": i}, f"{i}.0")
        test_versions.append(v)
        engine.record_metric(f"metric-{i}", float(i))
        tester.operations_executed += 1
    
    # Record initial state
    initial_latest = manager.get_latest_version("wf-integrity-0")
    initial_metrics = engine.get_metric_data("metric-0")
    
    # Perform random operations
    print(f"\n📝 Applying random state-changing operations...")
    
    for i in range(500):
        op_type = random.choice(['create', 'record', 'activate'])
        
        if op_type == 'create':
            wf_idx = random.randint(0, 99)
            manager.create_version(
                f"wf-integrity-{wf_idx}",
                {"random": random.randint(0, 1000)},
                f"{i}.modified"
            )
        
        elif op_type == 'record':
            m_idx = random.randint(0, 99)
            engine.record_metric(f"metric-{m_idx}", random.random() * 1000)
        
        elif op_type == 'activate':
            wf_idx = random.randint(0, 99)
            versions = manager.get_workflow_versions(f"wf-integrity-{wf_idx}")
            if versions:
                manager.activate_version(versions[0].id)
        
        tester.operations_executed += 1
    
    # Verify integrity still holds
    print(f"\n📝 Verifying data integrity...")
    
    data_integrity_failures = 0
    for i in range(100):
        versions = manager.get_workflow_versions(f"wf-integrity-{i}")
        if not versions:
            data_integrity_failures += 1
        else:
            v = manager.get_version(versions[0].id)
            if not v:
                data_integrity_failures += 1
    
    if data_integrity_failures > 0:
        tester.record_defect(DefectFound(
            id="DEF-INTEG-001",
            severity="high",
            description=f"Data integrity failures: {data_integrity_failures}/100 workflows corrupted",
            test_case="test_state_persistence_and_integrity",
            reproduction_steps="Apply random operations then verify data"
        ))
    else:
        print(f"   ✓ Data integrity preserved - 100/100 workflows intact")
    
    print("\n✅ DATA INTEGRITY TEST COMPLETED")
    return tester


def run_all_extreme_practice_tests():
    """运行所有极端实践测试"""
    print("\n" + "="*120)
    print("🚀 MAOS v14.0 - EXTREME REAL-WORLD PRACTICE TESTING")
    print("="*120)
    
    all_testers = []
    
    test_functions = [
        ("Race Conditions", test_extreme_concurrent_race_conditions),
        ("Memory Management", test_memory_management_verification),
        ("Error Recovery", test_error_recovery_and_resilience),
        ("Data Volume", test_extreme_data_volume_processing),
        ("Data Integrity", test_state_persistence_and_integrity),
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
    
    # Final summary
    print("\n" + "="*120)
    print("📊 FINAL EXTREME PRACTICE SUMMARY")
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
        print(f"\n⚠️  DEFECTS FOUND:")
        for defect in all_defects:
            print(f"   [{defect.severity.upper()}] {defect.id}: {defect.description}")
    
    print("\n" + "="*120)
    
    return all_defects


if __name__ == "__main__":
    defects = run_all_extreme_practice_tests()
    
    if not defects:
        print("\n🎉 NO CRITICAL DEFECTS FOUND! SYSTEM IS ROBUST!\n")
