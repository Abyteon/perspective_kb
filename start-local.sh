#!/bin/bash

# 视角知识库系统 - 本地开发快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $GREEN "🚀 视角知识库系统 - 本地开发模式"
echo ""

# 检查pixi是否安装
if ! command -v pixi &> /dev/null; then
    print_message $RED "❌ pixi 未安装，请先安装 pixi"
    echo "安装命令: curl -fsSL https://pixi.sh/install.sh | bash"
    exit 1
fi

print_message $BLUE "✅ pixi 环境检查通过"

# 检查Ollama是否运行
if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    print_message $YELLOW "🔄 启动 Ollama 服务..."
    ollama serve &
    sleep 5
    
    # 检查模型是否存在
    if ! ollama list | grep -q "mitoza/Qwen3-Embedding"; then
        print_message $YELLOW "📥 拉取嵌入模型..."
        ollama pull mitoza/Qwen3-Embedding-0.6B:latest
    fi
else
    print_message $BLUE "✅ Ollama 服务已运行"
fi

# 显示可用命令
echo ""
print_message $YELLOW "📋 可用命令："
echo "  pixi run python -m perspective_kb.cli status        # 检查系统状态"
echo "  pixi run python -m perspective_kb.cli process       # 处理数据"
echo "  pixi run python -m perspective_kb.cli search \"查询\" # 搜索功能"
echo ""

# 执行系统状态检查
print_message $BLUE "🔍 检查系统状态..."
pixi run python -m perspective_kb.cli status

echo ""
print_message $GREEN "🎉 本地开发环境就绪！"
print_message $YELLOW "💡 提示：修改代码后无需重启，直接运行相应命令即可测试"
