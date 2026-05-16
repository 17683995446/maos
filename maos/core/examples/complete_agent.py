"""
MAOS v5.0 - 完整的Agent示例
展示如何使用Agent基类创建功能完整的Agent
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional, AsyncGenerator, Dict, Any
from datetime import datetime

from maos.core.agent import (
    Agent,
    AgentMessage,
    AgentStatus,
    MessageType,
    AgentCallbacks,
    AgentOptions,
    AgentStreamResponse
)


class SimpleAgentCallbacks(AgentCallbacks):
    """简单的回调实现"""
    
    async def on_agent_start(
        self,
        agent_name: str,
        payload_input: str,
        messages: List[Dict],
        metadata: Dict
    ):
        print(f"🤖 {agent_name} 开始处理: {payload_input[:50]}...")
        return {"start_time": datetime.now().isoformat()}
    
    async def on_agent_end(
        self,
        agent_name: str,
        response: Any,
        messages: List[Dict],
        metadata: Dict
    ):
        print(f"✅ {agent_name} 处理完成")
        return {"end_time": datetime.now().isoformat()}
    
    async def on_agent_error(
        self,
        agent_name: str,
        error: Exception
    ):
        print(f"❌ {agent_name} 错误: {error}")
        return {"error_time": datetime.now().isoformat()}
    
    async def on_llm_new_token(self, agent_name: str, token: str):
        """流式token回调"""
        pass
    
    async def on_agent_finish(self, agent_name: str, final_output: str):
        """完成回调"""
        pass


class EchoAgent(Agent):
    """
    Echo Agent - 简单的回显Agent
    演示基本的消息处理流程
    """
    
    def __init__(self, name: str = "echo-agent", capabilities: Optional[List[str]] = None):
        super().__init__(
            agent_id=name,
            capabilities=capabilities or ["echo", "basic"],
            options=AgentOptions(
                name=name,
                description="Simple echo agent"
            )
        )
        self.callbacks = SimpleAgentCallbacks()
        self.processed_count = 0
    
    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        """处理消息的实际实现"""
        self.processed_count += 1
        
        response_content = f"Echo: {message.content}"
        
        response = AgentMessage(
            sender=self.name,
            receivers=[message.sender],
            msg_type=MessageType.RESPONSE,
            content=response_content,
            metadata={
                'processed_count': self.processed_count,
                'original_timestamp': message.timestamp.isoformat()
            },
            reply_to=message.id
        )
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'name': self.name,
            'status': self.status.value,
            'processed_count': self.processed_count,
            'capabilities': self.capabilities
        }


class DataProcessingAgent(Agent):
    """
    Data Processing Agent - 数据处理Agent
    演示更复杂的处理逻辑
    """
    
    def __init__(self, name: str = "data-processor", capabilities: Optional[List[str]] = None):
        super().__init__(
            agent_id=name,
            capabilities=capabilities or ["data_processing", "analysis"],
            options=AgentOptions(
                name=name,
                description="Data processing and analysis agent"
            )
        )
        self.callbacks = SimpleAgentCallbacks()
        self.data_cache: Dict[str, Any] = {}
    
    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        """处理数据处理请求"""
        content = message.content.lower()
        
        # 简单的数据处理逻辑
        if "clean" in content or "清洗" in content:
            result = self._clean_data(message.content)
        elif "analyze" in content or "分析" in content:
            result = self._analyze_data(message.content)
        elif "transform" in content or "转换" in content:
            result = self._transform_data(message.content)
        else:
            result = f"Data processed: {message.content}"
        
        response = AgentMessage(
            sender=self.name,
            receivers=[message.sender],
            msg_type=MessageType.RESPONSE,
            content=result,
            metadata={'processor': self.name},
            reply_to=message.id
        )
        
        return response
    
    def _clean_data(self, data: str) -> str:
        """清洗数据"""
        import re
        cleaned = re.sub(r'\s+', ' ', data)
        cleaned = cleaned.strip()
        return f"✅ Data cleaned: {cleaned}"
    
    def _analyze_data(self, data: str) -> str:
        """分析数据"""
        word_count = len(data.split())
        char_count = len(data)
        return f"📊 Analysis: {word_count} words, {char_count} chars"
    
    def _transform_data(self, data: str) -> str:
        """转换数据"""
        return f"🔄 Transformed: {data.upper()}"


class LLMEnabledAgent(Agent):
    """
    LLM-Enabled Agent - 使用大模型的Agent
    集成硅基流动的LLM能力
    """
    
    def __init__(
        self,
        name: str = "llm-agent",
        capabilities: Optional[List[str]] = None
    ):
        super().__init__(
            agent_id=name,
            capabilities=capabilities or ["llm", "reasoning", "general"],
            options=AgentOptions(
                name=name,
                description="LLM-powered agent with reasoning capabilities"
            )
        )
        self.callbacks = SimpleAgentCallbacks()
        self.llm_client = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            from maos.llm import get_llm_client
            self.llm_client = get_llm_client()
        except Exception as e:
            print(f"⚠️ LLM client initialization failed: {e}")
            self.llm_client = None
    
    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        """使用LLM处理消息"""
        if not self.llm_client or not self.llm_client.is_available():
            response_content = "⚠️ LLM not available. Please check API configuration."
        else:
            try:
                from maos.llm import ChatMessage
                messages = [
                    ChatMessage(role="system", content="你是一个有帮助的AI助手。"),
                    ChatMessage(role="user", content=message.content)
                ]
                response = self.llm_client.chat(messages)
                response_content = response.content
            except Exception as e:
                response_content = f"❌ LLM Error: {str(e)}"
        
        response = AgentMessage(
            sender=self.name,
            receivers=[message.sender],
            msg_type=MessageType.RESPONSE,
            content=response_content,
            metadata={'llm_enabled': self.llm_client is not None},
            reply_to=message.id
        )
        
        return response
    
    async def process_request(
        self,
        input_text: str,
        user_id: str = "default",
        session_id: str = "default",
        chat_history: Optional[List] = None,
        callbacks: Optional[AgentCallbacks] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        处理请求 - 流式输出
        支持直接调用，生成器模式
        """
        if not self.llm_client or not self.llm_client.is_available():
            yield "⚠️ LLM not available"
            return
        
        try:
            from maos.llm import ChatMessage
            messages = [
                ChatMessage(role="system", content="你是一个有帮助的AI助手。"),
                ChatMessage(role="user", content=input_text)
            ]
            
            # 流式输出
            async for token in self.llm_client.achat_stream(messages):
                yield token
        
        except Exception as e:
            yield f"❌ Error: {str(e)}"


# 工厂函数
def create_agent(agent_type: str) -> Agent:
    """创建Agent的工厂函数"""
    agent_map = {
        "echo": EchoAgent,
        "data": DataProcessingAgent,
        "llm": LLMEnabledAgent
    }
    
    agent_class = agent_map.get(agent_type.lower(), EchoAgent)
    return agent_class()


# 示例和测试
async def demo_agents():
    """演示不同的Agent"""
    print("\n" + "=" * 80)
    print("  MAOS v5.0 - Agent Examples")
    print("=" * 80)
    
    # 1. Echo Agent
    print("\n📋 1. Echo Agent Demo")
    print("-" * 80)
    echo_agent = EchoAgent()
    
    message1 = AgentMessage(
        sender="user",
        receivers=["echo-agent"],
        msg_type=MessageType.REQUEST,
        content="Hello, Echo!"
    )
    
    response1 = await echo_agent.process_message_async(message1)
    print(f"Input: {message1.content}")
    print(f"Output: {response1.content}")
    
    # 2. Data Processing Agent
    print("\n📋 2. Data Processing Agent Demo")
    print("-" * 80)
    data_agent = DataProcessingAgent()
    
    for query in ["clean this data", "analyze statistics", "transform to uppercase"]:
        message = AgentMessage(
            sender="user",
            receivers=["data-processor"],
            msg_type=MessageType.REQUEST,
            content=query
        )
        
        response = await data_agent.process_message_async(message)
        print(f"Query: {query}")
        print(f"Result: {response.content}")
    
    # 3. LLM Agent
    print("\n📋 3. LLM Agent Demo")
    print("-" * 80)
    llm_agent = LLMEnabledAgent()
    
    print("Query: 'What is Python?'")
    print("Response: ", end="", flush=True)
    
    async for token in llm_agent.process_request("用一句话解释Python"):
        print(token, end="", flush=True)
    
    print("\n")
    
    # 显示统计
    print("\n📊 Agent Statistics")
    print("-" * 80)
    print(f"Echo Agent: {echo_agent.get_stats()}")
    print(f"Data Agent: {data_agent.get_stats()}")


if __name__ == "__main__":
    asyncio.run(demo_agents())
