"""
MAOS v6.0 - 性能基准测试框架
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
import psutil
import statistics
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float  # ops/second
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'iterations': self.iterations,
            'total_time': f"{self.total_time:.4f}s",
            'avg_time': f"{self.avg_time*1000:.2f}ms",
            'min_time': f"{self.min_time*1000:.2f}ms",
            'max_time': f"{self.max_time*1000:.2f}ms",
            'std_dev': f"{self.std_dev*1000:.2f}ms",
            'throughput': f"{self.throughput:.2f} ops/s",
            'memory_mb': f"{self.memory_mb:.2f}MB",
            'cpu_percent': f"{self.cpu_percent:.1f}%"
        }


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(self, warmup_runs: int = 3, measurement_runs: int = 10):
        self.warmup_runs = warmup_runs
        self.measurement_runs = measurement_runs
        self.results: List[BenchmarkResult] = []
    
    def benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 1000,
        async_func: bool = False
    ) -> BenchmarkResult:
        """运行基准测试"""
        print(f"\n📊 Benchmark: {name}")
        print(f"   Iterations: {iterations}")
        
        # 预热
        if async_func:
            asyncio.run(self._warmup_async(func, self.warmup_runs))
        else:
            self._warmup_sync(func, self.warmup_runs)
        
        # 测量
        times = []
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        if async_func:
            times = asyncio.run(self._measure_async(func, iterations))
        else:
            times = self._measure_sync(func, iterations)
        
        # 资源使用
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_used = final_memory - initial_memory
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # 计算统计
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=sum(times),
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            throughput=iterations / sum(times),
            memory_mb=memory_used,
            cpu_percent=cpu_percent
        )
        
        self.results.append(result)
        
        # 打印结果
        print(f"   ✅ Completed:")
        print(f"      Total: {result.total_time:.4f}s")
        print(f"      Avg: {result.avg_time*1000:.2f}ms")
        print(f"      Throughput: {result.throughput:.2f} ops/s")
        print(f"      Memory: {result.memory_mb:.2f}MB")
        
        return result
    
    def _warmup_sync(self, func: Callable, runs: int):
        """同步预热"""
        for _ in range(runs):
            func()
    
    def _measure_sync(self, func: Callable, iterations: int) -> List[float]:
        """同步测量"""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            times.append(time.perf_counter() - start)
        return times
    
    async def _warmup_async(self, func: Callable, runs: int):
        """异步预热"""
        for _ in range(runs):
            await func()
    
    async def _measure_async(self, func: Callable, iterations: int) -> List[float]:
        """异步测量"""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await func()
            times.append(time.perf_counter() - start)
        return times
    
    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 80)
        print("  Performance Benchmark Summary")
        print("=" * 80)
        
        print(f"\n{'Benchmark':<30} {'Throughput':<20} {'Avg Time':<15} {'Memory':<15}")
        print("-" * 80)
        
        for result in sorted(self.results, key=lambda x: x.throughput, reverse=True):
            print(f"{result.name:<30} {result.throughput:>15.2f} ops/s {result.avg_time*1000:>10.2f}ms {result.memory_mb:>10.2f}MB")
        
        print("=" * 80)


# 具体基准测试
def run_core_benchmarks():
    """运行核心模块基准测试"""
    runner = BenchmarkRunner(warmup_runs=2, measurement_runs=5)
    
    print("\n" + "=" * 80)
    print("  MAOS v6.0 - Core Module Benchmarks")
    print("=" * 80)
    
    # 1. 配置系统
    def test_config():
        from maos.config import MAOSConfig
        config = MAOSConfig()
        _ = config.system_name
    
    runner.benchmark("Config Creation", test_config, iterations=10000)
    
    # 2. Agent创建
    def test_agent():
        from maos.core.agent import Agent, AgentStatus
        class TestAgent(Agent):
            async def _process_message_impl(self, message):
                pass
        agent = TestAgent(agent_id="bench-agent", capabilities=["test"])
        _ = agent.status
    
    runner.benchmark("Agent Creation", test_agent, iterations=1000)
    
    # 3. 任务创建
    def test_task_creation():
        from maos.orchestration import TaskManager, TaskPriority
        manager = TaskManager()
        task = manager.create_task(name="Bench", requirements=["test"], priority=TaskPriority.NORMAL)
    
    runner.benchmark("Task Creation", test_task_creation, iterations=5000)
    
    # 4. 任务调度
    def test_task_scheduling():
        from maos.orchestration import TaskManager, TaskPriority
        manager = TaskManager()
        for i in range(10):
            manager.create_task(name=f"Task-{i}", requirements=["test"], priority=TaskPriority.NORMAL)
        _ = manager.get_pending_tasks()
    
    runner.benchmark("Task Scheduling (10 tasks)", test_task_scheduling, iterations=1000)
    
    # 5. 监控记录
    def test_monitoring():
        from maos.monitoring import record_metric
        record_metric("bench.metric", 1.0, "counter")
    
    runner.benchmark("Metric Recording", test_monitoring, iterations=10000)
    
    # 6. 日志记录
    def test_logging():
        from maos.monitoring import get_logger
        logger = get_logger("bench")
        logger.info("Benchmark log entry")
    
    runner.benchmark("Log Recording", test_logging, iterations=5000)
    
    # 打印摘要
    runner.print_summary()


def run_llm_benchmarks():
    """运行LLM基准测试"""
    runner = BenchmarkRunner(warmup_runs=1, measurement_runs=3)
    
    print("\n" + "=" * 80)
    print("  MAOS v6.0 - LLM Module Benchmarks")
    print("=" * 80)
    
    # 1. LLM Client初始化
    def test_llm_init():
        from maos.llm import LLMClient
        client = LLMClient()
        _ = client.is_available()
    
    runner.benchmark("LLM Client Init", test_llm_init, iterations=100)
    
    # 2. 聊天消息构建
    def test_message_building():
        from maos.llm import ChatMessage
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there")
        ]
        _ = len(messages)
    
    runner.benchmark("Message Building (3 msgs)", test_message_building, iterations=1000)
    
    # 打印摘要
    runner.print_summary()


async def run_all_benchmarks():
    """运行所有基准测试"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║         MAOS v6.0 - Performance Benchmark Suite                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    # 系统信息
    print("\n🖥️  System Information:")
    print(f"   CPU Count: {psutil.cpu_count()}")
    print(f"   Memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f}GB")
    print(f"   Python: {sys.version.split()[0]}")
    
    # 运行基准测试
    run_core_benchmarks()
    run_llm_benchmarks()
    
    print("\n" + "=" * 80)
    print("  🎉 All Benchmarks Completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
