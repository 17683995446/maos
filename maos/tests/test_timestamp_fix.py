#!/usr/bin/env python3
"""
验证时间戳修复 - 极端时间戳测试
"""

import sys
import time

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage

def test_extreme_timestamps():
    """测试各种极端时间戳"""
    
    print("="*80)
    print("验证时间戳修复 - 极端时间戳测试")
    print("="*80)
    
    storage = InMemoryChatStorage()
    
    extreme_timestamps = [
        # 正常时间戳
        ("当前时间", time.time()),
        ("过去1天", time.time() - 86400),
        ("未来1天", time.time() + 86400),
        
        # 极端时间戳 - 应该被优雅处理
        ("极小值 -1e30", -1e30),
        ("极大值 1e30", 1e30),
        ("负无穷 float('-inf')", float('-inf')),
        ("正无穷 float('inf')", float('inf')),
        ("极小负数 -1000000000000", -1000000000000),
        ("极大正数 1000000000000", 1000000000000),
        ("零 0", 0),
    ]
    
    errors = 0
    successes = 0
    
    for name, ts in extreme_timestamps:
        try:
            print(f"\n测试: {name}, ts={ts}")
            result = storage.save_message(
                "test_user", 
                {"content": f"测试消息: {name}", "timestamp": ts}
            )
            if result:
                print(f"  ✓ 成功")
                successes +=1 
            else:
                print(f"  ✗ 失败")
                errors +=1
        except Exception as e:
            print(f"  ✗ 异常: {type(e).__name__}: {e}")
            errors +=1
    
    print("\n" + "="*80)
    print(f"测试总结: 成功={successes}, 失败={errors}")
    
    # 验证消息都正确保存了
    conv = storage.get_conversation("test_user")
    print(f"保存的消息数: {len(conv)}")
    
    for i, msg in enumerate(conv):
        print(f"消息 {i}: timestamp={msg.get('timestamp')}")
    
    if errors == 0 and len(conv) == len(extreme_timestamps):
        print("\n✅ 完美！所有时间戳都被正确处理了！")
        return 0
    else:
        print("\n⚠️ 发现问题！")
        return 1

if __name__ == "__main__":
    exit_code = test_extreme_timestamps()
    sys.exit(exit_code)
