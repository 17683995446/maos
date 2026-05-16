"""
MAOS v13.0 - Multi-Tenant SaaS Layer & Billing System
多租户SaaS层与计费系统
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid


class TenantIsolationLevel(Enum):
    """租户隔离级别"""
    ROW = "row"  # 行级隔离（共享数据库和Schema）
    SCHEMA = "schema"  # Schema级隔离（共享数据库，独立Schema）
    DATABASE = "database"  # 数据库级隔离（独立数据库）


class SubscriptionPlan(Enum):
    """订阅计划"""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class BillingStatus(Enum):
    """计费状态"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIAL = "trial"


@dataclass
class TenantQuota:
    """租户配额"""
    max_workflows: int = 10
    max_executions_per_month: int = 1000
    max_storage_gb: float = 1.0
    max_agents: int = 5
    api_rate_limit_per_minute: int = 100


@dataclass
class PlanConfig:
    """计划配置"""
    plan: SubscriptionPlan
    price_monthly: float
    price_yearly: float
    quota: TenantQuota
    features: List[str] = field(default_factory=list)
    sla_availability: float = 99.9


# 预定义计划配置
PLAN_CONFIGS = {
    SubscriptionPlan.FREE: PlanConfig(
        plan=SubscriptionPlan.FREE,
        price_monthly=0.0,
        price_yearly=0.0,
        quota=TenantQuota(
            max_workflows=3,
            max_executions_per_month=1000,
            max_storage_gb=0.5,
            max_agents=2,
            api_rate_limit_per_minute=50
        ),
        features=["基础工作流", "社区支持", "API访问"],
        sla_availability=99.0
    ),
    SubscriptionPlan.PRO: PlanConfig(
        plan=SubscriptionPlan.PRO,
        price_monthly=49.0,
        price_yearly=499.0,
        quota=TenantQuota(
            max_workflows=100,
            max_executions_per_month=50000,
            max_storage_gb=10.0,
            max_agents=20,
            api_rate_limit_per_minute=500
        ),
        features=["无限工作流", "邮件支持", "高级分析", "插件市场"],
        sla_availability=99.9
    ),
    SubscriptionPlan.BUSINESS: PlanConfig(
        plan=SubscriptionPlan.BUSINESS,
        price_monthly=199.0,
        price_yearly=1999.0,
        quota=TenantQuota(
            max_workflows=1000,
            max_executions_per_month=200000,
            max_storage_gb=100.0,
            max_agents=100,
            api_rate_limit_per_minute=2000
        ),
        features=["团队协作", "SLA 99.9%", "优先支持", "SSO"],
        sla_availability=99.9
    ),
    SubscriptionPlan.ENTERPRISE: PlanConfig(
        plan=SubscriptionPlan.ENTERPRISE,
        price_monthly=999.0,
        price_yearly=9999.0,
        quota=TenantQuota(
            max_workflows=10000,
            max_executions_per_month=1000000,
            max_storage_gb=1000.0,
            max_agents=1000,
            api_rate_limit_per_minute=10000
        ),
        features=["私有部署", "定制开发", "专属支持", "SLA 99.99%"],
        sla_availability=99.99
    )
}


@dataclass
class Tenant:
    """租户"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: str = ""
    isolation_level: TenantIsolationLevel = TenantIsolationLevel.ROW
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    billing_status: BillingStatus = BillingStatus.TRIAL
    quota: TenantQuota = field(default_factory=TenantQuota)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    trial_ends_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.subscription_plan in PLAN_CONFIGS:
            self.quota = PLAN_CONFIGS[self.subscription_plan].quota
        if self.billing_status == BillingStatus.TRIAL and not self.trial_ends_at:
            self.trial_ends_at = datetime.now() + timedelta(days=14)

    def is_trial_active(self) -> bool:
        """检查试用期是否激活"""
        if self.billing_status != BillingStatus.TRIAL:
            return False
        return self.trial_ends_at and self.trial_ends_at > datetime.now()

    def is_active(self) -> bool:
        """检查租户是否活跃"""
        if self.billing_status in [BillingStatus.CANCELLED]:
            return False
        if self.billing_status == BillingStatus.TRIAL:
            return self.is_trial_active()
        return True


@dataclass
class UsageMetric:
    """用量指标"""
    tenant_id: str
    metric_type: str  # "executions", "storage", "api_calls"
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Invoice:
    """发票"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: str = "draft"  # draft, paid, failed, void
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Payment:
    """支付记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    invoice_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    payment_method: str = ""  # "stripe", "paypal", etc.
    status: str = "pending"  # pending, succeeded, failed
    transaction_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class TenantManager:
    """租户管理器"""

    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._usage: Dict[str, List[UsageMetric]] = {}
        self._invoices: Dict[str, Invoice] = {}
        self._payments: Dict[str, Payment] = {}

    def create_tenant(
        self,
        name: str,
        domain: str,
        plan: SubscriptionPlan = SubscriptionPlan.FREE,
        isolation_level: TenantIsolationLevel = TenantIsolationLevel.ROW
    ) -> Tenant:
        """创建租户"""
        tenant = Tenant(
            name=name,
            domain=domain,
            subscription_plan=plan,
            isolation_level=isolation_level,
            billing_status=BillingStatus.TRIAL if plan == SubscriptionPlan.FREE else BillingStatus.ACTIVE
        )
        self._tenants[tenant.id] = tenant
        print(f"✅ Tenant created: {tenant.name} ({tenant.id})")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """获取租户"""
        return self._tenants.get(tenant_id)

    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """通过域名获取租户"""
        for tenant in self._tenants.values():
            if tenant.domain == domain:
                return tenant
        return None

    def update_tenant_plan(self, tenant_id: str, new_plan: SubscriptionPlan) -> bool:
        """更新租户计划"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        tenant.subscription_plan = new_plan
        tenant.quota = PLAN_CONFIGS[new_plan].quota
        tenant.updated_at = datetime.now()
        tenant.billing_status = BillingStatus.ACTIVE
        print(f"✅ Tenant {tenant.name} updated to plan: {new_plan.value}")
        return True

    def record_usage(self, tenant_id: str, metric_type: str, value: float, metadata: Dict[str, Any] = None) -> bool:
        """记录用量"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        if tenant_id not in self._usage:
            self._usage[tenant_id] = []
        metric = UsageMetric(
            tenant_id=tenant_id,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        self._usage[tenant_id].append(metric)
        return True

    def get_usage_summary(self, tenant_id: str, month: int = None, year: int = None) -> Dict[str, float]:
        """获取用量摘要"""
        now = datetime.now()
        target_month = month or now.month
        target_year = year or now.year
        
        usage = self._usage.get(tenant_id, [])
        summary = {"executions": 0, "storage": 0, "api_calls": 0}
        
        for metric in usage:
            if metric.timestamp.year == target_year and metric.timestamp.month == target_month:
                if metric.metric_type in summary:
                    summary[metric.metric_type] += metric.value
        return summary

    def create_invoice(self, tenant_id: str, items: List[Dict[str, Any]] = None) -> Optional[Invoice]:
        """创建发票"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        plan_config = PLAN_CONFIGS[tenant.subscription_plan]
        
        invoice_items = items or []
        if not invoice_items:
            invoice_items.append({
                "description": f"{tenant.subscription_plan.value} plan (monthly)",
                "amount": plan_config.price_monthly
            })
        
        total = sum(item["amount"] for item in invoice_items)
        
        invoice = Invoice(
            tenant_id=tenant_id,
            amount=total,
            items=invoice_items,
            due_date=datetime.now() + timedelta(days=14)
        )
        self._invoices[invoice.id] = invoice
        print(f"📄 Invoice created for {tenant.name}: ${total:.2f}")
        return invoice

    def process_payment(self, invoice_id: str, payment_method: str = "stripe") -> Optional[Payment]:
        """处理支付"""
        invoice = self._invoices.get(invoice_id)
        if not invoice:
            return None
        
        payment = Payment(
            tenant_id=invoice.tenant_id,
            invoice_id=invoice_id,
            amount=invoice.amount,
            payment_method=payment_method,
            transaction_id=str(uuid.uuid4()),
            status="succeeded"
        )
        self._payments[payment.id] = payment
        
        invoice.status = "paid"
        invoice.paid_at = datetime.now()
        
        print(f"💳 Payment processed for invoice {invoice_id}: ${payment.amount:.2f}")
        return payment

    def list_tenants(self) -> List[Tenant]:
        """列出所有租户"""
        return list(self._tenants.values())


class RateLimiter:
    """速率限制器"""

    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self._request_counts: Dict[str, List[datetime]] = {}

    def check_rate_limit(self, tenant_id: str) -> bool:
        """检查是否超过速率限制"""
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        if tenant_id not in self._request_counts:
            self._request_counts[tenant_id] = []
        
        # 清理旧记录
        self._request_counts[tenant_id] = [
            t for t in self._request_counts[tenant_id] if t > minute_ago
        ]
        
        count = len(self._request_counts[tenant_id])
        limit = tenant.quota.api_rate_limit_per_minute
        
        if count >= limit:
            return False
        
        self._request_counts[tenant_id].append(now)
        return True


class MultiTenantOrchestrator:
    """多租户编排器"""

    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self.rate_limiter = RateLimiter(tenant_manager)
        self._tenant_orchestrators: Dict[str, Any] = {}

    def execute_workflow_for_tenant(
        self,
        tenant_id: str,
        workflow: Any,
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """为租户执行工作流"""
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant or not tenant.is_active():
            return {"error": "Tenant not found or inactive"}
        
        if not self.rate_limiter.check_rate_limit(tenant_id):
            return {"error": "Rate limit exceeded"}
        
        usage = self.tenant_manager.get_usage_summary(tenant_id)
        if usage["executions"] >= tenant.quota.max_executions_per_month:
            return {"error": "Execution quota exceeded"}
        
        self.tenant_manager.record_usage(tenant_id, "executions", 1.0)
        
        return {
            "status": "success",
            "tenant": tenant.name,
            "workflow": workflow.name if hasattr(workflow, 'name') else "unknown",
            "timestamp": datetime.now().isoformat()
        }
