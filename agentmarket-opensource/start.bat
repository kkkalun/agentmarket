@echo off
chcp 65001 >nul
echo ==========================================
echo   AgentMarket 开发服务器启动脚本
echo ==========================================
echo.

:: 切换到项目目录
cd /d "%~dp0"

:: 启动服务器（内置端口清理）
python -B main.py

pause
