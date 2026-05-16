"""
核心模块测试 - Agent基类、消息、状态和回调测试
=============================================

测试覆盖：
- Agent基类创建和配置
- Agent状态管理
- 消息发送/接收
- 消息序列化/反序列化
- 事件处理系统
- 消息队列管理
- 异步处理功能
- 流式响应支持
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maos.core import (
    Agent,
    AgentCallbacks,
    AgentEvent,
    AgentMessage,
    AgentOptions,
    AgentProcessingResult,
    AgentResponse,
    AgentStatus,
    AgentStreamResponse,
    MessageType,
)


class ConcreteTestAgent(Agent):
    """具体测试用Agent实现"""

    def __init__(self, options: AgentOptions):
        super().__init__(options)
        self.processed_messages: List[AgentMessage] = []

    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        """实现消息处理逻辑"""
        self.processed_messages.append(message)
        return message.create_response(
            content={"status": "processed", "original": message.content}
        )

    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[Any],
        additional_params: Dict[str, Any] = None,
    ) -> str:
        """实现请求处理"""
        return f"Processed: {input_text}"


@pytest.mark.asyncio
class TestAgentCreation:
    """Agent创建测试"""

    async def test_agent_creation_with_defaults(self):
        """测试使用默认配置创建Agent"""
        options = AgentOptions(name="test_agent")
        agent = ConcreteTestAgent(options)

        assert agent.name == "test_agent"
        assert agent.status == AgentStatus.IDLE
        assert agent.id == "test-agent"
        assert isinstance(agent.message_queue, asyncio.Queue)

    async def test_agent_creation_with_capabilities(self):
        """测试创建具有特定能力的Agent"""
        options = AgentOptions(
            name="capable_agent",
            capabilities=["analysis", "reporting", "processing"]
        )
        agent = ConcreteTestAgent(options)

        assert len(agent.capabilities) == 3
        assert "analysis" in agent.capabilities
        assert "reporting" in agent.capabilities
        assert "processing" in agent.capabilities

    async def test_agent_creation_with_custom_config(self):
        """测试使用自定义配置创建Agent"""
        options = AgentOptions(
            name="custom_agent",
            description="自定义描述",
            capabilities=["test"],
            save_chat=False,
            max_queue_size=500,
            processing_timeout=60.0,
            log_debug_trace=True
        )
        agent = ConcreteTestAgent(options)

        assert agent.description == "自定义描述"
        assert agent.save_chat is False
        assert agent.processing_timeout == 60.0
        assert agent.log_debug_trace is True

    async def test_generate_key_from_name(self):
        """测试从名称生成唯一键"""
        test_cases = [
            ("Simple Agent", "simple-agent"),
            ("Agent With Spaces", "agent-with-spaces"),
            ("Agent-With-Dashes", "agent-with-dashes"),
            ("Agent With Special!@#Chars", "agent-with-specialchars"),
        ]

        for name, expected_key in test_cases:
            generated_key = Agent.generate_key_from_name(name)
            assert generated_key == expected_key


@pytest.mark.asyncio
class TestAgentStatusManagement:
    """Agent状态管理测试"""

    async def test_initial_status(self):
        """测试初始状态为IDLE"""
        options = AgentOptions(name="status_test_agent")
        agent = ConcreteTestAgent(options)

        assert agent.status == AgentStatus.IDLE

    async def test_status_transition_to_busy(self):
        """测试状态转换为BUSY"""
        options = AgentOptions(name="status_test_agent")
        agent = ConcreteTestAgent(options)

        agent.update_status(AgentStatus.BUSY)
        assert agent.status == AgentStatus.BUSY

    async def test_status_transition_to_error(self):
        """测试状态转换为ERROR"""
        options = AgentOptions(name="status_test_agent")
        agent = ConcreteTestAgent(options)

        agent.update_status(AgentStatus.ERROR)
        assert agent.status == AgentStatus.ERROR

    async def test_status_transition_to_terminated(self):
        """测试状态转换为TERMINATED"""
        options = AgentOptions(name="status_test_agent")
        agent = ConcreteTestAgent(options)

        agent.update_status(AgentStatus.TERMINATED)
        assert agent.status == AgentStatus.TERMINATED

    async def test_status_change_event_emission(self):
        """测试状态变更事件发射"""
        options = AgentOptions(name="event_test_agent")
        agent = ConcreteTestAgent(options)

        received_events = []

        def event_handler(event: AgentEvent):
            received_events.append(event)

        agent.on_event("status_changed", event_handler)
        agent.update_status(AgentStatus.BUSY)

        assert len(received_events) == 1
        assert received_events[0].event_type == "status_changed"
        assert received_events[0].data["old_status"] == "idle"
        assert received_events[0].data["new_status"] == "busy"

    async def test_off_event_handler(self):
        """测试取消注册事件处理器"""
        options = AgentOptions(name="event_test_agent")
        agent = ConcreteTestAgent(options)

        def event_handler(event: AgentEvent):
            pass

        agent.on_event("status_changed", event_handler)
        assert len(agent._event_handlers["status_changed"]) == 1

        agent.off_event("status_changed", event_handler)
        assert len(agent._event_handlers["status_changed"]) == 0


@pytest.mark.asyncio
class TestAgentCapabilities:
    """Agent能力管理测试"""

    async def test_has_capability(self):
        """测试能力检查"""
        options = AgentOptions(name="capable_agent", capabilities=["analysis", "processing"])
        agent = ConcreteTestAgent(options)

        assert agent.has_capability("analysis") is True
        assert agent.has_capability("processing") is True
        assert agent.has_capability("reporting") is False

    async def test_add_capability(self):
        """测试添加能力"""
        options = AgentOptions(name="capable_agent", capabilities=["analysis"])
        agent = ConcreteTestAgent(options)

        agent.add_capability("processing")
        assert agent.has_capability("processing") is True
        assert len(agent.capabilities) == 2

    async def test_add_duplicate_capability(self):
        """测试添加重复能力"""
        options = AgentOptions(name="capable_agent", capabilities=["analysis"])
        agent = ConcreteTestAgent(options)

        agent.add_capability("analysis")
        assert len(agent.capabilities) == 1

    async def test_remove_capability(self):
        """测试移除能力"""
        options = AgentOptions(name="capable_agent", capabilities=["analysis", "processing"])
        agent = ConcreteTestAgent(options)

        agent.remove_capability("analysis")
        assert agent.has_capability("analysis") is False
        assert len(agent.capabilities) == 1

    async def test_can_handle_task(self):
        """测试任务处理能力判断"""
        options = AgentOptions(name="capable_agent", capabilities=["analysis", "processing", "reporting"])
        agent = ConcreteTestAgent(options)

        assert agent.can_handle_task(["analysis"]) is True
        assert agent.can_handle_task(["analysis", "processing"]) is True
        assert agent.can_handle_task(["analysis", "processing", "reporting"]) is True
        assert agent.can_handle_task(["analysis", "unknown"]) is False


@pytest.mark.asyncio
class TestAgentMessage:
    """Agent消息测试"""

    def test_message_creation(self):
        """测试消息创建"""
        message = AgentMessage(
            sender="sender1",
            receivers=["receiver1", "receiver2"],
            msg_type=MessageType.REQUEST,
            content={"action": "test"}
        )

        assert message.sender == "sender1"
        assert len(message.receivers) == 2
        assert message.msg_type == MessageType.REQUEST
        assert message.content["action"] == "test"
        assert message.id is not None
        assert message.correlation_id is not None

    def test_message_to_dict(self):
        """测试消息序列化"""
        message = AgentMessage(
            sender="sender1",
            receivers=["receiver1"],
            msg_type=MessageType.RESPONSE,
            content="test content"
        )

        message_dict = message.to_dict()

        assert message_dict["sender"] == "sender1"
        assert message_dict["receivers"] == ["receiver1"]
        assert message_dict["msg_type"] == "response"
        assert message_dict["content"] == "test content"
        assert "id" in message_dict
        assert "timestamp" in message_dict

    def test_message_from_dict(self):
        """测试消息反序列化"""
        original = AgentMessage(
            sender="sender1",
            receivers=["receiver1"],
            msg_type=MessageType.REQUEST,
            content="test"
        )
        original_dict = original.to_dict()

        restored = AgentMessage.from_dict(original_dict)

        assert restored.sender == original.sender
        assert restored.receivers == original.receivers
        assert restored.msg_type == original.msg_type
        assert restored.content == original.content

    def test_create_response(self):
        """测试创建响应消息"""
        original = AgentMessage(
            sender="sender1",
            receivers=["receiver1"],
            msg_type=MessageType.REQUEST,
            content="request"
        )

        response = original.create_response(
            content="response content",
            metadata={"status": "success"}
        )

        assert response.sender == "sender1"
        assert response.msg_type == MessageType.RESPONSE
        assert response.content == "response content"
        assert response.reply_to == original.id
        assert response.correlation_id == original.correlation_id

    def test_message_types(self):
        """测试消息类型枚举"""
        assert MessageType.REQUEST.value == "request"
        assert MessageType.RESPONSE.value == "response"
        assert MessageType.BROADCAST.value == "broadcast"
        assert MessageType.HEARTBEAT.value == "heartbeat"
        assert MessageType.ERROR.value == "error"
        assert MessageType.STREAM.value == "stream"


@pytest.mark.asyncio
class TestAgentMessageQueue:
    """Agent消息队列测试"""

    async def test_send_message(self):
        """测试发送消息"""
        options = AgentOptions(name="queue_test_agent")
        agent = ConcreteTestAgent(options)

        message = AgentMessage(
            sender="test",
            receivers=[agent.name],
            content="test message"
        )

        await agent.send_message(message)
        assert agent.get_queue_size() == 1

    async def test_receive_message(self):
        """测试接收消息"""
        options = AgentOptions(name="queue_test_agent")
        agent = ConcreteTestAgent(options)

        message = AgentMessage(
            sender="external",
            receivers=[agent.name],
            content="received message"
        )

        agent.receive_message(message)
        assert agent.get_queue_size() == 1

    async def test_clear_queue(self):
        """测试清空队列"""
        options = AgentOptions(name="queue_test_agent")
        agent = ConcreteTestAgent(options)

        for i in range(5):
            message = AgentMessage(
                sender=f"sender{i}",
                receivers=[agent.name],
                content=f"message {i}"
            )
            agent.receive_message(message)

        assert agent.get_queue_size() == 5

        agent.clear_queue()
        assert agent.get_queue_size() == 0


@pytest.mark.asyncio
class TestAgentAsyncProcessing:
    """Agent异步处理测试"""

    async def test_process_message_async(self):
        """测试异步消息处理"""
        options = AgentOptions(name="processing_agent")
        agent = ConcreteTestAgent(options)

        message = AgentMessage(
            sender="test_sender",
            receivers=[agent.name],
            msg_type=MessageType.REQUEST,
            content={"action": "process"}
        )

        response = await agent.process_message_async(message)

        assert response.msg_type == MessageType.RESPONSE
        assert response.content["status"] == "processed"

    async def test_process_message_batch_sequential(self):
        """测试批量处理消息（顺序）"""
        options = AgentOptions(name="batch_agent")
        agent = ConcreteTestAgent(options)

        messages = [
            AgentMessage(
                sender=f"sender{i}",
                receivers=[agent.name],
                content={"index": i}
            )
            for i in range(3)
        ]

        results = await agent.process_message_batch(messages, parallel=False)

        assert len(results) == 3
        assert all(r.msg_type == MessageType.RESPONSE for r in results)

    async def test_process_message_batch_parallel(self):
        """测试批量处理消息（并行）"""
        options = AgentOptions(name="batch_agent")
        agent = ConcreteTestAgent(options)

        messages = [
            AgentMessage(
                sender=f"sender{i}",
                receivers=[agent.name],
                content={"index": i}
            )
            for i in range(3)
        ]

        results = await agent.process_message_batch(messages, parallel=True)

        assert len(results) == 3
        assert all(r.msg_type == MessageType.RESPONSE for r in results)

    async def test_process_message_with_callbacks(self, mock_agent_callbacks):
        """测试带回调的消息处理"""
        options = AgentOptions(name="callback_agent", callbacks=mock_agent_callbacks)
        agent = ConcreteTestAgent(options)

        message = AgentMessage(
            sender="test",
            receivers=[agent.name],
            content="test"
        )

        await agent.process_message_async(message)

        mock_agent_callbacks.on_agent_start.assert_called_once()
        mock_agent_callbacks.on_agent_end.assert_called_once()

    async def test_process_message_with_timeout(self):
        """测试带超时的消息处理"""
        options = AgentOptions(name="timeout_agent", processing_timeout=0.1)

        class SlowAgent(Agent):
            async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
                await asyncio.sleep(1)
                return message.create_response(content="done")

            async def process_request(
                self,
                input_text: str,
                user_id: str,
                session_id: str,
                chat_history: List[Any],
                additional_params: Dict[str, Any] = None,
            ) -> str:
                return "done"

        agent = SlowAgent(options)

        message = AgentMessage(
            sender="test",
            receivers=[agent.name],
            content="test"
        )

        response = await agent.process_message_async(message)

        assert response.content == "处理超时 (timeout=0.1s)"
        assert response.metadata.get("error") == "timeout"

    async def test_process_message_with_error(self):
        """测试消息处理错误"""
        options = AgentOptions(name="error_agent")

        class ErrorAgent(Agent):
            async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
                raise ValueError("Test error")

            async def process_request(
                self,
                input_text: str,
                user_id: str,
                session_id: str,
                chat_history: List[Any],
                additional_params: Dict[str, Any] = None,
            ) -> str:
                return "error"

        agent = ErrorAgent(options)

        message = AgentMessage(
            sender="test",
            receivers=[agent.name],
            content="test"
        )

        response = await agent.process_message_async(message)

        assert "处理错误" in response.content
        assert response.metadata.get("error") is not None


@pytest.mark.asyncio
class TestAgentStreaming:
    """Agent流式响应测试"""

    async def test_stream_response(self):
        """测试流式响应"""
        options = AgentOptions(name="streaming_agent")
        agent = ConcreteTestAgent(options)

        message = AgentMessage(
            sender="test",
            receivers=[agent.name],
            content="stream test"
        )

        chunks = []
        async for chunk in agent.stream_response(message):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert chunks[-1].final_message is not None

    async def test_is_streaming_enabled(self):
        """测试流式启用检查"""
        options = AgentOptions(name="test_agent")
        agent = ConcreteTestAgent(options)

        assert agent.is_streaming_enabled() is False


@pytest.mark.asyncio
class TestAgentHealthCheck:
    """Agent健康检查测试"""

    async def test_health_check_idle(self):
        """测试IDLE状态健康检查"""
        options = AgentOptions(name="health_check_agent")
        agent = ConcreteTestAgent(options)

        health = await agent.health_check()

        assert health["agent_name"] == "health_check_agent"
        assert health["status"] == "idle"
        assert health["healthy"] is True
        assert health["queue_size"] == 0

    async def test_health_check_busy(self):
        """测试BUSY状态健康检查"""
        options = AgentOptions(name="health_check_agent")
        agent = ConcreteTestAgent(options)
        agent.update_status(AgentStatus.BUSY)

        health = await agent.health_check()

        assert health["status"] == "busy"
        assert health["healthy"] is True

    async def test_health_check_error(self):
        """测试ERROR状态健康检查"""
        options = AgentOptions(name="health_check_agent")
        agent = ConcreteTestAgent(options)
        agent.update_status(AgentStatus.ERROR)

        health = await agent.health_check()

        assert health["status"] == "error"
        assert health["healthy"] is False


@pytest.mark.asyncio
class TestAgentLogging:
    """Agent日志测试"""

    async def test_log_debug(self):
        """测试调试日志输出"""
        options = AgentOptions(name="log_agent", log_debug_trace=True)
        agent = ConcreteTestAgent(options)

        agent.log_debug("Test debug message", {"key": "value"})

    async def test_log_debug_no_trace(self):
        """测试禁用调试跟踪时的日志"""
        options = AgentOptions(name="log_agent", log_debug_trace=False)
        agent = ConcreteTestAgent(options)

        agent.log_debug("Test debug message")

    async def test_log_error(self):
        """测试错误日志输出"""
        options = AgentOptions(name="log_agent")
        agent = ConcreteTestAgent(options)

        agent.log_error("Test error message", {"error": "test"})


@pytest.mark.asyncio
class TestAgentInfo:
    """Agent信息测试"""

    async def test_get_info(self):
        """测试获取Agent信息"""
        options = AgentOptions(
            name="info_agent",
            description="Test description",
            capabilities=["test1", "test2"]
        )
        agent = ConcreteTestAgent(options)

        info = agent.get_info()

        assert info["name"] == "info_agent"
        assert info["description"] == "Test description"
        assert info["capabilities"] == ["test1", "test2"]
        assert info["status"] == "idle"
        assert info["queue_size"] == 0
        assert info["streaming_enabled"] is False


@pytest.mark.asyncio
class TestAgentShutdown:
    """Agent关闭测试"""

    async def test_shutdown(self):
        """测试Agent优雅关闭"""
        options = AgentOptions(name="shutdown_agent")
        agent = ConcreteTestAgent(options)

        message = AgentMessage(
            sender="test",
            receivers=[agent.name],
            content="test"
        )
        agent.receive_message(message)

        await agent.shutdown()

        assert agent.status == AgentStatus.TERMINATED
        assert agent.get_queue_size() == 0


@pytest.mark.asyncio
class TestAgentCallbacks:
    """Agent回调测试"""

    async def test_callbacks_on_agent_start(self, mock_agent_callbacks):
        """测试on_agent_start回调"""
        result = await mock_agent_callbacks.on_agent_start(
            agent_name="test_agent",
            payload_input="test input",
            messages=[],
            metadata={}
        )

        assert result is not None

    async def test_callbacks_on_agent_end(self, mock_agent_callbacks):
        """测试on_agent_end回调"""
        await mock_agent_callbacks.on_agent_end(
            agent_name="test_agent",
            response="test response",
            messages=[],
            metadata={}
        )

        mock_agent_callbacks.on_agent_end.assert_called_once()

    async def test_callbacks_on_error(self, mock_agent_callbacks):
        """测试on_error回调"""
        error = ValueError("Test error")
        context = {"test": "context"}

        await mock_agent_callbacks.on_error("test_agent", error, context)

        mock_agent_callbacks.on_error.assert_called_once()


@pytest.mark.asyncio
class TestAgentProcessingResult:
    """Agent处理结果测试"""

    def test_processing_result_creation(self):
        """测试处理结果创建"""
        result = AgentProcessingResult(
            user_input="test input",
            agent_id="agent-123",
            agent_name="test_agent",
            user_id="user-456",
            session_id="session-789"
        )

        assert result.user_input == "test input"
        assert result.agent_id == "agent-123"
        assert result.agent_name == "test_agent"
        assert result.user_id == "user-456"
        assert result.session_id == "session-789"
        assert result.error is None


@pytest.mark.asyncio
class TestAgentStreamResponse:
    """Agent流式响应测试"""

    def test_stream_response_creation(self):
        """测试流式响应创建"""
        response = AgentStreamResponse(
            text="chunk text",
            thinking="thinking process",
            final_message="final result"
        )

        assert response.text == "chunk text"
        assert response.thinking == "thinking process"
        assert response.final_message == "final result"


@pytest.mark.asyncio
class TestAgentEvent:
    """Agent事件测试"""

    def test_event_creation(self):
        """测试事件创建"""
        event = AgentEvent(
            event_type="test_event",
            agent_name="test_agent",
            data={"key": "value"}
        )

        assert event.event_type == "test_event"
        assert event.agent_name == "test_agent"
        assert event.data["key"] == "value"
        assert isinstance(event.timestamp, datetime)


@pytest.mark.parametrize(
    "name,expected_capabilities_count",
    [
        ("agent1", 0),
        ("agent2", 1),
        ("agent3", 3),
    ],
)
@pytest.mark.asyncio
class TestAgentParametrized:
    """参数化Agent测试"""

    async def test_create_agent_with_capabilities(
        self, name: str, expected_capabilities_count: int
    ):
        """测试创建具有不同能力数量的Agent"""
        capabilities = ["cap1", "cap2", "cap3"][:expected_capabilities_count]
        options = AgentOptions(name=name, capabilities=capabilities)
        agent = ConcreteTestAgent(options)

        assert agent.name == name
        assert len(agent.capabilities) == expected_capabilities_count


@pytest.mark.parametrize(
    "message_type,expected_value",
    [
        (MessageType.REQUEST, "request"),
        (MessageType.RESPONSE, "response"),
        (MessageType.BROADCAST, "broadcast"),
        (MessageType.HEARTBEAT, "heartbeat"),
        (MessageType.ERROR, "error"),
        (MessageType.STREAM, "stream"),
    ],
)
def test_message_type_values(message_type: MessageType, expected_value: str):
    """参数化测试消息类型值"""
    assert message_type.value == expected_value


@pytest.mark.parametrize(
    "status,expected_value",
    [
        (AgentStatus.IDLE, "idle"),
        (AgentStatus.BUSY, "busy"),
        (AgentStatus.ERROR, "error"),
        (AgentStatus.TERMINATED, "terminated"),
    ],
)
def test_agent_status_values(status: AgentStatus, expected_value: str):
    """参数化测试Agent状态值"""
    assert status.value == expected_value


@pytest.mark.asyncio
class TestAgentConcurrency:
    """Agent并发测试"""

    async def test_concurrent_message_sending(self):
        """测试并发发送消息"""
        options = AgentOptions(name="concurrent_agent")
        agent = ConcreteTestAgent(options)

        async def send_message(index: int):
            message = AgentMessage(
                sender=f"sender{index}",
                receivers=[agent.name],
                content=f"message {index}"
            )
            await agent.send_message(message)

        await asyncio.gather(*[send_message(i) for i in range(10)])

        assert agent.get_queue_size() == 10

    async def test_concurrent_message_processing(self):
        """测试并发处理消息"""
        options = AgentOptions(name="concurrent_processor")
        agent = ConcreteTestAgent(options)

        messages = [
            AgentMessage(
                sender=f"sender{i}",
                receivers=[agent.name],
                content={"index": i}
            )
            for i in range(5)
        ]

        results = await agent.process_message_batch(messages, parallel=True)

        assert len(results) == 5
        assert agent.get_queue_size() == 0
