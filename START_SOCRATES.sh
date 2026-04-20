#!/bin/bash
# Complete Socrates Startup Script
# Starts API server, frontend, and displays CLI instructions

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_PORT=8000
FRONTEND_PORT=5173

echo "======================================================================"
echo "         🤔 SOCRATES - Complete Modular System Startup"
echo "======================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 1. Start API Server
print_step "Starting Socrates API server..."

cd "$PROJECT_ROOT/backend"

# Check if venv exists
if [ ! -d ".venv" ]; then
    print_warning "Virtual environment not found. Creating..."
    python -m venv .venv
fi

# Activate venv
source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null

# Install dependencies
if ! pip list | grep -q fastapi; then
    print_warning "Installing dependencies..."
    pip install -q -e .
fi

# Start API in background
python -m uvicorn socrates_api.main:app --reload --host 0.0.0.0 --port $API_PORT &
API_PID=$!
print_success "API server started (PID: $API_PID) on http://localhost:$API_PORT"

# Wait for API to be ready
print_step "Waiting for API server to be ready..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:$API_PORT/health > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "API server failed to start"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
print_success "API server is ready"

# 2. Start Frontend
print_step "Starting Socrates Frontend..."

cd "$PROJECT_ROOT/socrates-frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_warning "Installing frontend dependencies..."
    npm install -q
fi

# Start frontend in background
npm run dev -- --port $FRONTEND_PORT > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
print_success "Frontend started (PID: $FRONTEND_PID) on http://localhost:$FRONTEND_PORT"

# Wait for frontend to be ready
print_step "Waiting for Frontend to be ready..."
sleep 5
print_success "Frontend is ready"

# 3. Display instructions
echo ""
echo "======================================================================"
echo "              🎉 SOCRATES IS RUNNING - Choose Your Interface"
echo "======================================================================"
echo ""

echo -e "${GREEN}📚 WEB FRONTEND (Recommended for Chat)${NC}"
echo "   URL: http://localhost:$FRONTEND_PORT"
echo "   - Interactive Socratic chat interface"
echo "   - Visual project management"
echo "   - Real-time specs and conflicts"
echo ""

echo -e "${GREEN}🖥️  REST API${NC}"
echo "   URL: http://localhost:$API_PORT"
echo "   - Full REST API for programmatic access"
echo "   - OpenAPI docs: http://localhost:$API_PORT/docs"
echo ""

echo -e "${GREEN}⌨️  COMMAND LINE INTERFACE (CLI)${NC}"
echo "   Usage: python -m socrates_cli <command>"
echo ""
echo "   Quick start:"
echo "   - socrates project create --name 'My Project'"
echo "   - socrates chat                              # Interactive Socratic chat"
echo "   - socrates project list                      # List projects"
echo "   - socrates maturity status                   # Check maturity"
echo "   - socrates subscription status               # Check subscription"
echo ""
echo "   For more commands:"
echo "   - socrates --help"
echo ""

echo "======================================================================"
echo "              📊 SYSTEM COMPONENTS"
echo "======================================================================"
echo ""

echo -e "${GREEN}✓ API Server${NC}        (localhost:$API_PORT)"
echo -e "${GREEN}✓ Web Frontend${NC}       (localhost:$FRONTEND_PORT)"
echo -e "${GREEN}✓ CLI Tool${NC}           (ready for commands)"
echo ""

echo "======================================================================"
echo "              🔧 INTEGRATION NOTES"
echo "======================================================================"
echo ""

echo "Environment Variables:"
echo "  SOCRATES_API_URL=http://localhost:$API_PORT (for CLI)"
echo "  ANTHROPIC_API_KEY=<your-key>                   (for LLM)"
echo ""

echo "Key Features:"
echo "  ✓ Socratic Question Generation"
echo "  ✓ Spec Extraction from Responses"
echo "  ✓ Conflict Detection"
echo "  ✓ Maturity Tracking"
echo "  ✓ Phase Transitions"
echo "  ✓ Real-time Feedback"
echo ""

echo "======================================================================"
echo "              📝 TESTING YOUR SETUP"
echo "======================================================================"
echo ""

echo "1. Test API Health:"
echo "   curl http://localhost:$API_PORT/health"
echo ""

echo "2. Create a Project (via CLI):"
echo "   python -m socrates_cli project create --name 'Calculator App'"
echo ""

echo "3. Start Interactive Chat (via CLI):"
echo "   python -m socrates_cli chat"
echo ""

echo "4. Open Web Frontend:"
echo "   Open browser to: http://localhost:$FRONTEND_PORT"
echo ""

echo "======================================================================"
echo "              🛑 STOPPING SOCRATES"
echo "======================================================================"
echo ""

echo "To stop all services:"
echo "  1. Press Ctrl+C here to stop API and Frontend"
echo "  2. Or kill specific processes:"
echo "     kill $API_PID         (API server)"
echo "     kill $FRONTEND_PID    (Frontend)"
echo ""

# Create a cleanup trap
cleanup() {
    print_step "Shutting down Socrates..."
    kill $API_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    print_success "Socrates stopped"
}

trap cleanup EXIT

echo "======================================================================"
echo ""

# Keep the script running
wait $API_PID $FRONTEND_PID 2>/dev/null || true
