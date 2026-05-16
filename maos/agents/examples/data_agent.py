"""
Data Processing Agent - 数据处理Agent示例
负责数据清洗、转换和预处理

功能特性：
- 数据清洗：移除空值、格式化数据
- 数据转换：类型转换、格式标准化
- 数据验证：Schema验证、规则检查
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, AsyncIterable

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


class DataProcessingAgent(Agent):
    """
    数据处理Agent

    负责对输入数据进行清洗、转换和验证处理。
    支持多种数据类型，包括字典和列表。

    能力：
        - data_cleaning: 数据清洗
        - data_transformation: 数据转换
        - data_validation: 数据验证
    """

    def __init__(
        self,
        options: AgentOptions,
        callbacks: Optional[AgentCallbacks] = None
    ):
        """
        初始化DataProcessingAgent

        参数：
            options: Agent配置选项
            callbacks: 可选的回调处理器
        """
        if callbacks:
            options.callbacks = callbacks
        super().__init__(options)
        self.processed_count = 0
        self._initialize_processing_stats()

    def _initialize_processing_stats(self) -> None:
        """初始化处理统计信息"""
        self.stats = {
            'total_processed': 0,
            'successful_cleaning': 0,
            'failed_validation': 0,
            'transformations_applied': 0,
        }

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
            input_text: 用户输入文本（可以是JSON字符串或描述）
            user_id: 用户标识
            session_id: 会话标识
            chat_history: 对话历史
            additional_params: 附加参数

        返回：
            处理结果描述
        """
        self.processed_count += 1

        try:
            import json
            if additional_params and 'data' in additional_params:
                data = additional_params['data']
            elif input_text.startswith('{'):
                data = json.loads(input_text)
            else:
                data = {'raw_input': input_text}

            processed = self._process_data(data)

            return f"数据处理完成: 处理了 {len(processed) if isinstance(processed, list) else 1} 条记录"

        except Exception as e:
            return f"数据处理失败: {str(e)}"

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
            input_data = self._extract_input_data(content)

            if not input_data:
                return message.create_response(
                    content={'status': 'error', 'message': '未提供输入数据'},
                    metadata={'error': 'no_data'}
                )

            result = self._process_data(input_data)
            self.processed_count += 1

            return message.create_response(
                content={
                    'status': 'success',
                    'processed_data': result,
                    'records_processed': self._count_records(result),
                    'processing_metadata': {
                        'agent': self.name,
                        'records_count': self._count_records(result),
                        'processed_at': self._get_timestamp()
                    }
                },
                metadata={
                    'agent': self.name,
                    'task_type': 'data_processing',
                    'records_processed': self._count_records(result)
                }
            )

        except Exception as e:
            self.log_error(f"数据处理错误: {str(e)}")
            return message.create_response(
                content={'status': 'error', 'message': f'处理错误: {str(e)}'},
                metadata={'error': str(e)}
            )

    def _extract_input_data(self, content: Any) -> Any:
        """
        从消息内容中提取输入数据

        参数：
            content: 消息内容

        返回：
            提取的数据
        """
        if isinstance(content, dict):
            return content.get('input', content.get('data', content))
        elif isinstance(content, str):
            try:
                import json
                return json.loads(content)
            except json.JSONDecodeError:
                return {'raw_data': content}
        return content

    def _process_data(self, data: Any) -> Any:
        """
        执行数据处理逻辑

        参数：
            data: 输入数据

        返回：
            处理后的数据
        """
        if isinstance(data, dict):
            return self._clean_dict_data(data)
        elif isinstance(data, list):
            valid_records = [
                item for item in data
                if isinstance(item, dict) and self._is_valid_record(item)
            ]
            return [self._clean_dict_data(item) for item in valid_records]
        return data

    def _clean_dict_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗字典数据

        参数：
            data: 输入字典

        返回：
            清洗后的字典
        """
        cleaned = {}
        for key, value in data.items():
            if value is not None and value != '':
                if isinstance(value, str):
                    value = value.strip()
                    if value:
                        cleaned[key] = value
                else:
                    cleaned[key] = value
        return cleaned

    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """
        检查记录是否有效

        参数：
            record: 待检查的记录

        返回：
            是否有效
        """
        if not isinstance(record, dict):
            return False

        required_fields = ['name', 'id']
        for field in required_fields:
            if field not in record or not record[field]:
                return False

        return True

    def _count_records(self, data: Any) -> int:
        """
        统计记录数量

        参数：
            data: 数据对象

        返回：
            记录数量
        """
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        return 0

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳

        返回：
            ISO格式的时间字符串
        """
        from datetime import datetime
        return datetime.now().isoformat()

    def validate_data(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证数据是否符合schema定义

        参数：
            data: 待验证的数据
            schema: 数据schema定义

        返回：
            验证结果，包含valid和errors字段
        """
        errors = []

        for field, rules in schema.items():
            if rules.get('required', False) and field not in data:
                errors.append(f"缺少必需字段: {field}")

            if field in data:
                value = data[field]
                expected_type = rules.get('type')

                if expected_type and not self._check_type(value, expected_type):
                    errors.append(
                        f"字段 {field} 类型错误: 期望 {expected_type}, "
                        f"实际 {type(value).__name__}"
                    )

                min_value = rules.get('min')
                max_value = rules.get('max')
                if isinstance(value, (int, float)):
                    if min_value is not None and value < min_value:
                        errors.append(f"字段 {field} 值过小: {value} < {min_value}")
                    if max_value is not None and value > max_value:
                        errors.append(f"字段 {field} 值过大: {value} > {max_value}")

                if isinstance(value, str):
                    min_length = rules.get('min_length')
                    max_length = rules.get('max_length')
                    if min_length and len(value) < min_length:
                        errors.append(
                            f"字段 {field} 长度过短: {len(value)} < {min_length}"
                        )
                    if max_length and len(value) > max_length:
                        errors.append(
                            f"字段 {field} 长度过长: {len(value)} > {max_length}"
                        )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'validated_fields': len(schema),
            'missing_fields': [
                f for f in schema.keys()
                if f not in data
            ]
        }

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        检查值类型

        参数：
            value: 待检查的值
            expected_type: 期望的类型名称

        返回：
            是否匹配
        """
        type_mapping = {
            'string': str,
            'int': int,
            'float': (int, float),
            'bool': bool,
            'list': list,
            'dict': dict,
        }

        expected = type_mapping.get(expected_type.lower())
        if expected is None:
            return True

        return isinstance(value, expected)

    def transform_data(
        self,
        data: Dict[str, Any],
        transformation_rules: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        应用数据转换规则

        参数：
            data: 输入数据
            transformation_rules: 转换规则，格式为 {目标字段: 源字段或表达式}

        返回：
            转换后的数据
        """
        transformed = data.copy()

        for target_field, rule in transformation_rules.items():
            if '.' in rule:
                source_field = rule.split('.')[0]
                if source_field in data:
                    value = data[source_field]
                    parts = rule.split('.')
                    for part in parts[1:]:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                    transformed[target_field] = value
            elif rule in data:
                transformed[target_field] = data[rule]

        return transformed

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息

        返回：
            统计信息字典
        """
        return {
            **self.stats,
            'current_session_processed': self.processed_count
        }

    async def stream_process_data(
        self,
        data: List[Dict[str, Any]]
    ) -> AsyncIterable[AgentStreamResponse]:
        """
        流式处理数据

        参数：
            data: 数据列表

        生成：
            AgentStreamResponse: 处理进度和结果
        """
        total = len(data)
        processed = 0

        for item in data:
            if isinstance(item, dict) and self._is_valid_record(item):
                cleaned_item = self._clean_dict_data(item)
                processed += 1

                yield AgentStreamResponse(
                    text=f"处理记录 {processed}/{total}",
                    final_message=None
                )

                await asyncio.sleep(0.01)
            else:
                yield AgentStreamResponse(
                    text=f"跳过无效记录",
                    final_message=None
                )

        yield AgentStreamResponse(
            text="",
            final_message=f"处理完成: {processed}/{total} 条记录"
        )
