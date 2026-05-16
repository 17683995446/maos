"""
MAOS v14.0 - Advanced Analytics & Visualization Dashboard
高级分析与可视化仪表盘
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid


class ChartType(Enum):
    """图表类型"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    TABLE = "table"
    GAUGE = "gauge"
    HEATMAP = "heatmap"


class TimeRange(Enum):
    """时间范围"""
    LAST_HOUR = "last_hour"
    LAST_24_HOURS = "last_24_hours"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CUSTOM = "custom"


@dataclass
class ChartDataPoint:
    """图表数据点"""
    timestamp: datetime
    value: float
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartConfig:
    """图表配置"""
    title: str = ""
    type: ChartType = ChartType.LINE
    x_label: str = ""
    y_label: str = ""
    colors: List[str] = field(default_factory=lambda: ["#667eea", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"])
    show_legend: bool = True
    stacked: bool = False
    smooth: bool = True


@dataclass
class DashboardWidget:
    """仪表盘组件"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    chart_type: ChartType = ChartType.LINE
    config: ChartConfig = field(default_factory=ChartConfig)
    data: List[ChartDataPoint] = field(default_factory=list)
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0, "width": 4, "height": 3})


@dataclass
class Dashboard:
    """仪表盘"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    widgets: List[DashboardWidget] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MetricSummary:
    """指标摘要"""
    name: str
    value: float
    unit: str = ""
    change: float = 0.0
    change_percent: float = 0.0
    trend: str = "stable"  # "up", "down", "stable"


@dataclass
class AnalyticsReport:
    """分析报告"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    period: str = ""
    summary: str = ""
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: List[MetricSummary] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class AnalyticsEngine:
    """分析引擎"""
    
    def __init__(self):
        self._dashboards: Dict[str, Dashboard] = {}
        self._metrics_store: Dict[str, List[ChartDataPoint]] = {}
    
    def record_metric(self, name: str, value: float, timestamp: datetime = None, metadata: Dict[str, Any] = None) -> None:
        """记录指标"""
        if name not in self._metrics_store:
            self._metrics_store[name] = []
        
        self._metrics_store[name].append(ChartDataPoint(
            timestamp=timestamp or datetime.now(),
            value=value,
            metadata=metadata or {}
        ))
        
        # 保留最近10000条记录
        if len(self._metrics_store[name]) > 10000:
            self._metrics_store[name] = self._metrics_store[name][-10000:]
    
    def get_metric_data(self, name: str, time_range: TimeRange = TimeRange.LAST_24_HOURS,
                       start_time: datetime = None, end_time: datetime = None) -> List[ChartDataPoint]:
        """获取指标数据"""
        data = self._metrics_store.get(name, [])
        
        now = datetime.now()
        if time_range == TimeRange.LAST_HOUR:
            start = now - timedelta(hours=1)
        elif time_range == TimeRange.LAST_24_HOURS:
            start = now - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7_DAYS:
            start = now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            start = now - timedelta(days=30)
        elif time_range == TimeRange.CUSTOM and start_time:
            start = start_time
            end = end_time or now
        else:
            start = now - timedelta(hours=24)
        
        end = end_time if end_time else now
        return [d for d in data if start <= d.timestamp <= end]
    
    def get_all_metrics(self) -> Dict[str, List[ChartDataPoint]]:
        """获取所有指标"""
        return self._metrics_store
    
    def calculate_summary(self, name: str, time_range: TimeRange = TimeRange.LAST_24_HOURS) -> MetricSummary:
        """计算指标摘要"""
        data = self.get_metric_data(name, time_range)
        if not data:
            return MetricSummary(name=name, value=0.0)
        
        values = [d.value for d in data]
        current_value = values[-1]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)
        
        # 计算变化
        if len(values) >= 2:
            previous_value = values[0] if len(values) == 2 else values[int(len(values) * 0.1)]
            change = current_value - previous_value
            change_percent = (change / previous_value) * 100 if previous_value != 0 else 0
            trend = "up" if change_percent > 5 else "down" if change_percent < -5 else "stable"
        else:
            change = 0
            change_percent = 0
            trend = "stable"
        
        return MetricSummary(
            name=name,
            value=round(current_value, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            trend=trend
        )
    
    def create_dashboard(self, name: str, description: str = "") -> Dashboard:
        """创建仪表盘"""
        dashboard = Dashboard(name=name, description=description)
        self._dashboards[dashboard.id] = dashboard
        return dashboard
    
    def add_widget(self, dashboard_id: str, name: str, chart_type: ChartType, 
                  metric_name: str, position: Dict[str, int] = None) -> DashboardWidget:
        """添加组件到仪表盘"""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        config = ChartConfig(title=name)
        data = self.get_metric_data(metric_name)
        
        widget = DashboardWidget(
            name=name,
            chart_type=chart_type,
            config=config,
            data=data,
            position=position or {"x": len(dashboard.widgets) * 4, "y": 0, "width": 4, "height": 3}
        )
        
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now()
        return widget
    
    def generate_report(self, title: str, period: str = "last_24_hours") -> AnalyticsReport:
        """生成分析报告"""
        metrics = [
            self.calculate_summary("executions", TimeRange.LAST_24_HOURS),
            self.calculate_summary("errors", TimeRange.LAST_24_HOURS),
            self.calculate_summary("latency_ms", TimeRange.LAST_24_HOURS),
            self.calculate_summary("throughput", TimeRange.LAST_24_HOURS),
            self.calculate_summary("cost_usd", TimeRange.LAST_24_HOURS),
        ]
        
        insights = []
        recommendations = []
        
        for metric in metrics:
            if metric.name == "errors" and metric.value > 100:
                insights.append(f"高错误率检测: {metric.value} 错误")
                recommendations.append("建议检查工作流配置和Agent状态")
            if metric.name == "latency_ms" and metric.value > 500:
                insights.append(f"高延迟检测: {metric.value}ms")
                recommendations.append("建议优化工作流步骤或增加资源")
            if metric.name == "cost_usd" and metric.change_percent > 20:
                insights.append(f"成本增长: +{metric.change_percent}%")
                recommendations.append("建议审查工作流执行和资源配置")
        
        summary = f"报告周期: {period}\n"
        summary += f"总执行次数: {metrics[0].value}\n"
        summary += f"错误率: {metrics[1].value}次\n"
        summary += f"平均延迟: {metrics[2].value}ms\n"
        summary += f"吞吐量: {metrics[3].value}/min\n"
        summary += f"成本: ${metrics[4].value:.2f}"
        
        return AnalyticsReport(
            title=title,
            period=period,
            summary=summary,
            insights=insights,
            recommendations=recommendations,
            metrics=metrics
        )


class VisualizationGenerator:
    """可视化生成器"""
    
    @staticmethod
    def generate_chart_html(widget: DashboardWidget) -> str:
        """生成图表HTML"""
        config = widget.config
        
        if widget.chart_type == ChartType.LINE:
            return VisualizationGenerator._generate_line_chart(widget)
        elif widget.chart_type == ChartType.BAR:
            return VisualizationGenerator._generate_bar_chart(widget)
        elif widget.chart_type == ChartType.PIE:
            return VisualizationGenerator._generate_pie_chart(widget)
        elif widget.chart_type == ChartType.GAUGE:
            return VisualizationGenerator._generate_gauge_chart(widget)
        else:
            return f"<div>{widget.name}: {len(widget.data)} data points</div>"
    
    @staticmethod
    def _generate_line_chart(widget: DashboardWidget) -> str:
        """生成折线图"""
        data_points = ",".join([f"[{int(d.timestamp.timestamp() * 1000)}, {d.value}]" for d in widget.data])
        
        return f"""
<div class="chart-container">
  <h3>{widget.config.title}</h3>
  <canvas id="chart-{widget.id}"></canvas>
  <script>
    new Chart(document.getElementById('chart-{widget.id}'), {{
      type: 'line',
      data: {{
        datasets: [{{
          label: '{widget.name}',
          data: [{data_points}],
          borderColor: '{widget.config.colors[0]}',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: {1 if widget.config.smooth else 0},
          fill: {str(widget.config.stacked).lower()}
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: {str(widget.config.show_legend).lower()} }} }}
      }}
    }});
  </script>
</div>
"""
    
    @staticmethod
    def _generate_bar_chart(widget: DashboardWidget) -> str:
        """生成柱状图"""
        labels = ",".join([f"'{d.label or d.timestamp.strftime('%H:%M')}'" for d in widget.data])
        values = ",".join([str(d.value) for d in widget.data])
        
        return f"""
<div class="chart-container">
  <h3>{widget.config.title}</h3>
  <canvas id="chart-{widget.id}"></canvas>
  <script>
    new Chart(document.getElementById('chart-{widget.id}'), {{
      type: 'bar',
      data: {{
        labels: [{labels}],
        datasets: [{{
          label: '{widget.name}',
          data: [{values}],
          backgroundColor: '{widget.config.colors[0]}',
          borderColor: '{widget.config.colors[0]}',
          borderWidth: 1
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: {str(widget.config.show_legend).lower()} }} }}
      }}
    }});
  </script>
</div>
"""
    
    @staticmethod
    def _generate_pie_chart(widget: DashboardWidget) -> str:
        """生成饼图"""
        labels = ",".join([f"'{d.label}'" for d in widget.data])
        values = ",".join([str(d.value) for d in widget.data])
        colors = ",".join([f"'{c}'" for c in widget.config.colors[:len(widget.data)]])
        
        return f"""
<div class="chart-container">
  <h3>{widget.config.title}</h3>
  <canvas id="chart-{widget.id}"></canvas>
  <script>
    new Chart(document.getElementById('chart-{widget.id}'), {{
      type: 'pie',
      data: {{
        labels: [{labels}],
        datasets: [{{
          data: [{values}],
          backgroundColor: [{colors}]
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: {str(widget.config.show_legend).lower()} }} }}
      }}
    }});
  </script>
</div>
"""
    
    @staticmethod
    def _generate_gauge_chart(widget: DashboardWidget) -> str:
        """生成仪表盘"""
        value = widget.data[-1].value if widget.data else 0
        max_value = max([d.value for d in widget.data]) if widget.data else 100
        
        return f"""
<div class="gauge-container">
  <h3>{widget.config.title}</h3>
  <div class="gauge" style="width: 200px; height: 200px;">
    <svg viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" stroke-width="10"/>
      <circle cx="50" cy="50" r="40" fill="none" stroke="{widget.config.colors[0]}" 
              stroke-width="10" stroke-dasharray="{2 * 3.14159 * 40}" 
              stroke-dashoffset="{2 * 3.14159 * 40 * (1 - {value / max_value})}"
              transform="rotate(-90 50 50)"/>
      <text x="50" y="55" text-anchor="middle" font-size="20">{round(value, 1)}</text>
    </svg>
  </div>
</div>
"""
    
    @staticmethod
    def generate_dashboard_html(dashboard: Dashboard) -> str:
        """生成仪表盘HTML"""
        widgets_html = "\n".join([VisualizationGenerator.generate_chart_html(w) for w in dashboard.widgets])
        
        return f"""
<!DOCTYPE html>
<html>
<head>
  <title>{dashboard.name}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    .dashboard {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; padding: 20px; }}
    .chart-container {{ padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  </style>
</head>
<body>
  <h1>{dashboard.name}</h1>
  <div class="dashboard">{widgets_html}</div>
</body>
</html>
"""
