"""
MAOS v11.0 - LLM深度集成
真实LLM API集成(SiliconFlow/OpenAI)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import openai
import asyncio
import json


class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"
    SILICONFLOW = "siliconflow"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class LLMMessage:
    """LLM消息"""
    role: str
    content: str
    name: Optional[str] = None


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = True


class LLMClient:
    """LLM客户端"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig(
            provider=LLMProvider.SILICONFLOW,
            model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        )
        self.client = self._init_client()

    def _init_client(self):
        """初始化客户端"""
        api_key = os.environ.get("SILICONFLOW_API_KEY", "REDACTED_API_KEY")
        base_url = None

        if self.config.provider == LLMProvider.SILICONFLOW:
            api_key = os.environ.get("SILICONFLOW_API_KEY", "REDACTED_API_KEY")
            base_url = "https://api.siliconflow.cn/v1"
        elif self.config.provider == LLMProvider.OPENAI:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            base_url = "https://api.openai.com/v1"

        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        return client

    async def generate(self,
                    messages: List[LLMMessage],
                    config: Optional[LLMConfig] = None) -> str:
        """生成LLM生成"""
        config = config or self.config

        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        response = await self.client.chat.completions.create(
            model=config.model,
            messages=formatted_messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stream=False,
        )

        return response.choices[0].message.content

    async def generate_stream(self,
                             messages: List[LLMMessage],
                             config: Optional[LLMConfig] = None) -> AsyncGenerator[str, None]:
        """流式生成"""
        config = config or self.config

        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        response = await self.client.chat.completions.create(
            model=config.model,
            messages=formatted_messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AIAssistant:
    """AI助手"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.conversation_history: List[LLMMessage] = []

    async def chat(self, user_input: str, system_prompt: Optional[str] = None) -> str:
        """聊天"""
        messages = []

        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        messages.extend(self.conversation_history)
        messages.append(LLMMessage(role="user", content=user_input))

        response = await self.llm.generate(messages)
        self.conversation_history.append(LLMMessage(role="user", content=user_input))
        self.conversation_history.append(LLMMessage(role="assistant", content=response))

        return response

    async def chat_stream(self, user_input: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式聊天"""
        messages = []

        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        messages.extend(self.conversation_history)
        messages.append(LLMMessage(role="user", content=user_input))

        response = ""
        async for chunk in self.llm.generate_stream(messages):
            response += chunk
            yield chunk

        self.conversation_history.append(LLMMessage(role="user", content=user_input))
        self.conversation_history.append(LLMMessage(role="assistant", content=response))

    async def generate_workflow(self, description: str) -> Dict:
        """根据描述生成工作流"""
        system_prompt = """
你是一个多Agent编排系统的工作流生成专家。根据用户的自然语言描述，生成一个工作流的JSON结构。

生成的JSON应该包含以下字段：
- name: 工作流名称
- description: 工作流描述
- nodes: 节点数组，每个节点包含
  - id: 唯一ID
  - type: 节点类型 (task/llm/api_call/data_transform/condition/parallel/loop等
  - name: 节点名称
  - position: x,y 坐标
  - config: 节点配置
- connections: 连接数组，包含fromNode, toNode

使用以下节点类型：
- start: 开始节点
- task: 任务节点
- llm: LLM处理节点
- api_call: API调用节点
- data_transform: 数据转换节点
- condition: 条件判断节点
- parallel: 并行执行节点
- loop: 循环节点
- end: 结束节点

请只返回JSON，不要包含其他文字。
"""

        response = await self.llm.generate([
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=description),
        ])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": response}

    async def generate_code(self, task_description: str, language: str = "python") -> str:
        """生成代码"""
        prompt = f"""
你是一个代码生成专家。根据任务描述生成高质量的代码。

任务描述：{task_description}

语言：{language}

请只返回代码，不要包含其他文字。
"""

        return await self.llm.generate([
            LLMMessage(role="user", content=prompt),
        ])

    async def optimize_workflow(self, workflow: Dict) -> Dict:
        """优化工作流"""
        prompt = f"""
你是一个工作流优化专家。分析并优化给定的工作流。

工作流：
{json.dumps(workflow, indent=2, ensure_ascii=False)}

请提供以下优化建议：
1. 性能优化
2. 成本优化
3. 错误处理改进
4. 并行化建议

请用中文回答，返回JSON格式。
"""

        response = await self.llm.generate([
            LLMMessage(role="user", content=prompt),
        ])

        try:
            return json.loads(response)
        except:
            return {"suggestions": response}

    async def fix_error(self, error: str, context: str = "") -> str:
        """修复错误"""
        prompt = f"""
错误：{error}

上下文：{context}

请提供详细解释错误并提供修复方案。
"""

        return await self.llm.generate([
            LLMMessage(role="user", content=prompt),
        ])

    async def suggest_improvements(self, workflow: Dict) -> List[Dict]:
        """建议改进"""
        prompt = f"""
分析以下工作流，提供改进建议。

工作流：
{json.dumps(workflow, indent=2, ensure_ascii=False)}

请返回建议列表：
- suggestion: 建议内容
- priority: 优先级 (high/medium/low)
- impact: 影响描述
"""

        response = await self.llm.generate([
            LLMMessage(role="user", content=prompt),
        ])

        try:
            data = json.loads(response)
            if isinstance(data, dict) and "suggestions" in data:
                return data["suggestions"]
            return data
        except:
            return [{"suggestion": response, "priority": "medium"}]


# LLM节点处理器
class LLMNodeProcessor:
    """LLM节点处理器"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    async def process(self, node_config: Dict, input_data: Any = None) -> Any:
        """处理LLM节点"""
        prompt = node_config.get("prompt", "")

        if input_data:
            prompt = f"{prompt}\n\n输入数据：{input_data}"

        system_prompt = node_config.get("system_prompt", "你是一个有用的AI助手。")

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=prompt),
        ]

        return await self.llm.generate(messages)


# 初始化默认配置
DEFAULT_CONFIG = LLMConfig(
    provider=LLMProvider.SILICONFLOW,
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    temperature=0.7,
    max_tokens=2000,
)
