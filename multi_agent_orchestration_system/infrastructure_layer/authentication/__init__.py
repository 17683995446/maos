"""
Infrastructure Layer - Authentication Module
==========================================

Provides JWT-based authentication and authorization.
Part of the production hardening Phase 1 improvements.

Key Features:
  - JWT token generation and validation
  - Role-based access control (RBAC)
  - API key authentication support
  - Rate limiting middleware
  - Token refresh and revocation

Architecture:
  - Uses PyJWT for token handling
  - Supports HS256, HS384, HS512 algorithms
  - Integrates with Redis for token blacklist
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import logging

try:
    import jwt
    from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """Fine-grained permissions"""
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_VIEW_METRICS = "admin:view_metrics"
    ADMIN_SYSTEM_CONFIG = "admin:system_config"


ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: set(Permission),
    UserRole.OPERATOR: {
        Permission.AGENT_READ, Permission.AGENT_UPDATE,
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ,
        Permission.WORKFLOW_UPDATE, Permission.WORKFLOW_EXECUTE
    },
    UserRole.DEVELOPER: {
        Permission.AGENT_READ, Permission.TASK_CREATE, Permission.TASK_READ,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_READ, Permission.WORKFLOW_EXECUTE
    },
    UserRole.VIEWER: {
        Permission.AGENT_READ, Permission.TASK_READ, Permission.WORKFLOW_READ
    },
    UserRole.GUEST: {
        Permission.WORKFLOW_READ
    }
}


@dataclass
class UserAccount:
    """User account data model"""
    username: str
    role: UserRole = UserRole.VIEWER
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    is_superuser: bool = False
    api_keys: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        if self.is_superuser:
            return True
        if permission in self.permissions:
            return True
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        return all(self.has_permission(p) for p in permissions)


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    sub: str
    username: str
    role: str
    permissions: List[str]
    issued_at: int
    expires_at: int
    token_type: str = "access"
    api_key_id: Optional[str] = None


@dataclass
class AuthenticationConfiguration:
    """Authentication configuration"""
    jwt_secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key_prefix: str = "maos_"
    api_key_length: int = 32
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    enable_api_key_auth: bool = True
    enable_jwt_auth: bool = True


class JWTAuthenticationService:
    """
    JWT-based authentication service.
    
    Features:
      - Token generation and validation
      - Token refresh
      - Token blacklist/revocation
      - Multi-algorithm support (HS256, HS384, HS512)
    
    Usage:
      auth_service = JWTAuthenticationService(config)
      token = auth_service.create_access_token(user)
      is_valid = auth_service.verify_token(token)
    """
    
    def __init__(self, config: Optional[AuthenticationConfiguration] = None):
        self.config = config or AuthenticationConfiguration()
        self._token_blacklist: Set[str] = set()
        self._revoked_api_keys: Set[str] = set()
        
        if not JWT_AVAILABLE:
            logger.warning("PyJWT not available, JWT authentication disabled")
    
    def create_access_token(self, user: UserAccount) -> str:
        """
        Create JWT access token for user.
        
        Args:
            user: User account to create token for
        
        Returns:
            Encoded JWT token string
        """
        if not JWT_AVAILABLE:
            raise RuntimeError("JWT library not available")
        
        now = datetime.now()
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            'sub': user.username,
            'username': user.username,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions],
            'iat': int(now.timestamp()),
            'exp': int(expires.timestamp()),
            'type': 'access'
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        logger.info(f"Access token created for user: {user.username}")
        return token
    
    def create_refresh_token(self, user: UserAccount) -> str:
        """Create JWT refresh token for user"""
        if not JWT_AVAILABLE:
            raise RuntimeError("JWT library not available")
        
        now = datetime.now()
        expires = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            'sub': user.username,
            'username': user.username,
            'iat': int(now.timestamp()),
            'exp': int(expires.timestamp()),
            'type': 'refresh'
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        logger.info(f"Refresh token created for user: {user.username}")
        return token
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verify JWT token and extract payload.
        
        Args:
            token: JWT token string
        
        Returns:
            TokenPayload if valid, None if invalid
        """
        if not JWT_AVAILABLE:
            return None
        
        if token in self._token_blacklist:
            logger.warning("Attempted to use blacklisted token")
            return None
        
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            return TokenPayload(
                sub=payload['sub'],
                username=payload['username'],
                role=payload['role'],
                permissions=payload.get('permissions', []),
                issued_at=payload['iat'],
                expires_at=payload['exp'],
                token_type=payload.get('type', 'access')
            )
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Add token to blacklist (logout)"""
        self._token_blacklist.add(token)
        logger.info("Token added to blacklist")
        return True
    
    def refresh_access_token(self, refresh_token: str, user: UserAccount) -> Optional[str]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            user: User account to create new access token for
        
        Returns:
            New access token or None if refresh token invalid
        """
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.token_type != 'refresh':
            return None
        
        if payload.username != user.username:
            return None
        
        return self.create_access_token(user)
    
    def generate_api_key(self, user: UserAccount) -> str:
        """
        Generate API key for user.
        
        Args:
            user: User account to generate key for
        
        Returns:
            API key string
        """
        if not self.config.enable_api_key_auth:
            raise RuntimeError("API key authentication is disabled")
        
        key_id = secrets.token_hex(16)
        key_secret = secrets.token_urlsafe(self.config.api_key_length)
        api_key = f"{self.config.api_key_prefix}{key_id}_{key_secret}"
        
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
        user.api_keys.append(hashed_key)
        
        logger.info(f"API key generated for user: {user.username}")
        return api_key
    
    def verify_api_key(self, api_key: str, users: Dict[str, UserAccount]) -> Optional[UserAccount]:
        """
        Verify API key and return associated user.
        
        Args:
            api_key: API key string
            users: Dictionary of username -> UserAccount
        
        Returns:
            UserAccount if valid, None otherwise
        """
        if not self.config.enable_api_key_auth:
            return None
        
        if api_key in self._revoked_api_keys:
            return None
        
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
        
        for user in users.values():
            if hashed_key in user.api_keys and user.is_active:
                user.last_login = datetime.now()
                logger.info(f"API key authenticated user: {user.username}")
                return user
        
        return None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key"""
        self._revoked_api_keys.add(api_key)
        logger.info("API key revoked")
        return True


class RoleBasedAccessControl:
    """
    Role-Based Access Control (RBAC) service.
    
    Features:
      - Permission checking
      - Role hierarchy
      - Permission inheritance
      - Access audit logging
    
    Usage:
      rbac = RoleBasedAccessControl()
      if rbac.check_permission(user, Permission.TASK_CREATE):
          create_task()
    """
    
    def __init__(self):
        self._permission_cache: Dict[str, bool] = {}
        self._access_log: List[Dict[str, Any]] = []
    
    def check_permission(
        self,
        user: UserAccount,
        permission: Permission,
        resource_owner: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission to perform action.
        
        Args:
            user: User to check
            permission: Required permission
            resource_owner: Owner of resource (for ownership checks)
        
        Returns:
            True if user has permission
        """
        has_permission = user.has_permission(permission)
        
        self._log_access_check(user, permission, has_permission, resource_owner)
        
        if not has_permission and resource_owner == user.username:
            return True
        
        return has_permission
    
    def check_any_permission(
        self,
        user: UserAccount,
        permissions: List[Permission]
    ) -> bool:
        """Check if user has any of the specified permissions"""
        return user.has_any_permission(permissions)
    
    def check_all_permissions(
        self,
        user: UserAccount,
        permissions: List[Permission]
    ) -> bool:
        """Check if user has all specified permissions"""
        return user.has_all_permissions(permissions)
    
    def get_user_permissions(self, user: UserAccount) -> Set[Permission]:
        """Get all permissions for user (including role-based)"""
        return ROLE_PERMISSIONS.get(user.role, set()) | user.permissions
    
    def grant_permission(self, user: UserAccount, permission: Permission) -> None:
        """Grant additional permission to user"""
        user.permissions.add(permission)
        logger.info(f"Permission {permission.value} granted to user: {user.username}")
    
    def revoke_permission(self, user: UserAccount, permission: Permission) -> None:
        """Revoke permission from user"""
        user.permissions.discard(permission)
        logger.info(f"Permission {permission.value} revoked from user: {user.username}")
    
    def _log_access_check(
        self,
        user: UserAccount,
        permission: Permission,
        granted: bool,
        resource_owner: Optional[str]
    ) -> None:
        """Log access check for audit trail"""
        self._access_log.append({
            'timestamp': datetime.now().isoformat(),
            'username': user.username,
            'permission': permission.value,
            'granted': granted,
            'resource_owner': resource_owner
        })
        
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-5000:]
    
    def get_access_log(
        self,
        username: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get access log entries"""
        log = self._access_log
        
        if username:
            log = [entry for entry in log if entry['username'] == username]
        
        return log[-limit:]


class RateLimitMiddleware:
    """
    Rate limiting middleware using sliding window algorithm.
    
    Features:
      - Token bucket algorithm
      - Per-user rate limiting
      - Burst allowance
      - Redis backend support (optional)
    
    Usage:
      limiter = RateLimitMiddleware(requests_per_minute=60)
      if not limiter.check_rate_limit(user_id):
          raise RateLimitExceeded()
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        use_redis: bool = False
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._user_timestamps: Dict[str, List[float]] = {}
        self._redis_client = None
        self._use_redis = use_redis
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: User ID or API key identifier
        
        Returns:
            True if request allowed, False if rate limited
        """
        current_time = datetime.now().timestamp()
        window_start = current_time - 60
        
        if identifier not in self._user_timestamps:
            self._user_timestamps[identifier] = []
        
        timestamps = self._user_timestamps[identifier]
        
        timestamps = [ts for ts in timestamps if ts > window_start]
        
        timestamps.append(current_time)
        self._user_timestamps[identifier] = timestamps
        
        total_requests = len(timestamps)
        
        burst_used = sum(1 for ts in timestamps if ts > current_time - 1)
        
        if burst_used > self.burst_size:
            logger.warning(f"Rate limit exceeded (burst) for: {identifier}")
            return False
        
        if total_requests > self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for: {identifier}")
            return False
        
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests in current window"""
        if identifier not in self._user_timestamps:
            return self.requests_per_minute
        
        current_time = datetime.now().timestamp()
        window_start = current_time - 60
        
        active_timestamps = [
            ts for ts in self._user_timestamps[identifier]
            if ts > window_start
        ]
        
        return max(0, self.requests_per_minute - len(active_timestamps))
    
    def reset_rate_limit(self, identifier: str) -> None:
        """Reset rate limit for identifier"""
        if identifier in self._user_timestamps:
            del self._user_timestamps[identifier]
        logger.info(f"Rate limit reset for: {identifier}")


def get_default_admin_user() -> UserAccount:
    """Get default admin user for initial setup"""
    return UserAccount(
        username="admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
        metadata={'created_by': 'system', 'description': 'Default admin user'}
    )


if __name__ == "__main__":
    config = AuthenticationConfiguration(
        jwt_secret_key="your-secret-key-change-in-production",
        access_token_expire_minutes=30
    )
    
    auth_service = JWTAuthenticationService(config)
    rbac = RoleBasedAccessControl()
    rate_limiter = RateLimitMiddleware(requests_per_minute=60)
    
    admin = get_default_admin_user()
    
    token = auth_service.create_access_token(admin)
    print(f"Token: {token[:50]}...")
    
    payload = auth_service.verify_token(token)
    print(f"Valid: {payload is not None}")
    print(f"Username: {payload.username if payload else 'N/A'}")
    print(f"Role: {payload.role if payload else 'N/A'}")
    
    print(f"Has AGENT_CREATE permission: {rbac.check_permission(admin, Permission.AGENT_CREATE)}")
    print(f"Has GUEST permission: {rbac.check_permission(admin, Permission.GUEST)}")
    
    print(f"Rate limit check: {rate_limiter.check_rate_limit('test_user')}")
