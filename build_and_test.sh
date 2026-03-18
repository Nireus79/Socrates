#!/bin/bash

# Build and test all Socrates packages
# This script builds all packages and verifies they can be installed and imported

set -e

echo "=========================================="
echo "Socrates Package Build and Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0

# Function to test a package
test_package() {
    local package_dir=$1
    local package_name=$2

    TOTAL=$((TOTAL + 1))

    echo -e "${YELLOW}[${TOTAL}] Testing ${package_name}...${NC}"

    if [ ! -d "$package_dir" ]; then
        echo -e "${RED}❌ Directory not found: ${package_dir}${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi

    cd "$package_dir"

    # Check if pyproject.toml exists
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}❌ pyproject.toml not found${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi

    # Build package
    echo "  Building..."
    if python -m build --quiet 2>/dev/null; then
        echo "  ✓ Build successful"
    else
        echo -e "${RED}  ❌ Build failed${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi

    # Verify wheel was created
    if ls dist/*.whl > /dev/null 2>&1; then
        echo "  ✓ Wheel created"
    else
        echo -e "${RED}  ❌ Wheel not found${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi

    # Verify source distribution was created
    if ls dist/*.tar.gz > /dev/null 2>&1; then
        echo "  ✓ Source distribution created"
    else
        echo -e "${RED}  ❌ Source distribution not found${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi

    echo -e "${GREEN}✓ ${package_name} passed${NC}"
    PASSED=$((PASSED + 1))
    cd - > /dev/null
    return 0
}

# Function to test package imports
test_imports() {
    local package_name=$1
    local import_statement=$2

    echo "  Testing import: ${import_statement}"
    if python -c "${import_statement}" 2>/dev/null; then
        echo "  ✓ Import successful"
        return 0
    else
        echo -e "${RED}  ❌ Import failed${NC}"
        return 1
    fi
}

# Check prerequisites
echo "Checking prerequisites..."
command -v python >/dev/null 2>&1 || { echo "Python not found"; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "pip not found"; exit 1; }

python -m pip install -q build twine > /dev/null 2>&1 || { echo "Failed to install build tools"; exit 1; }
echo "✓ Prerequisites met"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Building Packages"
echo "=========================================="
echo ""

# Test each package
test_package "socratic-core" "socratic-core"
test_package "socrates-cli" "socrates-cli"
test_package "socrates-api" "socrates-api"

echo ""
echo "=========================================="
echo "Testing Package Imports"
echo "=========================================="
echo ""

# Install core for import testing
echo "Installing socratic-core for import testing..."
cd "$SCRIPT_DIR/socratic-core"
pip install -q -e . > /dev/null 2>&1

# Test imports
echo "Testing socratic-core imports..."
test_imports "socratic-core" "from socratic_core import SocratesConfig; print('OK')"
test_imports "socratic-core" "from socratic_core import EventEmitter, EventType; print('OK')"
test_imports "socratic-core" "from socratic_core.exceptions import SocratesError; print('OK')"
test_imports "socratic-core" "from socratic_core.utils import ProjectIDGenerator; print('OK')"

echo ""
echo "Testing backward compatibility..."
cd "$SCRIPT_DIR"
test_imports "backward-compat" "from socratic_system import SocratesConfig; print('OK')"
test_imports "backward-compat" "from socratic_system import EventType; print('OK')"

echo ""
echo "=========================================="
echo "Verifying Package Contents"
echo "=========================================="
echo ""

# Check README files
echo "Checking documentation..."
docs=(
    "QUICKSTART.md"
    "INSTALL.md"
    "ARCHITECTURE.md"
    "MIGRATION_GUIDE.md"
    "TRANSFORMATION_STORY.md"
    "socratic-core/README.md"
    "socrates-cli/README.md"
    "socrates-api/README.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✓ $doc"
    else
        echo "  ❌ Missing: $doc"
        FAILED=$((FAILED + 1))
    fi
done

# Check LICENSE files
echo ""
echo "Checking license files..."
licenses=(
    "LICENSE"
    "socratic-core/LICENSE"
    "socrates-cli/LICENSE"
    "socrates-api/LICENSE"
)

for license in "${licenses[@]}"; do
    if [ -f "$license" ]; then
        echo "  ✓ $license"
    else
        echo "  ❌ Missing: $license"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=========================================="
echo "Verification Results"
echo "=========================================="
echo ""
echo "Total tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "All tests passed! ✓"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Review dist/ directories for build artifacts"
    echo "2. Test package installations:"
    echo "   pip install socratic-core/dist/*.whl"
    echo "3. Publish to PyPI:"
    echo "   twine upload socratic-core/dist/*"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "Some tests failed ✗"
    echo "=========================================="
    exit 1
fi
