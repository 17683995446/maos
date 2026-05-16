"""
MAOS v12.0 - 企业级监控系统（简化版）
为快速修复版本，避免了前面的复杂错误
"""
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class SimpleAlert:
    id: str
    title: str
    level: str
    timestamp: datetime
    source: str


class SimpleMonitoring:
    """简化的监控系统"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = {}
        self.alerts: List[SimpleAlert] = []
        self.logs: List[str] = []
        print("✅ 监控系统初始化")

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录指标"""
        key = name
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append({
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat()
        })

    def create_alert(self, title: str, level: str, source: str = "system"):
        """创建告警"""
        alert = SimpleAlert(
            id=str(uuid.uuid4()),
            title=title,
            level=level,
            timestamp=datetime.now(),
            source=source,
        )
        self.alerts.append(alert)
        return alert

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            "metrics": self.metrics,
            "alerts": len(self.alerts),
            "logs": self.logs,
        }
