"""
MAOS v8.0 - AI驱动的智能调度器
预测性任务调度和AI优化引擎
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math


class AIStrategy(Enum):
    """AI调度策略"""
    FIFO = "fifo"
    PRIORITY = "priority"
    SHORTEST_JOB_FIRST = "sjf"
    LONGEST_JOB_FIRST = "ljf"
    ROUND_ROBIN = "round_robin"
    PREDICTIVE = "predictive"
    ML_OPTIMIZED = "ml_optimized"


@dataclass
class TaskProfile:
    """任务性能档案"""
    task_type: str
    avg_duration: float = 0.0
    std_duration: float = 0.0
    success_rate: float = 1.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    sample_count: int = 0


@dataclass
class AgentProfile:
    """Agent性能档案"""
    agent_id: str
    capabilities: List[str] = field(default_factory=list)
    avg_task_time: float = 0.0
    success_rate: float = 1.0
    current_load: float = 0.0
    task_history: List[Dict] = field(default_factory=list)
    max_concurrent_tasks: int = 10


class AIScheduler:
    """AI驱动的智能调度器"""
    
    def __init__(self, strategy: AIStrategy = AIStrategy.PREDICTIVE):
        self.strategy = strategy
        self.task_profiles: Dict[str, TaskProfile] = {}
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.performance_history: List[Dict] = []
        self.decision_history: List[Dict] = []
        self.historical_data: List[Dict] = []
        
        # 性能指标
        self.total_scheduled = 0
        self.total_executed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.avg_scheduling_time = 0.0
        
        # 预测模型（简化版，实际可用真实ML模型）
        self.prediction_weights: Dict[str, float] = {
            "capability_match": 0.4,
            "load_balance": 0.3,
            "historical_performance": 0.2,
            "resource_availability": 0.1
        }
        
        print("🤖 AIScheduler initialized with strategy:", strategy.value)
    
    def register_agent(self, agent_id: str, capabilities: List[str] = None):
        """注册Agent"""
        self.agent_profiles[agent_id] = AgentProfile(
            agent_id=agent_id,
            capabilities=capabilities or [],
            max_concurrent_tasks=10
        )
        print(f"🤖 Registered agent: {agent_id}")
    
    def record_task_completion(self, task_id: str, agent_id: str, duration: float, success: bool):
        """记录任务完成数据"""
        self.historical_data.append({
            "task_id": task_id,
            "agent_id": agent_id,
            "duration": duration,
            "success": success,
            "timestamp": time.time()
        })
        
        # 更新Agent档案
        if agent_id in self.agent_profiles:
            profile = self.agent_profiles[agent_id]
            profile.task_history.append({
                "task_id": task_id,
                "duration": duration,
                "success": success
            })
            
            # 计算统计数据
            if len(profile.task_history) > 0:
                profile.avg_task_time = sum(t["duration"] for t in profile.task_history) / len(profile.task_history)
                profile.success_rate = sum(1 for t in profile.task_history if t["success"]) / len(profile.task_history)
        
        self.total_executed += 1
        if success:
            self.total_successful += 1
        else:
            self.total_failed += 1
    
    def predict_task_duration(self, task_type: str) -> float:
        """预测任务执行时间（基于历史数据）"""
        if task_type in self.task_profiles:
            profile = self.task_profiles[task_type]
            if profile.sample_count > 0:
                return profile.avg_duration
        
        # 默认预测值
        return 5.0
    
    def select_optimal_agent(self, task_requirements: List[str], available_agents: List[str]) -> Optional[str]:
        """选择最优Agent（基于AI评分）"""
        if not available_agents:
            return None
        
        best_agent = None
        best_score = -float("inf")
        
        for agent_id in available_agents:
            score = self._calculate_agent_score(agent_id, task_requirements)
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        return best_agent
    
    def _calculate_agent_score(self, agent_id: str, task_requirements: List[str]) -> float:
        """计算Agent适合度分数"""
        if agent_id not in self.agent_profiles:
            return -float("inf")
        
        profile = self.agent_profiles[agent_id]
        score = 0.0
        
        # 能力匹配
        capability_score = 0.0
        if task_requirements:
            matches = sum(1 for req in task_requirements if req in profile.capabilities)
            capability_score = matches / len(task_requirements)
        
        score += self.prediction_weights["capability_match"] * capability_score
        
        # 负载均衡
        load_balance_score = 1.0 - (profile.current_load / profile.max_concurrent_tasks)
        score += self.prediction_weights["load_balance"] * load_balance_score
        
        # 历史表现
        historical_score = profile.success_rate
        score += self.prediction_weights["historical_performance"] * historical_score
        
        # 资源可用性
        resource_score = 0.8
        score += self.prediction_weights["resource_availability"] * resource_score
        
        return score
    
    def schedule_task(self, task_id: str, requirements: List[str], priority: int = 0) -> Optional[str]:
        """调度任务（AI驱动）"""
        start_time = time.perf_counter()
        
        # 根据策略选择Agent
        if self.strategy == AIStrategy.PREDICTIVE:
            # 预测驱动调度
            agent = self._schedule_predictive(task_id, requirements)
        elif self.strategy == AIStrategy.SHORTEST_JOB_FIRST:
            # 最短作业优先
            agent = self._schedule_shortest_job(task_id, requirements)
        elif self.strategy == AIStrategy.PRIORITY:
            # 优先级驱动
            agent = self._schedule_priority(task_id, requirements, priority)
        else:
            # 默认FIFO
            agent = self._schedule_fifo(task_id, requirements)
        
        self.total_scheduled += 1
        
        # 记录调度决策
        self.decision_history.append({
            "task_id": task_id,
            "selected_agent": agent,
            "timestamp": time.time()
        })
        
        # 计算耗时
        self.avg_scheduling_time = (self.avg_scheduling_time * (self.total_scheduled - 1) + 
                                    (time.perf_counter() - start_time)) / self.total_scheduled
        
        return agent
    
    def _schedule_predictive(self, task_id: str, requirements: List[str]) -> Optional[str]:
        """预测性调度策略"""
        available_agents = list(self.agent_profiles.keys())
        return self.select_optimal_agent(requirements, available_agents)
    
    def _schedule_shortest_job(self, task_id: str, requirements: List[str]) -> Optional[str]:
        """最短作业优先策略"""
        task_type = requirements[0] if requirements else "unknown"
        predicted_duration = self.predict_task_duration(task_type)
        available_agents = list(self.agent_profiles.keys())
        
        # 选择处理最快的Agent
        best_agent = None
        shortest_time = float("inf")
        
        for agent_id in available_agents:
            profile = self.agent_profiles[agent_id]
            if profile.avg_task_time < shortest_time:
                shortest_time = profile.avg_task_time
                best_agent = agent_id
        
        return best_agent
    
    def _schedule_priority(self, task_id: str, requirements: List[str], priority: int) -> Optional[str]:
        """优先级驱动策略"""
        available_agents = list(self.agent_profiles.keys())
        
        # 优先级越高，越选择高能力Agent
        available_agents.sort(
            key=lambda aid: len(self.agent_profiles[aid].capabilities),
            reverse=(priority > 0)
        )
        
        return available_agents[0] if available_agents else None
    
    def _schedule_fifo(self, task_id: str, requirements: List[str]) -> Optional[str]:
        """FIFO策略"""
        available_agents = list(self.agent_profiles.keys())
        return available_agents[0] if available_agents else None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "total_scheduled": self.total_scheduled,
            "total_executed": self.total_executed,
            "success_rate": (self.total_successful / self.total_executed * 100) if self.total_executed > 0 else 0,
            "avg_scheduling_time_ms": self.avg_scheduling_time * 1000,
            "agents_count": len(self.agent_profiles),
            "historical_records": len(self.historical_data)
        }
    
    def optimize(self):
        """AI优化：自动调整权重"""
        if len(self.historical_data) < 10:
            return
        
        # 基于成功率调整权重
        if self.total_successful / self.total_executed > 0.9:
            # 表现很好，稍微增加能力匹配权重
            self.prediction_weights["capability_match"] *= 1.1
        else:
            # 需要改进，增加负载均衡权重
            self.prediction_weights["load_balance"] *= 1.1
        
        # 归一化权重
        total = sum(self.prediction_weights.values())
        for key in self.prediction_weights:
            self.prediction_weights[key] /= total
        
        print("🔧 AIScheduler optimized weights:", self.prediction_weights)


class AutoScaler:
    """自动扩缩容器"""
    
    def __init__(self, min_agents: int = 2, max_agents: int = 20):
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.current_agents = min_agents
        self.performance_threshold = 0.7
    
    def decide_scaling(self, queue_length: int, avg_wait_time: float) -> str:
        """决定扩缩容策略"""
        load = queue_length / (self.current_agents * 10)
        
        if load > 0.8 and self.current_agents < self.max_agents:
            self.current_agents = min(self.current_agents + 1, self.max_agents)
            return "scale_out"
        elif load < 0.3 and self.current_agents > self.min_agents:
            self.current_agents = max(self.current_agents - 1, self.min_agents)
            return "scale_in"
        else:
            return "stable"
