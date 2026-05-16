"""
Reporting Agent - 报告生成Agent示例
负责生成各种格式的报告和可视化

功能特性：
- 报告生成：文本、摘要、详细报告
- 格式转换：支持多种输出格式
- 数据可视化：图表和结构化展示
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, AsyncIterable
from datetime import datetime

from maos.core import (
    Agent,
    AgentOptions,
    AgentMessage,
    AgentStatus,
    MessageType,
    AgentStreamResponse,
    AgentCallbacks,
    AgentParamsType,
)


class ReportingAgent(Agent):
    """
    报告生成Agent

    负责根据输入数据生成各种格式和风格的报告。
    支持文本报告、摘要报告、详细报告等多种格式。

    能力：
        - report_generation: 报告生成
        - format_conversion: 格式转换
        - data_visualization: 数据可视化
    """

    SUPPORTED_FORMATS = ['text', 'summary', 'detailed', 'json', 'table']

    def __init__(
        self,
        options: AgentOptions,
        callbacks: Optional[AgentCallbacks] = None
    ):
        """
        初始化ReportingAgent

        参数：
            options: Agent配置选项
            callbacks: 可选的回调处理器
        """
        if callbacks:
            options.callbacks = callbacks
        super().__init__(options)
        self.reports_generated = 0
        self._initialize_reporting_stats()

    def _initialize_reporting_stats(self) -> None:
        """初始化报告生成统计信息"""
        self.stats = {
            'total_reports': 0,
            'format_breakdown': {fmt: 0 for fmt in self.SUPPORTED_FORMATS},
            'average_generation_time': 0.0,
        }
        self._report_history: List[Dict[str, Any]] = []

    async def process_request(
        self,
        input_text: str,
        user_id: str,
        session_id: str,
        chat_history: List[Any],
        additional_params: Optional[AgentParamsType] = None
    ) -> str:
        """
        处理用户请求

        参数：
            input_text: 用户输入文本
            user_id: 用户标识
            session_id: 会话标识
            chat_history: 对话历史
            additional_params: 附加参数

        返回：
            生成的报告内容
        """
        self.reports_generated += 1

        try:
            import json

            data = None
            report_format = 'text'

            if additional_params:
                data = additional_params.get('data')
                report_format = additional_params.get('format', 'text')

            if not data and input_text:
                if input_text.startswith('{') or input_text.startswith('['):
                    try:
                        data = json.loads(input_text)
                    except json.JSONDecodeError:
                        data = {'content': input_text}
                else:
                    data = {'content': input_text}

            if not data:
                return "报告生成失败: 未提供有效数据"

            report = self._generate_report(data, report_format)
            return f"报告生成完成 ({report_format}格式)"

        except Exception as e:
            return f"报告生成失败: {str(e)}"

    async def _process_message_impl(self, message: AgentMessage) -> AgentMessage:
        """
        处理消息实现

        参数：
            message: 输入消息

        返回：
            响应消息
        """
        try:
            content = message.content

            if isinstance(content, dict):
                data = content.get('input', content.get('data', {}))
                report_format = content.get('format', 'text')
                title = content.get('title', 'Analysis Report')
            else:
                data = content
                report_format = 'text'
                title = 'Analysis Report'

            if not data:
                return message.create_response(
                    content={'status': 'error', 'message': '未提供报告数据'},
                    metadata={'error': 'no_data'}
                )

            if report_format not in self.SUPPORTED_FORMATS:
                report_format = 'text'

            report = self._generate_report(data, report_format, title)
            self.reports_generated += 1
            self._update_stats(report_format)

            return message.create_response(
                content={
                    'status': 'success',
                    'report': report,
                    'format': report_format,
                    'report_metadata': {
                        'agent': self.name,
                        'title': title,
                        'generated_at': self._get_timestamp(),
                        'data_size': self._calculate_data_size(data)
                    }
                },
                metadata={
                    'agent': self.name,
                    'task_type': 'reporting',
                    'format': report_format
                }
            )

        except Exception as e:
            self.log_error(f"报告生成错误: {str(e)}")
            return message.create_response(
                content={'status': 'error', 'message': f'报告生成错误: {str(e)}'},
                metadata={'error': str(e)}
            )

    def _generate_report(
        self,
        data: Any,
        format_type: str = 'text',
        title: str = 'Analysis Report'
    ) -> Dict[str, Any]:
        """
        生成报告

        参数：
            data: 报告数据
            format_type: 报告格式
            title: 报告标题

        返回：
            生成的报告字典
        """
        report = {
            'title': title,
            'generated_at': self._get_timestamp(),
            'data': data,
            'format': format_type
        }

        if format_type == 'text':
            report['content'] = self._generate_text_report(data, title)
        elif format_type == 'summary':
            report['content'] = self._generate_summary(data)
        elif format_type == 'detailed':
            report['content'] = self._generate_detailed_report(data, title)
        elif format_type == 'json':
            report['content'] = self._generate_json_report(data)
        elif format_type == 'table':
            report['content'] = self._generate_table_report(data)
        else:
            report['content'] = self._generate_text_report(data, title)

        self._report_history.append({
            'timestamp': self._get_timestamp(),
            'format': format_type,
            'title': title
        })

        return report

    def _generate_text_report(self, data: Any, title: str = 'Report') -> str:
        """
        生成文本格式报告

        参数：
            data: 报告数据
            title: 报告标题

        返回：
            文本报告字符串
        """
        lines = [
            "=" * 60,
            title.upper(),
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 60
        ]

        if isinstance(data, dict):
            for key, value in data.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, (dict, list)):
                    lines.append(f"{formatted_key}:")
                    lines.extend(self._format_nested_data(value, indent=2))
                else:
                    lines.append(f"{formatted_key}: {value}")

        elif isinstance(data, list):
            lines.append(f"Total Items: {len(data)}")
            lines.append("-" * 40)
            for i, item in enumerate(data[:10], 1):
                lines.append(f"  {i}. {self._format_item(item)}")
            if len(data) > 10:
                lines.append(f"  ... and {len(data) - 10} more items")

        else:
            lines.append(str(data))

        lines.append("=" * 60)
        lines.append(f"Report generated by {self.name}")
        return "\n".join(lines)

    def _generate_summary(self, data: Any) -> Dict[str, Any]:
        """
        生成摘要报告

        参数：
            data: 报告数据

        返回：
            摘要字典
        """
        summary = {
            'type': type(data).__name__,
            'size': len(data) if hasattr(data, '__len__') else 1,
            'generated_at': self._get_timestamp()
        }

        if isinstance(data, dict):
            summary['keys'] = list(data.keys())
            summary['key_count'] = len(data)

            numeric_values = {
                k: v for k, v in data.items()
                if isinstance(v, (int, float))
            }
            if numeric_values:
                summary['numeric_keys'] = list(numeric_values.keys())

        elif isinstance(data, list):
            if data:
                summary['first_item_type'] = type(data[0]).__name__
                summary['last_item_type'] = type(data[-1]).__name__

                if data and isinstance(data[0], dict):
                    common_keys = set(data[0].keys())
                    for item in data[1:]:
                        if isinstance(item, dict):
                            common_keys &= set(item.keys())
                    summary['common_keys'] = list(common_keys) if common_keys else []

        return summary

    def _generate_detailed_report(
        self,
        data: Any,
        title: str = 'Detailed Report'
    ) -> Dict[str, Any]:
        """
        生成详细报告

        参数：
            data: 报告数据
            title: 报告标题

        返回：
            详细报告字典
        """
        return {
            'overview': self._generate_summary(data),
            'full_data': data,
            'metadata': {
                'generated_by': self.name,
                'title': title,
                'timestamp': self._get_timestamp(),
                'version': '1.0',
                'data_type': type(data).__name__
            },
            'statistics': self._generate_data_statistics(data)
        }

    def _generate_json_report(self, data: Any) -> Dict[str, Any]:
        """
        生成JSON格式报告

        参数：
            data: 报告数据

        返回：
            JSON报告字典
        """
        return {
            'report': {
                'generated_at': self._get_timestamp(),
                'generator': self.name,
                'version': '1.0'
            },
            'data': data,
            'metadata': {
                'type': type(data).__name__,
                'size': len(data) if hasattr(data, '__len__') else 1
            }
        }

    def _generate_table_report(self, data: Any) -> Dict[str, Any]:
        """
        生成表格格式报告

        参数：
            data: 报告数据

        返回：
            表格报告字典
        """
        table_report = {
            'headers': [],
            'rows': [],
            'metadata': {
                'generated_at': self._get_timestamp()
            }
        }

        if isinstance(data, dict):
            table_report['headers'] = ['Key', 'Value']
            for key, value in data.items():
                table_report['rows'].append([key, self._format_value(value)])

        elif isinstance(data, list) and data:
            if isinstance(data[0], dict):
                keys = list(data[0].keys())
                table_report['headers'] = keys

                for item in data:
                    if isinstance(item, dict):
                        row = [self._format_value(item.get(k, '')) for k in keys]
                        table_report['rows'].append(row)

            else:
                table_report['headers'] = ['Index', 'Value']
                for i, item in enumerate(data):
                    table_report['rows'].append([i, self._format_value(item)])

        return table_report

    def _generate_data_statistics(self, data: Any) -> Dict[str, Any]:
        """
        生成数据统计信息

        参数：
            data: 数据对象

        返回：
            统计信息字典
        """
        stats = {
            'data_type': type(data).__name__,
            'is_empty': self._is_empty(data)
        }

        if isinstance(data, dict):
            stats['field_count'] = len(data)
            stats['field_names'] = list(data.keys())

        elif isinstance(data, list):
            stats['item_count'] = len(data)
            stats['item_types'] = self._count_item_types(data)

        elif isinstance(data, (int, float)):
            stats['value'] = data
            stats['category'] = self._categorize_value(data)

        return stats

    def _format_nested_data(
        self,
        data: Any,
        indent: int = 0,
        max_depth: int = 3
    ) -> List[str]:
        """
        格式化嵌套数据

        参数：
            data: 数据对象
            indent: 缩进级别
            max_depth: 最大嵌套深度

        返回：
            格式化后的行列表
        """
        lines = []
        prefix = "  " * indent

        if indent >= max_depth:
            lines.append(f"{prefix}...")
            return lines

        if isinstance(data, dict):
            for key, value in list(data.items())[:10]:
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(self._format_nested_data(value, indent + 1, max_depth))
                else:
                    lines.append(f"{prefix}{key}: {value}")

        elif isinstance(data, list):
            for i, item in enumerate(data[:10]):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.extend(self._format_nested_data(item, indent + 1, max_depth))
                else:
                    lines.append(f"{prefix}[{i}]: {item}")

            if len(data) > 10:
                lines.append(f"{prefix}... and {len(data) - 10} more")

        return lines

    def _format_item(self, item: Any) -> str:
        """
        格式化单个数据项

        参数：
            item: 数据项

        返回：
            格式化字符串
        """
        if isinstance(item, dict):
            return str({k: v for k, v in list(item.items())[:3]})
        elif isinstance(item, str):
            return item[:50] + '...' if len(item) > 50 else item
        return str(item)

    def _format_value(self, value: Any) -> str:
        """
        格式化单个值

        参数：
            value: 值

        返回：
            格式化字符串
        """
        if isinstance(value, (dict, list)):
            return str(type(value).__name__)
        elif isinstance(value, str):
            return value[:100] + '...' if len(value) > 100 else value
        return str(value)

    def _count_item_types(self, data: List[Any]) -> Dict[str, int]:
        """
        统计列表中各类型数量

        参数：
            data: 列表数据

        返回：
            类型计数字典
        """
        type_counts = {}
        for item in data:
            type_name = type(item).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts

    def _categorize_value(self, value: float) -> str:
        """
        数值分类

        参数：
            value: 数值

        返回：
            分类标签
        """
        if isinstance(value, int):
            return 'integer'
        return 'float'

    def _is_empty(self, data: Any) -> bool:
        """
        检查数据是否为空

        参数：
            data: 数据对象

        返回：
            是否为空
        """
        if data is None:
            return True
        if isinstance(data, (str, list, dict)):
            return len(data) == 0
        return False

    def _calculate_data_size(self, data: Any) -> int:
        """
        计算数据大小

        参数：
            data: 数据对象

        返回：
            估计的数据大小（字节）
        """
        import sys
        return len(str(data).encode('utf-8'))

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳

        返回：
            ISO格式的时间字符串
        """
        return datetime.now().isoformat()

    def _update_stats(self, format_type: str) -> None:
        """
        更新统计信息

        参数：
            format_type: 报告格式
        """
        self.stats['total_reports'] += 1
        if format_type in self.stats['format_breakdown']:
            self.stats['format_breakdown'][format_type] += 1

    def get_reporting_stats(self) -> Dict[str, Any]:
        """
        获取报告生成统计信息

        返回：
            统计信息字典
        """
        return {
            **self.stats,
            'current_session_reports': self.reports_generated,
            'report_history_size': len(self._report_history)
        }

    async def stream_report_generation(
        self,
        data: Any,
        format_type: str = 'text',
        title: str = 'Report'
    ) -> AsyncIterable[AgentStreamResponse]:
        """
        流式报告生成

        参数：
            data: 报告数据
            format_type: 报告格式
            title: 报告标题

        生成：
            AgentStreamResponse: 生成进度和结果
        """
        yield AgentStreamResponse(
            text="开始生成报告...",
            final_message=None
        )

        await asyncio.sleep(0.1)

        yield AgentStreamResponse(
            text="处理数据...",
            final_message=None
        )

        report = self._generate_report(data, format_type, title)

        await asyncio.sleep(0.1)

        yield AgentStreamResponse(
            text="格式化输出...",
            final_message=None
        )

        yield AgentStreamResponse(
            text="",
            final_message=f"报告生成完成: {title} ({format_type}格式)"
        )
