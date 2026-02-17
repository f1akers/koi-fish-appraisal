#!/bin/bash

# ========================================
# Koi Fish Appraisal - Linux/Mac Setup Script
# ========================================
# This script will:
# 1. Check for sudo privileges
# 2. Check/Install Python 3.10+
# 3. Check/Install Node.js 18+
# 4. Create Python virtual environment
# 5. Install Python dependencies
# 6. Install Node.js dependencies
# 7. Build the frontend
#
# Run with: bash setup.sh
# ========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "  Koi Fish Appraisal - Setup"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ========================================
# Helper Functions
# ========================================

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Check if running on Linux or macOS
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)     OS_NAME="Linux";;
    Darwin*)    OS_NAME="macOS";;
    *)          OS_NAME="UNKNOWN";;
esac

print_info "Detected OS: $OS_NAME"
echo ""

# ========================================
# Step 1: Check Python Installation
# ========================================
echo "[STEP 1/7] Checking Python installation..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_ok "Python $PYTHON_VERSION is installed"
    PYTHON_CMD="python3"
else
    print_error "Python 3 is not installed"
    print_info "Please install Python 3.10 or higher:"
    
    if [ "$OS_NAME" = "Linux" ]; then
        print_info "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
        print_info "  Fedora/RHEL:   sudo dnf install python3 python3-pip"
        print_info "  Arch:          sudo pacman -S python python-pip"
    elif [ "$OS_NAME" = "macOS" ]; then
        print_info "  Using Homebrew: brew install python@3.11"
        print_info "  Or download from: https://www.python.org/downloads/"
    fi
    
    echo ""
    print_info "After installing Python, run this script again."
    exit 1
fi

# Verify Python version is 3.10 or higher
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10+ is required, but you have $PYTHON_VERSION"
    print_info "Please upgrade Python to version 3.10 or higher"
    exit 1
fi
echo ""

# ========================================
# Step 2: Check Node.js Installation
# ========================================
echo "[STEP 2/7] Checking Node.js installation..."

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_ok "Node.js $NODE_VERSION is installed"
else
    print_error "Node.js is not installed"
    print_info "Please install Node.js 18 or higher:"
    
    if [ "$OS_NAME" = "Linux" ]; then
        print_info "  Using NodeSource repository:"
        print_info "    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        print_info "    sudo apt-get install -y nodejs"
        print_info "  Or download from: https://nodejs.org/"
    elif [ "$OS_NAME" = "macOS" ]; then
        print_info "  Using Homebrew: brew install node"
        print_info "  Or download from: https://nodejs.org/"
    fi
    
    echo ""
    print_info "After installing Node.js, run this script again."
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_ok "npm $NPM_VERSION is installed"
else
    print_error "npm is not installed"
    print_info "Please reinstall Node.js from https://nodejs.org/"
    exit 1
fi
echo ""

# ========================================
# Step 3: Create Python Virtual Environment
# ========================================
echo "[STEP 3/7] Setting up Python virtual environment..."
cd "$SCRIPT_DIR/backend"

if [ -d "venv" ]; then
    print_info "Virtual environment already exists"
else
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        print_info "You may need to install python3-venv:"
        print_info "  Ubuntu/Debian: sudo apt install python3-venv"
        exit 1
    fi
    print_ok "Virtual environment created"
fi
echo ""

# ========================================
# Step 4: Install Python Dependencies
# ========================================
echo "[STEP 4/7] Installing Python dependencies..."

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

print_info "Upgrading pip..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
    print_warning "Failed to upgrade pip, continuing anyway..."
fi

print_info "Installing requirements from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install Python dependencies"
    exit 1
fi
print_ok "Python dependencies installed successfully"
echo ""

# ========================================
# Step 5: Install Node.js Dependencies
# ========================================
echo "[STEP 5/7] Installing Node.js dependencies..."
cd "$SCRIPT_DIR/frontend"

print_info "Running npm install..."
npm install
if [ $? -ne 0 ]; then
    print_error "Failed to install Node.js dependencies"
    exit 1
fi
print_ok "Node.js dependencies installed successfully"
echo ""

# ========================================
# Step 6: Build Frontend
# ========================================
echo "[STEP 6/7] Building frontend for production..."
print_info "Running npm run build..."
npm run build
if [ $? -ne 0 ]; then
    print_error "Failed to build frontend"
    exit 1
fi
print_ok "Frontend built successfully"
echo ""

# ========================================
# Step 7: Verify Models Directory
# ========================================
echo "[STEP 7/7] Verifying models directory..."
cd "$SCRIPT_DIR/backend/models"

MODELS_FOUND=0

if [ -f "koi-segment.pt" ]; then
    print_ok "koi-segment.pt found"
    ((MODELS_FOUND++))
fi

if [ -f "coin.pt" ]; then
    print_ok "coin.pt found"
    ((MODELS_FOUND++))
fi

if [ -f "koi-pattern.pt" ]; then
    print_ok "koi-pattern.pt found"
    ((MODELS_FOUND++))
fi

if [ $MODELS_FOUND -lt 3 ]; then
    echo ""
    print_warning "Some required model files are missing:"
    [ ! -f "koi-segment.pt" ] && echo "  - koi-segment.pt (YOLOv8 instance segmentation)"
    [ ! -f "coin.pt" ] && echo "  - coin.pt (YOLOv8 coin detection)"
    [ ! -f "koi-pattern.pt" ] && echo "  - koi-pattern.pt (YOLOv8 pattern classification)"
    echo ""
    print_info "Place these model files in backend/models/ directory"
    print_info "You can train the linear regression model using:"
    print_info "  python -m app.train [options]"
else
    print_ok "All required model files found"
fi
echo ""

# ========================================
# Setup Complete
# ========================================
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "[NEXT STEPS]"
echo "  1. Ensure all model files are in backend/models/"
echo "  2. Run './run.sh' to start the application"
echo "  3. Access the app at http://localhost:5173"
echo "  4. API docs at http://localhost:8000/docs"
echo ""
echo "[OPTIONAL] Train the linear regression model:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m app.train --ogon-csv images/ogon-data.csv --ogon-images images/ogon --showa-csv images/sanke-data.csv --showa-images images/sanke --kohaku-csv images/kohaku-data.csv --kohaku-images images/kohaku"
echo ""
echo "========================================"
