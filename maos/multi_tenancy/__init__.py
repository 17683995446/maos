"""
Multi-Tenancy Module for MAOS
=============================

Provides comprehensive multi-tenant data isolation and management capabilities.

Key Features:
  - Tenant isolation strategies (row-level, schema-level, dedicated)
  - Tenant context management with thread-safety
  - Resource quota enforcement
  - Cross-tenant admin operations
  - Tenant-aware repository pattern

Usage:
    from maos.multi_tenancy import TenantManagementService, Tenant, TenantContext

    service = TenantManagementService()
    tenant = service.create_tenant("Acme Corp", "acme.com")
"""

from maos.multi_tenancy.tenant_manager import (
    Tenant,
    TenantContext,
    TenantQuota,
    TenantManagementService,
    TenantAwareRepository,
    TenantScopedContextManager,
    TenantIsolationStrategy,
    TenantStatus,
    generate_tenant_id,
    set_current_tenant_context,
    get_current_tenant_context,
    clear_current_tenant_context,
    set_admin_context,
    get_tenant_service,
)

__all__ = [
    "Tenant",
    "TenantContext",
    "TenantQuota",
    "TenantManagementService",
    "TenantAwareRepository",
    "TenantScopedContextManager",
    "TenantIsolationStrategy",
    "TenantStatus",
    "generate_tenant_id",
    "set_current_tenant_context",
    "get_current_tenant_context",
    "clear_current_tenant_context",
    "set_admin_context",
    "get_tenant_service",
]
