"""Messaging layer for agent communication.

Provides event-driven agent-to-agent messaging without direct coupling.
"""

from .agent_bus import AgentBus, AgentError, AgentTimeoutError

__all__ = [
    "AgentBus",
    "AgentError",
    "AgentTimeoutError",
]
