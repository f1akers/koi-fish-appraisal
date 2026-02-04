#!/bin/bash

# Koi Fish Appraisal - Linux/macOS Run Script
# Starts both backend and frontend servers simultaneously

echo "========================================"
echo "  Koi Fish Appraisal - Starting Servers"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed or not in PATH"
    exit 1
fi

# Determine python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in PATH"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "[INFO] Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start Backend Server
echo "[INFO] Starting Backend Server (FastAPI)..."
cd "$SCRIPT_DIR/backend"
$PYTHON_CMD -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2

# Start Frontend Server
echo "[INFO] Starting Frontend Server (Vite)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Servers Started Successfully!"
echo "========================================"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo "========================================"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
