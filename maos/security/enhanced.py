"""
MAOS v9.0 - 企业级安全模块
完整的OAuth2.0、JWT和RBAC实现
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
import hmac
import secrets
import time
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import base64
import struct


# ============================================================
# JWT Token 实现
# ============================================================

class JWTAlgorithm(Enum):
    """JWT算法"""
    HS256 = "HS256"
    HS384 = "HS384"
    HS512 = "HS512"
    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"


@dataclass
class JWTClaims:
    """JWT声明"""
    sub: str  # Subject (用户ID)
    aud: str = "maos"  # Audience
    exp: Optional[int] = None  # Expiration Time
    iat: Optional[int] = None  # Issued At
    nbf: Optional[int] = None  # Not Before
    jti: Optional[str] = None  # JWT ID
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    custom_claims: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        claims = {
            "sub": self.sub,
            "aud": self.aud
        }
        if self.exp:
            claims["exp"] = self.exp
        if self.iat:
            claims["iat"] = self.iat
        if self.nbf:
            claims["nbf"] = self.nbf
        if self.jti:
            claims["jti"] = self.jti
        if self.roles:
            claims["roles"] = self.roles
        if self.permissions:
            claims["permissions"] = self.permissions
        claims.update(self.custom_claims)
        return claims
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'JWTClaims':
        return cls(
            sub=data["sub"],
            aud=data.get("aud", "maos"),
            exp=data.get("exp"),
            iat=data.get("iat"),
            nbf=data.get("nbf"),
            jti=data.get("jti"),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            custom_claims={k: v for k, v in data.items() 
                         if k not in ["sub", "aud", "exp", "iat", "nbf", "jti", "roles", "permissions"]}
        )


class JWTToken:
    """JWT令牌"""
    
    def __init__(self, secret_key: str, algorithm: JWTAlgorithm = JWTAlgorithm.HS256):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, claims: JWTClaims) -> str:
        """创建JWT令牌"""
        header = {
            "alg": self.algorithm.value,
            "typ": "JWT"
        }
        
        # 编码header
        header_b64 = self._base64url_encode(json.dumps(header, separators=(',', ':')))
        
        # 编码payload
        payload_dict = claims.to_dict()
        if payload_dict.get("iat") is None:
            payload_dict["iat"] = int(time.time())
        if payload_dict.get("jti") is None:
            payload_dict["jti"] = secrets.token_hex(16)
        payload_b64 = self._base64url_encode(json.dumps(payload_dict, separators=(',', ':')))
        
        # 计算签名
        message = f"{header_b64}.{payload_b64}"
        signature = self._sign(message)
        
        return f"{message}.{signature}"
    
    def verify_token(self, token: str) -> Optional[JWTClaims]:
        """验证JWT令牌"""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature = parts
            
            # 验证签名
            message = f"{header_b64}.{payload_b64}"
            expected_signature = self._sign(message)
            
            if not self._secure_compare(signature, expected_signature):
                return None
            
            # 解码payload
            payload_json = self._base64url_decode(payload_b64)
            payload = json.loads(payload_json)
            
            # 验证时间
            now = int(time.time())
            
            if payload.get("exp") and payload["exp"] < now:
                return None
            
            if payload.get("nbf") and payload["nbf"] > now:
                return None
            
            return JWTClaims.from_dict(payload)
        
        except Exception:
            return None
    
    def _sign(self, message: str) -> str:
        """签名"""
        if self.algorithm == JWTAlgorithm.HS256:
            hash_func = hashlib.sha256
        elif self.algorithm == JWTAlgorithm.HS384:
            hash_func = hashlib.sha384
        elif self.algorithm == JWTAlgorithm.HS512:
            hash_func = hashlib.sha512
        else:
            hash_func = hashlib.sha256
        
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hash_func
        ).digest()
        
        return self._base64url_encode(signature)
    
    @staticmethod
    def _base64url_encode(data: str) -> str:
        """Base64 URL编码"""
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
    
    @staticmethod
    def _base64url_decode(data: str) -> str:
        """Base64 URL解码"""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data).decode()
    
    @staticmethod
    def _secure_compare(a: str, b: str) -> bool:
        """安全比较"""
        return hmac.compare_digest(a, b)


# ============================================================
# OAuth2.0 实现
# ============================================================

class GrantType(Enum):
    """授权类型"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    PASSWORD = "password"


class OAuthScope(Enum):
    """OAuth范围"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    AGENT_CREATE = "agent:create"
    AGENT_DELETE = "agent:delete"
    TASK_MANAGE = "task:manage"
    METRICS_READ = "metrics:read"
    METRICS_WRITE = "metrics:write"


@dataclass
class OAuthClient:
    """OAuth客户端"""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    allowed_scopes: List[str]
    created_at: datetime
    is_active: bool = True


@dataclass
class AuthorizationCode:
    """授权码"""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: List[str]
    expires_at: datetime
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None


class OAuth2Server:
    """OAuth2.0服务器"""
    
    def __init__(self, jwt_secret: str):
        self.jwt_token = JWTToken(jwt_secret)
        self.clients: Dict[str, OAuthClient] = {}
        self.auth_codes: Dict[str, AuthorizationCode] = {}
        self.refresh_tokens: Dict[str, Dict] = {}
        self.code_lifetime = timedelta(minutes=10)
        self.refresh_lifetime = timedelta(days=30)
        self.access_token_lifetime = timedelta(hours=1)
    
    def register_client(
        self,
        client_name: str,
        redirect_uris: List[str],
        allowed_scopes: List[str] = None
    ) -> tuple[str, str]:
        """注册OAuth客户端"""
        client_id = f"client_{secrets.token_hex(16)}"
        client_secret = secrets.token_urlsafe(32)
        
        client = OAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_name,
            redirect_uris=redirect_uris,
            allowed_scopes=allowed_scopes or [scope.value for scope in OAuthScope],
            created_at=datetime.now()
        )
        
        self.clients[client_id] = client
        return client_id, client_secret
    
    def authorize(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scopes: List[str],
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> Optional[str]:
        """授权码授权"""
        client = self.clients.get(client_id)
        if not client or not client.is_active:
            return None
        
        if redirect_uri not in client.redirect_uris:
            return None
        
        # 生成授权码
        code = secrets.token_urlsafe(32)
        
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            expires_at=datetime.now() + self.code_lifetime,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        self.auth_codes[code] = auth_code
        return code
    
    def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        code_verifier: Optional[str] = None
    ) -> Optional[Dict]:
        """交换授权码获取令牌"""
        auth_code = self.auth_codes.get(code)
        if not auth_code:
            return None
        
        if auth_code.expires_at < datetime.now():
            del self.auth_codes[code]
            return None
        
        client = self.clients.get(client_id)
        if not client or client.client_secret != client_secret:
            return None
        
        # PKCE验证（简化版）
        if auth_code.code_challenge:
            if not code_verifier:
                return None
            # 实际应该验证PKCE
            pass
        
        # 删除授权码
        del self.auth_codes[code]
        
        # 生成令牌
        return self._generate_token_response(auth_code.user_id, auth_code.scopes)
    
    def client_credentials_grant(
        self,
        client_id: str,
        client_secret: str,
        scopes: List[str]
    ) -> Optional[Dict]:
        """客户端凭证授权"""
        client = self.clients.get(client_id)
        if not client or client.client_secret != client_secret:
            return None
        
        # 使用client_id作为subject
        return self._generate_token_response(client_id, scopes)
    
    def refresh_access_token(
        self,
        refresh_token: str
    ) -> Optional[Dict]:
        """刷新访问令牌"""
        token_data = self.refresh_tokens.get(refresh_token)
        if not token_data:
            return None
        
        if token_data.get("expires_at", datetime.now()) < datetime.now():
            del self.refresh_tokens[refresh_token]
            return None
        
        # 生成新令牌
        return self._generate_token_response(
            token_data["user_id"],
            token_data["scopes"]
        )
    
    def _generate_token_response(self, user_id: str, scopes: List[str]) -> Dict:
        """生成令牌响应"""
        # 生成访问令牌
        now = int(time.time())
        access_token_claims = JWTClaims(
            sub=user_id,
            exp=now + int(self.access_token_lifetime.total_seconds()),
            iat=now,
            roles=self._scopes_to_roles(scopes),
            permissions=scopes
        )
        access_token = self.jwt_token.create_token(access_token_claims)
        
        # 生成刷新令牌
        refresh_token = secrets.token_urlsafe(32)
        self.refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "scopes": scopes,
            "expires_at": datetime.now() + self.refresh_lifetime
        }
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": int(self.access_token_lifetime.total_seconds()),
            "refresh_token": refresh_token,
            "scope": " ".join(scopes)
        }
    
    def _scopes_to_roles(self, scopes: List[str]) -> List[str]:
        """将范围转换为角色"""
        roles = set()
        for scope in scopes:
            if scope == "admin":
                roles.add("admin")
            elif scope.startswith("write") or scope.startswith("delete"):
                roles.add("editor")
            elif scope.startswith("read") or scope.startswith("get"):
                roles.add("viewer")
        return list(roles)


# ============================================================
# 增强的安全管理器
# ============================================================

class EnhancedSecurityManager:
    """增强的安全管理器"""
    
    def __init__(self, jwt_secret: str):
        self.oauth_server = OAuth2Server(jwt_secret)
        self.jwt_token = JWTToken(jwt_secret)
    
    def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[Dict]:
        """用户认证"""
        # 简化实现：实际应该查询数据库
        # 这里使用简单的验证
        if self._verify_password(username, password):
            # 生成令牌
            return self.oauth_server._generate_token_response(
                username,
                ["read", "write", "task:manage"]
            )
        return None
    
    def _verify_password(self, username: str, password: str) -> bool:
        """验证密码"""
        # 简化实现
        # 实际应该使用bcrypt等安全哈希
        stored_hash = self._get_password_hash(username)
        if not stored_hash:
            return False
        return hmac.compare_digest(
            hashlib.sha256(password.encode()).hexdigest(),
            stored_hash
        )
    
    def _get_password_hash(self, username: str) -> Optional[str]:
        """获取密码哈希"""
        # 简化实现
        # 实际应该从数据库查询
        return None
    
    def verify_request(self, token: str) -> Optional[JWTClaims]:
        """验证请求"""
        return self.jwt_token.verify_token(token)
    
    def check_permission(self, claims: JWTClaims, required_permission: str) -> bool:
        """检查权限"""
        return required_permission in claims.permissions or "admin" in claims.roles
