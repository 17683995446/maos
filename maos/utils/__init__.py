"""
MAOS工具函数和实用工具包
========================

提供日志、辅助函数和指标收集等核心工具。

模块：
    logger: 结构化日志工具
    helpers: 辅助函数（ID生成、时间工具、数据验证、序列化）
    metrics: Prometheus风格指标收集

示例：
    from maos.utils import Logger, generate_uuid, registry

    logger = Logger.get_logger("my_app")
    logger.info("Hello", user_id="123")

    uuid = generate_uuid()

    registry.counter("requests_total").inc()
"""

from maos.utils.logger import (
    Logger,
    StructuredLogger,
    LogContext,
    Timer,
    LogLevel,
    LogFormat,
    setup_logging,
)

from maos.utils.helpers import (
    generate_uuid,
    generate_short_id,
    generate_timestamp_id,
    generate_hash_id,
    generate_session_id,
    generate_request_id,
    encode_id,
    decode_id,
    get_current_timestamp,
    get_current_timestamp_ms,
    get_current_utc_time,
    get_current_local_time,
    format_timestamp,
    parse_timestamp,
    parse_iso_timestamp,
    to_utc,
    to_local_time,
    add_timedelta,
    get_time_difference,
    RetryTimer,
    validate_type,
    validate_not_none,
    validate_not_empty,
    validate_range,
    validate_email,
    validate_url,
    ValidationError,
    ValidationResult,
    Validator,
    to_json_serializable,
    serialize_to_json,
    deserialize_from_json,
    serialize_to_pickle,
    deserialize_from_pickle,
    DataClassEncoder,
    Cache,
    timer,
    safe_get,
    merge_dicts,
    flatten_dict,
    chunk_list,
)

from maos.utils.metrics import (
    MetricType,
    MetricMetadata,
    MetricSample,
    Counter,
    LabeledCounter,
    Gauge,
    LabeledGauge,
    Histogram,
    LabeledHistogram,
    MetricsRegistry,
    Timer as MetricsTimer,
    AsyncTimer as MetricsAsyncTimer,
    track_inprogress,
    track_duration,
    registry,
)

__all__ = [
    "Logger",
    "StructuredLogger",
    "LogContext",
    "Timer",
    "LogLevel",
    "LogFormat",
    "setup_logging",
    "generate_uuid",
    "generate_short_id",
    "generate_timestamp_id",
    "generate_hash_id",
    "generate_session_id",
    "generate_request_id",
    "encode_id",
    "decode_id",
    "get_current_timestamp",
    "get_current_timestamp_ms",
    "get_current_utc_time",
    "get_current_local_time",
    "format_timestamp",
    "parse_timestamp",
    "parse_iso_timestamp",
    "to_utc",
    "to_local_time",
    "add_timedelta",
    "get_time_difference",
    "RetryTimer",
    "validate_type",
    "validate_not_none",
    "validate_not_empty",
    "validate_range",
    "validate_email",
    "validate_url",
    "ValidationError",
    "ValidationResult",
    "Validator",
    "to_json_serializable",
    "serialize_to_json",
    "deserialize_from_json",
    "serialize_to_pickle",
    "deserialize_from_pickle",
    "DataClassEncoder",
    "Cache",
    "timer",
    "safe_get",
    "merge_dicts",
    "flatten_dict",
    "chunk_list",
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
    "MetricsTimer",
    "MetricsAsyncTimer",
    "track_inprogress",
    "track_duration",
    "registry",
]
