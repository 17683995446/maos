"""
MAOS v5.0 - 安全模块
API密钥认证和简单授权
"""

import hashlib
import secrets
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class APIKey:
    """API密钥"""
    key_id: str
    key_hash: str
    name: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True


class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        self._rate_limits: Dict[str, List[float]] = {}
        self._rate_limit_window = 60  # 1分钟窗口
        self._rate_limit_max = 100  # 每分钟最多100次
    
    def generate_key(self, name: str, scopes: List[str] = None, expires_in_days: int = None) -> tuple[str, str]:
        """
        生成新的API密钥
        
        返回: (key_id, secret_key)
        """
        key_id = f"mk_{secrets.token_hex(8)}"
        secret_key = secrets.token_urlsafe(32)
        
        # 哈希存储
        key_hash = hashlib.sha256(secret_key.encode()).hexdigest()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            scopes=scopes or ["read"],
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        self._keys[key_id] = api_key
        
        # 返回完整的密钥（仅显示一次）
        full_key = f"{key_id}.{secret_key}"
        return key_id, full_key
    
    def verify_key(self, api_key: str) -> Optional[APIKey]:
        """验证API密钥"""
        try:
            parts = api_key.split(".")
            if len(parts) != 2:
                return None
            
            key_id, secret = parts
            key_hash = hashlib.sha256(secret.encode()).hexdigest()
            
            api_key_obj = self._keys.get(key_id)
            if not api_key_obj:
                return None
            
            if api_key_obj.key_hash != key_hash:
                return None
            
            if not api_key_obj.is_active:
                return None
            
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now():
                return None
            
            # 更新最后使用时间
            api_key_obj.last_used = datetime.now()
            
            return api_key_obj
        except Exception:
            return None
    
    def check_rate_limit(self, key_id: str) -> bool:
        """检查速率限制"""
        now = time.time()
        
        if key_id not in self._rate_limits:
            self._rate_limits[key_id] = []
        
        # 清理旧记录
        self._rate_limits[key_id] = [
            t for t in self._rate_limits[key_id]
            if now - t < self._rate_limit_window
        ]
        
        if len(self._rate_limits[key_id]) >= self._rate_limit_max:
            return False
        
        self._rate_limits[key_id].append(now)
        return True
    
    def revoke_key(self, key_id: str) -> bool:
        """撤销密钥"""
        if key_id in self._keys:
            self._keys[key_id].is_active = False
            return True
        return False
    
    def get_key_info(self, key_id: str) -> Optional[Dict]:
        """获取密钥信息"""
        api_key = self._keys.get(key_id)
        if not api_key:
            return None
        
        return {
            'key_id': api_key.key_id,
            'name': api_key.name,
            'scopes': api_key.scopes,
            'created_at': api_key.created_at.isoformat(),
            'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
            'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
            'is_active': api_key.is_active
        }


class SimpleAuth:
    """简单认证"""
    
    def __init__(self):
        self.key_manager = APIKeyManager()
    
    def create_api_key(self, name: str, scopes: List[str] = None) -> tuple[str, str]:
        """创建API密钥"""
        return self.key_manager.generate_key(name, scopes)
    
    def authenticate(self, api_key: str) -> Optional[APIKey]:
        """认证"""
        return self.key_manager.verify_key(api_key)
    
    def check_permission(self, api_key: str, required_scope: str) -> bool:
        """检查权限"""
        key_obj = self.authenticate(api_key)
        if not key_obj:
            return False
        return required_scope in key_obj.scopes


# 全局认证实例
_auth: Optional[SimpleAuth] = None


def get_auth() -> SimpleAuth:
    """获取认证实例"""
    global _auth
    if _auth is None:
        _auth = SimpleAuth()
    return _auth
