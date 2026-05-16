"""
Multi-Agent Orchestration System - Main Package
=============================================

A comprehensive, production-ready multi-agent orchestration platform built with
modern Python patterns and enterprise-grade architecture.

Key Modules:
  - config_management: Type-safe configuration and settings
  - core_abstractions: Fundamental abstractions and base classes
  - domain_entities: Domain models and agent implementations
  - application_services: Business logic services
  - infrastructure_layer: Messaging, monitoring, persistence
  - interface_layer: API and CLI interfaces

Architecture follows clean architecture principles with clear separation of concerns.

Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "MAOS Development Team"
__description__ = "Enterprise Multi-Agent Orchestration System"

from multi_agent_orchestration_system.core_abstractions import (
    BaseAgent,
    AgentOperationalStatus,
    AgentMessageType,
    AgentMessage,
    AgentCapabilities
)

from multi_agent_orchestration_system.domain_entities.agent.examples import (
    DataProcessingAgent,
    DataAnalysisAgent,
    ReportGenerationAgent
)

from multi_agent_orchestration_system.application_services.orchestration import (
    OrchestrationEngine,
    WorkflowExecutionStrategy,
    WorkflowDefinition
)

from multi_agent_orchestration_system.application_services.scheduling import (
    TaskSchedulerService,
    TaskDefinition,
    TaskPriorityLevel,
    TaskLifecycleState
)

from multi_agent_orchestration_system.application_services.registry import (
    AgentRegistryService
)

__all__ = [
    "BaseAgent",
    "AgentOperationalStatus",
    "AgentMessageType",
    "AgentMessage",
    "AgentCapabilities",
    "DataProcessingAgent",
    "DataAnalysisAgent",
    "ReportGenerationAgent",
    "OrchestrationEngine",
    "WorkflowExecutionStrategy",
    "WorkflowDefinition",
    "TaskSchedulerService",
    "TaskDefinition",
    "TaskPriorityLevel",
    "TaskLifecycleState",
    "AgentRegistryService"
]
