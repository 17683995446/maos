#!/bin/bash
# MAOS v7.0 - 一键启动脚本

set -e

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║         MAOS v7.0 - One-Click Startup Script                         ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# 安装依赖
echo ""
echo "📦 Installing dependencies..."
pip3 install -q fastapi uvicorn pydantic openai python-dotenv psutil

# 设置环境
export PYTHONPATH="$(pwd)"
export MAOS_SYSTEM_NAME="MAOS-v7.0"
export MAOS_API_PORT=8000

# 选项菜单
echo ""
echo "🌟 Choose what to start:"
echo "   1) API Server (REST + WebSocket)"
echo "   2) Dashboard (HTTP Server)"
echo "   3) Both (API + Dashboard)"
echo "   4) Docker Compose (Full Stack)"
echo "   5) Kubernetes (Production)"
echo ""

read -p "Enter choice (1-5, default=1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "🌐 Starting MAOS API Server v7.0..."
        echo "   📚 Docs: http://localhost:8000/docs"
        echo "   🔌 WebSocket: ws://localhost:8000/ws"
        echo ""
        python3 -m maos.api_v2
        ;;
    2)
        echo ""
        echo "🎨 Starting Dashboard..."
        echo "   🌐 URL: http://localhost:8080"
        echo ""
        python3 -m http.server 8080
        ;;
    3)
        echo ""
        echo "🚀 Starting Both..."
        echo "   API: http://localhost:8000/docs"
        echo "   Dashboard: http://localhost:8080"
        echo ""
        # 启动API
        python3 -m maos.api_v2 &
        API_PID=$!
        sleep 2
        # 启动Dashboard
        python3 -m http.server 8080 &
        DASH_PID=$!
        echo ""
        echo "✅ Services started!"
        echo "   Press Ctrl+C to stop"
        trap "kill $API_PID $DASH_PID 2>/dev/null; exit" INT TERM
        wait
        ;;
    4)
        echo ""
        echo "🐳 Starting with Docker Compose..."
        docker-compose up -d
        ;;
    5)
        echo ""
        echo "☸️  Kubernetes deployment requires:"
        echo "   kubectl configured"
        echo "   Run: kubectl apply -f kubernetes/"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
