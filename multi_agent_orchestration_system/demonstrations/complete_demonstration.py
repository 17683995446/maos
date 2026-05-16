"""
Multi-Agent Orchestration System - Complete Demonstration
====================================================

This module demonstrates all features of the orchestration system.
It provides a comprehensive example of multi-agent workflow execution.
"""

import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '/workspace')

from multi_agent_orchestration_system.domain_entities.agent.examples import (
    DataProcessingAgent,
    DataAnalysisAgent,
    ReportGenerationAgent
)
from multi_agent_orchestration_system.application_services.orchestration import (
    OrchestrationEngine,
    WorkflowExecutionStrategy
)
from multi_agent_orchestration_system.application_services.scheduling import (
    TaskPriorityLevel
)


def print_section_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subsection(title: str):
    """Print formatted subsection"""
    print(f"\n--- {title} ---")


def demonstrate_agent_registration(orchestrator: OrchestrationEngine):
    """Demonstrate agent registration capabilities"""
    print_section_header("DEMONSTRATION 1: Agent Registration and Management")
    
    print_subsection("Creating Specialized Agents")
    
    data_agent = DataProcessingAgent(agent_name="sales_data_processor")
    analysis_agent = DataAnalysisAgent(agent_name="sales_data_analyzer")
    reporting_agent = ReportGenerationAgent(agent_name="sales_report_generator")
    
    print(f"✅ Created Data Processing Agent: {data_agent.agent_name}")
    print(f"✅ Created Analysis Agent: {analysis_agent.agent_name}")
    print(f"✅ Created Reporting Agent: {reporting_agent.agent_name}")
    
    print_subsection("Registering Agents with Orchestrator")
    
    for agent in [data_agent, analysis_agent, reporting_agent]:
        success = orchestrator.register_agent_with_orchestrator(agent)
        if success:
            capabilities = agent.get_agent_capabilities().capability_list
            print(f"✅ Registered: {agent.agent_name}")
            print(f"   Capabilities: {', '.join(capabilities)}")
    
    print_subsection("Agent Registry Statistics")
    
    status = orchestrator.get_orchestrator_status()
    agent_stats = status['agent_statistics']
    
    print(f"Total Registered Agents: {agent_stats['total_registered_agents']}")
    print(f"Idle Agents: {agent_stats['idle_agents']}")
    print(f"Busy Agents: {agent_stats['busy_agents']}")


def demonstrate_single_task_execution(orchestrator: OrchestrationEngine):
    """Demonstrate single task creation and execution"""
    print_section_header("DEMONSTRATION 2: Single Task Execution")
    
    print_subsection("Creating Data Cleaning Task")
    
    test_data = {
        'customer_records': [
            {'customer_id': 1, 'name': 'Alice Johnson', 'email': 'alice@example.com', 'total_purchases': 1500.00, 'region': 'North'},
            {'customer_id': 2, 'name': 'Bob Smith', 'email': 'bob@example.com', 'total_purchases': None, 'region': ''},
            {'customer_id': 3, 'name': 'Charlie Brown', 'email': 'charlie@example.com', 'total_purchases': 2200.50, 'region': 'South'},
            {'customer_id': 4, 'name': '', 'email': 'david@example.com', 'total_purchases': 800.00, 'region': 'East'},
        ]
    }
    
    print("Input Data:")
    print(f"  Total Records: {len(test_data['customer_records'])}")
    print(f"  Fields: customer_id, name, email, total_purchases, region")
    
    print_subsection("Executing Task")
    
    result = orchestrator.create_and_execute_task(
        task_name="clean_customer_data",
        required_capabilities=['data_cleaning'],
        input_data=test_data,
        priority=TaskPriorityLevel.HIGH,
        task_description="Clean and validate customer records"
    )
    
    if result:
        print("✅ Task Completed Successfully")
        print(f"Task ID: {result['task_id']}")
        print(f"Executed By: {result['executed_by']}")
        print(f"Status: {result['status']}")
        
        if result.get('result'):
            result_data = result['result']
            if isinstance(result_data, dict) and 'result' in result_data:
                processed_records = result_data['result']
                if isinstance(processed_records, list):
                    print(f"Records Processed: {len(processed_records)}")


def demonstrate_multi_step_workflow(orchestrator: OrchestrationEngine):
    """Demonstrate workflow with multiple steps"""
    print_section_header("DEMONSTRATION 3: Multi-Step Workflow Execution")
    
    print_subsection("Defining Sales Analytics Workflow")
    
    sales_data = {
        'transactions': [
            {'transaction_id': 'TX001', 'product': 'Widget Pro', 'amount': 299.99, 'quantity': 2, 'date': '2024-01-15'},
            {'transaction_id': 'TX002', 'product': 'Gadget Plus', 'amount': 149.99, 'quantity': 1, 'date': '2024-01-16'},
            {'transaction_id': 'TX003', 'product': 'Widget Pro', 'amount': 299.99, 'quantity': 3, 'date': '2024-01-17'},
            {'transaction_id': 'TX004', 'product': 'Doohickey', 'amount': 79.99, 'quantity': 5, 'date': '2024-01-18'},
            {'transaction_id': 'TX005', 'product': 'Gadget Plus', 'amount': 149.99, 'quantity': 2, 'date': '2024-01-19'},
        ]
    }
    
    sales_values = [299.99, 149.99, 299.99, 79.99, 149.99]
    
    workflow_steps = [
        {
            'step_name': 'clean_transaction_data',
            'required_capabilities': ['data_cleaning'],
            'priority': 'HIGH',
            'input_data': sales_data['transactions'],
            'depends_on': []
        },
        {
            'step_name': 'analyze_sales_statistics',
            'required_capabilities': ['statistical_analysis'],
            'priority': 'HIGH',
            'input_data': {'sales_amounts': sales_values},
            'depends_on': []
        },
        {
            'step_name': 'generate_weekly_summary',
            'required_capabilities': ['report_generation'],
            'priority': 'NORMAL',
            'input_data': {'period': 'Week 3', 'region': 'All Regions'},
            'depends_on': ['clean_transaction_data', 'analyze_sales_statistics']
        }
    ]
    
    print("Workflow Steps:")
    for idx, step in enumerate(workflow_steps, 1):
        print(f"  {idx}. {step['step_name']}")
        print(f"     Capabilities: {', '.join(step['required_capabilities'])}")
        print(f"     Priority: {step['priority']}")
        if step['depends_on']:
            print(f"     Depends On: {', '.join(step['depends_on'])}")
    
    print_subsection("Executing Workflow")
    
    workflow_result = orchestrator.execute_workflow_steps(workflow_steps)
    
    print(f"\nWorkflow Execution Result:")
    print(f"  Workflow ID: {workflow_result['workflow_id']}")
    print(f"  Status: {workflow_result['status']}")
    print(f"  Completed Steps: {len(workflow_result['completed_steps'])}")
    print(f"  Failed Steps: {len(workflow_result['failed_steps'])}")
    print(f"  Total Duration: {workflow_result.get('duration_seconds', 0):.2f} seconds")
    
    if workflow_result['completed_steps']:
        print(f"\nCompleted Steps:")
        for step_name in workflow_result['completed_steps']:
            print(f"  ✅ {step_name}")
    
    if workflow_result['failed_steps']:
        print(f"\nFailed Steps:")
        for step_name in workflow_result['failed_steps']:
            print(f"  ❌ {step_name}")


def demonstrate_system_monitoring(orchestrator: OrchestrationEngine):
    """Demonstrate system monitoring and statistics"""
    print_section_header("DEMONSTRATION 4: System Monitoring and Statistics")
    
    print_subsection("System Status Overview")
    
    status = orchestrator.get_orchestrator_status()
    
    print(f"Orchestrator: {status['orchestrator_name']}")
    print(f"System Uptime: {status['system_uptime_seconds']:.2f} seconds")
    print(f"Execution Strategy: {status['current_execution_strategy']}")
    
    print_subsection("Agent Statistics")
    
    agent_stats = status['agent_statistics']
    print(f"Total Registered Agents: {agent_stats['total_registered_agents']}")
    print(f"Idle Agents: {agent_stats['idle_agents']}")
    print(f"Busy Agents: {agent_stats['busy_agents']}")
    print(f"Error Agents: {agent_stats['error_agents']}")
    
    print_subsection("Task Statistics")
    
    task_stats = status['task_statistics']
    print(f"Total Tasks: {task_stats['total_tasks']}")
    for state_name, count in task_stats['tasks_by_state'].items():
        print(f"  {state_name}: {count}")
    
    print_subsection("Workflow Statistics")
    
    workflow_stats = status['workflow_statistics']
    print(f"Total Workflows Executed: {workflow_stats['total_workflows_executed']}")
    print(f"Active Workflows: {workflow_stats['active_workflows']}")
    print(f"Successful Workflows: {workflow_stats['successful_workflows']}")
    
    print_subsection("Registered Agent Details")
    
    for agent_info in status['registered_agents']:
        print(f"\nAgent: {agent_info['agent_name']}")
        print(f"  Status: {agent_info['current_status']}")
        print(f"  Capabilities: {', '.join(agent_info['capabilities']['capability_list'])}")


def demonstrate_capability_matching(orchestrator: OrchestrationEngine):
    """Demonstrate capability-based agent selection"""
    print_section_header("DEMONSTRATION 5: Intelligent Capability-Based Agent Selection")
    
    test_scenarios = [
        ("Data Cleaning Only", ['data_cleaning']),
        ("Statistical Analysis Only", ['statistical_analysis']),
        ("Report Generation Only", ['report_generation']),
        ("Data Processing Pipeline", ['data_cleaning', 'data_transformation']),
        ("Full Analytics Suite", ['statistical_analysis', 'pattern_recognition'])
    ]
    
    print("Testing Agent Selection for Various Capability Requirements:\n")
    
    for scenario_name, required_capabilities in test_scenarios:
        selected_agent = orchestrator.find_suitable_agent_for_task(required_capabilities)
        
        if selected_agent:
            capabilities = selected_agent.get_agent_capabilities().capability_list
            print(f"{scenario_name}:")
            print(f"  Required: {', '.join(required_capabilities)}")
            print(f"  Selected Agent: {selected_agent.agent_name}")
            print(f"  Agent Capabilities: {', '.join(capabilities)}")
            print(f"  Can Handle: {selected_agent.get_agent_capabilities().has_all_capabilities(required_capabilities)}")
            print()
        else:
            print(f"{scenario_name}:")
            print(f"  Required: {', '.join(required_capabilities)}")
            print(f"  ❌ No suitable agent available")
            print()


def run_complete_demonstration():
    """Run the complete orchestration system demonstration"""
    print("\n" + "=" * 80)
    print("  MULTI-AGENT ORCHESTRATION SYSTEM - COMPREHENSIVE DEMONSTRATION")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Version: 2.0.0")
    
    try:
        orchestrator = OrchestrationEngine(orchestrator_name="production_orchestrator")
        
        demonstrate_agent_registration(orchestrator)
        demonstrate_single_task_execution(orchestrator)
        demonstrate_multi_step_workflow(orchestrator)
        demonstrate_system_monitoring(orchestrator)
        demonstrate_capability_matching(orchestrator)
        
        print("\n" + "=" * 80)
        print("  DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        print("\n📋 Next Steps:")
        print("  1. Review the system architecture in docs/")
        print("  2. Run the test suite: python -m pytest tests/")
        print("  3. Explore the API layer for programmatic access")
        print("  4. Customize agents for your specific use case")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demonstration interrupted by user")
    except Exception as error:
        print(f"\n\n❌ Error during demonstration: {error}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 80)


if __name__ == "__main__":
    run_complete_demonstration()
