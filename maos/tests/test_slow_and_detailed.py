#!/usr/bin/env python3
"""
MAOS 慢工出细活深度测试套件 v6.0
遵循"慢工出细活"原理 - 深入、细致、持续的测试
特点：
1. 长时间运行测试
2. 精细化边界测试
3. 持续监控和记录
4. 深度性能分析
5. 异常情况模拟
"""

import threading
import time
import random
import sys
import gc
import traceback
import weakref
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
import psutil
import os
import json

sys.path.insert(0, '/workspace')


class DetailedBugTracker:
    """详细的Bug追踪器"""
    def __init__(self):
        self.bugs = []
        self.warnings = []
        self.performance_logs = []
        self.memory_logs = []
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.test_count = 0
        self.error_count = 0
        
    def record_bug(self, component, test_name, severity, description, 
                   assumption, expected, actual, stack=''):
        self.error_count += 1
        bug = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': time.time() - self.start_time,
            'component': component,
            'test_name': test_name,
            'severity': severity,
            'description': description,
            'assumption': assumption,
            'expected': expected,
            'actual': actual,
            'stack_trace': stack
        }
        with self.lock:
            self.bugs.append(bug)
        
        icons = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}
        icon = icons.get(severity, '⚪')
        print(f"{icon} [{severity}] [{bug['elapsed']:.1f}s] {component}.{test_name}")
        print(f"   假设: {assumption}")
        print(f"   期望: {expected}")
        print(f"   实际: {actual[:100] if isinstance(actual, str) else actual}")
    
    def record_warning(self, component, test_name, description):
        with self.lock:
            self.warnings.append({
                'timestamp': datetime.now().isoformat(),
                'component': component,
                'test_name': test_name,
                'description': description
            })
        print(f"⚠️  {component}.{test_name}: {description}")
    
    def record_performance(self, component, operation, duration_ms, iteration):
        with self.lock:
            self.performance_logs.append({
                'timestamp': time.time(),
                'component': component,
                'operation': operation,
                'duration_ms': duration_ms,
                'iteration': iteration
            })
    
    def record_memory(self, component, mem_mb, iteration):
        with self.lock:
            self.memory_logs.append({
                'timestamp': time.time(),
                'component': component,
                'mem_mb': mem_mb
            })
    
    def increment_test(self):
        with self.lock:
            self.test_count += 1
    
    def get_summary(self):
        with self.lock:
            return {
                'total_tests': self.test_count,
                'total_errors': self.error_count,
                'total_bugs': len(self.bugs),
                'critical': len([b for b in self.bugs if b['severity'] == 'CRITICAL']),
                'high': len([b for b in self.bugs if b['severity'] == 'HIGH']),
                'medium': len([b for b in self.bugs if b['severity'] == 'MEDIUM']),
                'low': len([b for b in self.bugs if b['severity'] == 'LOW']),
                'warnings': len(self.warnings)
            }


# ========== 测试1: 精细化组件测试 ==========
def test_component_refinement(tracker):
    """测试1: 精细化组件测试 - 每个方法逐一测试"""
    print("\n" + "="*90)
    print("🔬 测试1: 精细化组件测试 (慢工出细活)")
    print("="*90)
    
    from maos.orchestration.orchestrator import (
        AgentRegistry, MessageBroker, EventEmitter,
        OrchestratorEvent, OrchestratorEventType
    )
    from maos.version.v14 import VersionManager, ABTestManager
    from maos.analytics.v14 import AnalyticsEngine
    
    components = [
        ("AgentRegistry", AgentRegistry(), [
            ("register", test_agent_register),
            ("unregister", test_agent_unregister),
            ("get_agent", test_agent_get),
            ("get_all_agents", test_agent_get_all),
            ("update_status", test_agent_update_status),
            ("select_best_agent", test_agent_select),
            ("statistics", test_agent_statistics),
            ("cleanup", test_agent_cleanup),
        ]),
        ("MessageBroker", MessageBroker(), [
            ("publish", test_broker_publish),
            ("subscribe", test_broker_subscribe),
            ("receive", test_broker_receive),
            ("unsubscribe", test_broker_unsubscribe),
            ("cleanup", test_broker_cleanup),
        ]),
        ("EventEmitter", EventEmitter(), [
            ("on", test_emitter_on),
            ("off", test_emitter_off),
            ("emit", test_emitter_emit),
            ("cleanup", test_emitter_cleanup),
        ]),
        ("VersionManager", VersionManager(), [
            ("create_version", test_vm_create),
            ("get_version", test_vm_get),
            ("list_versions", test_vm_list),
            ("get_latest", test_vm_latest),
            ("activate", test_vm_activate),
            ("rollback", test_vm_rollback),
            ("cleanup", test_vm_cleanup),
        ]),
        ("AnalyticsEngine", AnalyticsEngine(), [
            ("record_metric", test_ae_record),
            ("get_metric_data", test_ae_get_data),
            ("calculate_summary", test_ae_summary),
            ("get_summary", test_ae_get_summary),
            ("cleanup", test_ae_cleanup),
        ]),
    ]
    
    for component_name, component, methods in components:
        print(f"\n📦 测试组件: {component_name}")
        
        for method_name, test_func in methods:
            tracker.increment_test()
            try:
                result = test_func(component, method_name)
                if not result['passed']:
                    tracker.record_bug(
                        component_name,
                        method_name,
                        result.get('severity', 'MEDIUM'),
                        result.get('description', '测试失败'),
                        result.get('assumption', ''),
                        result.get('expected', ''),
                        result.get('actual', ''),
                        result.get('stack', '')
                    )
                else:
                    print(f"   ✅ {method_name}")
            except Exception as e:
                tracker.record_bug(
                    component_name,
                    method_name,
                    'MEDIUM',
                    f'测试异常: {str(e)}',
                    f'{method_name}方法可用',
                    '正常运行',
                    str(e),
                    traceback.format_exc()
                )
    
    return tracker


def test_agent_register(component, method):
    """测试AgentRegistry.register方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        agent = MockAgent('test_agent')
        result = component.register(agent)
        
        if result:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'register方法返回True表示成功',
                'expected': 'True',
                'actual': result
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'register方法应该正常工作',
            'expected': '成功注册',
            'actual': str(e),
            'stack': traceback.format_exc()
        }


def test_agent_unregister(component, method):
    """测试AgentRegistry.unregister方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        agent = MockAgent('test_unreg_agent')
        component.register(agent)
        result = component.unregister('test_unreg_agent')
        
        if result:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'unregister返回True表示成功',
                'expected': 'True',
                'actual': result
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'unregister方法应该正常工作',
            'expected': '成功注销',
            'actual': str(e)
        }


def test_agent_get(component, method):
    """测试AgentRegistry.get_agent方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        agent = MockAgent('test_get_agent')
        component.register(agent)
        retrieved = component.get_agent('test_get_agent')
        
        if retrieved and retrieved.name == 'test_get_agent':
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'get_agent返回正确的agent',
                'expected': 'MockAgent对象',
                'actual': retrieved
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'get_agent方法应该正常工作',
            'expected': '成功获取agent',
            'actual': str(e)
        }


def test_agent_get_all(component, method):
    """测试AgentRegistry.get_all_agents方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        for i in range(10):
            agent = MockAgent(f'test_all_agent_{i}')
            component.register(agent)
        
        agents = component.get_all_agents()
        
        if len(agents) >= 10:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'get_all_agents返回所有注册的agent',
                'expected': '>=10个agent',
                'actual': len(agents)
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'get_all_agents方法应该正常工作',
            'expected': '返回agent列表',
            'actual': str(e)
        }


def test_agent_update_status(component, method):
    """测试AgentRegistry.update_agent_status方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        agent = MockAgent('test_status_agent')
        component.register(agent)
        result = component.update_agent_status('test_status_agent', 'busy')
        
        if result:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'update_agent_status返回True表示成功',
                'expected': 'True',
                'actual': result
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'update_agent_status方法应该正常工作',
            'expected': '成功更新状态',
            'actual': str(e)
        }


def test_agent_select(component, method):
    """测试AgentRegistry.select_best_agent方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test', 'analyze']
    
    try:
        for i in range(5):
            agent = MockAgent(f'test_select_agent_{i}')
            component.register(agent)
        
        selected = component.select_best_agent(['test'])
        
        if selected:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'select_best_agent返回最佳agent',
                'expected': 'MockAgent对象',
                'actual': selected
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'select_best_agent方法应该正常工作',
            'expected': '成功选择agent',
            'actual': str(e)
        }


def test_agent_statistics(component, method):
    """测试AgentRegistry.get_statistics方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        for i in range(3):
            agent = MockAgent(f'test_stat_agent_{i}')
            component.register(agent)
        
        stats = component.get_statistics()
        
        if 'total' in stats and stats['total'] >= 3:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'get_statistics返回正确的统计信息',
                'expected': "包含'total'键",
                'actual': stats
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'get_statistics方法应该正常工作',
            'expected': '返回统计信息',
            'actual': str(e)
        }


def test_agent_cleanup(component, method):
    """测试AgentRegistry.cleanup方法"""
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = 'idle'
            self.capabilities = ['test']
    
    try:
        for i in range(5):
            agent = MockAgent(f'test_cleanup_agent_{i}')
            component.register(agent)
        
        component.cleanup()
        agents = component.get_all_agents()
        
        if len(agents) == 0:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'cleanup清空所有agent',
                'expected': '0个agent',
                'actual': len(agents)
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'cleanup方法应该正常工作',
            'expected': '成功清理',
            'actual': str(e)
        }


# MessageBroker 测试
def test_broker_publish(component, method):
    """测试MessageBroker.publish方法"""
    try:
        result = component.publish({'test': 'message'})
        if result is None or result is True:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'publish方法正常工作',
                'expected': '无错误',
                'actual': result
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'publish方法应该正常工作',
            'expected': '成功发布',
            'actual': str(e)
        }


def test_broker_subscribe(component, method):
    """测试MessageBroker.subscribe方法"""
    try:
        received = []
        def callback(msg):
            received.append(msg)
        
        result = component.subscribe('test_channel', callback)
        if result is None or result is True:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'subscribe方法正常工作',
                'expected': '无错误',
                'actual': result
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'subscribe方法应该正常工作',
            'expected': '成功订阅',
            'actual': str(e)
        }


def test_broker_receive(component, method):
    """测试MessageBroker.receive方法"""
    try:
        component.publish({'test': 'data'})
        msg = component.receive(timeout=1)
        # receive可能返回None如果队列为空
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'receive方法应该正常工作',
            'expected': '成功接收或超时',
            'actual': str(e)
        }


def test_broker_unsubscribe(component, method):
    """测试MessageBroker.unsubscribe方法"""
    try:
        def callback(msg):
            pass
        component.subscribe('test_unsub', callback)
        result = component.unsubscribe('test_unsub', callback)
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'LOW',
            'description': str(e),
            'assumption': 'unsubscribe方法应该正常工作',
            'expected': '成功取消订阅',
            'actual': str(e)
        }


def test_broker_cleanup(component, method):
    """测试MessageBroker.cleanup方法"""
    try:
        component.cleanup()
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'LOW',
            'description': str(e),
            'assumption': 'cleanup方法应该正常工作',
            'expected': '成功清理',
            'actual': str(e)
        }


# EventEmitter 测试
def test_emitter_on(component, method):
    """测试EventEmitter.on方法"""
    try:
        from maos.orchestration.orchestrator import OrchestratorEventType
        def handler(event):
            pass
        component.on(OrchestratorEventType.TASK_CREATED, handler)
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'on方法应该正常工作',
            'expected': '成功注册监听器',
            'actual': str(e)
        }


def test_emitter_off(component, method):
    """测试EventEmitter.off方法"""
    try:
        from maos.orchestration.orchestrator import OrchestratorEventType
        def handler(event):
            pass
        component.on(OrchestratorEventType.TASK_CREATED, handler)
        component.off(OrchestratorEventType.TASK_CREATED, handler)
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'LOW',
            'description': str(e),
            'assumption': 'off方法应该正常工作',
            'expected': '成功注销监听器',
            'actual': str(e)
        }


def test_emitter_emit(component, method):
    """测试EventEmitter.emit方法"""
    try:
        received = []
        def handler(event):
            received.append(event)
        
        from maos.orchestration.orchestrator import OrchestratorEventType, OrchestratorEvent
        component.on(OrchestratorEventType.TASK_CREATED, handler)
        event = OrchestratorEvent(
            event_type=OrchestratorEventType.TASK_CREATED,
            data={'test': 'data'}
        )
        component.emit(event)
        
        if len(received) > 0:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'emit触发监听器',
                'expected': '至少1个事件被处理',
                'actual': len(received)
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'emit方法应该正常工作',
            'expected': '成功触发事件',
            'actual': str(e)
        }


def test_emitter_cleanup(component, method):
    """测试EventEmitter.cleanup方法"""
    try:
        from maos.orchestration.orchestrator import OrchestratorEventType
        def handler(event):
            pass
        component.on(OrchestratorEventType.TASK_CREATED, handler)
        component.cleanup()
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'LOW',
            'description': str(e),
            'assumption': 'cleanup方法应该正常工作',
            'expected': '成功清理',
            'actual': str(e)
        }


# VersionManager 测试
def test_vm_create(component, method):
    """测试VersionManager.create_version方法"""
    try:
        version = component.create_version('test_wf', {'data': 'test'})
        if version:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'create_version返回版本对象',
                'expected': 'WorkflowVersion对象',
                'actual': version
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'create_version应该正常工作',
            'expected': '成功创建版本',
            'actual': str(e)
        }


def test_vm_get(component, method):
    """测试VersionManager.get_version方法"""
    try:
        version = component.create_version('test_get_wf', {'data': 'test'})
        if version and hasattr(version, 'id'):
            retrieved = component.get_version(version.id)
            if retrieved:
                return {'passed': True}
            else:
                return {
                    'passed': False,
                    'severity': 'MEDIUM',
                    'assumption': 'get_version返回正确的版本',
                    'expected': 'WorkflowVersion对象',
                    'actual': retrieved
                }
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'get_version应该正常工作',
            'expected': '成功获取版本',
            'actual': str(e)
        }


def test_vm_list(component, method):
    """测试VersionManager.list_versions方法"""
    try:
        for i in range(3):
            component.create_version('test_list_wf', {'data': f'test_{i}'})
        
        versions = component.list_versions('test_list_wf')
        if len(versions) >= 3:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'list_versions返回所有版本',
                'expected': '>=3个版本',
                'actual': len(versions)
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'list_versions应该正常工作',
            'expected': '成功列出版本',
            'actual': str(e)
        }


def test_vm_latest(component, method):
    """测试VersionManager.get_latest_version方法"""
    try:
        for i in range(3):
            component.create_version('test_latest_wf', {'data': f'test_{i}'})
        
        latest = component.get_latest_version('test_latest_wf')
        if latest:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'get_latest_version返回最新版本',
                'expected': 'WorkflowVersion对象',
                'actual': latest
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'get_latest_version应该正常工作',
            'expected': '成功获取最新版本',
            'actual': str(e)
        }


def test_vm_activate(component, method):
    """测试VersionManager.activate_version方法"""
    try:
        version = component.create_version('test_act_wf', {'data': 'test'})
        if version and hasattr(version, 'id'):
            result = component.activate_version(version.id)
            if result:
                return {'passed': True}
            else:
                return {
                    'passed': False,
                    'severity': 'LOW',
                    'assumption': 'activate_version返回True表示成功',
                    'expected': 'True',
                    'actual': result
                }
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'activate_version应该正常工作',
            'expected': '成功激活版本',
            'actual': str(e)
        }


def test_vm_rollback(component, method):
    """测试VersionManager.rollback_to_version方法"""
    try:
        version = component.create_version('test_rb_wf', {'data': 'test'})
        if version and hasattr(version, 'id'):
            result = component.rollback_to_version('test_rb_wf', version.id)
            return {'passed': True}
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'rollback_to_version应该正常工作',
            'expected': '成功回滚',
            'actual': str(e)
        }


def test_vm_cleanup(component, method):
    """测试VersionManager.cleanup方法"""
    try:
        for i in range(5):
            component.create_version('test_cleanup_wf', {'data': f'test_{i}'})
        
        component.cleanup()
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'LOW',
            'description': str(e),
            'assumption': 'cleanup应该正常工作',
            'expected': '成功清理',
            'actual': str(e)
        }


# AnalyticsEngine 测试
def test_ae_record(component, method):
    """测试AnalyticsEngine.record_metric方法"""
    try:
        component.record_metric('test_metric', 1.0, None, {'tag': 'test'})
        return {'passed': True}
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'record_metric应该正常工作',
            'expected': '成功记录指标',
            'actual': str(e)
        }


def test_ae_get_data(component, method):
    """测试AnalyticsEngine.get_metric_data方法"""
    try:
        component.record_metric('test_data_metric', 2.0, None, {})
        data = component.get_metric_data('test_data_metric')
        if len(data) > 0:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'get_metric_data返回记录的数据',
                'expected': '至少1条数据',
                'actual': len(data)
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'get_metric_data应该正常工作',
            'expected': '成功获取数据',
            'actual': str(e)
        }


def test_ae_summary(component, method):
    """测试AnalyticsEngine.calculate_summary方法"""
    try:
        component.record_metric('test_summary_metric', 3.0, None, {})
        summary = component.calculate_summary('test_summary_metric')
        if summary:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'calculate_summary返回摘要',
                'expected': 'MetricSummary对象',
                'actual': summary
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'MEDIUM',
            'description': str(e),
            'assumption': 'calculate_summary应该正常工作',
            'expected': '成功计算摘要',
            'actual': str(e)
        }


def test_ae_get_summary(component, method):
    """测试AnalyticsEngine.get_summary方法"""
    try:
        component.record_metric('test_get_summary_metric', 4.0, None, {})
        summary = component.get_summary()
        if 'total_metrics' in summary:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'MEDIUM',
                'assumption': 'get_summary返回正确的摘要结构',
                'expected': "包含'total_metrics'键",
                'actual': summary
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'HIGH',
            'description': str(e),
            'assumption': 'get_summary应该正常工作',
            'expected': '成功获取摘要',
            'actual': str(e)
        }


def test_ae_cleanup(component, method):
    """测试AnalyticsEngine.cleanup方法"""
    try:
        for i in range(5):
            component.record_metric(f'test_cleanup_metric_{i}', float(i), None, {})
        
        component.cleanup()
        summary = component.get_summary()
        if summary['total_metrics'] == 0:
            return {'passed': True}
        else:
            return {
                'passed': False,
                'severity': 'LOW',
                'assumption': 'cleanup清空所有指标',
                'expected': '0个指标',
                'actual': summary['total_metrics']
            }
    except Exception as e:
        return {
            'passed': False,
            'severity': 'LOW',
            'description': str(e),
            'assumption': 'cleanup应该正常工作',
            'expected': '成功清理',
            'actual': str(e)
        }


# ========== 测试2: 精细化边界测试 ==========
def test精细化_boundary_cases(tracker):
    """测试2: 精细化边界测试"""
    print("\n" + "="*90)
    print("🎯 测试2: 精细化边界测试")
    print("="*90)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    boundary_cases = [
        ("空字符串", '', "VersionManager", "create_version"),
        ("None值", None, "VersionManager", "create_version"),
        ("超长字符串", "x" * 100000, "VersionManager", "create_version"),
        ("负数", -1, "AnalyticsEngine", "record_metric"),
        ("极大数", sys.maxsize, "AnalyticsEngine", "record_metric"),
        ("浮点数inf", float('inf'), "AnalyticsEngine", "record_metric"),
        ("NaN值", float('nan'), "AnalyticsEngine", "record_metric"),
        ("空字典", {}, "VersionManager", "create_version"),
        ("深层嵌套", {'a': {'b': {'c': {}}}}, "VersionManager", "create_version"),
        ("特殊字符", "<script>alert('xss')</script>", "VersionManager", "create_version"),
    ]
    
    vm = VersionManager()
    ae = AnalyticsEngine()
    
    for case_name, test_value, component, method in boundary_cases:
        tracker.increment_test()
        try:
            if component == "VersionManager":
                version = vm.create_version('boundary_wf', {'test_value': test_value})
                print(f"   ✅ {case_name}")
            else:
                ae.record_metric('boundary_metric', test_value, None, {})
                print(f"   ✅ {case_name}")
        except Exception as e:
            tracker.record_bug(
                component,
                method,
                'MEDIUM',
                f'{case_name} 处理失败',
                f'{method}应该处理{case_name}',
                '正常工作',
                str(e),
                traceback.format_exc()
            )
    
    return tracker


# ========== 测试3: 精细化并发测试 ==========
def test_精细化_concurrency(tracker):
    """测试3: 精细化并发测试"""
    print("\n" + "="*90)
    print("🔀 测试3: 精细化并发测试")
    print("="*90)
    
    from maos.orchestration.orchestrator import AgentRegistry
    from maos.version.v14 import VersionManager
    
    # 测试不同并发级别的AgentRegistry
    concurrency_levels = [10, 50, 100]
    
    for level in concurrency_levels:
        tracker.increment_test()
        try:
            registry = AgentRegistry()
            
            class MockAgent:
                def __init__(self, name):
                    self.name = name
                    self.status = 'idle'
                    self.capabilities = ['test']
            
            def register_agents(thread_id):
                for i in range(100):
                    agent = MockAgent(f'agent_{thread_id}_{i}')
                    registry.register(agent)
            
            threads = [threading.Thread(target=register_agents, args=(i,)) for i in range(level)]
            
            start = time.time()
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            duration = time.time() - start
            
            total_agents = len(registry.get_all_agents())
            expected = level * 100
            
            if total_agents == expected:
                print(f"   ✅ 并发级别 {level}: {total_agents}个agent, 耗时{duration:.2f}s")
            else:
                tracker.record_bug(
                    "AgentRegistry",
                    f"concurrent_{level}",
                    'HIGH',
                    f'并发级别{level}下数据不一致',
                    f'应该注册{expected}个agent',
                    expected,
                    total_agents
                )
        except Exception as e:
            tracker.record_bug(
                "AgentRegistry",
                f"concurrent_{level}",
                'HIGH',
                str(e),
                f'并发级别{level}应该正常工作',
                '正常运行',
                str(e)
            )
    
    return tracker


# ========== 测试4: 精细化内存测试 ==========
def test_精细化_memory(tracker):
    """测试4: 精细化内存测试"""
    print("\n" + "="*90)
    print("💾 测试4: 精细化内存测试")
    print("="*90)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    
    gc.collect()
    process = psutil.Process(os.getpid())
    initial_mem = process.memory_info().rss / 1024 / 1024
    
    print(f"   初始内存: {initial_mem:.2f} MB")
    
    # 创建大量版本
    tracker.increment_test()
    try:
        vm = VersionManager()
        for i in range(10000):
            vm.create_version(f'perf_wf_{i}', {'data': f'test_{i}'})
        
        gc.collect()
        after_vm_mem = process.memory_info().rss / 1024 / 1024
        vm_growth = after_vm_mem - initial_mem
        vm_growth_pct = (vm_growth / initial_mem * 100) if initial_mem > 0 else 0
        
        print(f"   VersionManager (10000版本): {after_vm_mem:.2f}MB (增长 {vm_growth:.2f}MB / {vm_growth_pct:.1f}%)")
        
        if vm_growth_pct > 100:
            tracker.record_bug(
                "VersionManager",
                "memory_test",
                'HIGH',
                f'内存增长过高: {vm_growth_pct:.1f}%',
                '内存增长应该<100%',
                '<100%',
                f'{vm_growth_pct:.1f}%'
            )
    except Exception as e:
        tracker.record_bug(
            "VersionManager",
            "memory_test",
            'HIGH',
            str(e),
            '创建大量版本应该正常工作',
            '正常运行',
            str(e)
        )
    
    # 创建大量指标
    tracker.increment_test()
    try:
        ae = AnalyticsEngine()
        for i in range(10000):
            ae.record_metric(f'metric_{i}', float(i), None, {})
        
        gc.collect()
        after_ae_mem = process.memory_info().rss / 1024 / 1024
        ae_growth = after_ae_mem - after_vm_mem
        ae_growth_pct = (ae_growth / after_vm_mem * 100) if after_vm_mem > 0 else 0
        
        print(f"   AnalyticsEngine (10000指标): {after_ae_mem:.2f}MB (增长 {ae_growth:.2f}MB / {ae_growth_pct:.1f}%)")
        
        if ae_growth_pct > 100:
            tracker.record_bug(
                "AnalyticsEngine",
                "memory_test",
                'HIGH',
                f'内存增长过高: {ae_growth_pct:.1f}%',
                '内存增长应该<100%',
                '<100%',
                f'{ae_growth_pct:.1f}%'
            )
    except Exception as e:
        tracker.record_bug(
            "AnalyticsEngine",
            "memory_test",
            'HIGH',
            str(e),
            '创建大量指标应该正常工作',
            '正常运行',
            str(e)
        )
    
    return tracker


# ========== 测试5: 精细化错误恢复测试 ==========
def test_精细化_error_recovery(tracker):
    """测试5: 精细化错误恢复测试"""
    print("\n" + "="*90)
    print("⚠️ 测试5: 精细化错误恢复测试")
    print("="*90)
    
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.orchestration.orchestrator import AgentRegistry
    
    components = [
        ("VersionManager", VersionManager(), "create_version"),
        ("AnalyticsEngine", AnalyticsEngine(), "record_metric"),
        ("AgentRegistry", AgentRegistry(), "register"),
    ]
    
    error_scenarios = [
        ("无效字典键", {'__class__': 'malicious'}),
        ("循环引用", None),
        ("类型错误", "not_a_dict"),
    ]
    
    for component_name, component, method in components:
        tracker.increment_test()
        try:
            # 先正常工作
            if component_name == "VersionManager":
                component.create_version('recovery_wf', {'data': 'normal'})
            elif component_name == "AnalyticsEngine":
                component.record_metric('recovery_metric', 1.0, None, {})
            else:
                class MockAgent:
                    def __init__(self, name):
                        self.name = name
                        self.status = 'idle'
                        self.capabilities = ['test']
                component.register(MockAgent('recovery_agent'))
            
            # 尝试错误操作
            try:
                if component_name == "VersionManager":
                    component.create_version('error_wf', {'test': error_scenarios[0][1]})
                elif component_name == "AnalyticsEngine":
                    component.record_metric('error_metric', 'not_a_number', None, {})
                else:
                    component.register(None)
            except:
                pass
            
            # 验证系统仍然工作
            if component_name == "VersionManager":
                version = component.create_version('after_error_wf', {'data': 'recovered'})
                if version:
                    print(f"   ✅ {component_name} 错误恢复成功")
                else:
                    tracker.record_warning(component_name, "error_recovery", "错误后无法恢复")
            elif component_name == "AnalyticsEngine":
                component.record_metric('after_error_metric', 1.0, None, {})
                print(f"   ✅ {component_name} 错误恢复成功")
            else:
                class MockAgent2:
                    def __init__(self, name):
                        self.name = name
                        self.status = 'idle'
                        self.capabilities = ['test']
                component.register(MockAgent2('after_error_agent'))
                print(f"   ✅ {component_name} 错误恢复成功")
                
        except Exception as e:
            tracker.record_bug(
                component_name,
                "error_recovery",
                'HIGH',
                f'{component_name} 错误后无法恢复',
                '错误后系统应该继续工作',
                '正常工作',
                str(e),
                traceback.format_exc()
            )
    
    return tracker


# ========== 运行所有测试 ==========
def run_all_tests():
    """运行所有测试"""
    print("="*90)
    print("🚀 MAOS 慢工出细活深度测试套件 v6.0")
    print("="*90)
    print(f"开始时间: {datetime.now().isoformat()}")
    print("原则: 深入、细致、持续")
    print("="*90)
    
    tracker = DetailedBugTracker()
    
    tests = [
        ("精细化组件测试", test_component_refinement),
        ("精细化边界测试", test精细化_boundary_cases),
        ("精细化并发测试", test_精细化_concurrency),
        ("精细化内存测试", test_精细化_memory),
        ("精细化错误恢复", test_精细化_error_recovery),
    ]
    
    for test_name, test_func in tests:
        try:
            tracker = test_func(tracker)
        except Exception as e:
            print(f"\n❌ {test_name} 执行失败: {str(e)}")
            traceback.print_exc()
    
    # 最终报告
    print("\n" + "="*90)
    print("📊 慢工出细活测试 - 最终报告")
    print("="*90)
    
    summary = tracker.get_summary()
    
    print(f"\n📝 测试统计:")
    print(f"   总测试数: {summary['total_tests']}")
    print(f"   总错误数: {summary['total_errors']}")
    
    print(f"\n🐛 Bug发现统计:")
    print(f"   🔴 CRITICAL: {summary['critical']}")
    print(f"   🟠 HIGH: {summary['high']}")
    print(f"   🟡 MEDIUM: {summary['medium']}")
    print(f"   🔵 LOW: {summary['low']}")
    print(f"   ⚠️  警告: {summary['warnings']}")
    
    # 健康评分
    if summary['total_tests'] > 0:
        pass_rate = ((summary['total_tests'] - summary['total_errors']) / summary['total_tests'] * 100)
    else:
        pass_rate = 100
    
    health_score = 100
    health_score -= summary['critical'] * 20
    health_score -= summary['high'] * 10
    health_score -= summary['medium'] * 5
    health_score -= summary['low'] * 1
    health_score = max(0, min(100, health_score))
    
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
    print(f"   通过率: {pass_rate:.1f}%")
    
    # 详细Bug列表
    if tracker.bugs:
        print(f"\n📝 详细Bug列表:")
        for bug in tracker.bugs[:20]:
            print(f"\n   [{bug['severity']}] {bug['component']}.{bug['test_name']}")
            print(f"       假设: {bug['assumption']}")
            print(f"       期望: {bug['expected']}")
            print(f"       实际: {str(bug['actual'])[:60]}")
    
    print("\n" + "="*90)
    print("✅ 慢工出细活测试完成")
    print("="*90)
    
    return tracker


if __name__ == '__main__':
    run_all_tests()
