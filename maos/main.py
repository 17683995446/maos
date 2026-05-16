#!/usr/bin/env python3
"""
MAOS - Multi-Agent Orchestration System
MAOS多智能体编排系统主入口

MAOS是一个生产级的企业级多智能体编排系统，提供以下核心功能：
- 分布式通信：基于Redis的发布/订阅实现Agent间消息传递
- 企业级任务队列：支持重试、超时、优先级管理的任务队列
- REST API：基于FastAPI的自动OpenAPI文档接口
- 生产监控：Prometheus指标收集和结构化日志
- 多租户支持：完整的租户隔离和管理机制
- 高级分析：实时指标和异常检测
- 流式响应：完整的异步流式响应支持
- Agent回调：全面的事件系统用于监控

Architecture:
  - Clean Architecture with clear separation of concerns
  - Domain-Driven Design patterns
  - Event-driven orchestration
  - RESTful API layer with FastAPI
  - Multiple storage backends (Redis, PostgreSQL, DynamoDB)

Version: 3.0.0
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maos import __version__
from maos.examples import basic_demo, complete_demo


class MAOSCLI:
    """
    MAOS命令行接口

    提供命令行界面以运行各种MAOS功能和演示。
    """

    def __init__(self):
        self.banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ███╗   ███╗██╗███╗   ██╗██╗███╗   ██╗ ██████╗             ║
║     ████╗ ████║██║████╗  ██║██║████╗  ██║██╔════╝             ║
║     ██╔████╔██║██║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗            ║
║     ██║╚██╔╝██║██║██║╚██╗██║██║██║╚██╗██║██║   ██║            ║
║     ██║ ╚═╝ ██║██║██║ ╚████║██║██║ ╚████║╚██████╔╝            ║
║     ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝             ║
║                                                                  ║
║         Multi-Agent Orchestration System                         ║
║         多智能体编排系统 v{version:<37}║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """.format(version=__version__)

    def print_banner(self):
        """打印系统横幅"""
        print(self.banner)

    def print_menu(self):
        """打印主菜单"""
        print("""
请选择操作：

  基础演示:
    [1] 运行基础演示 (Basic Demo)
        - Agent创建和注册
        - 任务创建和执行
        - 工作流执行
        - 系统状态查看

    [2] 运行完整演示 (Complete Demo)
        - 高级Agent管理
        - 复杂工作流编排
        - 多租户支持
        - 实时分析和监控
        - 错误处理和恢复
        - 事件驱动架构

  工具命令:
    [3] 系统信息 (System Info)
        - 查看MAOS版本和配置
        - 显示系统架构

    [4] 快速开始指南 (Quick Start)
        - 简短的使用示例
        - 常见使用场景

  其他:
    [h] 帮助信息
    [q] 退出
""")

    def print_system_info(self):
        """打印系统信息"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                       MAOS 系统信息                               ║
╠══════════════════════════════════════════════════════════════════╣
║  版本信息:                                                        ║
║    - MAOS版本: {version:<50}║
║    - Python版本: {python_version:<46}║
║                                                                  ║
║  核心模块:                                                        ║
║    - core: Agent基类、消息类型、事件系统                          ║
║    - orchestration: 编排器、任务管理器、工作流                    ║
║    - agents: 数据处理、分析、报告生成Agent                        ║
║    - storage: 存储后端（内存、Redis等）                           ║
║    - utils: 日志、指标、辅助工具                                  ║
║                                                                  ║
║  主要特性:                                                        ║
║    ✓ 异步消息处理                                                ║
║    ✓ 事件驱动架构                                                ║
║    ✓ 多租户隔离                                                  ║
║    ✓ 任务队列管理                                                ║
║    ✓ 工作流编排                                                  ║
║    ✓ 流式响应                                                    ║
║    ✓ 错误恢复机制                                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """.format(
            version=__version__,
            python_version=sys.version.split()[0]
        ))

    def print_quick_start(self):
        """打印快速开始指南"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                       MAOS 快速开始指南                           ║
╠══════════════════════════════════════════════════════════════════╣

  1. 基本使用示例:

     from maos.core import AgentOptions
     from maos.agents.examples import DataProcessingAgent
     from maos.orchestration.orchestrator import OrchestratorService

     # 创建编排器
     orchestrator = OrchestratorService(name="my_orchestrator")

     # 创建Agent
     agent = DataProcessingAgent(AgentOptions(
         name="my_agent",
         capabilities=["data_cleaning"]
     ))

     # 注册Agent
     orchestrator.register_agent(agent)

     # 创建并执行任务
     task = orchestrator.create_task(
         name="my_task",
         requirements=["data_cleaning"],
         input_data={"data": [1, 2, 3]}
     )

  2. 常见使用场景:

     场景1: 数据处理管道
       - 创建数据处理Agent
       - 定义清洗-验证-转换工作流
       - 自动Agent选择和任务分配

     场景2: 分析报告生成
       - 数据收集 → 分析 → 报告生成
       - 多Agent协作
       - 结果聚合和可视化

     场景3: 多租户数据处理
       - 隔离的租户环境
       - 资源配额管理
       - 独立的任务队列

  3. 下一步:

     - 运行 'python main.py --demo basic' 查看基础演示
     - 运行 'python main.py --demo complete' 查看完整演示
     - 查看 examples/ 目录下的示例代码
     - 阅读 docs/ 目录下的详细文档

╚══════════════════════════════════════════════════════════════════╝
        """)

    def print_help(self):
        """打印帮助信息"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                       MAOS 帮助信息                               ║
╠══════════════════════════════════════════════════════════════════╣

  命令行参数:
    --demo, -d        运行指定演示 (basic|complete)
    --info, -i        显示系统信息
    --quickstart, -q  显示快速开始指南
    --help, -h        显示此帮助信息
    --version, -v     显示版本信息

  使用示例:

    # 运行基础演示
    python main.py --demo basic

    # 运行完整演示
    python main.py --demo complete

    # 显示系统信息
    python main.py --info

    # 显示快速开始指南
    python main.py --quickstart

    # 交互式菜单（无参数）
    python main.py

  文档:
    - 完整文档: docs/
    - API参考: docs/api/
    - 架构说明: docs/architecture.md
    - 示例代码: examples/

╚══════════════════════════════════════════════════════════════════╝
        """)

    def run_interactive(self):
        """运行交互式菜单"""
        self.print_banner()
        self.print_menu()

        while True:
            try:
                choice = input("\n请输入选项: ").strip().lower()

                if choice == '1':
                    print("\n" + "="*70)
                    print("  正在启动基础演示...")
                    print("="*70)
                    basic_demo.run_demo()
                    break
                elif choice == '2':
                    print("\n" + "="*70)
                    print("  正在启动完整演示...")
                    print("="*70)
                    complete_demo.run_complete_demo()
                    break
                elif choice == '3':
                    self.print_system_info()
                elif choice == '4':
                    self.print_quick_start()
                elif choice in ['h', 'help']:
                    self.print_help()
                elif choice in ['q', 'quit', 'exit']:
                    print("\n感谢使用MAOS，再见！\n")
                    break
                else:
                    print("\n无效选项，请重新选择。输入 'h' 查看帮助。")

            except KeyboardInterrupt:
                print("\n\n操作已取消。")
                break
            except EOFError:
                print("\n\n输入已结束。")
                break

    def run_demo(self, demo_type: str):
        """运行指定类型的演示"""
        if demo_type == 'basic':
            print("\n" + "="*70)
            print("  启动基础演示")
            print("="*70 + "\n")
            basic_demo.run_demo()
        elif demo_type == 'complete':
            print("\n" + "="*70)
            print("  启动完整演示")
            print("="*70 + "\n")
            complete_demo.run_complete_demo()
        else:
            print(f"\n错误: 未知的演示类型 '{demo_type}'")
            print("支持的类型: basic, complete")
            sys.exit(1)


def main():
    """
    MAOS主入口函数

    支持命令行参数和交互式菜单两种模式。
    """
    parser = argparse.ArgumentParser(
        description='MAOS - Multi-Agent Orchestration System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                  # 启动交互式菜单
  python main.py --demo basic      # 运行基础演示
  python main.py --demo complete   # 运行完整演示
  python main.py --info            # 显示系统信息
  python main.py --quickstart      # 显示快速开始指南
  python main.py --version         # 显示版本信息
        """
    )

    parser.add_argument(
        '--demo', '-d',
        choices=['basic', 'complete'],
        help='运行指定演示 (basic: 基础演示, complete: 完整演示)'
    )

    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='显示MAOS系统信息'
    )

    parser.add_argument(
        '--quickstart', '-q',
        action='store_true',
        help='显示快速开始指南'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'MAOS {__version__}'
    )

    args = parser.parse_args()

    cli = MAOSCLI()

    if args.demo:
        cli.run_demo(args.demo)
    elif args.info:
        cli.print_banner()
        cli.print_system_info()
    elif args.quickstart:
        cli.print_banner()
        cli.print_quick_start()
    else:
        cli.run_interactive()


def quick_demo():
    """
    快速演示函数

    提供最简单的演示方式，无需命令行参数。
    """
    cli = MAOSCLI()
    cli.print_banner()
    print("\n正在启动快速演示...\n")
    basic_demo.run_demo()


def advanced_demo():
    """
    高级演示函数

    提供完整功能的演示。
    """
    cli = MAOSCLI()
    cli.print_banner()
    print("\n正在启动高级演示...\n")
    complete_demo.run_complete_demo()


if __name__ == "__main__":
    main()
