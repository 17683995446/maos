#!/usr/bin/env python3
"""
MAOS - Quick Verification Test
Verify the system is properly installed and functional.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("MAOS - QUICK VERIFICATION")
print("=" * 60)

# Test 1: Import all main modules
print("\n[1/5] Testing imports...")
try:
    from maos import __version__
    from maos.core import Agent, AgentStatus
    from maos.services import OrchestratorService, TaskPriority
    from maos.agents import DataProcessingAgent
    print(f"   ✅ Imports OK (version: {__version__})")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Create an agent
print("\n[2/5] Testing agent creation...")
try:
    agent = DataProcessingAgent(name="test_agent")
    print(f"   ✅ Agent created: {agent.name}")
    print(f"   ✅ Capabilities: {agent.capabilities}")
except Exception as e:
    print(f"   ❌ Agent creation failed: {e}")
    sys.exit(1)

# Test 3: Create orchestrator
print("\n[3/5] Testing orchestrator initialization...")
try:
    orchestrator = OrchestratorService(name="test_orchestrator")
    print(f"   ✅ Orchestrator created: {orchestrator.name}")
except Exception as e:
    print(f"   ❌ Orchestrator failed: {e}")
    sys.exit(1)

# Test 4: Register agent
print("\n[4/5] Testing agent registration...")
try:
    success = orchestrator.register_agent(agent)
    if success:
        print(f"   ✅ Agent registered successfully")
        stats = orchestrator.registry.get_statistics()
        print(f"   ✅ Registry stats: {stats['total_agents']} agent(s)")
    else:
        print(f"   ❌ Agent registration failed")
except Exception as e:
    print(f"   ❌ Registration failed: {e}")
    sys.exit(1)

# Test 5: Create a task
print("\n[5/5] Testing task creation...")
try:
    task = orchestrator.create_task(
        name="test_task",
        requirements=["data_cleaning"],
        priority=TaskPriority.HIGH,
        input_data={"test": "data"}
    )
    print(f"   ✅ Task created: {task.name} (ID: {task.id[:8]}...)")
    print(f"   ✅ Status: {task.status.value}")
except Exception as e:
    print(f"   ❌ Task creation failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nNext steps:")
print("  1. Run the full demo: python demo.py")
print("  2. Start the API server: uvicorn maos.api.main:app --reload")
print("  3. Run the test suite: python -m pytest tests/ -v")
print("  4. Read the documentation in docs/")
print("\nThe Multi-Agent Orchestration System is ready! 🚀")
