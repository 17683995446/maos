"""
MAOS v5.0 - LLM Agent 演示
展示如何直接使用LLM Agent
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Optional, AsyncGenerator, Dict, Any
from datetime import datetime

from maos.llm import LLMClient, ChatMessage, get_llm_client
from maos.types import ConversationMessage


class SimpleLLMAgent:
    """
    简单的LLM Agent - 展示如何直接使用LLM
    不依赖Agent基类，更简单直接
    """
    
    def __init__(
        self,
        agent_id: str,
        system_prompt: str = "你是一个有帮助的AI助手。",
        model: Optional[str] = None,
        temperature: float = 0.7
    ):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.llm_client: Optional[LLMClient] = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            self.llm_client = get_llm_client()
        except Exception as e:
            print(f"⚠️ LLM client init failed: {e}")
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self.llm_client is not None and self.llm_client.is_available()
    
    async def chat(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None
    ) -> str:
        """简单的聊天"""
        if not self.is_available():
            return "⚠️ LLM not available"
        
        messages = []
        messages.append(ChatMessage(role="system", content=self.system_prompt))
        
        if chat_history:
            for msg in chat_history:
                messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        
        messages.append(ChatMessage(role="user", content=user_input))
        
        try:
            response = self.llm_client.chat(messages)
            return response.content
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def stream_chat(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        if not self.is_available():
            yield "⚠️ LLM not available"
            return
        
        messages = []
        messages.append(ChatMessage(role="system", content=self.system_prompt))
        
        if chat_history:
            for msg in chat_history:
                messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        
        messages.append(ChatMessage(role="user", content=user_input))
        
        try:
            async for token in self.llm_client.achat_stream(messages):
                yield token
        except Exception as e:
            yield f"❌ Error: {str(e)}"


# 预定义Agent
class ResearchAgent(SimpleLLMAgent):
    """研究助手"""
    def __init__(self):
        super().__init__(
            agent_id="research-assistant",
            system_prompt="你是一个专业的研究助手。擅长信息检索、分析和总结。",
            temperature=0.6
        )


class CodeAgent(SimpleLLMAgent):
    """编程助手"""
    def __init__(self):
        super().__init__(
            agent_id="code-assistant",
            system_prompt="你是一个专业的编程助手。擅长代码编写和调试。",
            temperature=0.5
        )


class CreativeAgent(SimpleLLMAgent):
    """创意助手"""
    def __init__(self):
        super().__init__(
            agent_id="creative-writer",
            system_prompt="你是一个富有创意的写作助手。",
            temperature=0.9
        )


# 演示
async def demo():
    """演示LLM Agent"""
    print("\n" + "=" * 80)
    print("  MAOS v5.0 - LLM Agent Demo")
    print("=" * 80)
    
    # 创建Agent
    print("\n📋 1. Creating Agents...")
    research = ResearchAgent()
    code = CodeAgent()
    creative = CreativeAgent()
    
    print(f"   ✅ Research Agent: {research.agent_id}")
    print(f"   ✅ Code Agent: {code.agent_id}")
    print(f"   ✅ Creative Agent: {creative.agent_id}")
    
    # 检查LLM状态
    print("\n📋 2. Checking LLM Status...")
    if research.is_available():
        print(f"   ✅ LLM available: {research.llm_client.config.model}")
    else:
        print("   ⚠️ LLM not available")
    
    # 简单聊天
    print("\n📋 3. Simple Chat Demo...")
    response = await research.chat("用一句话介绍Python")
    print(f"   Research Agent: {response[:100]}...")
    
    # 流式聊天
    print("\n📋 4. Streaming Chat Demo...")
    print("   Code Agent: ", end="", flush=True)
    async for token in code.stream_chat("写一个Python的快速排序"):
        print(token, end="", flush=True)
    print()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(demo())
