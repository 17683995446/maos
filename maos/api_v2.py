"""
MAOS v7.0 - 增强的API
完整的REST API + WebSocket支持
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入MAOS核心
from maos.config import get_config
from maos.orchestration import TaskManager, TaskPriority, TaskStatus
from maos.monitoring import get_monitoring_system
from maos.websocket import WebSocketServer, get_event_bus, EventType
from maos.cache import get_cache_manager


# Pydantic模型
class TaskCreateRequest(BaseModel):
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field("", description="任务描述")
    requirements: List[str] = Field(default_factory=list, description="能力需求")
    priority: str = Field("NORMAL", description="优先级")
    input_data: Optional[Any] = Field(None, description="输入数据")
    dependencies: Optional[List[str]] = Field(None, description="依赖任务")


class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    output_data: Optional[Any] = None
    assigned_agent: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field("default", description="会话ID")
    system_prompt: Optional[str] = Field("你是一个有帮助的AI助手。", description="系统提示")


class MetricRecord(BaseModel):
    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    metric_type: str = Field("gauge", description="指标类型")


# 初始化应用
app = FastAPI(
    title="MAOS v7.0 - Multi-Agent Orchestration System",
    description="生产级多Agent编排系统，支持REST API和WebSocket",
    version="7.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
task_manager: TaskManager = None
config = get_config()
ws_server = WebSocketServer()
event_bus = get_event_bus()
cache_manager = get_cache_manager()


@app.on_event("startup")
async def startup():
    """启动"""
    global task_manager
    task_manager = TaskManager()
    print(f"🚀 MAOS v7.0 API started on port {config.api_port}")
    print(f"📚 Docs: http://localhost:{config.api_port}/docs")


# ============================================================================
# 系统API
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "name": "MAOS v7.0",
        "version": "7.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws"
    }


@app.get("/api/v1/system/info", tags=["System"])
async def get_system_info():
    """系统信息"""
    return {
        "system_name": config.system_name,
        "version": config.system_version,
        "debug": config.debug,
        "max_concurrent_tasks": config.max_concurrent_tasks,
        "uptime": "0s"  # TODO: 实现uptime追踪
    }


@app.get("/api/v1/system/statistics", tags=["System"])
async def get_statistics():
    """系统统计"""
    return {
        "tasks": task_manager.get_statistics() if task_manager else {},
        "metrics": get_monitoring_system().metrics.get_summary(),
        "cache": cache_manager.get_all_stats(),
        "websocket_connections": ws_server.connection_manager.get_connection_count(),
        "event_bus_subscribers": len(event_bus._handlers)
    }


# ============================================================================
# 任务API
# ============================================================================

@app.post("/api/v1/tasks", tags=["Tasks"], status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreateRequest):
    """创建任务"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    priority_map = {
        "LOW": TaskPriority.LOW,
        "NORMAL": TaskPriority.NORMAL,
        "HIGH": TaskPriority.HIGH,
        "URGENT": TaskPriority.URGENT
    }
    priority = priority_map.get(request.priority.upper(), TaskPriority.NORMAL)
    
    task = task_manager.create_task(
        name=request.name,
        description=request.description,
        requirements=request.requirements,
        priority=priority,
        input_data=request.input_data,
        dependencies=request.dependencies or []
    )
    
    # 发布事件
    await event_bus.publish(
        EventType.TASK_CREATED,
        {
            "task_id": task.id,
            "name": task.name,
            "priority": task.priority.name,
            "created_at": task.created_at.isoformat()
        }
    )
    
    return {
        "task_id": task.id,
        "name": task.name,
        "status": task.status.value,
        "created_at": task.created_at.isoformat()
    }


@app.get("/api/v1/tasks", tags=["Tasks"])
async def list_tasks(status: Optional[str] = None):
    """列出任务"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    if status:
        try:
            status_enum = TaskStatus(status.lower())
            tasks = task_manager.get_tasks_by_status(status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        tasks = list(task_manager.tasks.values())
    
    return {
        "count": len(tasks),
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "status": t.status.value,
                "priority": t.priority.name,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in tasks[:100]  # 限制返回数量
        ]
    }


@app.get("/api/v1/tasks/{task_id}", tags=["Tasks"])
async def get_task(task_id: str):
    """获取任务详情"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task.to_dict()


@app.patch("/api/v1/tasks/{task_id}", tags=["Tasks"])
async def update_task(task_id: str, request: TaskUpdateRequest):
    """更新任务"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if request.status:
        status_map = {
            "pending": TaskStatus.PENDING,
            "running": TaskStatus.RUNNING,
            "completed": TaskStatus.COMPLETED,
            "failed": TaskStatus.FAILED,
            "cancelled": TaskStatus.CANCELLED
        }
        status_enum = status_map.get(request.status.lower())
        if status_enum:
            task_manager.update_task_status(task_id, status_enum)
    
    if request.assigned_agent:
        task.assigned_agent = request.assigned_agent
    
    return {"status": "success", "task_id": task_id}


@app.delete("/api/v1/tasks/{task_id}", tags=["Tasks"])
async def delete_task(task_id: str):
    """删除任务"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task_manager.cancel_task(task_id)
    return {"status": "success", "task_id": task_id}


# ============================================================================
# 指标API
# ============================================================================

@app.post("/api/v1/metrics", tags=["Metrics"])
async def record_metric(request: MetricRecord):
    """记录指标"""
    monitor = get_monitoring_system()
    monitor.record_metric(
        request.name,
        request.value,
        request.metric_type
    )
    return {"status": "success"}


@app.get("/api/v1/metrics", tags=["Metrics"])
async def get_metrics(limit: int = 100):
    """获取指标"""
    monitor = get_monitoring_system()
    return monitor.metrics.get_summary()


# ============================================================================
# WebSocket端点
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接"""
    await ws_server.handle_connection(websocket)


# ============================================================================
# 健康检查
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "task_manager": task_manager is not None,
            "monitoring": True,
            "websocket": True,
            "cache": True
        }
    }


# 运行服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
