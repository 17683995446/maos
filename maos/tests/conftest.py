"""
Pytest配置和共享Fixtures
========================

提供测试所需的共享fixtures、自动化设置和Mock配置。

Features:
    - 异步测试支持
    - 共享fixtures
    - Mock配置
    - 参数化测试支持
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_agent_options() -> Dict[str, Any]:
    """示例Agent配置选项"""
    from maos.core import AgentOptions

    return AgentOptions(
        name="test_agent",
        description="测试用Agent",
        capabilities=["test", "mock"],
        save_chat=True,
        log_debug_trace=False,
        max_queue_size=100,
        processing_timeout=30.0
    )


@pytest.fixture
def mock_agent_callbacks():
    """Mock Agent回调"""
    callbacks = MagicMock()
    callbacks.on_agent_start = AsyncMock(return_value={"tracking_id": "test123"})
    callbacks.on_agent_end = AsyncMock(return_value=None)
    callbacks.on_error = AsyncMock(return_value=None)
    return callbacks


@pytest.fixture
def sample_agent_message() -> Dict[str, Any]:
    """示例Agent消息"""
    from maos.core import AgentMessage, MessageType

    return AgentMessage(
        sender="test_sender",
        receivers=["test_receiver"],
        msg_type=MessageType.REQUEST,
        content={"action": "test", "data": "sample"},
        metadata={"priority": "normal"}
    )


@pytest.fixture
def sample_task_data() -> Dict[str, Any]:
    """示例任务数据"""
    return {
        "name": "test_task",
        "description": "测试任务描述",
        "requirements": ["test", "mock"],
        "priority": 2,
        "input_data": {"test_key": "test_value"},
        "dependencies": [],
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_conversation_data() -> List[Dict[str, Any]]:
    """示例对话数据"""
    return [
        {
            "role": "user",
            "content": "测试消息1",
            "timestamp": "2025-01-01T10:00:00"
        },
        {
            "role": "assistant",
            "content": "测试回复1",
            "timestamp": "2025-01-01T10:01:00"
        }
    ]


@pytest.fixture
def sample_analytics_metrics() -> List[Dict[str, Any]]:
    """示例分析指标数据"""
    return [
        {"metric_name": "test_metric_1", "value": 100.0, "labels": {"env": "test"}},
        {"metric_name": "test_metric_2", "value": 200.0, "labels": {"env": "test"}},
        {"metric_name": "test_metric_3", "value": 150.0, "labels": {"env": "prod"}},
    ]


@pytest.fixture
def mock_storage_backend():
    """Mock存储后端"""
    storage = MagicMock()
    storage.save_chat_message = AsyncMock(return_value=True)
    storage.fetch_chat = AsyncMock(return_value=[])
    storage.fetch_all_chats = AsyncMock(return_value=[])
    storage.delete_chat = AsyncMock(return_value=True)
    storage.initialize = AsyncMock(return_value=None)
    storage.close = AsyncMock(return_value=None)
    storage.health_check = AsyncMock(return_value={"healthy": True})
    return storage


@pytest.fixture
def mock_message_broker():
    """Mock消息代理"""
    broker = MagicMock()
    broker.publish = MagicMock(return_value=None)
    broker.subscribe = MagicMock(return_value=None)
    broker.get_messages = MagicMock(return_value=[])
    return broker


@pytest.fixture
def agent_registry_instance():
    """创建Agent注册表实例"""
    from maos.orchestration.orchestrator import AgentRegistry

    return AgentRegistry()


@pytest.fixture
def task_manager_instance():
    """创建任务管理器实例"""
    from maos.orchestration.task_manager import TaskManager

    return TaskManager()


@pytest.fixture
def orchestrator_service_instance():
    """创建编排器服务实例"""
    from maos.orchestration.orchestrator import OrchestratorService, ExecutionStrategy

    return OrchestratorService(
        name="test_orchestrator",
        max_concurrent_tasks=5,
        execution_strategy=ExecutionStrategy.HYBRID,
        enable_streaming=True
    )


@pytest.fixture
def analytics_engine_instance():
    """创建分析引擎实例"""
    from maos.analytics.engine import AnalyticsEngine

    return AnalyticsEngine()


@pytest.fixture
def cost_attribution_instance():
    """创建成本归因引擎实例"""
    from maos.analytics.engine import CostAttributionEngine

    return CostAttributionEngine()


@pytest.fixture
def in_memory_storage_instance():
    """创建内存存储实例"""
    from maos.storage.in_memory import InMemoryChatStorage

    storage = InMemoryChatStorage()
    return storage


@pytest.fixture
def sample_agent_instances():
    """创建示例Agent实例"""
    from maos.core import AgentOptions
    from maos.agents import DataProcessingAgent, AnalysisAgent, ReportingAgent

    data_agent = DataProcessingAgent(
        options=AgentOptions(
            name="data_processor",
            description="数据处理器",
            capabilities=["data_cleaning", "data_transformation", "data_validation"]
        )
    )

    analysis_agent = AnalysisAgent(
        options=AgentOptions(
            name="analyzer",
            description="数据分析器",
            capabilities=["data_analysis", "statistical_analysis", "pattern_recognition"]
        )
    )

    reporting_agent = ReportingAgent(
        options=AgentOptions(
            name="reporter",
            description="报告生成器",
            capabilities=["report_generation", "format_conversion", "data_visualization"]
        )
    )

    return {
        "data_agent": data_agent,
        "analysis_agent": analysis_agent,
        "reporting_agent": reporting_agent
    }


@pytest.fixture
def workflow_definition():
    """创建示例工作流定义"""
    from maos.orchestration.orchestrator import Workflow, WorkflowStep, ExecutionStrategy

    return Workflow(
        name="test_workflow",
        description="测试工作流",
        steps=[
            WorkflowStep(
                name="step1",
                requirements=["data_cleaning"],
                description="数据清洗步骤",
                priority=3
            ),
            WorkflowStep(
                name="step2",
                requirements=["data_analysis"],
                description="分析步骤",
                priority=2,
                dependencies=["step1"]
            ),
            WorkflowStep(
                name="step3",
                requirements=["report_generation"],
                description="报告生成步骤",
                priority=1,
                dependencies=["step2"]
            )
        ],
        strategy=ExecutionStrategy.SEQUENTIAL,
        metadata={"version": "1.0", "test": True}
    )


@pytest.fixture
def cleanup_after_test():
    """测试后清理fixture"""
    cleanup_functions: List[callable] = []

    def register_cleanup(func: callable) -> None:
        cleanup_functions.append(func)

    yield register_cleanup

    for func in cleanup_functions:
        try:
            func()
        except Exception as e:
            print(f"Cleanup error: {e}")


@pytest.fixture(autouse=True)
def reset_singletons():
    """自动重置单例实例（用于测试隔离）"""
    import maos.analytics.engine as analytics_module

    analytics_module._analytics_instance = None
    analytics_module._cost_attribution_instance = None

    yield

    analytics_module._analytics_instance = None
    analytics_module._cost_attribution_instance = None


def pytest_configure(config):
    """Pytest全局配置"""
    config.addinivalue_line("markers", "async: 异步测试标记")
    config.addinivalue_line("markers", "integration: 集成测试标记")
    config.addinivalue_line("markers", "unit: 单元测试标记")
    config.addinivalue_line("markers", "slow: 慢速测试标记")


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    for item in items:
        if "async" in item.keywords or asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


def pytest_runtest_setup(item):
    """测试运行前设置"""
    if asyncio.iscoroutinefunction(item.function):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                asyncio.set_event_loop(asyncio.new_event_loop())
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
