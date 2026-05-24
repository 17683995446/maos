#!/usr/bin/env python3
"""
运行 MAOS v14.0 完整超长持续测试 - 3分钟
"""

import sys
import os
import logging

# 设置日志级别为 WARNING，减少输出
logging.basicConfig(level=logging.WARNING)

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
    print("  MAOS v14.0 - 完整超长持续测试 - 3分钟")
    print("=" * 80)
    
    # 运行完整测试
    practice = SustainedLongevityPractice(
        test_duration=180.0,  # 3分钟完整测试
        num_workers=20,
        ops_per_sec_per_worker=10
    )
    
    longevity_result = practice.run()
    
    # 运行额外的快速测试
    quick_results = run_additional_quick_tests()
    
    # 综合报告
    print("\n" + "=" * 80)
    print("              完整测试完成 - 综合报告")
    print("=" * 80)
    
    print(f"\n1. 长寿测试 (3分钟):")
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
    
    print(f"\n{'✅ 完整测试完美通过！' if all_success else '⚠️ 发现问题，需要修复'}")
    print("=" * 80)
    
    # 保存详细报告
    with open("/workspace/MAOS_SUSTAINED_FINAL_REPORT.txt", "w", encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("  MAOS v14.0 - 超长持续测试最终报告\n")
        f.write("=" * 80 + "\n")
        
        f.write(f"\n1. 长寿测试 (3分钟):\n")
        f.write(f"   总操作: {longevity_result.operations:,}\n")
        f.write(f"   错误: {longevity_result.errors}\n")
        f.write(f"   成功率: {(1 - longevity_result.errors / max(1, longevity_result.operations)) * 100:.1f}%\n")
        
        if longevity_result.issues_found:
            f.write(f"\n发现的问题:\n")
            for issue in longevity_result.issues_found:
                f.write(f" - {issue}")
        
    return {
        "longevity": longevity_result,
        "quick_tests": quick_results,
        "all_success": all_success
    }


if __name__ == "__main__":
    main()

