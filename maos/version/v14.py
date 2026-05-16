"""
MAOS v14.0 - Workflow Version Control & A/B Testing
工作流版本控制与 A/B 测试
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class VersionStatus(Enum):
    """版本状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ABTestStatus(Enum):
    """A/B测试状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TrafficAllocationType(Enum):
    """流量分配类型"""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    USER_SEGMENT = "user_segment"


@dataclass
class WorkflowVersion:
    """工作流版本"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    version: str = "1.0"
    name: str = ""
    description: str = ""
    definition: Dict[str, Any] = field(default_factory=dict)
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    parent_version: Optional[str] = None
    changelog: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionDiff:
    """版本差异"""
    version_from: str
    version_to: str
    added_steps: List[str] = field(default_factory=list)
    removed_steps: List[str] = field(default_factory=list)
    modified_steps: List[str] = field(default_factory=list)
    changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ABTestVariant:
    """A/B测试变体"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    workflow_version_id: str = ""
    weight: float = 0.0
    traffic_allocation: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTest:
    """A/B测试"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    workflow_id: str = ""
    variants: List[ABTestVariant] = field(default_factory=list)
    status: ABTestStatus = ABTestStatus.DRAFT
    traffic_allocation_type: TrafficAllocationType = TrafficAllocationType.PERCENTAGE
    metrics: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_id: str = ""
    variant_id: str = ""
    variant_name: str = ""
    user_count: int = 0
    conversion_count: int = 0
    conversion_rate: float = 0.0
    avg_execution_time_ms: float = 0.0
    error_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)


class VersionManager:
    """版本管理器"""
    
    def __init__(self):
        self._versions: Dict[str, WorkflowVersion] = {}
        self._workflow_versions: Dict[str, List[str]] = {}  # workflow_id -> [version_ids]
    
    def create_version(self, workflow_id: str, definition: Dict[str, Any], version: str = None, 
                      name: str = "", description: str = "", changelog: str = "", 
                      parent_version_id: str = None, created_by: str = "") -> WorkflowVersion:
        """创建版本"""
        if version is None:
            existing_versions = self.get_workflow_versions(workflow_id)
            version = f"{len(existing_versions) + 1}.0"
        
        workflow_version = WorkflowVersion(
            workflow_id=workflow_id,
            version=version,
            name=name or f"Version {version}",
            description=description,
            definition=definition,
            changelog=changelog,
            parent_version=parent_version_id,
            created_by=created_by
        )
        
        self._versions[workflow_version.id] = workflow_version
        
        if workflow_id not in self._workflow_versions:
            self._workflow_versions[workflow_id] = []
        self._workflow_versions[workflow_id].append(workflow_version.id)
        
        print(f"📝 Version created: {workflow_id} v{version}")
        return workflow_version
    
    def get_version(self, version_id: str) -> Optional[WorkflowVersion]:
        """获取版本"""
        return self._versions.get(version_id)
    
    def get_workflow_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        """获取工作流的所有版本"""
        version_ids = self._workflow_versions.get(workflow_id, [])
        return [self._versions.get(vid) for vid in version_ids if self._versions.get(vid)]
    
    def get_latest_version(self, workflow_id: str) -> Optional[WorkflowVersion]:
        """获取最新版本"""
        versions = self.get_workflow_versions(workflow_id)
        if not versions:
            return None
        return sorted(versions, key=lambda v: v.created_at, reverse=True)[0]
    
    def activate_version(self, version_id: str) -> bool:
        """激活版本"""
        version = self._versions.get(version_id)
        if not version:
            return False
        
        version.status = VersionStatus.ACTIVE
        
        # 将同工作流的其他版本设为deprecated
        for vid in self._workflow_versions.get(version.workflow_id, []):
            if vid != version_id:
                other_version = self._versions.get(vid)
                if other_version and other_version.status == VersionStatus.ACTIVE:
                    other_version.status = VersionStatus.DEPRECATED
        
        print(f"✅ Version activated: {version.workflow_id} v{version.version}")
        return True
    
    def compare_versions(self, version_id_from: str, version_id_to: str) -> VersionDiff:
        """比较两个版本"""
        v1 = self._versions.get(version_id_from)
        v2 = self._versions.get(version_id_to)
        
        if not v1 or not v2:
            return VersionDiff(version_from=v1.version if v1 else "unknown", 
                            version_to=v2.version if v2 else "unknown")
        
        steps1 = set(v1.definition.get("steps", {}).keys()) if isinstance(v1.definition, dict) else set()
        steps2 = set(v2.definition.get("steps", {}).keys()) if isinstance(v2.definition, dict) else set()
        
        diff = VersionDiff(
            version_from=v1.version,
            version_to=v2.version,
            added_steps=list(steps2 - steps1),
            removed_steps=list(steps1 - steps2),
            modified_steps=[]
        )
        
        return diff
    
    def rollback_to_version(self, workflow_id: str, version_id: str) -> bool:
        """回滚到指定版本"""
        version = self._versions.get(version_id)
        if not version or version.workflow_id != workflow_id:
            return False
        
        new_version = self.create_version(
            workflow_id=workflow_id,
            definition=version.definition,
            changelog=f"Rollback to version {version.version}",
            parent_version_id=version_id
        )
        
        self.activate_version(new_version.id)
        print(f"🔄 Rolled back to version: {workflow_id} v{new_version.version}")
        return True


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
        self._tests: Dict[str, ABTest] = {}
        self._results: Dict[str, List[ABTestResult]] = {}
    
    def create_test(self, name: str, workflow_id: str, variants: List[Dict[str, Any]], 
                   description: str = "", metrics: List[str] = None) -> ABTest:
        """创建A/B测试"""
        ab_test = ABTest(
            name=name,
            workflow_id=workflow_id,
            description=description,
            metrics=metrics or ["conversion_rate", "execution_time", "error_rate"]
        )
        
        total_weight = sum(v.get("weight", 0) for v in variants)
        
        for variant in variants:
            ab_test.variants.append(ABTestVariant(
                name=variant["name"],
                workflow_version_id=variant["version_id"],
                weight=variant.get("weight", 0) / total_weight if total_weight > 0 else 0,
                traffic_allocation=int(variant.get("weight", 0))
            ))
        
        self._tests[ab_test.id] = ab_test
        self._results[ab_test.id] = []
        
        print(f"🧪 A/B Test created: {name}")
        return ab_test
    
    def start_test(self, test_id: str) -> bool:
        """启动测试"""
        test = self._tests.get(test_id)
        if not test:
            return False
        
        test.status = ABTestStatus.RUNNING
        test.started_at = datetime.now()
        print(f"🚀 A/B Test started: {test.name}")
        return True
    
    def pause_test(self, test_id: str) -> bool:
        """暂停测试"""
        test = self._tests.get(test_id)
        if not test or test.status != ABTestStatus.RUNNING:
            return False
        
        test.status = ABTestStatus.PAUSED
        print(f"⏸️ A/B Test paused: {test.name}")
        return True
    
    def complete_test(self, test_id: str) -> bool:
        """完成测试"""
        test = self._tests.get(test_id)
        if not test or test.status != ABTestStatus.RUNNING:
            return False
        
        test.status = ABTestStatus.COMPLETED
        test.completed_at = datetime.now()
        print(f"✅ A/B Test completed: {test.name}")
        return True
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """获取测试"""
        return self._tests.get(test_id)
    
    def select_variant(self, test_id: str, user_id: str = None) -> Optional[ABTestVariant]:
        """选择变体（基于用户ID哈希或随机）"""
        test = self._tests.get(test_id)
        if not test or test.status != ABTestStatus.RUNNING:
            return None
        
        if user_id:
            # 基于用户ID的确定性哈希选择
            hash_value = hash(user_id) % 100
            cumulative = 0
            for variant in test.variants:
                cumulative += variant.weight * 100
                if hash_value < cumulative:
                    return variant
        else:
            # 随机选择
            import random
            r = random.random()
            cumulative = 0
            for variant in test.variants:
                cumulative += variant.weight
                if r < cumulative:
                    return variant
        
        return test.variants[0] if test.variants else None
    
    def record_result(self, test_id: str, variant_id: str, success: bool = True, 
                     execution_time_ms: float = 0.0, metrics: Dict[str, Any] = None) -> None:
        """记录测试结果"""
        test = self._tests.get(test_id)
        if not test:
            return
        
        variant = next((v for v in test.variants if v.id == variant_id), None)
        if not variant:
            # Try to find by name if id doesn't match
            return
        
        if test_id not in self._results:
            self._results[test_id] = []
        
        existing_result = next((r for r in self._results[test_id] if r.variant_id == variant_id), None)
        
        if existing_result:
            existing_result.user_count += 1
            if success:
                existing_result.conversion_count += 1
            else:
                existing_result.error_count += 1
            existing_result.avg_execution_time_ms = (
                (existing_result.avg_execution_time_ms * (existing_result.user_count - 1) + execution_time_ms) 
                / existing_result.user_count
            )
            if existing_result.user_count > 0:
                existing_result.conversion_rate = existing_result.conversion_count / existing_result.user_count
        else:
            self._results[test_id].append(ABTestResult(
                test_id=test_id,
                variant_id=variant_id,
                variant_name=variant.name,
                user_count=1,
                conversion_count=1 if success else 0,
                conversion_rate=1.0 if success else 0.0,
                avg_execution_time_ms=execution_time_ms,
                error_count=0 if success else 1,
                metrics=metrics or {}
            ))
    
    def get_test_results(self, test_id: str) -> List[ABTestResult]:
        """获取测试结果"""
        return self._results.get(test_id, [])
    
    def get_best_variant(self, test_id: str) -> Optional[ABTestResult]:
        """获取最佳变体"""
        results = self.get_test_results(test_id)
        if not results:
            return None
        
        return max(results, key=lambda r: r.conversion_rate)
