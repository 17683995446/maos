"""
Example Agents - 演示如何使用多Agent编排系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_agent import DataProcessingAgent
from analysis_agent import AnalysisAgent
from reporting_agent import ReportingAgent
from demo import run_demo

__all__ = [
    'DataProcessingAgent',
    'AnalysisAgent',
    'ReportingAgent',
    'run_demo'
]
