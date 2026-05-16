"""
MAOS v5.0 - 完整的LLM生产演示
展示如何结合LLM和Agent系统
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from typing import List, Dict, Any

from maos.llm import LLMClient, ChatMessage, get_llm_client
from maos.orchestration import OrchestratorService, TaskManager, TaskPriority
from maos.config import get_config


class ProductionLLMOrchestrator:
    """
    生产级LLM编排器
    结合LLM和任务管理
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.task_manager = TaskManager()
        self.config = get_config()
        self.conversations: Dict[str, List[Dict]] = {}
    
    def is_llm_available(self) -> bool:
        """检查LLM可用性"""
        return self.llm_client is not None and self.llm_client.is_available()
    
    async def chat(
        self,
        session_id: str,
        user_input: str,
        system_prompt: str = "你是一个有帮助的AI助手。"
    ) -> str:
        """聊天"""
        if not self.is_llm_available():
            return "⚠️ LLM not available"
        
        # 获取历史
        history = self.conversations.get(session_id, [])
        
        # 构建消息
        messages = [ChatMessage(role="system", content=system_prompt)]
        for msg in history:
            messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        messages.append(ChatMessage(role="user", content=user_input))
        
        try:
            response = self.llm_client.chat(messages)
            
            # 保存历史
            history.append({'role': 'user', 'content': user_input})
            history.append({'role': 'assistant', 'content': response.content})
            self.conversations[session_id] = history
            
            return response.content
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def stream_chat(
        self,
        session_id: str,
        user_input: str,
        system_prompt: str = "你是一个有帮助的AI助手。"
    ):
        """流式聊天"""
        if not self.is_llm_available():
            yield "⚠️ LLM not available"
            return
        
        history = self.conversations.get(session_id, [])
        
        messages = [ChatMessage(role="system", content=system_prompt)]
        for msg in history:
            messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        messages.append(ChatMessage(role="user", content=user_input))
        
        full_response = ""
        try:
            async for token in self.llm_client.achat_stream(messages):
                full_response += token
                yield token
            
            history.append({'role': 'user', 'content': user_input})
            history.append({'role': 'assistant', 'content': full_response})
            self.conversations[session_id] = history
        except Exception as e:
            yield f"❌ Error: {str(e)}"
    
    def create_task(self, name: str, requirements: List[str], input_data: Any = None):
        """创建任务"""
        return self.task_manager.create_task(
            name=name,
            requirements=requirements,
            input_data=input_data
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            'llm_available': self.is_llm_available(),
            'model': self.llm_client.config.model if self.llm_client else None,
            'conversations': len(self.conversations),
            'tasks': self.task_manager.get_statistics()
        }


async def demo():
    """演示"""
    print("\n" + "=" * 80)
    print("  MAOS v5.0 - Production LLM Orchestrator")
    print("=" * 80)
    
    # 加载环境变量
    load_dotenv()
    
    # 创建编排器
    orchestrator = ProductionLLMOrchestrator()
    
    # 显示状态
    stats = orchestrator.get_stats()
    print("\n📊 System Status:")
    print(f"   LLM Available: {stats['llm_available']}")
    print(f"   Model: {stats['model']}")
    print(f"   Conversations: {stats['conversations']}")
    
    if not stats['llm_available']:
        print("\n⚠️ LLM not available. Checking configuration...")
        from maos.llm import LLMConfig
        config = LLMConfig.from_env()
        print(f"   API Key set: {'Yes' if config.api_key else 'No'}")
        print(f"   Base URL: {config.base_url}")
        print(f"   Model: {config.model}")
        return
    
    # 创建任务
    print("\n📋 Creating Tasks...")
    task1 = orchestrator.create_task(
        name="Research AI Trends",
        requirements=["research", "analysis"]
    )
    task2 = orchestrator.create_task(
        name="Code Review",
        requirements=["coding", "review"]
    )
    print(f"   ✅ Task 1: {task1.name} ({task1.id[:8]})")
    print(f"   ✅ Task 2: {task2.name} ({task2.id[:8]})")
    
    # 简单聊天
    print("\n💬 Simple Chat:")
    response = await orchestrator.chat("session-1", "What is machine learning?")
    print(f"   Response: {response[:150]}...")
    
    # 流式聊天
    print("\n💬 Streaming Chat:")
    print("   ", end="", flush=True)
    async for token in orchestrator.stream_chat("session-2", "Explain Python in one sentence"):
        print(token, end="", flush=True)
    print()
    
    # 显示最终统计
    print("\n📊 Final Statistics:")
    final_stats = orchestrator.get_stats()
    print(f"   Conversations: {final_stats['conversations']}")
    print(f"   Total Tasks: {final_stats['tasks']['total']}")


if __name__ == "__main__":
    asyncio.run(demo())
