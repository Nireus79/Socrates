"""LangChain integration for Socrates agents.

Provides LangChain-compatible tools and agents for invoking Socrates
capabilities within LangChain workflows.

Example:
    ```python
    from langchain.agents import initialize_agent, AgentType
    from socratic_system.api.adapters.langchain_integration import (
        create_socrates_tools, SocratesAgentExecutor
    )

    # Create Socrates tools
    tools = create_socrates_tools(
        api_url="http://localhost:8000",
        agent_names=["code_generator", "socratic_counselor"]
    )

    # Use with LangChain
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    result = agent.run("Generate Python code for a login system")
    ```
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from langchain.callbacks.manager import (
        AsyncCallbackManagerForToolRun,
        CallbackManagerForToolRun,
    )
    from langchain.tools import BaseTool
except ImportError:
    raise ImportError(
        "LangChain required for LangChain integration. " "Install with: pip install langchain"
    )

from socratic_system.clients.socrates_agent_client import (
    SocratesAgentClient,
    SocratesAgentClientSync,
)

logger = logging.getLogger(__name__)


class SocratesTool(BaseTool):
    """LangChain tool wrapper for a Socrates agent.

    Wraps a Socrates agent to be used as a LangChain tool.
    """

    name: str
    description: str
    agent_name: str
    client: SocratesAgentClientSync
    action: str = "process"
    project_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Run tool synchronously."""
        try:
            logger.debug(f"[SocratesTool] Invoking {self.agent_name}: {query}")

            result = self.client.invoke_agent(
                self.agent_name,
                action=self.action,
                project_id=self.project_id,
                query=query,
                **kwargs,
            )

            # Extract result text
            if isinstance(result, dict):
                if "result" in result:
                    return str(result["result"])
                if "output" in result:
                    return str(result["output"])
                if "data" in result:
                    return str(result["data"])
                return str(result)
            return str(result)

        except Exception as e:
            logger.error(f"[SocratesTool] Error invoking {self.agent_name}: {e}")
            return f"Error: {str(e)}"

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Run tool asynchronously."""
        try:
            logger.debug(f"[SocratesTool] Async invoking {self.agent_name}: {query}")

            client = SocratesAgentClient(
                api_url=self.client.api_url,
                auth_token=self.client.auth_token,
            )

            result = await client.invoke_agent_sync(
                self.agent_name,
                action=self.action,
                project_id=self.project_id,
                query=query,
                **kwargs,
            )

            await client.close()

            # Extract result text
            if isinstance(result, dict):
                if "result" in result:
                    return str(result["result"])
                if "output" in result:
                    return str(result["output"])
                if "data" in result:
                    return str(result["data"])
                return str(result)
            return str(result)

        except Exception as e:
            logger.error(f"[SocratesTool] Error invoking {self.agent_name}: {e}")
            return f"Error: {str(e)}"


def create_socrates_tools(
    api_url: str = "http://localhost:8000",
    auth_token: Optional[str] = None,
    agent_names: Optional[List[str]] = None,
    project_id: Optional[str] = None,
) -> List[SocratesTool]:
    """Create LangChain tools for Socrates agents.

    Args:
        api_url: Base URL of Socrates API
        auth_token: Optional authentication token
        agent_names: List of agent names to create tools for.
                     If None, creates tools for common agents.
        project_id: Optional project ID for context

    Returns:
        List of SocratesTool instances

    Raises:
        ImportError: If LangChain not installed
    """
    if agent_names is None:
        agent_names = [
            "code_generator",
            "socratic_counselor",
            "code_validation",
            "quality_controller",
            "conflict_detector",
        ]

    client = SocratesAgentClientSync(api_url, auth_token)

    agent_configs = {
        "code_generator": {
            "name": "socrates_code_generator",
            "description": "Generate code using Socrates code generation agent. "
            "Takes a description or spec and generates working code.",
        },
        "socratic_counselor": {
            "name": "socrates_counselor",
            "description": "Ask the Socratic counselor for guidance. "
            "Useful for design decisions, architectural advice, and best practices.",
        },
        "code_validation": {
            "name": "socrates_validator",
            "description": "Validate code and run tests using Socrates validator. "
            "Checks code quality, syntax, and test coverage.",
        },
        "quality_controller": {
            "name": "socrates_quality",
            "description": "Check code quality metrics and maturity assessment. "
            "Provides comprehensive quality analysis.",
        },
        "conflict_detector": {
            "name": "socrates_conflict",
            "description": "Detect conflicts and inconsistencies in code or design. "
            "Identifies technical and architectural conflicts.",
        },
    }

    tools = []
    for agent_name in agent_names:
        if agent_name not in agent_configs:
            logger.warning(f"Unknown agent: {agent_name}")
            continue

        config = agent_configs[agent_name]
        tool = SocratesTool(
            name=config["name"],
            description=config["description"],
            agent_name=agent_name,
            client=client,
            project_id=project_id,
        )
        tools.append(tool)

    logger.info(f"[LangChain] Created {len(tools)} Socrates tools")
    return tools


class SocratesAgentExecutor:
    """Executor for running Socrates agents as part of LangChain agent workflows."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        timeout: int = 300,
    ):
        """Initialize executor.

        Args:
            api_url: Base URL of Socrates API
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.auth_token = auth_token
        self.timeout = timeout
        self.client = SocratesAgentClientSync(api_url, auth_token, timeout)

    def execute(
        self,
        agent_name: str,
        action: str = "process",
        project_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a Socrates agent.

        Args:
            agent_name: Name of agent to invoke
            action: Action to perform
            project_id: Optional project context
            **kwargs: Additional parameters to pass to agent

        Returns:
            Agent response dictionary
        """
        return self.client.invoke_agent(agent_name, action, project_id, **kwargs)

    async def execute_async(
        self,
        agent_name: str,
        action: str = "process",
        project_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a Socrates agent asynchronously.

        Args:
            agent_name: Name of agent to invoke
            action: Action to perform
            project_id: Optional project context
            **kwargs: Additional parameters to pass to agent

        Returns:
            Agent response dictionary
        """
        client = SocratesAgentClient(self.api_url, self.auth_token, self.timeout)
        try:
            return await client.invoke_agent_sync(agent_name, action, project_id, **kwargs)
        finally:
            await client.close()

    def close(self):
        """Close executor resources."""
        self.client.close()

    async def aclose(self):
        """Close executor resources asynchronously."""
        await self.client._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
