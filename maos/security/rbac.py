"""
MAOS v9.0 - RBAC权限控制系统
完整的基于角色的访问控制实现
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict


class Permission(Enum):
    """系统权限"""
    # Agent权限
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    
    # 任务权限
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_EXECUTE = "task:execute"
    
    # 工作流权限
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    
    # 系统权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_METRICS = "system:metrics"
    
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 完全访问
    FULL_ACCESS = "*"


class RoleType(Enum):
    """系统角色"""
    ADMIN = "admin"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    AGENT = "agent"


@dataclass
class Role:
    """角色"""
    name: str
    description: str
    permissions: Set[str]
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        return permission in self.permissions or Permission.FULL_ACCESS.value in self.permissions


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    email: str
    roles: Set[str]
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RBACManager:
    """RBAC权限管理器"""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.role_hierarchy: Dict[str, List[str]] = defaultdict(list)
        
        # 初始化系统角色
        self._init_system_roles()
    
    def _init_system_roles(self):
        """初始化系统角色"""
        # 管理员角色 - 完全访问
        self.create_role(
            name=RoleType.ADMIN.value,
            description="系统管理员 - 完全访问",
            permissions=[p.value for p in Permission],
            is_system_role=True
        )
        
        # 操作员角色
        self.create_role(
            name=RoleType.OPERATOR.value,
            description="操作员 - 日常运维",
            permissions=[
                Permission.AGENT_READ.value,
                Permission.AGENT_EXECUTE.value,
                Permission.TASK_CREATE.value,
                Permission.TASK_READ.value,
                Permission.TASK_UPDATE.value,
                Permission.TASK_EXECUTE.value,
                Permission.WORKFLOW_READ.value,
                Permission.WORKFLOW_EXECUTE.value,
                Permission.SYSTEM_METRICS.value,
            ],
            is_system_role=True
        )
        
        # 开发者角色
        self.create_role(
            name=RoleType.DEVELOPER.value,
            description="开发者 - 开发调试",
            permissions=[
                Permission.AGENT_CREATE.value,
                Permission.AGENT_READ.value,
                Permission.AGENT_UPDATE.value,
                Permission.TASK_CREATE.value,
                Permission.TASK_READ.value,
                Permission.TASK_UPDATE.value,
                Permission.TASK_DELETE.value,
                Permission.TASK_EXECUTE.value,
                Permission.WORKFLOW_CREATE.value,
                Permission.WORKFLOW_READ.value,
                Permission.WORKFLOW_UPDATE.value,
                Permission.WORKFLOW_DELETE.value,
                Permission.WORKFLOW_EXECUTE.value,
            ],
            is_system_role=True
        )
        
        # 查看者角色
        self.create_role(
            name=RoleType.VIEWER.value,
            description="查看者 - 只读访问",
            permissions=[
                Permission.AGENT_READ.value,
                Permission.TASK_READ.value,
                Permission.WORKFLOW_READ.value,
                Permission.SYSTEM_METRICS.value,
            ],
            is_system_role=True
        )
        
        # Agent角色
        self.create_role(
            name=RoleType.AGENT.value,
            description="Agent - 自动化执行",
            permissions=[
                Permission.TASK_READ.value,
                Permission.TASK_UPDATE.value,
                Permission.TASK_EXECUTE.value,
            ],
            is_system_role=True
        )
    
    def create_role(
        self,
        name: str,
        description: str,
        permissions: List[str],
        is_system_role: bool = False
    ) -> Role:
        """创建角色"""
        role = Role(
            name=name,
            description=description,
            permissions=set(permissions),
            is_system_role=is_system_role
        )
        self.roles[name] = role
        return role
    
    def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: List[str]
    ) -> User:
        """创建用户"""
        # 验证角色存在
        for role_name in roles:
            if role_name not in self.roles:
                raise ValueError(f"Role not found: {role_name}")
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            roles=set(roles)
        )
        self.users[user_id] = user
        return user
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """分配角色"""
        user = self.users.get(user_id)
        role = self.roles.get(role_name)
        
        if not user or not role:
            return False
        
        user.roles.add(role_name)
        return True
    
    def remove_role(self, user_id: str, role_name: str) -> bool:
        """移除角色"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        if role_name in user.roles:
            user.roles.remove(role_name)
            return True
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户所有权限"""
        user = self.users.get(user_id)
        if not user:
            return set()
        
        if user.is_superuser:
            return {p.value for p in Permission}
        
        permissions = set()
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        
        return permissions
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有权限"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        if user.is_superuser:
            return True
        
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions or Permission.FULL_ACCESS.value in user_permissions
    
    def has_any_permission(self, user_id: str, permissions: List[str]) -> bool:
        """检查是否有任意权限"""
        return any(self.has_permission(user_id, p) for p in permissions)
    
    def has_all_permissions(self, user_id: str, permissions: List[str]) -> bool:
        """检查是否有所有权限"""
        return all(self.has_permission(user_id, p) for p in permissions)
    
    def check_access(self, user_id: str, resource_type: str, resource_id: str, action: str) -> bool:
        """检查资源访问权限"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        if user.is_superuser:
            return True
        
        # 构建权限字符串
        permission = f"{resource_type}:{action}"
        return self.has_permission(user_id, permission)
    
    def get_role_users(self, role_name: str) -> List[User]:
        """获取角色下的所有用户"""
        return [u for u in self.users.values() if role_name in u.roles]
    
    def list_roles(self) -> List[Dict]:
        """列出所有角色"""
        return [
            {
                "name": r.name,
                "description": r.description,
                "permissions": list(r.permissions),
                "is_system_role": r.is_system_role,
                "user_count": len(self.get_role_users(r.name))
            }
            for r in self.roles.values()
        ]
    
    def list_users(self) -> List[Dict]:
        """列出所有用户"""
        return [
            {
                "user_id": u.user_id,
                "username": u.username,
                "email": u.email,
                "roles": list(u.roles),
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in self.users.values()
        ]
