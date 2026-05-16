"""
Agent Registry Module
Agent注册表 - 管理Agent的注册、发现和选择
"""

from typing import Dict, List, Optional, Any
from agent import Agent, AgentStatus


class AgentRegistry:
    """Agent注册表"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> bool:
        """注册Agent"""
        if agent.name in self.agents:
            return False
        self.agents[agent.name] = agent
        return True

    def unregister(self, agent_name: str) -> bool:
        """注销Agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            return True
        return False

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """获取Agent"""
        return self.agents.get(agent_name)

    def get_all_agents(self) -> List[Agent]:
        """获取所有Agent"""
        return list(self.agents.values())

    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """根据能力获取Agent列表"""
        return [
            agent for agent in self.agents.values()
            if agent.has_capability(capability)
        ]

    def get_available_agents(self) -> List[Agent]:
        """获取空闲的Agent"""
        return [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
        ]

    def get_available_agents_for_task(self, requirements: List[str]) -> List[Agent]:
        """获取能够处理任务的空闲Agent"""
        available = self.get_available_agents()
        suitable = [
            agent for agent in available
            if agent.can_handle_task(requirements)
        ]
        return suitable

    def select_best_agent(self, requirements: List[str]) -> Optional[Agent]:
        """选择最适合的Agent"""
        suitable_agents = self.get_available_agents_for_task(requirements)
        if not suitable_agents:
            suitable_agents = self.get_available_agents()
        if not suitable_agents:
            return None
        return suitable_agents[0]

    def update_agent_status(self, agent_name: str, status: AgentStatus) -> bool:
        """更新Agent状态"""
        agent = self.agents.get(agent_name)
        if agent:
            agent.update_status(status)
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.agents)
        idle = len(self.get_available_agents())
        busy = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
        error = len([a for a in self.agents.values() if a.status == AgentStatus.ERROR])

        capability_counts: Dict[str, int] = {}
        for agent in self.agents.values():
            for cap in agent.capabilities:
                capability_counts[cap] = capability_counts.get(cap, 0) + 1

        return {
            'total_agents': total,
            'idle_agents': idle,
            'busy_agents': busy,
            'error_agents': error,
            'capabilities': capability_counts
        }

    def list_capabilities(self) -> List[str]:
        """列出所有能力"""
        capabilities = set()
        for agent in self.agents.values():
            capabilities.update(agent.capabilities)
        return sorted(list(capabilities))
