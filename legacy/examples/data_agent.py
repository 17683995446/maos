"""
Data Processing Agent - 数据处理Agent示例
负责数据清洗、转换和预处理
"""

from typing import Any, Dict, List
from agent import Agent, AgentMessage, AgentStatus, MessageType


class DataProcessingAgent(Agent):
    """数据处理Agent"""

    def __init__(self, name: str = "data_processor"):
        super().__init__(
            name=name,
            capabilities=['data_cleaning', 'data_transformation', 'data_validation']
        )
        self.processed_count = 0

    def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理数据处理请求"""
        if message.msg_type == MessageType.REQUEST:
            content = message.content
            input_data = content.get('input', {})

            result = self._process_data(input_data)

            self.processed_count += 1

            return AgentMessage(
                sender=self.name,
                receivers=[message.sender],
                msg_type=MessageType.RESPONSE,
                content={
                    'status': 'success',
                    'processed_data': result,
                    'records_processed': len(result) if isinstance(result, list) else 1
                },
                reply_to=message.id,
                metadata={'agent': self.name, 'task_type': 'data_processing'}
            )

        return super().process_message(message)

    def _process_data(self, data: Any) -> Any:
        """执行数据处理逻辑"""
        if isinstance(data, dict):
            return self._clean_dict_data(data)
        elif isinstance(data, list):
            valid_records = [item for item in data if isinstance(item, dict) and self._is_valid_record(item)]
            return [self._clean_dict_data(item) for item in valid_records]
        return data

    def _clean_dict_data(self, data: Dict) -> Dict:
        """清洗字典数据"""
        cleaned = {}
        for key, value in data.items():
            if value is not None and value != '':
                cleaned[key] = value
        return cleaned

    def _is_valid_record(self, record: Dict) -> bool:
        """检查记录是否有效"""
        if not isinstance(record, dict):
            return False
        name = record.get('name')
        return name and name != ''

    def validate_data(self, data: Dict, schema: Dict) -> Dict[str, Any]:
        """验证数据是否符合schema"""
        errors = []
        for field, rules in schema.items():
            if rules.get('required') and field not in data:
                errors.append(f"Missing required field: {field}")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
