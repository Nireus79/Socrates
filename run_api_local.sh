#!/bin/bash
# Run API with LOCAL code (monorepo)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/backend/src:$SCRIPT_DIR/cli/src:$PYTHONPATH"

echo "Starting Socrates API with LOCAL code (monorepo)"
echo "PYTHONPATH: $PYTHONPATH"
echo ""

python -m socrates_api
