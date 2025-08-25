@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM 视角知识库系统 - Windows Docker启动脚本
REM 用于快速启动整个系统

echo.
echo 🐳 视角知识库系统 - Windows Docker管理脚本
echo.

REM 检查参数
set ACTION=%1
if "%ACTION%"=="" set ACTION=simple

if "%ACTION%"=="help" goto :help
if "%ACTION%"=="-h" goto :help
if "%ACTION%"=="--help" goto :help
if "%ACTION%"=="stop" goto :stop
if "%ACTION%"=="clean" goto :clean
if "%ACTION%"=="logs" goto :logs

REM 检查Docker是否运行
echo 🔍 检查Docker状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未运行，请先启动Docker Desktop
    echo    下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo ✅ Docker运行正常

REM 创建必要的目录
echo.
echo 📁 创建必要的目录...
if not exist "volumes\ollama" mkdir volumes\ollama
if not exist "volumes\app_data" mkdir volumes\app_data
if not exist "log" mkdir log
echo ✅ 目录创建完成

REM 设置环境变量
echo.
echo ⚙️ 设置环境变量...
if not exist ".env" (
    copy env.example .env >nul
    echo 📋 已复制环境配置文件，请根据需要修改 .env
)
echo ✅ 环境配置完成

REM 选择配置文件
set COMPOSE_FILE=docker-compose.simple.yml
if "%ACTION%"=="dev" set COMPOSE_FILE=docker-compose.dev.yml
if "%ACTION%"=="prod" set COMPOSE_FILE=docker-compose.windows.yml

echo.
echo 🚀 启动Docker服务...
echo 使用配置文件: %COMPOSE_FILE%

REM 停止现有服务
docker-compose -f %COMPOSE_FILE% down >nul 2>&1

REM 构建并启动
echo 构建并启动服务...
docker-compose -f %COMPOSE_FILE% up --build -d

if errorlevel 1 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

echo ✅ 服务启动完成

REM 等待服务就绪
echo.
echo ⏳ 等待服务就绪...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 🔍 检查服务状态...
docker-compose -f %COMPOSE_FILE% ps

echo.
echo 📍 服务访问地址:
echo   • 应用服务: http://localhost:8000
echo   • Ollama API: http://localhost:11434
echo.
echo 📋 常用命令:
echo   查看日志: docker-compose -f %COMPOSE_FILE% logs -f
echo   停止服务: %~nx0 stop
echo   清理数据: %~nx0 clean
echo.
echo ✅ 系统启动完成！
pause
exit /b 0

:stop
echo ⏹️ 停止Docker服务...
docker-compose -f docker-compose.simple.yml down >nul 2>&1
docker-compose -f docker-compose.dev.yml down >nul 2>&1
docker-compose -f docker-compose.windows.yml down >nul 2>&1
echo ✅ 服务已停止
pause
exit /b 0

:clean
echo.
echo ⚠️ 警告：此操作将删除所有数据！
set /p CONFIRM=确认继续？(y/N): 
if /i not "%CONFIRM%"=="y" (
    echo 操作已取消
    pause
    exit /b 0
)
echo.
echo 🧹 清理Docker服务和数据...
docker-compose -f docker-compose.simple.yml down -v >nul 2>&1
docker-compose -f docker-compose.dev.yml down -v >nul 2>&1
docker-compose -f docker-compose.windows.yml down -v >nul 2>&1
docker system prune -f
if exist "volumes" rmdir /s /q volumes
echo ✅ 清理完成
pause
exit /b 0

:logs
echo 📋 显示服务日志...
REM 检测正在运行的compose文件
set COMPOSE_FILE=docker-compose.simple.yml
docker-compose -f docker-compose.dev.yml ps 2>nul | findstr "Up" >nul
if not errorlevel 1 set COMPOSE_FILE=docker-compose.dev.yml
docker-compose -f docker-compose.windows.yml ps 2>nul | findstr "Up" >nul
if not errorlevel 1 set COMPOSE_FILE=docker-compose.windows.yml

docker-compose -f %COMPOSE_FILE% logs -f
exit /b 0

:help
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   simple    启动简化版本（默认，使用Milvus Lite）
echo   dev       启动开发版本
echo   prod      启动生产版本（Windows优化）
echo   stop      停止所有服务
echo   clean     清理所有服务和数据
echo   logs      查看服务日志
echo   help      显示此帮助信息
echo.
echo 示例:
echo   %~nx0 simple   # 启动简化版本
echo   %~nx0 dev      # 启动开发版本
echo   %~nx0 stop     # 停止服务
echo   %~nx0 logs     # 查看日志
echo.
pause
exit /b 0
