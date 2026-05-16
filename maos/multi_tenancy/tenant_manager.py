"""
Tenant Manager Module
=====================

Provides comprehensive tenant management capabilities including:
  - Tenant lifecycle management (create, activate, suspend, archive)
  - Resource quota tracking and enforcement
  - Tenant context propagation for multi-tenant applications
  - Tenant-aware repository pattern for data isolation
  - Cross-tenant admin operations with proper authorization

The module uses ContextVars for thread-safe tenant context management,
making it suitable for both synchronous and asynchronous applications.
"""

from typing import Optional, Any, Dict, List, Type, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextvars import ContextVar
import logging
import uuid

try:
    from sqlalchemy import Column, String, DateTime, ForeignKey
    from sqlalchemy.orm import Session, declared_attr
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T')

current_tenant_context: ContextVar[Optional['TenantContext']] = ContextVar(
    'current_tenant',
    default=None
)


class TenantIsolationStrategy(Enum):
    """Tenant isolation strategies for different security requirements"""
    SHARED_ROW = "shared_row"
    SHARED_SCHEMA = "shared_schema"
    DEDICATED_DB = "dedicated_db"


class TenantStatus(Enum):
    """Tenant lifecycle status"""
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class TenantQuota:
    """Resource quota configuration for tenant"""
    max_agents: int = 100
    max_tasks: int = 10000
    max_workflows: int = 1000
    max_storage_bytes: int = 1073741824
    max_api_requests_per_day: int = 1000000
    max_concurrent_jobs: int = 50
    used_agents: int = 0
    used_tasks: int = 0
    used_workflows: int = 0
    used_storage_bytes: int = 0
    
    def has_available_agents(self) -> bool:
        return self.used_agents < self.max_agents
    
    def has_available_tasks(self) -> bool:
        return self.used_tasks < self.max_tasks
    
    def has_available_workflows(self) -> bool:
        return self.used_workflows < self.max_workflows
    
    def get_utilization_percentage(self) -> Dict[str, float]:
        return {
            'agents': (self.used_agents / self.max_agents) * 100 if self.max_agents > 0 else 0,
            'tasks': (self.used_tasks / self.max_tasks) * 100 if self.max_tasks > 0 else 0,
            'workflows': (self.used_workflows / self.max_workflows) * 100 if self.max_workflows > 0 else 0,
            'storage': (self.used_storage_bytes / self.max_storage_bytes) * 100 if self.max_storage_bytes > 0 else 0
        }


@dataclass
class TenantContext:
    """Current tenant context for request/session"""
    tenant_id: str
    tenant_name: str
    isolation_strategy: TenantIsolationStrategy = TenantIsolationStrategy.SHARED_ROW
    is_admin_context: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tenant:
    """Tenant domain model"""
    tenant_id: str
    tenant_name: str
    domain: str
    isolation_strategy: TenantIsolationStrategy = TenantIsolationStrategy.SHARED_ROW
    status: TenantStatus = TenantStatus.ACTIVE
    quota: TenantQuota = field(default_factory=TenantQuota)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE
    
    def is_suspended(self) -> bool:
        return self.status == TenantStatus.SUSPENDED
    
    def get_context(self) -> TenantContext:
        return TenantContext(
            tenant_id=self.tenant_id,
            tenant_name=self.tenant_name,
            isolation_strategy=self.isolation_strategy
        )


def generate_tenant_id() -> str:
    """Generate unique tenant ID"""
    return f"tnt_{uuid.uuid4().hex[:24]}"


def set_current_tenant_context(tenant: Optional[Tenant] = None) -> Optional[TenantContext]:
    """Set current tenant context (thread-local / async-safe)"""
    if tenant is None:
        current_tenant_context.set(None)
        return None
    
    context = tenant.get_context()
    current_tenant_context.set(context)
    logger.debug(f"Tenant context set: {tenant.tenant_id}")
    return context


def get_current_tenant_context() -> Optional[TenantContext]:
    """Get current tenant context from context var"""
    return current_tenant_context.get()


def clear_current_tenant_context() -> None:
    """Clear current tenant context"""
    current_tenant_context.set(None)
    logger.debug("Tenant context cleared")


def set_admin_context() -> None:
    """Set special admin context for cross-tenant operations"""
    context = TenantContext(
        tenant_id="ADMIN",
        tenant_name="SYSTEM_ADMIN",
        isolation_strategy=TenantIsolationStrategy.SHARED_ROW,
        is_admin_context=True
    )
    current_tenant_context.set(context)
    logger.debug("Admin context activated")


class TenantAwareModelBase:
    """
    Base mixin for tenant-aware models (row-level isolation).
    
    All tables using this mixin will automatically include tenant_id
    and be filtered by the current tenant context.
    """
    
    if SQLALCHEMY_AVAILABLE:
        @declared_attr
        def tenant_id(cls):
            return Column(String(64), ForeignKey('tenants.tenant_id'), nullable=False, index=True)


class TenantManagementService:
    """
    Tenant management service for admin operations.
    
    Features:
      - Tenant creation, update, deletion
      - Tenant quota management
      - Tenant lifecycle management
      - Cross-tenant analytics (with authorization)
    """
    
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._tenant_context_stack: List[TenantContext] = []
    
    def create_tenant(
        self,
        tenant_name: str,
        domain: str,
        isolation_strategy: TenantIsolationStrategy = TenantIsolationStrategy.SHARED_ROW,
        custom_quota: Optional[TenantQuota] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            tenant_name: Display name for tenant
            domain: Primary domain for tenant
            isolation_strategy: Data isolation strategy
            custom_quota: Custom resource quotas (uses defaults if None)
            metadata: Additional tenant metadata
            created_by: User ID who created the tenant
        
        Returns:
            Created Tenant object
        """
        tenant_id = generate_tenant_id()
        
        tenant = Tenant(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            domain=domain,
            isolation_strategy=isolation_strategy,
            status=TenantStatus.PENDING,
            quota=custom_quota or TenantQuota(),
            metadata=metadata or {},
            created_by=created_by
        )
        
        self._tenants[tenant_id] = tenant
        logger.info(f"Tenant created: {tenant_id} - {tenant_name}")
        return tenant
    
    def activate_tenant(self, tenant_id: str) -> bool:
        """Activate a pending tenant"""
        tenant = self._tenants.get(tenant_id)
        if tenant and tenant.status == TenantStatus.PENDING:
            tenant.status = TenantStatus.ACTIVE
            tenant.updated_at = datetime.now()
            logger.info(f"Tenant activated: {tenant_id}")
            return True
        return False
    
    def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspend an active tenant"""
        tenant = self._tenants.get(tenant_id)
        if tenant and tenant.is_active():
            tenant.status = TenantStatus.SUSPENDED
            tenant.updated_at = datetime.now()
            tenant.metadata['suspension_reason'] = reason
            tenant.metadata['suspended_at'] = datetime.now().isoformat()
            logger.warning(f"Tenant suspended: {tenant_id} - {reason}")
            return True
        return False
    
    def archive_tenant(self, tenant_id: str) -> bool:
        """Archive a tenant (soft delete)"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.status = TenantStatus.ARCHIVED
            tenant.updated_at = datetime.now()
            logger.info(f"Tenant archived: {tenant_id}")
            return True
        return False
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Permanently delete a tenant"""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            logger.info(f"Tenant deleted: {tenant_id}")
            return True
        return False
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self._tenants.get(tenant_id)
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        for tenant in self._tenants.values():
            if tenant.domain == domain:
                return tenant
        return None
    
    def get_all_tenants(self, status_filter: Optional[TenantStatus] = None) -> List[Tenant]:
        """Get all tenants with optional status filter"""
        tenants = list(self._tenants.values())
        if status_filter:
            tenants = [t for t in tenants if t.status == status_filter]
        return tenants
    
    def update_tenant_quota(
        self,
        tenant_id: str,
        new_quota: TenantQuota
    ) -> bool:
        """Update tenant resource quotas"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            tenant.quota = new_quota
            tenant.updated_at = datetime.now()
            logger.info(f"Tenant quota updated: {tenant_id}")
            return True
        return False
    
    def update_tenant(
        self,
        tenant_id: str,
        tenant_name: Optional[str] = None,
        domain: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update tenant properties"""
        tenant = self._tenants.get(tenant_id)
        if tenant:
            if tenant_name is not None:
                tenant.tenant_name = tenant_name
            if domain is not None:
                tenant.domain = domain
            if metadata is not None:
                tenant.metadata.update(metadata)
            tenant.updated_at = datetime.now()
            logger.info(f"Tenant updated: {tenant_id}")
            return True
        return False
    
    def get_tenant_statistics(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive tenant statistics"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        
        return {
            'tenant_id': tenant.tenant_id,
            'tenant_name': tenant.tenant_name,
            'status': tenant.status.value,
            'isolation_strategy': tenant.isolation_strategy.value,
            'quota': tenant.quota.get_utilization_percentage(),
            'quota_details': {
                'max_agents': tenant.quota.max_agents,
                'used_agents': tenant.quota.used_agents,
                'max_tasks': tenant.quota.max_tasks,
                'used_tasks': tenant.quota.used_tasks,
                'max_workflows': tenant.quota.max_workflows,
                'used_workflows': tenant.quota.used_workflows,
            },
            'created_at': tenant.created_at.isoformat(),
            'updated_at': tenant.updated_at.isoformat(),
            'uptime_seconds': (datetime.now() - tenant.created_at).total_seconds(),
            'metadata': tenant.metadata
        }
    
    def get_system_wide_statistics(self) -> Dict[str, Any]:
        """Get cross-tenant statistics (admin only)"""
        active = [t for t in self._tenants.values() if t.is_active()]
        suspended = [t for t in self._tenants.values() if t.is_suspended()]
        pending = [t for t in self._tenants.values() if t.status == TenantStatus.PENDING]
        archived = [t for t in self._tenants.values() if t.status == TenantStatus.ARCHIVED]
        
        total_utilization: Dict[str, float] = {}
        if active:
            all_utilization = [t.quota.get_utilization_percentage() for t in active]
            total_utilization = {
                'avg_agents': sum(u['agents'] for u in all_utilization) / len(all_utilization),
                'avg_tasks': sum(u['tasks'] for u in all_utilization) / len(all_utilization),
                'avg_workflows': sum(u['workflows'] for u in all_utilization) / len(all_utilization),
                'avg_storage': sum(u['storage'] for u in all_utilization) / len(all_utilization)
            }
        
        return {
            'total_tenants': len(self._tenants),
            'active_tenants': len(active),
            'suspended_tenants': len(suspended),
            'pending_tenants': len(pending),
            'archived_tenants': len(archived),
            'avg_utilization': total_utilization,
            'last_updated': datetime.now().isoformat()
        }


class TenantAwareRepository(Generic[T]):
    """
    Tenant-aware repository implementing automatic filtering by tenant.
    
    All operations are automatically scoped to the current tenant context,
    unless an admin context is active (for cross-tenant operations).
    
    Usage:
      repo = TenantAwareRepository[AgentPersistenceModel](session, model_class)
      agents = repo.find_all()  # Only returns agents for current tenant
    """
    
    def __init__(
        self,
        session: Session,
        model_class: Type[T],
        tenant_field: str = 'tenant_id'
    ):
        if not SQLALCHEMY_AVAILABLE:
            raise RuntimeError("SQLAlchemy is required for tenant-aware repositories")
        
        self.session = session
        self.model_class = model_class
        self.tenant_field = tenant_field
    
    def _get_tenant_filter(self) -> Dict[str, Any]:
        """Get filter dict for tenant isolation"""
        context = get_current_tenant_context()
        if context and context.is_admin_context:
            return {}
        elif context:
            return {self.tenant_field: context.tenant_id}
        raise RuntimeError("No tenant context available")
    
    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID within current tenant"""
        filters = self._get_tenant_filter()
        filters['id'] = id
        return self.session.query(self.model_class).filter_by(**filters).first()
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities for current tenant with pagination"""
        filters = self._get_tenant_filter()
        return (
            self.session.query(self.model_class)
            .filter_by(**filters)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def create(self, entity: T) -> T:
        """Create entity with tenant_id automatically set"""
        context = get_current_tenant_context()
        if context and not context.is_admin_context:
            setattr(entity, self.tenant_field, context.tenant_id)
        elif not context:
            raise RuntimeError("No tenant context available for create operation")
        
        self.session.add(entity)
        self.session.flush()
        return entity
    
    def update(self, entity: T) -> T:
        """Update entity (tenant-aware security handled by session)"""
        self.session.add(entity)
        self.session.flush()
        return entity
    
    def delete(self, id: int) -> bool:
        """Delete entity (tenant-aware)"""
        entity = self.find_by_id(id)
        if entity:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False
    
    def find_by_custom_field(
        self,
        field_name: str,
        field_value: Any
    ) -> List[T]:
        """Find entities by custom field (within tenant)"""
        filters = self._get_tenant_filter()
        filters[field_name] = field_value
        return self.session.query(self.model_class).filter_by(**filters).all()
    
    def count(self) -> int:
        """Count entities for current tenant"""
        filters = self._get_tenant_filter()
        return self.session.query(self.model_class).filter_by(**filters).count()


class TenantScopedContextManager:
    """
    Context manager for temporarily switching tenant context.
    
    Usage:
      with TenantScopedContextManager(tenant):
          # All operations inside use tenant's context
          agents = agent_repository.find_all()
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.previous_context: Optional[TenantContext] = None
    
    def __enter__(self) -> 'TenantScopedContextManager':
        self.previous_context = get_current_tenant_context()
        set_current_tenant_context(self.tenant)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self.previous_context:
            current_tenant_context.set(self.previous_context)
        else:
            clear_current_tenant_context()
        return False


_tenant_service_instance: Optional[TenantManagementService] = None


def get_tenant_service() -> TenantManagementService:
    """Get singleton tenant management service instance"""
    global _tenant_service_instance
    if _tenant_service_instance is None:
        _tenant_service_instance = TenantManagementService()
    return _tenant_service_instance
