# 视角知识库系统 - Windows PowerShell Docker启动脚本
# 用于快速启动整个系统

param(
    [string]$Action = "simple"
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "视角知识库系统 - Docker管理"

# 颜色定义
$Colors = @{
    Red = "Red"
    Green = "Green" 
    Yellow = "Yellow"
    Blue = "Cyan"
    White = "White"
}

# 打印带颜色的消息
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

# 检查Docker是否运行
function Test-Docker {
    Write-ColorMessage "🔍 检查Docker状态..." "Blue"
    try {
        $null = docker info 2>$null
        Write-ColorMessage "✅ Docker运行正常" "Green"
        return $true
    }
    catch {
        Write-ColorMessage "❌ Docker未运行，请先启动Docker Desktop" "Red"
        Write-ColorMessage "   下载地址: https://www.docker.com/products/docker-desktop/" "Yellow"
        return $false
    }
}

# 创建必要的目录
function New-RequiredDirectories {
    Write-ColorMessage "📁 创建必要的目录..." "Blue"
    
    $directories = @(
        "volumes\ollama",
        "volumes\app_data", 
        "log"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-ColorMessage "✅ 目录创建完成" "Green"
}

# 设置环境变量
function Set-Environment {
    Write-ColorMessage "⚙️ 设置环境变量..." "Blue"
    
    if (!(Test-Path ".env")) {
        Copy-Item "env.example" ".env"
        Write-ColorMessage "📋 已复制环境配置文件，请根据需要修改 .env" "Yellow"
    }
    
    Write-ColorMessage "✅ 环境配置完成" "Green"
}

# 选择配置文件
function Get-ComposeFile {
    param([string]$Action)
    
    switch ($Action.ToLower()) {
        "dev" { return "docker-compose.dev.yml" }
        "prod" { return "docker-compose.windows.yml" }
        default { return "docker-compose.simple.yml" }
    }
}

# 启动服务
function Start-Services {
    param([string]$Action)
    
    $composeFile = Get-ComposeFile $Action
    
    Write-ColorMessage "🚀 启动Docker服务..." "Blue"
    Write-ColorMessage "使用配置文件: $composeFile" "Yellow"
    
    # 停止现有服务
    Write-ColorMessage "停止现有服务..." "Blue"
    docker-compose -f $composeFile down 2>$null
    
    # 构建并启动
    Write-ColorMessage "构建并启动服务..." "Blue"
    $result = docker-compose -f $composeFile up --build -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorMessage "❌ 服务启动失败" "Red"
        return $false
    }
    
    Write-ColorMessage "✅ 服务启动完成" "Green"
    return $true
}

# 检查服务状态
function Test-Services {
    param([string]$Action)
    
    $composeFile = Get-ComposeFile $Action
    
    Write-ColorMessage "🔍 检查服务状态..." "Blue"
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-ColorMessage "服务状态:" "Yellow"
    docker-compose -f $composeFile ps
    
    Write-Host ""
    Write-ColorMessage "📍 服务访问地址:" "Yellow"
    Write-Host "  • 应用服务: http://localhost:8000"
    Write-Host "  • Ollama API: http://localhost:11434"
    Write-Host ""
    
    Write-ColorMessage "📋 常用命令:" "Blue"
    Write-Host "  查看日志: docker-compose -f $composeFile logs -f"
    Write-Host "  停止服务: .\scripts\docker-start.ps1 stop"
    Write-Host "  清理数据: .\scripts\docker-start.ps1 clean"
}

# 停止服务
function Stop-Services {
    Write-ColorMessage "⏹️ 停止Docker服务..." "Blue"
    
    $composeFiles = @(
        "docker-compose.simple.yml",
        "docker-compose.dev.yml", 
        "docker-compose.windows.yml"
    )
    
    foreach ($file in $composeFiles) {
        docker-compose -f $file down 2>$null
    }
    
    Write-ColorMessage "✅ 服务已停止" "Green"
}

# 清理服务和数据
function Clear-Services {
    Write-ColorMessage "⚠️ 警告：此操作将删除所有数据！" "Yellow"
    $confirm = Read-Host "确认继续？(y/N)"
    
    if ($confirm.ToLower() -ne "y") {
        Write-ColorMessage "操作已取消" "Yellow"
        return
    }
    
    Write-ColorMessage "🧹 清理Docker服务和数据..." "Blue"
    
    $composeFiles = @(
        "docker-compose.simple.yml",
        "docker-compose.dev.yml",
        "docker-compose.windows.yml"
    )
    
    foreach ($file in $composeFiles) {
        docker-compose -f $file down -v 2>$null
    }
    
    docker system prune -f | Out-Null
    
    if (Test-Path "volumes") {
        Remove-Item -Recurse -Force "volumes"
    }
    
    Write-ColorMessage "✅ 清理完成" "Green"
}

# 查看日志
function Show-Logs {
    Write-ColorMessage "📋 显示服务日志..." "Blue"
    
    # 检测正在运行的compose文件
    $composeFile = "docker-compose.simple.yml"
    
    $devStatus = docker-compose -f "docker-compose.dev.yml" ps 2>$null | Select-String "Up"
    if ($devStatus) {
        $composeFile = "docker-compose.dev.yml"
    }
    
    $prodStatus = docker-compose -f "docker-compose.windows.yml" ps 2>$null | Select-String "Up"
    if ($prodStatus) {
        $composeFile = "docker-compose.windows.yml"
    }
    
    docker-compose -f $composeFile logs -f
}

# 显示帮助信息
function Show-Help {
    Write-Host ""
    Write-ColorMessage "用法: .\scripts\docker-start.ps1 [选项]" "White"
    Write-Host ""
    Write-ColorMessage "选项:" "Yellow"
    Write-Host "  simple    启动简化版本（默认，使用Milvus Lite）"
    Write-Host "  dev       启动开发版本"
    Write-Host "  prod      启动生产版本（Windows优化）"
    Write-Host "  stop      停止所有服务"
    Write-Host "  clean     清理所有服务和数据"
    Write-Host "  logs      查看服务日志"
    Write-Host "  help      显示此帮助信息"
    Write-Host ""
    Write-ColorMessage "示例:" "Yellow"
    Write-Host "  .\scripts\docker-start.ps1 simple   # 启动简化版本"
    Write-Host "  .\scripts\docker-start.ps1 dev      # 启动开发版本"
    Write-Host "  .\scripts\docker-start.ps1 stop     # 停止服务"
    Write-Host "  .\scripts\docker-start.ps1 logs     # 查看日志"
    Write-Host ""
}

# 主函数
function Main {
    Clear-Host
    Write-ColorMessage "🐳 视角知识库系统 - Windows Docker管理脚本" "Green"
    Write-Host ""
    
    switch ($Action.ToLower()) {
        "simple" { 
            if (Test-Docker) {
                New-RequiredDirectories
                Set-Environment
                if (Start-Services $Action) {
                    Test-Services $Action
                }
            }
        }
        "dev" { 
            if (Test-Docker) {
                New-RequiredDirectories
                Set-Environment
                if (Start-Services $Action) {
                    Test-Services $Action
                }
            }
        }
        "prod" { 
            if (Test-Docker) {
                New-RequiredDirectories
                Set-Environment
                if (Start-Services $Action) {
                    Test-Services $Action
                }
            }
        }
        "stop" { Stop-Services }
        "clean" { Clear-Services }
        "logs" { Show-Logs }
        "help" { Show-Help }
        "-h" { Show-Help }
        "--help" { Show-Help }
        default {
            Write-ColorMessage "❌ 未知选项: $Action" "Red"
            Show-Help
            exit 1
        }
    }
}

# 执行主函数
try {
    Main
}
catch {
    Write-ColorMessage "❌ 发生错误: $($_.Exception.Message)" "Red"
    exit 1
}

Write-Host ""
Write-ColorMessage "按任意键继续..." "Blue"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
