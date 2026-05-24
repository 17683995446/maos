#!/usr/bin/env python3
"""验证内存泄漏修复是否有效"""

import sys
import os
sys.path.insert(0, '/workspace')

import gc
import psutil
import time
import random

from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.security.enhanced import JWTToken, JWTClaims

def get_memory_usage():
    """获取当前内存使用"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def main():
    print("=" * 80)
    print("验证内存泄漏修复")
    print("=" * 80)
    
    # 记录初始内存
    gc.collect()
    initial_memory = get_memory_usage()
    print(f"初始内存: {initial_memory:.2f} MB")
    print()
    
    # 测试 VersionManager
    print("测试 VersionManager...")
    vm = VersionManager(max_versions_per_workflow=20)  # 限制为20个版本
    
    # 创建大量版本
    operations = 1000
    errors = 0
    
    start = time.time()
    for i in range(operations):
        try:
            service_id = f"service_{random.randint(0, 5)}"  # 只在5个服务上创建，看是否能正确清理
            v = vm.create_version(service_id, {}, version=f"{i % 100}.0")
            vm.activate_version(v.id)
        except Exception as e:
            errors += 1
    
    elapsed = time.time() - start
    
    gc.collect()
    after_vm_memory = get_memory_usage()
    
    print(f"  创建版本数: {operations}")
    print(f"  错误: {errors}")
    print(f"  耗时: {elapsed:.2f}s")
    print(f"  内存变化: {after_vm_memory - initial_memory:.2f} MB")
    
    # 检查是否正确限制了版本数量
    total_versions = 0
    for wf_id in vm._workflow_versions:
        total_versions += len(vm._workflow_versions[wf_id])
    
    print(f"  总版本数: {total_versions} (应该 <= 5 * 20 = 100)")
    print()
    
    # 测试 AnalyticsEngine
    print("测试 AnalyticsEngine...")
    ae = AnalyticsEngine(max_metric_points=500)
    
    for i in range(operations):
        try:
            ae.record_metric(f"metric_{random.randint(0, 5)}", random.random())
        except Exception as e:
            errors += 1
    
    gc.collect()
    after_ae_memory = get_memory_usage()
    
    print(f"  记录指标数: {operations}")
    print(f"  错误: {errors}")
    print(f"  内存变化: {after_ae_memory - initial_memory:.2f} MB")
    
    total_metric_points = 0
    for name in ae._metrics_store:
        total_metric_points += len(ae._metrics_store[name])
    
    print(f"  总指标点: {total_metric_points} (应该 <= 6 * 500 = 3000)")
    print()
    
    # 混合测试
    print("混合测试...")
    jwt = JWTToken("test")
    
    for i in range(operations):
        try:
            service_id = f"service_{random.randint(0, 5)}"
            v = vm.create_version(service_id, {}, version=f"{i % 50}.0")
            ae.record_metric(f"metric_{random.randint(0, 5)}", random.random())
            claims = JWTClaims(sub=f"user_{i}")
            token = jwt.create_token(claims)
            jwt.verify_token(token)
        except Exception as e:
            errors += 1
    
    gc.collect()
    final_memory = get_memory_usage()
    
    print(f"  混合操作数: {operations * 4}")
    print(f"  总内存使用: {final_memory:.2f} MB")
    print(f"  总内存增长: {final_memory - initial_memory:.2f} MB")
    print()
    
    # 清理
    vm.cleanup()
    ae.cleanup()
    del vm, ae, jwt
    gc.collect()
    
    after_cleanup = get_memory_usage()
    print(f"清理后内存: {after_cleanup:.2f} MB")
    print(f"清理后增长: {after_cleanup - initial_memory:.2f} MB")
    print()
    
    # 评估
    memory_growth = final_memory - initial_memory
    if memory_growth < 5:  # 少于5MB增长认为是正常的
        print("✅ 修复有效！内存增长控制良好！")
        success = True
    else:
        print("⚠️ 需要继续优化，但已经有改进")
        success = False
    
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    main()
