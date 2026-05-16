"""
MAOS v5.0 - LLM-Powered Agents
真实的大模型驱动的智能Agent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional, AsyncGenerator, Any
from dataclasses import dataclass, field

from maos.core import Agent, AgentOptions, AgentCallbacks
from maos.types import ConversationMessage
from maos.llm import (
    LLMClient,
    get_llm_client,
    ChatMessage,
    LLMResponse,
    available_models
)
from maos.performance import async_timed, timed


@dataclass
class LLMAgentOptions(AgentOptions):
    """LLM Agent选项"""
    system_prompt: str = "你是一个有帮助的AI助手。"
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMAgent(Agent):
    """
    大语言模型驱动的Agent
    使用硅基流动等OpenAI兼容API
    """
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str] = None,
        options: Optional[LLMAgentOptions] = None,
        llm_client: Optional[LLMClient] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities or ["llm", "chat", "reasoning"],
            options=options or LLMAgentOptions()
        )
        self.options: LLMAgentOptions = options or LLMAgentOptions()
        self.llm_client = llm_client or get_llm_client()
    
    def _build_messages(
        self,
        input_text: str,
        chat_history: List[ConversationMessage] = None
    ) -> List[ChatMessage]:
        """构建LLM消息列表"""
        messages = []
        
        # 系统提示词
        if self.options.system_prompt:
            messages.append(ChatMessage(role="system", content=self.options.system_prompt))
        
        # 历史消息
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.role == "user" else "assistant"
                messages.append(ChatMessage(role=role, content=msg.content))
        
        # 当前输入
        messages.append(ChatMessage(role="user", content=input_text))
        
        return messages
    
    @async_timed(log_duration=True, record_metrics=True)
    async def process_request(
        self,
        input_text: str,
        user_id: str = "default",
        session_id: str = "default",
        chat_history: List[ConversationMessage] = None,
        callbacks: Optional[AgentCallbacks] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """处理请求 - 支持流式输出"""
        # 回调：开始
        if callbacks and hasattr(callbacks, 'on_agent_start'):
            await callbacks.on_agent_start(self.agent_id, input_text)
        
        # 检查LLM是否可用
        if not self.llm_client.is_available():
            error_msg = f"LLM not available. Agent {self.agent_id} requires valid API key."
            if callbacks and hasattr(callbacks, 'on_agent_error'):
                await callbacks.on_agent_error(self.agent_id, Exception(error_msg))
            yield f"⚠️ {error_msg}"
            return
        
        # 构建消息
        messages = self._build_messages(input_text, chat_history)
        
        # 流式输出
        full_response = ""
        try:
            async for token in self.llm_client.achat_stream(
                messages=messages,
                temperature=self.options.temperature,
                max_tokens=self.options.max_tokens,
                model=self.options.model
            ):
                # 回调：新token
                if callbacks and hasattr(callbacks, 'on_llm_new_token'):
                    await callbacks.on_llm_new_token(self.agent_id, token)
                
                full_response += token
                yield token
            
            # 回调：完成
            if callbacks and hasattr(callbacks, 'on_agent_finish'):
                await callbacks.on_agent_finish(self.agent_id, full_response)
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if callbacks and hasattr(callbacks, 'on_agent_error'):
                await callbacks.on_agent_error(self.agent_id, e)
            yield f"❌ {error_msg}"


# 预定义的专业Agent
class ResearchAgent(LLMAgent):
    """研究助手Agent"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            agent_id="research-assistant",
            capabilities=["research", "analysis", "writing"],
            options=LLMAgentOptions(
                system_prompt="你是一个专业的研究助手。擅长信息检索、分析和总结。请提供准确、详细的回答。",
                temperature=0.6
            ),
            llm_client=llm_client
        )


class CodeAgent(LLMAgent):
    """编程助手Agent"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            agent_id="code-assistant",
            capabilities=["coding", "debugging", "review"],
            options=LLMAgentOptions(
                system_prompt="你是一个专业的编程助手。擅长代码编写、调试和最佳实践建议。提供可运行的代码和清晰的解释。",
                temperature=0.5
            ),
            llm_client=llm_client
        )


class CreativeAgent(LLMAgent):
    """创意写作Agent"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            agent_id="creative-writer",
            capabilities=["creative_writing", "storytelling", "brainstorming"],
            options=LLMAgentOptions(
                system_prompt="你是一个富有创意的写作助手。擅长故事创作、头脑风暴和创意内容生成。保持想象力和独特性。",
                temperature=0.9
            ),
            llm_client=llm_client
        )


class DataAnalysisAgent(LLMAgent):
    """数据分析Agent"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            agent_id="data-analyst",
            capabilities=["data_analysis", "statistics", "visualization"],
            options=LLMAgentOptions(
                system_prompt="你是一个专业的数据分析师。擅长数据分析、统计解释和可视化建议。提供实用的洞察。",
                temperature=0.4
            ),
            llm_client=llm_client
        )


def create_agent(agent_type: str, llm_client: Optional[LLMClient] = None) -> LLMAgent:
    """创建预定义Agent的工厂函数"""
    agent_map = {
        "research": ResearchAgent,
        "code": CodeAgent,
        "creative": CreativeAgent,
        "data": DataAnalysisAgent
    }
    
    agent_class = agent_map.get(agent_type.lower(), LLMAgent)
    return agent_class(llm_client=llm_client)
