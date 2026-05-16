#!/bin/bash
# MAOS v10.0 CLI安装脚本

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║     🚀 MAOS v10.0 CLI Installer                                            ║"
echo("║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not found"
    exit 1
fi

echo "✅ pip3 found"

# 创建安装目录
INSTALL_DIR="${HOME}/.maos"
mkdir -p "$INSTALL_DIR"

echo ""
echo "📦 Installing MAOS CLI..."
echo "   Install directory: $INSTALL_DIR"

# 创建CLI包装脚本
cat > "${INSTALL_DIR}/maos" << 'SCRIPT'
#!/bin/bash
# MAOS CLI Wrapper

export PYTHONPATH="$(dirname "$0")/../../:$PYTHONPATH"
export MAOS_CLI_HOME="$(dirname "$0")"

python3 -c "
import sys
sys.path.insert(0, '$(pwd)')
from maos.cli import main
main()
" "$@"
SCRIPT

chmod +x "${INSTALL_DIR}/maos"

# 创建符号链接到PATH
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"

if [ -L "${BIN_DIR}/maos" ]; then
    rm "${BIN_DIR}/maos"
fi

ln -s "${INSTALL_DIR}/maos" "${BIN_DIR}/maos"

echo ""
echo "✅ MAOS CLI installed successfully!"
echo ""
echo "📝 Usage:"
echo "   maos info              Show system information"
echo "   maos status            Show system status"
echo "   maos tasks list        List tasks"
echo "   maos agents list       List agents"
echo "   maos workflows list     List workflows"
echo "   maos clusters list      List clusters"
echo "   maos metrics           Show metrics"
echo "   maos deploy k8s        Deploy to Kubernetes"
echo ""
echo "📚 Documentation: https://docs.maos.io/cli"
echo ""
