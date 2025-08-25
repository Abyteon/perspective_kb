@echo off
chcp 65001 >nul
echo ========================================
echo 视角知识库系统 - Windows Docker 停止脚本
echo ========================================
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker未运行
    pause
    exit /b 1
)

echo ✅ Docker正在运行
echo.

REM 选择停止模式
echo 请选择停止模式:
echo 1. 停止生产环境
echo 2. 停止开发环境
echo 3. 停止所有容器
echo 4. 停止并清理所有数据
echo.
set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🛑 停止生产环境...
    docker-compose -f docker-compose.windows.yml down
    if errorlevel 1 (
        echo ❌ 停止失败
        pause
        exit /b 1
    )
    echo ✅ 生产环境已停止

) else if "%choice%"=="2" (
    echo.
    echo 🛑 停止开发环境...
    docker-compose -f docker-compose.dev.yml down
    if errorlevel 1 (
        echo ❌ 停止失败
        pause
        exit /b 1
    )
    echo ✅ 开发环境已停止

) else if "%choice%"=="3" (
    echo.
    echo 🛑 停止所有容器...
    docker stop $(docker ps -q)
    if errorlevel 1 (
        echo ❌ 停止失败
        pause
        exit /b 1
    )
    echo ✅ 所有容器已停止

) else if "%choice%"=="4" (
    echo.
    echo ⚠️  警告: 这将删除所有容器和数据！
    set /p confirm="确认删除? (y/N): "
    if /i "%confirm%"=="y" (
        echo 🛑 停止并清理所有数据...
        docker-compose -f docker-compose.windows.yml down -v
        docker-compose -f docker-compose.dev.yml down -v
        docker system prune -f
        echo ✅ 所有容器和数据已清理
    ) else (
        echo ❌ 操作已取消
    )

) else (
    echo ❌ 无效选择
    pause
    exit /b 1
)

echo.
echo 🎉 操作完成！按任意键退出...
pause >nul
