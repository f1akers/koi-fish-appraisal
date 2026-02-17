@echo off
REM ========================================
REM Koi Fish Appraisal - Windows Setup Script
REM ========================================
REM This script will:
REM 1. Check for admin rights
REM 2. Install Python 3.11 (if not present)
REM 3. Install Node.js 20 LTS (if not present)
REM 4. Create Python virtual environment
REM 5. Install Python dependencies
REM 6. Install Node.js dependencies
REM 7. Build the frontend
REM
REM IMPORTANT: Run this from an Administrative PowerShell or Command Prompt
REM ========================================

echo.
echo ========================================
echo   Koi Fish Appraisal - Setup
echo ========================================
echo.

REM Check for administrative privileges
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] This script requires administrative privileges.
    echo [ERROR] Please run this script from an Administrative Command Prompt.
    echo.
    echo To do this:
    echo   1. Search for "cmd" or "PowerShell" in Start Menu
    echo   2. Right-click and select "Run as administrator"
    echo   3. Navigate to this directory and run setup.bat again
    echo.
    pause
    exit /b 1
)

echo [OK] Running with administrative privileges
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM ========================================
REM Step 1: Check/Install Python
REM ========================================
echo [STEP 1/7] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Python is not installed or not in PATH
    echo [INFO] Please install Python 3.10 or higher from https://www.python.org/downloads/
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    echo.
    echo After installing Python, run this script again.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
    echo [OK] Python !PYTHON_VERSION! is installed
)
echo.

REM ========================================
REM Step 2: Check/Install Node.js
REM ========================================
echo [STEP 2/7] Checking Node.js installation...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Node.js is not installed or not in PATH
    echo [INFO] Please install Node.js 18 or higher from https://nodejs.org/
    echo [INFO] Download the LTS (Long Term Support) version
    echo.
    echo After installing Node.js, run this script again.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_VERSION=%%v
    echo [OK] Node.js !NODE_VERSION! is installed
)

npm --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm is not installed
    echo [INFO] Please reinstall Node.js from https://nodejs.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('npm --version 2^>^&1') do set NPM_VERSION=%%v
    echo [OK] npm !NPM_VERSION! is installed
)
echo.

REM ========================================
REM Step 3: Create Python Virtual Environment
REM ========================================
echo [STEP 3/7] Setting up Python virtual environment...
cd /d "%SCRIPT_DIR%backend"

if exist "venv\" (
    echo [INFO] Virtual environment already exists
) else (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

REM ========================================
REM Step 4: Install Python Dependencies
REM ========================================
echo [STEP 4/7] Installing Python dependencies...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Failed to upgrade pip, continuing anyway...
)

echo [INFO] Installing requirements from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed successfully
echo.

REM ========================================
REM Step 5: Install Node.js Dependencies
REM ========================================
echo [STEP 5/7] Installing Node.js dependencies...
cd /d "%SCRIPT_DIR%frontend"

echo [INFO] Running npm install...
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo [OK] Node.js dependencies installed successfully
echo.

REM ========================================
REM Step 6: Build Frontend
REM ========================================
echo [STEP 6/7] Building frontend for production...
echo [INFO] Running npm run build...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to build frontend
    pause
    exit /b 1
)
echo [OK] Frontend built successfully
echo.

REM ========================================
REM Step 7: Verify Models Directory
REM ========================================
echo [STEP 7/7] Verifying models directory...
cd /d "%SCRIPT_DIR%backend\models"

set MODELS_FOUND=0
if exist "koi-segment.pt" (
    echo [OK] koi-segment.pt found
    set /a MODELS_FOUND+=1
)
if exist "coin.pt" (
    echo [OK] coin.pt found
    set /a MODELS_FOUND+=1
)
if exist "koi-pattern.pt" (
    echo [OK] koi-pattern.pt found
    set /a MODELS_FOUND+=1
)

if %MODELS_FOUND% lss 3 (
    echo.
    echo [WARNING] Some required model files are missing:
    if not exist "koi-segment.pt" echo   - koi-segment.pt (YOLOv8 instance segmentation)
    if not exist "coin.pt" echo   - coin.pt (YOLOv8 coin detection)
    if not exist "koi-pattern.pt" echo   - koi-pattern.pt (YOLOv8 pattern classification)
    echo.
    echo [INFO] Place these model files in backend\models\ directory
    echo [INFO] You can train the linear regression model using:
    echo [INFO]   python -m app.train [options]
) else (
    echo [OK] All required model files found
)
echo.

REM ========================================
REM Setup Complete
REM ========================================
cd /d "%SCRIPT_DIR%"
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo [NEXT STEPS]
echo   1. Ensure all model files are in backend\models\
echo   2. Run 'run.bat' to start the application
echo   3. Access the app at http://localhost:5173
echo   4. API docs at http://localhost:8000/docs
echo.
echo [OPTIONAL] Train the linear regression model:
echo   cd backend
echo   venv\Scripts\activate
echo   python -m app.train --ogon-csv images/ogon-data.csv --ogon-images images/ogon --showa-csv images/sanke-data.csv --showa-images images/sanke --kohaku-csv images/kohaku-data.csv --kohaku-images images/kohaku
echo.
echo ========================================
pause
