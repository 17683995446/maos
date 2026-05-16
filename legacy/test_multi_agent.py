"""
Tests for Multi-Agent Orchestration System
多Agent编排系统测试套件
"""

import unittest
from typing import Any, Dict, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import Agent, AgentMessage, AgentStatus, MessageType
from orchestrator import Orchestrator, ExecutionStrategy
from task_manager import Task, TaskStatus, TaskPriority, TaskManager
from registry import AgentRegistry
from examples.data_agent import DataProcessingAgent
from examples.analysis_agent import AnalysisAgent
from examples.reporting_agent import ReportingAgent


class TestAgent(unittest.TestCase):
    """测试Agent基类"""

    def test_agent_creation(self):
        """测试Agent创建"""
        agent = Agent(name="test_agent", capabilities=["test"])
        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.status, AgentStatus.IDLE)
        self.assertIn("test", agent.capabilities)

    def test_message_send_receive(self):
        """测试消息发送和接收"""
        agent1 = Agent(name="agent1")
        agent2 = Agent(name="agent2")

        message = AgentMessage(
            sender=agent1.name,
            receivers=[agent2.name],
            content="Hello"
        )

        agent1.send_message(message)
        self.assertEqual(len(agent1.message_queue), 1)

        agent2.receive_message(message)
        self.assertEqual(len(agent2.message_queue), 1)

    def test_capability_check(self):
        """测试能力检查"""
        agent = Agent(name="test", capabilities=["analyze", "process"])
        self.assertTrue(agent.has_capability("analyze"))
        self.assertFalse(agent.has_capability("unknown"))

    def test_task_handling(self):
        """测试任务处理能力判断"""
        agent = Agent(name="test", capabilities=["analyze", "process"])
        self.assertTrue(agent.can_handle_task(["analyze"]))
        self.assertTrue(agent.can_handle_task(["analyze", "process"]))
        self.assertFalse(agent.can_handle_task(["analyze", "unknown"]))


class TestTaskManager(unittest.TestCase):
    """测试任务管理器"""

    def setUp(self):
        self.task_manager = TaskManager()

    def test_task_creation(self):
        """测试任务创建"""
        task = self.task_manager.create_task(
            name="test_task",
            requirements=["analyze"],
            priority=TaskPriority.HIGH
        )
        self.assertEqual(task.name, "test_task")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.HIGH)

    def test_task_assignment(self):
        """测试任务分配"""
        task = self.task_manager.create_task(
            name="test_task",
            requirements=["analyze"]
        )
        success = self.task_manager.assign_task(task.id, "agent1")
        self.assertTrue(success)
        self.assertEqual(task.assigned_agent, "agent1")

    def test_task_status_update(self):
        """测试任务状态更新"""
        task = self.task_manager.create_task(name="test", requirements=[])
        task.mark_running()
        self.assertEqual(task.status, TaskStatus.RUNNING)

        task.mark_completed(output_data={"result": "success"})
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.output_data, {"result": "success"})

    def test_task_priority_queue(self):
        """测试任务优先级队列"""
        task1 = self.task_manager.create_task(name="low", requirements=[], priority=TaskPriority.LOW)
        task2 = self.task_manager.create_task(name="high", requirements=[], priority=TaskPriority.HIGH)

        ready_tasks = self.task_manager.get_ready_tasks()
        self.assertEqual(ready_tasks[0].name, "high")
        self.assertEqual(ready_tasks[1].name, "low")

    def test_task_dependencies(self):
        """测试任务依赖"""
        task1 = self.task_manager.create_task(name="task1", requirements=[])
        task2 = self.task_manager.create_task(
            name="task2",
            requirements=[],
            dependencies=[task1.id]
        )

        ready_tasks = self.task_manager.get_ready_tasks()
        self.assertEqual(len(ready_tasks), 1)
        self.assertEqual(ready_tasks[0].name, "task1")

        self.task_manager.update_task_status(task1.id, TaskStatus.COMPLETED)
        ready_tasks = self.task_manager.get_ready_tasks()
        self.assertEqual(len(ready_tasks), 1)
        self.assertEqual(ready_tasks[0].name, "task2")


class TestAgentRegistry(unittest.TestCase):
    """测试Agent注册表"""

    def setUp(self):
        self.registry = AgentRegistry()
        self.agent1 = Agent(name="agent1", capabilities=["analyze"])
        self.agent2 = Agent(name="agent2", capabilities=["process"])

    def test_agent_registration(self):
        """测试Agent注册"""
        success = self.registry.register(self.agent1)
        self.assertTrue(success)
        self.assertEqual(len(self.registry.agents), 1)

    def test_duplicate_registration(self):
        """测试重复注册"""
        self.registry.register(self.agent1)
        success = self.registry.register(self.agent1)
        self.assertFalse(success)

    def test_get_agents_by_capability(self):
        """测试按能力获取Agent"""
        self.registry.register(self.agent1)
        self.registry.register(self.agent2)

        analyze_agents = self.registry.get_agents_by_capability("analyze")
        self.assertEqual(len(analyze_agents), 1)
        self.assertEqual(analyze_agents[0].name, "agent1")

    def test_select_best_agent(self):
        """测试选择最佳Agent"""
        self.registry.register(self.agent1)
        self.registry.register(self.agent2)

        best = self.registry.select_best_agent(["analyze"])
        self.assertEqual(best.name, "agent1")

        best = self.registry.select_best_agent(["process"])
        self.assertEqual(best.name, "agent2")


class TestOrchestrator(unittest.TestCase):
    """测试编排器"""

    def setUp(self):
        self.orchestrator = Orchestrator(name="test_orchestrator")
        self.data_agent = DataProcessingAgent()
        self.analysis_agent = AnalysisAgent()
        self.reporting_agent = ReportingAgent()

    def test_orchestrator_creation(self):
        """测试编排器创建"""
        self.assertEqual(self.orchestrator.name, "test_orchestrator")
        self.assertIsNotNone(self.orchestrator.registry)
        self.assertIsNotNone(self.orchestrator.task_manager)

    def test_register_agents(self):
        """测试注册Agent"""
        self.orchestrator.register_agent(self.data_agent)
        self.orchestrator.register_agent(self.analysis_agent)

        self.assertEqual(len(self.orchestrator.registry.agents), 2)

    def test_create_and_execute_task(self):
        """测试创建和执行任务"""
        self.orchestrator.register_agent(self.data_agent)

        task = self.orchestrator.create_task(
            name="process_data",
            requirements=["data_cleaning"],
            input_data={"test": "data"}
        )

        self.assertEqual(task.status, TaskStatus.PENDING)

        result = self.orchestrator.execute_task(task)
        self.assertIsNotNone(result)

        task = self.orchestrator.task_manager.get_task(task.id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_workflow_execution(self):
        """测试工作流执行"""
        self.orchestrator.register_agent(self.data_agent)
        self.orchestrator.register_agent(self.analysis_agent)

        workflow = [
            {
                'name': 'step1',
                'requirements': ['data_cleaning'],
                'priority': 'HIGH',
                'input_data': {'test': 1}
            },
            {
                'name': 'step2',
                'requirements': ['data_analysis'],
                'priority': 'NORMAL',
                'input_data': {'test': 2}
            }
        ]

        results = self.orchestrator.execute_workflow(workflow)
        self.assertEqual(len(results), 2)

    def test_message_broadcast(self):
        """测试消息广播"""
        self.orchestrator.register_agent(self.data_agent)
        self.orchestrator.register_agent(self.analysis_agent)

        self.orchestrator.broadcast_message(
            content={'message': 'test'},
            sender='orchestrator'
        )

        for agent in self.orchestrator.registry.get_all_agents():
            self.assertEqual(len(agent.message_queue), 1)

    def test_system_status(self):
        """测试系统状态获取"""
        self.orchestrator.register_agent(self.data_agent)

        status = self.orchestrator.get_system_status()
        self.assertEqual(status['agents']['total_agents'], 1)
        self.assertEqual(status['tasks']['total'], 0)


class TestDataProcessingAgent(unittest.TestCase):
    """测试数据处理Agent"""

    def setUp(self):
        self.agent = DataProcessingAgent(name="test_processor")

    def test_process_dict_data(self):
        """测试处理字典数据"""
        data = {'name': 'test', 'value': 123, 'empty': None}
        result = self.agent._process_data(data)

        self.assertIn('name', result)
        self.assertIn('value', result)
        self.assertNotIn('empty', result)

    def test_process_list_data(self):
        """测试处理列表数据"""
        data = [
            {'name': 'a', 'value': 1},
            {'name': 'b', 'value': None},
            {'name': '', 'value': 3}
        ]
        result = self.agent._process_data(data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'a')
        self.assertEqual(result[1]['name'], 'b')


class TestAnalysisAgent(unittest.TestCase):
    """测试分析Agent"""

    def setUp(self):
        self.agent = AnalysisAgent(name="test_analyzer")

    def test_analyze_numeric_list(self):
        """测试分析数值列表"""
        data = [10, 20, 30, 40, 50]
        result = self.agent._analyze_list(data)

        self.assertEqual(result['count'], 5)
        self.assertEqual(result['numeric_summary']['min'], 10)
        self.assertEqual(result['numeric_summary']['max'], 50)
        self.assertEqual(result['numeric_summary']['avg'], 30)

    def test_calculate_statistics(self):
        """测试统计计算"""
        data = [10, 20, 30, 40, 50]
        stats = self.agent.calculate_statistics(data)

        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['mean'], 30)
        self.assertEqual(stats['median'], 30)


class TestReportingAgent(unittest.TestCase):
    """测试报告生成Agent"""

    def setUp(self):
        self.agent = ReportingAgent(name="test_reporter")

    def test_generate_text_report(self):
        """测试生成文本报告"""
        data = {'title': 'Test', 'value': 100}
        report = self.agent._generate_text_report(data)

        self.assertIn('Test', report)
        self.assertIn('100', report)

    def test_generate_summary(self):
        """测试生成摘要"""
        data = [1, 2, 3, 4, 5]
        summary = self.agent._generate_summary(data)

        self.assertEqual(summary['type'], 'list')
        self.assertEqual(summary['size'], 5)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        orchestrator = Orchestrator(name="integration_test")
        orchestrator.register_agent(DataProcessingAgent())
        orchestrator.register_agent(AnalysisAgent())
        orchestrator.register_agent(ReportingAgent())

        task = orchestrator.create_task(
            name="full_pipeline",
            requirements=["data_cleaning", "data_analysis", "report_generation"],
            input_data={'data': [1, 2, 3, None, 5]}
        )

        result = orchestrator.execute_task(task)
        self.assertIsNotNone(result)

        status = orchestrator.get_system_status()
        self.assertEqual(status['tasks']['completed'], 1)


if __name__ == '__main__':
    unittest.main()
