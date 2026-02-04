@echo off
REM Koi Fish Appraisal - Windows Run Script
REM Starts both backend and frontend servers simultaneously

echo ========================================
echo   Koi Fish Appraisal - Starting Servers
echo ========================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Start Backend Server
echo [INFO] Starting Backend Server (FastAPI)...
start "Koi Backend" cmd /k "cd /d %SCRIPT_DIR%backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to initialize
timeout /t 2 /nobreak >nul

REM Start Frontend Server
echo [INFO] Starting Frontend Server (Vite)...
start "Koi Frontend" cmd /k "cd /d %SCRIPT_DIR%frontend && npm run dev"

echo.
echo ========================================
echo   Servers Started Successfully!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo   Close the terminal windows to stop the servers.
echo ========================================
