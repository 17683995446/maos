#!/usr/bin/env python3
"""
MAOS 全面测试套件
"""

import sys
import time

sys.path.insert(0, '/workspace')

print("="*100)
print("MAOS 全面测试套件")
print("="*100)
print()

# 1. 高压力专项测试
print("="*100)
print("测试 1: 高压力专项测试")
print("="*100)
import subprocess
result = subprocess.run(
    ["python", "maos/tests/test_high_pressure.py"],
    cwd="/workspace",
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print("stderr:", result.stderr)

print()
print("="*100)
print("测试 2: 终极混乱测试")
print("="*100)
result = subprocess.run(
    ["python", "maos/tests/test_ultimate_chaos_v6.py"],
    cwd="/workspace",
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print("stderr:", result.stderr)

print()
print("="*100)
print("测试 3: 集成测试")
print("="*100)
result = subprocess.run(
    ["python", "maos/tests/test_integration_chaos.py"],
    cwd="/workspace",
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print("stderr:", result.stderr)

print()
print("="*100)
print("✅ 全面测试完成！")
print("="*100)
