#!/usr/bin/env python3
"""
Custom pytest runner that bypasses Windows I/O issues
Uses pytest.main() directly without capture module
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up module alias before any imports
try:
    import socrates
except ModuleNotFoundError:
    import socratic_system as socrates
    sys.modules['socrates'] = socrates


def run_tests():
    """Run tests using pytest.main() with capture disabled"""
    import pytest

    print("=" * 90)
    print("SOCRATES COMPREHENSIVE TEST SUITE")
    print("Running with pytest (capture disabled to avoid Windows I/O issues)")
    print("=" * 90)
    print()

    # Run pytest with specific arguments
    args = [
        "tests/",
        "-v",  # Verbose
        "-p", "no:cacheprovider",  # Disable cache
        "-p", "no:assertion",  # Disable assertion rewriting
        "--tb=short",  # Short traceback format
        "-W", "ignore::DeprecationWarning",  # Ignore deprecation warnings
        "--no-header",  # Don't print pytest header
    ]

    # Run tests
    exit_code = pytest.main(args)

    print()
    print("=" * 90)
    if exit_code == 0:
        print("STATUS: ALL TESTS PASSED")
    else:
        print(f"STATUS: TESTS FAILED (exit code: {exit_code})")
    print("=" * 90)

    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
