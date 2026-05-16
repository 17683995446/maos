"""
Interface Layer - REST API Module
================================

FastAPI-based REST API for the Multi-Agent Orchestration System.
Provides comprehensive endpoints for agent management, task execution, and monitoring.

Key Endpoints:
  - /health: Health check endpoints
  - /api/v1/agents: Agent CRUD operations
  - /api/v1/tasks: Task management
  - /api/v1/workflows: Workflow execution
  - /api/v1/stats: System statistics and monitoring
  - /metrics: Prometheus metrics endpoint

Architecture:
  - FastAPI: Modern async web framework
  - Pydantic: Data validation and serialization
  - OpenAPI: Auto-generated API documentation
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, AnyStr
from datetime import datetime
from enum import Enum

from multi_agent_orchestration_system.application_services.orchestration import (
    OrchestrationEngine
)
from multi_agent_orchestration_system.application_services.scheduling import (
    TaskPriorityLevel,
    TaskLifecycleState
)
from multi_agent_orchestration_system.domain_entities.agent.examples import (
    DataProcessingAgent,
    DataAnalysisAgent,
    ReportGenerationAgent
)
from multi_agent_orchestration_system.infrastructure_layer.observability import (
    PrometheusMetricsCollector,
    HealthCheckEndpoint,
    StructuredLogger
)
from multi_agent_orchestration_system.config_management import (
    ApplicationConfiguration,
    get_application_configuration
)

logger = StructuredLogger.get_logger("api")
config = get_application_configuration()

app = FastAPI(
    title="Multi-Agent Orchestration System API",
    description="Enterprise-grade API for managing agents, tasks, and workflows",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_collector = PrometheusMetricsCollector()
health_check = HealthCheckEndpoint()

orchestrator: Optional[OrchestrationEngine] = None


class AgentStatusEnum(str, Enum):
    """Agent status enumeration for API"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"
    OFFLINE = "offline"


class TaskPriorityEnum(str, Enum):
    """Task priority enumeration for API"""
    LOWEST = "lowest"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent"""
    agent_name: str = Field(..., min_length=1, max_length=100, description="Unique agent name")
    agent_description: str = Field(default="", max_length=500, description="Agent description")
    agent_type: str = Field(default="custom", description="Agent type: data_processor, analyzer, reporter, or custom")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Agent name must be alphanumeric with optional _ and -')
        return v


class AgentResponse(BaseModel):
    """Response model for agent information"""
    agent_name: str
    agent_description: str
    capabilities: List[str]
    status: str
    registered_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreateRequest(BaseModel):
    """Request model for creating a task"""
    task_name: str = Field(..., min_length=1, max_length=200, description="Task name")
    task_description: str = Field(default="", max_length=500, description="Task description")
    required_capabilities: List[str] = Field(..., min_length=1, description="Required agent capabilities")
    priority: TaskPriorityEnum = Field(default=TaskPriorityEnum.NORMAL, description="Task priority")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Task input data")
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Task timeout in seconds")
    retry_count: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")


class TaskResponse(BaseModel):
    """Response model for task information"""
    task_id: str
    task_name: str
    task_description: str
    required_capabilities: List[str]
    priority: str
    status: str
    assigned_agent: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class WorkflowStepRequest(BaseModel):
    """Request model for a workflow step"""
    step_name: str = Field(..., description="Step name")
    required_capabilities: List[str] = Field(..., description="Required capabilities")
    priority: TaskPriorityEnum = Field(default=TaskPriorityEnum.NORMAL)
    input_data: Optional[Dict[str, Any]] = None
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow"""
    workflow_name: str = Field(..., description="Workflow name")
    workflow_description: str = Field(default="", description="Workflow description")
    execution_strategy: str = Field(default="sequential", description="sequential, parallel, or hybrid")
    steps: List[WorkflowStepRequest] = Field(..., min_length=1, description="Workflow steps")


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution"""
    workflow_id: str
    status: str
    completed_steps: List[str]
    failed_steps: List[str]
    total_duration_seconds: Optional[float] = None
    started_at: str
    completed_at: Optional[str] = None


class SystemStatsResponse(BaseModel):
    """Response model for system statistics"""
    orchestrator_name: str
    system_uptime_seconds: float
    total_agents: int
    idle_agents: int
    busy_agents: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_workflows: int
    available_capabilities: List[str]


class HealthCheckResponse(BaseModel):
    """Response model for health checks"""
    status: str
    timestamp: str
    checks: Optional[Dict[str, Any]] = None
    uptime_seconds: Optional[float] = None


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator and services on startup"""
    global orchestrator
    orchestrator = OrchestrationEngine(orchestrator_name="api_orchestrator")
    
    data_agent = DataProcessingAgent(agent_name="api_data_processor")
    analysis_agent = DataAnalysisAgent(agent_name="api_analyzer")
    reporting_agent = ReportGenerationAgent(agent_name="api_reporter")
    
    orchestrator.register_agent_with_orchestrator(data_agent)
    orchestrator.register_agent_with_orchestrator(analysis_agent)
    orchestrator.register_agent_with_orchestrator(reporting_agent)
    
    health_check.register_check("orchestrator", lambda: (True, "Orchestrator running"))
    
    logger.info("API server started", version="2.0.0")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if orchestrator:
        orchestrator.shutdown_orchestrator()
    logger.info("API server stopped")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Multi-Agent Orchestration System API",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"], response_model=HealthCheckResponse)
async def health_check_endpoint():
    """Basic health check endpoint"""
    liveness = health_check.check_liveness()
    return HealthCheckResponse(
        status="healthy",
        timestamp=liveness['timestamp'],
        uptime_seconds=liveness['uptime_seconds']
    )


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with all component status"""
    return health_check.get_detailed_status()


@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    if orchestrator:
        uptime = (datetime.now() - datetime.fromisoformat(
            orchestrator.system_start_time.isoformat()
        )).total_seconds()
        metrics_collector.update_system_uptime(uptime)
    
    return PlainTextResponse(
        content=metrics_collector.get_metrics().decode('utf-8'),
        media_type="text/plain"
    )


@app.post("/api/v1/agents", tags=["Agents"], status_code=201)
async def create_agent(request: AgentCreateRequest):
    """Register a new agent"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    agent_type_map = {
        'data_processor': DataProcessingAgent,
        'analyzer': DataAnalysisAgent,
        'reporter': ReportGenerationAgent
    }
    
    agent_class = agent_type_map.get(request.agent_type, None)
    if agent_class:
        agent = agent_class(agent_name=request.agent_name)
    else:
        from multi_agent_orchestration_system.core_abstractions import BaseAgent
        agent = BaseAgent(
            agent_name=request.agent_name,
            agent_description=request.agent_description,
            capability_list=request.capabilities,
            metadata=request.metadata
        )
    
    success = orchestrator.register_agent_with_orchestrator(agent)
    
    if not success:
        raise HTTPException(status_code=409, detail="Agent already exists")
    
    metrics_collector.set_agents_count(
        orchestrator.get_orchestrator_status()['agent_statistics']['total_registered_agents']
    )
    
    return {
        "status": "success",
        "message": f"Agent '{request.agent_name}' registered successfully",
        "agent": AgentResponse(
            agent_name=agent.agent_name,
            agent_description=agent.agent_description,
            capabilities=agent.get_agent_capabilities().capability_list,
            status=agent.agent_status.value,
            metadata=agent.metadata.custom_properties if hasattr(agent, 'metadata') else {}
        ).model_dump()
    }


@app.get("/api/v1/agents", tags=["Agents"])
async def list_agents(status: Optional[AgentStatusEnum] = None):
    """List all registered agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    agents = orchestrator.get_all_registered_agents()
    
    if status:
        agents = [a for a in agents if a.agent_status.value == status.value]
    
    return {
        "total": len(agents),
        "agents": [
            AgentResponse(
                agent_name=a.agent_name,
                agent_description=a.agent_description,
                capabilities=a.get_agent_capabilities().capability_list,
                status=a.agent_status.value,
                last_heartbeat=a.last_heartbeat_timestamp.isoformat()
            ).model_dump()
            for a in agents
        ]
    }


@app.get("/api/v1/agents/{agent_name}", tags=["Agents"])
async def get_agent(agent_name: str):
    """Get agent by name"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    agent = orchestrator.get_registered_agent(agent_name)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        agent_name=agent.agent_name,
        agent_description=agent.agent_description,
        capabilities=agent.get_agent_capabilities().capability_list,
        status=agent.agent_status.value,
        last_heartbeat=agent.last_heartbeat_timestamp.isoformat()
    ).model_dump()


@app.delete("/api/v1/agents/{agent_name}", tags=["Agents"])
async def delete_agent(agent_name: str):
    """Unregister an agent"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    success = orchestrator.unregister_agent_from_orchestrator(agent_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "success", "message": f"Agent '{agent_name}' unregistered"}


@app.post("/api/v1/tasks", tags=["Tasks"], status_code=201)
async def create_task(request: TaskCreateRequest):
    """Create and execute a new task"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    priority_map = {
        TaskPriorityEnum.LOWEST: TaskPriorityLevel.LOWEST,
        TaskPriorityEnum.LOW: TaskPriorityLevel.LOW,
        TaskPriorityEnum.NORMAL: TaskPriorityLevel.NORMAL,
        TaskPriorityEnum.HIGH: TaskPriorityLevel.HIGH,
        TaskPriorityEnum.CRITICAL: TaskPriorityLevel.CRITICAL,
        TaskPriorityEnum.URGENT: TaskPriorityLevel.URGENT
    }
    
    result = orchestrator.create_and_execute_task(
        task_name=request.task_name,
        required_capabilities=request.required_capabilities,
        input_data=request.input_data,
        priority=priority_map[request.priority],
        task_description=request.task_description
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Task execution failed")
    
    task = orchestrator.task_scheduler.get_task_by_id(result['task_id'])
    
    return {
        "status": "success",
        "task_id": result['task_id'],
        "executed_by": result['executed_by'],
        "result": result.get('result'),
        "task": TaskResponse(
            task_id=task.task_id,
            task_name=task.task_name,
            task_description=task.task_description,
            required_capabilities=task.required_capabilities,
            priority=task.priority.name.lower(),
            status=task.lifecycle_state.value,
            assigned_agent=task.assigned_agent_name,
            created_at=task.created_timestamp.isoformat(),
            started_at=task.started_timestamp.isoformat() if task.started_timestamp else None,
            completed_at=task.completed_timestamp.isoformat() if task.completed_timestamp else None
        ).model_dump()
    }


@app.get("/api/v1/tasks", tags=["Tasks"])
async def list_tasks(status: Optional[str] = None):
    """List all tasks"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    tasks = list(orchestrator.task_scheduler.task_registry.values())
    
    if status:
        tasks = [t for t in tasks if t.lifecycle_state.value == status]
    
    return {
        "total": len(tasks),
        "tasks": [
            TaskResponse(
                task_id=t.task_id,
                task_name=t.task_name,
                task_description=t.task_description,
                required_capabilities=t.required_capabilities,
                priority=t.priority.name.lower(),
                status=t.lifecycle_state.value,
                assigned_agent=t.assigned_agent_name,
                created_at=t.created_timestamp.isoformat(),
                started_at=t.started_timestamp.isoformat() if t.started_timestamp else None,
                completed_at=t.completed_timestamp.isoformat() if t.completed_timestamp else None,
                error_message=t.error_message
            ).model_dump()
            for t in tasks
        ]
    }


@app.get("/api/v1/tasks/{task_id}", tags=["Tasks"])
async def get_task(task_id: str):
    """Get task by ID"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    task = orchestrator.task_scheduler.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        task_id=task.task_id,
        task_name=task.task_name,
        task_description=task.task_description,
        required_capabilities=task.required_capabilities,
        priority=task.priority.name.lower(),
        status=task.lifecycle_state.value,
        assigned_agent=task.assigned_agent_name,
        created_at=task.created_timestamp.isoformat(),
        started_at=task.started_timestamp.isoformat() if task.started_timestamp else None,
        completed_at=task.completed_timestamp.isoformat() if task.completed_timestamp else None,
        error_message=task.error_message
    ).model_dump()


@app.post("/api/v1/workflows", tags=["Workflows"], status_code=201)
async def create_workflow(request: WorkflowCreateRequest):
    """Execute a workflow"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    workflow_steps = [
        {
            'step_name': step.step_name,
            'required_capabilities': step.required_capabilities,
            'priority': step.priority.value,
            'input_data': step.input_data,
            'depends_on': step.depends_on
        }
        for step in request.steps
    ]
    
    result = orchestrator.execute_workflow_steps(workflow_steps)
    
    metrics_collector.record_workflow_executed(result['status'])
    
    return WorkflowExecutionResponse(
        workflow_id=result['workflow_id'],
        status=result['status'],
        completed_steps=result['completed_steps'],
        failed_steps=result['failed_steps'],
        total_duration_seconds=result.get('duration_seconds'),
        started_at=datetime.now().isoformat(),
        completed_at=datetime.now().isoformat()
    ).model_dump()


@app.get("/api/v1/stats", tags=["Statistics"])
async def get_statistics():
    """Get comprehensive system statistics"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    status = orchestrator.get_orchestrator_status()
    
    return SystemStatsResponse(
        orchestrator_name=status['orchestrator_name'],
        system_uptime_seconds=status['system_uptime_seconds'],
        total_agents=status['agent_statistics']['total_registered_agents'],
        idle_agents=status['agent_statistics']['idle_agents'],
        busy_agents=status['agent_statistics']['busy_agents'],
        total_tasks=status['task_statistics']['total_tasks'],
        completed_tasks=status['task_statistics']['tasks_by_state'].get('completed_success', 0),
        failed_tasks=status['task_statistics']['tasks_by_state'].get('completed_failure', 0),
        total_workflows=status['workflow_statistics']['total_workflows_executed'],
        available_capabilities=orchestrator.get_orchestrator_status()['agent_statistics']
    ).model_dump()


@app.get("/api/v1/capabilities", tags=["Capabilities"])
async def list_capabilities():
    """List all available capabilities"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    agents = orchestrator.get_all_registered_agents()
    capabilities = set()
    
    for agent in agents:
        capabilities.update(agent.get_agent_capabilities().capability_list)
    
    return {
        "total": len(capabilities),
        "capabilities": sorted(list(capabilities))
    }
