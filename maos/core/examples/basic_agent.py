"""
MAOS Agent基础示例
演示如何使用MAOS核心Agent基类创建自定义Agent
"""

import asyncio
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


class LoggingCallbacks(AgentCallbacks):
    """带日志记录的回调实现"""

    async def on_agent_start(self, **kwargs) -> dict:
        print(f"[回调] Agent开始: {kwargs.get('agent_name')}")
        print(f"[回调] 输入: {kwargs.get('payload_input')}")
        return {"start_time": "recorded"}

    async def on_agent_end(self, **kwargs) -> None:
        print(f"[回调] Agent结束: {kwargs.get('agent_name')}")

    async def on_error(self, agent_name: str, error: Exception, context: Optional[dict] = None, **kwargs) -> None:
        print(f"[回调] Agent错误: {agent_name}, 错误: {error}")


class SimpleAgent(Agent):
    """简单的文本处理Agent"""

    def __init__(self, options: AgentOptions):
        super().__init__(options)
        self.processed_count = 0

    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[Any],
        additional_params: Optional[dict[str, Any]] = None,
    ) -> str:
        self.processed_count += 1
        return f"[{self.name}] 处理了: {input_text} (计数: {self.processed_count})"

    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        content = message.content
        if isinstance(content, dict):
            content = content.get('text', str(content))

        response_content = f"[{self.name}] 已收到消息: {content}"
        return message.create_response(
            content=response_content,
            metadata={'processed': True, 'count': self.processed_count}
        )


class StreamingEchoAgent(Agent):
    """流式响应Echo Agent"""

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
    ) -> AsyncIterable[AgentStreamResponse]:
        words = input_text.split()
        for word in words:
            yield AgentStreamResponse(text=word + " ")
            await asyncio.sleep(0.05)

        yield AgentStreamResponse(
            final_message=f"流式完成: {input_text}",
            text=""
        )

    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        return message.create_response(content=f"流式响应: {message.content}")


async def demo_basic_agent():
    """基本Agent演示"""
    print("\n" + "="*60)
    print("演示1: 基本Agent使用")
    print("="*60)

    agent = SimpleAgent(
        AgentOptions(
            name="EchoAgent",
            description="简单的回显Agent",
            capabilities=["echo", "text_processing"],
            callbacks=LoggingCallbacks(),
            log_debug_trace=True,
        )
    )

    print(f"\n1. Agent信息: {agent.get_info()}")
    print(f"2. Agent状态: {agent.status.value}")

    response = await agent.process_request(
        input_text="Hello World",
        user_id="user1",
        session_id="session1",
        chat_history=[]
    )
    print(f"3. 处理请求: {response}")

    message = AgentMessage(
        sender="client",
        receivers=["echoagent"],
        content={"text": "测试消息"}
    )
    print(f"4. 发送消息...")
    response_msg = await agent.process_message(message)
    print(f"5. 消息响应: {response_msg.content}")

    print(f"6. Agent状态: {agent.status.value}")


async def demo_streaming_agent():
    """流式Agent演示"""
    print("\n" + "="*60)
    print("演示2: 流式响应Agent")
    print("="*60)

    agent = StreamingEchoAgent(
        AgentOptions(
            name="StreamEcho",
            description="流式回显Agent",
            capabilities=["streaming"],
        )
    )

    print(f"流式启用: {agent.is_streaming_enabled()}")

    response = await agent.process_request(
        input_text="这 是 一 个 流 式 响 应",
        user_id="user1",
        session_id="session1",
        chat_history=[]
    )

    print("流式输出: ", end="", flush=True)
    async for chunk in response:
        if chunk.text:
            print(chunk.text, end="", flush=True)
        if chunk.final_message:
            print(f"\n最终消息: {chunk.final_message}")


async def demo_event_system():
    """事件系统演示"""
    print("\n" + "="*60)
    print("演示3: 事件系统")
    print("="*60)

    agent = SimpleAgent(
        AgentOptions(
            name="EventDemo",
            description="事件系统演示Agent",
        )
    )

    received_events = []

    def event_handler(event):
        received_events.append(event)
        print(f"[事件] 类型: {event.event_type}, 数据: {event.data}")

    agent.on_event('message_received', event_handler)
    agent.on_event('status_changed', event_handler)

    print("发送消息触发事件...")
    message = AgentMessage(content="测试事件")
    await agent.send_message(message)

    print(f"\n接收到 {len(received_events)} 个事件")


async def demo_health_check():
    """健康检查演示"""
    print("\n" + "="*60)
    print("演示4: 健康检查")
    print("="*60)

    agent = SimpleAgent(
        AgentOptions(name="HealthCheck")
    )

    health = await agent.health_check()
    print(f"健康状态: {health}")

    message = AgentMessage(content="test")
    agent.receive_message(message)

    health = await agent.health_check()
    print(f"收到消息后: {health}")


async def demo_message_serialization():
    """消息序列化演示"""
    print("\n" + "="*60)
    print("演示5: 消息序列化")
    print("="*60)

    original = AgentMessage(
        sender="sender",
        receivers=["receiver1", "receiver2"],
        msg_type=MessageType.REQUEST,
        content={"key": "value", "data": [1, 2, 3]},
        metadata={"priority": "high"}
    )

    print(f"原始消息: {original.to_dict()}")

    serialized = original.to_dict()
    restored = AgentMessage.from_dict(serialized)

    print(f"恢复消息: sender={restored.sender}, receivers={restored.receivers}")
    print(f"消息类型: {restored.msg_type.value}")

    response = original.create_response(
        content="这是响应内容",
        metadata={'status': 'success'}
    )
    print(f"响应消息: {response.to_dict()}")


async def main():
    """运行所有演示"""
    print("MAOS Agent基础示例")
    print("="*60)

    await demo_basic_agent()
    await demo_streaming_agent()
    await demo_event_system()
    await demo_health_check()
    await demo_message_serialization()

    print("\n" + "="*60)
    print("所有演示完成!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
