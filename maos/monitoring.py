"""
MAOS v5.0 - 监控和日志系统
企业级可观测性解决方案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import asyncio


class LogLevel(Enum):
    """日志级别"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    logger: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.name,
            'logger': self.logger,
            'message': self.message,
            'metadata': self.metadata
        }


@dataclass
class Metric:
    """指标"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels
        }


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, retention_seconds: int = 3600):
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self.retention_seconds = retention_seconds
        self._lock = threading.Lock()
    
    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """记录计数器"""
        with self._lock:
            self._counters[name] += value
            metric = Metric(
                name=name,
                value=self._counters[name],
                metric_type=MetricType.COUNTER,
                labels=labels or {}
            )
            self._metrics[name].append(metric)
            self._cleanup_old_metrics()
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录仪表"""
        with self._lock:
            self._gauges[name] = value
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                labels=labels or {}
            )
            self._metrics[name].append(metric)
            self._cleanup_old_metrics()
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图"""
        with self._lock:
            self._histograms[name].append(value)
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                labels=labels or {}
            )
            self._metrics[name].append(metric)
            self._cleanup_old_metrics()
    
    def _cleanup_old_metrics(self):
        """清理旧指标"""
        cutoff = datetime.now() - timedelta(seconds=self.retention_seconds)
        for name in list(self._metrics.keys()):
            while self._metrics[name] and self._metrics[name][0].timestamp < cutoff:
                self._metrics[name].popleft()
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取指标"""
        with self._lock:
            if name:
                metrics = list(self._metrics.get(name, []))
            else:
                metrics = []
                for m_list in self._metrics.values():
                    metrics.extend(m_list)
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return [m.to_dict() for m in metrics]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        with self._lock:
            return {
                'total_metrics': sum(len(m) for m in self._metrics.values()),
                'unique_metrics': len(self._metrics),
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    name: {
                        'count': len(values),
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'avg': sum(values) / len(values) if values else 0
                    }
                    for name, values in self._histograms.items()
                }
            }


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.name = name
        self._logs: deque = deque(maxlen=10000)
        self._handlers: List[Callable] = []
        self._lock = threading.Lock()
    
    def add_handler(self, handler: Callable):
        """添加日志处理器"""
        self._handlers.append(handler)
    
    def _log(self, level: LogLevel, message: str, **metadata):
        """记录日志"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            logger=self.name,
            message=message,
            metadata=metadata
        )
        
        with self._lock:
            self._logs.append(entry)
        
        for handler in self._handlers:
            try:
                handler(entry)
            except Exception:
                pass
        
        return entry
    
    def debug(self, message: str, **metadata):
        return self._log(LogLevel.DEBUG, message, **metadata)
    
    def info(self, message: str, **metadata):
        return self._log(LogLevel.INFO, message, **metadata)
    
    def warning(self, message: str, **metadata):
        return self._log(LogLevel.WARNING, message, **metadata)
    
    def error(self, message: str, **metadata):
        return self._log(LogLevel.ERROR, message, **metadata)
    
    def critical(self, message: str, **metadata):
        return self._log(LogLevel.CRITICAL, message, **metadata)
    
    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取日志"""
        with self._lock:
            logs = list(self._logs)
        
        if level:
            logs = [l for l in logs if l.level.value >= level.value]
        
        if since:
            logs = [l for l in logs if l.timestamp >= since]
        
        return [l.to_dict() for l in logs[-limit:]]


class MonitoringSystem:
    """监控系统 - 整合日志和指标"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.loggers: Dict[str, StructuredLogger] = {}
        self.alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def get_logger(self, name: str) -> StructuredLogger:
        """获取日志器"""
        if name not in self.loggers:
            self.loggers[name] = StructuredLogger(name)
        return self.loggers[name]
    
    def record_metric(self, name: str, value: float, metric_type: str = "gauge", labels: Dict[str, str] = None):
        """记录指标"""
        m_type = MetricType(metric_type)
        
        if m_type == MetricType.COUNTER:
            self.metrics.record_counter(name, value, labels)
        elif m_type == MetricType.GAUGE:
            self.metrics.record_gauge(name, value, labels)
        elif m_type == MetricType.HISTOGRAM:
            self.metrics.record_histogram(name, value, labels)
    
    def create_alert(self, name: str, message: str, severity: str = "warning", **metadata):
        """创建告警"""
        alert = {
            'id': f"alert-{int(time.time())}",
            'name': name,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata,
            'acknowledged': False
        }
        
        with self._lock:
            self.alerts.append(alert)
        
        return alert
    
    def acknowledge_alert(self, alert_id: str):
        """确认告警"""
        with self._lock:
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_at'] = datetime.now().isoformat()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'timestamp': datetime.now().isoformat(),
            'metrics_summary': self.metrics.get_summary(),
            'active_alerts': len([a for a in self.alerts if not a['acknowledged']]),
            'loggers_count': len(self.loggers),
            'recent_logs': {
                name: logger.get_logs(limit=10)
                for name, logger in list(self.loggers.items())[:5]
            }
        }


# 全局监控系统
_monitoring_system: Optional[MonitoringSystem] = None


def get_monitoring_system() -> MonitoringSystem:
    """获取全局监控系统"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system


def get_logger(name: str) -> StructuredLogger:
    """获取日志器"""
    return get_monitoring_system().get_logger(name)


def record_metric(name: str, value: float, metric_type: str = "gauge", labels: Dict[str, str] = None):
    """记录指标"""
    get_monitoring_system().record_metric(name, value, metric_type, labels)
