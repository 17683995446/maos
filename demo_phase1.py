#!/usr/bin/env python3
"""
MAOS v6.0 - Phase 1: 性能优化演示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import asyncio


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


async def demo_cache():
    """演示缓存功能"""
    print_header("1. Cache System Demo")
    
    from maos.cache import get_cache_manager, LRUCache
    
    # 创建缓存管理器
    manager = get_cache_manager()
    
    # 创建测试缓存
    cache = manager.get_or_create_cache("test", max_size=100, ttl=10)
    
    # 基本操作
    print("\n📋 Basic Operations:")
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    print(f"   Set 3 keys, size: {len(cache)}")
    
    v1 = cache.get("key1")
    print(f"   Get key1: {v1}")
    
    v_missing = cache.get("nonexistent", default="default_value")
    print(f"   Get nonexistent: {v_missing}")
    
    # LRU功能
    print("\n📋 LRU Functionality:")
    
    # 访问key1（提升到最新）
    cache.get("key1")
    cache.get("key2")
    
    # 添加新键直到超过容量
    for i in range(10):
        cache.set(f"overflow_{i}", f"value_{i}")
    
    stats = cache.get_stats()
    print(f"   After overflow:")
    print(f"      Size: {stats['size']}")
    print(f"      Evictions: {stats['evictions']}")
    print(f"      Hit Rate: {stats['hit_rate']}")
    
    # 清理过期
    time.sleep(0.1)  # 等待一小段时间
    expired = cache.cleanup_expired()
    print(f"\n📋 Cleanup:")
    print(f"   Expired entries removed: {expired}")
    
    # 显示统计
    print("\n📊 Cache Statistics:")
    final_stats = cache.get_stats()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")


async def demo_performance_decorators():
    """演示性能装饰器"""
    print_header("2. Performance Decorators")
    
    from maos.performance import timed, get_all_performance_metrics, print_performance_summary
    
    # 使用timed装饰器
    @timed(log_duration=True, record_metrics=False)
    def slow_function():
        time.sleep(0.01)
        return "result"
    
    print("\n📋 Running decorated function 5 times...")
    
    for i in range(5):
        result = slow_function()
    
    print_performance_summary()


async def demo_optimized_task_manager():
    """演示优化后的任务管理器"""
    print_header("3. Optimized Task Manager")
    
    from maos.orchestration import TaskManager, TaskPriority
    import time
    
    manager = TaskManager()
    
    # 批量创建任务
    print("\n📋 Creating 1000 tasks...")
    start = time.perf_counter()
    
    for i in range(1000):
        manager.create_task(
            name=f"Task-{i}",
            requirements=["test"],
            priority=TaskPriority.NORMAL
        )
    
    duration = time.perf_counter() - start
    throughput = 1000 / duration
    
    print(f"   ✅ Created 1000 tasks in {duration:.4f}s")
    print(f"   📊 Throughput: {throughput:.2f} tasks/s")
    
    # 批量查询
    print("\n📋 Querying tasks...")
    start = time.perf_counter()
    
    for _ in range(100):
        pending = manager.get_pending_tasks()
        stats = manager.get_statistics()
    
    duration = time.perf_counter() - start
    throughput = 100 / duration
    
    print(f"   ✅ 100 query rounds in {duration:.4f}s")
    print(f"   📊 Throughput: {throughput:.2f} queries/s")
    
    # 清理
    manager.clear_all_tasks()
    print(f"\n   ✅ Cleared all tasks")


async def demo_cache_decorator():
    """演示缓存装饰器"""
    print_header("4. Cache Decorator Demo")
    
    from maos.cache import cached, get_cache_manager
    
    call_count = 0
    
    @cached(cache_name="demo", ttl=5)
    def expensive_computation(x: int) -> int:
        nonlocal call_count
        call_count += 1
        time.sleep(0.01)  # 模拟耗时操作
        return x * 2
    
    print("\n📋 Testing cache decorator:")
    
    # 第一次调用
    start = time.perf_counter()
    result1 = expensive_computation(10)
    time1 = time.perf_counter() - start
    print(f"   Call 1: result={result1}, time={time1*1000:.2f}ms, actual_calls={call_count}")
    
    # 第二次调用（应该使用缓存）
    start = time.perf_counter()
    result2 = expensive_computation(10)
    time2 = time.perf_counter() - start
    print(f"   Call 2: result={result2}, time={time2*1000:.2f}ms, actual_calls={call_count}")
    
    # 第三次调用（不同参数）
    start = time.perf_counter()
    result3 = expensive_computation(20)
    time3 = time.perf_counter() - start
    print(f"   Call 3: result={result3}, time={time3*1000:.2f}ms, actual_calls={call_count}")
    
    # 第四次调用（参数1，缓存）
    start = time.perf_counter()
    result4 = expensive_computation(10)
    time4 = time.perf_counter() - start
    print(f"   Call 4: result={result4}, time={time4*1000:.2f}ms, actual_calls={call_count}")
    
    print(f"\n   📊 Cache efficiency: 3 cache hits out of 4 calls")


async def main():
    """主函数"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║       MAOS v6.0 - Phase 1: Performance Optimization Demo              ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    await demo_cache()
    await demo_performance_decorators()
    await demo_optimized_task_manager()
    await demo_cache_decorator()
    
    print("\n" + "=" * 80)
    print("  🎉 Phase 1 Performance Demo Complete!")
    print("=" * 80)
    print("\n📚 Next Steps:")
    print("   - Run benchmarks: python benchmark.py")
    print("   - Explore maos/cache.py for caching implementation")
    print("   - Optimize specific components as needed")
    print()


if __name__ == "__main__":
    asyncio.run(main())
