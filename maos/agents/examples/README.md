# MAOS Agents Examples

本模块包含MAOS系统的三个核心示例Agent实现。

## Agents列表

### 1. DataProcessingAgent
数据处理Agent，负责数据清洗、转换和验证。

**能力**：
- `data_cleaning`: 数据清洗
- `data_transformation`: 数据转换
- `data_validation`: 数据验证

**主要功能**：
- 移除空值和无效数据
- 数据类型转换
- Schema验证
- 数据转换规则应用

### 2. AnalysisAgent
分析Agent，负责数据分析和统计计算。

**能力**：
- `data_analysis`: 基础数据分析
- `statistical_analysis`: 统计分析
- `pattern_recognition`: 模式识别

**主要功能**：
- 数值字段统计分析
- 数据类型检测
- 模式识别和分类
- 数据分布分析

### 3. ReportingAgent
报告生成Agent，负责生成各种格式的报告。

**能力**：
- `report_generation`: 报告生成
- `format_conversion`: 格式转换
- `data_visualization`: 数据可视化

**支持格式**：
- `text`: 文本报告
- `summary`: 摘要报告
- `detailed`: 详细报告
- `json`: JSON格式
- `table`: 表格格式

## 快速开始

### 基本使用

```python
from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
from maos.core import AgentOptions, AgentMessage

# 创建Agent实例
data_agent = DataProcessingAgent(AgentOptions(
    name="DataProcessor",
    description="数据处理器",
    capabilities=["data_cleaning", "data_transformation", "data_validation"]
))

# 处理数据
test_data = [
    {"id": "1", "name": "张三", "email": "zhangsan@example.com"},
    {"id": "2", "name": "李四", "email": "", "age": 25}
]

message = AgentMessage(
    sender="client",
    receivers=["data-processor"],
    content={"input": test_data}
)

response = await data_agent.process_message(message)
print(response.content)
```

### 完整工作流

```python
import asyncio
from maos.agents.examples import (
    DataProcessingAgent,
    AnalysisAgent,
    ReportingAgent
)
from maos.core import AgentOptions, AgentMessage

async def workflow_demo():
    # 1. 数据处理
    data_agent = DataProcessingAgent(AgentOptions(name="DataProcessor"))
    data_msg = AgentMessage(
        sender="workflow",
        content={"input": raw_data}
    )
    data_response = await data_agent.process_message(data_msg)
    processed_data = data_response.content.get('processed_data')

    # 2. 数据分析
    analysis_agent = AnalysisAgent(AgentOptions(name="Analyzer"))
    analysis_msg = AgentMessage(
        sender="workflow",
        content={"input": processed_data}
    )
    analysis_response = await analysis_agent.process_message(analysis_msg)

    # 3. 报告生成
    reporting_agent = ReportingAgent(AgentOptions(name="Reporter"))
    report_msg = AgentMessage(
        sender="workflow",
        content={
            "input": {"data": processed_data, "analysis": analysis_response},
            "format": "detailed",
            "title": "数据分析报告"
        }
    )
    report_response = await reporting_agent.process_message(report_msg)

asyncio.run(workflow_demo())
```

## 文件结构

```
maos/agents/examples/
├── __init__.py              # 模块导出
├── data_agent.py            # 数据处理Agent
├── analysis_agent.py        # 分析Agent
├── reporting_agent.py       # 报告生成Agent
└── usage_demo.py            # 使用示例演示
```

## 运行演示

```bash
# 设置Python路径
export PYTHONPATH=/workspace

# 运行使用演示
python3 maos/agents/examples/usage_demo.py
```

演示内容：
1. 数据处理Agent的使用
2. 分析Agent的使用
3. 报告生成Agent的使用
4. 完整工作流演示

## API参考

### AgentOptions配置

所有Agent都接受`AgentOptions`参数：

```python
@dataclass
class AgentOptions:
    name: str                          # Agent名称
    description: str = ""              # Agent描述
    capabilities: List[str] = []        # 能力列表
    save_chat: bool = True             # 是否保存对话
    callbacks: AgentCallbacks = None   # 回调处理器
    log_debug_trace: bool = False      # 调试追踪
    max_queue_size: int = 1000         # 队列大小
    processing_timeout: float = None   # 处理超时
```

### 消息格式

```python
@dataclass
class AgentMessage:
    id: str                    # 消息ID
    sender: str                # 发送者
    receivers: List[str]       # 接收者列表
    msg_type: MessageType      # 消息类型
    content: Any               # 消息内容
    metadata: Dict[str, Any]   # 附加元数据
    timestamp: datetime        # 时间戳
    reply_to: str = None       # 回复目标
```

### 主要方法

所有Agent继承自`Agent`基类，提供以下核心方法：

- `process_request()`: 处理用户请求
- `process_message()`: 处理消息
- `get_info()`: 获取Agent信息
- `health_check()`: 健康检查
- `get_processing_stats()`: 获取处理统计

## 扩展开发

创建新的Agent只需继承`Agent`基类：

```python
from maos.core import Agent, AgentOptions, AgentMessage

class MyAgent(Agent):
    def __init__(self, options: AgentOptions):
        super().__init__(options)

    async def process_request(self, input_text, user_id, session_id,
                            chat_history, additional_params=None):
        # 实现请求处理逻辑
        return "处理结果"

    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        # 实现消息处理逻辑
        return message.create_response(content="响应内容")
```
