#!/usr/bin/env python3
"""
Test runner using subprocess to bypass pytest cleanup issues on Windows
"""

import subprocess
import sys
from pathlib import Path


def run_tests_subprocess():
    """Run pytest in a subprocess to avoid capture module issues"""

    print("=" * 90)
    print("SOCRATES COMPREHENSIVE TEST SUITE")
    print("Running pytest in subprocess to bypass Windows I/O issues")
    print("=" * 90)
    print()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "-s",  # No capture
        "--tb=short",
        "-p",
        "no:cacheprovider",
        "--co",  # Collect only first
    ]

    # First, show what tests will be run
    print("Collecting tests...")
    result = subprocess.run(cmd, cwd=str(Path(__file__).parent), capture_output=True, text=True)

    if result.returncode == 0:
        # Count tests
        lines = result.stdout.split("\n")
        test_count = len([l for l in lines if "<Function" in l or "<Method" in l])
        print(f"Found {test_count} tests")
        print()

        # Now run the actual tests
        print("Running tests (this may take a moment)...")
        print("-" * 90)

        # Use -x to stop on first failure, --tb=line for minimal output
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-v",
            "-s",
            "--tb=short",
            "-p",
            "no:cacheprovider",
        ]

        result = subprocess.run(cmd, cwd=str(Path(__file__).parent))

        print()
        print("=" * 90)
        if result.returncode == 0:
            print("STATUS: ALL TESTS PASSED")
        else:
            print(f"STATUS: TESTS FAILED OR INCOMPLETE (exit code: {result.returncode})")
        print("=" * 90)

        return result.returncode
    else:
        print("ERROR during test collection:")
        print(result.stderr)
        return 1


if __name__ == "__main__":
    exit_code = run_tests_subprocess()
    sys.exit(exit_code)
