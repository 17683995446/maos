"""
MAOS v9.0 - 企业级安全完整演示
展示OAuth2.0、JWT、RBAC和审计日志
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime, timedelta

# 导入安全模块
from maos.security.enhanced import OAuth2Server, JWTClaims, JWTAlgorithm, OAuthScope
from maos.security.rbac import RBACManager, Permission, RoleType
from maos.security.audit import AuditLogger, AuditEventType, Severity


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def demo_oauth2():
    """演示OAuth2.0"""
    print_section("1. OAuth2.0 认证系统")
    
    # 创建OAuth服务器
    oauth_server = OAuth2Server("super-secret-key-for-demo")
    
    # 注册客户端
    client_id, client_secret = oauth_server.register_client(
        client_name="MAOS Dashboard",
        redirect_uris=["http://localhost:3000/callback"],
        allowed_scopes=["read", "write", "task:manage"]
    )
    
    print(f"\n✅ 注册OAuth客户端:")
    print(f"   Client ID: {client_id}")
    print(f"   Client Secret: {client_secret[:20]}...")
    
    # 模拟用户授权
    print(f"\n📝 模拟用户授权流程...")
    auth_code = oauth_server.authorize(
        client_id=client_id,
        user_id="user_123",
        redirect_uri="http://localhost:3000/callback",
        scopes=["read", "write"]
    )
    print(f"   授权码: {auth_code[:20]}...")
    
    # 交换令牌
    print(f"\n🔄 交换授权码获取令牌...")
    token_response = oauth_server.exchange_code_for_token(
        code=auth_code,
        client_id=client_id,
        client_secret=client_secret
    )
    
    print(f"   Access Token: {token_response['access_token'][:30]}...")
    print(f"   Token Type: {token_response['token_type']}")
    print(f"   Expires In: {token_response['expires_in']}s")
    print(f"   Refresh Token: {token_response['refresh_token'][:20]}...")
    
    # 验证令牌
    print(f"\n🔐 验证JWT令牌...")
    jwt_token = oauth_server.jwt_token
    claims = jwt_token.verify_token(token_response['access_token'])
    
    if claims:
        print(f"   ✅ 令牌有效")
        print(f"   Subject: {claims.sub}")
        print(f"   Roles: {claims.roles}")
        print(f"   Permissions: {claims.permissions}")
    
    # 客户端凭证授权
    print(f"\n🔑 客户端凭证授权...")
    client_token = oauth_server.client_credentials_grant(
        client_id=client_id,
        client_secret=client_secret,
        scopes=["read", "write"]
    )
    print(f"   Access Token: {client_token['access_token'][:30]}...")


def demo_rbac():
    """演示RBAC"""
    print_section("2. RBAC 权限控制")
    
    # 创建RBAC管理器
    rbac = RBACManager()
    
    # 列出系统角色
    print(f"\n📋 系统角色:")
    roles = rbac.list_roles()
    for role in roles:
        print(f"   {role['name']}: {role['description']}")
        print(f"      权限数量: {len(role['permissions'])}")
    
    # 创建自定义角色
    print(f"\n➕ 创建自定义角色...")
    custom_role = rbac.create_role(
        name="data_analyst",
        description="数据分析师",
        permissions=[
            "task:read",
            "task:create",
            "workflow:read",
            "workflow:execute",
            "metrics:read"
        ]
    )
    print(f"   角色创建成功: {custom_role.name}")
    
    # 创建用户并分配角色
    print(f"\n👤 创建用户...")
    user = rbac.create_user(
        user_id="user_001",
        username="alice",
        email="alice@example.com",
        roles=["developer", "data_analyst"]
    )
    print(f"   用户: {user.username} ({user.email})")
    print(f"   角色: {list(user.roles)}")
    
    # 检查权限
    print(f"\n🔍 权限检查:")
    permissions_to_check = [
        "task:create",
        "task:delete",
        "agent:create",
        "system:config"
    ]
    
    for perm in permissions_to_check:
        has_perm = rbac.has_permission(user.user_id, perm)
        status = "✅" if has_perm else "❌"
        print(f"   {status} {perm}: {has_perm}")
    
    # 获取用户所有权限
    print(f"\n📊 用户所有权限:")
    all_permissions = rbac.get_user_permissions(user.user_id)
    for perm in sorted(all_permissions)[:10]:
        print(f"   - {perm}")
    print(f"   ... 共 {len(all_permissions)} 项")


def demo_audit():
    """演示审计日志"""
    print_section("3. 审计日志系统")
    
    # 创建审计日志器
    audit_logger = AuditLogger(retention_days=30)
    
    # 记录各种事件
    print(f"\n📝 记录审计事件...")
    
    # 模拟登录
    audit_logger.log_event(
        event_type=AuditEventType.LOGIN,
        severity=Severity.INFO,
        user_id="user_001",
        action="用户登录",
        details={"method": "password", "mfa": True}
    )
    print("   ✅ 用户登录事件")
    
    # 模拟任务创建
    audit_logger.log_event(
        event_type=AuditEventType.TASK_CREATE,
        severity=Severity.INFO,
        user_id="user_001",
        action="创建任务",
        resource_type="task",
        resource_id="task_123",
        details={"name": "数据分析任务", "priority": "high"}
    )
    print("   ✅ 任务创建事件")
    
    # 模拟安全告警
    audit_logger.log_event(
        event_type=AuditEventType.SECURITY_ALERT,
        severity=Severity.WARNING,
        user_id="user_002",
        action="异常登录",
        details={"ip": "192.168.1.100", "reason": "异地登录"},
        actor_ip="192.168.1.100"
    )
    print("   ✅ 安全告警事件")
    
    # 模拟权限拒绝
    audit_logger.log_event(
        event_type=AuditEventType.PERMISSION_DENIED,
        severity=Severity.WARNING,
        user_id="user_003",
        action="尝试删除Agent",
        resource_type="agent",
        resource_id="agent_999",
        outcome="failure",
        details={"reason": "权限不足"}
    )
    print("   ✅ 权限拒绝事件")
    
    # 查询事件
    print(f"\n🔍 查询审计事件...")
    events = audit_logger.query_events(limit=10)
    print(f"   查询到 {len(events)} 条事件")
    
    # 获取安全告警
    print(f"\n🚨 获取安全告警:")
    alerts = audit_logger.get_security_alerts()
    for alert in alerts:
        print(f"   - [{alert['severity']}] {alert['message']}")
    
    # 生成合规报告
    print(f"\n📊 生成合规报告...")
    report = audit_logger.generate_compliance_report(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    print(f"   报告ID: {report['report_id'][:20]}...")
    print(f"   总事件数: {report['summary']['total_events']}")
    print(f"   唯一用户数: {report['summary']['unique_users']}")
    print(f"   登录成功率: {report['summary']['login_success_rate']:.1f}%")
    
    if report['recommendations']:
        print(f"   建议:")
        for rec in report['recommendations']:
            print(f"      - {rec}")


def demo_integration():
    """演示集成"""
    print_section("4. 安全系统集成")
    
    # 创建完整的安全系统
    oauth_server = OAuth2Server("integration-secret-key")
    rbac = RBACManager()
    audit_logger = AuditLogger()
    
    # 1. 注册客户端
    client_id, client_secret = oauth_server.register_client(
        client_name="Enterprise App",
        redirect_uris=["https://app.example.com/callback"],
        allowed_scopes=["admin", "read", "write"]
    )
    
    # 2. 创建用户并分配角色
    admin_user = rbac.create_user(
        user_id="admin_001",
        username="admin",
        email="admin@maos.io",
        roles=["admin"]
    )
    
    # 3. 审计日志
    audit_logger.log_event(
        event_type=AuditEventType.USER_CREATE,
        severity=Severity.INFO,
        user_id="system",
        action="创建管理员用户",
        resource_type="user",
        resource_id=admin_user.user_id
    )
    
    print(f"\n✅ 安全系统集成完成:")
    print(f"   - OAuth2.0 客户端: {client_id[:20]}...")
    print(f"   - RBAC 用户: {admin_user.username} ({', '.join(admin_user.roles)})")
    print(f"   - 审计日志: {len(audit_logger.events)} 条")


def main():
    """主函数"""
    print("")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║     🔐 MAOS v9.0 - 企业级安全系统演示                                      ║")
    print("║                                                                            ║")
    print("║     OAuth2.0 | JWT | RBAC | 审计日志                                       ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    
    demo_oauth2()
    demo_rbac()
    demo_audit()
    demo_integration()
    
    print("\n" + "="*80)
    print("  🎉 企业级安全系统演示完成！")
    print("="*80)
    print("\n📚 MAOS v9.0 安全特性:")
    print("   ✅ OAuth2.0 认证")
    print("   ✅ JWT 令牌管理")
    print("   ✅ RBAC 权限控制")
    print("   ✅ 完整审计日志")
    print("   ✅ 安全告警")
    print("   ✅ 合规报告生成")
    print("\n📖 查看完整代码:")
    print("   - maos/security/enhanced.py (OAuth2.0 & JWT)")
    print("   - maos/security/rbac.py (RBAC)")
    print("   - maos/security/audit.py (审计日志)")
    print("\n🚀 MAOS v9.0 - 企业级安全增强！")


if __name__ == "__main__":
    main()
