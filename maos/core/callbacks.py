"""
MAOS Callbacks Module
MAOS系统的回调模块

提供Agent生命周期回调接口，支持监控、日志、追踪等功能。

回调类型：
- on_agent_start/end: Agent处理生命周期
- on_llm_start/new_token/end: LLM生成过程
- on_tool_start/end/error: 工具调用过程
- on_error: 错误处理

参考：
- AWS Agent Squad的AgentCallbacks设计
- LangChain的回调系统
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID


class AgentCallbacks:
    """
    Agent生命周期回调基类

    定义Agent处理过程中的关键回调点，
    支持监控、日志、追踪和自定义逻辑注入。

    使用方式：
        class MyCallbacks(AgentCallbacks):
            async def on_agent_start(self, ...):
                # 自定义逻辑
                return {}

        agent = Agent(options, callbacks=MyCallbacks())

    回调执行顺序：
        1. on_agent_start (开始处理)
        2. on_llm_start (LLM开始生成)
        3. on_llm_new_token (LLM生成每个token,多次调用)
        4. on_llm_end (LLM生成结束)
        5. on_agent_end (处理完成)
    """

    async def on_agent_start(
        self,
        agent_name: str,
        payload_input: Any,
        messages: List[Any],
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Agent开始处理时的回调

        在Agent开始处理请求之前调用，可用于：
        - 记录开始时间
        - 验证输入
        - 初始化追踪上下文
        - 发送监控事件

        参数：
            agent_name: 开始处理的Agent名称
            payload_input: Agent输入数据
            messages: 对话历史消息列表
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数

        返回：
            跟踪信息字典，会传递给其他回调
        """
        return {}

    async def on_agent_end(
        self,
        agent_name: str,
        response: Any,
        messages: List[Any],
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Agent完成处理时的回调

        在Agent完成请求处理之后调用，可用于：
        - 记录结束时间
        - 发送完成事件
        - 清理资源
        - 记录指标

        参数：
            agent_name: 完成处理的Agent名称
            response: Agent响应内容
            messages: 更新后的对话历史
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数

        返回：
            回调执行结果
        """
        pass

    async def on_llm_start(
        self,
        name: str,
        payload_input: Any,
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        LLM开始生成时的回调

        在LLM开始处理之前调用，可用于：
        - 记录LLM调用开始
        - 发送追踪事件
        - 准备监控上下文

        参数：
            name: LLM名称或标识
            payload_input: 输入数据
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数
        """
        pass

    async def on_llm_new_token(
        self,
        token: str,
        **kwargs: Any,
    ) -> None:
        """
        LLM生成新token时的回调

        在LLM生成每个token时调用，可用于：
        - 流式输出
        - 实时进度显示
        - 增量索引

        参数：
            token: 新生成的token
            **kwargs: 其他参数（如thinking等）
        """
        pass

    async def on_llm_end(
        self,
        name: str,
        output: Any,
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        LLM生成结束时的回调

        在LLM完成生成之后调用，可用于：
        - 记录LLM调用结束
        - 统计token使用
        - 发送追踪事件

        参数：
            name: LLM名称或标识
            output: 生成结果
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数

        返回：
            回调执行结果
        """
        pass

    async def on_error(
        self,
        agent_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        发生错误时的回调

        在Agent处理过程中发生错误时调用，可用于：
        - 错误日志记录
        - 错误追踪
        - 告警通知
        - 错误恢复

        参数：
            agent_name: 发生错误的Agent名称
            error: 异常对象
            context: 错误上下文信息
            **kwargs: 其他参数
        """
        pass


class AgentToolCallbacks:
    """
    工具调用回调基类

    定义工具调用过程中的关键回调点。
    """

    async def on_tool_start(
        self,
        tool_name: str,
        payload_input: Any,
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        工具开始执行时的回调

        参数：
            tool_name: 工具名称
            payload_input: 工具输入参数
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数
        """
        pass

    async def on_tool_end(
        self,
        tool_name: str,
        payload_input: Any,
        output: Any,
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        工具执行结束时的回调

        参数：
            tool_name: 工具名称
            payload_input: 工具输入参数
            output: 工具执行结果
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数
        """
        pass

    async def on_tool_error(
        self,
        tool_name: str,
        payload_input: Any,
        error: Exception,
        run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        工具执行错误时的回调

        参数：
            tool_name: 工具名称
            payload_input: 工具输入参数
            error: 异常对象
            run_id: 唯一运行标识符
            tags: 关联的标签列表
            metadata: 附加元数据
            **kwargs: 其他参数
        """
        pass


class CallbackManager:
    """
    回调管理器

    管理多个回调实例，支持添加、移除和组合回调。
    """

    def __init__(self):
        self._callbacks: List[AgentCallbacks] = []

    def add_callback(self, callback: AgentCallbacks) -> None:
        """
        添加回调实例

        参数：
            callback: 回调实例
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: AgentCallbacks) -> None:
        """
        移除回调实例

        参数：
            callback: 回调实例
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def on_agent_start(self, **kwargs) -> Dict[str, Any]:
        """触发所有on_agent_start回调"""
        results = {}
        for callback in self._callbacks:
            result = await callback.on_agent_start(**kwargs)
            if result:
                results.update(result)
        return results

    async def on_agent_end(self, **kwargs) -> None:
        """触发所有on_agent_end回调"""
        for callback in self._callbacks:
            await callback.on_agent_end(**kwargs)

    async def on_llm_start(self, **kwargs) -> None:
        """触发所有on_llm_start回调"""
        for callback in self._callbacks:
            await callback.on_llm_start(**kwargs)

    async def on_llm_new_token(self, **kwargs) -> None:
        """触发所有on_llm_new_token回调"""
        for callback in self._callbacks:
            await callback.on_llm_new_token(**kwargs)

    async def on_llm_end(self, **kwargs) -> None:
        """触发所有on_llm_end回调"""
        for callback in self._callbacks:
            await callback.on_llm_end(**kwargs)

    async def on_error(self, **kwargs) -> None:
        """触发所有on_error回调"""
        for callback in self._callbacks:
            await callback.on_error(**kwargs)
