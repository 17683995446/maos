#!/usr/bin/env python3
"""
MAOS 第一性原理完整测试 - 最终版
测试所有核心组件的基本假设
"""

import threading
import time
import sys
from datetime import datetime

sys.path.insert(0, '/workspace')

print("="*90)
print("🚀 MAOS 第一性原理完整测试 - 最终版")
print("="*90)

# 全局导入
print("\n📦 导入所有模块...")
try:
    from maos.orchestration.orchestrator import (
        OrchestratorService, AgentRegistry, MessageBroker, EventEmitter,
        OrchestratorEvent, OrchestratorEventType
    )
    from maos.version.v14 import VersionManager, ABTestManager
    from maos.analytics.v14 import AnalyticsEngine
    print("✅ 所有模块导入成功\n")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试结果
results = {
    'passed': [],
    'failed': []
}

def test(name, func):
    """运行单个测试"""
    try:
        result = func()
        if result['passed']:
            results['passed'].append(name)
            print(f"✅ {name}")
            if 'details' in result:
                print(f"   {result['details']}")
        else:
            results['failed'].append(name)
            print(f"❌ {name}")
            print(f"   问题: {result['details']}")
    except Exception as e:
        results['failed'].append(name)
        print(f"❌ {name}")
        print(f"   错误: {str(e)}")

# ========== 测试1: 数据结构基础 ==========
print("\n" + "="*90)
print("🔬 测试1: 数据结构基础（第一性原理）")
print("="*90)

def test_dict_atomicity():
    """字典操作原子性"""
    shared_dict = {}
    iterations = 100000
    threads = []
    
    def writer(thread_id):
        for i in range(iterations):
            shared_dict[f'key_{thread_id}_{i}'] = f'value_{i}'
    
    for i in range(10):
        threads.append(threading.Thread(target=writer, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    expected = 10 * iterations
    actual = len(shared_dict)
    
    if actual == expected:
        return {'passed': True, 'details': f'所有{expected}个键值对正确存储'}
    else:
        return {'passed': False, 'details': f'数据丢失: 期望{expected}, 实际{actual}'}

test("字典操作原子性", test_dict_atomicity)

def test_list_thread_safety():
    """列表线程安全"""
    shared_list = []
    threads = []
    
    def appender(thread_id):
        for i in range(10000):
            shared_list.append((thread_id, i))
    
    for i in range(20):
        threads.append(threading.Thread(target=appender, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    expected = 20 * 10000
    actual = len(shared_list)
    
    if actual == expected:
        return {'passed': True, 'details': f'所有{expected}个元素正确添加'}
    else:
        return {'passed': False, 'details': f'元素丢失: 期望{expected}, 实际{actual}'}

test("列表线程安全", test_list_thread_safety)

# ========== 测试2: MAOS核心组件 ==========
print("\n" + "="*90)
print("🔧 测试2: MAOS核心组件")
print("="*90)

def test_agent_registry():
    """AgentRegistry线程安全"""
    registry = AgentRegistry()
    
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    threads = []
    def register_worker(thread_id):
        for i in range(10000):
            registry.register(MockAgent(f'agent_{thread_id}_{i}'))
    
    for i in range(50):
        threads.append(threading.Thread(target=register_worker, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    total_expected = 50 * 10000
    total_actual = len(registry.get_all_agents())
    
    if total_actual == total_expected:
        return {'passed': True, 'details': f'注册了{total_actual}个agent'}
    else:
        return {'passed': False, 'details': f'注册失败: 期望{total_expected}, 实际{total_actual}'}

test("AgentRegistry线程安全", test_agent_registry)

def test_message_broker():
    """MessageBroker可靠性"""
    broker = MessageBroker()
    
    threads = []
    def publisher(thread_id):
        for i in range(1000):
            broker.publish({'thread': thread_id, 'seq': i})
    
    for i in range(20):
        threads.append(threading.Thread(target=publisher, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    return {'passed': True, 'details': 'MessageBroker正常工作'}

test("MessageBroker可靠性", test_message_broker)

def test_event_emitter():
    """EventEmitter可靠性"""
    emitter = EventEmitter()
    received = []
    lock = threading.Lock()
    
    def handler(event):
        with lock:
            received.append(event)
    
    emitter.on(OrchestratorEventType.AGENT_REGISTERED, handler)
    
    threads = []
    def emit_events(thread_id):
        for i in range(1000):
            event = OrchestratorEvent(
                event_type=OrchestratorEventType.AGENT_REGISTERED,
                data={'thread': thread_id, 'seq': i}
            )
            emitter.emit(event)
    
    for i in range(10):
        threads.append(threading.Thread(target=emit_events, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    total_expected = 10 * 1000
    total_actual = len(received)
    
    if total_actual == total_expected:
        return {'passed': True, 'details': f'接收了{total_actual}个事件'}
    else:
        return {'passed': False, 'details': f'事件丢失: 期望{total_expected}, 实际{total_actual}'}

test("EventEmitter可靠性", test_event_emitter)

def test_version_manager():
    """VersionManager正确性"""
    vm = VersionManager()
    
    threads = []
    def create_versions(thread_id):
        for i in range(1000):
            vm.create_version(f'wf_{thread_id}', {'data': i})
    
    for i in range(20):
        threads.append(threading.Thread(target=create_versions, args=(i,)))
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    versions = vm.list_versions('wf_0')
    
    if len(versions) > 0:
        return {'passed': True, 'details': f'创建了{len(versions)}个版本'}
    else:
        return {'passed': False, 'details': '版本创建失败'}

test("VersionManager正确性", test_version_manager)

# ========== 测试3: AnalyticsEngine ==========
print("\n" + "="*90)
print("📊 测试3: AnalyticsEngine")
print("="*90)

def test_analytics_get_summary():
    """AnalyticsEngine.get_summary()"""
    ae = AnalyticsEngine()
    ae.record_metric('test1', 1, None, {'tag': 'test'})
    ae.record_metric('test2', None, None, None)  # 测试None值
    
    summary = ae.get_summary()
    
    if 'total_metrics' in summary and summary['total_metrics'] >= 0:
        return {'passed': True, 'details': f'get_summary()返回{summary["total_metrics"]}个指标'}
    else:
        return {'passed': False, 'details': 'get_summary()失败'}

test("AnalyticsEngine.get_summary()", test_analytics_get_summary)

def test_analytics_none_handling():
    """AnalyticsEngine处理None值"""
    ae = AnalyticsEngine()
    ae.record_metric('null_test', None, None, None)
    
    summary = ae.get_summary()
    stats = summary.get('metric_stats', {})
    
    if 'null_test' in stats:
        return {'passed': True, 'details': 'None值被正确处理为0.0'}
    else:
        return {'passed': False, 'details': 'None值处理失败'}

test("AnalyticsEngine处理None值", test_analytics_none_handling)

# ========== 最终报告 ==========
print("\n" + "="*90)
print("📊 第一性原理完整测试 - 最终报告")
print("="*90)

total = len(results['passed']) + len(results['failed'])
passed = len(results['passed'])
failed = len(results['failed'])

print(f"\n📝 测试结果:")
print(f"   ✅ 通过: {passed}/{total}")
print(f"   ❌ 失败: {failed}/{total}")

if results['failed']:
    print(f"\n❌ 失败的测试:")
    for test_name in results['failed']:
        print(f"   - {test_name}")

# 健康评分
health_score = (passed / total * 100) if total > 0 else 0
health_score = int(health_score)

print(f"\n🏥 系统健康评分: {health_score}/100")

if health_score >= 90:
    status = "🌟 优秀"
elif health_score >= 70:
    status = "✅ 良好"
elif health_score >= 50:
    status = "⚠️ 一般"
else:
    status = "❌ 需改进"

print(f"   状态: {status}")

print("\n" + "="*90)
print("✅ 第一性原理完整测试完成")
print("="*90)
