#!/usr/bin/env python3
"""
MAOS System - Comprehensive Deep Verification Test Suite
全面的深度验证测试套件 - 覆盖所有核心组件
"""

import sys
import time
import random
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any

sys.path.insert(0, '/workspace')

# Import all core modules
from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine
from maos.types import ConversationMessage, ParticipantRole

class DeepVerificationTestSuite:
    """深度验证测试套件"""
    
    def __init__(self):
        self.errors = []
        self.successes = []
        self.warnings = []
        self.lock = threading.Lock()
        self.test_count = 0
        
    def log_success(self, test_name: str, details: str = ""):
        """记录成功"""
        with self.lock:
            self.successes.append({
                "test": test_name,
                "timestamp": datetime.now(),
                "details": details
            })
            self.test_count += 1
            print(f"✅ SUCCESS: {test_name} {details}")
    
    def log_error(self, test_name: str, error: Exception, details: str = ""):
        """记录错误"""
        with self.lock:
            self.errors.append({
                "test": test_name,
                "timestamp": datetime.now(),
                "error_type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
                "details": details
            })
            self.test_count += 1
            print(f"❌ ERROR: {test_name} - {type(error).__name__}: {str(error)}")
            print(f"   Details: {details}")
    
    def log_warning(self, test_name: str, message: str, details: str = ""):
        """记录警告"""
        with self.lock:
            self.warnings.append({
                "test": test_name,
                "timestamp": datetime.now(),
                "message": message,
                "details": details
            })
            print(f"⚠️  WARNING: {test_name} - {message} {details}")
    
    # ================================================
    # STORAGE MODULE TESTS
    # ================================================
    
    def test_storage_basic_save_and_read(self):
        """测试存储的基本保存和读取"""
        storage = InMemoryChatStorage()
        
        try:
            # Save message
            success = storage.save_message(
                "test_user",
                {"content": "Hello, world!", "session_id": "test", "agent_id": "default"}
            )
            assert success, "Save message should succeed"
            
            # Read message
            conv = storage.get_conversation("test_user", "test", "default")
            assert len(conv) == 1, f"Should have 1 message, got {len(conv)}"
            assert conv[0]["content"][0]["text"] == "Hello, world!", "Content mismatch"
            
            self.log_success("storage_basic_save_and_read", "Saved 1 message, verified content")
            
        except Exception as e:
            self.log_error("storage_basic_save_and_read", e)
    
    def test_storage_multiple_messages(self):
        """测试存储多条消息"""
        storage = InMemoryChatStorage()
        
        try:
            for i in range(100):
                storage.save_message(
                    "multi_user",
                    {"content": f"Message {i}", "session_id": "multi"}
                )
            
            conv = storage.get_conversation("multi_user", "multi")
            assert len(conv) == 100, f"Should have 100 messages, got {len(conv)}"
            
            # Verify all messages are present
            for i in range(100):
                assert f"Message {i}" in str(conv[i]["content"]), f"Missing message {i}"
            
            self.log_success("storage_multiple_messages", "Saved and verified 100 messages")
            
        except Exception as e:
            self.log_error("storage_multiple_messages", e)
    
    def test_storage_extreme_timestamps(self):
        """测试存储极端时间戳"""
        storage = InMemoryChatStorage()
        
        try:
            extreme_timestamps = [
                ("normal", time.time()),
                ("zero", 0),
                ("far_past", -100000000000),  # Way in past
                ("far_future", 100000000000),   # Way in future
                ("negative", -3600),  # 1 hour ago
                ("large_float", 1e20),  # Extremely large number
            ]
            
            for name, ts in extreme_timestamps:
                success = storage.save_message(
                    f"ts_user_{name}",
                    {"content": f"Test with {name} timestamp", "timestamp": ts}
                )
                assert success, f"Should handle {name} timestamp"
            
            self.log_success("storage_extreme_timestamps", "Handled all extreme timestamps")
            
        except Exception as e:
            self.log_error("storage_extreme_timestamps", e)
    
    def test_storage_session_separation(self):
        """测试会话分离"""
        storage = InMemoryChatStorage()
        
        try:
            storage.save_message("session_user", {"content": "Message in session 1", "session_id": "s1"})
            storage.save_message("session_user", {"content": "Message in session 2", "session_id": "s2"})
            
            conv1 = storage.get_conversation("session_user", "s1")
            conv2 = storage.get_conversation("session_user", "s2")
            
            assert len(conv1) == 1, "Session 1 should have 1 message"
            assert len(conv2) == 1, "Session 2 should have 1 message"
            assert conv1[0]["content"][0]["text"] == "Message in session 1"
            assert conv2[0]["content"][0]["text"] == "Message in session 2"
            
            self.log_success("storage_session_separation", "Sessions are properly isolated")
            
        except Exception as e:
            self.log_error("storage_session_separation", e)
    
    def test_storage_get_stats(self):
        """测试获取存储统计信息"""
        storage = InMemoryChatStorage()
        
        try:
            for i in range(10):
                storage.save_message("stats_user", {"content": f"Stats {i}"})
            
            stats = storage.get_stats()
            assert "conversation_count" in stats, "Should have conversation_count"
            assert "session_count" in stats, "Should have session_count"
            assert "total_messages" in stats, "Should have total_messages"
            
            self.log_success("storage_get_stats", f"Got stats: {stats}")
            
        except Exception as e:
            self.log_error("storage_get_stats", e)
    
    def test_storage_clear_all(self):
        """测试清除所有内容"""
        storage = InMemoryChatStorage()
        
        try:
            for i in range(10):
                storage.save_message("clear_user", {"content": f"Clear {i}"})
            
            stats_before = storage.get_stats()
            assert stats_before["total_messages"] == 10, "Should have 10 messages"
            
            storage.clear_all()
            
            stats_after = storage.get_stats()
            assert stats_after["total_messages"] == 0, "Should have 0 messages after clear"
            
            self.log_success("storage_clear_all", "Clear all function works correctly")
            
        except Exception as e:
            self.log_error("storage_clear_all", e)
    
    def test_storage_empty_and_null_values(self):
        """测试空值和null值"""
        storage = InMemoryChatStorage()
        
        try:
            test_cases = [
                {"content": "", "name": "empty_string"},
                {"content": None, "name": "null_value"},
                {"content": 123, "name": "number_value"},
                {"content": ["a", "b", None], "name": "list_with_null"},
                {"content": {"text": "test", "nested": None}, "name": "dict_with_null"},
            ]
            
            for test_case in test_cases:
                success = storage.save_message(
                    f"null_user_{test_case['name']}",
                    {"content": test_case["content"]}
                )
                assert success, f"Should handle {test_case['name']}"
            
            self.log_success("storage_empty_and_null_values", "Handled all empty and null test cases")
            
        except Exception as e:
            self.log_error("storage_empty_and_null_values", e)
    
    # ================================================
    # VERSION MANAGER TESTS
    # ================================================
    
    def test_version_basic_create_and_get(self):
        """测试版本的基本创建和获取"""
        vm = VersionManager()
        
        try:
            version = vm.create_version("test_wf", {"step": 1, "data": "test"})
            assert version is not None, "Version should be created"
            assert hasattr(version, "id"), "Version should have id"
            assert hasattr(version, "workflow_name"), "Version should have workflow name"
            
            retrieved = vm.get_version(version.id)
            assert retrieved is not None, "Should retrieve created version"
            
            self.log_success("version_basic_create_and_get", f"Version {version.id} created and retrieved")
            
        except Exception as e:
            self.log_error("version_basic_create_and_get", e)
    
    def test_version_list_versions(self):
        """测试版本列表"""
        vm = VersionManager()
        
        try:
            for i in range(10):
                vm.create_version("list_wf", {"iteration": i})
            
            versions = vm.list_versions("list_wf")
            assert len(versions) == 10, f"Should have 10 versions, got {len(versions)}"
            
            self.log_success("version_list_versions", f"Listed {len(versions)} versions")
            
        except Exception as e:
            self.log_error("version_list_versions", e)
    
    def test_version_workflow_separation(self):
        """测试工作流隔离"""
        vm = VersionManager()
        
        try:
            vm.create_version("wf1", {"x": 1})
            vm.create_version("wf2", {"x": 2})
            vm.create_version("wf2", {"x": 3})
            
            versions1 = vm.list_versions("wf1")
            versions2 = vm.list_versions("wf2")
            
            assert len(versions1) == 1, "Workflow 1 should have 1 version"
            assert len(versions2) == 2, "Workflow 2 should have 2 versions"
            
            self.log_success("version_workflow_separation", "Workflows are properly isolated")
            
        except Exception as e:
            self.log_error("version_workflow_separation", e)
    
    # ================================================
    # ANALYTICS ENGINE TESTS
    # ================================================
    
    def test_analytics_basic_recording(self):
        """测试分析引擎的基本记录"""
        analytics = AnalyticsEngine()
        
        try:
            for i in range(100):
                analytics.record_metric("test_metric", float(i))
            
            summary = analytics.get_summary()
            assert summary["total_metrics"] == 100, "Should have 100 metrics"
            assert "metric_names" in summary, "Should have metric_names"
            
            self.log_success("analytics_basic_recording", "Recorded and retrieved 100 metrics")
            
        except Exception as e:
            self.log_error("analytics_basic_recording", e)
    
    def test_analytics_extreme_values(self):
        """测试分析引擎的极端值"""
        analytics = AnalyticsEngine()
        
        try:
            analytics.record_metric("extreme_metric", float("inf"))
            analytics.record_metric("extreme_metric", float("-inf"))
            analytics.record_metric("extreme_metric", float("nan"))
            analytics.record_metric("extreme_metric", 0.0)
            analytics.record_metric("extreme_metric", 1e20)
            analytics.record_metric("extreme_metric", -1e20)
            
            summary = analytics.get_summary()
            data = summary["metric_stats"].get("extreme_metric", {})
            
            self.log_success("analytics_extreme_values", "Handled all extreme values")
            
        except Exception as e:
            self.log_error("analytics_extreme_values", e)
    
    def test_analytics_summary_calculation(self):
        """测试分析引擎的摘要计算"""
        analytics = AnalyticsEngine()
        
        try:
            for i in range(50):
                analytics.record_metric("summary_metric", float(i))
            
            summary_data = analytics.calculate_summary("summary_metric")
            assert hasattr(summary_data, "value"), "Should have value"
            assert hasattr(summary_data, "trend"), "Should have trend"
            
            self.log_success("analytics_summary_calculation", "Summary calculated successfully")
            
        except Exception as e:
            self.log_error("analytics_summary_calculation", e)
    
    def test_analytics_cleanup(self):
        """测试分析引擎的清理"""
        analytics = AnalyticsEngine()
        
        try:
            # Record some metrics
            for i in range(100):
                analytics.record_metric("cleanup_metric", float(i))
            
            # Cleanup
            analytics.cleanup()
            
            summary = analytics.get_summary()
            assert summary["total_metrics"] == 0, "Should have 0 metrics after cleanup"
            
            self.log_success("analytics_cleanup", "Cleanup function works correctly")
            
        except Exception as e:
            self.log_error("analytics_cleanup", e)
    
    # ================================================
    # CONCURRENCY & STRESS TESTS
    # ================================================
    
    def test_concurrent_storage_operations(self):
        """测试并发存储操作"""
        storage = InMemoryChatStorage()
        errors = []
        operations = [0]
        lock = threading.Lock()
        
        def worker(worker_id):
            try:
                for i in range(100):
                    storage.save_message(
                        f"concurrent_user_{worker_id % 10}",
                        {"content": f"Worker {worker_id} message {i}"}
                    )
                    with lock:
                        operations[0] += 1
            except Exception as e:
                with lock:
                    errors.append(e)
        
        try:
            threads = []
            for i in range(10):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=60)
            
            assert len(errors) == 0, f"Should have 0 errors, got {len(errors)}"
            assert operations[0] == 1000, f"Should have 1000 operations, got {operations[0]}"
            
            self.log_success("test_concurrent_storage_operations", f"10 threads, 1000 operations successful")
            
        except Exception as e:
            self.log_error("test_concurrent_storage_operations", e)
    
    def test_concurrent_analytics_recording(self):
        """测试并发分析记录"""
        analytics = AnalyticsEngine()
        errors = []
        operations = [0]
        lock = threading.Lock()
        
        def worker(worker_id):
            try:
                for i in range(50):
                    analytics.record_metric(f"metric_{worker_id % 5}", float(i))
                    with lock:
                        operations[0] += 1
            except Exception as e:
                with lock:
                    errors.append(e)
        
        try:
            threads = []
            for i in range(20):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=60)
            
            assert len(errors) == 0, f"Should have 0 errors, got {len(errors)}"
            summary = analytics.get_summary()
            assert summary["total_metrics"] == 1000, f"Should have 1000 metrics"
            
            self.log_success("test_concurrent_analytics_recording", "20 threads, 1000 metric recordings successful")
            
        except Exception as e:
            self.log_error("test_concurrent_analytics_recording", e)
    
    # ================================================
    # INTEGRATION TESTS
    # ================================================
    
    def test_storage_analytics_integration(self):
        """测试存储和分析引擎的集成"""
        storage = InMemoryChatStorage()
        analytics = AnalyticsEngine()
        
        try:
            # Record messages and metrics
            for i in range(50):
                storage.save_message("integrated_user", {"content": f"Msg {i}"})
                analytics.record_metric("messages_recorded", float(i))
            
            # Verify both work
            conv = storage.get_conversation("integrated_user")
            summary = analytics.get_summary()
            
            assert len(conv) == 50, "Should have 50 messages"
            assert summary["total_metrics"] == 50, "Should have 50 metrics"
            
            self.log_success("storage_analytics_integration", "Integration between storage and analytics works")
            
        except Exception as e:
            self.log_error("storage_analytics_integration", e)
    
    # ================================================
    # BOUNDARY & EDGE TESTS
    # ================================================
    
    def test_unicode_content(self):
        """测试Unicode内容"""
        storage = InMemoryChatStorage()
        
        try:
            unicode_content = [
                "Hello, world! 🌍",
                "中文日本語한국어",
                "🎉🎊🎁🎀🎄",
                "a̐éö̲\r\n",
                "\x00\x01\x02\x03\x04\x05",  # Control characters
            ]
            
            for content in unicode_content:
                success = storage.save_message(
                    "unicode_user",
                    {"content": content}
                )
                assert success, f"Should handle unicode: {content[:20]}"
            
            self.log_success("test_unicode_content", "Handled all unicode test cases")
            
        except Exception as e:
            self.log_error("test_unicode_content", e)
    
    def test_large_content(self):
        """测试大内容"""
        storage = InMemoryChatStorage()
        
        try:
            large_content = "x" * 10000  # 10KB content
            success = storage.save_message(
                "large_user",
                {"content": large_content}
            )
            assert success, "Should handle large content"
            
            conv = storage.get_conversation("large_user")
            assert len(conv) == 1, "Should have 1 message"
            
            self.log_success("test_large_content", "Handled 10KB content")
            
        except Exception as e:
            self.log_error("test_large_content", e)
    
    # ================================================
    # SUMMARY & REPORTING
    # ================================================
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 100)
        print("MAOS COMPREHENSIVE TEST REPORT")
        print("=" * 100)
        
        total = len(self.errors) + len(self.successes)
        error_rate = len(self.errors) / max(total, 1) * 100
        
        print(f"Total tests: {total}")
        print(f"Successful: {len(self.successes)}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Error rate: {error_rate:.2f}%")
        
        if self.errors:
            print("\n" + "-" * 100)
            print("DETAILED ERROR LIST")
            print("-" * 100)
            for i, err in enumerate(self.errors):
                print(f"\n{+1}. [{err['severity'] if 'severity' in err else 'ERROR'}] [{err['test']}]")
                print(f"   {err['timestamp']}")
                print(f"   {err['error_type']}: {err['message']}")
                if err['details']:
                    print(f"   Details: {err['details']}")
        
        if error_rate == 0:
            print("\n✅ ALL TESTS PASSED! System is working perfectly!")
            return 0
        else:
            print(f"\n⚠️  {len(self.errors)} TEST(S) FAILED!")
            return 1


def main():
    """主测试函数"""
    suite = DeepVerificationTestSuite()
    
    print("=" * 100)
    print("MAOS SYSTEM - COMPREHENSIVE DEEP VERIFICATION TEST")
    print("=" * 100)
    print(f"Start time: {datetime.now().isoformat()}")
    print()
    
    # ======================================================
    # RUN ALL TESTS
    # ======================================================
    
    print("\n" + "=" * 100)
    print("STORAGE MODULE TESTS")
    print("=" * 100)
    suite.test_storage_basic_save_and_read()
    suite.test_storage_multiple_messages()
    suite.test_storage_extreme_timestamps()
    suite.test_storage_session_separation()
    suite.test_storage_get_stats()
    suite.test_storage_clear_all()
    suite.test_storage_empty_and_null_values()
    
    print("\n" + "=" * 100)
    print("VERSION MANAGER TESTS")
    print("=" * 100)
    suite.test_version_basic_create_and_get()
    suite.test_version_list_versions()
    suite.test_version_workflow_separation()
    
    print("\n" + "=" * 100)
    print("ANALYTICS ENGINE TESTS")
    print("=" * 100)
    suite.test_analytics_basic_recording()
    suite.test_analytics_extreme_values()
    suite.test_analytics_summary_calculation()
    suite.test_analytics_cleanup()
    
    print("\n" + "=" * 100)
    print("CONCURRENCY & STRESS TESTS")
    print("=" * 100)
    suite.test_concurrent_storage_operations()
    suite.test_concurrent_analytics_recording()
    
    print("\n" + "=" * 100)
    print("INTEGRATION TESTS")
    print("=" * 100)
    suite.test_storage_analytics_integration()
    
    print("\n" + "=" * 100)
    print("BOUNDARY & EDGE TESTS")
    print("=" * 100)
    suite.test_unicode_content()
    suite.test_large_content()
    
    # ======================================================
    # GENERATE FINAL REPORT
    # ======================================================
    print()
    exit_code = suite.generate_report()
    
    print("\n" + "=" * 100)
    print(f"End time: {datetime.now().isoformat()}")
    print("=" * 100)
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
