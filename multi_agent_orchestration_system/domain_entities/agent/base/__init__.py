"""
Domain Entities - Agent Base Module
================================

Provides the base agent class and agent-related domain models.
This module contains the foundational agent abstractions used throughout the system.

Core Components:
  - BaseAgent: Abstract base class for all agents
  - AgentFactory: Factory for creating agent instances
  - AgentValidator: Validation utilities for agent configurations
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod

from multi_agent_orchestration_system.core_abstractions import (
    BaseAgent as CoreBaseAgent,
    AgentMessage,
    AgentMessagePayload,
    AgentMessageType,
    AgentCapabilities,
    AgentOperationalStatus
)


class DomainAgent(CoreBaseAgent):
    """
    Domain-specific agent base class extending the core agent abstraction.
    Provides additional domain logic and integration points.
    
    This class can be further specialized for specific domains or use cases.
    """
    
    def __init__(
        self,
        agent_name: str,
        agent_description: str = "",
        capability_list: Optional[List[str]] = None,
        domain_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            agent_name=agent_name,
            agent_description=agent_description,
            capability_list=capability_list or [],
            metadata=metadata or {}
        )
        
        self.domain_tags = domain_tags or []
        self.execution_history: List[Dict[str, Any]] = []
        self.performance_metrics = {
            'total_tasks_processed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_processing_time_seconds': 0.0
        }
    
    def record_task_execution(
        self,
        task_id: str,
        task_name: str,
        success: bool,
        duration_seconds: float,
        error_message: Optional[str] = None
    ) -> None:
        """Record task execution in agent's history"""
        execution_record = {
            'task_id': task_id,
            'task_name': task_name,
            'success': success,
            'duration_seconds': duration_seconds,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.execution_history.append(execution_record)
        
        self.performance_metrics['total_tasks_processed'] += 1
        if success:
            self.performance_metrics['successful_tasks'] += 1
        else:
            self.performance_metrics['failed_tasks'] += 1
        
        self.performance_metrics['total_processing_time_seconds'] += duration_seconds
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        total = self.performance_metrics['total_tasks_processed']
        
        if total == 0:
            success_rate = 0.0
            avg_duration = 0.0
        else:
            success_rate = (self.performance_metrics['successful_tasks'] / total) * 100
            avg_duration = (
                self.performance_metrics['total_processing_time_seconds'] / total
            )
        
        return {
            'agent_name': self.agent_name,
            'total_tasks': total,
            'successful_tasks': self.performance_metrics['successful_tasks'],
            'failed_tasks': self.performance_metrics['failed_tasks'],
            'success_rate_percent': round(success_rate, 2),
            'average_duration_seconds': round(avg_duration, 3),
            'total_processing_time_seconds': round(
                self.performance_metrics['total_processing_time_seconds'], 2
            )
        }
    
    def get_detailed_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information including performance"""
        base_info = self.get_agent_info()
        
        return {
            **base_info,
            'domain_tags': self.domain_tags,
            'performance_summary': self.get_performance_summary(),
            'recent_execution_history': self.execution_history[-10:]
        }


class AgentFactory:
    """
    Factory class for creating agent instances.
    Provides convenient methods for creating standard agent types.
    """
    
    @staticmethod
    def create_data_processing_agent(agent_name: str = "data_processor") -> DomainAgent:
        """Create a configured data processing agent"""
        from multi_agent_orchestration_system.domain_entities.agent.examples import DataProcessingAgent
        return DataProcessingAgent(agent_name=agent_name)
    
    @staticmethod
    def create_analysis_agent(agent_name: str = "data_analyzer") -> DomainAgent:
        """Create a configured analysis agent"""
        from multi_agent_orchestration_system.domain_entities.agent.examples import DataAnalysisAgent
        return DataAnalysisAgent(agent_name=agent_name)
    
    @staticmethod
    def create_reporting_agent(agent_name: str = "report_generator") -> DomainAgent:
        """Create a configured reporting agent"""
        from multi_agent_orchestration_system.domain_entities.agent.examples import ReportGenerationAgent
        return ReportGenerationAgent(agent_name=agent_name)
    
    @staticmethod
    def create_custom_agent(
        agent_name: str,
        capability_list: List[str],
        agent_description: str = "",
        domain_tags: Optional[List[str]] = None
    ) -> DomainAgent:
        """Create a custom agent with specified capabilities"""
        return DomainAgent(
            agent_name=agent_name,
            agent_description=agent_description,
            capability_list=capability_list,
            domain_tags=domain_tags
        )


class AgentValidator:
    """
    Utility class for validating agent configurations and states.
    """
    
    @staticmethod
    def validate_agent_name(agent_name: str) -> tuple[bool, Optional[str]]:
        """Validate agent name meets requirements"""
        if not agent_name:
            return False, "Agent name cannot be empty"
        
        if len(agent_name) < 3:
            return False, "Agent name must be at least 3 characters"
        
        if len(agent_name) > 100:
            return False, "Agent name must be less than 100 characters"
        
        if not agent_name.replace('_', '').replace('-', '').isalnum():
            return False, "Agent name must be alphanumeric (with optional _ and -)"
        
        return True, None
    
    @staticmethod
    def validate_capability_list(capability_list: List[str]) -> tuple[bool, Optional[str]]:
        """Validate capability list"""
        if not capability_list:
            return False, "Capability list cannot be empty"
        
        for capability in capability_list:
            if not capability or not capability.strip():
                return False, "Capability names cannot be empty"
            
            if len(capability) > 50:
                return False, f"Capability '{capability}' exceeds maximum length of 50"
        
        if len(capability_list) != len(set(capability_list)):
            return False, "Capability list contains duplicates"
        
        return True, None
    
    @staticmethod
    def validate_agent_for_registration(agent: DomainAgent) -> tuple[bool, List[str]]:
        """Validate agent can be registered"""
        errors = []
        
        valid, error = AgentValidator.validate_agent_name(agent.agent_name)
        if not valid:
            errors.append(error)
        
        valid, error = AgentValidator.validate_capability_list(
            agent.get_agent_capabilities().capability_list
        )
        if not valid:
            errors.append(error)
        
        return len(errors) == 0, errors
