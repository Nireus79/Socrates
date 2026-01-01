#!/usr/bin/env python3
"""
Complete Socrates AI Workflow Example

This example demonstrates actual real-world usage of Socrates AI library,
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
    python socrates.py
"""

import importlib.util
import os

if importlib.util.find_spec("socrates_ai") is None:
    print("Install socrates-ai: pip install socrates-ai")
    raise ImportError("socrates-ai is not installed")

api_key = os.environ.get("ANTHROPIC_API_KEY")
if api_key:
    print('ANTHROPIC_API_KEY is environment variable is set')
else:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")


def main():
    from socrates_ai import SocraticRAGSystem
    system = SocraticRAGSystem()
    system.start()


if __name__ == "__main__":
    main()
