#!/usr/bin/env python3
"""
MAOS - 第一阶段：复杂业务流程深度测试
Phase 1: Complex Business Scenario Deep Testing
重点：嵌套调用链路、多组件深度交互、隐藏逻辑发现
"""

import sys
import time
import random
import threading
import gc
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import logging

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(threadName)-12s] %(levelname)-8s %(message)s'
)
logger = logging.getLogger(__name__)


class ComplexBusinessScenarioTest:
    """复杂业务场景测试"""
    
    def __init__(self):
        self.storage = InMemoryChatStorage()
        self.vm = VersionManager()
        self.analytics = AnalyticsEngine()
        
        self.errors = []
        self.warnings = []
        self.operation_log = deque(maxlen=5000)
        
        self.stats = {
            "total_operations": 0,
            "nested_operations": 0,
            "cross_component_calls": 0,
            "hidden_logic_triggers": 0,
            "error_count": 0,
            "start_time": None
        }
        
        self.lock = threading.Lock()
    
    def log_operation(self, component, operation, details="", level="INFO"):
        """记录操作（带详细日志）"""
        timestamp = datetime.now()
        with self.lock:
            self.operation_log.append({
                "timestamp": timestamp,
                "component": component,
                "operation": operation,
                "details": details,
                "level": level
            })
            self.stats["total_operations"] += 1
            
            log_msg = f"[{component}] [{operation}] {details}"
            if level == "ERROR":
                logger.error(log_msg)
            elif level == "WARNING":
                logger.warning(log_msg)
            else:
                logger.debug(log_msg)
    
    def log_error(self, component, operation, error, context=""):
        """记录错误"""
        with self.lock:
            self.errors.append({
                "timestamp": datetime.now(),
                "component": component,
                "operation": operation,
                "error_type": type(error).__name__,
                "message": str(error),
                "context": context,
                "traceback": traceback.format_exc()
            })
            self.stats["error_count"] += 1
            logger.error(f"[{component}] [{operation}] ERROR: {type(error).__name__}: {str(error)} | Context: {context}")
    
    # ========================================================
    # 场景1：嵌套调用链路测试
    # ========================================================
    
    def test_nested_call_chain_depth_5(self):
        """测试5层嵌套调用链路"""
        print("\n" + "=" * 120)
        print("场景1: 5层嵌套调用链路测试")
        print("=" * 120)
        
        errors = [0]
        
        def level_1(user_id, depth=1):
            """第1层：基础存储操作"""
            try:
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Starting level 1")
                
                # 调用第2层
                level_2(user_id, depth + 1)
                
                # 返回后记录
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Completed level 1")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("NESTED", f"Level-{depth}", e, f"User: {user_id}")
        
        def level_2(user_id, depth=2):
            """第2层：存储+版本"""
            try:
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Starting level 2")
                
                # 存储操作
                self.storage.save_message(user_id, {
                    "content": f"Level 2 message",
                    "session_id": f"session_{depth}"
                })
                
                # 调用第3层
                level_3(user_id, depth + 1)
                
                # 验证存储
                conv = self.storage.get_conversation(user_id)
                
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Completed level 2")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("NESTED", f"Level-{depth}", e, f"User: {user_id}")
        
        def level_3(user_id, depth=3):
            """第3层：版本管理+分析"""
            try:
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Starting level 3")
                
                # 版本创建
                version = self.vm.create_version(f"wf_{user_id}", {
                    "depth": depth,
                    "user": user_id
                })
                
                # 分析记录
                self.analytics.record_metric(f"user_{user_id}_level_{depth}", 1.0)
                
                # 调用第4层
                level_4(user_id, version.id, depth + 1)
                
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Completed level 3")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("NESTED", f"Level-{depth}", e, f"User: {user_id}")
        
        def level_4(user_id, version_id, depth=4):
            """第4层：深度存储查询"""
            try:
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Version: {version_id}, Starting level 4")
                
                # 批量存储
                for i in range(10):
                    self.storage.save_message(user_id, {
                        "content": f"Level 4 batch {i}",
                        "session_id": f"session_{depth}"
                    })
                
                # 查询
                conv = self.storage.get_conversation(user_id)
                
                # 调用第5层
                level_5(user_id, version_id, depth + 1)
                
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Completed level 4")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("NESTED", f"Level-{depth}", e, f"User: {user_id}")
        
        def level_5(user_id, version_id, depth=5):
            """第5层：最终验证"""
            try:
                self.log_operation("NESTED", f"Level-{depth}", f"User: {user_id}, Version: {version_id}, Starting level 5 (deepest)")
                
                # 最终验证所有操作
                conv = self.storage.get_conversation(user_id)
                versions = self.vm.list_versions(f"wf_{user_id}")
                summary = self.analytics.get_summary()
                
                # 记录完成
                self.log_operation("NESTED", f"Level-{depth}", 
                    f"User: {user_id}, Completed level 5. Conv: {len(conv)}, Versions: {len(versions)}, Metrics: {summary['total_metrics']}")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("NESTED", f"Level-{depth}", e, f"User: {user_id}")
        
        # 执行100次5层嵌套调用
        print("执行 100 次 5层嵌套调用...")
        for i in range(100):
            try:
                user_id = f"nested_user_{i}"
                level_1(user_id)
                
                if (i + 1) % 20 == 0:
                    print(f"  进度: {i + 1}/100")
                    
            except Exception as e:
                errors[0] += 1
                self.log_error("NESTED", "Main", e, f"User iteration {i}")
        
        print(f"完成! 错误数: {errors[0]}")
        return errors[0]
    
    # ========================================================
    # 场景2：多组件深度交互测试
    # ========================================================
    
    def test_cross_component_deep_interaction(self):
        """多组件深度交互测试"""
        print("\n" + "=" * 120)
        print("场景2: 多组件深度交互测试")
        print("=" * 120)
        
        errors = [0]
        
        def complex_workflow(workflow_id, user_id, iterations=10):
            """复杂工作流：存储→版本→分析→验证→存储→验证"""
            try:
                self.log_operation("CROSS", f"Workflow-{workflow_id}", f"User: {user_id}, Starting complex workflow")
                
                for i in range(iterations):
                    # 1. 创建版本
                    version = self.vm.create_version(
                        f"wf_{workflow_id}",
                        {
                            "iteration": i,
                            "user": user_id,
                            "timestamp": time.time()
                        }
                    )
                    
                    # 2. 保存消息（引用版本）
                    self.storage.save_message(
                        user_id,
                        {
                            "content": f"Message with version {version.id}",
                            "session_id": f"session_{workflow_id}",
                            "version_id": version.id
                        }
                    )
                    
                    # 3. 记录分析指标
                    self.analytics.record_metric(f"workflow_{workflow_id}_iteration", float(i))
                    self.analytics.record_metric(f"user_{user_id}_activity", 1.0)
                    
                    # 4. 验证数据一致性
                    conv = self.storage.get_conversation(user_id)
                    versions = self.vm.list_versions(f"wf_{workflow_id}")
                    summary = self.analytics.get_summary()
                    
                    # 5. 嵌套验证（调用自身更深一层）
                    if i % 3 == 0:
                        nested_verification(workflow_id, user_id, conv, versions)
                
                self.log_operation("CROSS", f"Workflow-{workflow_id}", f"User: {user_id}, Completed workflow with {iterations} iterations")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("CROSS", f"Workflow-{workflow_id}", e, f"User: {user_id}")
        
        def nested_verification(workflow_id, user_id, conv, versions):
            """嵌套验证"""
            try:
                self.log_operation("CROSS", f"Nested-Verification-{workflow_id}", f"User: {user_id}, Starting nested verification")
                
                # 深度验证
                for c in conv[-5:]:
                    self.analytics.record_metric(f"message_analysis", 1.0)
                
                for v in versions[-5:]:
                    retrieved = self.vm.get_version(v)
                    self.storage.save_message(user_id, {
                        "content": f"Verified version {retrieved.id}",
                        "session_id": f"verify_{workflow_id}"
                    })
                
                self.log_operation("CROSS", f"Nested-Verification-{workflow_id}", f"User: {user_id}, Completed nested verification")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("CROSS", "NestedVerification", e, f"User: {user_id}")
        
        # 执行50个复杂工作流
        print("执行 50 个复杂工作流...")
        threads = []
        for i in range(50):
            workflow_id = f"complex_wf_{i}"
            user_id = f"complex_user_{i}"
            iterations = random.randint(5, 20)
            
            t = threading.Thread(target=complex_workflow, args=(workflow_id, user_id, iterations))
            threads.append(t)
            t.start()
        
        for i, t in enumerate(threads):
            t.join(timeout=60)
            if (i + 1) % 10 == 0:
                print(f"  进度: {i + 1}/50")
        
        print(f"完成! 错误数: {errors[0]}")
        return errors[0]
    
    # ========================================================
    # 场景3：隐藏逻辑触发测试
    # ========================================================
    
    def test_hidden_logic_triggers(self):
        """隐藏逻辑触发测试"""
        print("\n" + "=" * 120)
        print("场景3: 隐藏逻辑触发测试")
        print("=" * 120)
        
        errors = [0]
        
        # 1. 测试边界条件触发
        print("  测试1: 边界条件触发")
        boundary_cases = [
            # 空字符串
            ("", "empty_string"),
            # 极长字符串
            ("x" * 100000, "very_long_string"),
            # 特殊字符
            ("\x00\x01\x02\n\r\t", "control_chars"),
            # Unicode边界
            ("文" * 10000, "unicode_boundary"),
            # None值
            (None, "none_value"),
            # 字典和列表
            ([{"nested": {"deep": [1, 2, 3]}}], "nested_structure"),
        ]
        
        for content, name in boundary_cases:
            try:
                self.log_operation("HIDDEN", f"Boundary-{name}", f"Testing boundary case: {name}")
                success = self.storage.save_message(
                    f"boundary_user_{name}",
                    {"content": content, "session_id": "boundary_test"}
                )
                
                if success:
                    conv = self.storage.get_conversation(f"boundary_user_{name}")
                    self.log_operation("HIDDEN", f"Boundary-{name}", f"Saved and retrieved {len(conv)} messages")
                else:
                    self.log_warning("HIDDEN", f"Boundary-{name}", "Save returned False")
                    
            except Exception as e:
                errors[0] += 1
                self.log_error("HIDDEN", f"Boundary-{name}", e)
        
        # 2. 测试时间边界
        print("  测试2: 时间边界触发")
        time_boundaries = [
            (0, "timestamp_zero"),
            (-1, "timestamp_negative"),
            (2147483647, "timestamp_2038"),
            (int(1e15), "timestamp_far_future"),
            (time.time() - 100*365*24*3600, "timestamp_100years_ago"),
        ]
        
        for ts, name in time_boundaries:
            try:
                self.log_operation("HIDDEN", f"Time-{name}", f"Testing time boundary: {name}")
                self.storage.save_message(
                    f"time_user_{name}",
                    {"content": f"Time test {name}", "timestamp": ts}
                )
                
            except Exception as e:
                errors[0] += 1
                self.log_error("HIDDEN", f"Time-{name}", e)
        
        # 3. 测试竞态条件
        print("  测试3: 竞态条件触发")
        def race_condition_worker(worker_id):
            user = f"race_user"
            try:
                for i in range(100):
                    self.storage.save_message(user, {"content": f"Race {worker_id}_{i}"})
                    self.storage.get_conversation(user)
                    self.storage.get_stats()
            except Exception as e:
                errors[0] += 1
                self.log_error("HIDDEN", "RaceCondition", e, f"Worker: {worker_id}")
        
        threads = []
        for i in range(20):
            t = threading.Thread(target=race_condition_worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"完成! 错误数: {errors[0]}")
        return errors[0]
    
    def log_warning(self, component, operation, message):
        """记录警告"""
        with self.lock:
            self.warnings.append({
                "component": component,
                "operation": operation,
                "message": message
            })
            logger.warning(f"[{component}] [{operation}] WARNING: {message}")
    
    # ========================================================
    # 场景4：完整业务流程闭环测试
    # ========================================================
    
    def test_complete_business_flow(self):
        """完整业务流程闭环测试"""
        print("\n" + "=" * 120)
        print("场景4: 完整业务流程闭环测试")
        print("=" * 120)
        
        errors = [0]
        
        def complete_business_flow(business_id, user_id):
            """
            完整业务流程：
            1. 用户登录 → 创建会话
            2. 发送消息 → 存储
            3. 创建版本 → 版本管理
            4. 记录指标 → 分析
            5. 查询历史 → 验证
            6. 清理会话 → 结束
            """
            try:
                self.log_operation("FLOW", f"Business-{business_id}", f"User: {user_id}, Starting complete business flow")
                
                # 步骤1: 创建会话
                session_id = f"session_{business_id}"
                agent_id = f"agent_{random.randint(1, 10)}"
                
                # 步骤2: 发送初始消息
                self.storage.save_message(user_id, {
                    "content": "Initial message",
                    "session_id": session_id,
                    "agent_id": agent_id
                })
                
                # 步骤3: 创建工作流版本
                version = self.vm.create_version(
                    f"business_wf_{business_id}",
                    {
                        "business_id": business_id,
                        "user": user_id,
                        "step": 1
                    }
                )
                
                # 步骤4: 批量消息交互
                for i in range(20):
                    self.storage.save_message(user_id, {
                        "content": f"Business message {i}",
                        "session_id": session_id,
                        "agent_id": agent_id,
                        "version_id": version.id
                    })
                    
                    self.analytics.record_metric(f"business_{business_id}_messages", 1.0)
                    
                    # 定期验证
                    if i % 5 == 0:
                        conv = self.storage.get_conversation(user_id, session_id, agent_id)
                        self.analytics.record_metric(f"business_{business_id}_verification", 1.0)
                
                # 步骤5: 创建第二个版本
                version2 = self.vm.create_version(
                    f"business_wf_{business_id}",
                    {
                        "business_id": business_id,
                        "user": user_id,
                        "step": 2,
                        "parent_version": version.id
                    }
                )
                
                # 步骤6: 最终验证
                conv = self.storage.get_conversation(user_id, session_id, agent_id)
                versions = self.vm.list_versions(f"business_wf_{business_id}")
                summary = self.analytics.get_summary()
                
                # 步骤7: 清理（不清除，保留数据）
                self.log_operation("FLOW", f"Business-{business_id}", 
                    f"User: {user_id}, Completed. Conv: {len(conv)}, Versions: {len(versions)}, Metrics: {summary['total_metrics']}")
                
            except Exception as e:
                errors[0] += 1
                self.log_error("FLOW", f"Business-{business_id}", e, f"User: {user_id}")
        
        # 执行100个完整业务流程
        print("执行 100 个完整业务流程...")
        threads = []
        for i in range(100):
            business_id = f"biz_{i}"
            user_id = f"biz_user_{i}"
            
            t = threading.Thread(target=complete_business_flow, args=(business_id, user_id))
            threads.append(t)
            t.start()
        
        for i, t in enumerate(threads):
            t.join(timeout=60)
            if (i + 1) % 20 == 0:
                print(f"  进度: {i + 1}/100")
        
        print(f"完成! 错误数: {errors[0]}")
        return errors[0]
    
    # ========================================================
    # 主测试函数
    # ========================================================
    
    def run_all_tests(self):
        """运行所有复杂业务场景测试"""
        print("=" * 120)
        print("🚀 第一阶段：复杂业务流程深度测试")
        print("=" * 120)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        self.stats["start_time"] = datetime.now()
        
        total_errors = 0
        
        # 场景1: 5层嵌套调用链路
        errors1 = self.test_nested_call_chain_depth_5()
        total_errors += errors1
        
        # 场景2: 多组件深度交互
        errors2 = self.test_cross_component_deep_interaction()
        total_errors += errors2
        
        # 场景3: 隐藏逻辑触发
        errors3 = self.test_hidden_logic_triggers()
        total_errors += errors3
        
        # 场景4: 完整业务流程闭环
        errors4 = self.test_complete_business_flow()
        total_errors += errors4
        
        # 生成报告
        self.generate_report(total_errors)
    
    def generate_report(self, total_errors):
        """生成测试报告"""
        print("\n" + "=" * 120)
        print("📊 第一阶段测试报告")
        print("=" * 120)
        
        duration = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        print(f"\n📈 操作统计:")
        print(f"  总操作数: {self.stats['total_operations']:,}")
        print(f"  嵌套操作: {self.stats['nested_operations']:,}")
        print(f"  跨组件调用: {self.stats['cross_component_calls']:,}")
        print(f"  隐藏逻辑触发: {self.stats['hidden_logic_triggers']:,}")
        print(f"  错误数: {self.stats['error_count']}")
        print(f"  测试时长: {duration:.2f}秒")
        print(f"  吞吐量: {self.stats['total_operations'] / max(duration, 1):.0f} ops/s")
        
        print(f"\n❌ 错误详情:")
        if self.errors:
            for i, err in enumerate(self.errors[:10], 1):
                print(f"  {i}. [{err['component']}] [{err['operation']}]")
                print(f"     {err['error_type']}: {err['message'][:80]}")
                if err['context']:
                    print(f"     Context: {err['context']}")
        else:
            print("  无错误!")
        
        print(f"\n⚠️  警告详情:")
        if self.warnings:
            for i, warn in enumerate(self.warnings[:5], 1):
                print(f"  {i}. [{warn['component']}] [{warn['operation']}]: {warn['message']}")
        else:
            print("  无警告!")
        
        print(f"\n💾 最终状态:")
        print(f"  存储: {self.storage.get_stats()}")
        print(f"  版本: {len(self.vm.versions) if hasattr(self.vm, 'versions') else 'N/A'} workflows")
        print(f"  分析: {self.analytics.get_summary()['total_metrics']} metrics")
        
        print("\n" + "=" * 120)
        if total_errors == 0:
            print("✅✅✅ 第一阶段测试通过！所有复杂业务场景零错误！✅✅✅")
        else:
            print(f"⚠️  发现 {total_errors} 个错误!")
        print("=" * 120)


def main():
    """主函数"""
    test = ComplexBusinessScenarioTest()
    test.run_all_tests()


if __name__ == "__main__":
    main()
