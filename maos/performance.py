"""
MAOS v5.0 - 性能监控和装饰器系统
集成了函数计时、性能分析和指标记录
"""

import time
import functools
import asyncio
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass
from collections import defaultdict

from maos.utils import Logger
from maos.analytics import get_analytics_engine


logger = Logger.get_logger("maos.performance")


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    errors: int = 0
    
    def record(self, duration: float, is_error: bool = False) -> None:
        """记录一次调用"""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.call_count
        if is_error:
            self.errors += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "function_name": self.function_name,
            "call_count": self.call_count,
            "total_time": self.total_time,
            "min_time": self.min_time if self.min_time != float('inf') else 0.0,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "errors": self.errors,
        }


# 全局性能指标存储
_performance_metrics: Dict[str, PerformanceMetrics] = {}


def get_performance_metrics(function_name: str) -> Optional[PerformanceMetrics]:
    """获取函数的性能指标"""
    return _performance_metrics.get(function_name)


def get_all_performance_metrics() -> Dict[str, PerformanceMetrics]:
    """获取所有性能指标"""
    return dict(_performance_metrics)


def timed(
    func: Optional[Callable] = None,
    *,
    record_metrics: bool = True,
    log_duration: bool = True,
    log_level: str = "DEBUG"
):
    """
    函数计时装饰器
    
    Args:
        func: 被装饰的函数
        record_metrics: 是否记录指标到分析引擎
        log_duration: 是否记录耗时到日志
        log_level: 日志级别
    """
    def decorator(fn):
        metrics = PerformanceMetrics(function_name=fn.__qualname__)
        _performance_metrics[fn.__qualname__] = metrics
        
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            is_error = False
            
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception:
                is_error = True
                raise
            finally:
                duration = time.time() - start_time
                metrics.record(duration, is_error)
                
                if log_duration:
                    log_func = getattr(logger, log_level.lower(), logger.debug)
                    log_func(f"Function {fn.__qualname__} took {duration:.4f}s")
                
                if record_metrics:
                    try:
                        analytics = get_analytics_engine()
                        analytics.record_metric(
                            f"function.{fn.__name__}.duration",
                            duration,
                            labels={"function": fn.__name__}
                        )
                        analytics.record_metric(
                            f"function.{fn.__name__}.calls",
                            1,
                            labels={"function": fn.__name__}
                        )
                    except Exception:
                        pass
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


def async_timed(
    func: Optional[Callable] = None,
    *,
    record_metrics: bool = True,
    log_duration: bool = True,
    log_level: str = "DEBUG"
):
    """
    异步函数计时装饰器
    
    Args:
        func: 被装饰的异步函数
        record_metrics: 是否记录指标到分析引擎
        log_duration: 是否记录耗时到日志
        log_level: 日志级别
    """
    def decorator(fn):
        metrics = PerformanceMetrics(function_name=fn.__qualname__)
        _performance_metrics[fn.__qualname__] = metrics
        
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            is_error = False
            
            try:
                result = await fn(*args, **kwargs)
                return result
            except Exception:
                is_error = True
                raise
            finally:
                duration = time.time() - start_time
                metrics.record(duration, is_error)
                
                if log_duration:
                    log_func = getattr(logger, log_level.lower(), logger.debug)
                    log_func(f"Async function {fn.__qualname__} took {duration:.4f}s")
                
                if record_metrics:
                    try:
                        analytics = get_analytics_engine()
                        analytics.record_metric(
                            f"function.{fn.__name__}.duration",
                            duration,
                            labels={"function": fn.__name__}
                        )
                        analytics.record_metric(
                            f"function.{fn.__name__}.calls",
                            1,
                            labels={"function": fn.__name__}
                        )
                    except Exception:
                        pass
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍数
        exceptions: 要重试的异常类型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay:.2f}s"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步重试装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay:.2f}s"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def print_performance_summary() -> None:
    """打印性能摘要"""
    if not _performance_metrics:
        print("No performance metrics available")
        return
    
    print("\n" + "=" * 80)
    print("Performance Summary".center(80))
    print("=" * 80)
    print(f"{'Function':<40} {'Calls':>8} {'Avg (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10} {'Errors':>8}")
    print("-" * 80)
    
    for name, metrics in sorted(_performance_metrics.items(), key=lambda x: x[1].call_count, reverse=True):
        print(
            f"{name[:38]:<40} "
            f"{metrics.call_count:>8} "
            f"{metrics.avg_time*1000:>10.2f} "
            f"{metrics.min_time*1000:>10.2f} "
            f"{metrics.max_time*1000:>10.2f} "
            f"{metrics.errors:>8}"
        )
    
    print("-" * 80 + "\n")
