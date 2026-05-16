"""
MAOS Types 使用示例
展示如何创建和使用MAOS系统中的类型定义
"""

from conversation import (
    ParticipantRole, MessageContentType, StreamingStatus,
    MessageContent, ConversationMessage, StreamingChunk,
    ConversationTurn, ConversationContext
)


def basic_message_example():
    """基础消息示例"""
    print("=== 基础消息示例 ===")

    msg = ConversationMessage(
        role=ParticipantRole.USER,
        content="你好，请帮我查询天气"
    )

    print(f"消息ID: {msg.id}")
    print(f"角色: {msg.role.value}")
    print(f"内容: {msg.get_text_content()}")

    print()


def multi_modal_message_example():
    """多模态消息示例"""
    print("=== 多模态消息示例 ===")

    content = [
        MessageContent.create_text("请看这张图片并描述内容:"),
        MessageContent.create_image_url("https://example.com/image.jpg"),
    ]

    msg = ConversationMessage(
        role=ParticipantRole.USER,
        content=content
    )

    print(f"消息内容类型: {type(msg.content).__name__}")
    print(f"内容块数量: {len(msg.content)}")

    print()


def tool_call_example():
    """工具调用示例"""
    print("=== 工具调用示例 ===")

    tool_call = MessageContent.create_tool_call(
        tool_name="weather_api",
        tool_input={"city": "北京", "unit": "celsius"},
        tool_id="call_123"
    )

    print(f"工具名称: {tool_call.tool_call['name']}")
    print(f"工具输入: {tool_call.tool_call['input']}")

    tool_result = MessageContent.create_tool_result(
        tool_call_id="call_123",
        result={"temperature": 25, "condition": "晴朗"}
    )

    print(f"工具结果: {tool_result.tool_result['content']}")

    print()


def streaming_example():
    """流式响应示例"""
    print("=== 流式响应示例 ===")

    chunks = []
    full_content = ""

    for i, chunk_text in enumerate(["你好", "，欢迎", "使用MAOS", "系统！"]):
        chunk = StreamingChunk(
            message_id="msg_streaming",
            chunk_index=i,
            content=chunk_text,
            is_final=(i == 3),
            status=StreamingStatus.COMPLETED if i == 3 else StreamingStatus.IN_PROGRESS
        )
        chunks.append(chunk)
        full_content += chunk.content

    print(f"流式块数量: {len(chunks)}")
    print(f"完整内容: {full_content}")
    print(f"最终块状态: {chunks[-1].status.value}")

    print()


def conversation_context_example():
    """多轮对话上下文示例"""
    print("=== 多轮对话上下文示例 ===")

    context = ConversationContext(
        conversation_id="conv_001",
        system_prompt="你是一个有帮助的AI助手",
        max_turns=10
    )

    # 添加用户消息
    user_msg = ConversationMessage(
        role=ParticipantRole.USER,
        content="今天天气怎么样？"
    )
    context.add_message(user_msg)

    # 添加助手消息
    assistant_msg = ConversationMessage(
        role=ParticipantRole.ASSISTANT,
        content="今天是晴天，气温25度。"
    )
    context.add_message(assistant_msg)

    # 添加更多消息
    context.add_message(ConversationMessage(
        role=ParticipantRole.USER,
        content="适合出门吗？"
    ))

    print(f"对话ID: {context.conversation_id}")
    print(f"总消息数: {len(context.messages)}")
    print(f"用户消息数: {len(context.get_messages_by_role(ParticipantRole.USER))}")
    print(f"助手消息数: {len(context.get_messages_by_role(ParticipantRole.ASSISTANT))}")
    print(f"最近2条消息: {[m.get_text_content() for m in context.get_recent_messages(2)]}")

    print()


def legacy_compatibility_example():
    """Legacy版本兼容性示例"""
    print("=== Legacy版本兼容性示例 ===")

    # 模拟Legacy格式的AgentMessage
    legacy_data = {
        'id': 'legacy_msg_001',
        'sender': 'analysis_agent',
        'receivers': ['orchestrator'],
        'msg_type': 'response',
        'content': '分析完成，发现3个关键点',
        'metadata': {'confidence': 0.92},
        'timestamp': '2024-01-15T10:30:00'
    }

    # 从Legacy格式转换
    msg = ConversationMessage.from_legacy_format(legacy_data)
    print(f"转换后的角色: {msg.role.value}")
    print(f"转换后的内容: {msg.content}")

    # 转换为Legacy格式
    legacy_output = msg.to_legacy_format()
    print(f"转换回Legacy格式的msg_type: {legacy_output['msg_type']}")

    print()


def conversation_turn_example():
    """对话回合示例"""
    print("=== 对话回合示例 ===")

    turn = ConversationTurn(conversation_id="conv_002")

    # 用户消息
    turn.user_message = ConversationMessage(
        role=ParticipantRole.USER,
        content="帮我查询北京的天气"
    )

    # 助手调用的工具
    turn.tool_calls.append(ConversationMessage(
        role=ParticipantRole.ASSISTANT,
        content=MessageContent.create_tool_call(
            "weather_api",
            {"city": "北京"}
        )
    ))

    # 工具执行结果
    turn.tool_results.append(ConversationMessage(
        role=ParticipantRole.TOOL,
        content=MessageContent.create_tool_result(
            "call_001",
            {"temperature": 25, "condition": "晴"}
        )
    ))

    # 助手最终响应
    turn.assistant_message = ConversationMessage(
        role=ParticipantRole.ASSISTANT,
        content="北京今天天气晴朗，气温25度，适合外出。"
    )

    print(f"回合ID: {turn.id}")
    print(f"消息总数: {len(turn.get_all_messages())}")
    print(f"工具调用次数: {len(turn.tool_calls)}")
    print(f"工具结果次数: {len(turn.tool_results)}")

    print()


def serialization_example():
    """序列化/反序列化示例"""
    print("=== 序列化/反序列化示例 ===")

    # 创建复杂消息
    original = ConversationMessage(
        role=ParticipantRole.ASSISTANT,
        content=[
            MessageContent.create_text("分析结果："),
            MessageContent.create_tool_result("call_x", {"count": 3})
        ],
        metadata={"confidence": 0.95},
        tags=["analysis", "important"]
    )

    # 序列化为字典
    msg_dict = original.to_dict()
    print(f"序列化后的字典键: {list(msg_dict.keys())}")
    print(f"元数据: {msg_dict['metadata']}")
    print(f"标签: {msg_dict['tags']}")

    # 从字典恢复
    restored = ConversationMessage.from_dict(msg_dict)
    print(f"恢复后的内容类型: {type(restored.content).__name__}")
    print(f"恢复后的角色: {restored.role.value}")

    print()


if __name__ == "__main__":
    basic_message_example()
    multi_modal_message_example()
    tool_call_example()
    streaming_example()
    conversation_context_example()
    legacy_compatibility_example()
    conversation_turn_example()
    serialization_example()

    print("=" * 50)
    print("所有示例执行完成！")
