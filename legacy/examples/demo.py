"""
Demo - 演示多Agent编排系统的使用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict
from orchestrator import Orchestrator, ExecutionStrategy
from task_manager import TaskPriority
from examples.data_agent import DataProcessingAgent
from examples.analysis_agent import AnalysisAgent
from examples.reporting_agent import ReportingAgent


def run_demo():
    """运行演示"""
    print("=" * 60)
    print("Multi-Agent Orchestration System Demo")
    print("=" * 60)

    orchestrator = Orchestrator(name="demo_orchestrator")
    orchestrator.execution_strategy = ExecutionStrategy.SEQUENTIAL

    data_agent = DataProcessingAgent(name="data_processor_1")
    analysis_agent = AnalysisAgent(name="analyzer_1")
    reporting_agent = ReportingAgent(name="reporter_1")

    print("\n1. Registering agents...")
    orchestrator.register_agent(data_agent)
    orchestrator.register_agent(analysis_agent)
    orchestrator.register_agent(reporting_agent)
    print(f"   Registered agents: {list(orchestrator.registry.agents.keys())}")

    print("\n2. Creating tasks...")
    task1 = orchestrator.create_task(
        name="clean_user_data",
        requirements=['data_cleaning'],
        description="Clean and validate user data",
        priority=TaskPriority.HIGH,
        input_data={
            'users': [
                {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'},
                {'name': 'Bob', 'age': 25, 'email': 'bob@example.com', 'phone': None},
                {'name': '', 'age': 35, 'email': ''}
            ]
        }
    )
    print(f"   Created task: {task1.name} (ID: {task1.id[:8]}...)")

    task2 = orchestrator.create_task(
        name="analyze_statistics",
        requirements=['statistical_analysis'],
        description="Calculate statistics from processed data",
        priority=TaskPriority.NORMAL,
        input_data={'values': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]}
    )
    print(f"   Created task: {task2.name} (ID: {task2.id[:8]}...)")

    task3 = orchestrator.create_task(
        name="generate_report",
        requirements=['report_generation'],
        description="Generate final report",
        priority=TaskPriority.LOW,
        input_data={'report_type': 'summary'}
    )
    print(f"   Created task: {task3.name} (ID: {task3.id[:8]}...)")

    print("\n3. Executing workflow...")
    workflow = [
        {
            'name': 'step_1_process_data',
            'requirements': ['data_cleaning'],
            'priority': 'HIGH',
            'input_data': {'items': [1, 2, 3, None, 5]}
        },
        {
            'name': 'step_2_analyze',
            'requirements': ['data_analysis'],
            'priority': 'NORMAL',
            'input_data': {'metrics': [15, 25, 35]}
        }
    ]

    results = orchestrator.execute_workflow(workflow)
    print(f"   Workflow completed with {len(results)} results")

    print("\n4. System status:")
    status = orchestrator.get_system_status()
    print(f"   Total agents: {status['agents']['total_agents']}")
    print(f"   Idle agents: {status['agents']['idle_agents']}")
    print(f"   Total tasks: {status['tasks']['total']}")
    print(f"   Completed tasks: {status['tasks']['completed']}")

    print("\n5. Testing agent coordination...")
    task4 = orchestrator.create_task(
        name="coordinated_analysis",
        requirements=['data_analysis', 'report_generation'],
        description="Multi-agent coordinated task",
        priority=TaskPriority.HIGH,
        input_data={'data': [1, 2, 3, 4, 5]}
    )

    orchestrator.schedule_task(task4.id)
    result = orchestrator.execute_task(task4)
    print(f"   Coordinated task result: {result is not None}")

    print("\n6. Testing message broadcast...")
    orchestrator.broadcast_message(
        content={'type': 'system_announcement', 'message': 'System update available'},
        sender='orchestrator'
    )
    print("   Broadcast message sent to all agents")

    print("\n7. Agent statistics:")
    for agent in orchestrator.registry.get_all_agents():
        info = agent.get_info()
        print(f"   {info['name']}: {info['status']}, capabilities: {info['capabilities']}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)

    return orchestrator


if __name__ == "__main__":
    run_demo()
