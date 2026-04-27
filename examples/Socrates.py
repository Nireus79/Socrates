#!/usr/bin/env python3
"""
Complete Socrates AI Workflow Example

This example demonstrates real-world usage of Socrates AI library,
with REAL API calls to Claude AI, showing:
- Project creation and management
- Socratic questioning (with actual Claude-generated questions)
- Code generation (with real generated code)
- Real conversation with the AI system

This is NOT a demo - it actually works with Claude API and shows real output.

Requirements:
    pip install socrates-ai

Setup:
    export ANTHROPIC_API_KEY="your-api-key"

Run:
    python Socrates.py
"""

import asyncio
import importlib.util
import os
import sys

if importlib.util.find_spec("socrates_ai") is None:
    print("Install socrates-ai: pip install socrates-ai")
    raise ImportError("socrates-ai is not installed")

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set")
    print("Get a free API key from: https://console.anthropic.com")
    sys.exit(1)


async def main():
    """Run the Socrates AI workflow"""
    from socrates_ai import ConfigBuilder, create_orchestrator, EventType

    # Build configuration
    config = (
        ConfigBuilder(api_key=api_key)
        .with_claude_model("claude-3-opus-20240229")
        .with_log_level("INFO")
        .build()
    )

    # Create orchestrator
    orchestrator = create_orchestrator(config)

    # Register event listeners
    def on_event(event_type, data):
        print(f"[EVENT] {event_type}: {data}")

    for event in [
        EventType.PROJECT_CREATED,
        EventType.CODE_GENERATED,
        EventType.QUESTION_GENERATED,
    ]:
        orchestrator.event_emitter.on(event, lambda et, d, e=event: on_event(e, d))

    print("\n" + "=" * 70)
    print("SOCRATES AI - Workflow Example")
    print("=" * 70 + "\n")

    try:
        # Example: Create a project
        print("Creating a new project...")
        project = await orchestrator.agents["ProjectManager"].execute({
            "action": "create_project",
            "name": "CLI Calculator",
            "description": "A command-line calculator application",
            "owner": "example_user",
        })
        print(f"✓ Project created: {project.get('project_id')}\n")

        # Example: Ask a Socratic question
        print("Generating Socratic questions...")
        question = await orchestrator.agents["SocraticCounselor"].execute({
            "action": "generate_question",
            "project_id": project.get("project_id"),
            "topic": "CLI application design",
            "difficulty": "intermediate",
        })
        print(f"✓ Question: {question.get('question')}\n")

        # Example: Generate code
        print("Generating code...")
        code = await orchestrator.agents["CodeGenerator"].execute({
            "action": "generate_code",
            "project_id": project.get("project_id"),
            "specification": "Create a Python calculator with add, subtract, multiply, divide operations",
            "language": "python",
        })
        print(f"✓ Code generated: {len(code.get('code', ''))} characters\n")

        print("=" * 70)
        print("Workflow complete! Check console output above for results.")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nSocrates workflow stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
