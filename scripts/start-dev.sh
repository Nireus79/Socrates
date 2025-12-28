#!/bin/bash

# Socrates AI - Development Startup Script for Linux/macOS
#
# Starts the entire system:
# - Backend API (FastAPI)
# - Frontend Dev Server (Vite)
#
# Usage: From Socrates root directory
#    ./scripts/start-dev.sh
# or
#    bash scripts/start-dev.sh

set -e

# Colors
BLUE='\033[94m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
END='\033[0m'

# Helper functions
print_header() {
    echo -e "\n${BLUE}======================================================${END}"
    echo -e "${BLUE}$1${END}"
    echo -e "${BLUE}======================================================${END}\n"
}

print_ok() {
    echo -e "${GREEN}✓ $1${END}"
}

print_error() {
    echo -e "${RED}✗ $1${END}"
    exit 1
}

print_info() {
    echo -e "${YELLOW}→ $1${END}"
}

# Check if in correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the Socrates root directory"
fi

# Main startup
print_header "Socrates AI - Development Startup"

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3.9+ not found. Please install it first."
fi
print_ok "Python 3 found: $(python3 --version)"

if ! command -v node &> /dev/null; then
    print_error "Node.js 14+ not found. Please install it first."
fi
print_ok "Node.js found: $(node --version)"

if ! command -v npm &> /dev/null; then
    print_error "npm not found. Please install Node.js first."
fi
print_ok "npm found: $(npm --version)"

# Install Python dependencies
print_info "Checking Python dependencies..."
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    print_info "Installing Python dependencies..."
    pip install -q -r requirements.txt
fi
print_ok "Python dependencies ready"

# Install Node dependencies
if [ ! -d "socrates-frontend/node_modules" ]; then
    print_info "Installing Node.js dependencies..."
    cd socrates-frontend
    npm install -q --legacy-peer-deps
    cd ..
fi
print_ok "Node.js dependencies ready"

# Cleanup function for graceful shutdown
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${END}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}Services stopped${END}"
    exit 0
}

# Set trap for Ctrl+C
trap cleanup SIGINT SIGTERM

# Start services
print_header "Starting Services"

# Start Backend
print_info "Starting Backend API (port 8000)..."
ENVIRONMENT=development python3 -m uvicorn socrates_api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload > /tmp/socrates-backend.log 2>&1 &
BACKEND_PID=$!
sleep 2
print_ok "Backend API started (PID: $BACKEND_PID)"

# Start Frontend
print_info "Starting Frontend Dev Server (port 5173)..."
cd socrates-frontend
npm run dev > /tmp/socrates-frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3
cd ..
print_ok "Frontend Dev Server started (PID: $FRONTEND_PID)"

# Print access information
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${END}"
echo -e "${GREEN}║     Socrates AI is Running!            ║${END}"
echo -e "${GREEN}╚════════════════════════════════════════╝${END}"
echo ""
echo -e "Frontend:       ${BLUE}http://localhost:5173${END}"
echo -e "Backend API:    ${BLUE}http://localhost:8000${END}"
echo -e "API Docs:       ${BLUE}http://localhost:8000/docs${END}"
echo ""
echo "Logs:"
echo "  Backend:  tail -f /tmp/socrates-backend.log"
echo "  Frontend: tail -f /tmp/socrates-frontend.log"
echo ""
echo -e "Press ${YELLOW}Ctrl+C${END} to stop all services"
echo ""

# Monitor processes
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend API crashed (check /tmp/socrates-backend.log)"
    fi

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend Dev Server crashed (check /tmp/socrates-frontend.log)"
    fi

    sleep 5
done
