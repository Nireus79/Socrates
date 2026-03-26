#!/bin/bash
# Setup environment for Socrates monorepo development
# Usage: source setup_env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SRC="$SCRIPT_DIR/backend/src"
CLI_SRC="$SCRIPT_DIR/cli/src"

# Set PYTHONPATH to include local code
export PYTHONPATH="$BACKEND_SRC:$CLI_SRC:$PYTHONPATH"

echo "================================================="
echo "Socrates Monorepo Environment Setup"
echo "================================================="
echo ""
echo "PYTHONPATH configured for local imports:"
echo "  Backend: $BACKEND_SRC"
echo "  CLI:     $CLI_SRC"
echo ""
echo "You can now run:"
echo "  python -m socrates_api         # Start API server"
echo "  cd frontend && npm run dev     # Start frontend"
echo ""
