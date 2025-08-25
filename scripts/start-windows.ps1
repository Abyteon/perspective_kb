# 视角知识库系统 - Windows PowerShell 启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视角知识库系统 - Windows Docker 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否安装
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
    Write-Host "✅ Docker已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 未检测到Docker，请先安装Docker Desktop" -ForegroundColor Red
    Write-Host "下载地址: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""

# 检查Docker是否运行
try {
    docker info >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
    Write-Host "✅ Docker正在运行" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: Docker未运行，请启动Docker Desktop" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""

# 创建必要的目录
$directories = @("volumes", "log", "data\processed")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "✅ 目录结构已准备" -ForegroundColor Green
Write-Host ""

# 选择运行模式
Write-Host "请选择运行模式:" -ForegroundColor Yellow
Write-Host "1. 生产环境 (完整Milvus + Ollama)" -ForegroundColor White
Write-Host "2. 开发环境 (Milvus Lite + Ollama)" -ForegroundColor White
Write-Host "3. 仅启动Ollama服务" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选择 (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 启动生产环境..." -ForegroundColor Green
        
        try {
            docker-compose -f docker-compose.windows.yml up -d
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to start production environment"
            }
            
            Write-Host ""
            Write-Host "✅ 生产环境启动成功！" -ForegroundColor Green
            Write-Host "📊 服务地址:" -ForegroundColor Cyan
            Write-Host "  - Milvus: http://localhost:19530" -ForegroundColor White
            Write-Host "  - MinIO Console: http://localhost:9001" -ForegroundColor White
            Write-Host "  - Ollama: http://localhost:11434" -ForegroundColor White
            Write-Host "  - 应用: http://localhost:8000" -ForegroundColor White
            Write-Host ""
            Write-Host "📝 查看日志: docker-compose -f docker-compose.windows.yml logs -f" -ForegroundColor Gray
        } catch {
            Write-Host "❌ 启动失败: $($_.Exception.Message)" -ForegroundColor Red
            Read-Host "按回车键退出"
            exit 1
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "🚀 启动开发环境..." -ForegroundColor Green
        
        try {
            docker-compose -f docker-compose.dev.yml up -d
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to start development environment"
            }
            
            Write-Host ""
            Write-Host "✅ 开发环境启动成功！" -ForegroundColor Green
            Write-Host "📊 服务地址:" -ForegroundColor Cyan
            Write-Host "  - Milvus Lite: http://localhost:19530" -ForegroundColor White
            Write-Host "  - Ollama: http://localhost:11434" -ForegroundColor White
            Write-Host "  - 应用: http://localhost:8000" -ForegroundColor White
            Write-Host ""
            Write-Host "📝 查看日志: docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor Gray
        } catch {
            Write-Host "❌ 启动失败: $($_.Exception.Message)" -ForegroundColor Red
            Read-Host "按回车键退出"
            exit 1
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "🚀 仅启动Ollama服务..." -ForegroundColor Green
        
        try {
            docker run -d --name ollama-standalone -p 11434:11434 -v "${PWD}\volumes\ollama:/root/.ollama" ollama/ollama:latest
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to start Ollama service"
            }
            
            Write-Host ""
            Write-Host "✅ Ollama服务启动成功！" -ForegroundColor Green
            Write-Host "📊 服务地址: http://localhost:11434" -ForegroundColor White
            Write-Host ""
            Write-Host "📝 查看日志: docker logs -f ollama-standalone" -ForegroundColor Gray
        } catch {
            Write-Host "❌ 启动失败: $($_.Exception.Message)" -ForegroundColor Red
            Read-Host "按回车键退出"
            exit 1
        }
    }
    
    default {
        Write-Host "❌ 无效选择" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 启动完成！按回车键退出..." -ForegroundColor Green
Read-Host
