"""
Analysis Agent - 分析Agent示例
负责数据分析、统计计算和模式识别
"""

from typing import Any, Dict, List
from agent import Agent, AgentMessage, AgentStatus, MessageType


class AnalysisAgent(Agent):
    """数据分析Agent"""

    def __init__(self, name: str = "analyzer"):
        super().__init__(
            name=name,
            capabilities=['data_analysis', 'statistical_analysis', 'pattern_recognition']
        )
        self.analysis_count = 0

    def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理数据分析请求"""
        if message.msg_type == MessageType.REQUEST:
            content = message.content
            data = content.get('input', {})

            analysis_result = self._analyze_data(data)

            self.analysis_count += 1

            return AgentMessage(
                sender=self.name,
                receivers=[message.sender],
                msg_type=MessageType.RESPONSE,
                content={
                    'status': 'success',
                    'analysis': analysis_result
                },
                reply_to=message.id,
                metadata={'agent': self.name, 'task_type': 'analysis'}
            )

        return super().process_message(message)

    def _analyze_data(self, data: Any) -> Dict[str, Any]:
        """执行数据分析"""
        if isinstance(data, dict):
            return self._analyze_dict(data)
        elif isinstance(data, list):
            return self._analyze_list(data)
        return {'summary': 'Data type not supported for analysis'}

    def _analyze_dict(self, data: Dict) -> Dict[str, Any]:
        """分析字典数据"""
        numeric_fields = {k: v for k, v in data.items() if isinstance(v, (int, float))}

        analysis = {
            'total_fields': len(data),
            'numeric_fields': list(numeric_fields.keys()),
            'summary': {}
        }

        if numeric_fields:
            for field, value in numeric_fields.items():
                analysis['summary'][field] = {
                    'value': value,
                    'type': 'numeric'
                }

        return analysis

    def _analyze_list(self, data: List) -> Dict[str, Any]:
        """分析列表数据"""
        if not data:
            return {'count': 0, 'summary': 'Empty list'}

        numeric_items = [item for item in data if isinstance(item, (int, float))]
        dict_items = [item for item in data if isinstance(item, dict)]

        analysis = {
            'count': len(data),
            'numeric_count': len(numeric_items),
            'dict_items_count': len(dict_items)
        }

        if numeric_items:
            analysis['numeric_summary'] = {
                'min': min(numeric_items),
                'max': max(numeric_items),
                'avg': sum(numeric_items) / len(numeric_items)
            }

        return analysis

    def calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """计算统计指标"""
        if not data:
            return {}

        sorted_data = sorted(data)
        n = len(data)

        return {
            'count': n,
            'sum': sum(data),
            'mean': sum(data) / n,
            'min': min(data),
            'max': max(data),
            'median': sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        }
