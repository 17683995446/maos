"""
日志工具模块
提供结构化日志、彩色输出、日志级别控制和格式化功能
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class Fore:
        RED = RESET = CYAN = MAGENTA = YELLOW = GREEN = BLUE = WHITE = DIM = BRIGHT = ""
    class Style:
        RESET_ALL = DIM = BRIGHT = NORMAL = ""


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """日志格式枚举"""
    SIMPLE = "simple"
    STANDARD = "standard"
    JSON = "json"
    DETAILED = "detailed"


class Logger:
    """
    结构化日志工具类

    支持功能：
    - 多种日志级别
    - 彩色终端输出
    - 结构化JSON输出
    - 自定义格式化
    - 文件输出
    - 模块隔离

    示例：
        logger = Logger("my_app")
        logger.info("User logged in", user_id="123", action="login")
        logger.error("Failed to process", error_code=500, details={"retry": True})
    """

    _instances: Dict[str, 'Logger'] = {}
    _default_logger: Optional['Logger'] = None

    def __init__(
        self,
        name: str,
        level: Union[int, LogLevel] = LogLevel.INFO,
        log_format: LogFormat = LogFormat.STANDARD,
        use_colors: bool = True,
        log_file: Optional[Union[str, Path]] = None,
        enable_json: bool = False,
        include_caller_info: bool = False,
    ):
        """
        初始化日志记录器

        参数：
            name: 日志记录器名称
            level: 日志级别
            log_format: 日志格式
            use_colors: 是否使用彩色输出
            log_file: 日志文件路径（可选）
            enable_json: 是否启用JSON格式输出
            include_caller_info: 是否包含调用者信息
        """
        self.name = name
        self.level = level.value if isinstance(level, LogLevel) else level
        self.log_format = log_format
        self.use_colors = use_colors and COLORAMA_AVAILABLE
        self.enable_json = enable_json
        self.include_caller_info = include_caller_info

        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.level)
        self._logger.handlers.clear()

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        self._console_handler = console_handler
        self._logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(self.level)
            self._logger.addHandler(file_handler)

        self._structured_logging = StructuredLogger(name, level=self.level)

    @classmethod
    def get_logger(
        cls,
        name: str = "maos",
        **kwargs
    ) -> 'Logger':
        """
        获取或创建日志记录器实例

        参数：
            name: 日志记录器名称
            **kwargs: 其他配置参数

        返回：
            Logger实例
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
        return cls._instances[name]

    @classmethod
    def get_default_logger(cls) -> 'Logger':
        """获取默认日志记录器"""
        if cls._default_logger is None:
            cls._default_logger = cls.get_logger("maos")
        return cls._default_logger

    def _format_message(
        self,
        level: str,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        caller_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        格式化日志消息

        参数：
            level: 日志级别
            message: 日志消息
            extra_data: 附加数据
            caller_info: 调用者信息

        返回：
            格式化的消息字符串
        """
        timestamp = datetime.now().isoformat()

        if self.log_format == LogFormat.JSON or self.enable_json:
            data = {
                "timestamp": timestamp,
                "level": level,
                "logger": self.name,
                "message": message,
            }
            if extra_data:
                data["data"] = extra_data
            if caller_info:
                data["caller"] = caller_info
            return json.dumps(data, ensure_ascii=False, default=str)

        elif self.log_format == LogFormat.SIMPLE:
            return f"[{timestamp}] {message}"

        elif self.log_format == LogFormat.DETAILED:
            parts = [f"[{timestamp}] [{level.upper()}] [{self.name}]"]
            if caller_info:
                parts.append(f"{caller_info['file']}:{caller_info['line']} in {caller_info['function']}")
            parts.append(message)
            if extra_data:
                parts.append(f"Data: {json.dumps(extra_data, ensure_ascii=False, default=str)}")
            return " | ".join(parts)

        else:
            level_color = self._get_level_color(level)
            return f"{level_color}[{timestamp}] [{level.upper()}] {message}{Style.RESET_ALL}"

    def _get_level_color(self, level: str) -> str:
        """获取日志级别对应的颜色"""
        if not self.use_colors:
            return ""

        colors = {
            "DEBUG": Fore.DIM + Fore.WHITE,
            "INFO": Fore.CYAN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Fore.RED + Style.BRIGHT,
        }
        return colors.get(level.upper(), "")

    def log(self, level: int, message: str, *args, **kwargs) -> None:
        """
        通用的日志方法

        参数：
            level: 日志级别
            message: 日志消息
            *args: 位置参数
            **kwargs: 关键字参数
        """
        extra_data = kwargs.pop("extra", None)
        level_name = logging.getLevelName(level)
        self._log(level, level_name, message, *args, extra=extra_data, **kwargs)

    def _log(
        self,
        level: int,
        level_name: str,
        message: str,
        *args,
        **kwargs
    ) -> None:
        """内部日志方法"""
        extra_data = kwargs.pop("extra", None)
        caller_info = None

        if self.include_caller_info:
            import traceback
            stack = traceback.extract_stack()
            for frame in reversed(stack[:-2]):
                if frame.filename != __file__:
                    caller_info = {
                        "file": Path(frame.filename).name,
                        "line": frame.lineno,
                        "function": frame.name,
                    }
                    break

        formatted_message = self._format_message(level_name, message, extra_data, caller_info)
        self._logger.log(level, formatted_message, *args)

    def debug(self, message: str, *args, **kwargs) -> None:
        """记录调试日志"""
        self._log(logging.DEBUG, "DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """记录信息日志"""
        self._log(logging.INFO, "INFO", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """记录警告日志"""
        self._log(logging.WARNING, "WARNING", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """记录错误日志"""
        self._log(logging.ERROR, "ERROR", message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """记录严重错误日志"""
        self._log(logging.CRITICAL, "CRITICAL", message, *args, **kwargs)

    def log_structured(
        self,
        level: Union[str, int],
        message: str,
        **kwargs
    ) -> None:
        """
        记录结构化日志

        参数：
            level: 日志级别
            message: 日志消息
            **kwargs: 结构化数据字段
        """
        self._structured_logging.log(level, message, **kwargs)

    def set_level(self, level: Union[int, LogLevel]) -> None:
        """
        设置日志级别

        参数：
            level: 日志级别
        """
        self.level = level.value if isinstance(level, LogLevel) else level
        self._logger.setLevel(self.level)
        self._console_handler.setLevel(self.level)

    def add_file_handler(
        self,
        log_file: Union[str, Path],
        level: Optional[Union[int, LogLevel]] = None,
        format: Optional[LogFormat] = None,
    ) -> None:
        """
        添加文件处理器

        参数：
            log_file: 日志文件路径
            level: 日志级别（可选）
            format: 日志格式（可选）
        """
        handler = logging.FileHandler(log_file)
        handler.setLevel(level.value if isinstance(level, LogLevel) else (level or self.level))
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self._logger.addHandler(handler)


class StructuredLogger:
    """
    结构化日志记录器

    提供键值对形式的数据日志记录，便于日志分析和监控。
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        初始化结构化日志记录器

        参数：
            name: 日志记录器名称
            level: 日志级别
        """
        self.name = name
        self.logger = logging.getLogger(f"{name}.structured")
        self.logger.setLevel(level)

    def log(
        self,
        level: Union[str, int],
        message: str,
        **kwargs
    ) -> None:
        """
        记录结构化日志

        参数：
            level: 日志级别
            message: 日志消息
            **kwargs: 结构化数据字段
        """
        data = {
            "logger": self.name,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            **kwargs
        }
        log_level = level.value if isinstance(level, LogLevel) else level
        self.logger.log(log_level, json.dumps(data, ensure_ascii=False, default=str))


class LogContext:
    """
    日志上下文管理器

    在上下文中添加额外的日志字段。

    示例：
        logger = Logger.get_logger()
        with LogContext(logger, request_id="123", user_id="456"):
            logger.info("Processing request")
    """

    def __init__(
        self,
        logger: Logger,
        **context
    ):
        """
        初始化日志上下文

        参数：
            logger: Logger实例
            **context: 上下文字段
        """
        self.logger = logger
        self.context = context
        self._previous_extra = None

    def __enter__(self):
        self._previous_extra = getattr(self.logger, '_current_extra', {})
        self.logger._current_extra = {**self._previous_extra, **self.context}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger._current_extra = self._previous_extra
        return False


class Timer:
    """
    日志计时器

    用于测量代码执行时间。

    示例：
        with Timer(logger, "operation_name"):
            # 执行操作
            pass
    """

    def __init__(
        self,
        logger: Optional[Logger] = None,
        name: str = "operation",
        log_on_exit: bool = True,
        level: int = logging.INFO,
    ):
        """
        初始化计时器

        参数：
            logger: Logger实例（可选）
            name: 计时器名称
            log_on_exit: 退出时是否记录时间
            level: 日志级别
        """
        self.logger = logger or Logger.get_default_logger()
        self.name = name
        self.log_on_exit = log_on_exit
        self.level = level
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.log_on_exit:
            _elapsed_ms = (self.end_time - self.start_time) * 1000
            self.logger.log(
                self.level,
                f"{self.name} took {_elapsed_ms:.2f}ms",
                extra={"operation": self.name, "duration_ms": _elapsed_ms}
            )
        return False

    def elapsed(self) -> float:
        """获取经过的时间（秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    def elapsed_ms(self) -> float:
        """获取经过的时间（毫秒）"""
        return self.elapsed() * 1000


def setup_logging(
    level: Union[int, str, LogLevel] = LogLevel.INFO,
    log_format: LogFormat = LogFormat.STANDARD,
    log_file: Optional[Union[str, Path]] = None,
    enable_json: bool = False,
) -> Logger:
    """
    配置全局日志系统

    参数：
        level: 日志级别
        log_format: 日志格式
        log_file: 日志文件路径（可选）
        enable_json: 是否启用JSON输出

    返回：
        配置好的Logger实例
    """
    if isinstance(level, str):
        level = LogLevel[level.upper()]

    logger = Logger.get_logger(
        "maos",
        level=level,
        log_format=log_format,
        log_file=log_file,
        enable_json=enable_json,
        include_caller_info=True,
    )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return logger


__all__ = [
    "Logger",
    "StructuredLogger",
    "LogContext",
    "Timer",
    "LogLevel",
    "LogFormat",
    "setup_logging",
]
