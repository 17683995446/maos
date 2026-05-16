"""
MAOS v5.0 - 配置管理系统
集成了环境变量、配置文件和默认配置
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class MAOSConfig:
    """MAOS系统配置"""
    
    # 系统配置
    system_name: str = "MAOS"
    system_version: str = "5.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Orchestrator配置
    max_concurrent_tasks: int = 10
    execution_strategy: str = "HYBRID"
    enable_streaming: bool = True
    
    # Agent配置
    default_agent_timeout: int = 300  # 秒
    
    # 存储配置
    storage_backend: str = "memory"  # memory, redis, postgresql
    storage_ttl: int = 3600  # 秒
    auto_cleanup: bool = True
    
    # 分析配置
    enable_analytics: bool = True
    metrics_retention: int = 86400  # 秒 (1天)
    anomaly_detection_enabled: bool = True
    
    # 多租户配置
    enable_multi_tenancy: bool = True
    default_isolation_strategy: str = "SHARED_ROW"
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    enable_cors: bool = True
    
    # 高级配置
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60  # 秒
    
    @classmethod
    def from_env(cls) -> 'MAOSConfig':
        """从环境变量创建配置"""
        return cls(
            system_name=os.getenv("MAOS_SYSTEM_NAME", "MAOS"),
            debug=os.getenv("MAOS_DEBUG", "false").lower() == "true",
            log_level=os.getenv("MAOS_LOG_LEVEL", "INFO"),
            max_concurrent_tasks=int(os.getenv("MAOS_MAX_TASKS", "10")),
            execution_strategy=os.getenv("MAOS_EXECUTION_STRATEGY", "HYBRID"),
            storage_backend=os.getenv("MAOS_STORAGE_BACKEND", "memory"),
            storage_ttl=int(os.getenv("MAOS_STORAGE_TTL", "3600")),
            api_host=os.getenv("MAOS_API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("MAOS_API_PORT", "8000")),
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'MAOSConfig':
        """从配置文件创建配置"""
        try:
            import json
            config_data = json.loads(Path(config_path).read_text())
            return cls(**config_data)
        except Exception:
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "system_name": self.system_name,
            "system_version": self.system_version,
            "debug": self.debug,
            "log_level": self.log_level,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "execution_strategy": self.execution_strategy,
            "enable_streaming": self.enable_streaming,
            "default_agent_timeout": self.default_agent_timeout,
            "storage_backend": self.storage_backend,
            "storage_ttl": self.storage_ttl,
            "auto_cleanup": self.auto_cleanup,
            "enable_analytics": self.enable_analytics,
            "metrics_retention": self.metrics_retention,
            "anomaly_detection_enabled": self.anomaly_detection_enabled,
            "enable_multi_tenancy": self.enable_multi_tenancy,
            "default_isolation_strategy": self.default_isolation_strategy,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "enable_cors": self.enable_cors,
            "enable_circuit_breaker": self.enable_circuit_breaker,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "circuit_breaker_timeout": self.circuit_breaker_timeout,
        }


# 全局配置实例
_config_instance: Optional[MAOSConfig] = None


def get_config() -> MAOSConfig:
    """获取全局配置"""
    global _config_instance
    if _config_instance is None:
        _config_instance = MAOSConfig.from_env()
    return _config_instance


def set_config(config: MAOSConfig) -> None:
    """设置全局配置"""
    global _config_instance
    _config_instance = config
