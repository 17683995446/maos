#!/usr/bin/env python3
"""
调试边界日期时间问题
"""
import sys
sys.path.insert(0, '/workspace')

from datetime import datetime, timedelta
import traceback
from maos.storage.in_memory import InMemoryChatStorage

print("测试边界日期时间...")

storage = InMemoryChatStorage()
edge_dates = [
    datetime.min,
    datetime.max,
    datetime(1970, 1, 1),
    datetime(9999, 12, 31),
    datetime.now() - timedelta(days=365*100),
    datetime.now() + timedelta(days=365*100),
]

for i, dt in enumerate(edge_dates):
    print(f"\n测试日期 {i}: {dt}")
    try:
        ts = dt.timestamp()
        print(f"  时间戳: {ts}")
        storage.save_message(f"date_test_{i}", {"timestamp": ts})
        print(f"  ✓ 保存成功")
    except Exception as e:
        print(f"  ✗ 保存失败: {type(e).__name__}: {e}")
        traceback.print_exc()

print("\n调试完成")
