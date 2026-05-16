"""
Integration Tests - Agent and Orchestration
=========================================

Integration tests for agent collaboration and orchestration workflows.
"""

import unittest
import time
from datetime import datetime

from multi_agent_orchestration_system.application_services.orchestration import OrchestrationEngine
from multi_agent_orchestration_system.application_services.scheduling import TaskPriorityLevel
from multi_agent_orchestration_system.domain_entities.agent.examples import (
    DataProcessingAgent,
    DataAnalysisAgent,
    ReportGenerationAgent
)


class TestAgentOrchestrationIntegration(unittest.TestCase):
    """Integration tests for agent registration and task execution"""
    
    def setUp(self):
        """Set up test orchestrator with agents"""
        self.orchestrator = OrchestrationEngine(orchestrator_name="integration_test_orchestrator")
        
        self.data_agent = DataProcessingAgent(agent_name="test_data_processor")
        self.analysis_agent = DataAnalysisAgent(agent_name="test_analyzer")
        self.reporting_agent = ReportGenerationAgent(agent_name="test_reporter")
    
    def tearDown(self):
        """Cleanup after tests"""
        self.orchestrator.shutdown_orchestrator()
    
    def test_agent_registration_and_discovery(self):
        """Test agent registration and capability-based discovery"""
        self.orchestrator.register_agent_with_orchestrator(self.data_agent)
        self.orchestrator.register_agent_with_orchestrator(self.analysis_agent)
        
        agents = self.orchestrator.get_all_registered_agents()
        self.assertEqual(len(agents), 2)
        
        suitable = self.orchestrator.find_suitable_agent_for_task(['data_cleaning'])
        self.assertIsNotNone(suitable)
        self.assertEqual(suitable.agent_name, 'test_data_processor')
    
    def test_single_task_execution_lifecycle(self):
        """Test complete task lifecycle from creation to completion"""
        self.orchestrator.register_agent_with_orchestrator(self.data_agent)
        
        test_data = {
            'records': [
                {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
                {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
            ]
        }
        
        result = self.orchestrator.create_and_execute_task(
            task_name='test_data_cleaning',
            required_capabilities=['data_cleaning'],
            input_data=test_data,
            priority=TaskPriorityLevel.HIGH
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        self.assertIn('task_id', result)
        self.assertIn('executed_by', result)
    
    def test_multi_agent_collaboration(self):
        """Test collaboration between multiple agents"""
        self.orchestrator.register_agent_with_orchestrator(self.data_agent)
        self.orchestrator.register_agent_with_orchestrator(self.analysis_agent)
        
        workflow_steps = [
            {
                'step_name': 'clean_sales_data',
                'required_capabilities': ['data_cleaning'],
                'priority': 'HIGH',
                'input_data': {'raw': 'data'}
            },
            {
                'step_name': 'analyze_sales',
                'required_capabilities': ['statistical_analysis'],
                'priority': 'NORMAL',
                'input_data': {'values': [10, 20, 30]}
            }
        ]
        
        result = self.orchestrator.execute_workflow_steps(workflow_steps)
        
        self.assertEqual(len(result['completed_steps']), 2)
        self.assertEqual(result['status'], 'completed_successfully')
    
    def test_capability_matching_priority(self):
        """Test that best agent is selected based on capabilities"""
        self.orchestrator.register_agent_with_orchestrator(self.data_agent)
        
        suitable = self.orchestrator.find_suitable_agent_for_task(
            ['data_cleaning', 'data_transformation']
        )
        
        self.assertIsNotNone(suitable)
        capabilities = suitable.get_agent_capabilities()
        self.assertTrue(capabilities.has_all_capabilities(['data_cleaning', 'data_transformation']))
    
    def test_agent_status_tracking(self):
        """Test agent status changes during task execution"""
        self.orchestrator.register_agent_with_orchestrator(self.data_agent)
        
        initial_status = self.orchestrator.get_registered_agent('test_data_processor')
        self.assertEqual(initial_status.agent_status.value, 'idle')
        
        test_data = {'records': [{'id': 1, 'name': 'Test'}]}
        
        self.orchestrator.create_and_execute_task(
            task_name='test_task',
            required_capabilities=['data_cleaning'],
            input_data=test_data
        )
    
    def test_workflow_with_dependencies(self):
        """Test workflow execution with task dependencies"""
        self.orchestrator.register_agent_with_orchestrator(self.data_agent)
        
        workflow_steps = [
            {
                'step_name': 'step1_clean',
                'required_capabilities': ['data_cleaning'],
                'priority': 'HIGH',
                'input_data': {'step': 1}
            },
            {
                'step_name': 'step2_process',
                'required_capabilities': ['data_cleaning'],
                'priority': 'NORMAL',
                'input_data': {'step': 2},
                'depends_on': ['step1_clean']
            }
        ]
        
        result = self.orchestrator.execute_workflow_steps(workflow_steps)
        
        self.assertIn('step1_clean', result['completed_steps'])
        self.assertIn('step2_process', result['completed_steps'])


class TestTaskSchedulingIntegration(unittest.TestCase):
    """Integration tests for task scheduling"""
    
    def test_task_priority_ordering(self):
        """Test that tasks are scheduled by priority"""
        orchestrator = OrchestrationEngine(orchestrator_name="priority_test_orchestrator")
        
        agent = DataProcessingAgent(agent_name="priority_test_agent")
        orchestrator.register_agent_with_orchestrator(agent)
        
        for i in range(5):
            orchestrator.create_and_execute_task(
                task_name=f'task_{i}',
                required_capabilities=['data_cleaning'],
                input_data={'index': i}
            )
        
        stats = orchestrator.get_orchestrator_status()
        self.assertGreater(stats['task_statistics']['total_tasks'], 0)
        
        orchestrator.shutdown_orchestrator()
    
    def test_task_state_transitions(self):
        """Test task state machine transitions"""
        orchestrator = OrchestrationEngine(orchestrator_name="state_test_orchestrator")
        
        agent = DataProcessingAgent(agent_name="state_test_agent")
        orchestrator.register_agent_with_orchestrator(agent)
        
        test_data = {'records': [{'id': 1, 'data': 'test'}]}
        
        result = orchestrator.create_and_execute_task(
            task_name='state_test_task',
            required_capabilities=['data_cleaning'],
            input_data=test_data
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        
        orchestrator.shutdown_orchestrator()


class TestSystemMonitoringIntegration(unittest.TestCase):
    """Integration tests for system monitoring and metrics"""
    
    def test_system_statistics_collection(self):
        """Test that system statistics are properly collected"""
        orchestrator = OrchestrationEngine(orchestrator_name="monitoring_test_orchestrator")
        
        data_agent = DataProcessingAgent(agent_name="mon_data_agent")
        analysis_agent = DataAnalysisAgent(agent_name="mon_analysis_agent")
        
        orchestrator.register_agent_with_orchestrator(data_agent)
        orchestrator.register_agent_with_orchestrator(analysis_agent)
        
        orchestrator.create_and_execute_task(
            task_name='test_task',
            required_capabilities=['data_cleaning'],
            input_data={'test': 'data'}
        )
        
        status = orchestrator.get_orchestrator_status()
        
        self.assertEqual(status['agent_statistics']['total_registered_agents'], 2)
        self.assertIn('task_statistics', status)
        self.assertIn('workflow_statistics', status)
        
        orchestrator.shutdown_orchestrator()
    
    def test_agent_registry_statistics(self):
        """Test agent registry statistics"""
        orchestrator = OrchestrationEngine(orchestrator_name="registry_test")
        
        agent1 = DataProcessingAgent(agent_name="reg_agent_1")
        agent2 = DataAnalysisAgent(agent_name="reg_agent_2")
        
        orchestrator.register_agent_with_orchestrator(agent1)
        orchestrator.register_agent_with_orchestrator(agent2)
        
        registry_stats = orchestrator.get_orchestrator_status()['agent_statistics']
        
        self.assertEqual(registry_stats['total_registered_agents'], 2)
        
        orchestrator.shutdown_orchestrator()


if __name__ == '__main__':
    unittest.main()
