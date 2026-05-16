"""
Multi-Agent Orchestration System
多Agent编排系统 - 负责任务分解、调度和Agent协调
"""

from .agent import Agent, AgentMessage, AgentStatus
from .orchestrator import Orchestrator
from .registry import AgentRegistry
from .task_manager import Task, TaskStatus, TaskManager

__all__ = [
    'Agent',
    'AgentMessage', 
    'AgentStatus',
    'Orchestrator',
    'AgentRegistry',
    'Task',
    'TaskStatus',
    'TaskManager'
]

__version__ = '1.0.0'
