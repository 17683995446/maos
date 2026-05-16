"""
Interface Layer - CLI Module
=========================

Command-line interface for the Multi-Agent Orchestration System.
Provides interactive and scriptable access to all MAOS functionality.

Commands:
  - agent: Manage agents (list, create, delete, info)
  - task: Manage tasks (create, list, status, cancel)
  - workflow: Execute and manage workflows
  - stats: System statistics and monitoring
  - serve: Start the API server

Architecture:
  - Typer: Modern CLI framework with type hints
  - Rich: Rich console output with colors and formatting
  - Pydantic: Data validation for CLI arguments
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box
from datetime import datetime

from multi_agent_orchestration_system.application_services.orchestration import (
    OrchestrationEngine
)
from multi_agent_orchestration_system.application_services.scheduling import (
    TaskPriorityLevel
)
from multi_agent_orchestration_system.domain_entities.agent.examples import (
    DataProcessingAgent,
    DataAnalysisAgent,
    ReportGenerationAgent
)

app_cli = typer.Typer(
    name="maos",
    help="Multi-Agent Orchestration System CLI",
    add_completion=False
)
console = Console()


@app_cli.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="API server host"),
    port: int = typer.Option(8000, help="API server port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
    workers: int = typer.Option(1, help="Number of workers")
):
    """Start the MAOS API server"""
    console.print(Panel.fit(
        "[bold blue]Starting MAOS API Server[/bold blue]\n"
        f"Host: {host}:{port}\n"
        f"Workers: {workers}\n"
        f"Reload: {reload}"
    ))
    
    try:
        import uvicorn
        from multi_agent_orchestration_system.interface_layer.api import app
        
        uvicorn.run(
            "multi_agent_orchestration_system.interface_layer.api:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers
        )
    except ImportError:
        console.print("[red]Error: uvicorn not installed[/red]")
        console.print("[yellow]Install with: pip install uvicorn[/yellow]")


@app_cli.command()
def version():
    """Show MAOS version information"""
    console.print(Panel.fit(
        "[bold green]Multi-Agent Orchestration System[/bold green]\n"
        "Version: 2.0.0\n"
        "Architecture: Enterprise-Grade Multi-Agent Platform"
    ))


@app_cli.command()
def agents(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all agents"),
    create: Optional[str] = typer.Option(None, "--create", "-c", help="Create new agent"),
    agent_type: str = typer.Option("custom", help="Agent type: data_processor, analyzer, reporter"),
    delete: Optional[str] = typer.Option(None, "--delete", "-d", help="Delete agent by name"),
    info: Optional[str] = typer.Option(None, "--info", "-i", help="Show agent info")
):
    """Manage agents"""
    orchestrator = OrchestrationEngine(orchestrator_name="cli_orchestrator")
    
    console.print("[bold cyan]Agent Management[/bold cyan]\n")
    
    if create:
        console.print(f"Creating agent: {create}")
        
        agent_map = {
            'data_processor': DataProcessingAgent,
            'analyzer': DataAnalysisAgent,
            'reporter': ReportGenerationAgent
        }
        
        agent_class = agent_map.get(agent_type, None)
        if agent_class:
            agent = agent_class(agent_name=create)
        else:
            from multi_agent_orchestration_system.core_abstractions import BaseAgent
            agent = BaseAgent(agent_name=create, capability_list=[])
        
        if orchestrator.register_agent_with_orchestrator(agent):
            console.print(f"[green]✓ Agent '{create}' created successfully[/green]")
        else:
            console.print(f"[red]✗ Agent '{create}' already exists[/red]")
    
    elif delete:
        console.print(f"Deleting agent: {delete}")
        if orchestrator.unregister_agent_from_orchestrator(delete):
            console.print(f"[green]✓ Agent '{delete}' deleted successfully[/green]")
        else:
            console.print(f"[red]✗ Agent '{delete}' not found[/red]")
    
    elif info:
        agent = orchestrator.get_registered_agent(info)
        if agent:
            table = Table(box=box.ROUNDED)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Name", agent.agent_name)
            table.add_row("Status", agent.agent_status.value)
            table.add_row("Capabilities", ", ".join(agent.get_agent_capabilities().capability_list))
            table.add_row("Last Heartbeat", agent.last_heartbeat_timestamp.isoformat())
            
            console.print(table)
        else:
            console.print(f"[red]✗ Agent '{info}' not found[/red]")
    
    elif list_all:
        agents = orchestrator.get_all_registered_agents()
        
        if not agents:
            console.print("[yellow]No agents registered[/yellow]")
            return
        
        table = Table(title="Registered Agents", box=box.ROUNDED)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Status", style="yellow")
        table.add_column("Capabilities", style="green")
        table.add_column("Last Heartbeat", style="blue")
        
        for agent in agents:
            table.add_row(
                agent.agent_name,
                agent.agent_status.value,
                ", ".join(agent.get_agent_capabilities().capability_list[:3]),
                agent.last_heartbeat_timestamp.strftime("%H:%M:%S")
            )
        
        console.print(table)
        console.print(f"\n[bold]Total Agents:[/bold] {len(agents)}")
    
    else:
        console.print("[yellow]Use --list, --create, --delete, or --info[/yellow]")


@app_cli.command()
def tasks(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all tasks"),
    create: Optional[str] = typer.Option(None, "--create", "-c", help="Create and execute task"),
    task_name: str = typer.Option("unnamed_task", help="Task name"),
    capabilities: str = typer.Option("data_cleaning", help="Required capabilities (comma-separated)"),
    priority: str = typer.Option("normal", help="Priority: lowest, low, normal, high, critical, urgent"),
    input_data: str = typer.Option("{}", help="Input data as JSON string"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter tasks by status")
):
    """Manage tasks"""
    orchestrator = OrchestrationEngine(orchestrator_name="cli_orchestrator")
    
    data_agent = DataProcessingAgent(agent_name="cli_data_processor")
    orchestrator.register_agent_with_orchestrator(data_agent)
    
    console.print("[bold cyan]Task Management[/bold cyan]\n")
    
    if create or task_name != "unnamed_task":
        import json
        
        cap_list = [c.strip() for c in capabilities.split(',')]
        
        priority_map = {
            'lowest': TaskPriorityLevel.LOWEST,
            'low': TaskPriorityLevel.LOW,
            'normal': TaskPriorityLevel.NORMAL,
            'high': TaskPriorityLevel.HIGH,
            'critical': TaskPriorityLevel.CRITICAL,
            'urgent': TaskPriorityLevel.URGENT
        }
        
        try:
            input_json = json.loads(input_data)
        except:
            input_json = {"data": input_data}
        
        console.print(f"Creating task: {task_name}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Executing task...", total=None)
            
            result = orchestrator.create_and_execute_task(
                task_name=task_name,
                required_capabilities=cap_list,
                input_data=input_json,
                priority=priority_map.get(priority.lower(), TaskPriorityLevel.NORMAL)
            )
        
        if result:
            console.print(f"[green]✓ Task executed successfully[/green]")
            console.print(f"Task ID: {result['task_id']}")
            console.print(f"Executed by: {result['executed_by']}")
        else:
            console.print(f"[red]✗ Task execution failed[/red]")
    
    elif list_all:
        all_tasks = list(orchestrator.task_scheduler.task_registry.values())
        
        if status:
            all_tasks = [t for t in all_tasks if t.lifecycle_state.value == status]
        
        if not all_tasks:
            console.print("[yellow]No tasks found[/yellow]")
            return
        
        table = Table(title="Tasks", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Priority", style="blue")
        table.add_column("Agent", style="green")
        table.add_column("Created", style="magenta")
        
        for task in all_tasks:
            table.add_row(
                task.task_name,
                task.lifecycle_state.value,
                task.priority.name,
                task.assigned_agent_name or "-",
                task.created_timestamp.strftime("%H:%M:%S")
            )
        
        console.print(table)
        console.print(f"\n[bold]Total Tasks:[/bold] {len(all_tasks)}")
    
    else:
        console.print("[yellow]Use --list or provide task details[/yellow]")


@app_cli.command()
def workflows(
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute a workflow"),
    name: str = typer.Option("cli_workflow", help="Workflow name"),
    steps: str = typer.Option("data_cleaning,statistical_analysis,report_generation", 
                              help="Steps as comma-separated capabilities"),
    strategy: str = typer.Option("sequential", help="Execution strategy: sequential, parallel, hybrid")
):
    """Execute workflows"""
    orchestrator = OrchestrationEngine(orchestrator_name="cli_workflow_orchestrator")
    
    data_agent = DataProcessingAgent(agent_name="wf_data_processor")
    analysis_agent = DataAnalysisAgent(agent_name="wf_analyzer")
    reporter_agent = ReportGenerationAgent(agent_name="wf_reporter")
    
    orchestrator.register_agent_with_orchestrator(data_agent)
    orchestrator.register_agent_with_orchestrator(analysis_agent)
    orchestrator.register_agent_with_orchestrator(reporter_agent)
    
    console.print("[bold cyan]Workflow Execution[/bold cyan]\n")
    
    if execute:
        cap_list = [c.strip() for c in steps.split(',')]
        
        workflow_steps = [
            {
                'step_name': f'step_{i+1}_{cap}',
                'required_capabilities': [cap],
                'priority': 'NORMAL',
                'input_data': {'step': i+1, 'capability': cap}
            }
            for i, cap in enumerate(cap_list)
        ]
        
        console.print(f"Executing workflow: {name}")
        console.print(f"Steps: {len(workflow_steps)}")
        console.print(f"Strategy: {strategy}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Executing workflow...", total=None)
            
            result = orchestrator.execute_workflow_steps(workflow_steps)
        
        console.print(f"[green]✓ Workflow completed[/green]")
        console.print(f"Status: {result['status']}")
        console.print(f"Completed Steps: {len(result['completed_steps'])}")
        console.print(f"Failed Steps: {len(result['failed_steps'])}")
        
        if result['completed_steps']:
            console.print("\n[bold green]Completed Steps:[/bold green]")
            for step in result['completed_steps']:
                console.print(f"  ✓ {step}")
        
        if result['failed_steps']:
            console.print("\n[bold red]Failed Steps:[/bold red]")
            for step in result['failed_steps']:
                console.print(f"  ✗ {step}")
    else:
        console.print("[yellow]Use --execute with workflow details[/yellow]")


@app_cli.command()
def stats():
    """Show system statistics"""
    orchestrator = OrchestrationEngine(orchestrator_name="cli_stats_orchestrator")
    
    data_agent = DataProcessingAgent(agent_name="stats_data_agent")
    analysis_agent = DataAnalysisAgent(agent_name="stats_analysis_agent")
    
    orchestrator.register_agent_with_orchestrator(data_agent)
    orchestrator.register_agent_with_orchestrator(analysis_agent)
    
    console.print("[bold cyan]System Statistics[/bold cyan]\n")
    
    status = orchestrator.get_orchestrator_status()
    
    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green", justify="right")
    
    table.add_row("Orchestrator", status['orchestrator_name'])
    table.add_row("Uptime (seconds)", f"{status['system_uptime_seconds']:.2f}")
    table.add_row("Total Agents", str(status['agent_statistics']['total_registered_agents']))
    table.add_row("Idle Agents", str(status['agent_statistics']['idle_agents']))
    table.add_row("Busy Agents", str(status['agent_statistics']['busy_agents']))
    table.add_row("Total Tasks", str(status['task_statistics']['total_tasks']))
    table.add_row("Completed Tasks", str(status['task_statistics']['tasks_by_state'].get('completed_success', 0)))
    table.add_row("Failed Tasks", str(status['task_statistics']['tasks_by_state'].get('completed_failure', 0)))
    table.add_row("Total Workflows", str(status['workflow_statistics']['total_workflows_executed']))
    
    console.print(table)
    
    console.print("\n[bold]Task Status Distribution:[/bold]")
    for state, count in status['task_statistics']['tasks_by_state'].items():
        if count > 0:
            console.print(f"  {state}: {count}")


if __name__ == "__main__":
    app_cli()
