"""
Application Services - Orchestration Engine Module
===============================================

Core orchestration engine that coordinates agents and tasks.
Manages workflow execution, agent coordination, and system orchestration.

Key Responsibilities:
  - Workflow creation and execution
  - Agent task assignment and coordination
  - Event-driven architecture support
  - System health monitoring

Execution Strategies:
  - Sequential: Execute tasks one after another
  - Parallel: Execute independent tasks concurrently
  - Hybrid: Combine sequential and parallel based on dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid

from multi_agent_orchestration_system.core_abstractions import (
    BaseAgent,
    AgentMessage,
    AgentMessagePayload,
    AgentMessageType,
    AgentOperationalStatus
)
from multi_agent_orchestration_system.application_services.scheduling import (
    TaskDefinition,
    TaskSchedulerService,
    TaskPriorityLevel,
    TaskLifecycleState
)


class WorkflowExecutionStrategy(Enum):
    """Workflow execution strategies for orchestrating tasks"""
    SEQUENTIAL_EXECUTION = "sequential"
    PARALLEL_EXECUTION = "parallel"
    HYBRID_EXECUTION = "hybrid"


class OrchestrationEventType(Enum):
    """Types of events emitted during orchestration"""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"


@dataclass
class WorkflowStepDefinition:
    """Definition of a single step in a workflow"""
    step_name: str
    required_capabilities: List[str]
    step_description: str = ""
    input_data_mapping: Dict[str, str] = field(default_factory=dict)
    depends_on_steps: List[str] = field(default_factory=list)
    priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL
    timeout_seconds: int = 300
    retry_configuration: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowDefinition:
    """Complete workflow definition with multiple steps"""
    workflow_id: str
    workflow_name: str
    workflow_description: str = ""
    execution_strategy: WorkflowExecutionStrategy = WorkflowExecutionStrategy.SEQUENTIAL_EXECUTION
    steps: List[WorkflowStepDefinition] = field(default_factory=list)
    created_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution"""
    workflow_id: str
    status: str
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    started_timestamp: datetime = field(default_factory=datetime.now)
    completed_timestamp: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None


class OrchestrationEngine:
    """
    Core orchestration engine that coordinates agents and manages task execution.
    
    Key Features:
      - Multi-agent coordination
      - Workflow execution strategies
      - Event-driven architecture
      - Comprehensive monitoring and logging
      - Fault tolerance and retry mechanisms
    
    Architecture:
      - Uses TaskSchedulerService for task management
      - Coordinates with AgentRegistryService for agent selection
      - Emits events for monitoring and extensibility
    """
    
    def __init__(self, orchestrator_name: str):
        self.orchestrator_name = orchestrator_name
        self.task_scheduler = TaskSchedulerService()
        self.agent_registry: Dict[str, BaseAgent] = {}
        self.event_handlers: Dict[OrchestrationEventType, List[Callable]] = {
            event_type: [] for event_type in OrchestrationEventType
        }
        self.workflow_execution_history: List[WorkflowExecutionResult] = []
        self.active_workflows: Dict[str, WorkflowExecutionResult] = {}
        self.execution_strategy = WorkflowExecutionStrategy.SEQUENTIAL_EXECUTION
        self.system_start_time = datetime.now()
        self._register_internal_event_handlers()
    
    def _register_internal_event_handlers(self) -> None:
        """Register internal handlers for system events"""
        self.register_event_handler(
            OrchestrationEventType.TASK_COMPLETED,
            self._log_task_completion
        )
        self.register_event_handler(
            OrchestrationEventType.TASK_FAILED,
            self._log_task_failure
        )
    
    def register_event_handler(
        self,
        event_type: OrchestrationEventType,
        handler: Callable
    ) -> None:
        """Register event handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        if handler not in self.event_handlers[event_type]:
            self.event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: OrchestrationEventType, event_data: Dict[str, Any]) -> None:
        """Emit event to all registered handlers"""
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event_data)
            except Exception:
                pass
    
    def _log_task_completion(self, event_data: Dict[str, Any]) -> None:
        """Internal handler for task completion logging"""
        task = event_data.get('task')
        if task:
            pass
    
    def _log_task_failure(self, event_data: Dict[str, Any]) -> None:
        """Internal handler for task failure logging"""
        task = event_data.get('task')
        error = event_data.get('error')
        if task:
            pass
    
    def register_agent_with_orchestrator(self, agent: BaseAgent) -> bool:
        """
        Register an agent with the orchestration engine.
        Agents must be registered before they can receive tasks.
        """
        if agent.agent_name in self.agent_registry:
            return False
        
        self.agent_registry[agent.agent_name] = agent
        self._emit_event(
            OrchestrationEventType.AGENT_REGISTERED,
            {'agent': agent, 'timestamp': datetime.now()}
        )
        
        return True
    
    def unregister_agent_from_orchestrator(self, agent_name: str) -> bool:
        """
        Unregister an agent from the orchestration engine.
        """
        if agent_name not in self.agent_registry:
            return False
        
        agent = self.agent_registry[agent_name]
        agent.update_agent_status(AgentOperationalStatus.TERMINATED)
        del self.agent_registry[agent_name]
        
        self._emit_event(
            OrchestrationEventType.AGENT_UNREGISTERED,
            {'agent_name': agent_name, 'timestamp': datetime.now()}
        )
        
        return True
    
    def get_registered_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get registered agent by name"""
        return self.agent_registry.get(agent_name)
    
    def get_all_registered_agents(self) -> List[BaseAgent]:
        """Get list of all registered agents"""
        return list(self.agent_registry.values())
    
    def find_suitable_agent_for_task(self, required_capabilities: List[str]) -> Optional[BaseAgent]:
        """
        Find the best available agent that can handle the required capabilities.
        
        Selection Strategy:
          1. Filter agents with matching capabilities
          2. Filter for idle agents
          3. Sort by number of capabilities (prefer specialists)
          4. Return best match
        """
        suitable_agents = []
        
        for agent in self.agent_registry.values():
            if agent.agent_status != AgentOperationalStatus.IDLE:
                continue
            
            capabilities = agent.get_agent_capabilities()
            if capabilities.has_all_capabilities(required_capabilities):
                suitable_agents.append(agent)
        
        if not suitable_agents:
            available_idle = [
                agent for agent in self.agent_registry.values()
                if agent.agent_status == AgentOperationalStatus.IDLE
            ]
            if available_idle:
                suitable_agents = available_idle
        
        if not suitable_agents:
            return None
        
        suitable_agents.sort(
            key=lambda a: (
                -len(a.get_agent_capabilities().capability_list),
                a.last_heartbeat_timestamp
            )
        )
        
        return suitable_agents[0]
    
    def create_and_execute_task(
        self,
        task_name: str,
        required_capabilities: List[str],
        input_data: Any = None,
        priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL,
        task_description: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new task and execute it immediately.
        
        Process:
          1. Create task definition
          2. Find suitable agent
          3. Assign task to agent
          4. Execute task
          5. Return result
        """
        task = self.task_scheduler.create_new_task(
            task_name=task_name,
            required_capabilities=required_capabilities,
            task_description=task_description,
            priority=priority,
            input_data=input_data
        )
        
        suitable_agent = self.find_suitable_agent_for_task(required_capabilities)
        if not suitable_agent:
            self.task_scheduler.fail_task_execution(task.task_id, "No suitable agent available")
            return None
        
        self.task_scheduler.assign_task_to_agent(task.task_id, suitable_agent.agent_name)
        self.task_scheduler.start_task_execution(task.task_id)
        suitable_agent.update_agent_status(AgentOperationalStatus.BUSY)
        
        self._emit_event(
            OrchestrationEventType.TASK_STARTED,
            {'task': task, 'agent': suitable_agent}
        )
        
        try:
            message = AgentMessage(
                sender_agent_name=self.orchestrator_name,
                receiver_agent_names=[suitable_agent.agent_name],
                message_type=AgentMessageType.TASK_REQUEST,
                payload=AgentMessagePayload(data_content={
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'input_data': task.input_data
                }),
                metadata={'task_id': task.task_id}
            )
            
            suitable_agent.receive_message(message)
            response = suitable_agent.process_task_request(message)
            
            if response and response.payload:
                result_data = response.payload.data_content
                self.task_scheduler.complete_task_successfully(task.task_id, result_data)
                
                self._emit_event(
                    OrchestrationEventType.TASK_COMPLETED,
                    {'task': task, 'result': result_data}
                )
                
                suitable_agent.update_agent_status(AgentOperationalStatus.IDLE)
                
                return {
                    'task_id': task.task_id,
                    'status': 'success',
                    'result': result_data,
                    'executed_by': suitable_agent.agent_name
                }
            else:
                self.task_scheduler.fail_task_execution(task.task_id, "Agent returned no response")
                self._emit_event(
                    OrchestrationEventType.TASK_FAILED,
                    {'task': task, 'error': 'No response from agent'}
                )
                suitable_agent.update_agent_status(AgentOperationalStatus.IDLE)
                return None
                
        except Exception as error:
            self.task_scheduler.fail_task_execution(task.task_id, str(error))
            self._emit_event(
                OrchestrationEventType.TASK_FAILED,
                {'task': task, 'error': str(error)}
            )
            suitable_agent.update_agent_status(AgentOperationalStatus.ERROR)
            return None
    
    def execute_workflow_steps(
        self,
        workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a workflow consisting of multiple steps.
        
        Workflow Step Format:
          {
            'step_name': 'step_1',
            'required_capabilities': ['capability_1'],
            'priority': 'NORMAL',
            'input_data': {...},
            'depends_on': []
          }
        """
        self.execution_strategy = WorkflowExecutionStrategy.SEQUENTIAL_EXECUTION
        
        workflow_result = WorkflowExecutionResult(
            workflow_id=str(uuid.uuid4()),
            status='in_progress',
            started_timestamp=datetime.now()
        )
        
        self.active_workflows[workflow_result.workflow_id] = workflow_result
        
        self._emit_event(
            OrchestrationEventType.WORKFLOW_STARTED,
            {'workflow': workflow_result}
        )
        
        step_results = {}
        step_dependencies_satisfied = {}
        
        for step_config in workflow_steps:
            step_name = step_config.get('step_name', f'step_{len(step_results)}')
            required_capabilities = step_config.get('required_capabilities', [])
            priority_str = step_config.get('priority', 'NORMAL')
            priority = TaskPriorityLevel[priority_str.upper()]
            input_data = step_config.get('input_data')
            depends_on = step_config.get('depends_on', [])
            
            depends_on_completed = all(
                step_name in step_results and step_name in workflow_result.completed_steps
                for step_name in depends_on
            )
            
            if not depends_on_completed:
                workflow_result.failed_steps.append(step_name)
                workflow_result.errors[step_name] = "Dependencies not satisfied"
                continue
            
            try:
                result = self.create_and_execute_task(
                    task_name=step_name,
                    required_capabilities=required_capabilities,
                    input_data=input_data,
                    priority=priority
                )
                
                if result:
                    step_results[step_name] = result
                    workflow_result.completed_steps.append(step_name)
                    workflow_result.step_results[step_name] = result
                else:
                    workflow_result.failed_steps.append(step_name)
                    workflow_result.errors[step_name] = "Task execution failed"
                    
            except Exception as error:
                workflow_result.failed_steps.append(step_name)
                workflow_result.errors[step_name] = str(error)
        
        workflow_result.completed_timestamp = datetime.now()
        workflow_result.total_duration_seconds = (
            workflow_result.completed_timestamp - workflow_result.started_timestamp
        ).total_seconds()
        
        if workflow_result.failed_steps:
            workflow_result.status = 'completed_with_errors'
        else:
            workflow_result.status = 'completed_successfully'
        
        self._emit_event(
            OrchestrationEventType.WORKFLOW_COMPLETED,
            {'workflow': workflow_result}
        )
        
        self.workflow_execution_history.append(workflow_result)
        
        return {
            'workflow_id': workflow_result.workflow_id,
            'status': workflow_result.status,
            'completed_steps': workflow_result.completed_steps,
            'failed_steps': workflow_result.failed_steps,
            'results': workflow_result.step_results,
            'errors': workflow_result.errors,
            'duration_seconds': workflow_result.total_duration_seconds
        }
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the orchestration engine.
        
        Returns:
          - Orchestrator information
          - Agent statistics
          - Task statistics
          - Workflow statistics
        """
        task_statistics = self.task_scheduler.get_system_statistics()
        
        agent_stats = {
            'total_registered_agents': len(self.agent_registry),
            'idle_agents': sum(
                1 for a in self.agent_registry.values()
                if a.agent_status == AgentOperationalStatus.IDLE
            ),
            'busy_agents': sum(
                1 for a in self.agent_registry.values()
                if a.agent_status == AgentOperationalStatus.BUSY
            ),
            'error_agents': sum(
                1 for a in self.agent_registry.values()
                if a.agent_status == AgentOperationalStatus.ERROR
            )
        }
        
        workflow_stats = {
            'total_workflows_executed': len(self.workflow_execution_history),
            'active_workflows': len(self.active_workflows),
            'successful_workflows': sum(
                1 for w in self.workflow_execution_history
                if w.status == 'completed_successfully'
            ),
            'failed_workflows': sum(
                1 for w in self.workflow_execution_history
                if w.failed_steps
            )
        }
        
        return {
            'orchestrator_name': self.orchestrator_name,
            'system_uptime_seconds': (datetime.now() - self.system_start_time).total_seconds(),
            'current_execution_strategy': self.execution_strategy.value,
            'agent_statistics': agent_stats,
            'task_statistics': task_statistics,
            'workflow_statistics': workflow_stats,
            'registered_agents': [
                agent.get_agent_info()
                for agent in self.agent_registry.values()
            ]
        }
    
    def shutdown_orchestrator(self) -> None:
        """Gracefully shutdown the orchestration engine"""
        for agent in self.agent_registry.values():
            agent.update_agent_status(AgentOperationalStatus.TERMINATED)
        
        self.agent_registry.clear()
        
        self.active_workflows.clear()


from dataclasses import dataclass, field
import uuid
