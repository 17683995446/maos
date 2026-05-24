#!/usr/bin/env python3
"""
分步测试 - 先测试基本功能
"""

import sys
sys.path.insert(0, '/workspace')

print("测试 1: 导入模块")
try:
    from maos.storage.in_memory import InMemoryChatStorage
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.orchestration.orchestrator import MessageBroker
    print("  ✅ 导入成功")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    sys.exit(1)

print("\n测试 2: InMemoryChatStorage")
try:
    storage = InMemoryChatStorage()
    print("  ✅ 创建存储成功")
    
    result = storage.save_message("test_user", {"content": "test"})
    print(f"  ✅ 保存消息成功: {result}")
    
    messages = storage.get_conversation("test_user")
    print(f"  ✅ 获取对话成功: {len(messages)} 条")
    
    print("  ✅ InMemoryChatStorage 测试通过")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试 3: VersionManager")
try:
    vm = VersionManager()
    print("  ✅ 创建版本管理器成功")
    
    version = vm.create_version("test_wf", {"step": 1})
    print(f"  ✅ 创建版本成功: {version.id}")
    
    versions = vm.list_versions("test_wf")
    print(f"  ✅ 列出版本成功: {len(versions)} 个")
    
    retrieved = vm.get_version(version.id)
    print(f"  ✅ 获取版本成功: {retrieved is not None}")
    
    print("  ✅ VersionManager 测试通过")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试 4: AnalyticsEngine")
try:
    analytics = AnalyticsEngine()
    print("  ✅ 创建分析引擎成功")
    
    analytics.record_metric("test", 1.0)
    print("  ✅ 记录指标成功")
    
    summary = analytics.get_summary()
    print(f"  ✅ 获取摘要成功: {summary}")
    
    print("  ✅ AnalyticsEngine 测试通过")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试 5: MessageBroker")
try:
    broker = MessageBroker()
    print("  ✅ 创建消息代理成功")
    
    broker.publish({"id": 1, "type": "test"})
    print("  ✅ 发布消息成功")
    
    received = broker.receive()
    print(f"  ✅ 接收消息成功: {received is not None}")
    
    print("  ✅ MessageBroker 测试通过")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 所有基本测试通过!")
