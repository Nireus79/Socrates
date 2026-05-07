"""API layer for external access to agents.

Provides REST/gRPC adapters and library client for accessing Socrates agents.
"""

from .client import SocratesAgentClient, SocratesAgentClientSync
from .rest_handlers import create_agent_router

__all__ = [
    "create_agent_router",
    "SocratesAgentClient",
    "SocratesAgentClientSync",
]
