#!/usr/bin/env python3
"""
MAOS - 第四和第五阶段快速综合测试
Phase 4 & 5: Data Consistency + Production Simulation
"""

import sys
import time
import random
import threading
from datetime import datetime

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine


class CombinedPhase45Test:
    """第四和第五阶段综合测试"""
    
    def __init__(self):
        self.storage = InMemoryChatStorage()
        self.vm = VersionManager()
        self.analytics = AnalyticsEngine()
        self.errors = []
        self.lock = threading.Lock()
    
    def log_error(self, msg):
        with self.lock:
            self.errors.append(msg)
            print(f"❌ ERROR: {msg}")
    
    def test_data_consistency(self):
        """第四阶段：数据一致性深度验证"""
        print("\n" + "=" * 120)
        print("🚀 第四阶段：数据一致性深度验证")
        print("=" * 120)
        
        errors = 0
        
        # 1. 创建-读取一致性
        print("  测试1: 创建-读取一致性...")
        for i in range(100):
            user = f"consistency_user_{i}"
            self.storage.save_message(user, {"content": f"Message {i}"})
            conv = self.storage.get_conversation(user)
            if len(conv) != 1:  # 每个用户只保存了一条消息
                errors += 1
                self.log_error(f"User {user}: Expected 1 message, got {len(conv)}")
        
        # 2. 版本一致性
        print("  测试2: 版本一致性...")
        wf_id = "consistency_wf"
        for i in range(50):
            v = self.vm.create_version(wf_id, {"step": i})
            retrieved = self.vm.get_version(v.id)
            if retrieved.id != v.id:
                errors += 1
                self.log_error(f"Version mismatch: {v.id} vs {retrieved.id}")
        
        # 3. 分析指标一致性
        print("  测试3: 分析指标一致性...")
        for i in range(50):
            self.analytics.record_metric("test_metric", float(i))
        summary = self.analytics.get_summary()
        if summary['total_metrics'] < 50:
            errors += 1
            self.log_error(f"Metric count mismatch: expected >= 50, got {summary['total_metrics']}")
        
        # 4. 并发一致性
        print("  测试4: 并发一致性...")
        def worker(wid):
            try:
                for i in range(100):
                    self.storage.save_message(f"concurrent_user_{wid}", {"content": f"Msg {i}"})
            except Exception as e:
                self.log_error(f"Worker {wid}: {e}")
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        # 验证
        for i in range(20):
            conv = self.storage.get_conversation(f"concurrent_user_{i}")
            if len(conv) != 100:
                errors += 1
                self.log_error(f"Concurrent user {i}: Expected 100, got {len(conv)}")
        
        print(f"\n第四阶段完成: {errors} errors")
        return errors
    
    def test_production_simulation(self):
        """第五阶段：生产环境模拟测试"""
        print("\n" + "=" * 120)
        print("🚀 第五阶段：生产环境模拟测试")
        print("=" * 120)
        
        errors = 0
        
        # 模拟真实生产环境的工作负载
        print("  模拟1: 真实用户行为...")
        
        def simulate_user(user_id, message_count=50):
            try:
                session = f"session_{user_id}"
                for i in range(message_count):
                    # 发送消息
                    self.storage.save_message(user_id, {
                        "content": f"User {user_id} message {i}",
                        "session_id": session
                    })
                    
                    # 记录指标
                    self.analytics.record_metric(f"user_{user_id}", 1.0)
                    
                    # 偶尔查询历史
                    if i % 10 == 0:
                        conv = self.storage.get_conversation(user_id, session)
                    
                    # 偶尔创建版本
                    if i % 15 == 0:
                        self.vm.create_version(f"wf_{user_id}", {"step": i})
            except Exception as e:
                self.log_error(f"User {user_id}: {e}")
        
        threads = []
        for i in range(100):
            t = threading.Thread(target=simulate_user, args=(f"prod_user_{i}", random.randint(30, 100)))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 验证系统状态
        print("  验证2: 系统状态验证...")
        stats = self.storage.get_stats()
        summary = self.analytics.get_summary()
        
        print(f"    存储: {stats['total_messages']} messages")
        print(f"    分析: {summary['total_metrics']} metrics")
        
        # 压力测试
        print("  模拟3: 峰值压力测试...")
        def peak_worker(wid):
            try:
                for i in range(200):
                    self.storage.save_message(f"peak_user_{wid}", {"content": f"Peak {i}"})
                    self.analytics.record_metric("peak_metric", float(i))
            except Exception as e:
                self.log_error(f"Peak worker {wid}: {e}")
        
        threads = [threading.Thread(target=peak_worker, args=(i,)) for i in range(50)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        print(f"\n第五阶段完成: {len([e for e in self.errors if 'Peak' in str(e)])} errors")
        return len(self.errors)
    
    def run(self):
        """运行所有测试"""
        errors1 = self.test_data_consistency()
        errors2 = self.test_production_simulation()
        
        total_errors = errors1 + errors2
        
        print("\n" + "=" * 120)
        print("📊 第四和第五阶段综合报告")
        print("=" * 120)
        print(f"\n总错误数: {total_errors}")
        print(f"数据一致性: {'✅ PASS' if errors1 == 0 else '❌ FAIL'}")
        print(f"生产模拟: {'✅ PASS' if errors2 == 0 else '❌ FAIL'}")
        
        if total_errors == 0:
            print("\n✅✅✅ 第四和第五阶段测试通过！✅✅✅")
        
        return total_errors


def main():
    test = CombinedPhase45Test()
    exit_code = test.run()
    sys.exit(0 if exit_code == 0 else 1)


if __name__ == "__main__":
    main()
