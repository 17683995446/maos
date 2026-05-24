#!/usr/bin/env python3
"""
快速调试测试 - 发现并修复问题
"""
import sys
sys.path.insert(0, '/workspace')

print("测试基本导入...")
try:
    from maos.storage.in_memory import InMemoryChatStorage
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.orchestration.orchestrator import MessageBroker
    print("  ✓ 导入成功")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n测试 InMemoryChatStorage...")
try:
    storage = InMemoryChatStorage()
    result = storage.save_message("test", {"content": "hello"})
    print(f"  ✓ save_message 返回: {result}")
    
    conv = storage.get_conversation("test")
    print(f"  ✓ get_conversation 返回 {len(conv)} 条消息")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试 VersionManager...")
try:
    vm = VersionManager()
    version = vm.create_version("test_wf", {"step": 1})
    print(f"  ✓ create_version 返回 ID: {version.id}")
    
    list_ver = vm.list_versions("test_wf")
    print(f"  ✓ list_versions 返回 {len(list_ver)} 个版本")
    
    get_ver = vm.get_version(version.id)
    print(f"  ✓ get_version 成功")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试 AnalyticsEngine...")
try:
    analytics = AnalyticsEngine()
    analytics.record_metric("test", 1.0)
    print(f"  ✓ record_metric 成功")
    
    summary = analytics.get_summary()
    print(f"  ✓ get_summary 返回: {summary}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试 MessageBroker...")
try:
    broker = MessageBroker()
    broker.publish({"type": "test", "data": 1})
    print(f"  ✓ publish 成功")
    
    msg = broker.receive()
    print(f"  ✓ receive 返回: {msg is not None}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 所有基础测试通过!")
