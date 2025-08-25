@echo off
chcp 65001 >nul
title 视角知识库系统 - 快速启动

echo.
echo ==========================================
echo 🚀 视角知识库系统 - Windows快速启动
echo ==========================================
echo.

REM 检查Docker是否运行
echo 🔍 检查Docker状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未运行！
    echo.
    echo 请先启动Docker Desktop:
    echo 1. 双击桌面上的Docker Desktop图标
    echo 2. 等待Docker完全启动（约1-2分钟）
    echo 3. 再次运行此脚本
    echo.
    echo 如果没有安装Docker Desktop，请访问:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo ✅ Docker运行正常

REM 显示部署选项
echo.
echo 请选择部署模式:
echo [1] 简化模式 - 快速启动，适合初次使用 (推荐)
echo [2] 开发模式 - 开发调试功能完整
echo [3] 生产模式 - 完整功能，适合正式使用
echo [4] 查看服务状态
echo [5] 停止所有服务
echo [6] 查看日志
echo [0] 退出
echo.

set /p choice=请输入选择 (1-6): 

if "%choice%"=="1" (
    echo.
    echo 🚀 启动简化模式...
    call scripts\docker-start.bat simple
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 🚀 启动开发模式...
    call scripts\docker-start.bat dev
    goto end
)

if "%choice%"=="3" (
    echo.
    echo 🚀 启动生产模式...
    call scripts\docker-start.bat prod
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 🔍 查看服务状态...
    echo.
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo.
    pause
    goto end
)

if "%choice%"=="5" (
    echo.
    echo ⏹️ 停止所有服务...
    call scripts\docker-start.bat stop
    goto end
)

if "%choice%"=="6" (
    echo.
    echo 📋 查看日志...
    call scripts\docker-start.bat logs
    goto end
)

if "%choice%"=="0" (
    echo 再见！
    exit /b 0
)

echo ❌ 无效选择，请重新运行脚本
pause

:end
echo.
echo 脚本执行完成。
pause
