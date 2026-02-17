@echo off
REM Koi Fish Appraisal - Windows Run Script
REM Starts both backend and frontend servers simultaneously

echo ========================================
echo   Koi Fish Appraisal - Starting Servers
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Check if virtual environment exists
if not exist "%SCRIPT_DIR%backend\venv\" (
    echo [ERROR] Python virtual environment not found
    echo [INFO] Please run setup.bat first to install dependencies
    pause
    exit /b 1
)

REM Check if frontend build exists
if not exist "%SCRIPT_DIR%frontend\dist\" (
    echo [ERROR] Frontend build not found
    echo [INFO] Please run setup.bat first to build the frontend
    pause
    exit /b 1
)

REM Check if Node.js is available
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo [INFO] Please run setup.bat first to install Node.js
    pause
    exit /b 1
)

REM Start Backend Server
echo [INFO] Starting Backend Server (FastAPI)...
start "Koi Backend" cmd /k "cd /d %SCRIPT_DIR%backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start Frontend Server (Production Preview)
echo [INFO] Starting Frontend Server (Vite Preview)...
start "Koi Frontend" cmd /k "cd /d %SCRIPT_DIR%frontend && npm run preview -- --host 0.0.0.0 --port 5173"

echo.
echo ========================================
echo   Servers Started Successfully!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo   NOTE: Running in production mode (built frontend)
echo   To run in development mode, use:
echo     Backend:  cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo     Frontend: cd frontend ^&^& npm run dev
echo.
echo   Close the terminal windows to stop the servers.
echo ========================================
