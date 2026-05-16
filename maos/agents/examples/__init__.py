"""
MAOS Agents Examples
MAOS系统示例Agent模块

本模块包含三个主要的示例Agent：
- DataProcessingAgent: 数据处理Agent，负责数据清洗、转换和验证
- AnalysisAgent: 分析Agent，负责数据分析和统计计算
- ReportingAgent: 报告生成Agent，负责生成各种格式的报告

使用示例：
    from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent

    data_agent = DataProcessingAgent(AgentOptions(
        name="DataProcessor",
        description="数据处理器",
        capabilities=["data_cleaning", "data_transformation", "data_validation"]
    ))
"""

from maos.agents.examples.data_agent import DataProcessingAgent
from maos.agents.examples.analysis_agent import AnalysisAgent
from maos.agents.examples.reporting_agent import ReportingAgent

__all__ = [
    'DataProcessingAgent',
    'AnalysisAgent',
    'ReportingAgent',
]
