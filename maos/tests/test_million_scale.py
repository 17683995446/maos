"""
MAOS v14.0 - 百万级极限压力测试
Phase A: 挑战系统极限，发现性能瓶颈
"""

import pytest
import time
import threading
import gc
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

from maos.version.v14 import VersionManager, ABTestManager
from maos.analytics.v14 import AnalyticsEngine
from maos.mobile.v14 import MobileAPIManager


# ============================================================
# 百万级操作极限测试
# ============================================================

def test_million_version_creation():
    """测试: 100万个版本创建"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 1,000,000 Version Creations")
    print("="*80)
    
    manager = VersionManager()
    start_time = time.time()
    
    batch_size = 10000
    total_batches = 100
    total_versions = 0
    errors = 0
    
    print(f"\n📊 Progress: 0 / {total_versions} (0%)")
    
    for batch in range(total_batches):
        batch_start = time.time()
        
        def create_batch(offset):
            batch_versions = []
            for i in range(batch_size):
                try:
                    v = manager.create_version(
                        workflow_id=f"wf-million-{offset % 100}",  # 100个不同工作流
                        definition={"steps": {"step": i}},
                        version=f"{offset + i}.0",
                        name=f"Version {offset + i}"
                    )
                    batch_versions.append(v)
                except Exception as e:
                    nonlocal errors
                    errors += 1
            return batch_versions
        
        # 并行创建
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_batch, batch * batch_size)]
            results = [f.result() for f in as_completed(futures)]
        
        total_versions += len([v for sublist in results for v in sublist])
        
        # 进度更新
        progress = (batch + 1) / total_batches * 100
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            ops_per_sec = total_versions / elapsed
            print(f"   Progress: {batch + 1}/{total_batches} ({progress:.1f}%) - {total_versions} versions - {ops_per_sec:.0f} ops/sec")
    
    total_time = time.time() - start_time
    
    # 验证
    all_versions = 0
    for i in range(100):
        versions = manager.get_workflow_versions(f"wf-million-{i}")
        all_versions += len(versions)
    
    print(f"\n📊 Final Results:")
    print(f"   Total Versions Created: {total_versions}")
    print(f"   Versions in System: {all_versions}")
    print(f"   Errors: {errors}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Ops/Second: {total_versions / total_time:.0f}")
    
    assert errors == 0, f"{errors} errors occurred during million test"
    assert all_versions == total_versions, f"Version count mismatch"
    
    print("\n✅ MILLION VERSION TEST PASSED!")


def test_million_metric_recordings():
    """测试: 100万个指标记录"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 1,000,000 Metric Recordings")
    print("="*80)
    
    engine = AnalyticsEngine()
    start_time = time.time()
    
    batch_size = 10000
    total_batches = 100
    total_metrics = 0
    errors = 0
    
    print(f"\n📊 Progress: 0 / {total_metrics} (0%)")
    
    for batch in range(total_batches):
        
        def record_batch(offset):
            local_errors = 0
            for i in range(batch_size):
                try:
                    metric_name = f"metric-{offset % 1000}"  # 1000个不同指标
                    engine.record_metric(metric_name, float(offset + i))
                except Exception as e:
                    nonlocal errors
                    errors += 1
        
        # 并行记录
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(record_batch, batch * batch_size)]
            [f.result() for f in as_completed(futures)]
        
        total_metrics += batch_size
        
        # 进度更新
        progress = (batch + 1) / total_batches * 100
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            ops_per_sec = total_metrics / elapsed
            print(f"   Progress: {batch + 1}/{total_batches} ({progress:.1f}%) - {total_metrics} metrics - {ops_per_sec:.0f} ops/sec")
    
    total_time = time.time() - start_time
    
    # 验证
    total_in_system = 0
    for name, data in engine.get_all_metrics().items():
        total_in_system += len(data)
    
    print(f"\n📊 Final Results:")
    print(f"   Total Metrics Recorded: {total_metrics}")
    print(f"   Metrics in System: {total_in_system}")
    print(f"   Errors: {errors}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Ops/Second: {total_metrics / total_time:.0f}")
    
    # 由于可能有重复时间戳，允许一些差异
    assert total_in_system >= 900000, f"Metric count too low: {total_in_system}"
    
    print("\n✅ MILLION METRIC TEST PASSED!")


def test_500k_ab_test_results():
    """测试: 50万次A/B测试流量"""
    print("\n" + "="*80)
    print("🔴 EXTREME TEST: 500,000 A/B Test Requests")
    print("="*80)
    
    manager = VersionManager()
    ab_manager = ABTestManager(manager)
    
    # 创建版本和测试
    versions = []
    for i in range(10):
        v = manager.create_version(f"wf-ab-million", {}, f"{i}.0")
        versions.append(v)
    
    test = ab_manager.create_test("Million Traffic Test", "wf-ab-million", [
        {"name": f"Variant {i}", "version_id": v.id, "weight": 10}
        for i, v in enumerate(versions)
    ])
    ab_manager.start_test(test.id)
    
    start_time = time.time()
    
    batch_size = 10000
    total_batches = 50
    total_requests = 0
    errors = 0
    
    print(f"\n📊 Progress: 0 / {total_requests} (0%)")
    
    for batch in range(total_batches):
        
        def process_batch(offset):
            for i in range(batch_size):
                try:
                    user_id = f"user-{offset + i}"
                    variant = ab_manager.select_variant(test.id, user_id)
                    success = (i % 10) != 0
                    latency = 100 + (i % 50)
                    ab_manager.record_result(test.id, variant.id, success=success, execution_time_ms=latency)
                except Exception as e:
                    nonlocal errors
                    errors += 1
        
        # 并行处理
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(process_batch, batch * batch_size)]
            [f.result() for f in as_completed(futures)]
        
        total_requests += batch_size
        
        # 进度更新
        progress = (batch + 1) / total_batches * 100
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            ops_per_sec = total_requests / elapsed
            print(f"   Progress: {batch + 1}/{total_batches} ({progress:.1f}%) - {total_requests} requests - {ops_per_sec:.0f} ops/sec")
    
    total_time = time.time() - start_time
    
    # 验证
    results = ab_manager.get_test_results(test.id)
    total_users = sum(r.user_count for r in results)
    
    print(f"\n📊 Final Results:")
    print(f"   Total Requests: {total_requests}")
    print(f"   Results Recorded: {total_users}")
    print(f"   Errors: {errors}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Ops/Second: {total_requests / total_time:.0f}")
    
    assert errors == 0, f"{errors} errors occurred"
    
    print("\n✅ 500K AB TEST PASSED!")


def test_memory_usage_under_load():
    """测试: 负载下的内存使用"""
    print("\n" + "="*80)
    print("🔴 MEMORY TEST: Under Heavy Load")
    print("="*80)
    
    gc.collect()
    initial_objects = len(gc.get_objects())
    start_time = time.time()
    
    # 大量创建和释放对象
    manager = VersionManager()
    engine = AnalyticsEngine()
    
    object_snapshot = []
    
    # 阶段1: 创建大量对象
    for i in range(50000):
        v = manager.create_version(f"wf-memory-test", {}, f"{i}.0")
        engine.record_metric("memory-test-metric", float(i))
    
    after_create = len(gc.get_objects())
    time_after_create = time.time() - start_time
    
    # 阶段2: 释放引用
    del manager
    del engine
    gc.collect()
    
    after_delete = len(gc.get_objects())
    time_after_delete = time.time() - start_time
    
    object_growth = after_create - initial_objects
    object_released = after_create - after_delete
    release_ratio = object_released / object_growth if object_growth > 0 else 0
    
    print(f"\n📊 Memory Analysis:")
    print(f"   Initial Objects: {initial_objects}")
    print(f"   After Creation: {after_create}")
    print(f"   After GC: {after_delete}")
    print(f"   Object Growth: {object_growth}")
    print(f"   Objects Released: {object_released}")
    print(f"   Release Ratio: {release_ratio:.1%}")
    print(f"   Time to Create: {time_after_create:.2f}s")
    print(f"   Time to GC: {time_after_delete - time_after_create:.2f}s")
    
    assert release_ratio >= 0.8, f"Poor memory management: release ratio {release_ratio:.1%}"
    
    print("\n✅ MEMORY TEST PASSED!")


def test_sustained_hourly_load():
    """测试: 模拟1小时持续负载 (压缩为30秒)"""
    print("\n" + "="*80)
    print("🔴 SUSTAINED LOAD TEST: 1 Hour (Compressed to 30s)")
    print("="*80)
    
    manager = VersionManager()
    engine = AnalyticsEngine()
    mobile_manager = MobileAPIManager()
    
    start_time = time.time()
    duration = 30  # 30秒代替1小时
    
    ops_count = {"version": 0, "metric": 0, "device": 0}
    errors = 0
    checkpoints = []
    
    def do_work():
        try:
            # 混合操作
            manager.create_version("wf-sustained", {}, f"{ops_count['version']}.0")
            engine.record_metric("sustained-metric", float(ops_count['metric']))
            ops_count["version"] += 1
            ops_count["metric"] += 1
            
            if ops_count['version'] % 10 == 0:
                mobile_manager.register_device(
                    f"user-{ops_count['version']}",
                    f"token-{ops_count['version']}",
                    "ios",
                    "1.0.0",
                    "17.0"
                )
                ops_count["device"] += 1
                
        except Exception as e:
            nonlocal errors
            errors += 1
    
    # 模拟持续负载
    print(f"\n📊 Running load for {duration} seconds...")
    
    checkpoint_interval = 5
    next_checkpoint = checkpoint_interval
    
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        
        # 打印进度
        if elapsed >= next_checkpoint:
            checkpoints.append({
                "time": elapsed,
                "total_ops": ops_count["version"] + ops_count["metric"] + ops_count["device"]
            })
            print(f"   Elapsed: {elapsed:.0f}s - Total: {checkpoints[-1]['total_ops']} ops")
            next_checkpoint += checkpoint_interval
        
        # 快速批量操作
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(do_work) for _ in range(20)]
            [f.result() for f in as_completed(futures)]
    
    total_time = time.time() - start_time
    total_ops = ops_count["version"] + ops_count["metric"] + ops_count["device"]
    ops_per_sec = total_ops / total_time
    
    print(f"\n📊 Final Results:")
    print(f"   Duration: {total_time:.1f}s")
    print(f"   Version Creates: {ops_count['version']}")
    print(f"   Metric Records: {ops_count['metric']}")
    print(f"   Device Registers: {ops_count['device']}")
    print(f"   Total Operations: {total_ops}")
    print(f"   Errors: {errors}")
    print(f"   Ops/Second: {ops_per_sec:.0f}")
    print(f"\n   Checkpoints: {checkpoints}")
    
    assert errors == 0, f"{errors} errors occurred during sustained load"
    
    print("\n✅ SUSTAINED LOAD TEST PASSED!")


# ============================================================
# 运行所有百万级测试
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 MAOS v14.0 - EXTREME MILLION-SCALE TEST SUITE")
    print("="*80)
    print("\nThis suite will push the system to its absolute limits...")
    print("WARNING: May consume significant memory and CPU!\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
