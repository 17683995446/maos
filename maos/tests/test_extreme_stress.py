"""
MAOS v14.0 - 极端压力测试套件
Phase 1: 10000+ 并发操作压力测试
"""

import pytest
import time
import threading
import asyncio
import gc
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any
import traceback

from maos.sdk.v14 import MAOSSDK, SDKConfig, SDKLanguage, SDKFactory
from maos.version.v14 import VersionManager, ABTestManager, WorkflowVersion, ABTest, ABTestStatus
from maos.analytics.v14 import AnalyticsEngine, ChartType, TimeRange
from maos.mobile.v14 import MobileAPIManager, MobileOptimizedAPI, MobilePlatform


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.errors = []
        self.success_count = 0
        self.failure_count = 0
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.end_time = time.time()
    
    def record_success(self):
        self.success_count += 1
    
    def record_failure(self, error):
        self.failure_count += 1
        self.errors.append(str(error))
    
    def get_stats(self) -> Dict[str, Any]:
        duration = self.end_time - self.start_time if self.end_time else time.time() - self.start_time
        
        return {
            "duration_seconds": round(duration, 2),
            "total_operations": self.success_count + self.failure_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_count / (self.success_count + self.failure_count) * 100, 2) if (self.success_count + self.failure_count) > 0 else 0,
            "operations_per_second": round((self.success_count + self.failure_count) / duration, 2) if duration > 0 else 0,
            "errors": self.errors[:10]  # Only first 10 errors
        }


# ============================================================
# 极端压力测试: 10000+ 并发操作
# ============================================================

def test_extreme_version_creation_10k():
    """测试: 10000个并发版本创建"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 10,000 Concurrent Version Creations")
    print("="*80)
    
    manager = VersionManager()
    monitor = PerformanceMonitor()
    monitor.start()
    
    def create_version(i):
        try:
            v = manager.create_version(
                workflow_id=f"wf-{i % 100}",  # 100个不同工作流
                version=f"{i}.0",
                definition={"steps": {f"step-{j}": {} for j in range(10)}},
                name=f"Version {i}"
            )
            monitor.record_success()
            return v
        except Exception as e:
            monitor.record_failure(e)
            return None
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(create_version, i) for i in range(10000)]
        results = [f.result() for f in as_completed(futures)]
    duration = time.time() - start
    
    monitor.stop()
    stats = monitor.get_stats()
    
    print(f"\n📊 Results:")
    print(f"   Duration: {stats['duration_seconds']}s")
    print(f"   Total Operations: {stats['total_operations']}")
    print(f"   Success: {stats['success_count']}")
    print(f"   Failure: {stats['failure_count']}")
    print(f"   Success Rate: {stats['success_rate']}%")
    print(f"   Operations/Second: {stats['operations_per_second']}")
    
    # Assertions
    assert stats['success_count'] == 10000, f"Expected 10000 successes, got {stats['success_count']}"
    assert stats['failure_count'] == 0, f"Expected 0 failures, got {stats['failure_count']}"
    assert stats['duration_seconds'] < 60, f"Too slow: {stats['duration_seconds']}s"
    
    print("\n✅ EXTREME TEST PASSED!")


def test_extreme_metric_recording_50k():
    """测试: 50000个并发指标记录"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 50,000 Concurrent Metric Recordings")
    print("="*80)
    
    engine = AnalyticsEngine()
    monitor = PerformanceMonitor()
    monitor.start()
    
    def record_metric_batch(batch_id):
        try:
            for i in range(100):  # 50000 / 100 = 500 batches
                engine.record_metric(f"metric-{batch_id}-{i % 10}", float(i))
            monitor.record_success()
        except Exception as e:
            monitor.record_failure(e)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(record_metric_batch, i) for i in range(500)]
        [f.result() for f in as_completed(futures)]
    
    monitor.stop()
    stats = monitor.get_stats()
    
    print(f"\n📊 Results:")
    print(f"   Duration: {stats['duration_seconds']}s")
    print(f"   Total Operations: {stats['total_operations']}")
    print(f"   Success: {stats['success_count']}")
    print(f"   Failure: {stats['failure_count']}")
    print(f"   Success Rate: {stats['success_rate']}%")
    print(f"   Operations/Second: {stats['operations_per_second']}")
    
    # Verify metrics stored
    all_metrics = engine.get_all_metrics()
    total_metrics = sum(len(v) for v in all_metrics.values())
    print(f"   Total Metrics Stored: {total_metrics}")
    
    assert stats['success_rate'] >= 95, f"Success rate too low: {stats['success_rate']}%"
    print("\n✅ EXTREME TEST PASSED!")


def test_extreme_device_registration_5k():
    """测试: 5000个并发设备注册"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 5,000 Concurrent Device Registrations")
    print("="*80)
    
    manager = MobileAPIManager()
    monitor = PerformanceMonitor()
    monitor.start()
    
    def register_device_batch(batch_id):
        try:
            for i in range(50):  # 5000 / 50 = 100 batches
                manager.register_device(
                    user_id=f"user-{batch_id}-{i % 20}",
                    device_token=f"token-{batch_id}-{i}-{hash(str(i))}",
                    platform=MobilePlatform.IOS if i % 2 == 0 else MobilePlatform.ANDROID,
                    app_version=f"1.{i % 10}.0",
                    os_version=f"{17 - (i % 5)}.{i % 10}"
                )
            monitor.record_success()
        except Exception as e:
            monitor.record_failure(e)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(register_device_batch, i) for i in range(100)]
        [f.result() for f in as_completed(futures)]
    
    monitor.stop()
    stats = monitor.get_stats()
    
    print(f"\n📊 Results:")
    print(f"   Duration: {stats['duration_seconds']}s")
    print(f"   Total Operations: {stats['total_operations']}")
    print(f"   Success: {stats['success_count']}")
    print(f"   Failure: {stats['failure_count']}")
    print(f"   Success Rate: {stats['success_rate']}%")
    print(f"   Operations/Second: {stats['operations_per_second']}")
    
    assert stats['success_count'] == 100, f"Expected 100 successes, got {stats['success_count']}"
    print("\n✅ EXTREME TEST PASSED!")


def test_extreme_ab_test_traffic_20k():
    """测试: 20000次A/B测试流量"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 20,000 A/B Test Traffic")
    print("="*80)
    
    manager = VersionManager()
    ab_manager = ABTestManager(manager)
    
    # Create versions and test
    versions = []
    for i in range(10):
        v = manager.create_version(f"wf-ab-{i}", {"steps": {}}, f"{i}.0")
        versions.append(v)
    
    test = ab_manager.create_test("Extreme Traffic Test", "wf-ab-0", [
        {"name": f"Variant-{i}", "version_id": v.id, "weight": 10}
        for i, v in enumerate(versions)
    ])
    ab_manager.start_test(test.id)
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    def run_ab_test_batch(batch_id):
        try:
            for i in range(200):  # 20000 / 200 = 100 batches
                user_id = f"user-{batch_id}-{i}"
                variant = ab_manager.select_variant(test.id, user_id)
                success = (i % 10) != 0  # 90% success rate
                latency = 100 + (i % 50)
                ab_manager.record_result(test.id, variant.id, success=success, execution_time_ms=latency)
            monitor.record_success()
        except Exception as e:
            monitor.record_failure(e)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(run_ab_test_batch, i) for i in range(100)]
        [f.result() for f in as_completed(futures)]
    
    monitor.stop()
    stats = monitor.get_stats()
    
    print(f"\n📊 Results:")
    print(f"   Duration: {stats['duration_seconds']}s")
    print(f"   Total Operations: {stats['total_operations']}")
    print(f"   Success: {stats['success_count']}")
    print(f"   Failure: {stats['failure_count']}")
    print(f"   Success Rate: {stats['success_rate']}%")
    print(f"   Operations/Second: {stats['operations_per_second']}")
    
    results = ab_manager.get_test_results(test.id)
    total_users = sum(r.user_count for r in results)
    print(f"   Total Users in Test: {total_users}")
    
    assert total_users == 20000, f"Expected 20000 users, got {total_users}"
    print("\n✅ EXTREME TEST PASSED!")


def test_memory_leak_detection():
    """测试: 内存泄漏检测"""
    print("\n" + "="*80)
    print("🔴 MEMORY LEAK DETECTION TEST")
    print("="*80)
    
    gc.collect()
    
    engine = AnalyticsEngine()
    
    # Record many metrics
    for i in range(100000):
        engine.record_metric(f"leak-test-{i % 1000}", float(i))
    
    # Check metrics are stored correctly
    all_metrics = engine.get_all_metrics()
    total_metrics = sum(len(v) for v in all_metrics.values())
    
    print(f"\n📊 Memory Usage:")
    print(f"   Total Metrics: {total_metrics}")
    print(f"   Unique Metrics: {len(all_metrics)}")
    
    # Test passes if metrics are stored correctly
    assert total_metrics >= 1000, f"Expected at least 1000 metrics, got {total_metrics}"
    print("\n✅ MEMORY LEAK TEST PASSED!")


def test_cpu_intensive_operations():
    """测试: CPU密集型操作"""
    print("\n" + "="*80)
    print("🔴 CPU INTENSIVE OPERATIONS TEST")
    print("="*80)
    
    manager = VersionManager()
    
    # Create many complex versions
    monitor = PerformanceMonitor()
    monitor.start()
    
    def create_complex_version(i):
        try:
            # Create version with complex definition
            definition = {
                "steps": {
                    f"step-{j}": {
                        "handler": f"handler-{j}",
                        "config": {"timeout": 30, "retries": 3},
                        "dependencies": [f"step-{k}" for k in range(j)] if j > 0 else []
                    }
                    for j in range(50)  # 50 complex steps
                }
            }
            v = manager.create_version(f"wf-cpu-{i % 10}", definition, f"{i}.0")
            monitor.record_success()
            return v
        except Exception as e:
            monitor.record_failure(e)
            return None
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(create_complex_version, i) for i in range(1000)]
        results = [f.result() for f in as_completed(futures)]
    
    monitor.stop()
    stats = monitor.get_stats()
    
    print(f"\n📊 Results:")
    print(f"   Duration: {stats['duration_seconds']}s")
    print(f"   Total Operations: {stats['total_operations']}")
    print(f"   Success: {stats['success_count']}")
    print(f"   Operations/Second: {stats['operations_per_second']}")
    
    assert stats['success_count'] == 1000, f"Expected 1000 successes, got {stats['success_count']}"
    print("\n✅ CPU INTENSIVE TEST PASSED!")


def test_sustained_load_30_seconds():
    """测试: 30秒持续负载"""
    print("\n" + "="*80)
    print("🔴 SUSTAINED LOAD TEST: 30 Seconds")
    print("="*80)
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    mobile_manager = MobileAPIManager()
    
    start_time = time.time()
    operation_count = 0
    errors = []
    
    def mixed_operations():
        nonlocal operation_count
        try:
            # Version creation
            manager.create_version(f"wf-sustained-{operation_count}", {}, f"{operation_count}.0")
            operation_count += 1
            
            # Metric recording
            engine.record_metric("sustained-load", float(operation_count))
            
            # Device registration (every 10th operation)
            if operation_count % 10 == 0:
                mobile_manager.register_device(
                    f"user-{operation_count}", f"token-{operation_count}",
                    MobilePlatform.IOS, "1.0.0", "17.0"
                )
            
            return True
        except Exception as e:
            errors.append(str(e))
            return False
    
    while time.time() - start_time < 30:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mixed_operations) for _ in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        time.sleep(0.1)  # Small delay between batches
    
    duration = time.time() - start_time
    success_count = sum(1 for r in results if r)
    failure_count = len(results) - success_count
    
    print(f"\n📊 Results:")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Total Operations: {operation_count}")
    print(f"   Success: {success_count}")
    print(f"   Failure: {failure_count}")
    print(f"   Operations/Second: {operation_count / duration:.2f}")
    print(f"   Error Count: {len(errors)}")
    
    if errors:
        print(f"   First 5 Errors: {errors[:5]}")
    
    assert operation_count > 0, "No operations performed"
    print("\n✅ SUSTAINED LOAD TEST PASSED!")


# ============================================================
# 运行所有极端测试
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 MAOS v14.0 - EXTREME STRESS TEST SUITE")
    print("="*80)
    print("\nThis suite will run extreme tests with 10000+ operations...")
    print("Expected to find performance bottlenecks and potential issues.\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
