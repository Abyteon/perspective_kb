#!/bin/bash

# 视角知识库系统 - Docker启动脚本
# 用于快速启动整个系统

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

# 检查Docker是否运行
check_docker() {
    print_message $BLUE "🔍 检查Docker状态..."
    if ! docker info > /dev/null 2>&1; then
        print_message $RED "❌ Docker未运行，请先启动Docker Desktop"
        exit 1
    fi
    print_message $GREEN "✅ Docker运行正常"
}

# 创建必要的目录
create_directories() {
    print_message $BLUE "📁 创建必要的目录..."
    mkdir -p volumes/ollama
    mkdir -p volumes/app_data
    mkdir -p log
    print_message $GREEN "✅ 目录创建完成"
}

# 设置环境变量
setup_environment() {
    print_message $BLUE "⚙️  设置环境变量..."
    if [ ! -f .env ]; then
        cp env.example .env
        print_message $YELLOW "📋 已复制环境配置文件，请根据需要修改 .env"
    fi
    print_message $GREEN "✅ 环境配置完成"
}

# 构建并启动服务
start_services() {
    print_message $BLUE "🚀 启动Docker服务..."
    
    # 选择配置文件
    local compose_file="docker-compose.simple.yml"
    if [ "$1" = "dev" ]; then
        compose_file="docker-compose.dev.yml"
    elif [ "$1" = "prod" ]; then
        compose_file="docker-compose.windows.yml"
    fi
    
    print_message $YELLOW "使用配置文件: $compose_file"
    
    # 停止现有服务
    docker-compose -f $compose_file down 2>/dev/null || true
    
    # 构建并启动
    docker-compose -f $compose_file up --build -d
    
    print_message $GREEN "✅ 服务启动完成"
}

# 检查服务状态
check_services() {
    print_message $BLUE "🔍 检查服务状态..."
    sleep 5
    
    local compose_file="docker-compose.simple.yml"
    if [ "$1" = "dev" ]; then
        compose_file="docker-compose.dev.yml"
    elif [ "$1" = "prod" ]; then
        compose_file="docker-compose.windows.yml"
    fi
    
    echo ""
    print_message $YELLOW "服务状态:"
    docker-compose -f $compose_file ps
    
    echo ""
    print_message $YELLOW "服务访问地址:"
    echo "• 应用服务: http://localhost:8000"
    echo "• Ollama API: http://localhost:11434"
    echo ""
    
    print_message $BLUE "📋 查看日志命令:"
    echo "docker-compose -f $compose_file logs -f"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  simple    启动简化版本（默认，使用Milvus Lite）"
    echo "  dev       启动开发版本"
    echo "  prod      启动生产版本"
    echo "  stop      停止所有服务"
    echo "  clean     清理所有服务和数据"
    echo "  logs      查看服务日志"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 simple   # 启动简化版本"
    echo "  $0 dev      # 启动开发版本"
    echo "  $0 stop     # 停止服务"
    echo "  $0 logs     # 查看日志"
}

# 停止服务
stop_services() {
    print_message $BLUE "⏹️  停止Docker服务..."
    docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose -f docker-compose.windows.yml down 2>/dev/null || true
    print_message $GREEN "✅ 服务已停止"
}

# 清理服务和数据
clean_services() {
    print_message $YELLOW "⚠️  警告：此操作将删除所有数据！"
    read -p "确认继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message $BLUE "🧹 清理Docker服务和数据..."
        docker-compose -f docker-compose.simple.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.windows.yml down -v 2>/dev/null || true
        docker system prune -f
        rm -rf volumes/
        print_message $GREEN "✅ 清理完成"
    else
        print_message $YELLOW "操作已取消"
    fi
}

# 查看日志
show_logs() {
    local compose_file="docker-compose.simple.yml"
    if [ -f docker-compose.dev.yml ] && docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        compose_file="docker-compose.dev.yml"
    fi
    
    print_message $BLUE "📋 显示服务日志..."
    docker-compose -f $compose_file logs -f
}

# 主函数
main() {
    print_message $GREEN "🐳 视角知识库系统 - Docker管理脚本"
    echo ""
    
    case "${1:-simple}" in
        "simple"|"dev"|"prod")
            check_docker
            create_directories
            setup_environment
            start_services $1
            check_services $1
            ;;
        "stop")
            stop_services
            ;;
        "clean")
            clean_services
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_message $RED "❌ 未知选项: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
