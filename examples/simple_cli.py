#!/usr/bin/env python3
"""
Simplest Way to Use Socrates AI - Interactive CLI

This is the most direct way to use Socrates AI library:
1. Install: pip install socrates-ai
2. Set API key: export ANTHROPIC_API_KEY="your-api-key"
3. Run: python simple_cli.py

That's it! You now have a fully functional interactive learning system
with Socratic questions, code generation, and project management.

No need to fork the GitHub project - the library has everything you need.
"""

import os
import sys

try:
    from socrates_ai import SocraticRAGSystem
except ImportError:
    print("Error: socrates-ai library not installed")
    print("Install with: pip install socrates-ai")
    sys.exit(1)


def main():
    """Launch the interactive Socratic learning system"""

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set\n")
        print("Please set your Claude API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print()
        print("Get a free API key from: https://console.anthropic.com")
        print()
        sys.exit(1)

    print()
    print("=" * 70)
    print("SOCRATES AI - Interactive Learning System")
    print("=" * 70)
    print()
    print("Launching interactive CLI...")
    print()
    print("Available commands:")
    print("  /project create <name>     - Create a new learning project")
    print("  /ask <question>            - Ask Socratic questions")
    print("  /code generate <spec>      - Generate code from specifications")
    print("  /help                      - Show all available commands")
    print("  exit                       - Exit the system")
    print()

    try:
        # Launch the interactive system
        system = SocraticRAGSystem()
        system.start()

    except KeyboardInterrupt:
        print("\n\nSocrates AI stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
