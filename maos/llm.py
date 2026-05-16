"""
MAOS v5.0 - LLM Integration Module
支持硅基流动等兼容OpenAI格式的大模型API
"""

import os
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

# 尝试导入OpenAI SDK
try:
    from openai import OpenAI, AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class LLMProvider(Enum):
    """LLM提供商枚举"""
    SILICONFLOW = "siliconflow"
    OPENAI = "openai"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider = LLMProvider.SILICONFLOW
    api_key: str = ""
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量创建配置"""
        return cls(
            api_key=os.getenv("SILICONFLOW_API_KEY", ""),
            base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
            model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"),
            temperature=float(os.getenv("SILICONFLOW_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("SILICONFLOW_MAX_TOKENS", "2048"))
        )


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # "system", "user", "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


class LLMClient:
    """LLM客户端 - 支持硅基流动等OpenAI兼容API"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self._sync_client: Optional[Any] = None
        self._async_client: Optional[Any] = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化OpenAI兼容客户端"""
        if HAS_OPENAI and self.config.api_key:
            self._sync_client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
            self._async_client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return HAS_OPENAI and self.config.api_key and self._sync_client is not None
    
    def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> LLMResponse:
        """同步聊天补全"""
        if not self.is_available():
            raise RuntimeError("LLM client not available. Check API key and dependencies.")
        
        # 准备API参数
        api_messages = [msg.to_dict() for msg in messages]
        params = {
            "model": model or self.config.model,
            "messages": api_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }
        
        # 调用API
        response = self._sync_client.chat.completions.create(**params)
        
        # 解析响应
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=dict(response.usage) if response.usage else None,
            raw_response=response
        )
    
    async def achat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> LLMResponse:
        """异步聊天补全"""
        if not self.is_available():
            raise RuntimeError("LLM client not available. Check API key and dependencies.")
        
        # 准备API参数
        api_messages = [msg.to_dict() for msg in messages]
        params = {
            "model": model or self.config.model,
            "messages": api_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }
        
        # 调用API
        response = await self._async_client.chat.completions.create(**params)
        
        # 解析响应
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=dict(response.usage) if response.usage else None,
            raw_response=response
        )
    
    async def achat_stream(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """异步流式聊天补全"""
        if not self.is_available():
            raise RuntimeError("LLM client not available. Check API key and dependencies.")
        
        # 准备API参数
        api_messages = [msg.to_dict() for msg in messages]
        params = {
            "model": model or self.config.model,
            "messages": api_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": True
        }
        
        # 流式调用
        stream = await self._async_client.chat.completions.create(**params)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def simple_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """简单提示词调用"""
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))
        
        response = self.chat(messages)
        return response.content


# 全局实例
_default_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局LLM客户端"""
    global _default_llm_client
    if _default_llm_client is None:
        _default_llm_client = LLMClient()
    return _default_llm_client


def set_llm_client(client: LLMClient) -> None:
    """设置全局LLM客户端"""
    global _default_llm_client
    _default_llm_client = client


def available_models() -> List[str]:
    """硅基流动可用的模型列表"""
    return [
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Llama-3.1-405B-Instruct",
        "THUDM/glm-4-9b-chat",
        "01-ai/Yi-1.5-34B-Chat"
    ]
