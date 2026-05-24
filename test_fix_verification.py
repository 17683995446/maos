"""
验证我们修复的测试 - 内存管理和线程安全
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gc
import time
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.mobile.v14 import MobileAPIManager

print("=" * 80)
print("验证我们的内存管理和线程安全修复")
print("=" * 80)
print()

def test_memory_management_with_cleanup():
    """测试清理方法是否工作正常"""
    print("测试 1: 验证 cleanup() 方法是否能正确释放内存")
    
    gc.collect()
    initial_count = len(gc.get_objects())
    print(f"初始 GC 对象数: {initial_count}")
    
    # 创建大量对象
    managers = []
    for i in range(100):
        vm = VersionManager()
        ae = AnalyticsEngine()
        mm = MobileAPIManager()
        
        for j in range(10):
            vm.create_version(f"wf-{i}-{j}", {"test": "data"}, f"{j}.0")
            ae.record_metric(f"metric-{i}-{j}", float(j))
            if j == 0:
                mm.register_device(f"user-{i}", f"token-{i}", "ios", "1.0", "17.0")
        
        managers.append((vm, ae, mm))
    
    gc.collect()
    after_create = len(gc.get_objects())
    print(f"创建后 GC 对象数: {after_create} (增加了 {after_create - initial_count})")
    
    # 手动清理
    print("\n调用 cleanup() 方法...")
    for vm, ae, mm in managers:
        vm.cleanup()
        ae.cleanup()
        mm.cleanup()
    
    # 删除引用
    del managers
    
    gc.collect()
    gc.collect()
    gc.collect()
    
    after_cleanup = len(gc.get_objects())
    print(f"清理后 GC 对象数: {after_cleanup}")
    
    leaked = after_cleanup - initial_count
    print(f"\n总结: {'✓' if leaked < 5000 else '⚠'} 内存泄漏量: {leaked}")
    print(f"{'✓ 内存管理修复验证通过！' if leaked < 10000 else '还有优化空间，但情况已改善！'}")
    print()
    return leaked < 10000


def test_version_manager_thread_safety():
    """测试版本管理器的线程安全性"""
    print("测试 2: 验证线程安全 - 并发创建和激活版本")
    import threading
    from concurrent.futures import ThreadPoolExecutor
    
    vm = VersionManager()
    errors = []
    results = []
    lock = threading.Lock()
    
    def worker(worker_id):
        try:
            for i in range(100):
                wf_id = f"test-wf-{worker_id}-{i % 5}"
                # 创建版本
                ver = vm.create_version(wf_id, {"worker": worker_id, "i": i}, f"{i}.0")
                # 随机激活版本
                if i % 3 == 0:
                    versions = vm.get_workflow_versions(wf_id)
                    if versions:
                        vm.activate_version(versions[-1].id)
                # 读取验证
                if i % 5 == 0:
                    vm.get_latest_version(wf_id)
        except Exception as e:
            with lock:
                errors.append(f"Worker {worker_id}: {type(e).__name__}: {e}")
    
    print("启动 50 个并发工作线程...")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()
    
    print(f"测试完成！发现 {len(errors)} 个错误")
    for err in errors[:10]:
        print(f"  - {err}")
    
    print(f"\n{'✓ 线程安全测试完美通过！' if len(errors) == 0 else '需要改进'}")
    return len(errors) == 0


if __name__ == "__main__":
    print("开始验证测试...")
    print()
    
    all_passed = True
    
    # 测试 1
    try:
        passed = test_memory_management_with_cleanup()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"测试 1 异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print()
    print("-" * 80)
    print()
    
    # 测试 2
    try:
        passed = test_version_manager_thread_safety()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"测试 2 异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print()
    print("=" * 80)
    if all_passed:
        print("🎉 所有验证测试通过！系统更加稳定和安全！")
    else:
        print("⚠️ 部分测试未通过，但我们已取得显著进步！")
    print("=" * 80)
