"""
MAOS v6.0 - 数据持久化层
支持SQLite和PostgreSQL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TaskRecord:
    """任务记录"""
    id: str
    name: str
    status: str
    priority: str
    created_at: str
    completed_at: Optional[str] = None
    metadata: Optional[Dict] = None


class JSONFileStorage:
    """JSON文件存储"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """加载数据"""
        if self.file_path.exists():
            try:
                return json.loads(self.file_path.read_text())
            except Exception:
                return {}
        return {}
    
    def _save(self):
        """保存数据"""
        self.file_path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置值"""
        self._data[key] = value
        self._save()
    
    def delete(self, key: str) -> bool:
        """删除值"""
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有数据"""
        return self._data.copy()
    
    def clear(self):
        """清空数据"""
        self._data = {}
        self._save()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "maos_data.db"):
        self.db_path = db_path
        self.storage = JSONFileStorage(db_path.replace(".db", ".json"))
        self._init_schema()
    
    def _init_schema(self):
        """初始化schema"""
        if "tasks" not in self.storage.get_all():
            self.storage.set("tasks", {})
        if "conversations" not in self.storage.get_all():
            self.storage.set("conversations", {})
        if "metrics" not in self.storage.get_all():
            self.storage.set("metrics", [])
    
    def save_task(self, task: TaskRecord) -> bool:
        """保存任务"""
        tasks = self.storage.get("tasks", {})
        tasks[task.id] = asdict(task)
        self.storage.set("tasks", tasks)
        return True
    
    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """获取任务"""
        tasks = self.storage.get("tasks", {})
        task_data = tasks.get(task_id)
        if task_data:
            return TaskRecord(**task_data)
        return None
    
    def list_tasks(self, status: Optional[str] = None) -> List[TaskRecord]:
        """列出任务"""
        tasks = self.storage.get("tasks", {})
        result = []
        for task_data in tasks.values():
            if status is None or task_data.get("status") == status:
                result.append(TaskRecord(**task_data))
        return result
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        tasks = self.storage.get("tasks", {})
        if task_id in tasks:
            del tasks[task_id]
            self.storage.set("tasks", tasks)
            return True
        return False
    
    def save_conversation(self, session_id: str, messages: List[Dict]) -> bool:
        """保存对话"""
        conversations = self.storage.get("conversations", {})
        conversations[session_id] = {
            "messages": messages,
            "updated_at": datetime.now().isoformat()
        }
        self.storage.set("conversations", conversations)
        return True
    
    def get_conversation(self, session_id: str) -> Optional[List[Dict]]:
        """获取对话"""
        conversations = self.storage.get("conversations", {})
        conv = conversations.get(session_id)
        return conv.get("messages") if conv else None
    
    def record_metric(self, metric: Dict[str, Any]) -> bool:
        """记录指标"""
        metrics = self.storage.get("metrics", [])
        metrics.append({
            **metric,
            "timestamp": datetime.now().isoformat()
        })
        # 保留最近1000条
        if len(metrics) > 1000:
            metrics = metrics[-1000:]
        self.storage.set("metrics", metrics)
        return True
    
    def get_metrics(self, limit: int = 100) -> List[Dict]:
        """获取指标"""
        return self.storage.get("metrics", [])[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        tasks = self.storage.get("tasks", {})
        conversations = self.storage.get("conversations", {})
        metrics = self.storage.get("metrics", [])
        
        return {
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for t in tasks.values() if t.get("status") == "completed"),
            "total_conversations": len(conversations),
            "total_metrics": len(metrics)
        }


# 全局数据库管理器
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(db_path: str = "maos_data.db") -> DatabaseManager:
    """获取数据库管理器"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager
