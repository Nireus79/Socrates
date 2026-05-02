"""
Agent Registry - Central registry for agent discovery and lifecycle management.

Enables dynamic agent registration, discovery, and health monitoring.
Provides single source of truth for available agents and their capabilities.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class AgentMetadata:
    """Metadata about a registered agent."""

    name: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "active"  # "active", "busy", "offline"
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now()

    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """Check if agent heartbeat is recent."""
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds


@dataclass
class AgentHandler:
    """Wrapper for agent's message handler."""

    agent_name: str
    handler: Callable  # async callable that takes RequestMessage
    supports_sync: bool = True
    supports_async: bool = True

    async def invoke(self, request: Any) -> Any:
        """Invoke the handler with a request."""
        if self.supports_async:
            return await self.handler(request)
        else:
            # Wrap sync handler in async
            import asyncio

            return await asyncio.to_thread(self.handler, request)


class AgentRegistry:
    """
    Central registry for agent discovery and lifecycle management.

    Features:
    - Dynamic agent registration and unregistration
    - Agent metadata and capability tracking
    - Health checking and status monitoring
    - Capability-based agent lookup
    """

    def __init__(self, health_check_timeout: int = 60):
        """Initialize agent registry.

        Args:
            health_check_timeout: Seconds before agent considered unhealthy
        """
        self._agents: Dict[str, AgentMetadata] = {}
        self._handlers: Dict[str, AgentHandler] = {}
        self._lock = threading.RLock()
        self._health_check_timeout = health_check_timeout
        self.logger = logging.getLogger("socrates.messaging.registry")

    def register(
        self,
        agent_name: str,
        handler: Callable,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        supports_sync: bool = True,
        supports_async: bool = True,
    ) -> None:
        """Register an agent with the registry.

        Args:
            agent_name: Unique agent identifier
            handler: Async callable that processes requests
            capabilities: List of agent capabilities
            metadata: Additional agent metadata
            supports_sync: Whether agent supports sync processing
            supports_async: Whether agent supports async processing
        """
        with self._lock:
            if agent_name in self._agents:
                self.logger.warning(f"Agent {agent_name} already registered, updating")

            agent_meta = AgentMetadata(
                name=agent_name,
                capabilities=capabilities or [],
                metadata=metadata or {},
            )

            handler_wrapper = AgentHandler(
                agent_name=agent_name,
                handler=handler,
                supports_sync=supports_sync,
                supports_async=supports_async,
            )

            self._agents[agent_name] = agent_meta
            self._handlers[agent_name] = handler_wrapper

            self.logger.info(
                f"Registered agent {agent_name} with capabilities: {agent_meta.capabilities}"
            )

    def unregister(self, agent_name: str) -> bool:
        """Unregister an agent from the registry.

        Args:
            agent_name: Agent to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        with self._lock:
            if agent_name not in self._agents:
                return False

            del self._agents[agent_name]
            del self._handlers[agent_name]

            self.logger.info(f"Unregistered agent {agent_name}")
            return True

    def get_agent(self, agent_name: str) -> Optional[AgentMetadata]:
        """Get agent metadata.

        Args:
            agent_name: Agent to retrieve

        Returns:
            AgentMetadata if found, None otherwise
        """
        with self._lock:
            return self._agents.get(agent_name)

    def get_handler(self, agent_name: str) -> Optional[AgentHandler]:
        """Get agent's message handler.

        Args:
            agent_name: Agent whose handler to retrieve

        Returns:
            AgentHandler if found, None otherwise
        """
        with self._lock:
            return self._handlers.get(agent_name)

    def list_agents(self, capability: Optional[str] = None) -> List[str]:
        """List all registered agents, optionally filtered by capability.

        Args:
            capability: Optional capability filter

        Returns:
            List of agent names
        """
        with self._lock:
            if capability is None:
                return list(self._agents.keys())

            return [
                name
                for name, meta in self._agents.items()
                if capability in meta.capabilities
            ]

    def is_available(
        self, agent_name: str, check_health: bool = True
    ) -> bool:
        """Check if agent is available for requests.

        Args:
            agent_name: Agent to check
            check_health: Whether to verify heartbeat is recent

        Returns:
            True if agent is available, False otherwise
        """
        with self._lock:
            agent = self._agents.get(agent_name)
            if not agent:
                return False

            if check_health:
                return agent.is_healthy(self._health_check_timeout)

            return agent.status == "active"

    def update_heartbeat(self, agent_name: str) -> bool:
        """Update agent's heartbeat timestamp.

        Args:
            agent_name: Agent whose heartbeat to update

        Returns:
            True if updated, False if agent not found
        """
        with self._lock:
            agent = self._agents.get(agent_name)
            if not agent:
                return False

            agent.update_heartbeat()
            return True

    def set_status(self, agent_name: str, status: str) -> bool:
        """Set agent status.

        Args:
            agent_name: Agent whose status to set
            status: New status ("active", "busy", "offline")

        Returns:
            True if updated, False if agent not found
        """
        with self._lock:
            agent = self._agents.get(agent_name)
            if not agent:
                return False

            agent.status = status
            return True

    def get_status(self, agent_name: str) -> Optional[str]:
        """Get agent's current status.

        Args:
            agent_name: Agent whose status to get

        Returns:
            Status string or None if agent not found
        """
        with self._lock:
            agent = self._agents.get(agent_name)
            return agent.status if agent else None

    def get_capabilities(self, agent_name: str) -> List[str]:
        """Get agent's capabilities.

        Args:
            agent_name: Agent whose capabilities to retrieve

        Returns:
            List of capability strings
        """
        with self._lock:
            agent = self._agents.get(agent_name)
            return agent.capabilities if agent else []

    def find_by_capability(self, capability: str) -> List[str]:
        """Find all agents with a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agent names with that capability
        """
        return self.list_agents(capability=capability)

    def count(self) -> int:
        """Get number of registered agents.

        Returns:
            Number of agents
        """
        with self._lock:
            return len(self._agents)

    def get_all_metadata(self) -> Dict[str, AgentMetadata]:
        """Get metadata for all registered agents.

        Returns:
            Dictionary of agent names to metadata
        """
        with self._lock:
            return dict(self._agents)

    def clear(self) -> None:
        """Clear all registered agents (for testing)."""
        with self._lock:
            self._agents.clear()
            self._handlers.clear()

            self.logger.warning("Agent registry cleared")
