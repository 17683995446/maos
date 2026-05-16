"""
辅助函数模块
提供ID生成、时间工具、数据验证和序列化工具
"""

from __future__ import annotations

import base64
import hashlib
import json
import pickle
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)
import time


T = TypeVar('T')


class IDType(Enum):
    """ID类型枚举"""
    UUID = "uuid"
    SHORT = "short"
    CUSTOM = "custom"


def generate_uuid() -> str:
    """生成标准UUID字符串"""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    生成短ID

    参数：
        length: ID长度

    返回：
        短ID字符串
    """
    uuid_str = uuid.uuid4().hex
    return uuid_str[:length]


def generate_timestamp_id(prefix: str = "") -> str:
    """
    生成带时间戳的ID

    参数：
        prefix: ID前缀

    返回：
        带时间戳的ID字符串
    """
    timestamp = int(time.time() * 1000)
    unique_part = uuid.uuid4().hex[:6]
    return f"{prefix}{timestamp}-{unique_part}" if prefix else f"{timestamp}-{unique_part}"


def generate_hash_id(data: str, length: int = 12) -> str:
    """
    生成基于哈希的ID

    参数：
        data: 输入数据
        length: 哈希长度

    返回：
        哈希ID字符串
    """
    hash_obj = hashlib.sha256(data.encode('utf-8'))
    return hash_obj.hexdigest()[:length]


def generate_session_id() -> str:
    """生成会话ID"""
    return f"sess_{generate_uuid()}"


def generate_request_id() -> str:
    """生成请求ID"""
    return f"req_{int(time.time() * 1000)}"


def encode_id(id_value: str) -> str:
    """
    Base64编码ID

    参数：
        id_value: ID值

    返回：
        编码后的字符串
    """
    return base64.urlsafe_b64encode(id_value.encode()).decode()


def decode_id(encoded_value: str) -> str:
    """
    Base64解码ID

    参数：
        encoded_value: 编码后的字符串

    返回：
        解码后的ID
    """
    padding = 4 - len(encoded_value) % 4
    if padding != 4:
        encoded_value += '=' * padding
    return base64.urlsafe_b64decode(encoded_value.encode()).decode()


def get_current_timestamp() -> float:
    """获取当前时间戳（秒）"""
    return time.time()


def get_current_timestamp_ms() -> int:
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)


def get_current_utc_time() -> datetime:
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)


def get_current_local_time() -> datetime:
    """获取当前本地时间"""
    return datetime.now()


def format_timestamp(
    dt: Optional[datetime] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    格式化时间戳

    参数：
        dt: datetime对象（可选，默认当前时间）
        format_str: 格式字符串

    返回：
        格式化的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def parse_timestamp(
    timestamp_str: str,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """
    解析时间戳字符串

    参数：
        timestamp_str: 时间戳字符串
        format_str: 格式字符串

    返回：
        datetime对象
    """
    return datetime.strptime(timestamp_str, format_str)


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """
    解析ISO格式时间戳

    参数：
        timestamp_str: ISO格式时间戳字符串

    返回：
        datetime对象
    """
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


def to_utc(dt: datetime) -> datetime:
    """
    转换为UTC时间

    参数：
        dt: datetime对象

    返回：
        UTC时间
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_local_time(dt: datetime, local_tz: Optional[str] = None) -> datetime:
    """
    转换为本地时间

    参数：
        dt: datetime对象
        local_tz: 本地时区（可选）

    返回：
        本地时间
    """
    if local_tz:
        import zoneinfo
        local_zone = zoneinfo.ZoneInfo(local_tz)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(local_zone)
    return dt.astimezone()


def add_timedelta(
    dt: datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0
) -> datetime:
    """
    添加时间增量

    参数：
        dt: datetime对象
        days: 天数
        hours: 小时数
        minutes: 分钟数
        seconds: 秒数

    返回：
        新的datetime对象
    """
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return dt + delta


def get_time_difference(start: datetime, end: datetime) -> float:
    """
    计算时间差（秒）

    参数：
        start: 开始时间
        end: 结束时间

    返回：
        时间差（秒）
    """
    return (end - start).total_seconds()


class RetryTimer:
    """重试计时器，支持指数退避"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        """
        初始化重试计时器

        参数：
            base_delay: 基础延迟（秒）
            max_delay: 最大延迟（秒）
            multiplier: 延迟倍数
            jitter: 是否添加随机抖动
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.attempt = 0

    def get_delay(self) -> float:
        """
        获取下一次重试延迟

        返回：
            延迟时间（秒）
        """
        delay = min(self.base_delay * (self.multiplier ** self.attempt), self.max_delay)
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        self.attempt += 1
        return delay

    def reset(self) -> None:
        """重置计时器"""
        self.attempt = 0


def validate_type(value: Any, expected_type: Type[T]) -> T:
    """
    验证并转换类型

    参数：
        value: 待验证的值
        expected_type: 期望的类型

    返回：
        转换后的值

    异常：
        TypeError: 类型不匹配
    """
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
    return value


def validate_not_none(value: Any, field_name: str = "value") -> Any:
    """
    验证值不为None

    参数：
        value: 待验证的值
        field_name: 字段名称

    返回：
        值本身

    异常：
        ValueError: 值为None
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")
    return value


def validate_not_empty(value: Union[str, List, Dict], field_name: str = "value") -> Any:
    """
    验证值不为空

    参数：
        value: 待验证的值
        field_name: 字段名称

    返回：
        值本身

    异常：
        ValueError: 值为空
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    return value


def validate_range(
    value: Union[int, float],
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    field_name: str = "value"
) -> Union[int, float]:
    """
    验证值在指定范围内

    参数：
        value: 待验证的值
        min_val: 最小值
        max_val: 最大值
        field_name: 字段名称

    返回：
        值本身

    异常：
        ValueError: 值超出范围
    """
    if min_val is not None and value < min_val:
        raise ValueError(f"{field_name} must be >= {min_val}, got {value}")
    if max_val is not None and value > max_val:
        raise ValueError(f"{field_name} must be <= {max_val}, got {value}")
    return value


def validate_email(email: str) -> bool:
    """
    验证邮箱格式

    参数：
        email: 邮箱地址

    返回：
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    验证URL格式

    参数：
        url: URL地址

    返回：
        是否有效
    """
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str, code: Optional[str] = None) -> None:
        """添加错误"""
        self.errors.append(ValidationError(field=field, message=message, code=code))

    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """合并验证结果"""
        if other.valid:
            return self
        result = ValidationResult(valid=self.valid)
        result.errors = self.errors + other.errors
        result.valid = len(result.errors) == 0
        return result


class Validator:
    """数据验证器"""

    def __init__(self):
        self._rules: Dict[str, List[Callable[[Any], Optional[str]]]] = {}

    def add_rule(self, field: str, rule: Callable[[Any], Optional[str]]) -> 'Validator':
        """
        添加验证规则

        参数：
            field: 字段名
            rule: 验证函数，返回错误消息或None

        返回：
            Validator实例
        """
        if field not in self._rules:
            self._rules[field] = []
        self._rules[field].append(rule)
        return self

    def required(self, field: str) -> 'Validator':
        """必填字段"""
        return self.add_rule(field, lambda v: f"{field} is required" if v is None else None)

    def string(self, field: str, min_length: Optional[int] = None, max_length: Optional[int] = None) -> 'Validator':
        """字符串验证"""
        def rule(value):
            if value is None:
                return None
            if not isinstance(value, str):
                return f"{field} must be a string"
            if min_length is not None and len(value) < min_length:
                return f"{field} must be at least {min_length} characters"
            if max_length is not None and len(value) > max_length:
                return f"{field} must be at most {max_length} characters"
            return None
        return self.add_rule(field, rule)

    def number(self, field: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> 'Validator':
        """数字验证"""
        def rule(value):
            if value is None:
                return None
            if not isinstance(value, (int, float)):
                return f"{field} must be a number"
            if min_val is not None and value < min_val:
                return f"{field} must be >= {min_val}"
            if max_val is not None and value > max_val:
                return f"{field} must be <= {max_val}"
            return None
        return self.add_rule(field, rule)

    def email_field(self, field: str) -> 'Validator':
        """邮箱验证"""
        return self.add_rule(field, lambda v: f"{field} is not a valid email" if v and not validate_email(v) else None)

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证数据

        参数：
            data: 待验证的数据字典

        返回：
            ValidationResult实例
        """
        result = ValidationResult(valid=True)

        for field, rules in self._rules.items():
            value = data.get(field)
            for rule in rules:
                error = rule(value)
                if error:
                    result.add_error(field, error)
                    break

        result.valid = len(result.errors) == 0
        return result


def to_json_serializable(obj: Any) -> Any:
    """
    转换为JSON可序列化对象

    参数：
        obj: 任意对象

    返回：
        JSON可序列化的对象
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_json_serializable(item) for item in obj]
    if hasattr(obj, 'to_dict'):
        return to_json_serializable(obj.to_dict())
    if hasattr(obj, '__dict__'):
        return to_json_serializable(obj.__dict__)
    return str(obj)


def serialize_to_json(
    obj: Any,
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
    **kwargs
) -> str:
    """
    序列化为JSON字符串

    参数：
        obj: 待序列化的对象
        indent: 缩进空格数
        ensure_ascii: 是否转义非ASCII字符
        **kwargs: json.dumps的其他参数

    返回：
        JSON字符串
    """
    return json.dumps(
        to_json_serializable(obj),
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=str,
        **kwargs
    )


def deserialize_from_json(json_str: str, **kwargs) -> Any:
    """
    从JSON字符串反序列化

    参数：
        json_str: JSON字符串
        **kwargs: json.loads的其他参数

    返回：
        反序列化后的对象
    """
    return json.loads(json_str, **kwargs)


def serialize_to_pickle(obj: Any) -> bytes:
    """
    序列化为pickle字节串

    参数：
        obj: 待序列化的对象

    返回：
        pickle字节串
    """
    return pickle.dumps(obj)


def deserialize_from_pickle(pickle_bytes: bytes) -> Any:
    """
    从pickle字节串反序列化

    参数：
        pickle_bytes: pickle字节串

    返回：
        反序列化后的对象
    """
    return pickle.loads(pickle_bytes)


@dataclass
class DataClassEncoder:
    """数据类编码器"""
    exclude_none: bool = True
    exclude_fields: Optional[Set[str]] = None

    def encode(self, obj: Any) -> Dict[str, Any]:
        """编码对象"""
        if hasattr(obj, 'to_dict'):
            data = obj.to_dict()
        elif hasattr(obj, '__dataclass_fields__'):
            data = asdict(obj)
        elif isinstance(obj, dict):
            data = obj.copy()
        else:
            return {"value": str(obj)}

        if self.exclude_none:
            data = {k: v for k, v in data.items() if v is not None}

        if self.exclude_fields:
            data = {k: v for k, v in data.items() if k not in self.exclude_fields}

        return data


class Cache(Generic[T]):
    """简单的内存缓存"""

    def __init__(self, max_size: int = 100, ttl: Optional[float] = None):
        """
        初始化缓存

        参数：
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒）
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Tuple[T, float]] = {}

    def get(self, key: str) -> Optional[T]:
        """获取缓存值"""
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if self.ttl and (time.time() - timestamp) > self.ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: T) -> None:
        """设置缓存值"""
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        self._cache[key] = (value, time.time())

    def delete(self, key: str) -> None:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


@contextmanager
def timer(name: str = "operation"):
    """
    计时上下文管理器

    参数：
        name: 操作名称

    示例：
        with timer("data_processing"):
            # 执行操作
            pass
    """
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"{name} took {elapsed:.3f}s")


def safe_get(dictionary: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    安全获取嵌套字典值

    参数：
        dictionary: 字典对象
        *keys: 嵌套键路径
        default: 默认值

    返回：
        获取的值或默认值
    """
    result = dictionary
    for key in keys:
        if not isinstance(result, dict):
            return default
        result = result.get(key)
        if result is None:
            return default
    return result


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个字典

    参数：
        *dicts: 要合并的字典

    返回：
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    扁平化嵌套字典

    参数：
        d: 嵌套字典
        parent_key: 父键前缀
        sep: 分隔符

    返回：
        扁平化的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块

    参数：
        lst: 列表
        chunk_size: 块大小

    返回：
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


from typing import Tuple


__all__ = [
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
]
