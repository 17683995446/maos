"""
MAOS Basic Demo - MAOS系统基础演示

本模块展示MAOS系统的核心功能，包括：
- Agent的创建、注册和管理
- 任务的创建、调度和执行
- 工作流的定义和执行
- 系统状态的监控和查看

这是一个入门级的演示程序，适合初学者快速了解MAOS系统。
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maos.core import AgentOptions
from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
from maos.orchestration.orchestrator import OrchestratorService, ExecutionStrategy, Workflow, WorkflowStep, OrchestratorEventType
from maos.orchestration.task_manager import TaskPriority, TaskStatus


class BasicMAOSDemo:
    """
    MAOS基础演示类

    演示MAOS系统的核心功能，包括Agent管理、任务执行和工作流编排。
    """

    def __init__(self):
        """初始化演示环境"""
        self.orchestrator = OrchestratorService(name="basic_demo_orchestrator")
        self.setup_event_handlers()
        print("\n" + "=" * 70)
        print("  MAOS基础演示 - Multi-Agent Orchestration System")
        print("=" * 70)
        print(f"  演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

    def setup_event_handlers(self):
        """设置事件处理器，用于演示过程中的状态跟踪"""

        def on_agent_registered(event):
            try:
                data = event.data if hasattr(event, 'data') else {}
                agent = data.get('agent')
                if agent:
                    print(f"  [事件] Agent已注册: {agent.name}")
            except Exception as e:
                print(f"  [事件处理错误] agent_registered: {e}")

        def on_task_created(event):
            try:
                data = event.data if hasattr(event, 'data') else {}
                task = data.get('task')
                if task:
                    print(f"  [事件] 任务已创建: {task.name}")
            except Exception as e:
                print(f"  [事件处理错误] task_created: {e}")

        def on_task_assigned(event):
            try:
                data = event.data if hasattr(event, 'data') else {}
                task = data.get('task')
                agent_name = data.get('agent_name')
                if task and agent_name:
                    print(f"  [事件] 任务已分配: {task.name} -> {agent_name}")
            except Exception as e:
                print(f"  [事件处理错误] task_assigned: {e}")

        def on_task_completed(event):
            try:
                data = event.data if hasattr(event, 'data') else {}
                task = data.get('task')
                if task:
                    print(f"  [事件] 任务已完成: {task.name}")
            except Exception as e:
                print(f"  [事件处理错误] task_completed: {e}")

        def on_task_failed(event):
            try:
                data = event.data if hasattr(event, 'data') else {}
                task = data.get('task')
                error = data.get('error')
                if task:
                    print(f"  [事件] 任务失败: {task.name} - {error}")
            except Exception as e:
                print(f"  [事件处理错误] task_failed: {e}")

        self.orchestrator.on_event(OrchestratorEventType.AGENT_REGISTERED, on_agent_registered)
        self.orchestrator.on_event(OrchestratorEventType.TASK_CREATED, on_task_created)
        self.orchestrator.on_event(OrchestratorEventType.TASK_ASSIGNED, on_task_assigned)
        self.orchestrator.on_event(OrchestratorEventType.TASK_COMPLETED, on_task_completed)
        self.orchestrator.on_event(OrchestratorEventType.TASK_FAILED, on_task_failed)

    def print_section(self, title: str):
        """打印章节标题"""
        print("\n" + "-" * 70)
        print(f"  {title}")
        print("-" * 70)

    def demo_1_agent_creation(self):
        """
        演示1: Agent创建

        展示如何创建不同类型的Agent，包括数据处理Agent、分析Agent和报告生成Agent。
        每个Agent都有其特定的能力和职责。
        """
        self.print_section("演示1: Agent创建与注册")

        print("\n[步骤1] 创建DataProcessingAgent...")
        data_agent = DataProcessingAgent(AgentOptions(
            name="data_processor",
            description="数据处理Agent，负责数据清洗、转换和验证",
            capabilities=["data_cleaning", "data_transformation", "data_validation"]
        ))
        print(f"  ✓ 创建成功: {data_agent.name}")
        print(f"    - 能力: {', '.join(data_agent.capabilities)}")
        print(f"    - 状态: {data_agent.status.value}")

        print("\n[步骤2] 创建AnalysisAgent...")
        analysis_agent = AnalysisAgent(AgentOptions(
            name="data_analyst",
            description="数据分析Agent，负责数据分析和统计计算",
            capabilities=["data_analysis", "statistical_analysis", "pattern_recognition"]
        ))
        print(f"  ✓ 创建成功: {analysis_agent.name}")
        print(f"    - 能力: {', '.join(analysis_agent.capabilities)}")
        print(f"    - 状态: {analysis_agent.status.value}")

        print("\n[步骤3] 创建ReportingAgent...")
        reporting_agent = ReportingAgent(AgentOptions(
            name="report_generator",
            description="报告生成Agent，负责生成各种格式的报告",
            capabilities=["report_generation", "format_conversion", "data_visualization"]
        ))
        print(f"  ✓ 创建成功: {reporting_agent.name}")
        print(f"    - 能力: {', '.join(reporting_agent.capabilities)}")
        print(f"    - 状态: {reporting_agent.status.value}")

        print("\n[步骤4] 注册Agent到编排器...")
        self.orchestrator.register_agent(data_agent)
        self.orchestrator.register_agent(analysis_agent)
        self.orchestrator.register_agent(reporting_agent)
        print(f"  ✓ 已注册 {len(self.orchestrator.agent_registry.get_all_agents())} 个Agent")

        return [data_agent, analysis_agent, reporting_agent]

    def demo_2_task_creation(self):
        """
        演示2: 任务创建与执行

        展示如何创建任务、分配优先级以及执行任务。
        演示任务的生命周期管理。
        """
        self.print_section("演示2: 任务创建与执行")

        from maos.orchestration.task_manager import TaskManager
        task_manager = TaskManager(max_concurrent=5)
        self.orchestrator.set_task_manager(task_manager)

        print("\n[步骤1] 创建任务管理器...")
        print(f"  ✓ 任务管理器已创建，最大并发任务数: {task_manager.max_concurrent}")

        print("\n[步骤2] 创建数据清洗任务...")
        user_data = {
            'records': [
                {'id': 1, 'name': '张三', 'email': 'zhangsan@example.com', 'age': 28},
                {'id': 2, 'name': '李四', 'email': '', 'age': None},
                {'id': 3, 'name': '  王五  ', 'email': 'wangwu@example.com', 'age': 35},
                {'id': 4, 'name': '', 'email': 'invalid', 'age': 42},
            ]
        }

        task1 = self.orchestrator.create_task(
            name="清洗用户数据",
            requirements=["data_cleaning", "data_validation"],
            description="清洗和验证用户数据，去除无效记录",
            priority=TaskPriority.HIGH,
            input_data=user_data
        )

        if task1:
            print(f"  ✓ 任务创建成功: {task1.name}")
            print(f"    - 任务ID: {task1.id[:16]}...")
            print(f"    - 优先级: {task1.priority.name}")
            print(f"    - 状态: {task1.status.value}")
            print(f"    - 需求能力: {', '.join(task1.requirements)}")

        print("\n[步骤3] 创建数据分析任务...")
        numeric_data = [15, 28, 42, 35, 56, 78, 23, 91, 34, 67, 45, 89, 12, 56, 78]

        task2 = self.orchestrator.create_task(
            name="统计分析",
            requirements=["statistical_analysis"],
            description="对数值数据进行统计分析",
            priority=TaskPriority.NORMAL,
            input_data=numeric_data
        )

        if task2:
            print(f"  ✓ 任务创建成功: {task2.name}")
            print(f"    - 任务ID: {task2.id[:16]}...")
            print(f"    - 优先级: {task2.priority.name}")
            print(f"    - 状态: {task2.status.value}")

        print("\n[步骤4] 创建报告生成任务...")
        report_data = {
            'title': '数据分析报告',
            'period': '2024年第一季度',
            'metrics': {
                'total_users': 1250,
                'active_users': 890,
                'conversion_rate': 0.712
            }
        }

        task3 = self.orchestrator.create_task(
            name="生成报告",
            requirements=["report_generation"],
            description="生成数据摘要报告",
            priority=TaskPriority.LOW,
            input_data=report_data
        )

        if task3:
            print(f"  ✓ 任务创建成功: {task3.name}")
            print(f"    - 任务ID: {task3.id[:16]}...")
            print(f"    - 优先级: {task3.priority.name}")

        print("\n[步骤5] 查看任务统计...")
        stats = task_manager.get_statistics()
        print(f"  - 总任务数: {stats['total']}")
        print(f"  - 待处理: {stats['pending']}")
        print(f"  - 运行中: {stats['running']}")
        print(f"  - 已完成: {stats['completed']}")
        print(f"  - 已失败: {stats['failed']}")

        return [task1, task2, task3]

    def demo_3_workflow_execution(self):
        """
        演示3: 工作流执行

        展示如何定义工作流、设置执行策略以及执行复杂的工作流任务。
        工作流可以包含多个步骤，每个步骤可以有不同的需求和依赖关系。
        """
        self.print_section("演示3: 工作流执行")

        print("\n[步骤1] 定义工作流...")
        sales_workflow = Workflow(
            name="销售数据分析工作流",
            description="从原始销售数据到最终报告的完整流程",
            strategy=ExecutionStrategy.SEQUENTIAL
        )

        sales_workflow.steps = [
            WorkflowStep(
                name="step_1_clean_data",
                requirements=["data_cleaning"],
                description="清洗销售原始数据",
                priority=3
            ),
            WorkflowStep(
                name="step_2_analyze",
                requirements=["statistical_analysis"],
                description="分析销售数据趋势",
                priority=2,
                dependencies=["step_1_clean_data"]
            ),
            WorkflowStep(
                name="step_3_generate_report",
                requirements=["report_generation"],
                description="生成销售分析报告",
                priority=1,
                dependencies=["step_2_analyze"]
            )
        ]

        print(f"  ✓ 工作流已定义: {sales_workflow.name}")
        print(f"    - 步骤数: {len(sales_workflow.steps)}")
        print(f"    - 执行策略: {sales_workflow.strategy.value}")

        print("\n[步骤2] 准备工作流输入数据...")
        workflow_input = {
            'raw_transactions': [
                {'id': 'T001', 'product': '产品A', 'amount': 299.99, 'region': '华北', 'date': '2024-01-15'},
                {'id': 'T002', 'product': '产品B', 'amount': 499.99, 'region': '华东', 'date': '2024-01-16'},
                {'id': 'T003', 'product': '产品A', 'amount': 299.99, 'region': '华南', 'date': '2024-01-17'},
                {'id': 'T004', 'product': '产品C', 'amount': 199.99, 'region': '华北', 'date': '2024-01-18'},
                {'id': 'T005', 'product': '产品B', 'amount': '', 'region': None, 'date': '2024-01-19'},
            ]
        }
        print(f"  ✓ 输入数据已准备，包含 {len(workflow_input['raw_transactions'])} 条交易记录")

        print("\n[步骤3] 执行工作流...")
        start_time = time.time()
        print(f"  开始时间: {datetime.now().strftime('%H:%M:%S')}")

        results = self.orchestrator.execute_workflow(sales_workflow, workflow_input)

        elapsed = time.time() - start_time
        print(f"  结束时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"  执行耗时: {elapsed:.3f}秒")

        print("\n[步骤4] 查看工作流执行结果...")
        if isinstance(results, dict):
            print(f"  ✓ 工作流执行完成")
            print(f"    - 返回结果数: {len(results)}")
            for step_name, result in results.items():
                print(f"    - {step_name}: {'成功' if result else '失败'}")
        else:
            print(f"  ⚠ 工作流执行返回: {results}")

        return results

    def demo_4_system_status(self):
        """
        演示4: 系统状态监控

        展示如何查看系统状态、Agent状态和任务统计信息。
        这些信息对于系统运维和性能优化非常重要。
        """
        self.print_section("演示4: 系统状态监控")

        print("\n[步骤1] 获取系统状态...")
        status = self.orchestrator.get_system_status()

        print(f"\n  📊 编排器状态:")
        print(f"     名称: {status.get('name', 'N/A')}")
        print(f"     运行中: {status.get('running', False)}")
        print(f"     执行策略: {status.get('execution_strategy', 'N/A')}")
        print(f"     最大并发任务: {status.get('max_concurrent_tasks', 'N/A')}")

        print(f"\n  🤖 Agent统计:")
        agent_stats = status.get('agents', {})
        print(f"     总数: {agent_stats.get('total', 0)}")
        if 'by_status' in agent_stats:
            for status_name, count in agent_stats['by_status'].items():
                print(f"     - {status_name}: {count}")

        print(f"\n  📋 任务统计:")
        task_stats = status.get('tasks', {})
        if task_stats:
            print(f"     总数: {task_stats.get('total', 0)}")
            print(f"     待处理: {task_stats.get('pending', 0)}")
            print(f"     运行中: {task_stats.get('running', 0)}")
            print(f"     已完成: {task_stats.get('completed', 0)}")
            print(f"     已失败: {task_stats.get('failed', 0)}")
        else:
            print(f"     (任务统计不可用)")

        print(f"\n  📨 消息统计:")
        print(f"     已发送消息数: {status.get('messages_count', 0)}")

        print("\n[步骤2] 查看注册的Agent详情...")
        agents = self.orchestrator.agent_registry.get_all_agents()
        for agent in agents:
            print(f"\n  Agent: {agent.name}")
            print(f"    - 描述: {agent.description}")
            print(f"    - 能力: {', '.join(agent.capabilities)}")
            status_value = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)
            print(f"    - 当前状态: {status_value}")
            print(f"    - 消息队列大小: {agent.get_queue_size()}")

        print("\n[步骤3] 获取Agent统计信息...")
        registry_stats = self.orchestrator.agent_registry.get_statistics()
        print(f"\n  📈 注册表统计:")
        print(f"     总Agent数: {registry_stats['total']}")
        print(f"     可用能力列表:")
        for capability in registry_stats.get('capabilities', {}).keys():
            print(f"       • {capability}")

        return status

    def demo_5_capability_matching(self):
        """
        演示5: 能力匹配

        展示系统如何根据任务需求自动选择最合适的Agent。
        这是MAOS系统的核心功能之一。
        """
        self.print_section("演示5: 智能Agent选择（能力匹配）")

        print("\n[步骤1] 测试能力匹配...")

        test_cases = [
            {
                'name': '数据清洗任务',
                'requirements': ['data_cleaning', 'data_validation'],
                'description': '需要数据清洗和验证能力'
            },
            {
                'name': '统计分析任务',
                'requirements': ['statistical_analysis'],
                'description': '需要统计分析能力'
            },
            {
                'name': '报告生成任务',
                'requirements': ['report_generation'],
                'description': '需要报告生成能力'
            },
            {
                'name': '综合分析任务',
                'requirements': ['data_cleaning', 'statistical_analysis', 'report_generation'],
                'description': '需要多种能力'
            }
        ]

        print("\n  测试不同的任务需求场景:\n")

        for i, test_case in enumerate(test_cases, 1):
            print(f"  场景{i}: {test_case['name']}")
            print(f"    描述: {test_case['description']}")
            print(f"    需求能力: {', '.join(test_case['requirements'])}")

            selected_agent = self.orchestrator.agent_registry.select_best_agent(
                test_case['requirements']
            )

            if selected_agent:
                print(f"    ✓ 选中Agent: {selected_agent.name}")
                print(f"      Agent能力: {', '.join(selected_agent.capabilities)}")

                can_handle = selected_agent.can_handle_task(test_case['requirements'])
                print(f"      能否处理: {'是' if can_handle else '否'}")
            else:
                print(f"    ✗ 未找到合适的Agent")

            print()

    def demo_6_message_broadcast(self):
        """
        演示6: 消息广播

        展示如何向所有注册的Agent广播消息。
        这对于系统通知和协调多Agent操作非常有用。
        """
        self.print_section("演示6: 消息广播")

        print("\n[步骤1] 广播系统公告...")
        announcement = {
            'type': 'system_announcement',
            'title': '系统维护通知',
            'message': '系统将在今晚23:00进行例行维护，预计持续30分钟',
            'priority': 'normal',
            'timestamp': datetime.now().isoformat()
        }

        try:
            self.orchestrator.broadcast_message(
                content=announcement,
                sender='system_admin',
                msg_type='announcement'
            )
            print(f"  ✓ 广播消息已发送")
            print(f"    发送者: system_admin")
            print(f"    消息类型: announcement")
            print(f"    内容: {announcement['title']}")
        except Exception as e:
            print(f"  ✗ 广播失败: {e}")

        print("\n[步骤2] 直接发送消息给指定Agent...")
        agents = self.orchestrator.agent_registry.get_all_agents()
        if agents:
            target_agent = agents[0]
            direct_message = {
                'type': 'direct_task',
                'task': '请准备处理新数据',
                'deadline': '1小时'
            }

            try:
                success = self.orchestrator.send_message(
                    receiver=target_agent.name,
                    content=direct_message,
                    sender='coordinator',
                    msg_type='direct'
                )

                if success:
                    print(f"  ✓ 消息已发送给 {target_agent.name}")
                    print(f"    内容: {direct_message['task']}")
                else:
                    print(f"  ✗ 发送失败")
            except Exception as e:
                print(f"  ✗ 发送失败: {e}")

    def cleanup(self):
        """清理演示环境"""
        print("\n" + "=" * 70)
        print("  清理演示环境...")
        print("=" * 70)

        self.orchestrator.shutdown()
        print("  ✓ 编排器已关闭")
        print("  ✓ 所有Agent已停止")

    def run_demo(self):
        """
        运行完整的演示流程

        按顺序执行所有演示步骤，展示MAOS系统的核心功能。
        """
        try:
            print("\n" + "=" * 70)
            print("  准备开始演示...")
            print("=" * 70)

            self.demo_1_agent_creation()

            self.demo_2_task_creation()

            self.demo_3_workflow_execution()

            self.demo_4_system_status()

            self.demo_5_capability_matching()

            self.demo_6_message_broadcast()

            self.print_section("演示完成")
            print("\n  ✅ MAOS基础演示已成功完成！")
            print("\n  📚 接下来您可以:")
            print("     1. 查看 complete_demo.py 了解完整功能演示")
            print("     2. 尝试运行 main.py 体验CLI交互")
            print("     3. 阅读源码深入了解MAOS架构")
            print("     4. 编写自己的Agent和任务")
            print()

        except KeyboardInterrupt:
            print("\n\n  ⚠️ 演示被用户中断")
        except Exception as e:
            print(f"\n\n  ❌ 演示执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()


def run_demo():
    """
    运行基础演示的便捷函数

    使用方法:
        from maos.examples.basic_demo import run_demo
        run_demo()
    """
    demo = BasicMAOSDemo()
    demo.run_demo()


if __name__ == "__main__":
    run_demo()
