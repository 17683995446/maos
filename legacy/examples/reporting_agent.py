"""
Reporting Agent - 报告生成Agent示例
负责生成各种格式的报告和可视化
"""

from typing import Any, Dict, List
from datetime import datetime
from agent import Agent, AgentMessage, AgentStatus, MessageType


class ReportingAgent(Agent):
    """报告生成Agent"""

    def __init__(self, name: str = "reporter"):
        super().__init__(
            name=name,
            capabilities=['report_generation', 'format_conversion', 'data_visualization']
        )
        self.reports_generated = 0

    def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理报告生成请求"""
        if message.msg_type == MessageType.REQUEST:
            content = message.content
            data = content.get('input', {})
            report_format = content.get('format', 'text')

            report = self._generate_report(data, report_format)

            self.reports_generated += 1

            return AgentMessage(
                sender=self.name,
                receivers=[message.sender],
                msg_type=MessageType.RESPONSE,
                content={
                    'status': 'success',
                    'report': report,
                    'format': report_format
                },
                reply_to=message.id,
                metadata={'agent': self.name, 'task_type': 'reporting'}
            )

        return super().process_message(message)

    def _generate_report(self, data: Any, format_type: str = 'text') -> Dict[str, Any]:
        """生成报告"""
        report = {
            'title': 'Analysis Report',
            'generated_at': datetime.now().isoformat(),
            'data': data,
            'format': format_type
        }

        if format_type == 'text':
            report['content'] = self._generate_text_report(data)
        elif format_type == 'summary':
            report['content'] = self._generate_summary(data)
        elif format_type == 'detailed':
            report['content'] = self._generate_detailed_report(data)

        return report

    def _generate_text_report(self, data: Any) -> str:
        """生成文本报告"""
        lines = [
            "=" * 50,
            "ANALYSIS REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 50
        ]

        if isinstance(data, dict):
            for key, value in data.items():
                lines.append(f"{key}: {value}")
        elif isinstance(data, list):
            lines.append(f"Total items: {len(data)}")
            for i, item in enumerate(data[:5], 1):
                lines.append(f"  {i}. {item}")

        lines.append("=" * 50)
        return "\n".join(lines)

    def _generate_summary(self, data: Any) -> Dict[str, Any]:
        """生成摘要"""
        summary = {
            'type': type(data).__name__,
            'size': len(data) if hasattr(data, '__len__') else 1
        }

        if isinstance(data, dict):
            summary['keys'] = list(data.keys())
        elif isinstance(data, list):
            summary['first_item_type'] = type(data[0]).__name__ if data else None

        return summary

    def _generate_detailed_report(self, data: Any) -> Dict[str, Any]:
        """生成详细报告"""
        return {
            'overview': self._generate_summary(data),
            'full_data': data,
            'metadata': {
                'generated_by': self.name,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
