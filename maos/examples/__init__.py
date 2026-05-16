"""
MAOS Examples Module
MAOS系统示例模块

本模块包含MAOS系统的示例程序和演示代码，帮助用户快速上手和理解系统功能。

示例模块：
    - basic_demo：基础功能演示，展示Agent创建、任务执行等核心功能
    - complete_demo：完整功能演示，展示高级功能、工作流编排等

使用示例：
    from maos.examples import basic_demo, complete_demo

    # 运行基础演示
    basic_demo.run_demo()

    # 运行完整演示
    complete_demo.run_complete_demo()
"""

from maos.examples import basic_demo
from maos.examples import complete_demo

__all__ = [
    'basic_demo',
    'complete_demo',
]
