"""
Application Services - Agent Registry Module
=======================================

Manages agent lifecycle, discovery, and capability-based matching.
Provides enterprise features for agent management including:
  - Agent registration and unregistration
  - Capability-based agent discovery
  - Agent health monitoring and heartbeat tracking
  - Agent selection and load balancing
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import threading

from multi_agent_orchestration_system.core_abstractions import (
    BaseAgent,
    AgentCapabilities,
    AgentOperationalStatus
)


class AgentRegistryService:
    """
    Central registry for managing all agents in the orchestration system.
    
    Key Features:
      - Thread-safe agent registration and management
      - Capability-based agent discovery and matching
      - Heartbeat monitoring for agent health
      - Automatic cleanup of offline agents
      - Agent selection strategies (load balancing, capability matching)
    
    Architecture:
      - In-memory storage with optional persistence layer
      - Lock-based thread safety for concurrent access
      - Background heartbeat monitoring thread
      - Event-driven updates for agent status changes
    """
    
    def __init__(self, heartbeat_timeout_seconds: int = 300):
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}
        self._registry_lock = threading.RLock()
        self._heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)
        self._last_heartbeat_check = datetime.now()
        self._registry_statistics = {
            'total_registrations': 0,
            'total_unregistrations': 0,
            'heartbeat_timeouts': 0
        }
    
    def register_new_agent(self, agent: BaseAgent) -> bool:
        """
        Register a new agent with the registry.
        
        Args:
            agent: Agent instance to register
            
        Returns:
            True if registration successful, False if agent already exists
        """
        with self._registry_lock:
            if agent.agent_name in self._agents:
                return False
            
            self._agents[agent.agent_name] = agent
            self._agent_metadata[agent.agent_name] = {
                'registered_at': datetime.now(),
                'last_heartbeat': agent.last_heartbeat_timestamp,
                'registration_count': 1
            }
            
            self._registry_statistics['total_registrations'] += 1
            
            return True
    
    def unregister_existing_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_name: Name of agent to unregister
            
        Returns:
            True if unregistration successful, False if agent not found
        """
        with self._registry_lock:
            if agent_name not in self._agents:
                return False
            
            agent = self._agents[agent_name]
            agent.update_agent_status(AgentOperationalStatus.TERMINATED)
            
            del self._agents[agent_name]
            del self._agent_metadata[agent_name]
            
            self._registry_statistics['total_unregistrations'] += 1
            
            return True
    
    def get_agent_by_name(self, agent_name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        with self._registry_lock:
            return self._agents.get(agent_name)
    
    def get_all_registered_agents(self) -> List[BaseAgent]:
        """Get list of all registered agents"""
        with self._registry_lock:
            return list(self._agents.values())
    
    def get_agents_with_capability(self, capability_name: str) -> List[BaseAgent]:
        """
        Find all agents that have a specific capability.
        
        Args:
            capability_name: Name of capability to search for
            
        Returns:
            List of agents with the specified capability
        """
        with self._registry_lock:
            matching_agents = []
            
            for agent in self._agents.values():
                capabilities = agent.get_agent_capabilities()
                if capabilities.has_capability(capability_name):
                    matching_agents.append(agent)
            
            return matching_agents
    
    def get_agents_with_all_capabilities(self, required_capabilities: List[str]) -> List[BaseAgent]:
        """
        Find all agents that have ALL specified capabilities.
        
        Args:
            required_capabilities: List of capability names
            
        Returns:
            List of agents with all required capabilities
        """
        with self._registry_lock:
            matching_agents = []
            
            for agent in self._agents.values():
                capabilities = agent.get_agent_capabilities()
                if capabilities.has_all_capabilities(required_capabilities):
                    matching_agents.append(agent)
            
            return matching_agents
    
    def get_idle_agents(self) -> List[BaseAgent]:
        """Get all agents with IDLE status"""
        with self._registry_lock:
            return [
                agent for agent in self._agents.values()
                if agent.agent_status == AgentOperationalStatus.IDLE
            ]
    
    def get_idle_agents_with_capability(self, capability_name: str) -> List[BaseAgent]:
        """Get idle agents that have a specific capability"""
        with self._registry_lock:
            matching_agents = []
            
            for agent in self._agents.values():
                if agent.agent_status != AgentOperationalStatus.IDLE:
                    continue
                
                capabilities = agent.get_agent_capabilities()
                if capabilities.has_capability(capability_name):
                    matching_agents.append(agent)
            
            return matching_agents
    
    def select_best_agent_for_task(self, required_capabilities: List[str]) -> Optional[BaseAgent]:
        """
        Select the best available agent for a task based on capabilities and load.
        
        Selection Strategy:
          1. Filter for idle agents with all required capabilities
          2. Sort by capability count (prefer specialists)
          3. Return best match
        
        Args:
            required_capabilities: List of required capabilities
            
        Returns:
            Best matching agent or None if no suitable agent found
        """
        with self._registry_lock:
            suitable_agents = []
            
            for agent in self._agents.values():
                if agent.agent_status != AgentOperationalStatus.IDLE:
                    continue
                
                capabilities = agent.get_agent_capabilities()
                if capabilities.has_all_capabilities(required_capabilities):
                    suitable_agents.append(agent)
            
            if not suitable_agents:
                return None
            
            suitable_agents.sort(
                key=lambda a: (
                    -len(a.get_agent_capabilities().capability_list),
                    -a.get_agent_capabilities().estimated_processing_speed,
                    a.last_heartbeat_timestamp
                )
            )
            
            return suitable_agents[0]
    
    def update_agent_heartbeat(self, agent_name: str) -> bool:
        """Update agent's last heartbeat timestamp"""
        with self._registry_lock:
            if agent_name not in self._agents:
                return False
            
            agent = self._agents[agent_name]
            agent.last_heartbeat_timestamp = datetime.now()
            
            if agent_name in self._agent_metadata:
                self._agent_metadata[agent_name]['last_heartbeat'] = datetime.now()
            
            return True
    
    def get_agent_status(self, agent_name: str) -> Optional[AgentOperationalStatus]:
        """Get agent's current operational status"""
        with self._registry_lock:
            agent = self._agents.get(agent_name)
            return agent.agent_status if agent else None
    
    def update_agent_status(self, agent_name: str, new_status: AgentOperationalStatus) -> bool:
        """Update agent's operational status"""
        with self._registry_lock:
            agent = self._agents.get(agent_name)
            if not agent:
                return False
            
            agent.update_agent_status(new_status)
            return True
    
    def check_and_cleanup_offline_agents(self) -> int:
        """
        Check for agents that have missed heartbeats and mark them as offline.
        
        Returns:
            Number of agents marked as offline
        """
        with self._registry_lock:
            offline_count = 0
            current_time = datetime.now()
            
            for agent_name, agent in list(self._agents.items()):
                if agent.agent_status == AgentOperationalStatus.TERMINATED:
                    continue
                
                time_since_heartbeat = current_time - agent.last_heartbeat_timestamp
                
                if time_since_heartbeat > self._heartbeat_timeout:
                    agent.update_agent_status(AgentOperationalStatus.OFFLINE)
                    self._registry_statistics['heartbeat_timeouts'] += 1
                    offline_count += 1
            
            self._last_heartbeat_check = current_time
            
            return offline_count
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        with self._registry_lock:
            status_counts = {}
            for agent in self._agents.values():
                status = agent.agent_status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            all_capabilities = set()
            for agent in self._agents.values():
                all_capabilities.update(agent.get_agent_capabilities().capability_list)
            
            return {
                'total_registered_agents': len(self._agents),
                'status_distribution': status_counts,
                'idle_agents_count': status_counts.get('idle', 0),
                'busy_agents_count': status_counts.get('busy', 0),
                'offline_agents_count': status_counts.get('offline', 0),
                'error_agents_count': status_counts.get('error', 0),
                'unique_capabilities_count': len(all_capabilities),
                'all_capabilities': sorted(list(all_capabilities)),
                'total_registrations': self._registry_statistics['total_registrations'],
                'total_unregistrations': self._registry_statistics['total_unregistrations'],
                'heartbeat_timeouts': self._registry_statistics['heartbeat_timeouts'],
                'last_heartbeat_check': self._last_heartbeat_check.isoformat()
            }
    
    def get_all_capabilities(self) -> List[str]:
        """Get list of all unique capabilities across all agents"""
        with self._registry_lock:
            all_capabilities = set()
            for agent in self._agents.values():
                all_capabilities.update(agent.get_agent_capabilities().capability_list)
            return sorted(list(all_capabilities))
    
    def get_agents_by_status(self, status: AgentOperationalStatus) -> List[BaseAgent]:
        """Get all agents with a specific status"""
        with self._registry_lock:
            return [
                agent for agent in self._agents.values()
                if agent.agent_status == status
            ]
    
    def clear_registry(self) -> None:
        """Clear all agents from registry (use with caution)"""
        with self._registry_lock:
            for agent in self._agents.values():
                agent.update_agent_status(AgentOperationalStatus.TERMINATED)
            
            self._agents.clear()
            self._agent_metadata.clear()
