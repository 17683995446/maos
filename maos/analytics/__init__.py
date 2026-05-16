"""
MAOS v14.0 - Advanced Analytics Module
"""
from maos.analytics.v14 import (
    AnalyticsEngine,
    VisualizationGenerator,
    Dashboard,
    DashboardWidget,
    ChartType,
    TimeRange,
    MetricSummary,
    AnalyticsReport,
)

_global_analytics_engine = None

def get_analytics_engine() -> AnalyticsEngine:
    """Get global analytics engine instance"""
    global _global_analytics_engine
    if _global_analytics_engine is None:
        _global_analytics_engine = AnalyticsEngine()
    return _global_analytics_engine

class CostAttributionEngine:
    """Cost attribution engine stub for backward compatibility"""
    pass

__all__ = [
    "AnalyticsEngine",
    "VisualizationGenerator",
    "Dashboard",
    "DashboardWidget",
    "ChartType",
    "TimeRange",
    "MetricSummary",
    "AnalyticsReport",
    "get_analytics_engine",
    "CostAttributionEngine",
]
