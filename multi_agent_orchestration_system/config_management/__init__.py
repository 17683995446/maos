"""
Configuration Management Module
=========================

This module provides type-safe configuration management using Pydantic Settings.
It supports environment variables, .env files, and provides sensible defaults.

Architecture:
  - ApplicationConfig: Main configuration class
  - DatabaseConfig: Database-specific settings
  - RedisConfig: Redis/messaging settings
  - MonitoringConfig: Observability settings
  - APIConfig: API server settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class MessagingConfiguration(BaseSettings):
    """Message broker configuration for distributed communication"""
    
    model_config = SettingsConfigDict(env_prefix='MAOS_REDIS_')
    
    host: str = "localhost"
    port: int = 6379
    database_index: int = 0
    password: Optional[str] = None
    connection_url: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    @property
    def get_connection_url(self) -> str:
        """Construct Redis connection URL from components"""
        if self.connection_url:
            return self.connection_url
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database_index}"


class MonitoringConfiguration(BaseSettings):
    """Observability and monitoring configuration"""
    
    model_config = SettingsConfigDict(env_prefix='MAOS_MONITORING_')
    
    prometheus_port: int = 9090
    prometheus_enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    log_file_path: Optional[str] = None
    enable_structured_logging: bool = True
    enable_metrics: bool = True
    metrics_prefix: str = "maos"


class TaskQueueConfiguration(BaseSettings):
    """Task queue and scheduling configuration"""
    
    model_config = SettingsConfigDict(env_prefix='MAOS_QUEUE_')
    
    default_timeout_seconds: int = 300
    max_retry_attempts: int = 3
    retry_backoff_multiplier: int = 2
    initial_retry_delay_seconds: int = 10
    task_result_ttl_seconds: int = 86400
    max_concurrent_tasks: int = 10
    enable_dead_letter_queue: bool = True
    dead_letter_queue_name: str = "maos_dlq"


class ApplicationServerConfiguration(BaseSettings):
    """API server and web interface configuration"""
    
    model_config = SettingsConfigDict(env_prefix='MAOS_API_')
    
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload_enabled: bool = False
    cors_enabled: bool = True
    cors_allow_origins: str = "*"
    cors_allow_credentials: bool = True
    max_request_size_mb: int = 100
    request_timeout_seconds: int = 60
    enable_docs: bool = True
    enable_redoc: bool = True


class ApplicationConfiguration(BaseSettings):
    """
    Main application configuration that ties all sub-configurations together.
    Loads from environment variables with .env file support.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    application_name: str = "Multi-Agent Orchestration System"
    application_version: str = "2.0.0"
    application_description: str = "Enterprise-grade multi-agent orchestration platform"
    debug_mode: bool = False
    environment: str = "production"
    
    messaging: MessagingConfiguration = MessagingConfiguration()
    monitoring: MonitoringConfiguration = MonitoringConfiguration()
    task_queue: TaskQueueConfiguration = TaskQueueConfiguration()
    api: ApplicationServerConfiguration = ApplicationServerConfiguration()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"
    
    def get_metrics_endpoint(self) -> str:
        """Get Prometheus metrics endpoint URL"""
        if self.monitoring.prometheus_enabled:
            return f"http://{self.api.host}:{self.monitoring.prometheus_port}/metrics"
        return ""


@lru_cache()
def get_application_configuration() -> ApplicationConfiguration:
    """
    Get cached application configuration instance (singleton pattern).
    This ensures configuration is only loaded once and reused.
    """
    return ApplicationConfiguration()


configuration = get_application_configuration()
