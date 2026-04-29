"""
Middleware for integrating AgentBus with services and agents.

Provides adapters for:
- Service-to-service communication
- Service-to-agent communication
- Agent-to-agent communication
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from socratic_system.messaging.agent_bus import AgentBus


class AgentBusMiddleware:
    """Middleware for agent bus integration"""

    def __init__(self, agent_bus: AgentBus):
        """
        Initialize middleware.

        Args:
            agent_bus: AgentBus instance
        """
        self.agent_bus = agent_bus
        self.logger = logging.getLogger(__name__)

    async def call_agent(
        self,
        agent_name: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Call another agent via the bus.

        Args:
            agent_name: Target agent name
            action: Action to perform
            payload: Request payload
            timeout: Request timeout

        Returns:
            Response from agent
        """
        return await self.agent_bus.send_request(
            target_agent=agent_name,
            action=action,
            payload=payload,
            timeout=timeout,
        )

    async def call_agent_fire_and_forget(
        self,
        agent_name: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Call agent without waiting for response.

        Args:
            agent_name: Target agent name
            action: Action to perform
            payload: Request payload

        Returns:
            Request ID for tracking
        """
        result = await self.agent_bus.send_request(
            target_agent=agent_name,
            action=action,
            payload=payload,
            fire_and_forget=True,
        )
        return result.get("request_id", "")

    async def call_parallel(
        self,
        calls: list[tuple[str, str, Dict[str, Any]]],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Call multiple agents in parallel.

        Args:
            calls: List of (agent_name, action, payload) tuples
            timeout: Timeout for all requests

        Returns:
            Dictionary mapping agent names to responses
        """
        tasks = [
            self.call_agent(agent, action, payload, timeout)
            for agent, action, payload in calls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            calls[i][0]: (results[i] if not isinstance(results[i], Exception) else None)
            for i in range(len(calls))
        }

    def register_agent(
        self,
        agent_name: str,
        handler: Callable,
    ) -> None:
        """
        Register agent handler.

        Args:
            agent_name: Name of agent
            handler: Async handler function
        """
        self.agent_bus.register_handler(agent_name, handler)

    def get_bus_status(self) -> Dict[str, Any]:
        """
        Get agent bus status.

        Returns:
            Bus metrics and state
        """
        return self.agent_bus.get_metrics()


class ServiceAgentAdapter:
    """Adapter for services to use agent bus"""

    def __init__(self, agent_bus: AgentBus, service_name: str):
        """
        Initialize adapter.

        Args:
            agent_bus: AgentBus instance
            service_name: Name of service
        """
        self.agent_bus = agent_bus
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)

    async def request(
        self,
        target_agent: str,
        action: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make request to agent from service.

        Args:
            target_agent: Target agent name
            action: Action to perform
            **kwargs: Additional parameters

        Returns:
            Response from agent
        """
        return await self.agent_bus.send_request(
            target_agent=target_agent,
            action=action,
            payload=kwargs,
        )

    async def request_multiple(
        self,
        requests: Dict[str, tuple[str, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Make multiple requests in parallel.

        Args:
            requests: Dict mapping request names to (agent, payload) tuples

        Returns:
            Dict mapping request names to responses
        """
        tasks = {}
        for name, (agent, payload) in requests.items():
            tasks[name] = self.agent_bus.send_request(
                target_agent=agent,
                action="process",
                payload=payload,
            )

        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                self.logger.error(f"Request {name} failed: {e}")
                results[name] = {"error": str(e)}

        return results

    def fire_and_forget(
        self,
        target_agent: str,
        action: str,
        **kwargs,
    ) -> str:
        """
        Send fire-and-forget message.

        Args:
            target_agent: Target agent name
            action: Action to perform
            **kwargs: Message payload

        Returns:
            Request ID
        """
        # Convert to synchronous call (event is emitted directly)
        result = asyncio.run(
            self.agent_bus.send_request(
                target_agent=target_agent,
                action=action,
                payload=kwargs,
                fire_and_forget=True,
            )
        )
        return result.get("request_id", "")
