@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title 错题本知识溯源整理助手

echo ==========================================
echo   错题本知识溯源整理助手
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10 或更高版本。
    pause
    exit /b 1
)

python -c "import flask, sqlalchemy, requests, docx, PyPDF2, fitz" >nul 2>nul
if errorlevel 1 (
    echo [提示] 正在安装项目依赖...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络或 Python 环境。
        pause
        exit /b 1
    )
)

echo [提示] 正在启动服务...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:5000'"
echo [提示] 浏览器将自动打开 http://localhost:5000
echo [提示] 关闭本窗口即可停止服务。
echo.

python app.py

echo.
echo 服务已停止。
pause
