"""
MAOS v12.0 - AI优化引擎
智能性能优化、成本优化、资源调度
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import math


class OptimizationType(Enum):
    """优化类型"""
    PERFORMANCE = "performance"
    COST = "cost"
    RELIABILITY = "reliability"
    SCALABILITY = "scalability"


@dataclass
class PerformanceMetrics:
    """性能指标"""
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    throughput_per_sec: float = 0.0
    error_rate: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    task_queue_length: int = 0


@dataclass
class ResourceConfig:
    """资源配置"""
    cpu_cores: float = 1.0
    memory_gb: float = 2.0
    replicas: int = 3
    max_concurrent_tasks: int = 100


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    id: str
    type: OptimizationType
    priority: int
    description: str
    expected_improvement: float
    current_config: Dict[str, Any]
    suggested_config: Dict[str, Any]
    implementation_effort: str
    risk_level: str


class PerformancePredictor:
    """性能预测器（基于ML的简化实现）"""

    def __init__(self):
        self.history: List[Dict] = []
        self.model_trained = False

    def collect_metrics(self, metrics: PerformanceMetrics, config: ResourceConfig, timestamp: datetime):
        """收集性能指标"""
        self.history.append({
            "metrics": {
                "avg_latency_ms": metrics.avg_latency_ms,
                "p95_latency_ms": metrics.p95_latency_ms,
                "throughput_per_sec": metrics.throughput_per_sec,
                "error_rate": metrics.error_rate,
            },
            "config": {
                "cpu_cores": config.cpu_cores,
                "memory_gb": config.memory_gb,
                "replicas": config.replicas,
                "max_concurrent_tasks": config.max_concurrent_tasks,
            },
            "timestamp": timestamp.isoformat(),
        })

        if len(self.history) >= 20:
            self.model_trained = True

    def predict_performance(self, target_config: ResourceConfig) -> PerformanceMetrics:
        """预测给定配置下的性能"""
        if not self.model_trained:
            return self._default_prediction(target_config)

        # 简化的ML预测逻辑
        # 实际生产中会使用真实的ML模型
        base_metrics = PerformanceMetrics()

        # 基于历史的启发式预测
        cpu_scaling_factor = min(target_config.cpu_cores / 2.0, 3.0)
        mem_scaling_factor = min(target_config.memory_gb / 4.0, 2.5)
        replica_scaling_factor = math.sqrt(target_config.replicas / 2.0)

        combined_factor = (cpu_scaling_factor * 0.5
                          + mem_scaling_factor * 0.2
                          + replica_scaling_factor * 0.3)

        base_metrics.throughput_per_sec = 8000 * combined_factor
        base_metrics.avg_latency_ms = 50 / combined_factor
        base_metrics.p95_latency_ms = 120 / combined_factor
        base_metrics.p99_latency_ms = 200 / combined_factor

        return base_metrics

    def _default_prediction(self, config: ResourceConfig) -> PerformanceMetrics:
        """默认预测（无历史数据）"""
        base = 8000 * (config.replicas / 3.0)
        return PerformanceMetrics(
            avg_latency_ms=60.0,
            p95_latency_ms=150.0,
            p99_latency_ms=250.0,
            throughput_per_sec=base,
            error_rate=0.01,
        )


class AIOptimizer:
    """AI优化引擎"""

    def __init__(self):
        self.predictor = PerformancePredictor()
        self.current_config = ResourceConfig()
        self.current_metrics = PerformanceMetrics()

    def optimize(self, optimization_type: OptimizationType = OptimizationType.PERFORMANCE) -> List[OptimizationSuggestion]:
        """执行优化分析"""
        suggestions = []

        if optimization_type == OptimizationType.PERFORMANCE:
            suggestions.extend(self._optimize_performance())
        elif optimization_type == OptimizationType.COST:
            suggestions.extend(self._optimize_cost())
        elif optimization_type == OptimizationType.RELIABILITY:
            suggestions.extend(self._optimize_reliability())
        elif optimization_type == OptimizationType.SCALABILITY:
            suggestions.extend(self._optimize_scalability())

        return sorted(suggestions, key=lambda s: -s.priority)

    def _optimize_performance(self) -> List[OptimizationSuggestion]:
        """优化性能"""
        suggestions = []

        # 1. 副本数优化
        if self.current_config.replicas < 5:
            suggestion = OptimizationSuggestion(
                id="opt-1",
                type=OptimizationType.PERFORMANCE,
                priority=90,
                description="增加副本数以提高吞吐量",
                expected_improvement=40.0,
                current_config={"replicas": self.current_config.replicas},
                suggested_config={"replicas": 5},
                implementation_effort="low",
                risk_level="low",
            )
            suggestions.append(suggestion)

        # 2. CPU资源优化
        if self.current_config.cpu_cores < 4.0:
            suggestion = OptimizationSuggestion(
                id="opt-2",
                type=OptimizationType.PERFORMANCE,
                priority=85,
                description="增加CPU核心以降低延迟",
                expected_improvement=25.0,
                current_config={"cpu_cores": self.current_config.cpu_cores},
                suggested_config={"cpu_cores": 4.0},
                implementation_effort="low",
                risk_level="low",
            )
            suggestions.append(suggestion)

        # 3. 并发度优化
        if self.current_config.max_concurrent_tasks < 200:
            suggestion = OptimizationSuggestion(
                id="opt-3",
                type=OptimizationType.PERFORMANCE,
                priority=80,
                description="提高最大并发任务数",
                expected_improvement=30.0,
                current_config={"max_concurrent_tasks": self.current_config.max_concurrent_tasks},
                suggested_config={"max_concurrent_tasks": 200},
                implementation_effort="medium",
                risk_level="medium",
            )
            suggestions.append(suggestion)

        return suggestions

    def _optimize_cost(self) -> List[OptimizationSuggestion]:
        """优化成本"""
        suggestions = []

        if self.current_config.replicas > 2 and self.current_metrics.cpu_usage_percent < 40:
            suggestion = OptimizationSuggestion(
                id="cost-1",
                type=OptimizationType.COST,
                priority=88,
                description="减少副本数以节省成本（低CPU利用率）",
                expected_improvement=30.0,
                current_config={"replicas": self.current_config.replicas},
                suggested_config={"replicas": 2},
                implementation_effort="low",
                risk_level="low",
            )
            suggestions.append(suggestion)

        if self.current_config.cpu_cores > 2.0:
            suggestion = OptimizationSuggestion(
                id="cost-2",
                type=OptimizationType.COST,
                priority=75,
                description="适当降低CPU核心（平衡成本与性能）",
                expected_improvement=20.0,
                current_config={"cpu_cores": self.current_config.cpu_cores},
                suggested_config={"cpu_cores": 2.0},
                implementation_effort="low",
                risk_level="low",
            )
            suggestions.append(suggestion)

        return suggestions

    def _optimize_reliability(self) -> List[OptimizationSuggestion]:
        """优化可靠性"""
        suggestions = []

        if self.current_config.replicas < 3:
            suggestion = OptimizationSuggestion(
                id="rel-1",
                type=OptimizationType.RELIABILITY,
                priority=95,
                description="增加副本数以提高高可用性",
                expected_improvement=40.0,
                current_config={"replicas": self.current_config.replicas},
                suggested_config={"replicas": 3},
                implementation_effort="low",
                risk_level="very_low",
            )
            suggestions.append(suggestion)

        return suggestions

    def _optimize_scalability(self) -> List[OptimizationSuggestion]:
        """优化可扩展性"""
        suggestions = []

        suggestion = OptimizationSuggestion(
            id="scale-1",
            type=OptimizationType.SCALABILITY,
            priority=78,
            description="启用自动扩缩容（基于CPU/内存使用率）",
            expected_improvement=35.0,
            current_config={"auto_scaling": "disabled"},
            suggested_config={
                "auto_scaling": "enabled",
                "min_replicas": 2,
                "max_replicas": 20,
                "target_cpu": 70,
                "target_memory": 80,
            },
            implementation_effort="medium",
            risk_level="low",
        )
        suggestions.append(suggestion)

        return suggestions

    def apply_suggestion(self, suggestion: OptimizationSuggestion) -> bool:
        """应用优化建议"""
        print(f"✅ 应用优化建议: {suggestion.description}")

        if "replicas" in suggestion.suggested_config:
            self.current_config.replicas = suggestion.suggested_config["replicas"]
        if "cpu_cores" in suggestion.suggested_config:
            self.current_config.cpu_cores = suggestion.suggested_config["cpu_cores"]
        if "max_concurrent_tasks" in suggestion.suggested_config:
            self.current_config.max_concurrent_tasks = suggestion.suggested_config["max_concurrent_tasks"]

        return True


class CostOptimizer:
    """成本优化器"""

    def __init__(self):
        self.price_data = {
            "aws": {"cpu_per_core_hour": 0.04, "mem_per_gb_hour": 0.02},
            "gcp": {"cpu_per_core_hour": 0.035, "mem_per_gb_hour": 0.018},
            "azure": {"cpu_per_core_hour": 0.038, "mem_per_gb_hour": 0.019},
        }
        self.budget_alert_threshold = 0.9

    def calculate_monthly_cost(self, config: ResourceConfig, cloud_provider: str = "aws") -> float:
        """计算月度成本"""
        prices = self.price_data.get(cloud_provider, self.price_data["aws"])

        cpu_hours = config.cpu_cores * config.replicas * 730  # 730小时/月
        mem_hours = config.memory_gb * config.replicas * 730

        monthly_cost = (
            (cpu_hours * prices["cpu_per_core_hour"])
            + (mem_hours * prices["mem_per_gb_hour"])
        )

        return monthly_cost

    def get_cloud_comparison(self, config: ResourceConfig) -> Dict[str, float]:
        """比较不同云平台成本"""
        return {
            provider: self.calculate_monthly_cost(config, provider)
            for provider in self.price_data.keys()
        }


class AutoScaler:
    """自动扩缩容器"""

    def __init__(self):
        self.min_replicas = 2
        self.max_replicas = 20
        self.target_cpu = 70
        self.target_memory = 80

    def make_decision(self, cpu_usage: float, mem_usage: float, queue_length: int) -> Optional[int]:
        """做出扩缩容决策"""
        if queue_length > 1000:
            return 1

        if cpu_usage > self.target_cpu + 10:
            return 1

        if mem_usage > self.target_memory + 10:
            return 1

        if cpu_usage < self.target_cpu - 20 and mem_usage < self.target_memory - 20:
            return -1

        return None
