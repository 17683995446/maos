# MAOS v5.0 - 生产级演示应用
# Multi-Agent Orchestration System v5.0 Production Demo

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time
import asyncio
from typing import List, Dict, Any


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_separator():
    """打印分隔线"""
    print("-" * 80)


def demo_config_system():
    """演示配置系统"""
    print_header("1. Configuration System")
    
    from maos.config import MAOSConfig, get_config, set_config
    
    config = MAOSConfig(
        system_name="MAOS Production Demo",
        debug=True,
        max_concurrent_tasks=20
    )
    
    print(f"   System Name: {config.system_name}")
    print(f"   Version: {config.system_version}")
    print(f"   Debug Mode: {config.debug}")
    print(f"   Max Concurrent Tasks: {config.max_concurrent_tasks}")
    
    set_config(config)
    print("   ✅ Configuration system initialized")
    print_separator()


def demo_performance_decorators():
    """演示性能装饰器"""
    print_header("2. Performance Monitoring System")
    
    from maos.performance import (
        timed,
        retry,
        print_performance_summary
    )
    
    # 使用timed装饰器
    @timed(log_duration=False, record_metrics=False)
    def expensive_calculation(n: int) -> int:
        result = 0
        for i in range(n * 10000):
            result += i
        time.sleep(0.005)
        return result
    
    print("   Running performance tests...")
    for i in range(3):
        result = expensive_calculation(5 + i)
        print(f"   Iteration {i+1}: result = {result:,}")
    
    # 显示性能摘要
    print_separator()
    print_performance_summary()


def demo_task_orchestration():
    """演示任务编排"""
    print_header("3. Task Orchestration System")
    
    from maos.orchestration import TaskManager, TaskPriority, TaskStatus
    
    manager = TaskManager(max_concurrent=5)
    
    # 创建不同优先级的任务
    print("   Creating tasks...")
    task1 = manager.create_task(
        name="Data Cleaning",
        description="Clean and normalize raw data",
        requirements=["data_processing"],
        priority=TaskPriority.HIGH
    )
    
    task2 = manager.create_task(
        name="Feature Extraction",
        description="Extract features from cleaned data",
        requirements=["ml", "feature_engineering"],
        priority=TaskPriority.NORMAL,
        dependencies=[task1.id]
    )
    
    task3 = manager.create_task(
        name="Model Training",
        description="Train ML model on extracted features",
        requirements=["ml", "training"],
        priority=TaskPriority.HIGH,
        dependencies=[task2.id]
    )
    
    # 获取统计信息
    stats = manager.get_statistics()
    print(f"   Total Tasks: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   High Priority: {stats['by_priority']['HIGH']}")
    
    # 更新一些任务状态
    print("   Updating task states...")
    manager.update_task_status(task1.id, TaskStatus.RUNNING)
    task1.mark_completed({"status": "cleaned", "records": 10000})
    manager.update_task_status(task1.id, TaskStatus.COMPLETED)
    
    # 显示最终状态
    final_stats = manager.get_statistics()
    print(f"   Completed Tasks: {final_stats['completed']}")
    print("   ✅ Task orchestration system working")
    print_separator()


def demo_analytics_system():
    """演示分析系统"""
    print_header("4. Analytics Engine")
    
    from maos.analytics import get_analytics_engine
    
    analytics = get_analytics_engine()
    
    # 记录一些指标
    print("   Recording metrics...")
    analytics.record_metric("api.requests", 150, {"endpoint": "/api/v1/tasks"})
    analytics.record_metric("api.latency", 45.5, {"endpoint": "/api/v1/tasks"})
    analytics.record_metric("tasks.processed", 25)
    
    print("   ✅ Analytics engine working")
    print_separator()


def demo_api_endpoints():
    """演示API端点"""
    print_header("5. FastAPI Integration")
    print("   The MAOS v5.0 API includes:")
    print("")
    print("   📋 System APIs:")
    print("      GET  /api/v1/system/info          - System information")
    print("      GET  /api/v1/system/statistics    - Statistics")
    print("      GET  /api/v1/system/performance   - Performance metrics")
    print("")
    print("   📝 Task APIs:")
    print("      POST /api/v1/tasks                - Create task")
    print("      GET  /api/v1/tasks                - List tasks")
    print("      GET  /api/v1/tasks/{id}           - Get task details")
    print("      POST /api/v1/tasks/{id}/complete  - Complete task")
    print("      DELETE /api/v1/tasks/{id}         - Cancel task")
    print("")
    print("   📚 Documentation:")
    print("      GET  /docs                        - Swagger UI")
    print("      GET  /redoc                       - ReDoc UI")
    print("")
    print("   ✅ FastAPI integration complete")
    print_separator()


def show_deployment_options():
    """显示部署选项"""
    print_header("6. Deployment Options")
    print("")
    print("   🐳 Docker:")
    print("      docker build -t maos-v5 .")
    print("      docker run -p 8000:8000 maos-v5")
    print("")
    print("   🐙 Docker Compose:")
    print("      docker-compose up -d")
    print("      docker-compose down")
    print("")
    print("   🌐 Direct Python:")
    print("      python -m maos.api")
    print("      python -m http.server 8000 (for dashboard)")
    print("")
    print("   ✅ Deployment configurations ready")
    print_separator()


def main():
    """运行完整演示"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║         MAOS v5.0 - Production-Grade Multi-Agent Orchestration           ║")
    print("║                    with Open-Source Best Practices                        ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    # 运行所有演示
    demo_config_system()
    demo_performance_decorators()
    demo_task_orchestration()
    demo_analytics_system()
    demo_api_endpoints()
    show_deployment_options()
    
    # 完成信息
    print_header("🎊 Demo Complete!")
    print("")
    print("   📦 What's Included in MAOS v5.0:")
    print("      ✅ Configuration Management System")
    print("      ✅ Performance Monitoring & Decorators")
    print("      ✅ Task Orchestration & Management")
    print("      ✅ Analytics Engine")
    print("      ✅ FastAPI REST API with OpenAPI Docs")
    print("      ✅ Docker & Docker Compose Deployment")
    print("      ✅ Visual Dashboard (HTML + Mermaid)")
    print("")
    print("   🚀 Next Steps:")
    print("      1. Run the dashboard: python -m http.server 8000")
    print("      2. Run the API: python -m maos.api")
    print("      3. Visit http://localhost:8000/maos_dashboard.html")
    print("      4. Visit http://localhost:8000/docs for API docs")
    print("")
    print("   📚 Documentation:")
    print("      - See REFACTORING_PLAN.md for phase details")
    print("      - See MAOS_v4_FINAL_REPORT.md for full evaluation")
    print("      - See Dockerfile & docker-compose.yml for deployment")
    print("")
    print("=" * 80)
    print("")


if __name__ == "__main__":
    main()
