#!/usr/bin/env python3
"""
MAOS v13.0 - Complete Demo
MAOS v13.0 完整演示
"""

import asyncio
import time
from datetime import datetime


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║         🚀  MAOS v13.0 - Global Multi-Tenant SaaS Platform                      ║
║                                                                                ║
║         New Features: Multi-Tenant SaaS, Global CDN, State Machine Workflows  ║
║                                                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def demo_saas_layer():
    """演示SaaS层"""
    print("\n" + "="*80)
    print("  1. Multi-Tenant SaaS Layer Demo")
    print("="*80 + "\n")
    
    from maos.saas.v13 import (
        TenantManager,
        SubscriptionPlan,
        TenantIsolationLevel,
        MultiTenantOrchestrator,
        PLAN_CONFIGS
    )
    
    tenant_manager = TenantManager()
    
    print("📝 Creating tenants...")
    tenant1 = tenant_manager.create_tenant(
        name="Startup Inc",
        domain="startup.example.com",
        plan=SubscriptionPlan.FREE
    )
    
    tenant2 = tenant_manager.create_tenant(
        name="Enterprise Corp",
        domain="enterprise.example.com",
        plan=SubscriptionPlan.ENTERPRISE,
        isolation_level=TenantIsolationLevel.DATABASE
    )
    
    print(f"\n✅ Tenants created:")
    for tenant in tenant_manager.list_tenants():
        print(f"   - {tenant.name} ({tenant.id})")
        print(f"     Plan: {tenant.subscription_plan.value}, Quota: {tenant.quota.max_workflows} workflows")
        print(f"     Trial active: {tenant.is_trial_active()}")
    
    print("\n💰 Upgrading tenant plan...")
    tenant_manager.update_tenant_plan(tenant1.id, SubscriptionPlan.PRO)
    
    print("\n📊 Recording usage...")
    tenant_manager.record_usage(tenant1.id, "executions", 150)
    tenant_manager.record_usage(tenant1.id, "storage", 0.5)
    tenant_manager.record_usage(tenant1.id, "api_calls", 2500)
    
    summary = tenant_manager.get_usage_summary(tenant1.id)
    print(f"   Usage summary: executions={summary['executions']}, storage={summary['storage']}GB, api_calls={summary['api_calls']}")
    
    print("\n📄 Creating invoice...")
    invoice = tenant_manager.create_invoice(tenant1.id)
    print(f"   Invoice created: ${invoice.amount:.2f}")
    
    print("\n💳 Processing payment...")
    payment = tenant_manager.process_payment(invoice.id)
    print(f"   Payment successful: ${payment.amount:.2f}")
    
    print("\n🔗 Testing multi-tenant orchestrator...")
    orchestrator = MultiTenantOrchestrator(tenant_manager)
    
    # 模拟工作流
    class MockWorkflow:
        def __init__(self, name):
            self.name = name
    
    result = orchestrator.execute_workflow_for_tenant(
        tenant1.id,
        MockWorkflow("Test Workflow"),
        {"data": "test"}
    )
    print(f"   Execution result: {result}")


def demo_edge_computing():
    """演示边缘计算"""
    print("\n" + "="*80)
    print("  2. Global CDN & Edge Computing Demo")
    print("="*80 + "\n")
    
    from maos.edge.v13 import (
        GlobalTrafficManager,
        EdgeFunctionManager,
        CDNManager,
        Region,
        EdgeProvider
    )
    
    traffic_manager = GlobalTrafficManager()
    edge_manager = EdgeFunctionManager(traffic_manager)
    cdn_manager = CDNManager(traffic_manager)
    
    print("🌍 Testing geo-routing...")
    test_locations = [
        (40.7128, -74.0060, "New York, USA"),
        (51.5074, -0.1278, "London, UK"),
        (1.3521, 103.8198, "Singapore"),
        (35.6762, 139.6503, "Tokyo, Japan")
    ]
    
    for lat, lon, location in test_locations:
        route = traffic_manager.route_request(lat, lon)
        print(f"   {location} → routed to {route['region_name']} (load: {route['load']}/{route['capacity']})")
    
    print("\n🗄️ Testing CDN caching...")
    cache_key = "popular_workflow_config"
    cache_content = {"steps": ["step1", "step2", "step3"], "version": "1.0"}
    
    print(f"   Caching content globally...")
    cdn_manager.cache_content(cache_key, cache_content, ttl=3600)
    
    ny_lat, ny_lon = 40.7128, -74.0060
    retrieved = cdn_manager.get_content(cache_key, ny_lat, ny_lon)
    print(f"   Retrieved from nearest region: {retrieved}")
    
    print("\n🚀 Deploying edge function...")
    edge_func = edge_manager.deploy_function(
        name="request_transformer",
        code="async function transform(req) { return { ...req, transformed: true }; }",
        provider=EdgeProvider.CLOUDFLARE,
        region=Region.US_EAST
    )
    
    print(f"   Function deployed: {edge_func.name} ({edge_func.id})")
    
    print("\n⚡ Invoking edge function...")
    result = edge_manager.invoke_function(edge_func.id, {"data": "test"})
    print(f"   Result: {result}")
    
    print("\n📊 Global stats:")
    stats = traffic_manager.get_global_stats()
    print(f"   Total load: {stats['total_load']}/{stats['total_capacity']}")
    print(f"   Global utilization: {stats['global_utilization']:.1f}%")


async def demo_state_machine_workflow():
    """演示状态机工作流"""
    print("\n" + "="*80)
    print("  3. State Machine Workflow Engine Demo")
    print("="*80 + "\n")
    
    from maos.workflow.v13 import (
        StateMachineEngine,
        WorkflowState
    )
    
    engine = StateMachineEngine()
    
    print("📝 Creating workflow...")
    workflow = engine.create_workflow(
        name="E-Commerce Order Processing",
        description="Process e-commerce orders with validation, payment, and fulfillment"
    )
    
    print("   Adding steps...")
    
    async def validate_order(input_data):
        print(f"      → Validating order: {input_data.get('order_id')}")
        await asyncio.sleep(0.2)
        return {"valid": True, "order_total": input_data.get("total", 100.0)}
    
    async def process_payment(input_data):
        print(f"      → Processing payment for ${input_data.get('total')}")
        await asyncio.sleep(0.3)
        return {"transaction_id": "txn_12345", "success": True}
    
    async def fulfill_order(input_data):
        print(f"      → Fulfilling order...")
        await asyncio.sleep(0.25)
        return {"tracking_number": "TRK-7890", "carrier": "FastShip"}
    
    workflow.add_step(name="Validate Order", handler=validate_order, description="Validate the order details")
    workflow.add_step(name="Process Payment", handler=process_payment, dependencies=["Validate Order"], description="Process payment")
    workflow.add_step(name="Fulfill Order", handler=fulfill_order, dependencies=["Process Payment"], description="Fulfill and ship the order")
    
    print(f"\n🚀 Executing workflow with input data...")
    input_data = {"order_id": "ORD-001", "customer_id": "CUST-123", "total": 99.99}
    result = await engine.execute_workflow(workflow.id, input_data)
    
    print(f"\n✅ Workflow completed! State: {result.state}")
    print(f"   Output data: {result.output_data}")
    
    print(f"\n📋 Execution logs:")
    for log in engine.get_workflow_history(workflow.id):
        print(f"   [{log.timestamp.strftime('%H:%M:%S')}] [{log.level.upper()}] {log.message}")
    
    print("\n⏸️ Testing pause/resume...")
    # 创建另一个工作流来测试暂停/恢复
    print("   Creating second workflow for pause test...")
    workflow2 = engine.create_workflow("Pause Test Workflow")
    
    async def slow_step(input_data):
        print("      → Slow step running (1 second)...")
        for i in range(5):
            await asyncio.sleep(0.2)
            print(f"         Progress: {i*20}%")
        return {"done": True}
    
    workflow2.add_step("Slow Step", slow_step)
    
    # 开始执行，然后暂停
    print("\n   Starting workflow...")
    task = asyncio.create_task(engine.execute_workflow(workflow2.id, {}))
    await asyncio.sleep(0.3)
    print("   Pausing workflow...")
    await engine.pause_workflow(workflow2.id)
    print(f"   Workflow state after pause: {engine.get_workflow(workflow2.id).state}")
    await asyncio.sleep(0.5)
    print("   Resuming workflow...")
    await engine.resume_workflow(workflow2.id)
    await task
    print("   Workflow completed!")


def main():
    """主函数"""
    print_banner()
    
    try:
        # 演示1: SaaS层
        demo_saas_layer()
        
        # 演示2: 边缘计算
        demo_edge_computing()
        
        # 演示3: 状态机工作流
        print("\n" + "⏳ Running async workflow demo...")
        asyncio.run(demo_state_machine_workflow())
        
    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("  ✅ MAOS v13.0 Demo Complete!")
    print("="*80 + "\n")
    
    print("📚 New Features Summary:")
    print("   1. Multi-Tenant SaaS Layer (isolation, quotas, billing)")
    print("   2. Global CDN & Edge Computing (geo-routing, edge functions)")
    print("   3. State Machine Workflow Engine (persistence, pause/resume)")
    print("\n🚀 MAOS v13.0 - Global Multi-Tenant SaaS Platform!")


if __name__ == "__main__":
    main()
