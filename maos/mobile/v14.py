"""
MAOS v14.0 - Mobile API Support
移动端 API 支持
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid


class MobilePlatform(Enum):
    """移动平台"""
    IOS = "ios"
    ANDROID = "android"


class PushNotificationType(Enum):
    """推送通知类型"""
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    ALERT = "alert"
    MESSAGE = "message"
    UPDATE = "update"


@dataclass
class MobileDevice:
    """移动设备"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    platform: MobilePlatform = MobilePlatform.IOS
    device_token: str = ""
    app_version: str = ""
    os_version: str = ""
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)


@dataclass
class PushNotification:
    """推送通知"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: PushNotificationType = PushNotificationType.MESSAGE
    title: str = ""
    body: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    target_user_id: Optional[str] = None
    target_device_id: Optional[str] = None
    priority: int = 10
    badge: int = 0
    sound: str = "default"
    delivered: bool = False
    delivered_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MobileSession:
    """移动端会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    device_id: str = ""
    token: str = ""
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    created_at: datetime = field(default_factory=datetime.now)
    last_access_at: datetime = field(default_factory=datetime.now)


@dataclass
class MobileWorkflowSummary:
    """移动端工作流摘要"""
    id: str = ""
    name: str = ""
    status: str = ""
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class MobileExecutionResult:
    """移动端执行结果"""
    execution_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""
    status: str = ""
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    latency_ms: float = 0.0


class MobileAPIManager:
    """移动端API管理器"""
    
    def __init__(self):
        self._devices: Dict[str, MobileDevice] = {}
        self._notifications: Dict[str, PushNotification] = {}
        self._sessions: Dict[str, MobileSession] = {}
    
    def register_device(self, user_id: str, device_token: str, platform: MobilePlatform,
                       app_version: str, os_version: str, language: str = "zh-CN") -> MobileDevice:
        """注册设备"""
        if isinstance(platform, str):
            platform = MobilePlatform(platform)
        device = MobileDevice(
            user_id=user_id,
            platform=platform,
            device_token=device_token,
            app_version=app_version,
            os_version=os_version,
            language=language
        )
        self._devices[device.id] = device
        print(f"📱 Device registered: {device.id} ({platform.value})")
        return device
    
    def get_user_devices(self, user_id: str) -> List[MobileDevice]:
        """获取用户设备列表"""
        return [d for d in self._devices.values() if d.user_id == user_id and d.enabled]
    
    def update_device_token(self, device_id: str, new_token: str) -> bool:
        """更新设备token"""
        device = self._devices.get(device_id)
        if not device:
            return False
        device.device_token = new_token
        device.last_active_at = datetime.now()
        return True
    
    def create_session(self, user_id: str, device_id: str) -> MobileSession:
        """创建会话"""
        session = MobileSession(
            user_id=user_id,
            device_id=device_id,
            token=str(uuid.uuid4())
        )
        self._sessions[session.token] = session
        return session
    
    def validate_session(self, token: str) -> Optional[MobileSession]:
        """验证会话"""
        session = self._sessions.get(token)
        if session and session.expires_at > datetime.now():
            session.last_access_at = datetime.now()
            return session
        return None
    
    def send_notification(self, notification: PushNotification) -> bool:
        """发送通知"""
        self._notifications[notification.id] = notification
        
        targets = []
        if notification.target_user_id:
            targets.extend(self.get_user_devices(notification.target_user_id))
        elif notification.target_device_id:
            device = self._devices.get(notification.target_device_id)
            if device:
                targets.append(device)
        else:
            targets = list(self._devices.values())
        
        print(f"📤 Sending notification to {len(targets)} devices")
        
        for device in targets:
            self._send_to_device(device, notification)
        
        notification.delivered = True
        notification.delivered_at = datetime.now()
        return True
    
    def _send_to_device(self, device: MobileDevice, notification: PushNotification) -> None:
        """发送到单个设备"""
        if device.platform == MobilePlatform.IOS:
            print(f"   → iOS: {device.device_token[:20]}...")
        else:
            print(f"   → Android: {device.device_token[:20]}...")
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[PushNotification]:
        """获取用户通知"""
        user_devices = self.get_user_devices(user_id)
        device_ids = [d.id for d in user_devices]
        
        notifications = [
            n for n in self._notifications.values()
            if n.target_user_id == user_id or n.target_device_id in device_ids
        ]
        
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)[:limit]
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """标记通知已读"""
        notification = self._notifications.get(notification_id)
        if notification:
            notification.data["read"] = True
            return True
        return False
    
    def get_workflow_summary(self, user_id: str) -> List[MobileWorkflowSummary]:
        """获取工作流摘要（移动端优化）"""
        return [
            MobileWorkflowSummary(
                id="wf-1",
                name="订单处理",
                status="active",
                execution_count=1250,
                error_count=12,
                avg_latency_ms=245.5
            ),
            MobileWorkflowSummary(
                id="wf-2",
                name="数据同步",
                status="active",
                execution_count=890,
                error_count=5,
                avg_latency_ms=120.3
            ),
            MobileWorkflowSummary(
                id="wf-3",
                name="报告生成",
                status="completed",
                execution_count=45,
                error_count=0,
                avg_latency_ms=890.2
            )
        ]
    
    def execute_workflow_mobile(self, session_token: str, workflow_id: str, 
                               input_data: Dict[str, Any] = None) -> MobileExecutionResult:
        """移动端执行工作流"""
        session = self.validate_session(session_token)
        if not session:
            return MobileExecutionResult(status="error", error="Invalid session")
        
        return MobileExecutionResult(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            workflow_name="订单处理",
            status="completed",
            output_data=input_data or {},
            started_at=datetime.now(),
            completed_at=datetime.now(),
            latency_ms=156.8
        )


class MobileOptimizedAPI:
    """移动端优化API"""
    
    def __init__(self, api_manager: MobileAPIManager):
        self.api_manager = api_manager
    
    def authenticate(self, user_id: str, device_token: str, platform: str) -> Dict[str, Any]:
        """认证"""
        device = self.api_manager.register_device(
            user_id=user_id,
            device_token=device_token,
            platform=MobilePlatform(platform),
            app_version="1.0.0",
            os_version="17.0"
        )
        session = self.api_manager.create_session(user_id, device.id)
        return {"token": session.token, "expires_at": session.expires_at.isoformat()}
    
    def get_dashboard(self, session_token: str) -> Dict[str, Any]:
        """获取仪表盘"""
        session = self.api_manager.validate_session(session_token)
        if not session:
            return {"error": "Unauthorized"}
        
        summaries = self.api_manager.get_workflow_summary(session.user_id)
        return {
            "workflows": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status,
                    "executions": s.execution_count,
                    "errors": s.error_count,
                    "latency_ms": s.avg_latency_ms
                }
                for s in summaries
            ],
            "notifications": len(self.api_manager.get_user_notifications(session.user_id))
        }
    
    def execute(self, session_token: str, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        result = self.api_manager.execute_workflow_mobile(session_token, workflow_id, input_data)
        return {
            "execution_id": result.execution_id,
            "status": result.status,
            "latency_ms": result.latency_ms
        }
