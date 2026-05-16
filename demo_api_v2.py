"""
MAOS v7.0 - API v2.0演示
展示增强的REST API和WebSocket
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def demo_rest_api():
    """演示REST API"""
    import requests
    
    base_url = "http://localhost:8000"
    
    print_header("1. REST API Demo")
    
    # 1. 检查系统状态
    print("\n📋 System Info:")
    response = requests.get(f"{base_url}/api/v1/system/info")
    if response.status_code == 200:
        info = response.json()
        print(f"   Name: {info['system_name']}")
        print(f"   Version: {info['version']}")
        print(f"   Max Tasks: {info['max_concurrent_tasks']}")
    else:
        print("   ⚠️ API not available (start with: python maos/api_v2.py)")
        return
    
    # 2. 创建任务
    print("\n📋 Creating Task:")
    task_data = {
        "name": "API Test Task",
        "description": "Created via REST API",
        "requirements": ["test"],
        "priority": "HIGH"
    }
    response = requests.post(f"{base_url}/api/v1/tasks", json=task_data)
    if response.status_code == 201:
        task = response.json()
        print(f"   ✅ Task created: {task['task_id']}")
        print(f"   Status: {task['status']}")
        task_id = task['task_id']
    else:
        print(f"   ❌ Failed: {response.text}")
        return
    
    # 3. 列出任务
    print("\n📋 Listing Tasks:")
    response = requests.get(f"{base_url}/api/v1/tasks")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total tasks: {data['count']}")
    
    # 4. 获取任务详情
    print("\n📋 Getting Task Details:")
    response = requests.get(f"{base_url}/api/v1/tasks/{task_id}")
    if response.status_code == 200:
        task = response.json()
        print(f"   Name: {task['name']}")
        print(f"   Status: {task['status']}")
        print(f"   Priority: {task['priority']}")
    
    # 5. 记录指标
    print("\n📋 Recording Metrics:")
    metric_data = {
        "name": "api.test.metric",
        "value": 42.0,
        "metric_type": "gauge"
    }
    response = requests.post(f"{base_url}/api/v1/metrics", json=metric_data)
    if response.status_code == 200:
        print("   ✅ Metric recorded")


async def demo_websocket():
    """演示WebSocket"""
    import websockets
    import json
    
    print_header("2. WebSocket Demo")
    
    ws_url = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(ws_url) as ws:
            # 接收欢迎消息
            welcome = await ws.recv()
            print(f"\n📋 Connected: {json.loads(welcome)['data']['message']}")
            
            # 订阅任务频道
            subscribe_msg = {
                "event_type": "subscribe",
                "data": {"channel": "tasks"},
                "timestamp": "2024-01-01T00:00:00",
                "message_id": "test-1"
            }
            await ws.send(json.dumps(subscribe_msg))
            response = await ws.recv()
            print(f"📋 Subscribed: {json.loads(response)['data']}")
            
            # 创建任务（通过发送事件）
            create_msg = {
                "event_type": "task:create",
                "data": {
                    "name": "WebSocket Test Task",
                    "requirements": ["test"]
                },
                "timestamp": "2024-01-01T00:00:00",
                "message_id": "test-2"
            }
            await ws.send(json.dumps(create_msg))
            print("📋 Task creation event sent")
            
            # 接收响应（如果有）
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"📋 Response: {json.loads(response)['event_type']}")
            except asyncio.TimeoutError:
                print("📋 Waiting for response... (timeout)")
            
            # Ping测试
            ping_msg = {
                "event_type": "ping",
                "data": {},
                "timestamp": "2024-01-01T00:00:00",
                "message_id": "test-3"
            }
            await ws.send(json.dumps(ping_msg))
            pong = await ws.recv()
            print(f"📋 Pong: {json.loads(pong)['event_type']}")
            
    except Exception as e:
        print(f"\n   ⚠️ WebSocket not available")
        print(f"   Error: {e}")
        print("   Start with: python maos/api_v2.py")


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


async def main():
    """主函数"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║         MAOS v7.0 - Enhanced API Demo                                  ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    await demo_rest_api()
    await demo_websocket()
    
    print("\n" + "=" * 80)
    print("  Demo Complete!")
    print("=" * 80)
    print("\n📚 Next Steps:")
    print("   - Start API server: python maos/api_v2.py")
    print("   - Access docs: http://localhost:8000/docs")
    print("   - Test WebSocket: ws://localhost:8000/ws")


if __name__ == "__main__":
    asyncio.run(main())
