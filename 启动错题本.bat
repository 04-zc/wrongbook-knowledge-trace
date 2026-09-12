@echo off
setlocal
cd /d "%~dp0"
title Wrongbook Launcher

where python >nul 2>nul
if errorlevel 1 goto nopython

python -c "import flask, sqlalchemy, requests, docx, PyPDF2, fitz" >nul 2>nul
if errorlevel 1 goto install
goto run

:install
echo [INFO] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto installfail
goto run

:nopython
echo [ERROR] Python was not found. Please install Python 3.10 or newer.
pause
exit /b 1

:installfail
echo [ERROR] Failed to install dependencies.
pause
exit /b 1

:run
echo [INFO] Starting wrongbook application...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:5000'"
echo [INFO] Browser will open http://localhost:5000
echo [INFO] Close this window to stop the server.
echo.
python app.py
echo.
echo Server stopped.
pause
