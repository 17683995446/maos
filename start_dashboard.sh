#!/bin/bash

# MAOS Dashboard 快速启动脚本
echo "=========================================="
echo "  MAOS v3.0.0 Dashboard 启动"
echo "=========================================="
echo ""

# 设置可执行权限
chmod +x /workspace/watch_and_serve.py

# 创建一个简单的启动脚本
echo "启动本地服务器..."
echo ""
echo "📊 仪表板将在 http://localhost:8000 上运行"
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    export PYTHONPATH=/workspace
    cd /workspace && python3 - <<END
import http.server
import socketserver
import os

PORT = 8000

# 切换到workspace目录
os.chdir('/workspace')

# 创建自定义处理器
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/maos_dashboard.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

# 启动服务器
Handler = MyHTTPRequestHandler

print("🚀 MAOS Dashboard 已启动!")
print(f"📊 访问地址: http://localhost:{PORT}")
print("   (或者访问 http://localhost:{PORT}/maos_dashboard.html)")
print("")
print("按 Ctrl+C 停止服务器")
print("=" * 50)
print("")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()

END
else
    echo "错误: 未找到Python3!"
    exit 1
fi
