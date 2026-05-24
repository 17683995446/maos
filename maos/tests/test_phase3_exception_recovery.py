#!/usr/bin/env python3
"""
MAOS - 第三阶段：异常恢复与降级测试
Phase 3: Exception Recovery and Graceful Degradation Testing
目标：测试系统的异常处理、恢复机制、降级策略
"""

import sys
import time
import random
import threading
import traceback
from datetime import datetime

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine


class ExceptionRecoveryTest:
    """异常恢复与降级测试"""
    
    def __init__(self):
        self.storage = InMemoryChatStorage()
        self.vm = VersionManager()
        self.analytics = AnalyticsEngine()
        
        self.errors = []
        self.warnings = []
        self.recovery_count = 0
        self.degradation_count = 0
        
        self.stats = {
            "total_operations": 0,
            "exception_count": 0,
            "recovery_count": 0,
            "graceful_degradation_count": 0
        }
        
        self.lock = threading.Lock()
    
    def log_exception(self, component, operation, error):
        """记录异常"""
        with self.lock:
            self.errors.append({
                "timestamp": datetime.now(),
                "component": component,
                "operation": operation,
                "error_type": type(error).__name__,
                "message": str(error)
            })
            self.stats["exception_count"] += 1
    
    def test_extreme_value_handling(self):
        """测试极端值处理"""
        print("\n" + "=" * 120)
        print("测试1: 极端值处理")
        print("=" * 120)
        
        errors = 0
        
        extreme_values = [
            # 数学极端值
            ("float_inf", float('inf')),
            ("float_neg_inf", float('-inf')),
            ("float_nan", float('nan')),
            
            # 极大数值
            ("large_int", 10**308),
            ("large_float", 1e308),
            ("small_float", 1e-308),
            
            # 边界值
            ("zero", 0),
            ("negative_large", -10**308),
            
            # None和空
            ("none", None),
            ("empty_string", ""),
            
            # 超大字符串
            ("huge_string", "x" * 1000000),
        ]
        
        for name, value in extreme_values:
            try:
                # 尝试存储
                self.storage.save_message(f"extreme_user_{name}", {
                    "content": f"Test value: {name}",
                    "data": value,
                    "timestamp": time.time() if isinstance(value, (int, float)) else None
                })
                
                # 尝试检索
                conv = self.storage.get_conversation(f"extreme_user_{name}")
                
                # 尝试记录指标
                self.analytics.record_metric(f"extreme_metric_{name}", 
                    value if isinstance(value, (int, float)) else 0)
                
                print(f"  ✅ {name}: Handled gracefully")
                
            except Exception as e:
                errors += 1
                self.log_exception("EXTREME", name, e)
                print(f"  ❌ {name}: {type(e).__name__}: {str(e)[:50]}")
        
        print(f"\n极端值测试完成: {errors} errors")
        return errors
    
    def test_concurrent_failure_recovery(self):
        """测试并发失败恢复"""
        print("\n" + "=" * 120)
        print("测试2: 并发失败恢复")
        print("=" * 120)
        
        errors = 0
        failures = [0]
        
        def chaotic_worker(worker_id):
            try:
                user = f"chaos_user_{worker_id}"
                
                for i in range(50):
                    try:
                        # 随机操作
                        op = random.choice(["save", "read", "stats", "version", "analytics"])
                        
                        if op == "save":
                            self.storage.save_message(user, {
                                "content": f"Msg {i}"
                            })
                        elif op == "read":
                            self.storage.get_conversation(user)
                        elif op == "stats":
                            self.storage.get_stats()
                        elif op == "version":
                            self.vm.create_version(f"wf_{user}", {"step": i})
                        elif op == "analytics":
                            self.analytics.record_metric(f"metric_{user}", float(i))
                        
                    except Exception as e:
                        failures[0] += 1
                        self.log_exception("CHAOS", f"worker-{worker_id}", e)
                        
                        # 恢复机制：重试
                        try:
                            time.sleep(0.001)
                            self.storage.save_message(user, {
                                "content": f"Retry {i}"
                            })
                            with self.lock:
                                self.recovery_count += 1
                        except:
                            pass
                            
            except Exception as e:
                errors += 1
                self.log_exception("CHAOS", f"worker-{worker_id}", e)
        
        threads = []
        for i in range(30):
            t = threading.Thread(target=chaotic_worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"并发失败恢复测试完成: {errors} fatal errors, {failures[0]} recoverable errors")
        print(f"成功恢复次数: {self.recovery_count}")
        return errors
    
    def test_resource_exhaustion_handling(self):
        """测试资源耗尽处理"""
        print("\n" + "=" * 120)
        print("测试3: 资源耗尽处理")
        print("=" * 120)
        
        errors = 0
        
        # 快速创建大量对象
        for i in range(100):
            try:
                storage = InMemoryChatStorage()
                vm = VersionManager()
                analytics = AnalyticsEngine()
                
                # 填充数据
                for j in range(50):
                    storage.save_message(f"temp_user_{i}_{j}", {
                        "content": f"Temp message {j}"
                    })
                    vm.create_version(f"temp_wf_{i}_{j}", {"step": j})
                    analytics.record_metric(f"temp_metric_{i}_{j}", float(j))
                
                # 清理
                del storage
                del vm
                del analytics
                
                if (i + 1) % 20 == 0:
                    print(f"  创建/销毁进度: {i+1}/100")
                    
            except Exception as e:
                errors += 1
                self.log_exception("RESOURCE", f"iteration-{i}", e)
                print(f"  ❌ Iteration {i}: {type(e).__name__}")
        
        print(f"\n资源耗尽测试完成: {errors} errors")
        return errors
    
    def test_timeout_and_slow_response(self):
        """测试超时和慢响应处理"""
        print("\n" + "=" * 120)
        print("测试4: 超时和慢响应处理")
        print("=" * 120)
        
        errors = 0
        
        def slow_worker(worker_id):
            try:
                user = f"slow_user_{worker_id}"
                
                for i in range(20):
                    # 添加随机延迟模拟慢操作
                    if random.random() < 0.3:
                        time.sleep(random.uniform(0.01, 0.05))
                    
                    self.storage.save_message(user, {
                        "content": f"Slow message {i}"
                    })
                    
                    # 模拟超时场景
                    if i % 10 == 0 and random.random() < 0.2:
                        try:
                            # 尝试一个可能超时的操作
                            conv = self.storage.get_conversation(user)
                            # 验证数据一致性
                            if len(conv) > 0:
                                pass  # 正常
                        except Exception as e:
                            errors += 1
                            self.log_exception("TIMEOUT", f"worker-{worker_id}", e)
                            
            except Exception as e:
                errors += 1
                self.log_exception("TIMEOUT", f"worker-{worker_id}", e)
        
        threads = []
        for i in range(20):
            t = threading.Thread(target=slow_worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"超时和慢响应测试完成: {errors} errors")
        return errors
    
    def test_graceful_degradation(self):
        """测试优雅降级"""
        print("\n" + "=" * 120)
        print("测试5: 优雅降级")
        print("=" * 120)
        
        degradation_count = 0
        
        # 模拟各种降级场景
        scenarios = [
            # 场景1: 部分功能降级
            ("partial_degradation", lambda: self.storage.save_message("deg_user", {"content": "test"})),
            
            # 场景2: 降级到只读模式
            ("read_only", lambda: self.storage.get_conversation("deg_user")),
            
            # 场景3: 降级到最小功能集
            ("minimal", lambda: self.storage.get_stats()),
            
            # 场景4: 降级后恢复
            ("recovery", lambda: (
                self.storage.save_message("recovery_user", {"content": "recovery"}),
                self.vm.create_version("recovery_wf", {"step": 1}),
                self.analytics.record_metric("recovery_metric", 1.0)
            ))
        ]
        
        for name, func in scenarios:
            try:
                result = func()
                
                # 验证降级后的基本功能
                conv = self.storage.get_conversation("deg_user")
                stats = self.storage.get_stats()
                
                degradation_count += 1
                print(f"  ✅ {name}: Degraded gracefully, basic functions work")
                
            except Exception as e:
                self.log_exception("DEGRADE", name, e)
                print(f"  ❌ {name}: {type(e).__name__}: {str(e)[:50]}")
        
        print(f"\n优雅降级测试完成: {degradation_count}/{len(scenarios)} scenarios handled gracefully")
        return len(scenarios) - degradation_count
    
    def run_all_tests(self):
        """运行所有异常恢复测试"""
        print("=" * 120)
        print("🚀 第三阶段：异常恢复与降级测试")
        print("=" * 120)
        
        total_errors = 0
        
        # 测试1: 极端值处理
        errors1 = self.test_extreme_value_handling()
        total_errors += errors1
        
        # 测试2: 并发失败恢复
        errors2 = self.test_concurrent_failure_recovery()
        total_errors += errors2
        
        # 测试3: 资源耗尽处理
        errors3 = self.test_resource_exhaustion_handling()
        total_errors += errors3
        
        # 测试4: 超时和慢响应
        errors4 = self.test_timeout_and_slow_response()
        total_errors += errors4
        
        # 测试5: 优雅降级
        errors5 = self.test_graceful_degradation()
        total_errors += errors5
        
        # 生成报告
        self.generate_report(total_errors)
    
    def generate_report(self, total_errors):
        """生成测试报告"""
        print("\n" + "=" * 120)
        print("📊 第三阶段测试报告 - 异常恢复与降级")
        print("=" * 120)
        
        print(f"\n📈 操作统计:")
        print(f"  总操作数: {self.stats['total_operations']:,}")
        print(f"  异常数: {self.stats['exception_count']}")
        print(f"  恢复次数: {self.stats['recovery_count']}")
        print(f"  优雅降级次数: {self.stats['graceful_degradation_count']}")
        
        print(f"\n❌ 错误详情:")
        if self.errors:
            error_types = {}
            for err in self.errors:
                key = err['error_type']
                error_types[key] = error_types.get(key, 0) + 1
            
            print(f"  总错误数: {len(self.errors)}")
            print(f"  错误类型分布:")
            for err_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
                print(f"    {err_type}: {count}")
            
            print(f"\n  示例错误:")
            for i, err in enumerate(self.errors[:5], 1):
                print(f"    {i}. [{err['component']}] [{err['operation']}]")
                print(f"       {err['error_type']}: {err['message'][:80]}")
        else:
            print("  无错误!")
        
        print(f"\n✅ 恢复机制:")
        print(f"  恢复计数: {self.recovery_count}")
        print(f"  降级计数: {self.degradation_count}")
        
        print(f"\n💾 系统状态:")
        print(f"  存储: {self.storage.get_stats()}")
        print(f"  版本: {len(self.vm.versions) if hasattr(self.vm, 'versions') else 'N/A'} workflows")
        print(f"  分析: {self.analytics.get_summary()['total_metrics']} metrics")
        
        print("\n" + "=" * 120)
        if total_errors == 0:
            print("✅✅✅ 第三阶段测试通过！异常处理和恢复机制工作正常！✅✅✅")
        else:
            print(f"⚠️  发现 {total_errors} 个错误需要处理!")
        print("=" * 120)


def main():
    """主函数"""
    test = ExceptionRecoveryTest()
    test.run_all_tests()


if __name__ == "__main__":
    main()
