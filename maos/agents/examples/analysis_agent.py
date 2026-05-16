"""
Analysis Agent - 分析Agent示例
负责数据分析、统计计算和模式识别

功能特性：
- 基础数据分析：字段类型、分布统计
- 统计分析：均值、中位数、最大值、最小值等
- 模式识别：数据模式检测和分类
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


class AnalysisAgent(Agent):
    """
    数据分析Agent

    负责对输入数据进行深入分析和统计计算。
    支持多种数据类型的分析，包括数值、文本和结构化数据。

    能力：
        - data_analysis: 基础数据分析
        - statistical_analysis: 统计分析
        - pattern_recognition: 模式识别
    """

    def __init__(
        self,
        options: AgentOptions,
        callbacks: Optional[AgentCallbacks] = None
    ):
        """
        初始化AnalysisAgent

        参数：
            options: Agent配置选项
            callbacks: 可选的回调处理器
        """
        if callbacks:
            options.callbacks = callbacks
        super().__init__(options)
        self.analysis_count = 0
        self._initialize_analysis_cache()

    def _initialize_analysis_cache(self) -> None:
        """初始化分析缓存"""
        self.analysis_cache: Dict[str, Any] = {}
        self.stats = {
            'total_analyses': 0,
            'numeric_analyses': 0,
            'pattern_detections': 0,
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
            input_text: 用户输入文本
            user_id: 用户标识
            session_id: 会话标识
            chat_history: 对话历史
            additional_params: 附加参数

        返回：
            分析结果描述
        """
        self.analysis_count += 1

        try:
            import json
            if additional_params and 'data' in additional_params:
                data = additional_params['data']
            elif input_text.startswith('{') or input_text.startswith('['):
                data = json.loads(input_text)
            else:
                data = {'text': input_text}

            analysis_result = self._analyze_data(data)

            return f"分析完成: 发现 {len(analysis_result)} 个分析维度"

        except Exception as e:
            return f"分析失败: {str(e)}"

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
            data = self._extract_data(content)

            if not data:
                return message.create_response(
                    content={'status': 'error', 'message': '未提供分析数据'},
                    metadata={'error': 'no_data'}
                )

            analysis_result = self._analyze_data(data)
            self.analysis_count += 1

            return message.create_response(
                content={
                    'status': 'success',
                    'analysis': analysis_result,
                    'analysis_metadata': {
                        'agent': self.name,
                        'data_type': type(data).__name__,
                        'analyzed_at': self._get_timestamp()
                    }
                },
                metadata={
                    'agent': self.name,
                    'task_type': 'analysis',
                    'analysis_type': analysis_result.get('analysis_type', 'general')
                }
            )

        except Exception as e:
            self.log_error(f"分析错误: {str(e)}")
            return message.create_response(
                content={'status': 'error', 'message': f'分析错误: {str(e)}'},
                metadata={'error': str(e)}
            )

    def _extract_data(self, content: Any) -> Any:
        """
        从消息内容中提取数据

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
                return {'text': content}
        return content

    def _analyze_data(self, data: Any) -> Dict[str, Any]:
        """
        执行数据分析

        参数：
            data: 输入数据

        返回：
            分析结果字典
        """
        if isinstance(data, dict):
            return self._analyze_dict(data)
        elif isinstance(data, list):
            return self._analyze_list(data)
        elif isinstance(data, (int, float)):
            return self._analyze_numeric(data)
        elif isinstance(data, str):
            return self._analyze_text(data)
        else:
            return {
                'analysis_type': 'unknown',
                'summary': f'不支持的数据类型: {type(data).__name__}'
            }

    def _analyze_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析字典数据

        参数：
            data: 输入字典

        返回：
            分析结果
        """
        numeric_fields = {
            k: v for k, v in data.items()
            if isinstance(v, (int, float))
        }

        string_fields = {
            k: v for k, v in data.items()
            if isinstance(v, str)
        }

        analysis = {
            'analysis_type': 'dict',
            'total_fields': len(data),
            'field_types': {
                'numeric': list(numeric_fields.keys()),
                'string': list(string_fields.keys()),
                'other': [
                    k for k in data.keys()
                    if k not in numeric_fields and k not in string_fields
                ]
            },
            'summary': {}
        }

        if numeric_fields:
            analysis['numeric_summary'] = self._summarize_numeric_fields(numeric_fields)

        if string_fields:
            analysis['string_summary'] = self._summarize_string_fields(string_fields)

        pattern_result = self._detect_patterns(data)
        analysis['patterns_detected'] = pattern_result

        return analysis

    def _analyze_list(self, data: List[Any]) -> Dict[str, Any]:
        """
        分析列表数据

        参数：
            data: 输入列表

        返回：
            分析结果
        """
        if not data:
            return {
                'analysis_type': 'list',
                'count': 0,
                'summary': '空列表'
            }

        numeric_items = [item for item in data if isinstance(item, (int, float))]
        dict_items = [item for item in data if isinstance(item, dict)]
        string_items = [item for item in data if isinstance(item, str)]

        analysis = {
            'analysis_type': 'list',
            'count': len(data),
            'item_types': {
                'numeric': len(numeric_items),
                'dict': len(dict_items),
                'string': len(string_items),
                'other': len(data) - len(numeric_items) - len(dict_items) - len(string_items)
            }
        }

        if numeric_items:
            analysis['numeric_summary'] = {
                'min': min(numeric_items),
                'max': max(numeric_items),
                'avg': sum(numeric_items) / len(numeric_items),
                'count': len(numeric_items)
            }
            self.stats['numeric_analyses'] += 1

        if dict_items:
            analysis['dict_summary'] = self._analyze_dict_items(dict_items)

        pattern_result = self._detect_list_patterns(data)
        analysis['patterns_detected'] = pattern_result

        return analysis

    def _analyze_numeric(self, value: float) -> Dict[str, Any]:
        """
        分析数值数据

        参数：
            value: 数值

        返回：
            分析结果
        """
        return {
            'analysis_type': 'numeric',
            'value': value,
            'is_integer': isinstance(value, int),
            'category': self._categorize_numeric(value)
        }

    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """
        分析文本数据

        参数：
            text: 文本内容

        返回：
            分析结果
        """
        words = text.split()
        return {
            'analysis_type': 'text',
            'length': len(text),
            'word_count': len(words),
            'char_distribution': self._analyze_char_distribution(text),
            'patterns': self._detect_text_patterns(text)
        }

    def _summarize_numeric_fields(
        self,
        numeric_fields: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        汇总数值字段

        参数：
            numeric_fields: 数值字段字典

        返回：
            汇总结果
        """
        summary = {}
        for field, value in numeric_fields.items():
            summary[field] = {
                'value': value,
                'type': 'integer' if isinstance(value, int) else 'float',
                'category': self._categorize_numeric(value)
            }
        return summary

    def _summarize_string_fields(
        self,
        string_fields: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        汇总字符串字段

        参数：
            string_fields: 字符串字段字典

        返回：
            汇总结果
        """
        summary = {}
        for field, value in string_fields.items():
            summary[field] = {
                'length': len(value),
                'preview': value[:50] + '...' if len(value) > 50 else value
            }
        return summary

    def _categorize_numeric(self, value: float) -> str:
        """
        数值分类

        参数：
            value: 数值

        返回：
            分类标签
        """
        if value < 0:
            return 'negative'
        elif value == 0:
            return 'zero'
        elif value < 100:
            return 'small'
        elif value < 10000:
            return 'medium'
        else:
            return 'large'

    def _analyze_dict_items(
        self,
        dict_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析字典项列表

        参数：
            dict_items: 字典项列表

        返回：
            分析结果
        """
        if not dict_items:
            return {'count': 0}

        all_keys = set()
        for item in dict_items:
            all_keys.update(item.keys())

        return {
            'count': len(dict_items),
            'unique_keys': list(all_keys),
            'key_frequency': self._calculate_key_frequency(dict_items)
        }

    def _calculate_key_frequency(
        self,
        dict_items: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        计算键频率

        参数：
            dict_items: 字典项列表

        返回：
            键频率字典
        """
        frequency = {}
        for item in dict_items:
            for key in item.keys():
                frequency[key] = frequency.get(key, 0) + 1
        return frequency

    def _detect_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测数据模式

        参数：
            data: 输入数据

        返回：
            检测到的模式
        """
        patterns = {
            'has_id_field': any('id' in k.lower() for k in data.keys()),
            'has_name_field': any('name' in k.lower() for k in data.keys()),
            'has_timestamp': any('time' in k.lower() or 'date' in k.lower()
                                 for k in data.keys()),
            'is_empty': len(data) == 0
        }

        numeric_count = sum(1 for v in data.values() if isinstance(v, (int, float)))
        patterns['numeric_heavy'] = numeric_count > len(data) / 2

        self.stats['pattern_detections'] += 1
        return patterns

    def _detect_list_patterns(self, data: List[Any]) -> Dict[str, Any]:
        """
        检测列表数据模式

        参数：
            data: 列表数据

        返回：
            检测到的模式
        """
        patterns = {
            'is_empty': len(data) == 0,
            'is_homogeneous': len(set(type(item).__name__ for item in data)) == 1,
            'has_duplicates': len(data) != len(set(str(item) for item in data))
        }

        if data and isinstance(data[0], dict):
            patterns['all_dicts'] = True

        return patterns

    def _detect_text_patterns(self, text: str) -> Dict[str, Any]:
        """
        检测文本模式

        参数：
            text: 文本内容

        返回：
            检测到的模式
        """
        import re

        return {
            'has_uppercase': any(c.isupper() for c in text),
            'has_digits': any(c.isdigit() for c in text),
            'has_special_chars': bool(re.search(r'[^a-zA-Z0-9\s]', text)),
            'is_email_like': bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text)),
            'is_url_like': text.startswith(('http://', 'https://', 'www.'))
        }

    def _analyze_char_distribution(self, text: str) -> Dict[str, int]:
        """
        分析字符分布

        参数：
            text: 文本内容

        返回：
            字符分布统计
        """
        return {
            'letters': sum(1 for c in text if c.isalpha()),
            'digits': sum(1 for c in text if c.isdigit()),
            'spaces': sum(1 for c in text if c.isspace()),
            'special': sum(1 for c in text if not c.isalnum() and not c.isspace())
        }

    def _get_timestamp(self) -> str:
        """
        获取当前时间戳

        返回：
            ISO格式的时间字符串
        """
        from datetime import datetime
        return datetime.now().isoformat()

    def calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """
        计算数值列表的统计指标

        参数：
            data: 数值列表

        返回：
            统计指标字典
        """
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
            'median': sorted_data[n // 2] if n % 2 == 1
                      else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        }

    def get_analysis_stats(self) -> Dict[str, Any]:
        """
        获取分析统计信息

        返回：
            统计信息字典
        """
        return {
            **self.stats,
            'current_session_analyses': self.analysis_count,
            'cache_size': len(self.analysis_cache)
        }

    async def stream_analysis(
        self,
        data: Any
    ) -> AsyncIterable[AgentStreamResponse]:
        """
        流式数据分析

        参数：
            data: 输入数据

        生成：
            AgentStreamResponse: 分析进度和结果
        """
        yield AgentStreamResponse(
            text="开始分析...",
            final_message=None
        )

        if isinstance(data, list):
            total = len(data)
            for i, item in enumerate(data):
                yield AgentStreamResponse(
                    text=f"分析项目 {i + 1}/{total}",
                    final_message=None
                )
                await asyncio.sleep(0.01)

        analysis_result = self._analyze_data(data)

        yield AgentStreamResponse(
            text="",
            final_message=f"分析完成: {analysis_result.get('analysis_type', 'unknown')}类型"
        )
