"""
MAOS - Multi-Agent Orchestration System
=======================================

A production-grade, enterprise-ready multi-agent orchestration system
built on modern open-source foundations.

Key Features:
  - Distributed Communication: Redis-based pub/sub for agent messaging
  - Enterprise Task Queue: RQ (Redis Queue) with retries, timeouts, priorities
  - REST API: FastAPI with automatic OpenAPI documentation
  - Production Monitoring: Prometheus metrics + structured logging
  - Multi-Tenancy: Complete tenant isolation and management
  - Advanced Analytics: Real-time metrics and anomaly detection
  - Streaming Responses: Full async streaming support
  - Agent Callbacks: Comprehensive event system for monitoring

Architecture:
  - Clean Architecture with clear separation of concerns
  - Domain-Driven Design patterns
  - Event-driven orchestration
  - RESTful API layer with FastAPI
  - Multiple storage backends (Redis, PostgreSQL, DynamoDB)

Version: 5.0.0
"""

__version__ = "5.0.0"
__author__ = "MAOS Development Team"
__license__ = "MIT"

from maos.core import (
    Agent,
    AgentMessage,
    AgentStatus,
    MessageType,
    AgentOptions,
    AgentCallbacks,
    AgentStreamResponse,
)

from maos.orchestration import (
    OrchestratorService,
    TaskManager,
    Task,
    TaskPriority,
    TaskStatus,
    ExecutionStrategy,
)

from maos.analytics import AnalyticsEngine

from maos.multi_tenancy import TenantManagementService, Tenant, TenantContext

from maos.storage import InMemoryChatStorage, ChatStorage, ChatStorageConfig

from maos.config import MAOSConfig, get_config, set_config

from maos.performance import (
    timed,
    async_timed,
    retry,
    async_retry,
    get_performance_metrics,
    get_all_performance_metrics,
    print_performance_summary,
)

from maos.llm import (
    LLMClient,
    get_llm_client,
    set_llm_client,
    LLMConfig,
    LLMResponse,
    ChatMessage,
    available_models
)

from maos.agents import (
    LLMAgent,
    LLMAgentOptions,
    ResearchAgent,
    CodeAgent,
    CreativeAgent,
    DataAnalysisAgent,
    create_agent
)

__all__ = [
    "__version__",
    # Core
    "Agent",
    "AgentMessage", 
    "AgentStatus",
    "MessageType",
    "AgentOptions",
    "AgentCallbacks",
    "AgentStreamResponse",
    # Orchestration
    "OrchestratorService",
    "TaskManager",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "ExecutionStrategy",
    # Analytics
    "get_analytics_engine",
    "AnalyticsEngine",
    "CostAttributionEngine",
    # Multi-tenancy
    "TenantManagementService",
    "Tenant",
    "TenantContext",
    # Storage
    "InMemoryChatStorage",
    "ChatStorage",
    "ChatStorageConfig",
    # Configuration
    "MAOSConfig",
    "get_config",
    "set_config",
    # Performance
    "timed",
    "async_timed",
    "retry",
    "async_retry",
    "get_performance_metrics",
    "get_all_performance_metrics",
    "print_performance_summary",
    # LLM
    "LLMClient",
    "get_llm_client",
    "set_llm_client",
    "LLMConfig",
    "LLMResponse",
    "ChatMessage",
    "available_models",
    # LLM Agents
    "LLMAgent",
    "LLMAgentOptions",
    "ResearchAgent",
    "CodeAgent",
    "CreativeAgent",
    "DataAnalysisAgent",
    "create_agent"
]
