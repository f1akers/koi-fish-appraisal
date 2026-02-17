#!/bin/bash

# ========================================
# Koi Fish Appraisal - Linux/Mac Run Script
# ========================================
# Starts both backend and frontend servers simultaneously
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
echo "  Koi Fish Appraisal - Starting Servers"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Helper functions
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    print_error "Python virtual environment not found"
    print_info "Please run ./setup.sh first to install dependencies"
    exit 1
fi

# Check if frontend build exists
if [ ! -d "$SCRIPT_DIR/frontend/dist" ]; then
    print_error "Frontend build not found"
    print_info "Please run ./setup.sh first to build the frontend"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed or not in PATH"
    print_info "Please run ./setup.sh first to install Node.js"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    print_info "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend Server
print_info "Starting Backend Server (FastAPI)..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 3

# Start Frontend Server (Production Preview)
print_info "Starting Frontend Server (Vite Preview)..."
cd "$SCRIPT_DIR/frontend"
npm run preview -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

# Wait for frontend to initialize
sleep 2

echo ""
echo "========================================"
echo "  Servers Started Successfully!"
echo "========================================"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:5173"
echo ""
echo "  NOTE: Running in production mode (built frontend)"
echo "  To run in development mode, use:"
echo "    Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "    Frontend: cd frontend && npm run dev"
echo ""
echo "  Press Ctrl+C to stop the servers."
echo "========================================"
echo ""

# Wait for user to stop servers
wait
