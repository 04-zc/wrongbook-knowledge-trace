@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Wrongbook Launcher

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" goto :python_found

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" goto :python_found

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%PYTHON_EXE%" goto :python_found

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
if exist "%PYTHON_EXE%" goto :python_found

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if exist "%PYTHON_EXE%" goto :python_found

set "PYTHON_EXE="
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=python"
if defined PYTHON_EXE goto :python_found

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=py"
if defined PYTHON_EXE goto :python_found
goto :nopython

:python_found
echo [INFO] Using Python: "%PYTHON_EXE%"
"%PYTHON_EXE%" --version
if errorlevel 1 goto :nopython

"%PYTHON_EXE%" -c "import flask, sqlalchemy, requests, docx, PyPDF2, fitz" >nul 2>nul
if errorlevel 1 goto :install
goto :run

:install
echo [INFO] Installing missing dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto :installfail
goto :run

:nopython
echo [ERROR] Python 3.10 or newer was not found.
echo [ERROR] Install Python 3.10+ and tick "Add Python to PATH", then retry.
pause
exit /b 1

:installfail
echo [ERROR] Failed to install dependencies.
pause
exit /b 1

:run
echo [INFO] Starting wrongbook application...
echo [INFO] Browser will open http://localhost:5000
echo [INFO] Keep this window open while using the application.
echo.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:5000'"
"%PYTHON_EXE%" app.py
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Server stopped. Exit code: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
