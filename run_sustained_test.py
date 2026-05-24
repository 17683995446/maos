#!/usr/bin/env python3
"""
运行 MAOS v14.0 超长持续测试
"""

import sys
import os

# 添加正确的路径
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/maos/tests')

# 导入并运行测试
from maos.tests.test_sustained_longevity_practice import (
    SustainedLongevityPractice,
    run_additional_quick_tests
)

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("  MAOS v14.0 - 快速检查 - 30秒测试")
    print("=" * 80)
    
    # 运行30秒的简短版本测试
    practice = SustainedLongevityPractice(
        test_duration=30.0,  # 30秒快速检查
        num_workers=10,
        ops_per_sec_per_worker=8
    )
    
    longevity_result = practice.run()
    
    # 运行额外的快速测试
    quick_results = run_additional_quick_tests()
    
    # 综合报告
    print("\n" + "=" * 80)
    print("              快速检查完成 - 综合报告")
    print("=" * 80)
    
    print(f"\n1. 长寿测试 (30秒):")
    print(f"   总操作: {longevity_result.operations:,}")
    print(f"   错误: {longevity_result.errors}")
    print(f"   成功率: {(1 - longevity_result.errors / max(1, longevity_result.operations)) * 100:.1f}%")
    
    if longevity_result.issues_found:
        print(f"   ⚠️ 问题:")
        for issue in longevity_result.issues_found:
            print(f"   - {issue}")
    
    print(f"\n2. 高频并发测试:")
    hf = quick_results['high_frequency']
    print(f"   总操作: {hf['operations']:,}")
    print(f"   错误: {hf['errors']}")
    print(f"   吞吐量: {hf['throughput']:.1f} ops/sec")
    print(f"   成功: {'✅' if hf['success'] else '❌'}")
    
    print(f"\n3. 创建/销毁测试:")
    cd = quick_results['create_destroy']
    print(f"   总操作: {cd['operations']}")
    print(f"   错误: {cd['errors']}")
    print(f"   吞吐量: {cd['throughput']:.1f} ops/sec")
    print(f"   成功: {'✅' if cd['success'] else '❌'}")
    
    # 检查是否有任何错误
    all_success = (
        len(longevity_result.issues_found) == 0 and
        longevity_result.errors == 0 and
        hf['success'] and
        cd['success']
    )
    
    print(f"\n{'✅ 快速检查通过！' if all_success else '⚠️ 发现问题，需要修复'}")
    print("=" * 80)
    
    return {
        "longevity": longevity_result,
        "quick_tests": quick_results,
        "all_success": all_success
    }


if __name__ == "__main__":
    main()

