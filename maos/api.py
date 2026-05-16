"""
MAOS v5.0 - FastAPI REST API
完整的REST API，包含自动OpenAPI文档
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入MAOS核心模块
from maos.config import MAOSConfig, get_config
from maos.orchestration import TaskManager, TaskPriority, TaskStatus
from maos.analytics import get_analytics_engine
from maos.performance import timed, get_all_performance_metrics


# Pydantic模型定义
class TaskCreate(BaseModel):
    """创建任务的请求模型"""
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field("", description="任务描述")
    requirements: List[str] = Field(default_factory=list, description="任务要求的Agent能力")
    priority: Optional[str] = Field("NORMAL", description="优先级: LOW, NORMAL, HIGH, URGENT")
    input_data: Optional[Any] = Field(None, description="输入数据")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: str
    name: str
    description: str
    status: str
    priority: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    assigned_agent: Optional[str] = None


class SystemInfo(BaseModel):
    """系统信息模型"""
    system_name: str
    version: str
    debug: bool
    max_concurrent_tasks: int


class StatisticsResponse(BaseModel):
    """统计信息响应"""
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    by_priority: Dict[str, int]


# 初始化FastAPI应用
app = FastAPI(
    title="MAOS - Multi-Agent Orchestration System API",
    description="A production-grade multi-agent orchestration system with REST API",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
task_manager: TaskManager = None
config: MAOSConfig = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global task_manager, config
    config = get_config()
    task_manager = TaskManager(max_concurrent=config.max_concurrent_tasks)
    print(f"🚀 MAOS v5.0 API started on http://{config.api_host}:{config.api_port}")
    print(f"📚 API docs available at http://{config.api_host}:{config.api_port}/docs")


@app.get("/", tags=["Root"])
@timed(log_duration=False, record_metrics=False)
async def root():
    """根路径 - 返回欢迎信息"""
    return {
        "name": "MAOS - Multi-Agent Orchestration System",
        "version": "5.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/v1/system/info", tags=["System"], response_model=SystemInfo)
@timed(log_duration=False, record_metrics=False)
async def get_system_info():
    """获取系统信息"""
    return SystemInfo(
        system_name=config.system_name,
        version=config.system_version,
        debug=config.debug,
        max_concurrent_tasks=config.max_concurrent_tasks
    )


@app.get("/api/v1/system/statistics", tags=["System"], response_model=StatisticsResponse)
@timed(log_duration=False, record_metrics=False)
async def get_statistics():
    """获取系统统计信息"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    stats = task_manager.get_statistics()
    return StatisticsResponse(**stats)


@app.get("/api/v1/system/performance", tags=["System"])
@timed(log_duration=False, record_metrics=False)
async def get_performance():
    """获取性能指标"""
    perf_metrics = get_all_performance_metrics()
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            name: m.to_dict()
            for name, m in perf_metrics.items()
        }
    }


# 任务相关API
@app.post("/api/v1/tasks", tags=["Tasks"], response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@timed(log_duration=False, record_metrics=False)
async def create_task(task_request: TaskCreate):
    """创建新任务"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    # 解析优先级
    priority_map = {
        "LOW": TaskPriority.LOW,
        "NORMAL": TaskPriority.NORMAL,
        "HIGH": TaskPriority.HIGH,
        "URGENT": TaskPriority.URGENT
    }
    priority = priority_map.get(task_request.priority.upper(), TaskPriority.NORMAL)
    
    # 创建任务
    task = task_manager.create_task(
        name=task_request.name,
        description=task_request.description,
        requirements=task_request.requirements,
        priority=priority,
        input_data=task_request.input_data
    )
    
    # 返回响应
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        status=task.status.value,
        priority=task.priority.name,
        input_data=task.input_data,
        created_at=task.created_at.isoformat() if task.created_at else datetime.now().isoformat()
    )


@app.get("/api/v1/tasks", tags=["Tasks"])
@timed(log_duration=False, record_metrics=False)
async def list_tasks(status_filter: Optional[str] = None):
    """列出所有任务，可按状态过滤"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    if status_filter:
        try:
            status_enum = TaskStatus(status_filter.lower())
            tasks = task_manager.get_tasks_by_status(status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
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
            for t in tasks
        ]
    }


@app.get("/api/v1/tasks/{task_id}", tags=["Tasks"], response_model=TaskResponse)
@timed(log_duration=False, record_metrics=False)
async def get_task(task_id: str):
    """获取单个任务详情"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        status=task.status.value,
        priority=task.priority.name,
        input_data=task.input_data,
        output_data=task.output_data,
        error=task.error,
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        assigned_agent=task.assigned_agent
    )


@app.delete("/api/v1/tasks/{task_id}", tags=["Tasks"], status_code=status.HTTP_204_NO_CONTENT)
@timed(log_duration=False, record_metrics=False)
async def cancel_task(task_id: str):
    """取消任务"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be cancelled")


@app.post("/api/v1/tasks/{task_id}/complete", tags=["Tasks"])
@timed(log_duration=False, record_metrics=False)
async def complete_task(task_id: str, output_data: Optional[Any] = None):
    """标记任务为完成"""
    if not task_manager:
        raise HTTPException(status_code=500, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task.mark_completed(output_data)
    task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
    
    return {"status": "success", "message": f"Task {task_id} completed"}


# 运行服务器的主函数
def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行API服务器"""
    import uvicorn
    print(f"\n🌐 Starting MAOS v5.0 API Server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Docs: http://{host}:{port}/docs")
    print(f"\n🚀 API is ready to use!\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
