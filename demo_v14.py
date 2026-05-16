#!/usr/bin/env python3
"""
MAOS v14.0 - Complete Demo
MAOS v14.0 完整演示
"""

import asyncio
from datetime import datetime, timedelta


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║         🚀  MAOS v14.0 - Multi-Language SDK & Advanced Analytics               ║
║                                                                                ║
║         New Features: SDK v2, Version Control, Analytics, Mobile API          ║
║                                                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def demo_sdk():
    """演示多语言 SDK"""
    print("\n" + "="*80)
    print("  1. Multi-Language SDK Demo")
    print("="*80 + "\n")
    
    from maos.sdk.v14 import SDKFactory, SDKLanguage, SDKGenerator
    
    print("🔧 Generating SDK code for multiple languages...")
    
    languages = [SDKLanguage.PYTHON, SDKLanguage.JAVASCRIPT, SDKLanguage.GO, SDKLanguage.JAVA, SDKLanguage.RUST]
    
    for lang in languages:
        generator = SDKGenerator(lang)
        code = generator.generate_client()
        print(f"\n✅ Generated {lang.value} SDK code (first 10 lines):")
        lines = code.split('\n')[:10]
        for line in lines:
            print(f"   {line}")
    
    print("\n📦 Creating SDK instance...")
    sdk = SDKFactory.create(SDKLanguage.PYTHON, "test-api-key-123")
    print(f"   SDK created: {sdk.__class__.__name__}")


def demo_version_control():
    """演示版本控制与 A/B 测试"""
    print("\n" + "="*80)
    print("  2. Version Control & A/B Testing Demo")
    print("="*80 + "\n")
    
    from maos.version.v14 import VersionManager, ABTestManager, ABTestStatus
    
    version_manager = VersionManager()
    ab_test_manager = ABTestManager(version_manager)
    
    print("📝 Creating workflow versions...")
    
    v1 = version_manager.create_version(
        workflow_id="wf-order-processing",
        version="1.0",
        name="Initial Release",
        definition={"steps": {"validate": {}, "process": {}, "fulfill": {}}},
        changelog="Initial version"
    )
    
    v2 = version_manager.create_version(
        workflow_id="wf-order-processing",
        version="2.0",
        name="Optimized Release",
        definition={"steps": {"validate": {}, "process": {"optimized": True}, "fulfill": {}, "notify": {}}},
        parent_version_id=v1.id,
        changelog="Added notification step and optimized processing"
    )
    
    v3 = version_manager.create_version(
        workflow_id="wf-order-processing",
        version="2.1",
        name="Bug Fix Release",
        definition={"steps": {"validate": {}, "process": {"optimized": True}, "fulfill": {}, "notify": {}}},
        parent_version_id=v2.id,
        changelog="Fixed notification bug"
    )
    
    print(f"\n✅ Created versions: {[v.version for v in version_manager.get_workflow_versions('wf-order-processing')]}")
    
    print("\n🔄 Activating version 2.0...")
    version_manager.activate_version(v2.id)
    
    print("\n🔍 Comparing versions 1.0 vs 2.0...")
    diff = version_manager.compare_versions(v1.id, v2.id)
    print(f"   Added steps: {diff.added_steps}")
    print(f"   Removed steps: {diff.removed_steps}")
    
    print("\n🧪 Creating A/B Test...")
    ab_test = ab_test_manager.create_test(
        name="Order Processing Performance",
        workflow_id="wf-order-processing",
        variants=[
            {"name": "Control (v2.0)", "version_id": v2.id, "weight": 50},
            {"name": "Variant (v2.1)", "version_id": v3.id, "weight": 50}
        ],
        description="Test performance difference between v2.0 and v2.1"
    )
    
    print(f"   Test created: {ab_test.name}")
    
    print("\n🚀 Starting A/B Test...")
    ab_test_manager.start_test(ab_test.id)
    
    print("\n📊 Simulating traffic allocation...")
    users = ["user-1", "user-2", "user-3", "user-4", "user-5"]
    for user in users:
        variant = ab_test_manager.select_variant(ab_test.id, user)
        print(f"   User {user} → {variant.name}")
        ab_test_manager.record_result(
            ab_test.id,
            variant.id,
            success=True,
            execution_time_ms=150 + (50 if variant.name == "Control (v2.0)" else 30)
        )
    
    results = ab_test_manager.get_test_results(ab_test.id)
    print("\n📈 Test results:")
    for result in results:
        print(f"   {result.variant_name}: {result.user_count} users, {result.conversion_rate*100:.1f}% conversion, {result.avg_execution_time_ms:.1f}ms")
    
    best = ab_test_manager.get_best_variant(ab_test.id)
    print(f"\n🏆 Best variant: {best.variant_name} (conversion: {best.conversion_rate*100:.1f}%)")
    
    ab_test_manager.complete_test(ab_test.id)


def demo_analytics():
    """演示高级分析与可视化"""
    print("\n" + "="*80)
    print("  3. Advanced Analytics & Visualization Demo")
    print("="*80 + "\n")
    
    from maos.analytics.v14 import AnalyticsEngine, ChartType, TimeRange
    
    engine = AnalyticsEngine()
    
    print("📊 Recording metrics...")
    now = datetime.now()
    for i in range(24):
        engine.record_metric("executions", 100 + i * 5 + (i % 3) * 20, now - timedelta(hours=24 - i))
        engine.record_metric("errors", 2 + (i % 4), now - timedelta(hours=24 - i))
        engine.record_metric("latency_ms", 150 + i * 3 + (i % 5) * 10, now - timedelta(hours=24 - i))
        engine.record_metric("throughput", 50 + i * 2, now - timedelta(hours=24 - i))
        engine.record_metric("cost_usd", 10 + i * 0.5, now - timedelta(hours=24 - i))
    
    print("✅ Metrics recorded")
    
    print("\n📈 Getting summaries...")
    summaries = [
        engine.calculate_summary("executions"),
        engine.calculate_summary("errors"),
        engine.calculate_summary("latency_ms"),
        engine.calculate_summary("throughput"),
        engine.calculate_summary("cost_usd"),
    ]
    
    for summary in summaries:
        trend = "📈" if summary.trend == "up" else "📉" if summary.trend == "down" else "➡️"
        print(f"   {summary.name}: {summary.value} ({trend} {summary.change_percent:+.1f}%)")
    
    print("\n📋 Generating report...")
    report = engine.generate_report("Daily Operations Report")
    print(f"   Report: {report.title}")
    print(f"   Insights: {len(report.insights)}")
    for insight in report.insights:
        print(f"     • {insight}")
    print(f"   Recommendations: {len(report.recommendations)}")
    for rec in report.recommendations:
        print(f"     • {rec}")
    
    print("\n🖼️ Creating dashboard...")
    dashboard = engine.create_dashboard("Operations Dashboard")
    engine.add_widget(dashboard.id, "Executions", ChartType.LINE, "executions")
    engine.add_widget(dashboard.id, "Errors", ChartType.BAR, "errors")
    engine.add_widget(dashboard.id, "Latency", ChartType.LINE, "latency_ms")
    
    print(f"   Dashboard created with {len(dashboard.widgets)} widgets")


def demo_mobile():
    """演示移动端API"""
    print("\n" + "="*80)
    print("  4. Mobile API Demo")
    print("="*80 + "\n")
    
    from maos.mobile.v14 import MobileAPIManager, MobileOptimizedAPI, MobilePlatform, PushNotification, PushNotificationType
    
    api_manager = MobileAPIManager()
    mobile_api = MobileOptimizedAPI(api_manager)
    
    print("📱 Authenticating user...")
    auth_result = mobile_api.authenticate("user-123", "device-token-abc123", "ios")
    print(f"   Token: {auth_result['token'][:20]}...")
    
    print("\n📊 Getting mobile dashboard...")
    dashboard = mobile_api.get_dashboard(auth_result['token'])
    print(f"   Workflows: {len(dashboard['workflows'])}")
    print(f"   Notifications: {dashboard['notifications']}")
    
    print("\n🚀 Executing workflow from mobile...")
    result = mobile_api.execute(auth_result['token'], "wf-order", {"order_id": "ORD-001"})
    print(f"   Execution ID: {result['execution_id']}")
    print(f"   Status: {result['status']}")
    print(f"   Latency: {result['latency_ms']}ms")
    
    print("\n📤 Sending push notification...")
    notification = PushNotification(
        type=PushNotificationType.WORKFLOW_COMPLETED,
        title="工作流完成",
        body="您的订单处理工作流已完成",
        target_user_id="user-123",
        data={"workflow_id": "wf-order", "execution_id": result['execution_id']}
    )
    api_manager.send_notification(notification)
    print("   Notification sent!")


def main():
    """主函数"""
    print_banner()
    
    try:
        # 演示1: 多语言SDK
        demo_sdk()
        
        # 演示2: 版本控制与A/B测试
        demo_version_control()
        
        # 演示3: 高级分析
        demo_analytics()
        
        # 演示4: 移动端API
        demo_mobile()
        
    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("  ✅ MAOS v14.0 Demo Complete!")
    print("="*80 + "\n")
    
    print("📚 New Features Summary:")
    print("   1. Multi-Language SDK v2 (Python/JS/Go/Java/Rust)")
    print("   2. Workflow Version Control & A/B Testing")
    print("   3. Advanced Analytics & Visualization Dashboard")
    print("   4. Mobile API Support")
    print("\n🚀 MAOS v14.0 - Multi-Language SDK & Advanced Analytics!")


if __name__ == "__main__":
    main()
