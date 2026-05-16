#!/usr/bin/env python3
"""
MAOS v5.0 - 监控和日志演示
展示监控系统的功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
from datetime import datetime

from maos.monitoring import (
    get_monitoring_system,
    get_logger,
    record_metric,
    LogLevel,
    MetricsCollector,
    StructuredLogger
)


def demo_basic_logging():
    """演示基本日志"""
    print("\n" + "=" * 80)
    print("  1. Basic Logging Demo")
    print("=" * 80)
    
    logger = get_logger("maos.demo")
    
    logger.debug("Debug message with details")
    logger.info("Info message: System started")
    logger.warning("Warning: High memory usage")
    logger.error("Error: Connection failed")
    logger.critical("Critical: System shutdown")
    
    print("\n📋 Recent Logs:")
    logs = logger.get_logs(limit=5)
    for log in logs:
        print(f"   [{log['level']:8}] {log['message']}")


def demo_metrics():
    """演示指标收集"""
    print("\n" + "=" * 80)
    print("  2. Metrics Collection Demo")
    print("=" * 80)
    
    monitor = get_monitoring_system()
    
    # 记录各种指标
    record_metric("api.requests", 1, "counter", {"endpoint": "/api/v1/tasks"})
    record_metric("api.requests", 1, "counter", {"endpoint": "/api/v1/tasks"})
    record_metric("api.latency", 45.5, "histogram", {"endpoint": "/api/v1/tasks"})
    record_metric("api.latency", 32.1, "histogram", {"endpoint": "/api/v1/tasks"})
    record_metric("memory.usage", 1024, "gauge")
    record_metric("cpu.usage", 45.2, "gauge")
    
    print("\n📊 Metrics Summary:")
    summary = monitor.metrics.get_summary()
    
    print(f"\n   Counters:")
    for name, value in summary['counters'].items():
        print(f"      {name}: {value}")
    
    print(f"\n   Gauges:")
    for name, value in summary['gauges'].items():
        print(f"      {name}: {value}")
    
    print(f"\n   Histograms:")
    for name, stats in summary['histograms'].items():
        print(f"      {name}:")
        print(f"         Count: {stats['count']}")
        print(f"         Min: {stats['min']:.2f}ms")
        print(f"         Max: {stats['max']:.2f}ms")
        print(f"         Avg: {stats['avg']:.2f}ms")


def demo_alerts():
    """演示告警系统"""
    print("\n" + "=" * 80)
    print("  3. Alert System Demo")
    print("=" * 80)
    
    monitor = get_monitoring_system()
    
    # 创建告警
    alert1 = monitor.create_alert(
        name="HighCPU",
        message="CPU usage above 90%",
        severity="warning",
        cpu_usage=92.5
    )
    
    alert2 = monitor.create_alert(
        name="DatabaseConnection",
        message="Database connection timeout",
        severity="error",
        retry_count=3
    )
    
    print(f"\n   ⚠️  Created 2 alerts:")
    print(f"      1. {alert1['name']}: {alert1['message']}")
    print(f"      2. {alert2['name']}: {alert2['message']}")
    
    # 确认告警
    monitor.acknowledge_alert(alert1['id'])
    print(f"\n   ✅ Acknowledged alert: {alert1['name']}")
    
    # 显示活跃告警
    active = [a for a in monitor.alerts if not a['acknowledged']]
    print(f"\n   📊 Active Alerts: {len(active)}")


def demo_monitoring_system():
    """演示完整监控系统"""
    print("\n" + "=" * 80)
    print("  4. Complete Monitoring System")
    print("=" * 80)
    
    monitor = get_monitoring_system()
    
    # 记录一些指标
    for i in range(5):
        record_metric("requests.total", 1, "counter")
        record_metric("response.time", 100 + i * 10, "histogram")
        time.sleep(0.01)
    
    # 获取仪表板数据
    dashboard = monitor.get_dashboard_data()
    
    print("\n📊 Dashboard Data:")
    print(f"   Timestamp: {dashboard['timestamp']}")
    print(f"   Metrics Count: {dashboard['metrics_summary']['total_metrics']}")
    print(f"   Active Alerts: {dashboard['active_alerts']}")
    print(f"   Loggers: {dashboard['loggers_count']}")


import json

def demo_structured_logging():
    """演示结构化日志"""
    print("\n" + "=" * 80)
    print("  5. Structured Logging Demo")
    print("=" * 80)
    
    logger = get_logger("maos.structured")
    
    # 结构化日志
    logger.info(
        "User action",
        user_id="user-123",
        action="login",
        ip_address="192.168.1.100",
        success=True
    )
    
    logger.error(
        "Request failed",
        endpoint="/api/v1/tasks",
        method="POST",
        status_code=500,
        error_message="Internal server error"
    )
    
    print("\n📋 Structured Logs:")
    logs = logger.get_logs(limit=2)
    for log in logs:
        print(f"\n   [{log['level']}] {log['message']}")
        print(f"   Metadata: {json.dumps(log['metadata'], indent=6)}")


def main():
    """主函数"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║         MAOS v5.0 - Monitoring & Logging System Demo                     ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    import json
    
    demo_basic_logging()
    demo_metrics()
    demo_alerts()
    demo_monitoring_system()
    demo_structured_logging()
    
    print("\n" + "=" * 80)
    print("  🎉 Monitoring Demo Complete!")
    print("=" * 80)
    print("\n📚 Next Steps:")
    print("   - Explore maos/monitoring.py for implementation")
    print("   - Integrate with FastAPI for request logging")
    print("   - Add Prometheus exporter for metrics")
    print("   - Implement alerting webhooks")
    print("")


if __name__ == "__main__":
    main()
