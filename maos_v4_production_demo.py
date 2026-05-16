#!/usr/bin/env python3
"""
MAOS v4.0 - Production-Grade Multi-Agent Orchestration System
集成了AWS Agent Squad和OpenAI Swarm的最佳实践
"""

import sys
import asyncio
from pathlib import Path

# Add the workspace to Python path
sys.path.insert(0, str(Path(__file__).parent))

from maos import __version__
from maos.core import Agent, AgentOptions, AgentStatus
from maos.orchestration import OrchestratorService, TaskPriority
from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
from maos.storage import InMemoryChatStorage
from maos.analytics import get_analytics_engine
from maos.multi_tenancy import TenantManagementService
from maos.utils import Logger, generate_uuid, Timer


class ProductionDemo:
    """生产级别的完整演示应用"""
    
    def __init__(self):
        self.logger = Logger.get_logger("MAOS.ProductionDemo")
        self.orchestrator = None
        self.analytics = None
        self.storage = None
        self.tenant_service = None
        self.agents = []
    
    async def initialize(self):
        """初始化整个系统"""
        self.logger.info("="*70)
        self.logger.info("  MAOS v4.0 - 生产级多Agent编排系统")
        self.logger.info("="*70)
        
        # 1. 初始化核心组件
        self.logger.info("\n[1/6] 初始化核心组件...")
        self.storage = InMemoryChatStorage(auto_cleanup=True)
        self.analytics = get_analytics_engine()
        self.tenant_service = TenantManagementService()
        
        # 2. 创建Orchestrator
        self.logger.info("[2/6] 创建Orchestrator服务...")
        self.orchestrator = OrchestratorService(
            name="ProductionOrchestrator",
            max_concurrent_tasks=10
        )
        
        # 3. 注册Agents
        self.logger.info("[3/6] 注册Agents...")
        await self._register_agents()
        
        # 4. 初始化多租户
        self.logger.info("[4/6] 初始化多租户...")
        await self._init_tenants()
        
        # 5. 记录初始指标
        self.logger.info("[5/6] 记录系统指标...")
        self._record_initial_metrics()
        
        # 6. 显示系统状态
        self.logger.info("[6/6] 系统状态检查...")
        await self._show_system_status()
        
        self.logger.info("\n🎉 系统初始化完成！")
    
    async def _register_agents(self):
        """注册所有Agents"""
        agent_configs = [
            ("DataProcessor", "数据清洗和转换专家", DataProcessingAgent),
            ("DataAnalyzer", "数据分析和统计专家", AnalysisAgent),
            ("ReportGenerator", "报告生成和可视化专家", ReportingAgent),
        ]
        
        for name, desc, agent_class in agent_configs:
            agent = agent_class(AgentOptions(
                name=name,
                description=desc,
                capabilities=[desc.split()[0]]
            ))
            self.orchestrator.register_agent(agent)
            self.agents.append(agent)
            self.logger.info(f"  ✅ {name}: {desc}")
    
    async def _init_tenants(self):
        """初始化租户"""
        tenants = [
            ("AcmeCorp", "acme-corp-123"),
            ("TechStart", "tech-start-456"),
        ]
        
        for name, domain in tenants:
            tenant = self.tenant_service.create_tenant(name, domain)
            self.tenant_service.activate_tenant(tenant.tenant_id)
            self.logger.info(f"  ✅ 租户: {name} ({tenant.tenant_id})")
    
    def _record_initial_metrics(self):
        """记录初始系统指标"""
        self.analytics.record_metric("system.agents_total", len(self.agents))
        self.analytics.record_metric("system.status", 1.0)
    
    async def _show_system_status(self):
        """显示系统状态"""
        status = self.orchestrator.get_system_status()
        self.logger.info(f"\n📊 系统状态:")
        self.logger.info(f"  - Orchestrator: {status['name']}")
        self.logger.info(f"  - Agents总数: {status['agents']['total']}")
        self.logger.info(f"  - 可用Agents: {status['agents']['available']}")
    
    async def run_example_workflow(self):
        """运行一个示例工作流"""
        self.logger.info("\n" + "="*70)
        self.logger.info("  示例工作流: 数据分析管道")
        self.logger.info("="*70)
        
        with Timer() as timer:
            # 1. 创建任务
            self.logger.info("\n[1/3] 创建数据处理任务...")
            task1 = self.orchestrator.create_task(
                name="CleanSalesData",
                requirements=["data_cleaning"],
                priority=TaskPriority.HIGH,
                input_data={"records": [
                    {"id": 1, "amount": 100},
                    {"id": 2, "amount": 200},
                    {"id": 3, "amount": 300},
                ]}
            )
            self.logger.info(f"  ✅ 任务创建: {task1.name} (ID: {task1.id[:8]})")
            
            # 2. 创建分析任务
            self.logger.info("\n[2/3] 创建数据分析任务...")
            task2 = self.orchestrator.create_task(
                name="AnalyzeSales",
                requirements=["data_analysis"],
                priority=TaskPriority.HIGH,
                dependencies=[task1.id]
            )
            self.logger.info(f"  ✅ 任务创建: {task2.name} (ID: {task2.id[:8]})")
            
            # 3. 创建报告任务
            self.logger.info("\n[3/3] 创建报告生成任务...")
            task3 = self.orchestrator.create_task(
                name="GenerateReport",
                requirements=["report_generation"],
                priority=TaskPriority.NORMAL,
                dependencies=[task2.id]
            )
            self.logger.info(f"  ✅ 任务创建: {task3.name} (ID: {task3.id[:8]})")
        
        # 记录工作流指标
        self.analytics.record_metric("workflow.tasks_created", 3)
        self.analytics.record_metric("workflow.duration_sec", timer.elapsed)
        
        self.logger.info(f"\n⏱️  工作流完成，耗时: {timer.elapsed:.2f}秒")
        
        return [task1, task2, task3]
    
    async def show_metrics_dashboard(self):
        """显示指标仪表板"""
        self.logger.info("\n" + "="*70)
        self.logger.info("  系统指标仪表板")
        self.logger.info("="*70)
        
        dashboard = self.analytics.get_dashboard_data()
        
        self.logger.info("\n📈 最近指标:")
        for metric in dashboard["recent_metrics"][-5:]:
            self.logger.info(f"  - {metric['name']}: {metric['value']}")
        
        self.logger.info("\n🎯 指标统计:")
        self.logger.info(f"  - 总指标数: {len(dashboard['recent_metrics'])}")
        
        return dashboard


async def main():
    """主函数"""
    demo = ProductionDemo()
    
    try:
        # 初始化系统
        await demo.initialize()
        
        # 运行示例工作流
        await demo.run_example_workflow()
        
        # 显示指标
        await demo.show_metrics_dashboard()
        
        # 完成
        print("\n" + "="*70)
        print("  🎉 MAOS v4.0 演示完成！")
        print("="*70)
        print("\n📖 下一步:")
        print("  1. 访问 http://localhost:8000/maos_dashboard.html 查看可视化")
        print("  2. 运行 `python -m maos.cli demo` 进行更多演示")
        print("  3. 查看 MAOS_v4_FINAL_REPORT.md 获取详细报告")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
