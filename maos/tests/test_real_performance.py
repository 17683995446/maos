"""
MAOS v14.0 - Real Performance Monitor
真实性能监控器
"""

import time
import gc
import psutil
import sys
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    objects_count: int = 0


class RealPerformanceMonitor:
    """真实性能监控器"""
    
    def __init__(self):
        self._snapshots: List[PerformanceSnapshot] = []
        self._start_time = time.time()
        self._start_snapshot = self._take_snapshot()
    
    def _take_snapshot(self) -> PerformanceSnapshot:
        """获取性能快照"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()
            objects_count = len(gc.get_objects())
            
            return PerformanceSnapshot(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                objects_count=objects_count
            )
        except (ImportError, Exception):
            return PerformanceSnapshot()
    
    def capture(self, label: str = "") -> None:
        """捕获性能快照"""
        snapshot = self._take_snapshot()
        self._snapshots.append(snapshot)
    
    def report(self) -> Dict[str, Any]:
        """生成性能报告"""
        if not self._snapshots:
            return {}
        
        last = self._snapshots[-1]
        time_elapsed = time.time() - self._start_time
        
        if len(self._snapshots) > 1:
            memory_delta = last.memory_mb - self._start_snapshot.memory_mb
            objects_delta = last.objects_count - self._start_snapshot.objects_count
        else:
            memory_delta = 0
            objects_delta = 0
        
        return {
            "elapsed_seconds": round(time_elapsed, 2),
            "current_memory_mb": round(last.memory_mb, 2),
            "current_cpu_percent": last.cpu_percent,
            "memory_delta_mb": round(memory_delta, 2),
            "objects_delta": objects_delta,
            "total_objects": last.objects_count,
            "snapshots_taken": len(self._snapshots)
        }


def run_real_performance_test():
    """运行真实性能测试"""
    print("\n" + "="*80)
    print("🚀 MAOS v14.0 - REAL PERFORMANCE TESTING")
    print("="*80)
    
    monitor = RealPerformanceMonitor()
    
    # 测试导入时间
    import_time_start = time.time()
    from maos.version.v14 import VersionManager
    from maos.analytics.v14 import AnalyticsEngine
    from maos.mobile.v14 import MobileAPIManager
    import_time = time.time() - import_time_start
    print(f"\n⏱️  Module import time: {import_time*1000:.2f}ms")
    
    monitor.capture("after_imports")
    
    # 测试版本创建性能
    print("\n📝 Testing version creation...")
    manager = VersionManager()
    start = time.time()
    versions_created = 0
    for i in range(10000):
        manager.create_version(f"wf-test-{i%10}", {"step": i}, f"{i}.0")
        versions_created += 1
    version_time = time.time() - start
    print(f"   Created {versions_created} versions in {version_time:.2f}s")
    print(f"   {versions_created/version_time:.0f} versions/second")
    
    monitor.capture("after_versions")
    
    # 测试指标记录性能
    print("\n📊 Testing metric recording...")
    engine = AnalyticsEngine()
    start = time.time()
    metrics_recorded = 0
    for i in range(10000):
        engine.record_metric(f"metric-{i%100}", float(i))
        metrics_recorded += 1
    metric_time = time.time() - start
    print(f"   Recorded {metrics_recorded} metrics in {metric_time:.2f}s")
    print(f"   {metrics_recorded/metric_time:.0f} metrics/second")
    
    monitor.capture("after_metrics")
    
    # 测试设备注册性能
    print("\n📱 Testing device registration...")
    mobile = MobileAPIManager()
    start = time.time()
    devices_registered = 0
    for i in range(5000):
        mobile.register_device(
            f"user-{i%100}",
            f"token-{i}",
            "ios",
            "1.0.0",
            "17.0"
        )
        devices_registered += 1
    device_time = time.time() - start
    print(f"   Registered {devices_registered} devices in {device_time:.2f}s")
    print(f"   {devices_registered/device_time:.0f} devices/second")
    
    monitor.capture("after_devices")
    
    # 最终报告
    final_report = monitor.report()
    print("\n" + "="*80)
    print("📊 FINAL PERFORMANCE REPORT")
    print("="*80)
    for key, value in final_report.items():
        print(f"   {key:30}: {value}")
    
    return True


if __name__ == "__main__":
    run_real_performance_test()
