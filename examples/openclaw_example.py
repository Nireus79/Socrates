"""Example: Using Socrates with OpenClaw.

This example demonstrates how to integrate Socrates agents
as OpenClaw actions and event handlers.

Requirements:
    - Socrates API running at http://localhost:8000
    - OpenClaw installed (if using actual engine)

Run:
    python examples/openclaw_example.py
"""

import asyncio
import sys
from typing import Any, Dict

# Add parent directory to path
sys.path.insert(0, ".")

from socratic_system.api.adapters.openclaw_integration import (
    ClawEventListener,
    CodeGenerationAction,
    ConflictDetectionAction,
    QualityAction,
    SocratesClawAdapter,
    ValidationAction,
)


class MockClawEngine:
    """Mock OpenClaw engine for demonstration."""

    def __init__(self):
        self.handlers: Dict[str, Any] = {}
        self.listeners: Dict[str, Any] = {}

    def register_handler(self, name: str, handler: Any) -> None:
        """Register an action handler."""
        self.handlers[name] = handler
        print(f"  Registered handler: {name}")

    def execute_action(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute a registered action."""
        if action not in self.handlers:
            raise ValueError(f"Unknown action: {action}")
        return self.handlers[action](params)

    def add_listener(self, event: str, handler: Any) -> None:
        """Add event listener."""
        self.listeners[event] = handler
        print(f"  Added listener for: {event}")

    def trigger_event(self, event: str, params: Dict[str, Any]) -> Any:
        """Trigger an event."""
        if event not in self.listeners:
            return None
        return self.listeners[event](params)


def example_basic_actions():
    """Example 1: Basic action usage."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Socrates Actions")
    print("=" * 60)

    # Create individual actions
    print("\nCreating actions:")
    code_action = CodeGenerationAction()
    validation_action = ValidationAction()
    quality_action = QualityAction()
    conflict_action = ConflictDetectionAction()

    print(f"  - Code generation: {code_action.__class__.__name__}")
    print(f"  - Validation: {validation_action.__class__.__name__}")
    print(f"  - Quality: {quality_action.__class__.__name__}")
    print(f"  - Conflict detection: {conflict_action.__class__.__name__}")

    # Demonstrate parameter structure
    print("\nAction parameter examples:")

    print("\n  Code Generation:")
    params = {
        "spec": "Create a REST API with Python Flask",
        "project_id": "proj_123",
        "language": "python",
    }
    print(f"    Parameters: {params}")
    try:
        result = code_action.execute(params)
        print(f"    Result keys: {list(result.keys())}")
    except Exception as e:
        print(f"    Note: Requires API - {type(e).__name__}")

    print("\n  Validation:")
    params = {"project_id": "proj_123"}
    print(f"    Parameters: {params}")
    try:
        result = validation_action.execute(params)
        print(f"    Result keys: {list(result.keys())}")
    except Exception as e:
        print(f"    Note: Requires API - {type(e).__name__}")


def example_adapter():
    """Example 2: Using SocratesClawAdapter."""
    print("\n" + "=" * 60)
    print("Example 2: SocratesClawAdapter Integration")
    print("=" * 60)

    # Create adapter
    adapter = SocratesClawAdapter(api_url="http://localhost:8000")

    # Get available actions
    actions = adapter.get_actions()
    print(f"\nAvailable actions ({len(actions)}):")
    for action_name in actions.keys():
        print(f"  - {action_name}")

    # Show execution example
    print("\nAction execution example:")
    print("  action_name = 'socrates_code'")
    print("  params = {")
    print("    'spec': 'Generate a user authentication module',")
    print("    'project_id': 'proj_auth',")
    print("    'language': 'python'")
    print("  }")
    print("  result = adapter.execute_action(action_name, params)")

    try:
        result = adapter.execute_action(
            "socrates_code",
            {
                "spec": "Generate a simple greeting function",
                "project_id": "proj_demo",
            },
        )
        print(f"\n  Result: {list(result.keys())}")
    except Exception as e:
        print(f"\n  Note: Requires API - {type(e).__name__}")


def example_with_engine():
    """Example 3: Integrating with mock OpenClaw engine."""
    print("\n" + "=" * 60)
    print("Example 3: Integration with OpenClaw Engine")
    print("=" * 60)

    # Create mock engine
    engine = MockClawEngine()

    # Create adapter
    adapter = SocratesClawAdapter(api_url="http://localhost:8000")

    # Register actions with engine
    print("\nRegistering Socrates actions with engine:")
    adapter.register_with_engine(engine)

    # Show registered handlers
    print(f"\nRegistered handlers ({len(engine.handlers)}):")
    for handler_name in engine.handlers.keys():
        print(f"  - {handler_name}")

    # Demonstrate execution
    print("\nExecuting 'socrates_validate' action through engine:")
    params = {"project_id": "proj_test"}
    print(f"  Parameters: {params}")

    try:
        result = engine.execute_action("socrates_validate", params)
        print(f"  Execution completed")
        print(f"  Result keys: {list(result.keys())}")
    except Exception as e:
        print(f"  Note: Requires API - {type(e).__name__}")


def example_event_handling():
    """Example 4: Event-driven integration."""
    print("\n" + "=" * 60)
    print("Example 4: Event-Driven Integration")
    print("=" * 60)

    # Create engine
    engine = MockClawEngine()

    # Create listener
    listener = ClawEventListener(api_url="http://localhost:8000")

    # Register event handlers
    print("\nRegistering event handlers:")

    # Map OpenClaw events to Socrates actions
    listener.on("project.created", "socrates_code")
    listener.on("code.ready_for_review", "socrates_quality")
    listener.on("tests.required", "socrates_validate")
    listener.on("architecture.review", "socrates_conflict")

    print("  Events registered:")
    for event_name in listener.handlers.keys():
        print(f"    - {event_name}")

    # Register with engine
    listener.register_with_engine(engine)

    # Trigger events
    print("\nTriggering events:")

    print("\n  1. project.created event:")
    print("     Parameters: {'spec': 'Build login system', 'project_id': 'proj_new'}")
    try:
        result = engine.trigger_event(
            "project.created",
            {
                "spec": "Build login system",
                "project_id": "proj_new",
            },
        )
        if result:
            print(f"     Result: {list(result.keys()) if isinstance(result, dict) else 'completed'}")
    except Exception as e:
        print(f"     Note: {type(e).__name__}")

    print("\n  2. code.ready_for_review event:")
    print("     Parameters: {'project_id': 'proj_new'}")
    try:
        result = engine.trigger_event(
            "code.ready_for_review",
            {"project_id": "proj_new"},
        )
        if result:
            print(f"     Result: {list(result.keys()) if isinstance(result, dict) else 'completed'}")
    except Exception as e:
        print(f"     Note: {type(e).__name__}")


def example_workflow():
    """Example 5: Complete workflow integration."""
    print("\n" + "=" * 60)
    print("Example 5: Complete Workflow")
    print("=" * 60)

    # Setup
    engine = MockClawEngine()
    adapter = SocratesClawAdapter(api_url="http://localhost:8000")
    adapter.register_with_engine(engine)

    # Workflow steps
    print("\nComplete Development Workflow:")
    print("  1. Generate code from specification")
    print("  2. Validate generated code")
    print("  3. Assess code quality")
    print("  4. Detect architectural conflicts")

    project_spec = {
        "spec": "REST API with user management and authentication",
        "project_id": "proj_prod_001",
        "language": "python",
    }

    print(f"\nProject: {project_spec['project_id']}")
    print(f"Specification: {project_spec['spec']}")

    # Execute workflow
    workflow_steps = [
        ("socrates_code", "Code Generation"),
        ("socrates_validate", "Code Validation"),
        ("socrates_quality", "Quality Assessment"),
        ("socrates_conflict", "Conflict Detection"),
    ]

    print("\nExecuting workflow:")
    for action, description in workflow_steps:
        print(f"\n  {description} (action: {action}):")
        try:
            result = engine.execute_action(action, project_spec)
            print(f"    Status: ✓ Completed")
            if isinstance(result, dict):
                print(f"    Results: {', '.join(result.keys())}")
        except Exception as e:
            print(f"    Status: ✗ {type(e).__name__}")


async def example_async_execution():
    """Example 6: Asynchronous action execution."""
    print("\n" + "=" * 60)
    print("Example 6: Asynchronous Execution")
    print("=" * 60)

    adapter = SocratesClawAdapter(api_url="http://localhost:8000")

    print("\nAsynchronous action execution:")
    params = {
        "spec": "Background job processor",
        "project_id": "proj_async",
    }

    print(f"  Parameters: {params}")

    try:
        result = await adapter.execute_action_async("socrates_code", params)
        print(f"  Result: {list(result.keys())}")
    except Exception as e:
        print(f"  Note: Requires API - {type(e).__name__}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Socrates + OpenClaw Integration Examples")
    print("=" * 60)

    # Run examples
    example_basic_actions()
    example_adapter()
    example_with_engine()
    example_event_handling()
    example_workflow()
    asyncio.run(example_async_execution())

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start Socrates API: docker-compose up")
    print("2. Integrate with actual OpenClaw engine")
    print("3. Create custom actions by extending ClawAction")
    print("4. Set up event listeners for your workflows")


if __name__ == "__main__":
    main()
