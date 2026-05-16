#!/usr/bin/env python3
"""
MAOS v8.0 - 创新功能演示
AI调度器 + Agent协作 + 插件系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time


async def demo_ai_scheduler():
    """演示AI调度器"""
    print("\n" + "="*80)
    print("  1. AI驱动的智能调度器")
    print("="*80)
    
    from maos.ai_scheduler import AIScheduler, AIStrategy
    
    # 创建调度器
    scheduler = AIScheduler(strategy=AIStrategy.PREDICTIVE)
    
    # 注册Agent
    scheduler.register_agent("agent_1", ["data_processing", "analysis"])
    scheduler.register_agent("agent_2", ["data_processing", "reporting"])
    scheduler.register_agent("agent_3", ["analysis", "reporting", "visualization"])
    
    print("\n📋 Registered agents:")
    for aid in scheduler.agent_profiles.keys():
        print(f"   - {aid}")
    
    # 模拟任务调度
    print("\n🎯 Simulating task scheduling...")
    tasks = [
        ("task_1", ["data_processing"], 1),
        ("task_2", ["analysis"], 2),
        ("task_3", ["reporting"], 1),
        ("task_4", ["visualization"], 3),
    ]
    
    for task_id, requirements, priority in tasks:
        selected_agent = scheduler.schedule_task(task_id, requirements, priority)
        print(f"   Task {task_id} (req: {requirements}) -> {selected_agent}")
        
        # 模拟执行
        scheduler.record_task_completion(task_id, selected_agent, 2.0 + (priority * 0.5), True)
    
    # 显示指标
    print("\n📊 Scheduler performance metrics:")
    metrics = scheduler.get_performance_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # AI优化
    print("\n🔧 Running AI optimization...")
    scheduler.optimize()
    
    return True


async def demo_agent_collaboration():
    """演示Agent协作"""
    print("\n" + "="*80)
    print("  2. Multi-Agent协作协议")
    print("="*80)
    
    from maos.collaboration import (
        CollaboratingAgent, CollaborationBus, CollaborativeOrchestrator,
        CollaborationState, MessageType
    )
    
    # 创建总线
    bus = CollaborationBus()
    
    # 创建Agent
    agents = [
        CollaboratingAgent("worker_1", ["data_processing", "cleaning"]),
        CollaboratingAgent("worker_2", ["data_processing", "analysis"]),
        CollaboratingAgent("worker_3", ["analysis", "reporting"])
    ]
    
    for agent in agents:
        bus.register_agent(agent)
    
    # 创建编排器
    orchestrator = CollaborativeOrchestrator()
    
    # 创建协作
    contract = orchestrator.create_collaboration(
        task_id="complex_analysis_001",
        requirements=["data_processing", "analysis", "reporting"]
    )
    
    print(f"\n🤝 Created collaboration contract: {contract.contract_id}")
    
    # 模拟竞标过程
    print(f"\n📣 Announcing task to agents...")
    orchestrator.announce_task(contract)
    
    # 收集竞标（简化）
    print(f"🔍 Collecting bids...")
    selected_bids = orchestrator.collect_bids(contract.contract_id)
    selected_agents = [b["agent_id"] for b in selected_bids]
    print(f"   Selected agents: {selected_agents}")
    
    # 形成协作
    orchestrator.form_collaboration(contract, selected_agents)
    
    # 总线统计
    print("\n📊 Collaboration bus stats:")
    stats = bus.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return True


def demo_plugin_system():
    """演示插件系统"""
    print("\n" + "="*80)
    print("  3. 插件系统")
    print("="*80)
    
    from maos.plugins import (
        PluginManager, PluginType, PluginMetadata, 
        PluginContext, create_sample_plugin
    )
    
    # 创建管理器
    manager = PluginManager()
    
    # 创建示例插件
    print("\n📦 Creating sample plugin...")
    sample_plugin = create_sample_plugin()
    
    # 注册插件
    plugin_id = manager.registry.register_plugin(sample_plugin)
    print(f"   Plugin ID: {plugin_id}")
    
    # 激活插件
    print("\n✨ Activating plugin...")
    manager.activate_plugin(plugin_id)
    
    # 搜索插件
    print("\n🔍 Searching plugins...")
    results = manager.registry.search_plugins("agent")
    for result in results:
        print(f"   Found: {result['metadata']['name']}")
    
    # 列出插件
    print("\n📋 All plugins:")
    all_plugins = manager.registry.list_plugins()
    for plugin_info in all_plugins:
        print(f"   - {plugin_info['metadata']['name']} v{plugin_info['metadata']['version']}")
    
    # 系统状态
    print("\n📊 Plugin system status:")
    status = manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    return True


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("  🚀 MAOS v8.0 - 创新功能演示")
    print("="*80)
    
    # 运行所有演示
    demo_results = []
    demo_results.append(await demo_ai_scheduler())
    demo_results.append(await demo_agent_collaboration())
    demo_results.append(demo_plugin_system())
    
    # 总结
    print("\n" + "="*80)
    print("  创新功能演示完成")
    print("="*80)
    print(f"\n✅ 演示完成: {sum(demo_results)}/{len(demo_results)} 成功")
    print("\n📚 新增功能:")
    print("   1. 🤖 AI驱动的智能调度器")
    print("   2. 🤝 Multi-Agent协作协议")
    print("   3. 🔌 插件系统")
    print("\n📖 查看完整文档:")
    print("   - ROADMAP_V8.md (v8.0路线图)")
    print("   - maos/ai_scheduler.py (AI调度器)")
    print("   - maos/collaboration.py (Agent协作)")
    print("   - maos/plugins.py (插件系统)")
    print("\n🚀 MAOS v8.0 - AI驱动的多Agent编排新纪元！")


if __name__ == "__main__":
    asyncio.run(main())
