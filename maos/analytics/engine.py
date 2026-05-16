"""
Analytics Engine Module
======================

Provides comprehensive analytics, reporting, and business intelligence capabilities.

Key Features:
  - Real-time metrics collection and storage
  - Time series analysis
  - Anomaly detection using Z-score method
  - Custom alert conditions
  - Report generation
  - Cost attribution engine for multi-tenant billing
  - Decorator for automatic metric recording

The module is designed to be lightweight and suitable for both
synchronous and asynchronous applications.
"""

from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics
import logging
import uuid

logger = logging.getLogger(__name__)


class MetricAggregation(Enum):
    """Available metric aggregation types"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    PERCENTILE_50 = "p50"
    PERCENTILE_75 = "p75"
    PERCENTILE_90 = "p90"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


class ReportFormat(Enum):
    """Supported report formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    TXT = "txt"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """Single metric data point with timestamp"""
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimeSeriesData:
    """Time series data for charts and analysis"""
    metric_name: str
    data_points: List[MetricValue] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def get_timestamps(self) -> List[datetime]:
        """Get all timestamps in order"""
        return [dp.timestamp for dp in self.data_points]
    
    def get_values(self) -> List[float]:
        """Get all values in order"""
        return [dp.value for dp in self.data_points]
    
    def compute_aggregations(self) -> Dict[MetricAggregation, float]:
        """Compute all aggregations on data points"""
        if not self.data_points:
            return {}
        
        values = self.get_values()
        
        result: Dict[MetricAggregation, float] = {
            MetricAggregation.COUNT: float(len(values)),
            MetricAggregation.SUM: sum(values),
            MetricAggregation.AVG: statistics.mean(values),
            MetricAggregation.MIN: min(values),
            MetricAggregation.MAX: max(values)
        }
        
        sorted_vals = sorted(values)
        if len(sorted_vals) >= 2:
            for pct, enum_val in [
                (50, MetricAggregation.PERCENTILE_50),
                (75, MetricAggregation.PERCENTILE_75),
                (90, MetricAggregation.PERCENTILE_90),
                (95, MetricAggregation.PERCENTILE_95),
                (99, MetricAggregation.PERCENTILE_99)
            ]:
                idx = int(len(sorted_vals) * pct / 100)
                result[enum_val] = sorted_vals[min(idx, len(sorted_vals)-1)]
        
        return result
    
    def get_trend(self) -> str:
        """Calculate simple trend direction"""
        if len(self.data_points) < 2:
            return "insufficient_data"
        
        values = self.get_values()
        if len(values) >= 2:
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            avg_first = statistics.mean(first_half)
            avg_second = statistics.mean(second_half)
            
            if avg_second > avg_first * 1.1:
                return "increasing"
            elif avg_second < avg_first * 0.9:
                return "decreasing"
            return "stable"
        return "stable"


@dataclass
class Alert:
    """Analytics alert"""
    alert_id: str
    severity: AlertSeverity
    message: str
    condition_name: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    
    def acknowledge(self) -> None:
        """Acknowledge this alert"""
        self.acknowledged = True
        logger.info(f"Alert acknowledged: {self.alert_id}")


@dataclass
class ReportDefinition:
    """Configuration for report generation"""
    report_id: str
    report_name: str
    description: str
    metrics: List[str] = field(default_factory=list)
    time_range_hours: int = 24
    aggregation_levels: List[MetricAggregation] = field(default_factory=list)
    format: ReportFormat = ReportFormat.JSON
    scheduled_cron: Optional[str] = None
    recipients: List[str] = field(default_factory=list)
    enabled: bool = True


class AnalyticsEngine:
    """
    Core analytics engine with comprehensive capabilities.
    
    Features:
      - Metric collection and storage
      - Time series analysis
      - Anomaly detection
      - Trend forecasting
      - Custom metrics via decorators
      - Alert management
      - Report generation
    """
    
    def __init__(self):
        self._metrics_store: Dict[str, TimeSeriesData] = {}
        self._alerts: List[Alert] = []
        self._alert_conditions: Dict[str, Callable[[MetricValue], bool]] = {}
        self._report_definitions: Dict[str, ReportDefinition] = {}
        self._anomaly_history: List[Dict[str, Any]] = []
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MetricValue:
        """
        Record a single metric value.
        
        Args:
            metric_name: Unique name for the metric
            value: Numeric value
            labels: Optional dimension labels (e.g., {'environment': 'prod'})
            metadata: Additional metadata
        
        Returns:
            Created MetricValue object
        """
        metric = MetricValue(
            metric_name=metric_name,
            value=value,
            labels=labels or {},
            metadata=metadata or {}
        )
        
        if metric_name not in self._metrics_store:
            self._metrics_store[metric_name] = TimeSeriesData(
                metric_name=metric_name,
                labels=labels or {}
            )
        
        self._metrics_store[metric_name].data_points.append(metric)
        self._check_alert_conditions(metric)
        
        logger.debug(f"Metric recorded: {metric_name} = {value}")
        return metric
    
    def record_metrics_batch(
        self,
        metrics: List[MetricValue]
    ) -> None:
        """Record multiple metrics at once"""
        for metric in metrics:
            if metric.metric_name not in self._metrics_store:
                self._metrics_store[metric.metric_name] = TimeSeriesData(
                    metric_name=metric.metric_name,
                    labels=metric.labels
                )
            self._metrics_store[metric.metric_name].data_points.append(metric)
            self._check_alert_conditions(metric)
    
    def get_metric(
        self,
        metric_name: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> Optional[TimeSeriesData]:
        """
        Get time series data for a metric.
        
        Args:
            metric_name: Metric to retrieve
            from_time: Optional start time filter
            to_time: Optional end time filter
        
        Returns:
            Filtered TimeSeriesData or None if no data
        """
        if metric_name not in self._metrics_store:
            return None
        
        data = self._metrics_store[metric_name]
        
        if from_time or to_time:
            filtered_points = []
            for dp in data.data_points:
                if from_time and dp.timestamp < from_time:
                    continue
                if to_time and dp.timestamp > to_time:
                    continue
                filtered_points.append(dp)
            
            filtered_data = TimeSeriesData(
                metric_name=metric_name,
                data_points=filtered_points,
                labels=data.labels
            )
            return filtered_data
        
        return data
    
    def get_all_metrics(self) -> Dict[str, TimeSeriesData]:
        """Get all available metrics"""
        return self._metrics_store.copy()
    
    def get_metric_names(self) -> List[str]:
        """Get list of all metric names"""
        return list(self._metrics_store.keys())
    
    def compute_aggregations(
        self,
        metric_name: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> Dict[MetricAggregation, float]:
        """
        Compute aggregations on a metric over a time range.
        
        Returns:
            Dictionary mapping aggregation type to value
        """
        data = self.get_metric(metric_name, from_time, to_time)
        return data.compute_aggregations() if data else {}
    
    def detect_anomalies(
        self,
        metric_name: str,
        window_hours: int = 24,
        z_score_threshold: float = 3.0
    ) -> List[MetricValue]:
        """
        Detect anomalies using Z-score method.
        
        Args:
            metric_name: Metric to analyze
            window_hours: Lookback window in hours
            z_score_threshold: Z-score threshold for anomaly detection
        
        Returns:
            List of metric values considered anomalous
        """
        from_time = datetime.now() - timedelta(hours=window_hours)
        data = self.get_metric(metric_name, from_time=from_time)
        
        if not data or len(data.data_points) < 10:
            return []
        
        values = data.get_values()
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        anomalies = []
        for dp in data.data_points:
            if std_dev > 0:
                z_score = abs(dp.value - mean) / std_dev
                if z_score > z_score_threshold:
                    anomalies.append(dp)
        
        if anomalies:
            logger.warning(
                f"Detected {len(anomalies)} anomalies in {metric_name}"
            )
            for anomaly in anomalies:
                self._anomaly_history.append({
                    'metric_name': metric_name,
                    'value': anomaly.value,
                    'timestamp': anomaly.timestamp.isoformat(),
                    'z_score_threshold': z_score_threshold
                })
        
        return anomalies
    
    def get_anomaly_history(self) -> List[Dict[str, Any]]:
        """Get history of detected anomalies"""
        return self._anomaly_history.copy()
    
    def register_alert_condition(
        self,
        condition_name: str,
        metric_name: str,
        condition: Callable[[MetricValue], bool],
        severity: AlertSeverity = AlertSeverity.WARNING
    ) -> None:
        """
        Register a condition that will generate alerts when true.
        
        Args:
            condition_name: Unique name for condition
            metric_name: Metric to monitor
            condition: Function that returns True to trigger alert
            severity: Alert severity level
        """
        self._alert_conditions[condition_name] = condition
        logger.info(f"Alert condition registered: {condition_name} on {metric_name}")
    
    def _check_alert_conditions(self, metric: MetricValue) -> None:
        """Check all registered conditions and create alerts"""
        for cond_name, cond_func in self._alert_conditions.items():
            try:
                if cond_func(metric):
                    self._create_alert(cond_name, metric)
            except Exception as e:
                logger.error(f"Error checking condition {cond_name}: {e}")
    
    def _create_alert(
        self,
        condition_name: str,
        metric: MetricValue,
        severity: AlertSeverity = AlertSeverity.WARNING
    ) -> Alert:
        """Create and store an alert"""
        alert = Alert(
            alert_id=f"alert_{uuid.uuid4().hex[:16]}",
            severity=severity,
            message=f"Condition '{condition_name}' triggered for {metric.metric_name}: {metric.value}",
            condition_name=condition_name,
            metric_name=metric.metric_name,
            current_value=metric.value,
            threshold_value=0.0
        )
        
        self._alerts.append(alert)
        logger.warning(f"ALERT created: {alert.alert_id} - {alert.message}")
        return alert
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = self._alerts
        
        if severity is not None:
            alerts = [a for a in alerts if a.severity == severity]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        return alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge()
                return True
        return False
    
    def clear_acknowledged_alerts(self) -> int:
        """Clear all acknowledged alerts and return count"""
        original_count = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.acknowledged]
        return original_count - len(self._alerts)
    
    def register_report(self, definition: ReportDefinition) -> None:
        """Register a report definition"""
        self._report_definitions[definition.report_id] = definition
        logger.info(f"Report registered: {definition.report_id}")
    
    def get_report_definition(self, report_id: str) -> Optional[ReportDefinition]:
        """Get report definition by ID"""
        return self._report_definitions.get(report_id)
    
    def generate_report(
        self,
        report_id: str,
        format: Optional[ReportFormat] = None
    ) -> Dict[str, Any]:
        """
        Generate a report based on registered definition.
        
        Returns:
            Report data in requested format
        """
        definition = self._report_definitions.get(report_id)
        if not definition:
            raise ValueError(f"Unknown report: {report_id}")
        
        report_format = format or definition.format
        
        from_time = datetime.now() - timedelta(hours=definition.time_range_hours)
        
        report_data: Dict[str, Any] = {
            'report_id': report_id,
            'report_name': definition.report_name,
            'description': definition.description,
            'generated_at': datetime.now().isoformat(),
            'time_range_hours': definition.time_range_hours,
            'metrics': {}
        }
        
        for metric_name in definition.metrics:
            aggregations = self.compute_aggregations(metric_name, from_time=from_time)
            report_data['metrics'][metric_name] = {
                agg.value: val for agg, val in aggregations.items()
            }
        
        if report_format == ReportFormat.JSON:
            return report_data
        elif report_format == ReportFormat.CSV:
            return self._report_to_csv(report_data)
        else:
            return report_data
    
    def _report_to_csv(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert report to CSV format (simplified)"""
        return {
            'format': 'csv',
            'data': report_data
        }
    
    def get_dashboard_data(
        self,
        window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.
        
        Returns:
            Dashboard-ready data structure
        """
        from_time = datetime.now() - timedelta(hours=window_hours)
        
        unacknowledged_alerts = [a for a in self._alerts if not a.acknowledged]
        
        dashboard: Dict[str, Any] = {
            'generated_at': datetime.now().isoformat(),
            'window_hours': window_hours,
            'total_metrics': len(self._metrics_store),
            'alerts': {
                'active': len(unacknowledged_alerts),
                'critical': len([a for a in unacknowledged_alerts if a.severity == AlertSeverity.CRITICAL]),
                'warning': len([a for a in unacknowledged_alerts if a.severity == AlertSeverity.WARNING]),
                'total': len(self._alerts),
                'recent': [
                    {
                        'id': a.alert_id,
                        'severity': a.severity.value,
                        'message': a.message,
                        'timestamp': a.timestamp.isoformat(),
                        'metric_name': a.metric_name
                    }
                    for a in self._alerts[-10:]
                ]
            },
            'metrics': {}
        }
        
        for metric_name, data in self._metrics_store.items():
            aggregations = data.compute_aggregations()
            dashboard['metrics'][metric_name] = {
                agg.value: val for agg, val in aggregations.items()
            }
            dashboard['metrics'][metric_name]['trend'] = data.get_trend()
        
        return dashboard
    
    def clear_metrics(self, older_than_hours: Optional[int] = None) -> int:
        """Clear old metrics to manage memory"""
        if older_than_hours is None:
            cleared = sum(len(d.data_points) for d in self._metrics_store.values())
            self._metrics_store.clear()
            return cleared
        
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        cleared = 0
        for metric_name in list(self._metrics_store.keys()):
            data = self._metrics_store[metric_name]
            original_count = len(data.data_points)
            data.data_points = [dp for dp in data.data_points if dp.timestamp >= cutoff]
            cleared += original_count - len(data.data_points)
            
            if not data.data_points:
                del self._metrics_store[metric_name]
        
        return cleared


class CostAttributionEngine:
    """
    Engine for attributing costs to tenants, workflows, and agents.
    
    Features:
      - Resource usage tracking
      - Cost allocation
      - Optimization recommendations
      - Multi-tenant cost reporting
    """
    
    def __init__(self):
        self._usage_records: List[Dict[str, Any]] = []
        self._cost_models: Dict[str, Dict[str, float]] = {}
        self._optimization_recommendations: List[Dict[str, Any]] = []
    
    def set_cost_model(
        self,
        resource_type: str,
        unit_costs: Dict[str, float]
    ) -> None:
        """
        Set cost per unit for a resource type.
        
        Args:
            resource_type: Type of resource (e.g., 'compute', 'storage')
            unit_costs: Dictionary of cost components (e.g., {'cpu': 0.01, 'memory': 0.005})
        """
        self._cost_models[resource_type] = unit_costs
        logger.info(f"Cost model set for: {resource_type}")
    
    def get_cost_model(self, resource_type: str) -> Optional[Dict[str, float]]:
        """Get cost model for a resource type"""
        return self._cost_models.get(resource_type)
    
    def record_usage(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        usage_amount: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record resource usage for cost attribution"""
        record: Dict[str, Any] = {
            'tenant_id': tenant_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'usage_amount': usage_amount,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self._usage_records.append(record)
        logger.debug(f"Usage recorded: {tenant_id} - {resource_type} = {usage_amount}")
    
    def get_tenant_cost_report(
        self,
        tenant_id: str,
        window_hours: int = 720
    ) -> Dict[str, Any]:
        """
        Generate cost report for a tenant.
        
        Args:
            tenant_id: Tenant to generate report for
            window_hours: Time window for the report
        
        Returns:
            Cost report dictionary
        """
        from_time = datetime.now() - timedelta(hours=window_hours)
        
        tenant_records = [
            r for r in self._usage_records
            if r['tenant_id'] == tenant_id
            and datetime.fromisoformat(r['timestamp']) > from_time
        ]
        
        total_cost = 0.0
        by_resource_type: Dict[str, float] = defaultdict(float)
        by_resource_id: Dict[str, float] = defaultdict(float)
        
        for record in tenant_records:
            rt = record['resource_type']
            usage = record['usage_amount']
            resource_id = record['resource_id']
            
            if rt in self._cost_models:
                for cost_type, cost_per_unit in self._cost_models[rt].items():
                    cost = usage * cost_per_unit
                    by_resource_type[rt] += cost
                    by_resource_id[resource_id] += cost
                    total_cost += cost
        
        return {
            'tenant_id': tenant_id,
            'window_hours': window_hours,
            'generated_at': datetime.now().isoformat(),
            'total_cost': round(total_cost, 2),
            'by_resource_type': dict(by_resource_type),
            'by_resource_id': dict(by_resource_id),
            'record_count': len(tenant_records)
        }
    
    def get_all_tenants_cost_report(
        self,
        window_hours: int = 720
    ) -> Dict[str, Any]:
        """Get aggregated cost report for all tenants"""
        from_time = datetime.now() - timedelta(hours=window_hours)
        
        tenant_records_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in self._usage_records:
            if datetime.fromisoformat(record['timestamp']) > from_time:
                tenant_records_map[record['tenant_id']].append(record)
        
        tenant_costs = {}
        total_cost = 0.0
        by_resource_type: Dict[str, float] = defaultdict(float)
        
        for tenant_id, records in tenant_records_map.items():
            tenant_total = 0.0
            for record in records:
                rt = record['resource_type']
                usage = record['usage_amount']
                
                if rt in self._cost_models:
                    for cost_per_unit in self._cost_models[rt].values():
                        cost = usage * cost_per_unit
                        tenant_total += cost
                        by_resource_type[rt] += cost
            
            tenant_costs[tenant_id] = round(tenant_total, 2)
            total_cost += tenant_total
        
        return {
            'window_hours': window_hours,
            'generated_at': datetime.now().isoformat(),
            'total_cost': round(total_cost, 2),
            'by_tenant': tenant_costs,
            'by_resource_type': dict(by_resource_type),
            'tenant_count': len(tenant_records_map)
        }
    
    def get_optimization_recommendations(
        self,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations: List[Dict[str, Any]] = []
        
        by_resource = defaultdict(list)
        for record in self._usage_records:
            by_resource[record['resource_type']].append(record['usage_amount'])
        
        for resource_type, usage_values in by_resource.items():
            if len(usage_values) < 10:
                continue
            
            avg_usage = statistics.mean(usage_values)
            max_usage = max(usage_values)
            
            if (max_usage / (avg_usage + 1)) > 3:
                recommendations.append({
                    'priority': 'high',
                    'category': 'resource_optimization',
                    'resource_type': resource_type,
                    'recommendation': f'Consider right-sizing {resource_type} resources',
                    'estimated_savings': '15-30%',
                    'analysis': {
                        'avg_usage': round(avg_usage, 2),
                        'peak_usage': round(max_usage, 2),
                        'variance_ratio': round(max_usage / (avg_usage + 1), 2)
                    }
                })
        
        return sorted(
            recommendations,
            key=lambda x: x['priority'] == 'high',
            reverse=True
        )[:top_n]
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get overall usage statistics"""
        by_resource = defaultdict(int)
        total_usage = 0.0
        
        for record in self._usage_records:
            by_resource[record['resource_type']] += 1
            total_usage += record['usage_amount']
        
        return {
            'total_records': len(self._usage_records),
            'total_usage': round(total_usage, 2),
            'by_resource_type': dict(by_resource),
            'unique_tenants': len(set(r['tenant_id'] for r in self._usage_records)),
            'unique_resources': len(set(r['resource_id'] for r in self._usage_records))
        }


_analytics_instance: Optional[AnalyticsEngine] = None
_cost_attribution_instance: Optional[CostAttributionEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get singleton analytics engine instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AnalyticsEngine()
    return _analytics_instance


def get_cost_attribution_engine() -> CostAttributionEngine:
    """Get singleton cost attribution engine instance"""
    global _cost_attribution_instance
    if _cost_attribution_instance is None:
        _cost_attribution_instance = CostAttributionEngine()
    return _cost_attribution_instance


def analytics_metric(metric_name: str):
    """
    Decorator to automatically record function execution metrics.
    
    Usage:
      @analytics_metric('my_function_execution_time')
      def my_function():
          ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time
            engine = get_analytics_engine()
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                engine.record_metric(
                    f"{metric_name}_duration",
                    duration,
                    labels={'status': 'success'}
                )
                engine.record_metric(f"{metric_name}_success", 1.0)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                engine.record_metric(
                    f"{metric_name}_duration",
                    duration,
                    labels={'status': 'error'}
                )
                engine.record_metric(f"{metric_name}_error", 1.0)
                raise
        return wrapper
    return decorator
