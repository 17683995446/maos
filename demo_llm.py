#!/usr/bin/env python3
"""
MAOS v5.0 - LLM 演示应用
展示如何使用硅基流动的大模型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio
from dotenv import load_dotenv


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_separator():
    print("-" * 80)


async def demo_llm_client():
    """演示LLM客户端"""
    print_header("1. LLM Client Demo")
    
    from maos.llm import LLMClient, available_models, ChatMessage
    
    # 创建客户端
    client = LLMClient()
    
    if not client.is_available():
        print("   ⚠️ LLM client not available!")
        print("   Make sure:")
        print("     1. OpenAI SDK is installed: pip install openai")
        print("     2. API key is set in .env file")
        print("")
        return False
    
    print("   ✅ LLM client initialized successfully!")
    print(f"   Model: {client.config.model}")
    print(f"   Base URL: {client.config.base_url}")
    print_separator()
    
    # 显示可用模型
    print("   📋 Available Models:")
    for model in available_models():
        print(f"      - {model}")
    print_separator()
    
    # 简单测试
    print("   🧪 Testing simple prompt...")
    try:
        response = client.simple_prompt(
            prompt="用一句话介绍你自己",
            system_prompt="你是MAOS系统的AI助手"
        )
        print(f"\n   🤖 Response:\n   {response}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True


async def demo_llm_agents():
    """演示LLM Agent"""
    print_header("2. LLM Agent Demo")
    
    from maos.agents import create_agent, ResearchAgent, CodeAgent
    
    print("   Creating specialized agents...")
    print_separator()
    
    # 研究Agent
    print("   🔬 Research Agent - Quick Question:")
    try:
        research_agent = ResearchAgent()
        
        print("\n   Question: '什么是大语言模型?'")
        print("   Answer (streaming): ", end="", flush=True)
        
        async for token in research_agent.process_request(
            input_text="用2-3句话解释什么是大语言模型"
        ):
            print(token, end="", flush=True)
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_separator()
    
    # 编程Agent
    print("   💻 Code Agent - Quick Question:")
    try:
        code_agent = CodeAgent()
        
        print("\n   Question: '写一个Python的Hello World'")
        print("   Answer: ", end="", flush=True)
        
        async for token in code_agent.process_request(
            input_text="写一个简单的Python Hello World程序"
        ):
            print(token, end="", flush=True)
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print_separator()
    return True


async def interactive_chat():
    """交互式聊天"""
    print_header("3. Interactive Chat Mode")
    print("   Type 'quit' or 'exit' to quit, 'switch' to change agent")
    print_separator()
    
    from maos.agents import create_agent, ResearchAgent, CodeAgent, CreativeAgent, DataAnalysisAgent
    from maos.llm import LLMClient
    
    # 检查可用性
    client = LLMClient()
    if not client.is_available():
        print("   ❌ LLM not available, skipping interactive mode")
        return
    
    # Agent选择
    agents = {
        "1": ("General", lambda: create_agent("general", client)),
        "2": ("Research", lambda: ResearchAgent(client)),
        "3": ("Code", lambda: CodeAgent(client)),
        "4": ("Creative", lambda: CreativeAgent(client)),
        "5": ("Data", lambda: DataAnalysisAgent(client))
    }
    
    print("\n   🤖 Choose an agent:")
    for key, (name, _) in agents.items():
        print(f"      {key}. {name}")
    
    choice = input("\n   Enter choice (1-5, default=1): ").strip() or "1"
    agent_name, agent_creator = agents.get(choice, agents["1"])
    current_agent = agent_creator()
    
    print(f"\n   ✅ Using {agent_name} Agent")
    print_separator()
    print("   💬 Start chatting (type 'quit' to exit):")
    print("-" * 80)
    
    # 聊天循环
    while True:
        try:
            user_input = input("\n   You: ").strip()
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n   👋 Goodbye!")
                break
            
            if user_input.lower() in ["switch", "change"]:
                print("\n   🔄 Switching agent...")
                choice = input("   Enter choice (1-5): ").strip() or "1"
                agent_name, agent_creator = agents.get(choice, agents["1"])
                current_agent = agent_creator()
                print(f"   ✅ Switched to {agent_name} Agent")
                continue
            
            if not user_input:
                continue
            
            print(f"   {current_agent.agent_id}: ", end="", flush=True)
            
            async for token in current_agent.process_request(user_input):
                print(token, end="", flush=True)
            print()
            
        except KeyboardInterrupt:
            print("\n\n   👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n   ❌ Error: {e}")


async def main():
    """主函数"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║           MAOS v5.0 - SiliconFlow LLM Integration Demo                   ║")
    print("║                硅基流动大模型集成演示应用                                 ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    # 加载环境变量
    load_dotenv()
    
    # 安装依赖提示
    print_header("0. Setup Check")
    try:
        import openai
        import dotenv
        print("   ✅ Dependencies available")
    except ImportError:
        print("   ⚠️ Some dependencies missing!")
        print("   Install with: pip install openai python-dotenv")
        print("")
        return
    
    # 运行演示
    success = True
    
    if await demo_llm_client():
        await demo_llm_agents()
        
        # 询问是否进行交互式聊天
        print_header("Interactive Mode")
        choice = input("\n   🎮 Start interactive chat? (y/n, default=y): ").strip().lower()
        if choice != "n":
            await interactive_chat()
    
    print_header("Demo Complete!")
    print("")
    print("   📚 Next Steps:")
    print("      1. Explore maos/llm.py for LLM integration")
    print("      2. Explore maos/agents/llm_agent.py for Agent implementations")
    print("      3. Check .env for configuration")
    print("      4. Run 'pip install openai python-dotenv' if needed")
    print("")
    print("   🚀 Ready to build amazing AI applications!")
    print("")


if __name__ == "__main__":
    asyncio.run(main())
