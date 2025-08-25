@echo off
chcp 65001 >nul
echo ========================================
echo 视角知识库系统 - Windows Docker 启动脚本
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到Docker，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo ✅ Docker已安装
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker未运行，请启动Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker正在运行
echo.

REM 创建必要的目录
if not exist "volumes" mkdir volumes
if not exist "log" mkdir log
if not exist "data\processed" mkdir data\processed

echo ✅ 目录结构已准备
echo.

REM 选择运行模式
echo 请选择运行模式:
echo 1. 生产环境 (完整Milvus服务器 + Ollama)
echo 2. 开发环境 - 本地模式 (Milvus Lite + Ollama)
echo 3. 开发环境 - 服务器模式 (Milvus Lite服务器 + Ollama)
echo 4. 仅启动Ollama服务
echo.
set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动生产环境...
    docker-compose -f docker-compose.windows.yml up -d
    if errorlevel 1 (
        echo ❌ 启动失败
        pause
        exit /b 1
    )
    echo.
    echo ✅ 生产环境启动成功！
    echo 📊 服务地址:
    echo   - Milvus: http://localhost:19530
    echo   - MinIO Console: http://localhost:9001
    echo   - Ollama: http://localhost:11434
    echo   - 应用: http://localhost:8000
    echo.
    echo 📝 查看日志: docker-compose -f docker-compose.windows.yml logs -f

) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动开发环境（本地模式）...
    docker-compose -f docker-compose.dev.yml up -d perspective-kb-dev-local ollama
    if errorlevel 1 (
        echo ❌ 启动失败
        pause
        exit /b 1
    )
    echo.
    echo ✅ 开发环境（本地模式）启动成功！
    echo 📊 服务地址:
    echo   - Ollama: http://localhost:11434
    echo   - 应用: http://localhost:8000
    echo.
    echo 📝 查看日志: docker-compose -f docker-compose.dev.yml logs -f perspective-kb-dev-local

) else if "%choice%"=="3" (
    echo.
    echo 🚀 启动开发环境（服务器模式）...
    docker-compose -f docker-compose.dev.yml up -d perspective-kb-dev-server milvus-lite ollama
    if errorlevel 1 (
        echo ❌ 启动失败
        pause
        exit /b 1
    )
    echo.
    echo ✅ 开发环境（服务器模式）启动成功！
    echo 📊 服务地址:
    echo   - Milvus Lite: http://localhost:19530
    echo   - Ollama: http://localhost:11434
    echo   - 应用: http://localhost:8001
    echo.
    echo 📝 查看日志: docker-compose -f docker-compose.dev.yml logs -f perspective-kb-dev-server

) else if "%choice%"=="4" (
    echo.
    echo 🚀 仅启动Ollama服务...
    docker run -d --name ollama-standalone -p 11434:11434 -v %cd%\volumes\ollama:/root/.ollama ollama/ollama:latest
    if errorlevel 1 (
        echo ❌ 启动失败
        pause
        exit /b 1
    )
    echo.
    echo ✅ Ollama服务启动成功！
    echo 📊 服务地址: http://localhost:11434
    echo.
    echo 📝 查看日志: docker logs -f ollama-standalone

) else (
    echo ❌ 无效选择
    pause
    exit /b 1
)

echo.
echo 🎉 启动完成！按任意键退出...
pause >nul
