#!/usr/bin/env python3
"""
MAOS - Complete Demo Program
Showcase all features of the Multi-Agent Orchestration System
"""
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maos.services.orchestrator import OrchestratorService, ExecutionStrategy
from maos.services.task_manager import TaskPriority, TaskStatus
from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
from maos.config.settings import get_settings
from maos.infrastructure.monitoring import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("demo")

class MAOSDemo:
    """Complete MAOS demo application"""
    
    def __init__(self):
        self.settings = get_settings()
        self.orchestrator = OrchestratorService(name="maos_demo_orchestrator")
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up event handlers for demo visibility"""
        
        def on_task_created(data):
            task = data['task']
            print(f"  📋 Task created: {task.name} (ID: {task.id[:8]}...)")
        
        def on_task_assigned(data):
            task = data['task']
            agent = data['agent']
            print(f"  📤 Task assigned: {task.name} → {agent.name}")
        
        def on_task_completed(data):
            task = data['task']
            print(f"  ✅ Task completed: {task.name}")
        
        def on_task_failed(data):
            task = data['task']
            error = data.get('error', 'Unknown error')
            print(f"  ❌ Task failed: {task.name} - {error}")
        
        self.orchestrator.on_event('task_created', on_task_created)
        self.orchestrator.on_event('task_assigned', on_task_assigned)
        self.orchestrator.on_event('task_completed', on_task_completed)
        self.orchestrator.on_event('task_failed', on_task_failed)
    
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)
    
    def demo_1_agent_registration(self):
        """Demo 1: Agent registration and management"""
        self.print_header("DEMO 1: Agent Registration & Discovery")
        
        print("\nRegistering agents...")
        agents = [
            DataProcessingAgent(name="data_processor_1"),
            AnalysisAgent(name="analyst_1"),
            ReportingAgent(name="reporter_1"),
            DataProcessingAgent(name="data_processor_2"),
        ]
        
        for agent in agents:
            success = self.orchestrator.register_agent(agent)
            if success:
                print(f"  ✅ Registered: {agent.name} (capabilities: {agent.capabilities})")
        
        # Display registry stats
        stats = self.orchestrator.registry.get_statistics()
        print(f"\n📊 Registry stats: {stats['total_agents']} agents, {len(stats['capabilities'])} capabilities")
        print(f"   Capabilities available: {', '.join(stats['capabilities'])}")
        
        # Display available agents
        available = self.orchestrator.registry.get_available_agents()
        print(f"\n😴 Available agents ({len(available)}):")
        for agent in available:
            print(f"  • {agent.name} - {agent.capabilities}")
    
    def demo_2_single_task_execution(self):
        """Demo 2: Single task execution"""
        self.print_header("DEMO 2: Single Task Execution")
        
        print("\nCreating data cleaning task...")
        test_data = {
            'records': [
                {'id': 1, 'name': 'Alice', 'score': 95, 'email': 'alice@example.com'},
                {'id': 2, 'name': 'Bob', 'score': None, 'email': ''},
                {'id': 3, 'name': 'Charlie', 'score': 85, 'email': 'charlie@example.com'},
                {'id': 4, 'name': '', 'score': 70, 'email': 'david@example.com'},
            ]
        }
        
        task = self.orchestrator.create_task(
            name="clean_employee_records",
            requirements=["data_cleaning", "data_validation"],
            description="Clean and validate employee record data",
            priority=TaskPriority.HIGH,
            input_data=test_data
        )
        
        print(f"\nExecuting task: {task.name}...")
        time.sleep(0.5)  # Simulate processing
        result = self.orchestrator.execute_task(task)
        
        print(f"\n📊 Task result:")
        if result:
            print(f"  Status: {result.get('status', 'unknown')}")
            processed = result.get('processed_data', {})
            if isinstance(processed, list):
                print(f"  Processed {len(processed)} records")
            print(f"  Metadata: {result.get('agent_metadata', {})}")
    
    def demo_3_workflow_execution(self):
        """Demo 3: Multi-step workflow execution"""
        self.print_header("DEMO 3: Multi-Step Workflow Execution")
        
        print("\nSetting execution strategy to SEQUENTIAL...")
        self.orchestrator.execution_strategy = ExecutionStrategy.SEQUENTIAL
        
        # Define workflow
        sales_data = {
            'transactions': [
                {'id': 't1', 'product': 'Widget', 'amount': 29.99, 'date': '2024-01-15', 'region': 'North'},
                {'id': 't2', 'product': 'Gadget', 'amount': 49.99, 'date': '2024-01-16', 'region': 'South'},
                {'id': 't3', 'product': 'Widget', 'amount': 29.99, 'date': '2024-01-17', 'region': 'East'},
                {'id': 't4', 'product': 'Doohickey', 'amount': 19.99, 'date': '2024-01-18', 'region': 'West'},
                {'id': 't5', 'product': 'Gadget', 'amount': 49.99, 'date': '2024-01-19', 'region': 'North'},
            ],
            'values': [29.99, 49.99, 29.99, 19.99, 49.99]
        }
        
        workflow = [
            {
                'name': 'clean_sales_data',
                'requirements': ['data_cleaning'],
                'description': 'Clean raw sales transaction data',
                'priority': 'HIGH',
                'input_data': sales_data['transactions']
            },
            {
                'name': 'analyze_sales_trends',
                'requirements': ['data_analysis', 'statistical_analysis'],
                'description': 'Analyze sales performance and trends',
                'priority': 'HIGH',
                'input_data': sales_data['values']
            },
            {
                'name': 'generate_sales_report',
                'requirements': ['report_generation'],
                'description': 'Generate comprehensive sales report',
                'priority': 'NORMAL',
                'input_data': {'period': 'Week 1', 'region': 'All'}
            }
        ]
        
        print(f"\n🚀 Executing workflow with {len(workflow)} steps...")
        start_time = time.time()
        
        results = self.orchestrator.execute_workflow(workflow)
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ Workflow completed in {elapsed:.2f}s")
        print(f"✅ Results: {len(results)} tasks executed")
        
        # Display final report
        last_task_id = list(results.keys())[-1]
        last_result = results[last_task_id]
        if last_result and 'report' in last_result:
            report = last_result['report']
            print(f"\n📄 Final report: {report['title']}")
            print(f"   Summary: {report['summary']}")
    
    def demo_4_system_monitoring(self):
        """Demo 4: System monitoring and statistics"""
        self.print_header("DEMO 4: System Monitoring & Statistics")
        
        print("\n📊 System Status:")
        status = self.orchestrator.get_system_status()
        
        print(f"  Orchestrator: {status['orchestrator']}")
        print(f"  Strategy: {status['execution_strategy']}")
        
        print(f"\n🤖 Agent Stats:")
        agent_stats = status['agents']
        print(f"  Total: {agent_stats['total_agents']}")
        print(f"  Online: {agent_stats['online_agents']}")
        print(f"  Idle: {agent_stats['idle_agents']}")
        print(f"  Busy: {agent_stats['busy_agents']}")
        
        print(f"\n📋 Task Stats:")
        task_stats = status['tasks']
        print(f"  Total: {task_stats['total']}")
        print(f"  Pending: {task_stats['pending']}")
        print(f"  Running: {task_stats['running']}")
        print(f"  Completed: {task_stats['completed']}")
        print(f"  Failed: {task_stats['failed']}")
        
        print(f"\n💡 Available capabilities: {', '.join(self.orchestrator.registry.list_capabilities())}")
    
    def demo_5_capability_matching(self):
        """Demo 5: Intelligent agent selection"""
        self.print_header("DEMO 5: Capability-Based Agent Selection")
        
        test_cases = [
            ("Data cleaning only", ["data_cleaning"]),
            ("Analysis only", ["statistical_analysis"]),
            ("Reporting only", ["report_generation"]),
            ("Multi-capability", ["data_cleaning", "data_analysis"]),
        ]
        
        print("\nTesting agent selection for different requirements...")
        for desc, requirements in test_cases:
            agent = self.orchestrator.registry.select_best_agent(requirements)
            if agent:
                print(f"  🎯 {desc}:")
                print(f"     Selected: {agent.name}")
                print(f"     Capabilities: {agent.capabilities}")
                print(f"     Can handle: {agent.can_handle_task(requirements)}")
            else:
                print(f"  ❌ {desc}: No suitable agent available")
    
    def run_all_demos(self):
        """Run all demos in sequence"""
        self.print_header(f"MAOS - MULTI-AGENT ORCHESTRATION SYSTEM DEMO")
        print(f"  Version: {self.settings.app_version}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.demo_1_agent_registration()
            self.demo_2_single_task_execution()
            self.demo_3_workflow_execution()
            self.demo_4_system_monitoring()
            self.demo_5_capability_matching()
            
            self.print_header("DEMO COMPLETED SUCCESSFULLY!")
            
            print("""
  🎯 NEXT STEPS:
  1. Start the API server: `uvicorn maos.api.main:app --reload`
  2. Visit the API docs: http://localhost:8000/docs
  3. Run tests: `python -m pytest tests/ -v`
  4. Check the documentation in docs/
            """)
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Demo interrupted by user.")
        except Exception as e:
            print(f"\n\n❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.orchestrator.shutdown()

def main():
    """Main entry point"""
    demo = MAOSDemo()
    demo.run_all_demos()

if __name__ == "__main__":
    main()
