#!/usr/bin/env python3
"""
Windows Entry Point for Socrates EXE

This wrapper ensures that when the .exe is launched (double-clicked or via shortcut),
it defaults to --full mode (API + Frontend + Browser) instead of CLI-only mode.

For other modes, users can still use command line arguments:
  socrates.exe --api       (API server only)
  socrates.exe             (CLI only)
  socrates.exe --frontend  (CLI with frontend)
"""

import sys
from pathlib import Path

# Add current directory to path
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))


def main():
    """
    Main entry point that defaults to --full mode for Windows users.

    If user specified explicit mode flags, respect those.
    Otherwise, default to --full for the best user experience.
    """

    # Check if user provided explicit mode arguments
    has_explicit_mode = any(
        arg in sys.argv for arg in ["--api", "--full", "--frontend", "--help", "--version"]
    )

    # If no explicit mode was specified, add --full as default
    if not has_explicit_mode:
        sys.argv.append("--full")

    # Import and run the main socrates module
    from socrates import main as socrates_main
    socrates_main()


if __name__ == "__main__":
    main()
