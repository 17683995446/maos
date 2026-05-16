# MAOS Types 模块文档

## 概述

MAOS Types 是 Multi-Agent Orchestration System 的核心类型定义模块，提供了一套完整的类型系统来支持多Agent系统中的对话消息管理。

## 模块结构

```
maos/types/
├── __init__.py           # 模块导出
├── conversation.py       # 核心类型定义
└── examples.py           # 使用示例
```

## 核心类型

### 1. 枚举类型 (Enums)

#### ParticipantRole
参与者角色枚举，定义对话中的不同参与者类型：
- `USER` - 用户
- `ASSISTANT` - AI助手
- `SYSTEM` - 系统
- `AGENT` - Agent
- `TOOL` - 工具
- `FUNCTION` - 函数

#### MessageContentType
消息内容类型枚举：
- `TEXT` - 文本
- `IMAGE_URL` - 图片URL
- `IMAGE_BASE64` - Base64图片
- `TOOL_USE` - 工具调用
- `TOOL_RESULT` - 工具结果
- `FUNCTION_CALL` - 函数调用
- `FUNCTION_RESULT` - 函数结果
- `STREAMING` - 流式内容
- `ERROR` - 错误信息
- `CODE` - 代码
- `MARKDOWN` - Markdown
- `HTML` - HTML
- `JSON` - JSON

#### StreamingStatus
流式响应状态枚举：
- `START` - 开始
- `IN_PROGRESS` - 进行中
- `COMPLETED` - 完成
- `ERROR` - 错误
- `CANCELLED` - 取消

### 2. 数据类 (Dataclasses)

#### MessageContent
消息内容数据类，支持多种内容类型。

**主要属性：**
- `content_type: MessageContentType` - 内容类型
- `text: Optional[str]` - 文本内容
- `image_url: Optional[str]` - 图片URL
- `image_base64: Optional[str]` - Base64图片
- `tool_call: Optional[Dict[str, Any]]` - 工具调用信息
- `tool_result: Optional[Dict[str, Any]]` - 工具执行结果
- `function_call: Optional[Dict[str, Any]]` - 函数调用信息
- `function_result: Optional[Dict[str, Any]]` - 函数执行结果
- `metadata: Dict[str, Any]` - 额外元数据

**工厂方法：**
- `create_text(text, metadata)` - 创建文本消息
- `create_image_url(url, metadata)` - 创建图片URL消息
- `create_tool_call(tool_name, tool_input, tool_id, metadata)` - 创建工具调用
- `create_tool_result(tool_call_id, result, is_error, metadata)` - 创建工具结果

#### ConversationMessage
对话消息数据类，支持与Legacy版本兼容。

**主要属性：**
- `id: str` - 消息唯一标识符
- `role: ParticipantRole` - 消息发送者角色
- `content: Union[str, List[MessageContent], MessageContent]` - 消息内容
- `sender: str` - 发送者名称
- `receivers: List[str]` - 接收者名称列表
- `timestamp: datetime` - 消息时间戳
- `metadata: Dict[str, Any]` - 消息元数据
- `tags: List[str]` - 消息标签
- `conversation_id: Optional[str]` - 所属对话ID
- `parent_id: Optional[str]` - 父消息ID（用于多轮对话）
- `streaming: bool` - 是否为流式响应
- `streaming_status: Optional[StreamingStatus]` - 流式响应状态
- `is_final: bool` - 是否为最终消息

**主要方法：**
- `get_text_content()` - 获取文本内容
- `to_dict()` - 序列化为字典
- `from_dict(data)` - 从字典反序列化
- `to_legacy_format()` - 转换为Legacy格式
- `from_legacy_format(legacy_data)` - 从Legacy格式转换

#### StreamingChunk
流式响应数据块。

**主要属性：**
- `message_id: str` - 所属消息ID
- `chunk_index: int` - 块索引
- `content: str` - 块内容
- `is_final: bool` - 是否为最后一个块
- `status: StreamingStatus` - 流状态
- `timestamp: datetime` - 块时间戳
- `metadata: Dict[str, Any]` - 额外元数据

#### ConversationTurn
对话回合，表示多轮对话中的一个完整回合。

**主要属性：**
- `id: str` - 回合唯一标识符
- `conversation_id: Optional[str]` - 所属对话ID
- `user_message: Optional[ConversationMessage]` - 用户消息
- `assistant_message: Optional[ConversationMessage]` - Agent响应消息
- `tool_calls: List[ConversationMessage]` - 工具调用列表
- `tool_results: List[ConversationMessage]` - 工具执行结果列表
- `timestamp: datetime` - 回合时间戳
- `duration_ms: Optional[float]` - 响应耗时（毫秒）
- `metadata: Dict[str, Any]` - 额外元数据

**主要方法：**
- `get_all_messages()` - 获取回合中的所有消息

#### ConversationContext
对话上下文，存储和管理多轮对话的上下文信息。

**主要属性：**
- `conversation_id: str` - 对话唯一标识符
- `messages: List[ConversationMessage]` - 消息历史
- `turns: List[ConversationTurn]` - 对话回合列表
- `current_turn_index: int` - 当前回合索引
- `metadata: Dict[str, Any]` - 对话元数据
- `tags: List[str]` - 对话标签
- `created_at: datetime` - 创建时间
- `updated_at: datetime` - 最后更新时间
- `system_prompt: Optional[str]` - 系统提示
- `max_turns: Optional[int]` - 最大回合数

**主要方法：**
- `add_message(message)` - 添加消息到上下文
- `get_messages_by_role(role, limit)` - 获取指定角色的消息
- `get_recent_messages(count)` - 获取最近的消息
- `to_dict()` - 序列化为字典
- `from_dict(data)` - 从字典反序列化

### 3. 类型别名 (Type Aliases)

#### StreamingCallback
流式回调函数类型：`Callable[[StreamingChunk], None]`

#### MessageHandler
消息处理器类型：`Callable[[ConversationMessage], Optional[ConversationMessage]]`

#### ContentFormatter
内容格式化器类型：`Callable[[MessageContent], str]`

## 主要特性

### 1. Legacy版本兼容性
- ✅ 支持与Legacy版本的AgentMessage格式互转
- ✅ `to_legacy_format()` - 转换为Legacy格式
- ✅ `from_legacy_format()` - 从Legacy格式转换

### 2. 流式响应支持
- ✅ `StreamingChunk` - 流式数据块
- ✅ `StreamingStatus` - 流状态枚举
- ✅ 支持部分内容和最终内容的区分

### 3. 多轮对话支持
- ✅ `ConversationContext` - 对话上下文管理
- ✅ `ConversationTurn` - 对话回合
- ✅ 消息历史追踪
- ✅ 角色过滤和消息检索

### 4. 元数据和标签
- ✅ 支持任意元数据
- ✅ 支持标签分类
- ✅ 完整的时间戳追踪

### 5. 序列化支持
- ✅ 完整的 `to_dict()` 和 `from_dict()` 方法
- ✅ 支持JSON序列化
- ✅ 支持数据库存储

### 6. 多模态内容
- ✅ 文本内容
- ✅ 图片（URL和Base64）
- ✅ 工具调用和结果
- ✅ 函数调用和结果

## 使用示例

详见 [examples.py](examples.py)

## 导入方式

```python
# 导入所有类型
from maos.types import (
    ParticipantRole,
    MessageContentType,
    StreamingStatus,
    MessageContent,
    ConversationMessage,
    StreamingChunk,
    ConversationTurn,
    ConversationContext,
)

# 导入单个类型
from maos.types.conversation import ConversationMessage, MessageContent
```

## 版本信息

- **版本**: 1.0.0
- **Python版本**: 3.10+
- **依赖**: dataclasses, datetime, enum, typing, uuid

## 设计原则

1. **类型安全**: 使用完整的类型注解
2. **向后兼容**: 与Legacy版本完全兼容
3. **可扩展性**: 支持自定义元数据和标签
4. **实用性**: 提供工厂方法和便捷方法
5. **序列化**: 支持JSON和字典格式的序列化

## 扩展建议

### 添加新的消息内容类型

1. 在 `MessageContentType` 枚举中添加新类型
2. 在 `MessageContent` 类中添加相应属性
3. 更新 `to_dict()` 和 `from_dict()` 方法

### 添加新的角色类型

1. 在 `ParticipantRole` 枚举中添加新角色
2. 确保与Legacy格式的兼容性

## 注意事项

1. 所有时间戳使用 `datetime` 对象
2. 消息ID使用UUID自动生成
3. 默认值使用 `field(default_factory=...)` 模式
4. 枚举值使用小写字符串便于JSON序列化
