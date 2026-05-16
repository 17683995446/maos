"""
指标收集模块
提供Prometheus风格指标、计数器、仪表和延迟直方图
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
)

T = TypeVar('T')


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricMetadata:
    """指标元数据"""
    name: str
    description: str = ""
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)


class Counter:
    """
    计数器指标

    用于记录只递增的数值，如请求数、错误数等。

    示例：
        counter = Counter("requests_total", "Total number of requests")
        counter.inc()
        counter.inc(5)
        counter.labels(method="GET").inc()
    """

    _type = MetricType.COUNTER

    def __init__(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        initial_value: float = 0.0,
    ):
        """
        初始化计数器

        参数：
            name: 指标名称
            description: 指标描述
            unit: 单位
            initial_value: 初始值
        """
        self.name = name
        self._description = description
        self._unit = unit
        self._value = initial_value
        self._labels_values: Dict[Tuple, float] = defaultdict(float)
        self._lock = threading.Lock()
        self._metadata = MetricMetadata(
            name=name,
            description=description,
            unit=unit,
        )

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        增加计数器值

        参数：
            amount: 增加量
            labels: 标签字典
        """
        if labels is None:
            with self._lock:
                self._value += amount
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                self._labels_values[label_tuple] += amount

    def _labels_to_tuple(self, labels: Dict[str, str]) -> Tuple:
        """将标签字典转换为元组"""
        return tuple(sorted(labels.items()))

    def _tuple_to_labels(self, label_tuple: Tuple) -> Dict[str, str]:
        """将元组转换为标签字典"""
        return dict(label_tuple)

    def labels(self, **label_kwargs) -> 'LabeledCounter':
        """
        获取带标签的计数器

        参数：
            **label_kwargs: 标签键值对

        返回：
            LabeledCounter实例
        """
        return LabeledCounter(self, label_kwargs)

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """
        获取计数器值

        参数：
            labels: 标签字典（可选）

        返回：
            计数器值
        """
        if labels is None:
            with self._lock:
                return self._value
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                return self._labels_values.get(label_tuple, 0.0)

    def get_all_values(self) -> Dict[Dict[str, str], float]:
        """
        获取所有带标签的值

        返回：
            标签到值的映射
        """
        with self._lock:
            return {
                self._tuple_to_labels(k): v
                for k, v in self._labels_values.items()
            }

    def reset(self, labels: Optional[Dict[str, str]] = None) -> None:
        """
        重置计数器

        参数：
            labels: 标签字典（可选），为None时重置所有
        """
        if labels is None:
            with self._lock:
                self._value = 0.0
                self._labels_values.clear()
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                if label_tuple in self._labels_values:
                    del self._labels_values[label_tuple]

    def collect(self) -> List['MetricSample']:
        """收集指标样本"""
        samples = []
        with self._lock:
            if self._labels_values:
                for label_tuple, value in self._labels_values.items():
                    samples.append(MetricSample(
                        name=self.name,
                        value=value,
                        labels=self._tuple_to_labels(label_tuple),
                        metric_type=MetricType.COUNTER,
                    ))
            else:
                samples.append(MetricSample(
                    name=self.name,
                    value=self._value,
                    labels={},
                    metric_type=MetricType.COUNTER,
                ))
        return samples


class LabeledCounter:
    """带标签的计数器代理"""

    def __init__(self, counter: Counter, labels: Dict[str, str]):
        self._counter = counter
        self._labels = labels

    def inc(self, amount: float = 1.0) -> None:
        """增加计数器"""
        self._counter.inc(amount, self._labels)

    def get_value(self) -> float:
        """获取计数器值"""
        return self._counter.get_value(self._labels)


class Gauge:
    """
    仪表指标

    用于记录可以增减的数值，如当前连接数、内存使用量等。

    示例：
        gauge = Gauge("memory_usage_bytes", "Memory usage in bytes")
        gauge.set(1024)
        gauge.inc(10)
        gauge.dec(5)
    """

    _type = MetricType.GAUGE

    def __init__(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        initial_value: float = 0.0,
    ):
        """
        初始化仪表

        参数：
            name: 指标名称
            description: 指标描述
            unit: 单位
            initial_value: 初始值
        """
        self.name = name
        self._description = description
        self._unit = unit
        self._value = initial_value
        self._labels_values: Dict[Tuple, float] = defaultdict(float)
        self._lock = threading.Lock()
        self._metadata = MetricMetadata(
            name=name,
            description=description,
            unit=unit,
        )

    def _labels_to_tuple(self, labels: Dict[str, str]) -> Tuple:
        """将标签字典转换为元组"""
        return tuple(sorted(labels.items()))

    def _tuple_to_labels(self, label_tuple: Tuple) -> Dict[str, str]:
        """将元组转换为标签字典"""
        return dict(label_tuple)

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        设置仪表值

        参数：
            value: 新值
            labels: 标签字典
        """
        if labels is None:
            with self._lock:
                self._value = value
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                self._labels_values[label_tuple] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        增加仪表值

        参数：
            amount: 增加量
            labels: 标签字典
        """
        if labels is None:
            with self._lock:
                self._value += amount
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                self._labels_values[label_tuple] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        减少仪表值

        参数：
            amount: 减少量
            labels: 标签字典
        """
        self.inc(-amount, labels)

    def labels(self, **label_kwargs) -> 'LabeledGauge':
        """获取带标签的仪表"""
        return LabeledGauge(self, label_kwargs)

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """获取仪表值"""
        if labels is None:
            with self._lock:
                return self._value
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                return self._labels_values.get(label_tuple, 0.0)

    def get_all_values(self) -> Dict[Dict[str, str], float]:
        """获取所有带标签的值"""
        with self._lock:
            return {
                self._tuple_to_labels(k): v
                for k, v in self._labels_values.items()
            }

    def reset(self, labels: Optional[Dict[str, str]] = None) -> None:
        """重置仪表"""
        if labels is None:
            with self._lock:
                self._value = 0.0
                self._labels_values.clear()
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                if label_tuple in self._labels_values:
                    del self._labels_values[label_tuple]

    def collect(self) -> List['MetricSample']:
        """收集指标样本"""
        samples = []
        with self._lock:
            if self._labels_values:
                for label_tuple, value in self._labels_values.items():
                    samples.append(MetricSample(
                        name=self.name,
                        value=value,
                        labels=self._tuple_to_labels(label_tuple),
                        metric_type=MetricType.GAUGE,
                    ))
            else:
                samples.append(MetricSample(
                    name=self.name,
                    value=self._value,
                    labels={},
                    metric_type=MetricType.GAUGE,
                ))
        return samples


class LabeledGauge:
    """带标签的仪表代理"""

    def __init__(self, gauge: Gauge, labels: Dict[str, str]):
        self._gauge = gauge
        self._labels = labels

    def set(self, value: float) -> None:
        """设置仪表值"""
        self._gauge.set(value, self._labels)

    def inc(self, amount: float = 1.0) -> None:
        """增加仪表值"""
        self._gauge.inc(amount, self._labels)

    def dec(self, amount: float = 1.0) -> None:
        """减少仪表值"""
        self._gauge.dec(amount, self._labels)

    def get_value(self) -> float:
        """获取仪表值"""
        return self._gauge.get_value(self._labels)


class Histogram:
    """
    直方图指标

    用于记录数值的分布，支持自定义桶边界。
    常用于测量延迟、请求大小等。

    示例：
        histogram = Histogram(
            "request_duration_seconds",
            "Request duration in seconds",
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        histogram.observe(0.123)
    """

    _type = MetricType.HISTOGRAM

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)

    def __init__(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        buckets: Tuple[float, ...] = DEFAULT_BUCKETS,
    ):
        """
        初始化直方图

        参数：
            name: 指标名称
            description: 指标描述
            unit: 单位
            buckets: 桶边界元组
        """
        self.name = name
        self._description = description
        self._unit = unit
        self._buckets = tuple(sorted(buckets))
        self._counts: Dict[float, float] = defaultdict(float)
        self._sum = 0.0
        self._count = 0

        self._labels_counts: Dict[Tuple, Dict[float, float]] = defaultdict(lambda: defaultdict(float))
        self._labels_sums: Dict[Tuple, float] = defaultdict(float)
        self._labels_counts_total: Dict[Tuple, int] = defaultdict(int)

        self._lock = threading.Lock()
        self._metadata = MetricMetadata(
            name=name,
            description=description,
            unit=unit,
        )

    def _labels_to_tuple(self, labels: Dict[str, str]) -> Tuple:
        """将标签字典转换为元组"""
        return tuple(sorted(labels.items()))

    def _tuple_to_labels(self, label_tuple: Tuple) -> Dict[str, str]:
        """将元组转换为标签字典"""
        return dict(label_tuple)

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        记录观察值

        参数：
            value: 观察值
            labels: 标签字典
        """
        if labels is None:
            with self._lock:
                self._sum += value
                self._count += 1
                for bucket in self._buckets:
                    if value <= bucket:
                        self._counts[bucket] += 1
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                self._labels_sums[label_tuple] += value
                self._labels_counts_total[label_tuple] += 1
                for bucket in self._buckets:
                    if value <= bucket:
                        self._labels_counts[label_tuple][bucket] += 1

    def labels(self, **label_kwargs) -> 'LabeledHistogram':
        """获取带标签的直方图"""
        return LabeledHistogram(self, label_kwargs)

    def get_stats(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        获取统计信息

        参数：
            labels: 标签字典（可选）

        返回：
            包含count、sum、avg等统计信息
        """
        if labels is None:
            with self._lock:
                count = self._count
                total = self._sum
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                count = self._labels_counts_total.get(label_tuple, 0)
                total = self._labels_sums.get(label_tuple, 0.0)

        return {
            "count": count,
            "sum": total,
            "avg": total / count if count > 0 else 0.0,
        }

    def get_buckets(self, labels: Optional[Dict[str, str]] = None) -> Dict[float, float]:
        """
        获取桶计数

        参数：
            labels: 标签字典（可选）

        返回：
            桶边界到计数的映射
        """
        if labels is None:
            with self._lock:
                return dict(self._counts)
        else:
            label_tuple = self._labels_to_tuple(labels)
            with self._lock:
                return dict(self._labels_counts.get(label_tuple, {}))

    def collect(self) -> List['MetricSample']:
        """收集指标样本"""
        samples = []

        def add_bucket_samples(counts_dict: Dict[float, float], cum_count: float, labels: Dict[str, str]):
            cumulative = 0.0
            for bucket in self._buckets:
                cumulative += counts_dict.get(bucket, 0.0)
                samples.append(MetricSample(
                    name=f"{self.name}_bucket",
                    value=cumulative,
                    labels={**labels, "le": str(bucket)},
                    metric_type=MetricType.HISTOGRAM,
                ))
            samples.append(MetricSample(
                name=f"{self.name}_bucket",
                value=cum_count,
                labels={**labels, "le": "+Inf"},
                metric_type=MetricType.HISTOGRAM,
            ))

        with self._lock:
            if self._labels_counts:
                for label_tuple, counts in self._labels_counts.items():
                    labels = self._tuple_to_labels(label_tuple)
                    add_bucket_samples(counts, self._labels_counts_total[label_tuple], labels)
                for label_tuple, sum_val in self._labels_sums.items():
                    samples.append(MetricSample(
                        name=f"{self.name}_sum",
                        value=sum_val,
                        labels=self._tuple_to_labels(label_tuple),
                        metric_type=MetricType.HISTOGRAM,
                    ))
                for label_tuple, count in self._labels_counts_total.items():
                    samples.append(MetricSample(
                        name=f"{self.name}_count",
                        value=float(count),
                        labels=self._tuple_to_labels(label_tuple),
                        metric_type=MetricType.HISTOGRAM,
                    ))
            else:
                add_bucket_samples(self._counts, self._count, {})
                samples.append(MetricSample(
                    name=f"{self.name}_sum",
                    value=self._sum,
                    labels={},
                    metric_type=MetricType.HISTOGRAM,
                ))
                samples.append(MetricSample(
                    name=f"{self.name}_count",
                    value=float(self._count),
                    labels={},
                    metric_type=MetricType.HISTOGRAM,
                ))

        return samples


class LabeledHistogram:
    """带标签的直方图代理"""

    def __init__(self, histogram: Histogram, labels: Dict[str, str]):
        self._histogram = histogram
        self._labels = labels

    def observe(self, value: float) -> None:
        """记录观察值"""
        self._histogram.observe(value, self._labels)


@dataclass
class MetricSample:
    """指标样本"""
    name: str
    value: float
    labels: Dict[str, str]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsRegistry:
    """
    指标注册表

    管理所有指标实例，提供收集和导出功能。

    示例：
        registry = MetricsRegistry()

        @registry.register
        def get_requests_counter():
            return registry.get_or_create_counter("requests_total", "Total requests")

        registry.inc("requests_total")
        output = registry.export()
    """

    _instance: Optional['MetricsRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = threading.Lock()
        self._initialized = True

    @classmethod
    def get_default(cls) -> 'MetricsRegistry':
        """获取默认注册表"""
        return cls()

    def get_or_create_counter(
        self,
        name: str,
        description: str = "",
        unit: str = "",
    ) -> Counter:
        """
        获取或创建计数器

        参数：
            name: 指标名称
            description: 指标描述
            unit: 单位

        返回：
            Counter实例
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description, unit)
            return self._counters[name]

    def get_or_create_gauge(
        self,
        name: str,
        description: str = "",
        unit: str = "",
    ) -> Gauge:
        """
        获取或创建仪表

        参数：
            name: 指标名称
            description: 指标描述
            unit: 单位

        返回：
            Gauge实例
        """
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description, unit)
            return self._gauges[name]

    def get_or_create_histogram(
        self,
        name: str,
        description: str = "",
        unit: str = "",
        buckets: Tuple[float, ...] = Histogram.DEFAULT_BUCKETS,
    ) -> Histogram:
        """
        获取或创建直方图

        参数：
            name: 指标名称
            description: 指标描述
            unit: 单位
            buckets: 桶边界

        返回：
            Histogram实例
        """
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, unit, buckets)
            return self._histograms[name]

    def counter(self, name: str, **kwargs) -> Counter:
        """获取或创建计数器（简写）"""
        return self.get_or_create_counter(name, **kwargs)

    def gauge(self, name: str, **kwargs) -> Gauge:
        """获取或创建仪表（简写）"""
        return self.get_or_create_gauge(name, **kwargs)

    def histogram(self, name: str, **kwargs) -> Histogram:
        """获取或创建直方图（简写）"""
        return self.get_or_create_histogram(name, **kwargs)

    def inc(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器"""
        self.get_or_create_counter(name).inc(amount, labels)

    def dec(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """减少仪表"""
        self.get_or_create_gauge(name).dec(amount, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值"""
        self.get_or_create_gauge(name).set(value, labels)

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录直方图观察值"""
        self.get_or_create_histogram(name).observe(value, labels)

    def collect(self) -> List[MetricSample]:
        """收集所有指标样本"""
        samples = []
        with self._lock:
            for counter in self._counters.values():
                samples.extend(counter.collect())
            for gauge in self._gauges.values():
                samples.extend(gauge.collect())
            for histogram in self._histograms.values():
                samples.extend(histogram.collect())
        return samples

    def export(self, format: str = "prometheus") -> str:
        """
        导出指标

        参数：
            format: 输出格式（prometheus/text）

        返回：
            格式化的指标字符串
        """
        samples = self.collect()

        if format == "prometheus":
            lines = []
            for sample in samples:
                label_str = ""
                if sample.labels:
                    label_parts = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_parts) + "}"
                lines.append(f"{sample.name}{label_str} {sample.value}")
            return "\n".join(lines)

        elif format == "json":
            import json
            return json.dumps([
                {
                    "name": s.name,
                    "value": s.value,
                    "labels": s.labels,
                    "type": s.metric_type.value,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in samples
            ], indent=2)

        else:
            return str(samples)

    def clear(self) -> None:
        """清除所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


class Timer:
    """
    指标计时器

    自动记录操作延迟到直方图。

    示例：
        histogram = registry.histogram("operation_duration_seconds")
        with Timer(histogram):
            # 执行操作
            pass
    """

    def __init__(
        self,
        histogram: Optional[Histogram] = None,
        histogram_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        初始化计时器

        参数：
            histogram: Histogram实例
            histogram_name: 直方图名称（使用注册表创建）
            labels: 标签字典
        """
        self.histogram = histogram
        self.histogram_name = histogram_name
        self.labels = labels
        self.start_time: Optional[float] = None
        self._duration: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._duration = time.time() - self.start_time
        if self.histogram:
            self.histogram.observe(self._duration, self.labels)
        elif self.histogram_name:
            registry = MetricsRegistry.get_default()
            registry.observe(self.histogram_name, self._duration, self.labels)
        return False

    @property
    def duration(self) -> float:
        """获取经过的时间（秒）"""
        if self._duration is not None:
            return self._duration
        if self.start_time is not None:
            return time.time() - self.start_time
        return 0.0


class AsyncTimer:
    """
    异步指标计时器

    用于异步操作的计时。
    """

    def __init__(
        self,
        histogram: Optional[Histogram] = None,
        histogram_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.histogram = histogram
        self.histogram_name = histogram_name
        self.labels = labels
        self.start_time: Optional[float] = None
        self._duration: Optional[float] = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._duration = time.time() - self.start_time
        if self.histogram:
            self.histogram.observe(self._duration, self.labels)
        elif self.histogram_name:
            registry = MetricsRegistry.get_default()
            registry.observe(self.histogram_name, self._duration, self.labels)
        return False

    @property
    def duration(self) -> float:
        """获取经过的时间（秒）"""
        if self._duration is not None:
            return self._duration
        if self.start_time is not None:
            return time.time() - self.start_time
        return 0.0


def track_inprogress(gauge_name: str, labels: Optional[Dict[str, str]] = None):
    """
    装饰器：跟踪正在运行的任务数

    参数：
        gauge_name: 仪表名称
        labels: 标签字典

    示例：
        @track_inprogress("active_tasks")
        async def long_running_task():
            pass
    """
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            registry = MetricsRegistry.get_default()
            gauge = registry.get_or_create_gauge(gauge_name)
            gauge.inc(labels=labels)
            try:
                return await func(*args, **kwargs)
            finally:
                gauge.dec(labels=labels)

        def sync_wrapper(*args, **kwargs):
            registry = MetricsRegistry.get_default()
            gauge = registry.get_or_create_gauge(gauge_name)
            gauge.inc(labels=labels)
            try:
                return func(*args, **kwargs)
            finally:
                gauge.dec(labels=labels)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_duration(histogram_name: str, labels: Optional[Dict[str, str]] = None):
    """
    装饰器：跟踪函数执行时间

    参数：
        histogram_name: 直方图名称
        labels: 标签字典

    示例：
        @track_duration("function_duration_seconds")
        async def my_function():
            pass
    """
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            registry = MetricsRegistry.get_default()
            histogram = registry.get_or_create_histogram(histogram_name)
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                histogram.observe(duration, labels)

        def sync_wrapper(*args, **kwargs):
            registry = MetricsRegistry.get_default()
            histogram = registry.get_or_create_histogram(histogram_name)
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                histogram.observe(duration, labels)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


registry = MetricsRegistry.get_default()

__all__ = [
    "MetricType",
    "MetricMetadata",
    "MetricSample",
    "Counter",
    "LabeledCounter",
    "Gauge",
    "LabeledGauge",
    "Histogram",
    "LabeledHistogram",
    "MetricsRegistry",
    "Timer",
    "AsyncTimer",
    "track_inprogress",
    "track_duration",
    "registry",
]
