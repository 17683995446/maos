"""
MAOS Core Agent Module Tests
MAOS核心Agent模块测试

测试Agent基类的基本功能，包括：
- Agent实例创建
- 消息处理
- 状态管理
- 能力注册
- 事件系统
- 流式响应
"""

import asyncio
import pytest
from typing import Any, List, Optional, AsyncIterable, Union

from maos.core import (
    Agent,
    AgentOptions,
    AgentStatus,
    AgentMessage,
    MessageType,
    AgentCallbacks,
    AgentStreamResponse,
)


class MockAgentCallbacks(AgentCallbacks):
    """测试用回调类"""
    
    def __init__(self):
        super().__init__()
        self.agent_started = False
        self.agent_ended = False
        self.errors = []
    
    async def on_agent_start(self, **kwargs) -> dict:
        self.agent_started = True
        return {"test_run": True}
    
    async def on_agent_end(self, **kwargs) -> None:
        self.agent_ended = True
    
    async def on_error(self, agent_name: str, error: Exception, context: Optional[dict] = None, **kwargs) -> None:
        self.errors.append((agent_name, error, context))


class SimpleAgent(Agent):
    """用于测试的简单Agent实现"""
    
    def __init__(self, options: AgentOptions, test_callbacks: Optional[MockAgentCallbacks] = None):
        super().__init__(options)
        self.test_callbacks = test_callbacks
        self.processed_messages = []
    
    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[Any],
        additional_params: Optional[dict[str, Any]] = None,
    ) -> Union[str, AsyncIterable[AgentStreamResponse]]:
        return f"Processed: {input_text}"
    
    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        self.processed_messages.append(message)
        return message.create_response(
            content=f"Response to: {message.content}",
            metadata={'processed': True}
        )


class StreamingAgent(Agent):
    """支持流式响应的测试Agent"""
    
    def __init__(self, options: AgentOptions):
        super().__init__(options)
    
    def is_streaming_enabled(self) -> bool:
        return True
    
    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[Any],
        additional_params: Optional[dict[str, Any]] = None,
    ) -> Union[str, AsyncIterable[AgentStreamResponse]]:
        return self._stream_response(input_text)
    
    async def _stream_response(self, text: str) -> AsyncIterable[AgentStreamResponse]:
        words = text.split()
        for i, word in enumerate(words):
            yield AgentStreamResponse(text=word + " ")
            await asyncio.sleep(0.01)
        yield AgentStreamResponse(final_message=f"Complete: {text}", text="")
    
    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        return message.create_response(content=f"Streamed: {message.content}")


@pytest.fixture
def callbacks():
    return MockAgentCallbacks()


@pytest.fixture
def agent(callbacks):
    return SimpleAgent(
        AgentOptions(
            name="TestAgent",
            description="A test agent",
            capabilities=["test", "processing"],
            callbacks=callbacks,
            log_debug_trace=True,
        ),
        test_callbacks=callbacks
    )


@pytest.fixture
def streaming():
    return StreamingAgent(
        AgentOptions(
            name="StreamingAgent",
            description="A streaming test agent",
            capabilities=["streaming"],
        )
    )


def test_agent_creation(agent):
    """测试Agent创建"""
    assert agent.name == "TestAgent"
    assert agent.id == "testagent"
    assert agent.description == "A test agent"
    assert agent.status == AgentStatus.IDLE
    assert "test" in agent.capabilities
    assert "processing" in agent.capabilities


def test_agent_key_generation():
    """测试Agent键生成"""
    assert Agent.generate_key_from_name("My Agent") == "my-agent"
    assert Agent.generate_key_from_name("Test_Agent 123") == "testagent-123"
    assert Agent.generate_key_from_name("Agent@#$%") == "agent"


def test_capability_management(agent):
    """测试能力管理"""
    assert agent.has_capability("test")
    assert not agent.has_capability("nonexistent")
    
    agent.add_capability("new_capability")
    assert agent.has_capability("new_capability")
    
    agent.remove_capability("new_capability")
    assert not agent.has_capability("new_capability")


def test_can_handle_task(agent):
    """测试任务处理能力检查"""
    assert agent.can_handle_task(["test"])
    assert agent.can_handle_task(["test", "processing"])
    assert not agent.can_handle_task(["test", "nonexistent"])


def test_status_update(agent):
    """测试状态更新"""
    assert agent.status == AgentStatus.IDLE
    
    agent.update_status(AgentStatus.BUSY)
    assert agent.status == AgentStatus.BUSY
    
    agent.update_status(AgentStatus.ERROR)
    assert agent.status == AgentStatus.ERROR
    
    agent.update_status(AgentStatus.IDLE)
    assert agent.status == AgentStatus.IDLE


def test_message_queue(agent):
    """测试消息队列"""
    assert agent.get_queue_size() == 0
    
    message = AgentMessage(content="test message")
    agent.receive_message(message)
    assert agent.get_queue_size() == 1
    
    agent.clear_queue()
    assert agent.get_queue_size() == 0


def test_get_info(agent):
    """测试获取Agent信息"""
    info = agent.get_info()
    
    assert info['name'] == "TestAgent"
    assert info['id'] == "testagent"
    assert info['status'] == "idle"
    assert info['queue_size'] == 0
    assert 'test' in info['capabilities']
    assert info['streaming_enabled'] == False


@pytest.mark.asyncio
async def test_send_message(agent):
    """测试发送消息"""
    message = AgentMessage(content="Hello")
    await agent.send_message(message)
    
    assert agent.get_queue_size() == 1
    assert message.sender == "TestAgent"


@pytest.mark.asyncio
async def test_process_message(agent, callbacks):
    """测试处理消息"""
    message = AgentMessage(content="Test", receivers=["TestAgent"])
    response = await agent.process_message(message)
    
    assert response.content == "Response to: Test"
    assert response.metadata['processed'] == True
    assert response.msg_type == MessageType.RESPONSE
    assert len(agent.processed_messages) == 1


@pytest.mark.asyncio
async def test_process_message_batch(agent):
    """测试批量处理消息"""
    messages = [
        AgentMessage(content=f"Message {i}")
        for i in range(3)
    ]
    
    results = await agent.process_message_batch(messages, parallel=False)
    assert len(results) == 3
    assert all(r.msg_type == MessageType.RESPONSE for r in results)


@pytest.mark.asyncio
async def test_process_message_batch_parallel(agent):
    """测试并行批量处理"""
    messages = [
        AgentMessage(content=f"Message {i}")
        for i in range(5)
    ]
    
    results = await agent.process_message_batch(messages, parallel=True)
    assert len(results) == 5
    assert all(r.msg_type == MessageType.RESPONSE for r in results)


@pytest.mark.asyncio
async def test_callbacks(agent, callbacks):
    """测试回调"""
    message = AgentMessage(content="Callback test")
    await agent.process_message(message)
    
    assert callbacks.agent_started
    assert callbacks.agent_ended


@pytest.mark.asyncio
async def test_streaming_agent(streaming):
    """测试流式响应"""
    assert streaming.is_streaming_enabled()
    
    response = await streaming.process_request(
        "hello world",
        "user1",
        "session1",
        []
    )
    
    assert asyncio.iscoroutine(response) or hasattr(response, '__aiter__')
    
    collected_text = ""
    async for chunk in response:
        if chunk.text:
            collected_text += chunk.text
    
    assert "hello" in collected_text
    assert "world" in collected_text


@pytest.mark.asyncio
async def test_health_check(agent):
    """测试健康检查"""
    health = await agent.health_check()
    
    assert health['agent_name'] == "TestAgent"
    assert health['agent_id'] == "testagent"
    assert health['status'] == "idle"
    assert health['healthy'] == True


@pytest.mark.asyncio
async def test_shutdown(agent):
    """测试关闭"""
    await agent.shutdown()
    assert agent.status == AgentStatus.TERMINATED
    assert agent.get_queue_size() == 0


@pytest.mark.asyncio
async def test_event_handling(agent):
    """测试事件处理"""
    events_received = []
    
    def event_handler(event):
        events_received.append(event)
    
    agent.on_event('message_received', event_handler)
    
    message = AgentMessage(content="Event test")
    await agent.send_message(message)
    
    assert len(events_received) > 0
    assert events_received[0].event_type == 'message_received'


def test_agent_message_serialization():
    """测试消息序列化"""
    message = AgentMessage(
        sender="sender",
        receivers=["receiver1", "receiver2"],
        msg_type=MessageType.REQUEST,
        content={"data": "test"},
        metadata={"key": "value"}
    )
    
    serialized = message.to_dict()
    assert serialized['sender'] == "sender"
    assert len(serialized['receivers']) == 2
    assert serialized['msg_type'] == "request"
    
    deserialized = AgentMessage.from_dict(serialized)
    assert deserialized.sender == "sender"
    assert len(deserialized.receivers) == 2
    assert deserialized.msg_type == MessageType.REQUEST


def test_agent_message_create_response():
    """测试创建响应消息"""
    original = AgentMessage(
        sender="client",
        content="Hello",
        correlation_id="corr123"
    )
    
    response = original.create_response(
        content="Hi there!",
        metadata={'status': 'ok'}
    )
    
    assert response.sender == "client"
    assert response.content == "Hi there!"
    assert response.reply_to == original.id
    assert response.correlation_id == "corr123"
    assert response.msg_type == MessageType.RESPONSE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
