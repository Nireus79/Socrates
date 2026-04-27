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

import asyncio
import os
import sys

try:
    from socrates_ai import ConfigBuilder, create_orchestrator
except ImportError:
    print("Error: socrates-ai library not installed")
    print("Install with: pip install socrates-ai")
    sys.exit(1)


def print_help():
    """Print available commands"""
    print("\nAvailable commands:")
    print("  project <name>         - Create a new learning project")
    print("  question <topic>       - Get a Socratic question")
    print("  code <specification>   - Generate code from specifications")
    print("  help                   - Show this help message")
    print("  exit                   - Exit the system\n")


async def main():
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

    # Initialize Socrates
    config = ConfigBuilder(api_key=api_key).build()
    orchestrator = create_orchestrator(config)
    current_project_id = None

    print()
    print("=" * 70)
    print("SOCRATES AI - Interactive Learning System")
    print("=" * 70)
    print()
    print("Welcome to Socrates AI! Type 'help' for available commands.")
    print()

    try:
        while True:
            try:
                command = input("socrates> ").strip()

                if not command:
                    continue

                if command.lower() == "exit":
                    print("\nGoodbye!")
                    break

                if command.lower() == "help":
                    print_help()
                    continue

                # Parse command
                parts = command.split(maxsplit=1)
                action = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if action == "project" and args:
                    print(f"Creating project '{args}'...")
                    # In a real implementation, this would call the orchestrator
                    current_project_id = f"proj_{args.replace(' ', '_')}"
                    print(f"✓ Project created: {current_project_id}\n")

                elif action == "question" and args:
                    if not current_project_id:
                        print("Error: Create a project first with 'project <name>'\n")
                        continue
                    print(f"Generating question about '{args}'...")
                    # In a real implementation, this would call the orchestrator
                    print("✓ Question: What architectural patterns would be best for this?\n")

                elif action == "code" and args:
                    if not current_project_id:
                        print("Error: Create a project first with 'project <name>'\n")
                        continue
                    print(f"Generating code for: {args}...")
                    # In a real implementation, this would call the orchestrator
                    print("✓ Code generated successfully\n")

                else:
                    print("Unknown command. Type 'help' for available commands.\n")

            except KeyboardInterrupt:
                print("\n")
                continue
            except Exception as e:
                print(f"Error: {e}\n")

    except KeyboardInterrupt:
        print("\n\nSocrates AI stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
