#!/usr/bin/env python3
"""
Socrates AI - Command-line entry point with optional flags
Supports running with --testing flag to enable testing mode for the current user
"""

import argparse
import logging
import os


def main():
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(
        prog="socrates",
        description="Socrates AI - A Socratic method tutoring system powered by Claude AI",
    )

    parser.add_argument(
        "--testing",
        action="store_true",
        help="Enable testing mode (bypasses monetization restrictions)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logging and debugging output)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 8.0.0",
    )

    args = parser.parse_args()

    # Set environment variable for testing mode if flag is provided
    if args.testing:
        os.environ["SOCRATES_TESTING_MODE"] = "1"

    # Set environment variable for debug mode if flag is provided
    if args.debug:
        os.environ["SOCRATES_DEBUG_MODE"] = "1"
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)

    # Import and run the main app
    from socratic_system.ui.main_app import SocraticRAGSystem

    app = SocraticRAGSystem()
    app.start()


if __name__ == "__main__":
    main()
