#!/bin/bash
# MAOS v5.0 - Quick Start Script
# Get everything up and running in minutes

set -e

echo "🚀 MAOS v5.0 - Quick Start"
echo "=============================="
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo "======================================"
    echo "$1"
    echo "======================================"
}

# Check Python version
print_section "1. Checking Python version..."
python3 --version || { echo "❌ Python 3.8+ required!"; exit 1; }

# Check and install dependencies
print_section "2. Installing dependencies..."
pip3 install --upgrade pip
pip3 install fastapi uvicorn pydantic || {
    echo "⚠️ Could not install dependencies, skipping..."
}

# Verify installation
print_section "3. Verifying installation..."
export PYTHONPATH=$(pwd)
python3 -c "import maos; print(f'✅ MAOS v{maos.__version__} imported successfully!')"

# Check if dashboard exists
print_section "4. Starting services..."
echo ""
echo "📋 Available options:"
echo "   1) Start Dashboard only (HTTP server on port 8000)"
echo "   2) Start API server (FastAPI on port 8000)"
echo "   3) Start both (Dashboard on 8080, API on 8000)"
echo ""

read -p "Choose an option (1-3, default=1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "🎨 Starting Dashboard..."
        echo "   Open http://localhost:8000/maos_dashboard.html"
        export PYTHONPATH=$(pwd)
        python3 -m http.server 8000
        ;;
    2)
        echo ""
        echo "🌐 Starting API Server..."
        echo "   API Docs: http://localhost:8000/docs"
        export PYTHONPATH=$(pwd)
        python3 -c "from maos.api import run_server; run_server(host='0.0.0.0', port=8000)"
        ;;
    3)
        echo ""
        echo "🚀 Starting Both Services..."
        echo "   Dashboard: http://localhost:8080"
        echo "   API Docs:  http://localhost:8000/docs"
        echo ""
        echo "⚠️ Note: This requires two terminals."
        echo "   Please run these commands in separate terminals:"
        echo ""
        echo "   Terminal 1 (API):"
        echo "      export PYTHONPATH=$(pwd)"
        echo "      python3 -c \"from maos.api import run_server; run_server(host='0.0.0.0', port=8000)\""
        echo ""
        echo "   Terminal 2 (Dashboard):"
        echo "      python3 -m http.server 8080"
        echo ""
        ;;
    *)
        echo "❌ Invalid option!"
        exit 1
        ;;
esac
