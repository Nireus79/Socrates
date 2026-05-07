"""LangGraph integration for Socrates agents.

Provides LangGraph-compatible state nodes and graph builders for incorporating
Socrates capabilities into LangGraph workflows.

Example:
    ```python
    from langgraph.graph import StateGraph, END
    from socratic_system.api.adapters.langgraph_integration import (
        SocratesState, create_socrates_nodes
    )

    # Define workflow
    workflow = StateGraph(SocratesState)

    # Add Socrates nodes
    nodes = create_socrates_nodes(
        api_url="http://localhost:8000",
        agents=["code_generator", "code_validation"]
    )

    for node_name, node_fn in nodes.items():
        workflow.add_node(node_name, node_fn)

    # Connect nodes
    workflow.add_edge("code_generator", "code_validation")
    workflow.add_edge("code_validation", END)

    # Run
    app = workflow.compile()
    result = app.invoke({
        "query": "Generate a login system",
        "project_id": "proj_123"
    })
    ```
"""

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypedDict

try:
    from langchain.schema import AIMessage, BaseMessage, HumanMessage
except ImportError:
    raise ImportError(
        "LangChain required for LangGraph integration. "
        "Install with: pip install langchain"
    )

from socratic_system.clients.socrates_agent_client import (
    SocratesAgentClient,
    SocratesAgentClientSync,
)

logger = logging.getLogger(__name__)


class SocratesState(TypedDict):
    """State for LangGraph workflows with Socrates integration.

    Attributes:
        query: Current query or task description
        project_id: Project context (optional)
        agent_results: Dictionary of agent execution results
        messages: Message history
        metadata: Additional metadata
    """

    query: str
    project_id: Optional[str]
    agent_results: Dict[str, Any]
    messages: List[BaseMessage]
    metadata: Dict[str, Any]


class SocratesNode:
    """LangGraph node for executing a Socrates agent."""

    def __init__(
        self,
        agent_name: str,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        action: str = "process",
    ):
        """Initialize Socrates node.

        Args:
            agent_name: Name of Socrates agent to invoke
            api_url: Base URL of Socrates API
            auth_token: Optional authentication token
            action: Action to perform on agent
        """
        self.agent_name = agent_name
        self.api_url = api_url
        self.auth_token = auth_token
        self.action = action
        self.client = SocratesAgentClientSync(api_url, auth_token)

    def __call__(self, state: SocratesState) -> SocratesState:
        """Execute node synchronously.

        Args:
            state: Current graph state

        Returns:
            Updated state with agent results
        """
        try:
            logger.info(f"[SocratesNode] Executing {self.agent_name} with query: {state['query']}")

            result = self.client.invoke_agent(
                self.agent_name,
                action=self.action,
                project_id=state.get("project_id"),
                query=state["query"],
            )

            # Update state with results
            state["agent_results"][self.agent_name] = result

            # Add to message history
            result_msg = self._format_result_message(result)
            state["messages"].append(result_msg)

            logger.debug(f"[SocratesNode] {self.agent_name} completed successfully")

        except Exception as e:
            logger.error(f"[SocratesNode] Error executing {self.agent_name}: {e}")
            state["agent_results"][self.agent_name] = {"error": str(e)}
            state["messages"].append(
                AIMessage(content=f"Error from {self.agent_name}: {str(e)}")
            )

        return state

    async def acall(self, state: SocratesState) -> SocratesState:
        """Execute node asynchronously.

        Args:
            state: Current graph state

        Returns:
            Updated state with agent results
        """
        client = SocratesAgentClient(self.api_url, self.auth_token)
        try:
            logger.info(f"[SocratesNode] Async executing {self.agent_name}")

            result = await client.invoke_agent_sync(
                self.agent_name,
                action=self.action,
                project_id=state.get("project_id"),
                query=state["query"],
            )

            # Update state with results
            state["agent_results"][self.agent_name] = result

            # Add to message history
            result_msg = self._format_result_message(result)
            state["messages"].append(result_msg)

            logger.debug(f"[SocratesNode] {self.agent_name} completed successfully")

        except Exception as e:
            logger.error(f"[SocratesNode] Error executing {self.agent_name}: {e}")
            state["agent_results"][self.agent_name] = {"error": str(e)}
            state["messages"].append(
                AIMessage(content=f"Error from {self.agent_name}: {str(e)}")
            )

        finally:
            await client.close()

        return state

    @staticmethod
    def _format_result_message(result: Dict[str, Any]) -> AIMessage:
        """Format agent result as AIMessage.

        Args:
            result: Agent result dictionary

        Returns:
            Formatted AIMessage
        """
        if isinstance(result, dict):
            if "result" in result:
                content = str(result["result"])
            elif "output" in result:
                content = str(result["output"])
            elif "data" in result:
                content = str(result["data"])
            else:
                content = str(result)
        else:
            content = str(result)

        return AIMessage(content=content)


def create_socrates_nodes(
    api_url: str = "http://localhost:8000",
    auth_token: Optional[str] = None,
    agents: Optional[List[str]] = None,
) -> Dict[str, Callable[[SocratesState], SocratesState]]:
    """Create LangGraph nodes for Socrates agents.

    Args:
        api_url: Base URL of Socrates API
        auth_token: Optional authentication token
        agents: List of agent names. If None, uses common agents.

    Returns:
        Dictionary mapping node names to node functions
    """
    if agents is None:
        agents = [
            "code_generator",
            "socratic_counselor",
            "code_validation",
            "quality_controller",
            "conflict_detector",
        ]

    nodes = {}
    for agent_name in agents:
        node = SocratesNode(agent_name, api_url, auth_token)
        nodes[agent_name] = node
        logger.debug(f"[LangGraph] Created node for {agent_name}")

    logger.info(f"[LangGraph] Created {len(nodes)} Socrates nodes")
    return nodes


def create_initial_state(
    query: str,
    project_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> SocratesState:
    """Create initial state for LangGraph workflow.

    Args:
        query: Initial query/task
        project_id: Optional project context
        metadata: Optional additional metadata

    Returns:
        Initial SocratesState
    """
    return {
        "query": query,
        "project_id": project_id,
        "agent_results": {},
        "messages": [HumanMessage(content=query)],
        "metadata": metadata or {},
    }


class SocratesGraphBuilder:
    """Helper for building LangGraph workflows with Socrates agents."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
    ):
        """Initialize graph builder.

        Args:
            api_url: Base URL of Socrates API
            auth_token: Optional authentication token
        """
        self.api_url = api_url
        self.auth_token = auth_token
        self.nodes: Dict[str, SocratesNode] = {}

    def add_agent(
        self,
        agent_name: str,
        node_name: Optional[str] = None,
        action: str = "process",
    ) -> "SocratesGraphBuilder":
        """Add a Socrates agent as a node.

        Args:
            agent_name: Name of Socrates agent
            node_name: Custom node name (defaults to agent_name)
            action: Action to perform

        Returns:
            Self for chaining
        """
        node_key = node_name or agent_name
        self.nodes[node_key] = SocratesNode(
            agent_name,
            self.api_url,
            self.auth_token,
            action,
        )
        logger.debug(f"[GraphBuilder] Added agent {agent_name} as node {node_key}")
        return self

    def build_node(self, name: str) -> Callable[[SocratesState], SocratesState]:
        """Build a node function.

        Args:
            name: Node name

        Returns:
            Node function
        """
        if name not in self.nodes:
            raise ValueError(f"Node '{name}' not found")
        return self.nodes[name]

    def get_all_nodes(self) -> Dict[str, Callable[[SocratesState], SocratesState]]:
        """Get all built nodes.

        Returns:
            Dictionary of node functions
        """
        return {name: node for name, node in self.nodes.items()}
