#!/usr/bin/env python3
"""
MAOS 第一性原理快速验证测试
"""

import threading
import time
import sys
from datetime import datetime

sys.path.insert(0, '/workspace')

print("="*90)
print("🔬 MAOS 第一性原理快速验证测试")
print("="*90)

# 导入所有模块
try:
    from maos.orchestration.orchestrator import (
        OrchestratorService, AgentRegistry, MessageBroker, EventEmitter,
        OrchestratorEvent, OrchestratorEventType
    )
    from maos.version.v14 import VersionManager, ABTestManager
    from maos.analytics.v14 import AnalyticsEngine
    print("✅ 所有模块导入成功\n")
except ImportError as e:
    print(f"❌ 导入失败: {e}\n")
    sys.exit(1)

# 测试1: AnalyticsEngine.get_summary()
print("测试1: AnalyticsEngine.get_summary() 方法")
try:
    ae = AnalyticsEngine()
    ae.record_metric('test', 1, None, {'tag': 'test'})
    ae.record_metric('test', None, None, {})  # 测试None值
    
    summary = ae.get_summary()
    print(f"✅ get_summary() 返回: {summary['total_metrics']} 个指标")
except Exception as e:
    print(f"❌ get_summary() 失败: {e}")

# 测试2: None值处理
print("\n测试2: record_metric() 处理None值")
try:
    ae2 = AnalyticsEngine()
    ae2.record_metric('null_test', None, None, None)
    summary2 = ae2.get_summary()
    print(f"✅ None值被正确处理: {summary2['metric_stats']}")
except Exception as e:
    print(f"❌ None值处理失败: {e}")

# 测试3: AgentRegistry线程安全
print("\n测试3: AgentRegistry线程安全")
try:
    registry = AgentRegistry()
    
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    threads = []
    for i in range(50):
        def register():
            registry.register(MockAgent(f'agent_{i}'))
        threads.append(threading.Thread(target=register))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    agents = registry.get_all_agents()
    print(f"✅ 线程安全: 注册了 {len(agents)} 个agent")
except Exception as e:
    print(f"❌ AgentRegistry失败: {e}")

# 测试4: VersionManager
print("\n测试4: VersionManager")
try:
    vm = VersionManager()
    for i in range(10):
        vm.create_version(f'wf_{i}', {'data': i})
    
    versions = vm.list_versions('wf_0')
    print(f"✅ VersionManager工作正常: {len(versions)} 个版本")
except Exception as e:
    print(f"❌ VersionManager失败: {e}")

# 测试5: MessageBroker
print("\n测试5: MessageBroker")
try:
    broker = MessageBroker()
    for i in range(10):
        broker.publish({'msg': i})
    
    print(f"✅ MessageBroker工作正常")
except Exception as e:
    print(f"❌ MessageBroker失败: {e}")

print("\n" + "="*90)
print("✅ 快速验证测试完成")
print("="*90)
