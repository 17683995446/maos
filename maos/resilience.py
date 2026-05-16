"""
MAOS v6.0 - 错误处理和容错机制
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常，熔断器关闭
    OPEN = "open"          # 打开，请求被拒绝
    HALF_OPEN = "half_open"  # 半开，允许部分请求


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5        # 失败次数阈值
    success_threshold: int = 2        # 成功次数阈值（半开->关）
    timeout: float = 60.0           # 超时时间（秒）
    expected_exceptions: tuple = (Exception,)  # 期望的异常类型


class CircuitBreakerOpen(Exception):
    """断路器打开异常"""
    def __init__(self, message="Circuit breaker is open"):
        self.message = message
        super().__init__(self.message)


class CircuitBreaker:
    """断路器实现"""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """调用函数，带断路器保护"""
        async with self._lock:
            # 检查是否可以执行
            if not self._can_execute():
                raise CircuitBreakerOpen(f"Circuit breaker '{self.name}' is open")
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                await self._on_success()
                return result
            
            except self.config.expected_exceptions as e:
                await self._on_failure()
                raise
    
    def _can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # 检查超时
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.config.timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        
        # 半开状态，允许执行
        return True
    
    async def _on_success(self):
        """成功处理"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
    
    async def _on_failure(self):
        """失败处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_status(self) -> dict:
        """获取状态"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"              # 固定延迟
    LINEAR = "linear"            # 线性增长
    EXPONENTIAL = "exponential"  # 指数退避
    FIBONACCI = "fibonacci"      # 斐波那契退避


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    jitter_factor: float = 0.1


class RetryExhausted(Exception):
    """重试次数耗尽异常"""
    pass


class Retry:
    """重试装饰器/上下文管理器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.attempts = 0
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.initial_delay
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * attempt
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (2 ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            a, b = 1, 1
            for _ in range(attempt - 1):
                a, b = b, a + b
            delay = float(a)
        else:
            delay = self.config.initial_delay
        
        # 添加抖动
        if self.config.jitter:
            import random
            jitter = delay * self.config.jitter_factor
            delay = delay + random.uniform(-jitter, jitter)
        
        # 限制最大延迟
        return min(delay, self.config.max_delay)
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行带重试的函数"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.attempts = attempt
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise RetryExhausted(
                        f"Retry exhausted after {self.config.max_attempts} attempts"
                    ) from last_exception
        
        raise last_exception


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exceptions: tuple = (Exception,)
):
    """重试装饰器"""
    def decorator(func: Callable):
        retry_instance = Retry(RetryConfig(
            max_attempts=max_attempts,
            initial_delay=delay,
            strategy=strategy
        ))
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_instance.execute(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry_instance.execute(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class ErrorCategory(Enum):
    """错误分类"""
    TRANSIENT = "transient"      # 临时性错误（网络超时）
    RESOURCE = "resource"         # 资源错误（内存不足）
    LOGIC = "logic"              # 逻辑错误（bug）
    CONFIG = "config"            # 配置错误
    AUTH = "auth"                # 认证错误
    RATE_LIMIT = "rate_limit"    # 速率限制


@dataclass
class MAOSError:
    """MAOS错误"""
    code: str
    category: ErrorCategory
    message: str
    details: dict = None
    timestamp: datetime = None
    cause: Optional[Exception] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> dict:
        return {
            'code': self.code,
            'category': self.category.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.error_log: list[MAOSError] = []
        self.error_counts: dict[ErrorCategory, int] = {}
    
    def handle(self, error: Exception, context: dict = None) -> MAOSError:
        """处理错误"""
        category = self._categorize_error(error)
        maos_error = MAOSError(
            code=f"ERR_{category.value.upper()}",
            category=category,
            message=str(error),
            details=context or {},
            cause=error
        )
        
        # 记录错误
        self.error_log.append(maos_error)
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
        
        return maos_error
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_msg = str(error).lower()
        
        if "timeout" in error_msg or "connection" in error_msg:
            return ErrorCategory.TRANSIENT
        elif "memory" in error_msg or "disk" in error_msg:
            return ErrorCategory.RESOURCE
        elif "auth" in error_msg or "permission" in error_msg:
            return ErrorCategory.AUTH
        elif "rate limit" in error_msg or "too many" in error_msg:
            return ErrorCategory.RATE_LIMIT
        elif "config" in error_msg or "invalid" in error_msg:
            return ErrorCategory.CONFIG
        else:
            return ErrorCategory.LOGIC
    
    def get_error_summary(self) -> dict:
        """获取错误摘要"""
        return {
            'total_errors': len(self.error_log),
            'by_category': {
                cat.value: count for cat, count in self.error_counts.items()
            },
            'recent_errors': [
                err.to_dict() for err in self.error_log[-10:]
            ]
        }
