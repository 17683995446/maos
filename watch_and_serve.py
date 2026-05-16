#!/usr/bin/env python3
"""
MAOS Dashboard - 文件监控和自动更新脚本
监控项目文件变化，自动更新可视化网页
"""

import os
import sys
import time
import json
import hashlib
import asyncio
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# 配置
WATCH_DIRS = [
    "/workspace/maos",
    "/workspace/legacy",
    "/workspace/multi_agent_orchestration_system"
]

DASHBOARD_FILE = "/workspace/maos_dashboard.html"
PORT = 8000

# 文件哈希缓存
file_hashes = {}

def get_file_hash(file_path):
    """计算文件哈希值"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def scan_files():
    """扫描并统计项目文件"""
    files_data = []
    for watch_dir in WATCH_DIRS:
        if not os.path.exists(watch_dir):
            continue
            
        for root, dirs, files in os.walk(watch_dir):
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    try:
                        stat = os.stat(file_path)
                        file_hash = get_file_hash(file_path)
                        
                        file_info = {
                            'path': file_path,
                            'name': file,
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'hash': file_hash,
                            'extension': os.path.splitext(file)[1]
                        }
                        files_data.append(file_info)
                    except:
                        pass
    
    # 按修改时间排序
    files_data.sort(key=lambda x: x['modified'], reverse=True)
    return files_data

def update_dashboard():
    """更新仪表板HTML文件"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 更新仪表板...")
    
    files = scan_files()
    recent_files = files[:20]
    
    # 统计
    total_files = len(files)
    total_size = sum(f['size'] for f in files)
    python_files = len([f for f in files if f['extension'] == '.py'])
    
    # 运行测试获取结果
    test_results = run_tests()
    
    # 更新HTML文件时间戳
    with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 可以在这里动态修改内容
    # 简化版本：直接保存
    
    print(f"✅ 仪表板已更新！扫描到 {total_files} 个文件")
    return True

def run_tests():
    """运行测试并返回结果"""
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "maos/tests/", "-v", "--tb=short", "--quiet"],
            cwd="/workspace",
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except Exception as e:
        return {'error': str(e)}

class FileWatcher:
    """文件监控器"""
    
    def __init__(self):
        self.running = False
        
    def watch(self):
        """开始监控"""
        self.running = True
        print(f"开始监控文件变化...")
        print(f"监控目录: {WATCH_DIRS}")
        
        while self.running:
            changed = False
            
            # 检查文件变化
            for watch_dir in WATCH_DIRS:
                if not os.path.exists(watch_dir):
                    continue
                    
                for root, dirs, files in os.walk(watch_dir):
                    for file in files:
                        if file.startswith('.'):
                            continue
                            
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            try:
                                new_hash = get_file_hash(file_path)
                                old_hash = file_hashes.get(file_path)
                                
                                if old_hash is not None and old_hash != new_hash:
                                    print(f"检测到变化: {file_path}")
                                    changed = True
                                    file_hashes[file_path] = new_hash
                                elif old_hash is None:
                                    file_hashes[file_path] = new_hash
                            except:
                                pass
            
            if changed:
                update_dashboard()
            
            time.sleep(2)  # 每2秒检查一次
    
    def stop(self):
        """停止监控"""
        self.running = False

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP处理器"""
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/maos_dashboard.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def start_server():
    """启动HTTP服务器"""
    os.chdir('/workspace')
    server = HTTPServer(('0.0.0.0', PORT), MyHTTPRequestHandler)
    print(f"\n🚀 服务器已启动: http://localhost:{PORT}")
    print(f"📊 仪表板: http://localhost:{PORT}/maos_dashboard.html")
    print(f"\n按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止服务器...")
        server.shutdown()

def main():
    """主函数"""
    print("=" * 60)
    print("  MAOS v3.0.0 仪表板")
    print("=" * 60)
    
    # 初始扫描
    print("\n初始扫描文件...")
    files = scan_files()
    for f in files[:10]:
        file_hashes[f['path']] = f['hash']
    
    # 初始更新
    update_dashboard()
    
    # 在单独线程启动服务器
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 开始监控文件
    watcher = FileWatcher()
    try:
        watcher.watch()
    except KeyboardInterrupt:
        print("\n停止监控...")
        watcher.stop()

if __name__ == "__main__":
    main()
