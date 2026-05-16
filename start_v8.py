"""
MAOS v8.0 - 快速启动脚本
启动所有创新功能
"""

import os
import sys
import subprocess
import webbrowser
import time


def print_banner():
    """打印启动横幅"""
    print("")
    print("╔═══════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                             ║")
    print("║        🚀  MAOS v8.0 - AI驱动的多Agent编排新纪元                             ║")
    print("║                                                                             ║")
    print("╚═══════════════════════════════════════════════════════════════════════════╝")
    print("")


def main():
    print_banner()
    
    print("📋 选择启动模式:")
    print("   1. 仅运行演示")
    print("   2. 生成并打开监控看板")
    print("   3. 两者都执行")
    print("")
    
    choice = input("请输入选项 (1-3，默认为3): ").strip() or "3"
    
    if choice in ["2", "3"]:
        # 生成UI
        print("\n🎨 生成增强的监控看板...")
        try:
            import generate_v8_ui
            generate_v8_ui.generate_enhanced_dashboard()
            print("   ✅ 看板已生成")
        except Exception as e:
            print(f"   ⚠️  看板生成: {e}")
    
    if choice in ["1", "3"]:
        # 运行演示
        print("\n🚀 运行创新功能演示...")
        demo_process = subprocess.Popen([
            sys.executable, "-u", "demo_v8.py"
        ],
        env={
            "PYTHONPATH": "/workspace",
            **os.environ
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1)
        
        for line in iter(demo_process.stdout.readline, ""):
            print(line, end="")
        demo_process.wait()
        
        if demo_process.returncode != 0:
            print(f"\n   ⚠️  演示进程异常退出: {demo_process.returncode}")
    
    if choice in ["2", "3"]:
        # 尝试打开HTML (本地环境)
        print("\n📖 正在打开监控看板...")
        print("   可在浏览器中打开: maos_v8_dashboard.html")
    
    print("\n" + "="*80)
    print("  🎉 MAOS v8.0 启动完成！")
    print("="*80)
    print("\n📚 新增创新功能:")
    print("   1. 🤖 AI驱动的智能调度器 (maos/ai_scheduler.py)")
    print("   2. 🤝 Multi-Agent协作协议 (maos/collaboration.py)")
    print("   3. 🔌 插件系统 (maos/plugins.py)")
    print("   4. 🎨 增强的实时监控 (maos_v8_dashboard.html)")
    print("   5. 📊 完整路线图 (ROADMAP_V8.md)")
    print("\n🚀 下一阶段展望:")
    print("   - 云原生部署优化")
    print("   - 更多AI驱动功能")
    print("   - 插件市场和生态")
    print("   - 企业级安全")
    print("\n📖 完整报告: MAOS_v8_REPORT.md")
    print("")


if __name__ == "__main__":
    main()
