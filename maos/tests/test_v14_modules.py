"""
MAOS v14.0 完整测试套件
包含所有v14模块的单元测试、集成测试和系统测试
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# v14 模块测试
from maos.sdk.v14 import (
    MAOSSDK, SDKConfig, SDKLanguage, SDKGenerator, SDKFactory,
    APIResponse, APIResponseStatus, WorkflowCreateRequest, WorkflowExecutionRequest, ExecutionResult
)

from maos.version.v14 import (
    VersionManager, ABTestManager, WorkflowVersion, ABTest, ABTestVariant,
    VersionStatus, ABTestStatus, TrafficAllocationType
)

from maos.analytics.v14 import (
    AnalyticsEngine, VisualizationGenerator, Dashboard, DashboardWidget,
    ChartType, TimeRange, MetricSummary, AnalyticsReport
)

from maos.mobile.v14 import (
    MobileAPIManager, MobileOptimizedAPI, MobileDevice, MobileSession,
    PushNotification, MobilePlatform, PushNotificationType
)

from maos.analytics.v14 import ChartConfig

# Import all analytics classes


# ============================================================
# SDK 模块测试
# ============================================================

class TestSDK:
    """SDK模块测试"""
    
    def test_sdk_creation(self):
        """测试SDK创建"""
        sdk = MAOSSDK(api_key="test-key")
        assert sdk is not None
        assert sdk.config.api_key == "test-key"
    
    def test_sdk_config(self):
        """测试SDK配置"""
        config = SDKConfig(
            api_key="test-key",
            base_url="https://api.test.com",
            timeout=60,
            retries=5
        )
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.test.com"
        assert config.timeout == 60
        assert config.retries == 5
    
    def test_sdk_language_enum(self):
        """测试SDK语言枚举"""
        assert SDKLanguage.PYTHON.value == "python"
        assert SDKLanguage.JAVASCRIPT.value == "javascript"
        assert SDKLanguage.GO.value == "go"
        assert SDKLanguage.JAVA.value == "java"
        assert SDKLanguage.RUST.value == "rust"
    
    def test_api_response(self):
        """测试API响应"""
        response = APIResponse(
            status=APIResponseStatus.SUCCESS,
            data={"key": "value"},
            message="Success"
        )
        assert response.is_success() is True
        assert response.data == {"key": "value"}
    
    def test_workflow_create_request(self):
        """测试工作流创建请求"""
        request = WorkflowCreateRequest(
            name="Test Workflow",
            description="Test Description",
            version="1.0",
            steps=[{"name": "step1"}, {"name": "step2"}]
        )
        assert request.name == "Test Workflow"
        assert len(request.steps) == 2
    
    def test_workflow_execution_request(self):
        """测试工作流执行请求"""
        request = WorkflowExecutionRequest(
            workflow_id="wf-123",
            input_data={"key": "value"},
            sync=True
        )
        assert request.workflow_id == "wf-123"
        assert request.sync is True
    
    def test_execution_result(self):
        """测试执行结果"""
        result = ExecutionResult(
            execution_id="exec-123",
            status="completed",
            output_data={"result": "success"}
        )
        assert result.execution_id == "exec-123"
        assert result.status == "completed"


class TestSDKGenerator:
    """SDK代码生成器测试"""
    
    def test_python_sdk_generation(self):
        """测试Python SDK生成"""
        generator = SDKGenerator(SDKLanguage.PYTHON)
        code = generator.generate_client()
        assert "class MAOSClient:" in code
        assert "def __init__" in code
    
    def test_javascript_sdk_generation(self):
        """测试JavaScript SDK生成"""
        generator = SDKGenerator(SDKLanguage.JAVASCRIPT)
        code = generator.generate_client()
        assert "class MAOSClient" in code
        assert "constructor" in code
    
    def test_go_sdk_generation(self):
        """测试Go SDK生成"""
        generator = SDKGenerator(SDKLanguage.GO)
        code = generator.generate_client()
        assert "type MAOSClient struct" in code
        assert "func NewMAOSClient" in code
    
    def test_java_sdk_generation(self):
        """测试Java SDK生成"""
        generator = SDKGenerator(SDKLanguage.JAVA)
        code = generator.generate_client()
        assert "public class MAOSClient" in code
        assert "MAOSSDK" in code
    
    def test_rust_sdk_generation(self):
        """测试Rust SDK生成"""
        generator = SDKGenerator(SDKLanguage.RUST)
        code = generator.generate_client()
        assert "pub struct MAOSClient" in code
        assert "impl MAOSClient" in code
    
    def test_sdk_factory(self):
        """测试SDK工厂"""
        sdk = SDKFactory.create(SDKLanguage.PYTHON, "test-key")
        assert isinstance(sdk, MAOSSDK)


# ============================================================
# 版本控制与A/B测试模块测试
# ============================================================

class TestVersionControl:
    """版本控制测试"""
    
    def test_version_manager_creation(self):
        """测试版本管理器创建"""
        manager = VersionManager()
        assert manager is not None
        assert len(manager._versions) == 0
    
    def test_create_version(self):
        """测试创建版本"""
        manager = VersionManager()
        version = manager.create_version(
            workflow_id="wf-123",
            version="1.0",
            name="Initial Version",
            definition={"steps": {"step1": {}, "step2": {}}}
        )
        assert version.version == "1.0"
        assert version.name == "Initial Version"
        assert version.workflow_id == "wf-123"
    
    def test_get_version(self):
        """测试获取版本"""
        manager = VersionManager()
        created = manager.create_version("wf-123", {"steps": {}}, "1.0")
        retrieved = manager.get_version(created.id)
        assert retrieved == created
    
    def test_get_latest_version(self):
        """测试获取最新版本"""
        manager = VersionManager()
        manager.create_version("wf-123", {"steps": {}}, "1.0")
        manager.create_version("wf-123", {"steps": {}}, "2.0")
        latest = manager.get_latest_version("wf-123")
        assert latest.version == "2.0"
    
    def test_activate_version(self):
        """测试激活版本"""
        manager = VersionManager()
        v1 = manager.create_version("wf-123", {"steps": {}}, "1.0")
        v2 = manager.create_version("wf-123", {"steps": {}}, "2.0")
        
        result = manager.activate_version(v2.id)
        assert result is True
        assert manager.get_version(v2.id).status == VersionStatus.ACTIVE
    
    def test_compare_versions(self):
        """测试版本比较"""
        manager = VersionManager()
        v1 = manager.create_version("wf-123", {"steps": {"step1": {}, "step2": {}}}, "1.0")
        v2 = manager.create_version("wf-123", {"steps": {"step1": {}, "step3": {}}}, "2.0")
        
        diff = manager.compare_versions(v1.id, v2.id)
        assert "step3" in diff.added_steps
        assert "step2" in diff.removed_steps
    
    def test_rollback_version(self):
        """测试版本回滚"""
        manager = VersionManager()
        v1 = manager.create_version("wf-123", {"steps": {}}, "1.0")
        manager.create_version("wf-123", {"steps": {}}, "2.0")
        
        result = manager.rollback_to_version("wf-123", v1.id)
        assert result is True


class TestABTesting:
    """A/B测试测试"""
    
    def test_ab_test_manager_creation(self):
        """测试A/B测试管理器创建"""
        version_manager = VersionManager()
        manager = ABTestManager(version_manager)
        assert manager is not None
    
    def test_create_ab_test(self):
        """测试创建A/B测试"""
        version_manager = VersionManager()
        manager = ABTestManager(version_manager)
        
        v1 = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        v2 = version_manager.create_version("wf-123", {"steps": {}}, "2.0")
        
        test = manager.create_test(
            name="Performance Test",
            workflow_id="wf-123",
            variants=[
                {"name": "Control", "version_id": v1.id, "weight": 50},
                {"name": "Variant", "version_id": v2.id, "weight": 50}
            ]
        )
        assert test.name == "Performance Test"
        assert len(test.variants) == 2
    
    def test_start_test(self):
        """测试启动测试"""
        version_manager = VersionManager()
        manager = ABTestManager(version_manager)
        
        v1 = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        test = manager.create_test("Test", "wf-123", [{"name": "A", "version_id": v1.id, "weight": 100}])
        
        result = manager.start_test(test.id)
        assert result is True
        assert manager.get_test(test.id).status == ABTestStatus.RUNNING
    
    def test_select_variant(self):
        """测试选择变体"""
        version_manager = VersionManager()
        manager = ABTestManager(version_manager)
        
        v1 = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        v2 = version_manager.create_version("wf-123", {"steps": {}}, "2.0")
        
        test = manager.create_test("Test", "wf-123", [
            {"name": "Control", "version_id": v1.id, "weight": 50},
            {"name": "Variant", "version_id": v2.id, "weight": 50}
        ])
        manager.start_test(test.id)
        
        variant = manager.select_variant(test.id, "user-123")
        assert variant is not None
        assert variant.name in ["Control", "Variant"]
    
    def test_record_result(self):
        """测试记录结果"""
        version_manager = VersionManager()
        manager = ABTestManager(version_manager)
        
        v1 = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        test = manager.create_test("Test", "wf-123", [{"name": "Control", "version_id": v1.id, "weight": 100}])
        manager.start_test(test.id)
        variant = test.variants[0]
        
        manager.record_result(test.id, variant.id, success=True, execution_time_ms=150.0)
        results = manager.get_test_results(test.id)
        assert len(results) == 1
        assert results[0].user_count == 1
    
    def test_get_best_variant(self):
        """测试获取最佳变体"""
        version_manager = VersionManager()
        manager = ABTestManager(version_manager)
        
        v1 = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        v2 = version_manager.create_version("wf-123", {"steps": {}}, "2.0")
        
        test = manager.create_test("Test", "wf-123", [
            {"name": "Control", "version_id": v1.id, "weight": 50},
            {"name": "Variant", "version_id": v2.id, "weight": 50}
        ])
        manager.start_test(test.id)
        
        for i, variant in enumerate(test.variants):
            manager.record_result(test.id, variant.id, success=True, execution_time_ms=150.0 + i * 10)
        
        best = manager.get_best_variant(test.id)
        assert best is not None


# ============================================================
# 分析模块测试
# ============================================================

class TestAnalytics:
    """分析引擎测试"""
    
    def test_analytics_engine_creation(self):
        """测试分析引擎创建"""
        engine = AnalyticsEngine()
        assert engine is not None
        assert len(engine._metrics_store) == 0
    
    def test_record_metric(self):
        """测试记录指标"""
        engine = AnalyticsEngine()
        engine.record_metric("test.metric", 100.0)
        engine.record_metric("test.metric", 200.0)
        assert len(engine._metrics_store["test.metric"]) == 2
    
    def test_get_metric_data(self):
        """测试获取指标数据"""
        engine = AnalyticsEngine()
        now = datetime.now()
        engine.record_metric("test", 100.0, now - timedelta(hours=1))
        engine.record_metric("test", 200.0, now)
        
        data = engine.get_metric_data("test", TimeRange.LAST_HOUR)
        assert len(data) >= 1
    
    def test_calculate_summary(self):
        """测试计算摘要"""
        engine = AnalyticsEngine()
        for i in range(10):
            engine.record_metric("executions", 100.0 + i * 10)
        
        summary = engine.calculate_summary("executions")
        assert summary.name == "executions"
        assert summary.value > 0
    
    def test_create_dashboard(self):
        """测试创建仪表盘"""
        engine = AnalyticsEngine()
        dashboard = engine.create_dashboard("Test Dashboard", "Test Description")
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test Description"
    
    def test_add_widget(self):
        """测试添加组件"""
        engine = AnalyticsEngine()
        engine.record_metric("test.metric", 100.0)
        
        dashboard = engine.create_dashboard("Test")
        widget = engine.add_widget(dashboard.id, "Test Widget", ChartType.LINE, "test.metric")
        
        assert widget is not None
        assert widget.name == "Test Widget"
        assert len(dashboard.widgets) == 1
    
    def test_generate_report(self):
        """测试生成报告"""
        engine = AnalyticsEngine()
        for i in range(20):
            engine.record_metric("executions", 100.0 + i * 5)
            engine.record_metric("errors", 5.0 + (i % 3))
            engine.record_metric("latency_ms", 150.0 + i * 2)
        
        report = engine.generate_report("Daily Report")
        assert report.title == "Daily Report"
        assert len(report.metrics) >= 3


class TestVisualization:
    """可视化测试"""
    
    def test_dashboard_widget(self):
        """测试仪表盘组件"""
        widget = DashboardWidget(
            name="Test Widget",
            chart_type=ChartType.LINE,
            config=ChartConfig(title="Test Chart")
        )
        assert widget.name == "Test Widget"
        assert widget.chart_type == ChartType.LINE
    
    def test_chart_config(self):
        """测试图表配置"""
        config = ChartConfig(
            title="Test Chart",
            type=ChartType.BAR,
            colors=["#ff0000", "#00ff00", "#0000ff"]
        )
        assert config.title == "Test Chart"
        assert len(config.colors) == 3
    
    def test_metric_summary(self):
        """测试指标摘要"""
        summary = MetricSummary(
            name="test_metric",
            value=100.0,
            unit="count",
            change=10.0,
            change_percent=10.0,
            trend="up"
        )
        assert summary.name == "test_metric"
        assert summary.trend == "up"


# ============================================================
# 移动端API模块测试
# ============================================================

class TestMobileAPI:
    """移动端API测试"""
    
    def test_mobile_api_manager_creation(self):
        """测试移动端API管理器创建"""
        manager = MobileAPIManager()
        assert manager is not None
        assert len(manager._devices) == 0
    
    def test_register_device(self):
        """测试注册设备"""
        manager = MobileAPIManager()
        device = manager.register_device(
            user_id="user-123",
            device_token="token-abc",
            platform=MobilePlatform.IOS,
            app_version="1.0.0",
            os_version="17.0"
        )
        assert device.user_id == "user-123"
        assert device.platform == MobilePlatform.IOS
    
    def test_get_user_devices(self):
        """测试获取用户设备"""
        manager = MobileAPIManager()
        manager.register_device("user-123", "token-1", MobilePlatform.IOS, "1.0", "17.0")
        manager.register_device("user-123", "token-2", MobilePlatform.ANDROID, "1.0", "14.0")
        
        devices = manager.get_user_devices("user-123")
        assert len(devices) == 2
    
    def test_create_session(self):
        """测试创建会话"""
        manager = MobileAPIManager()
        device = manager.register_device("user-123", "token", MobilePlatform.IOS, "1.0", "17.0")
        session = manager.create_session("user-123", device.id)
        
        assert session.user_id == "user-123"
        assert session.token is not None
    
    def test_validate_session(self):
        """测试验证会话"""
        manager = MobileAPIManager()
        device = manager.register_device("user-123", "token", MobilePlatform.IOS, "1.0", "17.0")
        session = manager.create_session("user-123", device.id)
        
        validated = manager.validate_session(session.token)
        assert validated is not None
        assert validated.user_id == "user-123"
    
    def test_send_notification(self):
        """测试发送通知"""
        manager = MobileAPIManager()
        notification = PushNotification(
            type=PushNotificationType.WORKFLOW_COMPLETED,
            title="Test",
            body="Test body",
            target_user_id="user-123"
        )
        
        result = manager.send_notification(notification)
        assert result is True
        assert notification.delivered is True
    
    def test_get_workflow_summary(self):
        """测试获取工作流摘要"""
        manager = MobileAPIManager()
        summaries = manager.get_workflow_summary("user-123")
        assert len(summaries) >= 1
        assert summaries[0].name is not None
    
    def test_execute_workflow_mobile(self):
        """测试移动端执行工作流"""
        manager = MobileAPIManager()
        device = manager.register_device("user-123", "token", MobilePlatform.IOS, "1.0", "17.0")
        session = manager.create_session("user-123", device.id)
        
        result = manager.execute_workflow_mobile(session.token, "wf-123", {"data": "test"})
        assert result.status in ["completed", "error"]
    
    def test_mobile_optimized_api(self):
        """测试移动端优化API"""
        manager = MobileAPIManager()
        api = MobileOptimizedAPI(manager)
        
        auth_result = api.authenticate("user-123", "token", "ios")
        assert "token" in auth_result
        
        dashboard = api.get_dashboard(auth_result["token"])
        assert "workflows" in dashboard


# ============================================================
# 集成测试
# ============================================================

class TestIntegration:
    """集成测试"""
    
    def test_sdk_with_version_control(self):
        """测试SDK与版本控制集成"""
        sdk = SDKFactory.create(SDKLanguage.PYTHON, "test-key")
        version_manager = VersionManager()
        
        version = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        assert version.workflow_id == "wf-123"
    
    def test_analytics_with_mobile(self):
        """测试分析与移动端集成"""
        analytics = AnalyticsEngine()
        mobile_manager = MobileAPIManager()
        
        analytics.record_metric("mobile.executions", 100.0)
        
        device = mobile_manager.register_device("user-123", "token", MobilePlatform.IOS, "1.0", "17.0")
        session = mobile_manager.create_session("user-123", device.id)
        
        metrics = analytics.get_metric_data("mobile.executions")
        assert len(metrics) >= 1
    
    def test_full_workflow_version_abtest(self):
        """测试完整工作流版本和A/B测试"""
        version_manager = VersionManager()
        ab_test_manager = ABTestManager(version_manager)
        
        v1 = version_manager.create_version("wf-123", {"steps": {"validate": {}, "process": {}}}, "1.0")
        v2 = version_manager.create_version("wf-123", {"steps": {"validate": {}, "process": {}, "notify": {}}}, "2.0")
        
        test = ab_test_manager.create_test("Full Test", "wf-123", [
            {"name": "Control", "version_id": v1.id, "weight": 50},
            {"name": "Variant", "version_id": v2.id, "weight": 50}
        ])
        
        ab_test_manager.start_test(test.id)
        
        for i in range(10):
            variant = ab_test_manager.select_variant(test.id, f"user-{i}")
            ab_test_manager.record_result(test.id, variant.id, success=True, execution_time_ms=150.0 + i)
        
        best = ab_test_manager.get_best_variant(test.id)
        assert best is not None
        
        ab_test_manager.complete_test(test.id)
        assert test.status == ABTestStatus.COMPLETED


# ============================================================
# 系统测试
# ============================================================

class TestSystem:
    """系统测试"""
    
    def test_complete_system_initialization(self):
        """测试完整系统初始化"""
        # SDK
        sdk = SDKFactory.create(SDKLanguage.PYTHON, "test-key")
        
        # 版本控制
        version_manager = VersionManager()
        version = version_manager.create_version("wf-123", {"steps": {}}, "1.0")
        
        # A/B测试
        ab_test_manager = ABTestManager(version_manager)
        
        # 分析
        analytics = AnalyticsEngine()
        analytics.record_metric("system.initialization", 1.0)
        
        # 移动端
        mobile_manager = MobileAPIManager()
        device = mobile_manager.register_device("user-123", "token", MobilePlatform.IOS, "1.0", "17.0")
        
        # 验证
        assert sdk is not None
        assert version is not None
        assert analytics is not None
        assert device is not None
    
    def test_error_handling(self):
        """测试错误处理"""
        version_manager = VersionManager()
        
        # 获取不存在的版本
        version = version_manager.get_version("non-existent")
        assert version is None
        
        # 比较不存在的版本
        diff = version_manager.compare_versions("non-existent-1", "non-existent-2")
        assert diff.version_from == "unknown"
    
    def test_performance(self):
        """测试性能"""
        start = time.time()
        
        analytics = AnalyticsEngine()
        for i in range(1000):
            analytics.record_metric(f"perf.test.{i % 10}", float(i))
        
        elapsed = time.time() - start
        assert elapsed < 5.0  # 应该在5秒内完成


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
