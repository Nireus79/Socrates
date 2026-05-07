"""Example: Using Socrates with LangGraph.

This example demonstrates how to build LangGraph workflows
with Socrates agent nodes.

Requirements:
    - Socrates API running at http://localhost:8000
    - LangGraph installed: pip install langgraph langchain

Run:
    python examples/langgraph_example.py
"""

import asyncio
import sys
from typing import Any

# Add parent directory to path
sys.path.insert(0, ".")

try:
    from langgraph.graph import END, StateGraph
except ImportError:
    print("Please install LangGraph: pip install langgraph langchain")
    sys.exit(1)

from socratic_system.api.adapters.langgraph_integration import (
    SocratesGraphBuilder,
    SocratesState,
    create_initial_state,
    create_socrates_nodes,
)


def example_simple_workflow():
    """Example 1: Simple sequential workflow."""
    print("\n" + "=" * 60)
    print("Example 1: Simple Sequential Workflow")
    print("=" * 60)

    # Create workflow
    workflow = StateGraph(SocratesState)

    # Add Socrates nodes
    nodes = create_socrates_nodes(
        api_url="http://localhost:8000",
        agents=["socratic_counselor", "code_generator"],
    )

    for node_name, node_fn in nodes.items():
        workflow.add_node(node_name, node_fn)

    # Define edges
    workflow.add_edge("socratic_counselor", "code_generator")
    workflow.add_edge("code_generator", END)

    # Set entry point
    workflow.set_entry_point("socratic_counselor")

    print("Workflow created with nodes:")
    for name in nodes.keys():
        print(f"  - {name}")

    print("\nEdges:")
    print("  socratic_counselor -> code_generator -> END")

    # Compile
    app = workflow.compile()

    # Run
    initial_state = create_initial_state(
        query="How should I structure a Python web application?",
        project_id="proj_123",
    )

    print("\nRunning workflow...")
    print(f"Query: {initial_state['query']}")

    try:
        result = app.invoke(initial_state)
        print("\nWorkflow completed!")
        print(f"Agent results: {list(result['agent_results'].keys())}")
    except Exception as e:
        print(f"Note: Requires running Socrates API - {e}")


def example_conditional_workflow():
    """Example 2: Workflow with conditional routing."""
    print("\n" + "=" * 60)
    print("Example 2: Conditional Workflow")
    print("=" * 60)

    # Define routing function
    def route_to_validation(state: SocratesState) -> str:
        """Route based on query content."""
        if "test" in state["query"].lower() or "valid" in state["query"].lower():
            return "code_validation"
        return "code_generator"

    # Create workflow
    workflow = StateGraph(SocratesState)

    # Add nodes
    nodes = create_socrates_nodes(
        api_url="http://localhost:8000",
        agents=["code_generator", "code_validation", "quality_controller"],
    )

    for node_name, node_fn in nodes.items():
        workflow.add_node(node_name, node_fn)

    # Add conditional edge
    workflow.set_entry_point("code_generator")
    workflow.add_conditional_edges(
        "code_generator",
        route_to_validation,
        {
            "code_validation": "code_validation",
            "code_generator": "quality_controller",
        },
    )
    workflow.add_edge("code_validation", "quality_controller")
    workflow.add_edge("quality_controller", END)

    print("Conditional workflow created")
    print("Routing:")
    print("  - If query contains 'test' -> validation path")
    print("  - Otherwise -> quality assessment path")

    # Compile
    app = workflow.compile()

    # Example runs
    print("\nExample 1: Code generation query")
    state1 = create_initial_state(query="Generate a login system")
    try:
        result = app.invoke(state1)
        print(f"Executed agents: {list(result['agent_results'].keys())}")
    except Exception as e:
        print(f"Note: {e}")

    print("\nExample 2: Test/validation query")
    state2 = create_initial_state(query="Validate the test suite")
    try:
        result = app.invoke(state2)
        print(f"Executed agents: {list(result['agent_results'].keys())}")
    except Exception as e:
        print(f"Note: {e}")


def example_parallel_workflow():
    """Example 3: Workflow with parallel execution."""
    print("\n" + "=" * 60)
    print("Example 3: Parallel Execution Workflow")
    print("=" * 60)

    # Create workflow
    workflow = StateGraph(SocratesState)

    # Add nodes
    nodes = create_socrates_nodes(
        api_url="http://localhost:8000",
        agents=[
            "code_generator",
            "code_validation",
            "quality_controller",
            "conflict_detector",
        ],
    )

    for node_name, node_fn in nodes.items():
        workflow.add_node(node_name, node_fn)

    # Code generation first
    workflow.set_entry_point("code_generator")

    # Then parallel validation, quality, and conflict check
    workflow.add_edge("code_generator", "code_validation")
    workflow.add_edge("code_generator", "quality_controller")
    workflow.add_edge("code_generator", "conflict_detector")

    # All converge to END
    workflow.add_edge("code_validation", END)
    workflow.add_edge("quality_controller", END)
    workflow.add_edge("conflict_detector", END)

    print("Parallel workflow created")
    print("Execution pattern:")
    print("  1. Generate code")
    print("  2. In parallel:")
    print("     - Validate code")
    print("     - Assess quality")
    print("     - Detect conflicts")

    app = workflow.compile()

    state = create_initial_state(query="Generate and analyze a microservice architecture")

    print("\nRunning parallel workflow...")
    try:
        result = app.invoke(state)
        print(f"Completed agents: {list(result['agent_results'].keys())}")
    except Exception as e:
        print(f"Note: {e}")


def example_graph_builder():
    """Example 4: Using SocratesGraphBuilder."""
    print("\n" + "=" * 60)
    print("Example 4: Using SocratesGraphBuilder")
    print("=" * 60)

    # Create builder
    builder = (
        SocratesGraphBuilder(api_url="http://localhost:8000")
        .add_agent("code_generator", node_name="generate")
        .add_agent("code_validation", node_name="validate")
        .add_agent("quality_controller", node_name="quality")
    )

    # Build workflow
    workflow = StateGraph(SocratesState)

    nodes = builder.get_all_nodes()
    for node_name, node_fn in nodes.items():
        workflow.add_node(node_name, node_fn)

    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "validate")
    workflow.add_edge("validate", "quality")
    workflow.add_edge("quality", END)

    print("Built workflow with custom node names:")
    for name in nodes.keys():
        print(f"  - {name}")

    app = workflow.compile()

    state = create_initial_state(
        query="Build a production-ready API",
        project_id="proj_prod_001",
    )

    print("\nRunning builder-created workflow...")
    try:
        result = app.invoke(state)
        print(f"Agents executed: {list(result['agent_results'].keys())}")
    except Exception as e:
        print(f"Note: {e}")


async def example_async_workflow():
    """Example 5: Async workflow with custom routing."""
    print("\n" + "=" * 60)
    print("Example 5: Async Workflow")
    print("=" * 60)

    from socratic_system.api.adapters.langgraph_integration import SocratesNode

    # Create nodes using async
    node = SocratesNode("code_generator", api_url="http://localhost:8000")

    state = create_initial_state(
        query="Generate a FastAPI application",
        project_id="proj_async",
    )

    print("Testing async node execution...")
    try:
        result = await node.acall(state)
        print(f"Async execution completed")
        print(f"Messages: {len(result['messages'])}")
    except Exception as e:
        print(f"Note: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Socrates + LangGraph Integration Examples")
    print("=" * 60)

    # Run examples
    example_simple_workflow()
    example_conditional_workflow()
    example_parallel_workflow()
    example_graph_builder()
    asyncio.run(example_async_workflow())

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start Socrates API: docker-compose up")
    print("2. Run full workflows with API running")
    print("3. Create custom workflows using patterns above")


if __name__ == "__main__":
    main()
