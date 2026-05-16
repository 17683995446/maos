"""
MAOS v9.0 - 审计日志系统
完整的企业级审计追踪
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import uuid


class AuditEventType(Enum):
    """审计事件类型"""
    # 认证事件
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    TOKEN_REFRESH = "auth.token_refresh"
    
    # 用户管理事件
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_ASSIGN = "user.role_assign"
    USER_ROLE_REMOVE = "user.role_remove"
    
    # Agent事件
    AGENT_REGISTER = "agent.register"
    AGENT_UNREGISTER = "agent.unregister"
    AGENT_START = "agent.start"
    AGENT_STOP = "agent.stop"
    AGENT_ERROR = "agent.error"
    
    # 任务事件
    TASK_CREATE = "task.create"
    TASK_START = "task.start"
    TASK_COMPLETE = "task.complete"
    TASK_FAIL = "task.fail"
    TASK_CANCEL = "task.cancel"
    
    # 工作流事件
    WORKFLOW_CREATE = "workflow.create"
    WORKFLOW_START = "workflow.start"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_FAIL = "workflow.fail"
    
    # 安全事件
    SECURITY_ALERT = "security.alert"
    PERMISSION_DENIED = "security.permission_denied"
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    
    # 系统事件
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_ERROR = "system.error"


class Severity(Enum):
    """事件严重性"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    EMERGENCY = 60


@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    actor_ip: Optional[str]
    severity: Severity
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str = ""
    outcome: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "actor_ip": self.actor_ip,
            "severity": self.severity.name,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "details": self.details,
            "metadata": self.metadata,
            "request_id": self.request_id,
            "session_id": self.session_id
        }
    
    @property
    def checksum(self) -> str:
        """事件校验和"""
        data = f"{self.event_id}{self.event_type.value}{self.timestamp.isoformat()}{self.user_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, retention_days: int = 365):
        self.events: List[AuditEvent] = []
        self.retention_days = retention_days
        self.alerts: List[Dict] = []
        self.compliance_reports: List[Dict] = []
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: Severity,
        user_id: Optional[str] = None,
        action: str = "",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: str = "success",
        details: Dict = None,
        actor_ip: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Dict = None
    ) -> str:
        """记录审计事件"""
        event_id = str(uuid.uuid4())
        
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            actor_ip=actor_ip,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=details or {},
            request_id=request_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        
        # 检查是否需要告警
        if severity.value >= Severity.WARNING.value:
            self._process_alert(event)
        
        # 清理过期事件
        self._cleanup_old_events()
        
        return event_id
    
    def _process_alert(self, event: AuditEvent):
        """处理告警"""
        alert = {
            "alert_id": str(uuid.uuid4()),
            "event_id": event.event_id,
            "severity": event.severity.name,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "timestamp": event.timestamp.isoformat(),
            "message": f"{event.event_type.value}: {event.action}",
            "details": event.details,
            "acknowledged": False
        }
        self.alerts.append(alert)
    
    def _cleanup_old_events(self):
        """清理过期事件"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        self.events = [e for e in self.events if e.timestamp > cutoff]
    
    def query_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[Severity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """查询审计事件"""
        results = self.events
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        
        if severity:
            results = [e for e in results if e.severity == severity]
        
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        
        return [e.to_dict() for e in results[-limit:]]
    
    def get_user_activity(self, user_id: str, days: int = 30) -> Dict:
        """获取用户活动摘要"""
        cutoff = datetime.now() - timedelta(days=days)
        user_events = [e for e in self.events 
                      if e.user_id == user_id and e.timestamp > cutoff]
        
        # 统计
        total_events = len(user_events)
        by_type = {}
        by_severity = {}
        by_outcome = {"success": 0, "failure": 0}
        
        for event in user_events:
            # 按类型统计
            event_type = event.event_type.value
            by_type[event_type] = by_type.get(event_type, 0) + 1
            
            # 按严重性统计
            severity = event.severity.name
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # 按结果统计
            by_outcome[event.outcome] = by_outcome.get(event.outcome, 0) + 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": total_events,
            "by_type": by_type,
            "by_severity": by_severity,
            "by_outcome": by_outcome,
            "first_event": user_events[0].timestamp.isoformat() if user_events else None,
            "last_event": user_events[-1].timestamp.isoformat() if user_events else None
        }
    
    def get_security_alerts(self, acknowledged: bool = None, limit: int = 100) -> List[Dict]:
        """获取安全告警"""
        alerts = self.alerts
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a["acknowledged"] == acknowledged]
        
        return alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = acknowledged_by
                alert["acknowledged_at"] = datetime.now().isoformat()
                return True
        return False
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "full"
    ) -> Dict:
        """生成合规报告"""
        events = self.query_events(
            start_time=start_date,
            end_time=end_date
        )
        
        # 基本统计
        total_events = len(events)
        by_type = {}
        by_user = {}
        critical_events = []
        
        for event in events:
            # 按类型统计
            event_type = event["event_type"]
            by_type[event_type] = by_type.get(event_type, 0) + 1
            
            # 按用户统计
            if event.get("user_id"):
                user_id = event["user_id"]
                by_user[user_id] = by_user.get(user_id, 0) + 1
            
            # 记录严重事件
            if event.get("severity") in ["ERROR", "CRITICAL", "EMERGENCY"]:
                critical_events.append(event)
        
        # 认证事件统计
        auth_events = [e for e in events if e["event_type"].startswith("auth.")]
        login_events = [e for e in auth_events if e["event_type"] == "auth.login"]
        failed_logins = [e for e in auth_events if e["event_type"] == "auth.login_failed"]
        
        report = {
            "report_id": str(uuid.uuid4()),
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "unique_users": len(by_user),
                "critical_events": len(critical_events),
                "login_success_rate": (
                    len(login_events) / (len(login_events) + len(failed_logins)) * 100
                    if (len(login_events) + len(failed_logins)) > 0 else 100
                )
            },
            "events_by_type": by_type,
            "events_by_user": by_user,
            "critical_events": critical_events[:50],  # 限制数量
            "recommendations": self._generate_recommendations(events, by_type, by_user)
        }
        
        self.compliance_reports.append(report)
        return report
    
    def _generate_recommendations(
        self,
        events: List[Dict],
        by_type: Dict,
        by_user: Dict
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 检查异常
        failed_logins = sum(1 for e in events if e["event_type"] == "auth.login_failed")
        if failed_logins > 10:
            recommendations.append(
                f"检测到 {failed_logins} 次失败的登录尝试，建议检查账户安全"
            )
        
        # 检查高活跃用户
        if by_user:
            max_user = max(by_user.items(), key=lambda x: x[1])
            if max_user[1] > 1000:
                recommendations.append(
                    f"用户 {max_user[0]} 有 {max_user[1]} 次操作，建议审查其权限"
                )
        
        # 检查异常事件
        security_events = [e for e in events if "security" in e["event_type"]]
        if len(security_events) > 0:
            recommendations.append(
                f"检测到 {len(security_events)} 个安全事件，请审查安全告警"
            )
        
        return recommendations
    
    def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """导出审计日志"""
        events = self.query_events(
            start_time=start_time or datetime.now() - timedelta(days=7),
            end_time=end_time or datetime.now(),
            limit=10000
        )
        
        if format == "json":
            return json.dumps(events, indent=2, ensure_ascii=False)
        elif format == "csv":
            # CSV格式
            lines = ["event_id,event_type,timestamp,user_id,severity,action,outcome"]
            for event in events:
                lines.append(
                    f"{event['event_id']},{event['event_type']},{event['timestamp']},"
                    f"{event['user_id']},{event['severity']},{event['action']},{event['outcome']}"
                )
            return "\n".join(lines)
        else:
            return json.dumps(events, indent=2, ensure_ascii=False)
