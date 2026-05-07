"""Example: Using Socrates with LangChain.

This example demonstrates how to integrate Socrates agents with LangChain
for multi-agent workflows.

Requirements:
    - Socrates API running at http://localhost:8000
    - LangChain installed: pip install langchain
    - OpenAI API key set in environment (for LLM agent)

Run:
    python examples/langchain_example.py
"""

import asyncio
import sys
from typing import Any

# Add parent directory to path
sys.path.insert(0, ".")

try:
    from langchain.agents import AgentType, initialize_agent
    from langchain.llm_math.base import LLMMathChain
    from langchain_openai import ChatOpenAI
except ImportError:
    print("Please install LangChain: pip install langchain langchain-openai")
    sys.exit(1)

from socratic_system.api.adapters.langchain_integration import (
    SocratesAgentExecutor,
    create_socrates_tools,
)


def example_basic_tools():
    """Example 1: Basic tool creation and usage."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Socrates Tools with LangChain")
    print("=" * 60)

    # Create Socrates tools
    tools = create_socrates_tools(
        api_url="http://localhost:8000",
        agent_names=["code_generator", "socratic_counselor", "code_validation"],
    )

    print(f"Created {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # Demonstrate tool invocation
    print("\nTesting tool: socrates_code_generator")
    code_gen_tool = [t for t in tools if "code_generator" in t.agent_name][0]

    try:
        result = code_gen_tool._run(query="Generate a Python function to calculate Fibonacci numbers")
        print(f"Result: {result[:200]}...")
    except Exception as e:
        print(f"Note: Tool requires running Socrates API - {e}")


def example_with_agent():
    """Example 2: Using Socrates tools with LangChain agent."""
    print("\n" + "=" * 60)
    print("Example 2: Socrates Tools with LangChain Agent")
    print("=" * 60)

    try:
        # Initialize LLM
        llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)

        # Create Socrates tools
        tools = create_socrates_tools(
            api_url="http://localhost:8000",
            agent_names=["code_generator", "code_validation", "socratic_counselor"],
        )

        # Initialize agent
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=3,
        )

        # Run agent
        query = "Generate a Python REST API server with Flask and then validate it"
        print(f"\nQuery: {query}")
        print("\nNote: This requires OpenAI API key and running Socrates API")

        # Uncomment to run (requires API keys):
        # result = agent.run(query)
        # print(f"\nResult: {result}")

    except Exception as e:
        print(f"Setup example (full execution requires API keys): {e}")


async def example_executor():
    """Example 3: Using SocratesAgentExecutor for direct control."""
    print("\n" + "=" * 60)
    print("Example 3: Direct SocratesAgentExecutor Usage")
    print("=" * 60)

    async with SocratesAgentExecutor(api_url="http://localhost:8000") as executor:
        print("Executor initialized")
        print("Available methods:")
        print("  - executor.execute(agent_name, action, project_id, **kwargs)")
        print("  - await executor.execute_async(agent_name, action, project_id, **kwargs)")

        # Example execution (requires API)
        try:
            result = executor.execute(
                "socratic_counselor",
                action="process",
                query="What are best practices for Python code organization?",
            )
            print(f"\nResult: {result}")
        except Exception as e:
            print(f"\nNote: Execution requires running Socrates API - {e}")


def example_tool_registry():
    """Example 4: Creating tool registry for different workflows."""
    print("\n" + "=" * 60)
    print("Example 4: Tool Registry for Multiple Workflows")
    print("=" * 60)

    # Create specialized tool sets
    backend_tools = create_socrates_tools(
        agent_names=["code_generator", "code_validation"],
    )

    architecture_tools = create_socrates_tools(
        agent_names=["quality_controller", "conflict_detector", "socratic_counselor"],
    )

    print("Backend Development Tools:")
    for tool in backend_tools:
        print(f"  - {tool.name}")

    print("\nArchitecture Review Tools:")
    for tool in architecture_tools:
        print(f"  - {tool.name}")


def example_custom_tool():
    """Example 5: Creating custom tool with Socrates integration."""
    print("\n" + "=" * 60)
    print("Example 5: Custom Tool Composition")
    print("=" * 60)

    from socratic_system.api.adapters.langchain_integration import SocratesTool
    from socratic_system.clients.socrates_agent_client import SocratesAgentClientSync

    # Create custom tool combining multiple Socrates agents
    client = SocratesAgentClientSync("http://localhost:8000")

    class CodeQualityTool(SocratesTool):
        """Combined tool for code generation and quality checking."""

        name = "code_quality_pipeline"
        description = (
            "Generates code and validates its quality. "
            "Combines code generation and quality assessment."
        )
        agent_name = "code_generator"

        def _run(self, query: str, **kwargs) -> str:
            """Generate code and assess quality."""
            # Step 1: Generate code
            result = self.client.invoke_agent(
                "code_generator",
                action="process",
                query=query,
                **kwargs,
            )

            # Step 2: Validate
            validation = self.client.invoke_agent(
                "code_validation",
                action="process",
                query=f"Validate this code: {result}",
                **kwargs,
            )

            return f"Generated Code:\n{result}\n\nValidation:\n{validation}"

    tool = CodeQualityTool(client=client)
    print(f"Created custom tool: {tool.name}")
    print(f"Description: {tool.description}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Socrates + LangChain Integration Examples")
    print("=" * 60)

    # Run examples
    example_basic_tools()
    example_with_agent()
    asyncio.run(example_executor())
    example_tool_registry()
    example_custom_tool()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start Socrates API: docker-compose up")
    print("2. Set OpenAI API key: export OPENAI_API_KEY=sk-...")
    print("3. Run full examples (uncomment execution sections)")


if __name__ == "__main__":
    main()
