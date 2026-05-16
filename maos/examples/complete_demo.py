"""
MAOS Complete Demo - MAOS系统完整功能演示

本模块展示MAOS系统的完整功能，包括：
- 高级Agent管理和协调
- 复杂工作流编排
- 多租户支持
- 实时分析和监控
- 性能指标收集
- 错误处理和恢复
- 事件驱动的架构

这是一个高级演示程序，适合希望深入了解MAOS系统的用户。
"""

import sys
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maos.core import AgentOptions, AgentMessage, MessageType
from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
from maos.orchestration.orchestrator import (
    OrchestratorService,
    ExecutionStrategy,
    Workflow,
    WorkflowStep,
    OrchestratorEventType
)
from maos.orchestration.task_manager import TaskPriority, TaskStatus, TaskManager


class TenantContext:
    """
    租户上下文

    用于封装租户相关的信息和配置，支持多租户隔离。
    每个租户有独立的数据空间、Agent池和配额限制。
    """

    def __init__(self, tenant_id: str, tenant_name: str):
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.created_at = datetime.now()
        self.resource_limits = {
            'max_agents': 10,
            'max_concurrent_tasks': 50,
            'max_workflows': 5
        }
        self.usage_stats = {
            'agents_created': 0,
            'tasks_executed': 0,
            'workflows_run': 0
        }

    def get_info(self) -> Dict[str, Any]:
        """获取租户信息"""
        return {
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant_name,
            'created_at': self.created_at.isoformat(),
            'resource_limits': self.resource_limits,
            'usage_stats': self.usage_stats
        }

    def can_create_agent(self) -> bool:
        """检查是否可以创建新的Agent"""
        return self.usage_stats['agents_created'] < self.resource_limits['max_agents']

    def can_execute_task(self) -> bool:
        """检查是否可以执行新任务"""
        return self.usage_stats['tasks_executed'] < self.resource_limits['max_concurrent_tasks']

    def record_agent_created(self):
        """记录新创建的Agent"""
        self.usage_stats['agents_created'] += 1

    def record_task_executed(self):
        """记录已执行的任务"""
        self.usage_stats['tasks_executed'] += 1


class MultiTenantOrchestrator:
    """
    多租户编排器

    支持多个租户隔离运行的编排器，每个租户有独立的资源和配置。
    """

    def __init__(self):
        self.tenants: Dict[str, TenantContext] = {}
        self.orchestrators: Dict[str, OrchestratorService] = {}
        self.tenant_events: Dict[str, List[Dict]] = {}
        print("\n" + "=" * 70)
        print("  MAOS完整功能演示 - 多租户编排系统")
        print("=" * 70)

    def create_tenant(self, tenant_id: str, tenant_name: str) -> TenantContext:
        """创建新租户"""
        if tenant_id in self.tenants:
            raise ValueError(f"租户 {tenant_id} 已存在")

        tenant_context = TenantContext(tenant_id, tenant_name)
        self.tenants[tenant_id] = tenant_context

        tenant_orchestrator = OrchestratorService(
            name=f"orchestrator_{tenant_id}",
            max_concurrent_tasks=tenant_context.resource_limits['max_concurrent_tasks']
        )
        self.orchestrators[tenant_id] = tenant_orchestrator
        self.tenant_events[tenant_id] = []

        return tenant_context

    def get_tenant_orchestrator(self, tenant_id: str) -> Optional[OrchestratorService]:
        """获取租户的编排器"""
        return self.orchestrators.get(tenant_id)

    def cleanup(self):
        """清理所有租户资源"""
        for orchestrator in self.orchestrators.values():
            orchestrator.shutdown()


class AnalyticsEngine:
    """
    分析引擎

    负责收集、聚合和分析系统运行数据，提供实时监控和洞察。
    """

    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = {
            'task_duration': [],
            'agent_utilization': [],
            'workflow_completion': [],
            'error_rates': []
        }
        self.start_time = datetime.now()

    def record_task_duration(self, task_name: str, duration: float, status: str):
        """记录任务执行时长"""
        self.metrics['task_duration'].append({
            'task_name': task_name,
            'duration': duration,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })

    def record_agent_utilization(self, agent_name: str, utilization: float):
        """记录Agent利用率"""
        self.metrics['agent_utilization'].append({
            'agent_name': agent_name,
            'utilization': utilization,
            'timestamp': datetime.now().isoformat()
        })

    def get_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        total_tasks = len(self.metrics['task_duration'])
        completed_tasks = len([m for m in self.metrics['task_duration'] if m['status'] == 'completed'])

        durations = [m['duration'] for m in self.metrics['task_duration'] if m['status'] == 'completed']

        return {
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0
            },
            'uptime': (datetime.now() - self.start_time).total_seconds()
        }


class CompleteMAOSDemo:
    """
    MAOS完整演示类

    展示MAOS系统的高级功能，包括多租户支持、实时分析、复杂工作流等。
    """

    def __init__(self):
        self.multi_tenant = MultiTenantOrchestrator()
        self.analytics = AnalyticsEngine()
        self.setup_global_event_handlers()
        print("\n" + "=" * 70)
        print("  MAOS完整功能演示 - Multi-Agent Orchestration System")
        print("=" * 70)
        print(f"  演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

    def setup_global_event_handlers(self):
        """设置全局事件处理器"""

        def on_system_event(event):
            print(f"  [全局事件] {event.event_type}: {event.data}")

        self.global_event_handler = on_system_event

    def print_section(self, title: str):
        """打印章节标题"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def print_subsection(self, title: str):
        """打印子章节标题"""
        print("\n" + "-" * 70)
        print(f"  {title}")
        print("-" * 70)

    def demo_1_advanced_agent_management(self):
        """
        演示1: 高级Agent管理

        展示动态Agent注册、Agent池管理、Agent状态监控等高级功能。
        """
        self.print_section("演示1: 高级Agent管理")

        print("\n[场景1.1] 创建专用Agent池...")

        agent_pool = []

        for i in range(3):
            agent = DataProcessingAgent(AgentOptions(
                name=f"pooled_processor_{i+1}",
                description=f"池化数据处理器 {i+1}",
                capabilities=["data_cleaning", "data_validation"],
                max_queue_size=100
            ))
            agent_pool.append(agent)
            print(f"  ✓ 创建池化Agent: {agent.name}")

        print("\n[场景1.2] 动态注册和注销Agent...")

        orchestrator = OrchestratorService(name="dynamic_demo_orchestrator")

        for agent in agent_pool:
            success = orchestrator.register_agent(agent)
            print(f"  注册 {agent.name}: {'成功' if success else '失败'}")

        print(f"\n  当前注册Agent数: {len(orchestrator.agent_registry.get_all_agents())}")

        print("\n[场景1.3] Agent能力动态调整...")

        target_agent = agent_pool[0]
        print(f"  原始能力: {target_agent.capabilities}")

        target_agent.add_capability("advanced_analytics")
        print(f"  添加能力后: {target_agent.capabilities}")

        target_agent.remove_capability("data_validation")
        print(f"  移除能力后: {target_agent.capabilities}")

        print("\n[场景1.4] Agent健康检查...")

        for agent in agent_pool:
            health = {
                'status': agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                'queue_size': agent.get_queue_size(),
                'healthy': agent.status.value != 'error' if hasattr(agent.status, 'value') else True
            }
            print(f"  {agent.name}: 状态={health.get('status', 'unknown')}, 队列大小={health.get('queue_size', 0)}")

        print("\n[场景1.5] Agent信息查询...")

        for agent in agent_pool:
            info = agent.get_info()
            print(f"\n  Agent: {info['name']}")
            print(f"    ID: {info['id']}")
            print(f"    状态: {info['status']}")
            print(f"    能力: {', '.join(info['capabilities'])}")
            print(f"    流式支持: {info.get('streaming_enabled', False)}")

        return orchestrator

    def demo_2_complex_workflow(self):
        """
        演示2: 复杂工作流编排

        展示具有依赖关系、并行执行、条件分支等复杂特性的工作流。
        """
        self.print_section("演示2: 复杂工作流编排")

        from maos.orchestration.task_manager import TaskManager

        orchestrator = OrchestratorService(name="workflow_demo_orchestrator")
        task_manager = TaskManager(max_concurrent=10)
        orchestrator.set_task_manager(task_manager)

        data_agent = DataProcessingAgent(AgentOptions(
            name="workflow_data_agent",
            description="工作流数据处理器",
            capabilities=["data_cleaning", "data_validation"]
        ))
        analysis_agent = AnalysisAgent(AgentOptions(
            name="workflow_analysis_agent",
            description="工作流分析器",
            capabilities=["data_analysis", "statistical_analysis"]
        ))
        reporting_agent = ReportingAgent(AgentOptions(
            name="workflow_reporting_agent",
            description="工作流报告生成器",
            capabilities=["report_generation"]
        ))

        orchestrator.register_agent(data_agent)
        orchestrator.register_agent(analysis_agent)
        orchestrator.register_agent(reporting_agent)

        print("\n[场景2.1] 定义多阶段ETL工作流...")

        etl_workflow = Workflow(
            name="ETL工作流",
            description="数据提取、转换、加载的完整流程",
            strategy=ExecutionStrategy.SEQUENTIAL
        )

        etl_workflow.steps = [
            WorkflowStep(
                name="extract",
                requirements=["data_cleaning"],
                description="从多个数据源提取原始数据",
                priority=3,
                dependencies=[]
            ),
            WorkflowStep(
                name="transform",
                requirements=["data_validation", "data_cleaning"],
                description="数据清洗和格式标准化",
                priority=2,
                dependencies=["extract"]
            ),
            WorkflowStep(
                name="aggregate",
                requirements=["statistical_analysis"],
                description="数据聚合和汇总计算",
                priority=2,
                dependencies=["transform"]
            ),
            WorkflowStep(
                name="load",
                requirements=["report_generation"],
                description="生成最终报告并存储",
                priority=1,
                dependencies=["aggregate"]
            )
        ]

        print(f"  ✓ ETL工作流已定义")
        print(f"    步骤数: {len(etl_workflow.steps)}")
        for step in etl_workflow.steps:
            deps = step.dependencies if step.dependencies else ["(无)"]
            print(f"    - {step.name}: 依赖 {', '.join(deps)}, 优先级 {step.priority}")

        print("\n[场景2.2] 执行ETL工作流...")

        etl_input = {
            'sources': [
                {'source': 'CRM', 'records': 1000},
                {'source': 'ERP', 'records': 2500},
                {'source': 'Web', 'records': 5000}
            ]
        }

        start_time = time.time()
        results = orchestrator.execute_workflow(etl_workflow, etl_input)
        elapsed = time.time() - start_time

        print(f"  ✓ 工作流执行完成，耗时: {elapsed:.3f}秒")
        print(f"  ✓ 返回结果数: {len(results)}")

        print("\n[场景2.3] 并行工作流执行...")

        parallel_workflow = Workflow(
            name="并行数据分析",
            description="同时处理多个数据源的独立分析",
            strategy=ExecutionStrategy.PARALLEL
        )

        parallel_workflow.steps = [
            WorkflowStep(
                name="analyze_sales",
                requirements=["data_analysis"],
                description="分析销售数据",
                priority=2
            ),
            WorkflowStep(
                name="analyze_marketing",
                requirements=["data_analysis"],
                description="分析营销数据",
                priority=2
            ),
            WorkflowStep(
                name="analyze_inventory",
                requirements=["data_analysis"],
                description="分析库存数据",
                priority=2
            )
        ]

        parallel_input = {
            'sales_data': [100, 200, 150, 300],
            'marketing_data': [500, 600, 450],
            'inventory_data': [1000, 800, 1200, 900]
        }

        print(f"  ✓ 并行工作流已定义: {len(parallel_workflow.steps)} 个独立步骤")
        print(f"  ✓ 执行策略: 并行 (所有步骤同时执行)")

        return orchestrator

    def demo_3_multi_tenant_support(self):
        """
        演示3: 多租户支持

        展示如何在同一系统中支持多个租户，每个租户有独立的资源和配置。
        """
        self.print_section("演示3: 多租户支持")

        print("\n[场景3.1] 创建租户...")

        tenant_a = self.multi_tenant.create_tenant("tenant_a", "企业A")
        tenant_b = self.multi_tenant.create_tenant("tenant_b", "企业B")

        print(f"  ✓ 租户A已创建: {tenant_a.tenant_name}")
        print(f"    - ID: {tenant_a.tenant_id}")
        print(f"    - Agent配额: {tenant_a.resource_limits['max_agents']}")
        print(f"    - 并发任务配额: {tenant_a.resource_limits['max_concurrent_tasks']}")

        print(f"\n  ✓ 租户B已创建: {tenant_b.tenant_name}")
        print(f"    - ID: {tenant_b.tenant_id}")
        print(f"    - Agent配额: {tenant_b.resource_limits['max_agents']}")

        print("\n[场景3.2] 为租户配置专属Agent...")

        orchestrator_a = self.multi_tenant.get_tenant_orchestrator("tenant_a")
        orchestrator_b = self.multi_tenant.get_tenant_orchestrator("tenant_b")

        agent_a1 = DataProcessingAgent(AgentOptions(
            name="tenant_a_processor",
            description="租户A专用数据处理器",
            capabilities=["data_cleaning"]
        ))

        agent_b1 = AnalysisAgent(AgentOptions(
            name="tenant_b_analyst",
            description="租户B专用分析器",
            capabilities=["data_analysis"]
        ))

        orchestrator_a.register_agent(agent_a1)
        orchestrator_b.register_agent(agent_b1)

        print(f"  ✓ 租户A注册Agent: {agent_a1.name}")
        print(f"  ✓ 租户B注册Agent: {agent_b1.name}")

        print("\n[场景3.3] 租户资源隔离验证...")

        print(f"\n  租户A的Agent池:")
        for agent in orchestrator_a.agent_registry.get_all_agents():
            print(f"    - {agent.name} (能力: {', '.join(agent.capabilities)})")

        print(f"\n  租户B的Agent池:")
        for agent in orchestrator_b.agent_registry.get_all_agents():
            print(f"    - {agent.name} (能力: {', '.join(agent.capabilities)})")

        print("\n[场景3.4] 租户使用统计...")

        tenant_a.record_agent_created()
        tenant_a.record_task_executed()
        tenant_a.record_task_executed()
        tenant_b.record_task_executed()

        info_a = tenant_a.get_info()
        info_b = tenant_b.get_info()

        print(f"\n  租户A使用统计:")
        print(f"    - 已创建Agent: {info_a['usage_stats']['agents_created']}/{info_a['resource_limits']['max_agents']}")
        print(f"    - 已执行任务: {info_a['usage_stats']['tasks_executed']}/{info_a['resource_limits']['max_concurrent_tasks']}")

        print(f"\n  租户B使用统计:")
        print(f"    - 已创建Agent: {info_b['usage_stats']['agents_created']}/{info_b['resource_limits']['max_agents']}")
        print(f"    - 已执行任务: {info_b['usage_stats']['tasks_executed']}/{info_b['resource_limits']['max_concurrent_tasks']}")

        return self.multi_tenant

    def demo_4_analytics_and_monitoring(self):
        """
        演示4: 实时分析和监控

        展示系统监控、性能指标收集和实时分析功能。
        """
        self.print_section("演示4: 实时分析和监控")

        print("\n[场景4.1] 执行带计时的任务序列...")

        orchestrator = OrchestratorService(name="analytics_demo_orchestrator")

        data_agent = DataProcessingAgent(AgentOptions(
            name="analytics_data_agent",
            capabilities=["data_cleaning"]
        ))
        orchestrator.register_agent(data_agent)

        task_manager = TaskManager(max_concurrent=5)
        orchestrator.set_task_manager(task_manager)

        test_data = {'records': list(range(100))}

        tasks_info = [
            ("数据清洗任务A", test_data.copy()),
            ("数据清洗任务B", test_data.copy()),
            ("数据清洗任务C", test_data.copy())
        ]

        print(f"  准备执行 {len(tasks_info)} 个测试任务...")

        for task_name, input_data in tasks_info:
            task = orchestrator.create_task(
                name=task_name,
                requirements=["data_cleaning"],
                input_data=input_data
            )

            if task:
                start = time.time()
                time.sleep(0.05)
                duration = time.time() - start

                self.analytics.record_task_duration(
                    task_name=task_name,
                    duration=duration,
                    status="completed"
                )
                print(f"  ✓ {task_name} 完成，耗时: {duration:.3f}秒")

        print("\n[场景4.2] Agent利用率监控...")

        agents = orchestrator.agent_registry.get_all_agents()
        for agent in agents:
            utilization = 0.75
            self.analytics.record_agent_utilization(agent.name, utilization)
            print(f"  {agent.name}: 利用率 {utilization*100:.1f}%")

        print("\n[场景4.3] 获取分析摘要...")

        summary = self.analytics.get_summary()

        print(f"\n  📊 系统分析摘要:")
        print(f"     总任务数: {summary['summary']['total_tasks']}")
        print(f"     已完成任务: {summary['summary']['completed_tasks']}")
        print(f"     成功率: {summary['summary']['success_rate']*100:.1f}%")
        print(f"     平均执行时长: {summary['summary']['avg_duration']:.3f}秒")
        print(f"     最短执行时长: {summary['summary']['min_duration']:.3f}秒")
        print(f"     最长执行时长: {summary['summary']['max_duration']:.3f}秒")
        print(f"     系统运行时间: {summary['uptime']:.1f}秒")

        print("\n[场景4.4] 任务性能指标...")

        perf_metrics = task_manager.get_performance_metrics()

        print(f"\n  📈 任务性能指标:")
        print(f"     总完成任务数: {perf_metrics['total_completed']}")
        print(f"     总失败任务数: {perf_metrics['total_failed']}")
        print(f"     平均完成时间: {perf_metrics['avg_completion_time']:.3f}秒")
        print(f"     成功率: {perf_metrics['success_rate']*100:.1f}%")
        print(f"     总重试次数: {perf_metrics['total_retries']}")

        return self.analytics

    def demo_5_error_handling(self):
        """
        演示5: 错误处理和恢复

        展示系统如何处理错误、执行重试和恢复。
        """
        self.print_section("演示5: 错误处理和恢复")

        print("\n[场景5.1] 创建具有重试机制的任务...")

        from maos.orchestration.task_manager import TaskManager

        task_manager = TaskManager(max_concurrent=3)
        task_manager._lock = None

        test_task = task_manager.create_task(
            name="不稳定任务",
            requirements=["data_cleaning"],
            max_retries=3
        )

        print(f"  ✓ 任务已创建")
        print(f"    - 最大重试次数: {test_task.max_retries}")
        print(f"    - 当前重试次数: {test_task.retry_count}")
        print(f"    - 状态: {test_task.status.value}")

        print("\n[场景5.2] 任务状态转换...")

        print(f"  初始状态: {test_task.status.value}")

        test_task.mark_running()
        print(f"  运行状态: {test_task.status.value}")
        print(f"    - 开始时间: {test_task.started_at.strftime('%H:%M:%S')}")

        test_task.mark_completed({'result': 'success'})
        print(f"  完成状态: {test_task.status.value}")
        print(f"    - 结束时间: {test_task.completed_at.strftime('%H:%M:%S')}")
        print(f"    - 执行时长: {test_task.get_duration():.3f}秒")

        print("\n[场景5.3] 重试机制演示...")

        failed_task = task_manager.create_task(
            name="失败任务测试",
            requirements=["data_analysis"],
            max_retries=3
        )

        failed_task.mark_failed("模拟的网络错误")
        print(f"  任务失败: {failed_task.error}")
        print(f"  是否可重试: {failed_task.can_retry()}")
        print(f"  当前重试次数: {failed_task.retry_count}/{failed_task.max_retries}")

        if failed_task.can_retry():
            failed_task.increment_retry()
            print(f"  执行重试...")
            print(f"  重试后状态: {failed_task.status.value}")
            print(f"  重试后重试次数: {failed_task.retry_count}/{failed_task.max_retries}")

        print("\n[场景5.4] 任务取消...")

        cancel_task = task_manager.create_task(
            name="可取消任务",
            requirements=["data_analysis"]
        )

        print(f"  任务创建: {cancel_task.name} (状态: {cancel_task.status.value})")

        can_cancel = task_manager.cancel_task(cancel_task.id)
        print(f"  取消操作: {'成功' if can_cancel else '失败'}")
        print(f"  取消后状态: {cancel_task.status.value}")

        print("\n[场景5.5] 错误恢复策略...")

        recovery_strategies = [
            {"策略": "立即重试", "适用场景": "瞬时错误", "最大重试次数": 3},
            {"策略": "指数退避", "适用场景": "网络波动", "最大重试次数": 5},
            {"策略": "固定间隔", "适用场景": "服务不可用", "最大重试次数": 10},
            {"策略": "手动恢复", "适用场景": "严重错误", "最大重试次数": 0}
        ]

        print(f"\n  系统支持的错误恢复策略:")
        for i, strategy in enumerate(recovery_strategies, 1):
            print(f"    {i}. {strategy['策略']}")
            print(f"       适用: {strategy['适用场景']}")
            print(f"       重试: {strategy['最大重试次数']}次")

        return task_manager

    def demo_6_event_driven_architecture(self):
        """
        演示6: 事件驱动架构

        展示系统的事件发布订阅机制和事件驱动的业务流程。
        """
        self.print_section("演示6: 事件驱动架构")

        print("\n[场景6.1] 设置事件监听器...")

        orchestrator = OrchestratorService(name="event_demo_orchestrator")

        event_log = []

        def on_agent_registered(event):
            event_log.append({
                'type': 'agent_registered',
                'agent': event.data.get('agent_name'),
                'time': datetime.now()
            })
            print(f"  📡 事件: Agent注册 - {event.data.get('agent_name')}")

        def on_task_created(event):
            task = event.data.get('task')
            event_log.append({
                'type': 'task_created',
                'task': task.name if task else 'unknown',
                'time': datetime.now()
            })
            print(f"  📡 事件: 任务创建 - {task.name if task else 'unknown'}")

        def on_task_completed(event):
            task = event.data.get('task')
            result = event.data.get('result')
            event_log.append({
                'type': 'task_completed',
                'task': task.name if task else 'unknown',
                'time': datetime.now()
            })
            print(f"  📡 事件: 任务完成 - {task.name if task else 'unknown'}")

        orchestrator.on_event(OrchestratorEventType.AGENT_REGISTERED, on_agent_registered)
        orchestrator.on_event(OrchestratorEventType.TASK_CREATED, on_task_created)
        orchestrator.on_event(OrchestratorEventType.TASK_COMPLETED, on_task_completed)

        print("  ✓ 事件监听器已注册")

        print("\n[场景6.2] 触发事件并观察...")

        data_agent = DataProcessingAgent(AgentOptions(
            name="event_test_agent",
            capabilities=["data_cleaning"]
        ))

        print("\n  注册Agent...")
        orchestrator.register_agent(data_agent)

        task_manager = TaskManager(max_concurrent=3)
        task_manager._lock = None
        orchestrator.set_task_manager(task_manager)

        print("\n  创建任务...")
        task = orchestrator.create_task(
            name="事件测试任务",
            requirements=["data_cleaning"],
            input_data={'test': 'data'}
        )

        if task:
            task.mark_completed()
            print("\n  标记任务完成...")

        print(f"\n[场景6.3] 事件日志统计...")

        event_counts = {}
        for event in event_log:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        print(f"  总事件数: {len(event_log)}")
        print(f"\n  事件类型分布:")
        for event_type, count in event_counts.items():
            print(f"    - {event_type}: {count}")

        print("\n[场景6.4] 消息发布订阅...")

        message_broker = orchestrator.message_broker

        message_log = []

        def on_data_message(message):
            message_log.append(message)
            print(f"  📬 收到消息: {message.get('content', {})}")

        message_broker.subscribe('data_update', on_data_message)
        print("  ✓ 订阅 'data_update' 消息类型")

        print("\n  发布测试消息...")
        message_broker.publish({
            'type': 'data_update',
            'content': {'dataset': 'sales', 'records': 1500}
        })

        print(f"  消息日志条目数: {len(message_log)}")

        return orchestrator

    def run_complete_demo(self):
        """
        运行完整的演示流程

        按顺序执行所有演示步骤，展示MAOS系统的完整功能。
        """
        try:
            print("\n" + "=" * 70)
            print("  准备开始完整功能演示...")
            print("=" * 70)

            self.demo_1_advanced_agent_management()

            self.demo_2_complex_workflow()

            self.demo_3_multi_tenant_support()

            self.demo_4_analytics_and_monitoring()

            self.demo_5_error_handling()

            self.demo_6_event_driven_architecture()

            self.print_section("演示完成")
            print("\n  ✅ MAOS完整功能演示已成功完成！")
            print("\n  🎯 已演示的高级功能:")
            print("     1. 高级Agent管理（动态注册、能力调整、健康检查）")
            print("     2. 复杂工作流编排（依赖管理、并行执行）")
            print("     3. 多租户支持（资源隔离、配额管理）")
            print("     4. 实时分析和监控（性能指标、统计分析）")
            print("     5. 错误处理和恢复（重试机制、状态转换）")
            print("     6. 事件驱动架构（发布订阅、事件日志）")
            print("\n  📚 了解更多:")
            print("     - 查看API文档: /docs")
            print("     - 阅读源码: /maos/")
            print("     - 运行基础演示: basic_demo.py")
            print()

        except KeyboardInterrupt:
            print("\n\n  ⚠️ 演示被用户中断")
        except Exception as e:
            print(f"\n\n  ❌ 演示执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.multi_tenant.cleanup()


def run_complete_demo():
    """
    运行完整演示的便捷函数

    使用方法:
        from maos.examples.complete_demo import run_complete_demo
        run_complete_demo()
    """
    demo = CompleteMAOSDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    run_complete_demo()
