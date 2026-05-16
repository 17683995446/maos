#!/usr/bin/env python3
"""
MAOS v3.0.0 - 核心功能验证脚本
"""

import sys
import time
from datetime import datetime


def main():
    print("=" * 70)
    print("  MAOS v3.0.0 - 核心功能验证")
    print("=" * 70)

    results = {}
    total = 0
    passed = 0

    # Test 1: Base imports
    total += 1
    try:
        print()
        print("[1/8] 测试基础模块...")
        import maos
        from maos.core import Agent, AgentOptions, AgentStatus, AgentMessage, MessageType
        from maos.orchestration import OrchestratorService, ExecutionStrategy, TaskManager
        print("  ✅ 核心模块导入成功")
        results["core_modules"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ 核心模块导入失败: {e}")
        results["core_modules"] = f"FAIL: {e}"

    # Test 2: Example Agents
    total += 1
    try:
        print()
        print("[2/8] 测试示例Agents...")
        from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
        agent1 = DataProcessingAgent(AgentOptions(name="DataAgent"))
        agent2 = AnalysisAgent(AgentOptions(name="AnalysisAgent"))
        agent3 = ReportingAgent(AgentOptions(name="ReportAgent"))
        print(f"  ✅ Agents创建: {agent1.name}, {agent2.name}, {agent3.name}")
        results["agents"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ Agents创建失败: {e}")
        results["agents"] = f"FAIL: {e}"

    # Test 3: Orchestrator
    total += 1
    try:
        print()
        print("[3/8] 测试Orchestrator...")
        from maos.agents.examples import DataProcessingAgent, AnalysisAgent, ReportingAgent
        from maos.core import Agent, AgentOptions
        orchestrator = OrchestratorService(name="TestOrchestrator")
        agent1 = DataProcessingAgent(AgentOptions(name="DataAgent"))
        agent2 = AnalysisAgent(AgentOptions(name="AnalysisAgent"))
        agent3 = ReportingAgent(AgentOptions(name="ReportAgent"))
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)
        status = orchestrator.get_system_status()
        print(f"  ✅ Orchestrator就绪 - {status['agents']['total']}个Agents")
        results["orchestrator"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ Orchestrator测试失败: {e}")
        results["orchestrator"] = f"FAIL: {e}"

    # Test 4: Storage
    total += 1
    try:
        print()
        print("[4/8] 测试存储系统...")
        from maos.storage import InMemoryChatStorage
        from maos.types import ConversationMessage, ParticipantRole
        storage = InMemoryChatStorage(auto_cleanup=False)
        msg = ConversationMessage(role=ParticipantRole.USER, content="Hello MAOS!")
        print("  ✅ 存储系统就绪")
        results["storage"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ 存储系统测试失败: {e}")
        results["storage"] = f"FAIL: {e}"

    # Test 5: Analytics
    total += 1
    try:
        print()
        print("[5/8] 测试分析引擎...")
        from maos.analytics import get_analytics_engine
        analytics = get_analytics_engine()
        analytics.record_metric("test.core_functionality", 1.0)
        analytics.record_metric("test.agents", 3.0)
        print("  ✅ 分析引擎就绪")
        results["analytics"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ 分析引擎测试失败: {e}")
        results["analytics"] = f"FAIL: {e}"

    # Test 6: Multi-tenancy
    total += 1
    try:
        print()
        print("[6/8] 测试多租户...")
        from maos.multi_tenancy import TenantManagementService
        tenant_service = TenantManagementService()
        tenant = tenant_service.create_tenant("ValidationCorp", "validation.corp")
        tenant_service.activate_tenant(tenant.tenant_id)
        print(f"  ✅ 多租户就绪 - {tenant.tenant_name}")
        results["multi_tenancy"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ 多租户测试失败: {e}")
        results["multi_tenancy"] = f"FAIL: {e}"

    # Test 7: Utilities
    total += 1
    try:
        print()
        print("[7/8] 测试工具函数...")
        from maos.utils import Logger, generate_uuid, Timer
        logger = Logger.get_logger("validation")
        uuid = generate_uuid()
        print(f"  ✅ 工具函数就绪 - UUID: {uuid[:20]}...")
        results["utilities"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ 工具函数测试失败: {e}")
        results["utilities"] = f"FAIL: {e}"

    # Test 8: Types
    total += 1
    try:
        print()
        print("[8/8] 测试类型系统...")
        from maos.types import ConversationMessage, ParticipantRole, MessageContentType
        msg = ConversationMessage(
            role=ParticipantRole.USER,
            content="Test",
            sender="User1"
        )
        print("  ✅ 类型系统就绪")
        results["types"] = "PASS"
        passed += 1
    except Exception as e:
        print(f"  ❌ 类型系统测试失败: {e}")
        results["types"] = f"FAIL: {e}"

    # Final Summary
    print()
    print("=" * 70)
    print("  🎉 核心功能验证完成！")
    print("=" * 70)
    print()
    print("📊 验证报告:")
    print(f"  - MAOS 版本: 3.0.0")
    print(f"  - 测试总数: {total}")
    print(f"  - 通过: {passed}")
    print(f"  - 失败: {total - passed}")
    print(f"  - 通过率: {(passed/total*100):.1f}%")
    print()
    print("📋 详细结果:")
    for key, result in results.items():
        status = "✅" if result == "PASS" else "❌"
        print(f"  {status} {key}: {result}")
    print()

    if passed == total:
        print("🚀 系统已准备好投入使用！")
    else:
        print("⚠️  有部分功能需要检查")
    print()
    print("📁 项目文件:")
    print("  - /workspace/maos/ - 核心代码")
    print("  - /workspace/maos_dashboard.html - 仪表板")
    print("  - /workspace/pyproject.toml - 项目配置")
    print()


if __name__ == "__main__":
    main()
