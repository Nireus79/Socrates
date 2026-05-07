"""API adapters for external access."""

from .agent_adapter import AgentAdapter
from .langchain_integration import (
    SocratesAgentExecutor,
    SocratesTool,
    create_socrates_tools,
)
from .langgraph_integration import (
    SocratesGraphBuilder,
    SocratesNode,
    SocratesState,
    create_initial_state,
    create_socrates_nodes,
)
from .openclaw_integration import (
    ClawAction,
    ClawEventListener,
    CodeGenerationAction,
    ConflictDetectionAction,
    QualityAction,
    SocratesClawAdapter,
    ValidationAction,
)

__all__ = [
    "AgentAdapter",
    # LangChain
    "SocratesTool",
    "create_socrates_tools",
    "SocratesAgentExecutor",
    # LangGraph
    "SocratesState",
    "SocratesNode",
    "create_socrates_nodes",
    "create_initial_state",
    "SocratesGraphBuilder",
    # OpenClaw
    "ClawAction",
    "CodeGenerationAction",
    "ValidationAction",
    "QualityAction",
    "ConflictDetectionAction",
    "SocratesClawAdapter",
    "ClawEventListener",
]
