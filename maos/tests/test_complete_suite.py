"""
MAOS 完整测试套件
包含单元测试、集成测试和系统测试
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from maos.core import (
    Agent, AgentOptions, AgentStatus, AgentMessage, 
    MessageType, AgentCallbacks, CallbackManager
)
from maos.orchestration import (
    OrchestratorService, ExecutionStrategy, 
    TaskManager, Task, TaskStatus, TaskPriority,
    Workflow, WorkflowStep
)
from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
from maos.storage import InMemoryChatStorage, ChatStorageConfig
from maos.analytics import get_analytics_engine, AnalyticsEngine, CostAttributionEngine
from maos.multi_tenancy import TenantManagementService, Tenant, TenantContext
from maos.types import (
    ConversationMessage, ParticipantRole, MessageContentType,
    StreamingChunk, StreamingStatus
)
from maos.utils import Logger, generate_uuid, Timer, registry


class TestCoreAgent:
    """Agent基类测试"""
    
    def test_agent_creation(self):
        """测试Agent创建"""
        options = AgentOptions(name="TestAgent", description="Test Description")
        agent = Agent(options)
        
        assert agent.name == "TestAgent"
        assert agent.description == "Test Description"
        assert agent.status == AgentStatus.IDLE
        assert len(agent.capabilities) == 0
    
    def test_agent_with_capabilities(self):
        """测试带能力的Agent"""
        options = AgentOptions(name="TestAgent", capabilities=["data_cleaning", "analysis"])
        agent = Agent(options)
        
        assert "data_cleaning" in agent.capabilities
        assert "analysis" in agent.capabilities
        assert agent.has_capability("data_cleaning") is True
        assert agent.has_capability("unknown") is False
    
    def test_agent_status_change(self):
        """测试Agent状态变更"""
        agent = Agent(AgentOptions(name="TestAgent"))
        
        assert agent.status == AgentStatus.IDLE
        
        agent.set_status(AgentStatus.BUSY)
        assert agent.status == AgentStatus.BUSY
        
        agent.set_status(AgentStatus.IDLE)
        assert agent.status == AgentStatus.IDLE
    
    def test_agent_message_creation(self):
        """测试Agent消息创建"""
        msg = AgentMessage(
            sender="AgentA",
            receivers=["AgentB"],
            content={"data": "test"},
            message_type=MessageType.REQUEST
        )
        
        assert msg.sender == "AgentA"
        assert msg.receivers == ["AgentB"]
        assert msg.content == {"data": "test"}
        assert msg.message_type == MessageType.REQUEST
        assert msg.timestamp is not None
    
    def test_agent_message_serialization(self):
        """测试Agent消息序列化"""
        msg = AgentMessage(
            sender="AgentA",
            receivers=["AgentB"],
            content={"data": "test"}
        )
        
        serialized = msg.to_dict()
        assert "sender" in serialized
        assert "content" in serialized
        assert "timestamp" in serialized


class TestCallbacks:
    """回调系统测试"""
    
    def test_callback_manager_creation(self):
        """测试回调管理器创建"""
        manager = CallbackManager()
        assert len(manager._callbacks) == 0
    
    def test_callback_registration(self):
        """测试回调注册"""
        manager = CallbackManager()
        callback = MagicMock()
        
        manager.on("test_event", callback)
        assert "test_event" in manager._callbacks
        assert len(manager._callbacks["test_event"]) == 1
    
    def test_callback_emission(self):
        """测试回调触发"""
        manager = CallbackManager()
        callback = MagicMock()
        
        manager.on("test_event", callback)
        manager.emit("test_event", {"data": "test"})
        
        callback.assert_called_once_with({"data": "test"})


class TestOrchestration:
    """编排系统测试"""
    
    def test_orchestrator_creation(self):
        """测试Orchestrator创建"""
        orchestrator = OrchestratorService(name="TestOrchestrator")
        
        assert orchestrator.name == "TestOrchestrator"
        assert orchestrator.execution_strategy == ExecutionStrategy.HYBRID
        assert orchestrator.running is False
    
    def test_agent_registration(self):
        """测试Agent注册"""
        orchestrator = OrchestratorService()
        agent = DataProcessingAgent(AgentOptions(name="DataAgent"))
        
        result = orchestrator.register_agent(agent)
        assert result is True
        
        registered = orchestrator.agent_registry.get_agent("DataAgent")
        assert registered == agent
    
    def test_agent_unregistration(self):
        """测试Agent注销"""
        orchestrator = OrchestratorService()
        agent = DataProcessingAgent(AgentOptions(name="DataAgent"))
        
        orchestrator.register_agent(agent)
        result = orchestrator.unregister_agent("DataAgent")
        
        assert result is True
        assert orchestrator.agent_registry.get_agent("DataAgent") is None
    
    def test_multiple_agents(self):
        """测试多个Agent注册"""
        orchestrator = OrchestratorService()
        
        agent1 = DataProcessingAgent(AgentOptions(name="Agent1"))
        agent2 = AnalysisAgent(AgentOptions(name="Agent2"))
        agent3 = ReportingAgent(AgentOptions(name="Agent3"))
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)
        
        status = orchestrator.get_system_status()
        assert status["agents"]["total"] == 3


class TestTaskManager:
    """任务管理器测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        manager = TaskManager()
        task = manager.create_task(
            name="TestTask",
            requirements=["data_cleaning"],
            priority=TaskPriority.HIGH
        )
        
        assert task.name == "TestTask"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
    
    def test_task_status_update(self):
        """测试任务状态更新"""
        manager = TaskManager()
        task = manager.create_task(name="TestTask", requirements=["test"])
        
        result = manager.update_task_status(task.id, TaskStatus.RUNNING)
        assert result is True
        
        updated_task = manager.get_task(task.id)
        assert updated_task.status == TaskStatus.RUNNING
    
    def test_task_priority(self):
        """测试任务优先级"""
        manager = TaskManager()
        
        task1 = manager.create_task(name="Low", requirements=["test"], priority=TaskPriority.LOW)
        task2 = manager.create_task(name="High", requirements=["test"], priority=TaskPriority.HIGH)
        
        assert task1.priority == TaskPriority.LOW
        assert task2.priority == TaskPriority.HIGH
        assert task2.priority > task1.priority
    
    def test_get_tasks_by_status(self):
        """测试按状态获取任务"""
        manager = TaskManager()
        
        task1 = manager.create_task(name="Task1", requirements=["test"])
        task2 = manager.create_task(name="Task2", requirements=["test"])
        
        manager.update_task_status(task2.id, TaskStatus.COMPLETED)
        manager.completed_tasks.append(task2)
        
        pending = manager.get_tasks_by_status(TaskStatus.PENDING)
        completed = manager.get_tasks_by_status(TaskStatus.COMPLETED)
        
        assert len(pending) == 1
        assert len(completed) == 1


class TestStorage:
    """存储系统测试"""
    
    @pytest.mark.asyncio
    async def test_in_memory_storage_creation(self):
        """测试内存存储创建"""
        storage = InMemoryChatStorage(auto_cleanup=False)
        await storage.initialize()
        
        assert storage is not None
        assert len(storage._chats) == 0
    
    @pytest.mark.asyncio
    async def test_save_and_fetch_message(self):
        """测试保存和获取消息"""
        storage = InMemoryChatStorage(auto_cleanup=False)
        await storage.initialize()
        
        msg = ConversationMessage(
            role=ParticipantRole.USER,
            content="Hello World"
        )
        
        await storage.save_chat_message(
            user_id="user1",
            session_id="session1",
            agent_id="agent1",
            message=msg
        )
        
        messages = await storage.fetch_chat("user1", "session1", "agent1")
        assert len(messages) == 1
        assert messages[0].content == "Hello World"
    
    @pytest.mark.asyncio
    async def test_fetch_all_chats(self):
        """测试获取所有聊天"""
        storage = InMemoryChatStorage(auto_cleanup=False)
        await storage.initialize()
        
        msg1 = ConversationMessage(role=ParticipantRole.USER, content="Hello 1")
        msg2 = ConversationMessage(role=ParticipantRole.USER, content="Hello 2")
        
        await storage.save_chat_message("user1", "session1", "agent1", msg1)
        await storage.save_chat_message("user1", "session2", "agent1", msg2)
        
        all_chats = await storage.fetch_all_chats()
        assert len(all_chats) == 2


class TestAnalytics:
    """分析引擎测试"""
    
    def test_analytics_engine_creation(self):
        """测试分析引擎创建"""
        engine = AnalyticsEngine()
        assert engine is not None
        assert len(engine._metrics_store) == 0
    
    def test_record_metric(self):
        """测试记录指标"""
        engine = AnalyticsEngine()
        
        engine.record_metric("test.metric", 100.0)
        engine.record_metric("test.metric", 200.0)
        
        metrics = engine.get_all_metrics()
        assert "test.metric" in metrics
        assert len(metrics["test.metric"]) == 2
    
    def test_get_dashboard_data(self):
        """测试获取仪表板数据"""
        engine = AnalyticsEngine()
        
        engine.record_metric("cpu.usage", 50.0)
        engine.record_metric("memory.usage", 75.0)
        
        data = engine.get_dashboard_data()
        assert "recent_metrics" in data
        assert len(data["recent_metrics"]) >= 2
    
    def test_metrics_with_labels(self):
        """测试带标签的指标"""
        engine = AnalyticsEngine()
        
        engine.record_metric("requests.total", 100, labels={"endpoint": "/api"})
        engine.record_metric("requests.total", 200, labels={"endpoint": "/health"})
        
        metrics = engine.get_all_metrics()
        assert "requests.total" in metrics
        assert len(metrics["requests.total"]) == 2


class TestMultiTenancy:
    """多租户测试"""
    
    def test_tenant_creation(self):
        """测试租户创建"""
        service = TenantManagementService()
        tenant = service.create_tenant("TestCorp", "test.corp")
        
        assert tenant.tenant_name == "TestCorp"
        assert tenant.domain == "test.corp"
        assert tenant.tenant_id is not None
    
    def test_tenant_activation(self):
        """测试租户激活"""
        service = TenantManagementService()
        tenant = service.create_tenant("TestCorp", "test.corp")
        
        service.activate_tenant(tenant.tenant_id)
        context = TenantContext.get_current()
        
        assert context is not None
        assert context.tenant_id == tenant.tenant_id
    
    def test_get_tenant(self):
        """测试获取租户"""
        service = TenantManagementService()
        tenant = service.create_tenant("TestCorp", "test.corp")
        
        retrieved = service.get_tenant(tenant.tenant_id)
        assert retrieved == tenant
    
    def test_list_tenants(self):
        """测试列出租户"""
        service = TenantManagementService()
        
        service.create_tenant("Corp1", "corp1.com")
        service.create_tenant("Corp2", "corp2.com")
        
        tenants = service.list_tenants()
        assert len(tenants) == 2


class TestTypes:
    """类型定义测试"""
    
    def test_conversation_message_creation(self):
        """测试对话消息创建"""
        msg = ConversationMessage(
            role=ParticipantRole.USER,
            content="Hello",
            sender="User1"
        )
        
        assert msg.role == ParticipantRole.USER
        assert msg.content == "Hello"
        assert msg.sender == "User1"
        assert msg.timestamp is not None
    
    def test_conversation_message_serialization(self):
        """测试对话消息序列化"""
        msg = ConversationMessage(
            role=ParticipantRole.USER,
            content="Hello"
        )
        
        data = msg.to_dict()
        assert "role" in data
        assert "content" in data
        assert "timestamp" in data
    
    def test_streaming_chunk(self):
        """测试流式数据块"""
        chunk = StreamingChunk(
            content="Hello",
            status=StreamingStatus.IN_PROGRESS
        )
        
        assert chunk.content == "Hello"
        assert chunk.status == StreamingStatus.IN_PROGRESS
    
    def test_legacy_compatibility(self):
        """测试Legacy兼容性"""
        from maos.types.conversation import ConversationMessage as NewMessage
        from maos.core.agent import AgentMessage as OldMessage
        
        new_msg = NewMessage(role=ParticipantRole.USER, content="Hello")
        legacy = new_msg.to_legacy_format()
        
        assert isinstance(legacy, dict)
        assert "content" in legacy


class TestUtilities:
    """工具函数测试"""
    
    def test_generate_uuid(self):
        """测试UUID生成"""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        
        assert uuid1 is not None
        assert len(uuid1) > 0
        assert uuid1 != uuid2
    
    def test_logger_creation(self):
        """测试Logger创建"""
        logger = Logger.get_logger("test")
        
        assert logger is not None
        logger.info("Test message")  # Should not raise
    
    def test_timer(self):
        """测试Timer"""
        with Timer() as timer:
            time.sleep(0.01)
        
        assert timer.elapsed > 0
        assert timer.elapsed < 1.0
    
    def test_metrics_registry(self):
        """测试指标注册表"""
        registry.counter("test.counter").inc()
        registry.counter("test.counter").inc()
        
        assert "test.counter" in registry._counters


class TestExampleAgents:
    """示例Agent测试"""
    
    def test_data_processing_agent(self):
        """测试数据处理Agent"""
        agent = DataProcessingAgent(AgentOptions(name="DataAgent"))
        
        assert agent.name == "DataAgent"
        assert "data_cleaning" in agent.capabilities
        assert "data_transformation" in agent.capabilities
    
    def test_analysis_agent(self):
        """测试分析Agent"""
        agent = AnalysisAgent(AgentOptions(name="AnalysisAgent"))
        
        assert agent.name == "AnalysisAgent"
        assert "data_analysis" in agent.capabilities
        assert "statistical_analysis" in agent.capabilities
    
    def test_reporting_agent(self):
        """测试报告生成Agent"""
        agent = ReportingAgent(AgentOptions(name="ReportAgent"))
        
        assert agent.name == "ReportAgent"
        assert "report_generation" in agent.capabilities
        assert "format_conversion" in agent.capabilities


class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # Setup
        orchestrator = OrchestratorService(name="TestOrchestrator")
        
        # Register agents
        data_agent = DataProcessingAgent(AgentOptions(name="DataAgent"))
        analysis_agent = AnalysisAgent(AgentOptions(name="AnalysisAgent"))
        
        orchestrator.register_agent(data_agent)
        orchestrator.register_agent(analysis_agent)
        
        # Create tasks
        task1 = orchestrator.create_task("CleanData", ["data_cleaning"])
        task2 = orchestrator.create_task("AnalyzeData", ["data_analysis"])
        
        # Get system status
        status = orchestrator.get_system_status()
        
        # Verify
        assert status["agents"]["total"] == 2
        assert task1 is not None
        assert task2 is not None
    
    def test_multi_tenancy_with_agents(self):
        """测试多租户和Agent集成"""
        tenant_service = TenantManagementService()
        tenant = tenant_service.create_tenant("TestTenant", "test.tenant")
        tenant_service.activate_tenant(tenant.tenant_id)
        
        orchestrator = OrchestratorService()
        agent = DataProcessingAgent(AgentOptions(name="TenantAgent"))
        orchestrator.register_agent(agent)
        
        context = TenantContext.get_current()
        assert context.tenant_id == tenant.tenant_id
    
    def test_analytics_with_orchestration(self):
        """测试分析和编排集成"""
        analytics = get_analytics_engine()
        orchestrator = OrchestratorService()
        
        agent = DataProcessingAgent(AgentOptions(name="Agent"))
        orchestrator.register_agent(agent)
        
        analytics.record_metric("orchestrator.agents", 1)
        analytics.record_metric("system.uptime", 100.0)
        
        metrics = analytics.get_all_metrics()
        assert len(metrics) >= 2


class TestSystem:
    """系统测试"""
    
    def test_complete_system_initialization(self):
        """测试完整系统初始化"""
        # Initialize all components
        orchestrator = OrchestratorService(name="SystemTest")
        analytics = AnalyticsEngine()
        storage = InMemoryChatStorage()
        tenant_service = TenantManagementService()
        
        # Register agents
        agent1 = DataProcessingAgent(AgentOptions(name="DataAgent"))
        agent2 = AnalysisAgent(AgentOptions(name="AnalysisAgent"))
        agent3 = ReportingAgent(AgentOptions(name="ReportAgent"))
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)
        
        # Record metrics
        analytics.record_metric("system.agents", 3)
        analytics.record_metric("system.status", 1.0)
        
        # Verify
        status = orchestrator.get_system_status()
        assert status["agents"]["total"] == 3
        
        metrics = analytics.get_all_metrics()
        assert len(metrics) >= 2
    
    def test_error_handling(self):
        """测试错误处理"""
        orchestrator = OrchestratorService()
        
        # Trying to assign non-existent agent should not crash
        result = orchestrator.send_message(
            receiver="NonExistent",
            content={"test": "data"}
        )
        
        assert result is False  # Should gracefully handle


# Run tests if called directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
