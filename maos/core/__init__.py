"""
MAOS Core Module
MAOS系统的核心模块

提供Agent基类、消息类型、状态管理、回调系统和事件机制。

主要组件：
- Agent: 抽象基类，定义Agent接口
- AgentMessage: Agent间通信消息
- AgentStatus: Agent状态枚举
- MessageType: 消息类型枚举
- AgentCallbacks: 生命周期回调
- AgentOptions: 配置选项
- AgentStreamResponse: 流式响应
- AgentProcessingResult: 处理结果元数据
- AgentResponse: 完整响应

使用示例：
    from maos.core import Agent, AgentOptions, AgentStatus, MessageType

    class MyAgent(Agent):
        async def process_request(self, ...):
            # 实现具体逻辑
            pass

    agent = MyAgent(AgentOptions(name="my_agent"))
    await agent.process_request(...)
"""

from .agent import (
    Agent,
    AgentOptions,
    AgentStatus,
    AgentMessage,
    MessageType,
    AgentStreamResponse,
    AgentProcessingResult,
    AgentResponse,
    AgentEvent,
    EventHandler,
    AgentParamsType,
)

from .callbacks import (
    AgentCallbacks,
    AgentToolCallbacks,
    CallbackManager,
)

__all__ = [
    # Agent核心
    'Agent',
    'AgentOptions',
    'AgentStatus',
    'AgentMessage',
    'MessageType',

    # 流式响应
    'AgentStreamResponse',
    'AgentProcessingResult',
    'AgentResponse',

    # 事件系统
    'AgentEvent',
    'EventHandler',

    # 回调系统
    'AgentCallbacks',
    'AgentToolCallbacks',
    'CallbackManager',

    # 类型别名
    'AgentParamsType',
]

__version__ = "0.1.0"
