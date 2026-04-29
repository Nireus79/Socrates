"""
Integration layer for Agent Bus with existing orchestrator.

Provides backward compatibility while enabling migration to agent bus.
"""

import logging
from typing import Any, Callable, Dict, Optional

from socratic_system.messaging.agent_bus import AgentBus
from socratic_system.messaging.middleware import AgentBusMiddleware, ServiceAgentAdapter
from socratic_system.messaging.resilience import ResilientAgentCaller


class OrchestratorAgentBusAdapter:
    """
    Adapter to integrate AgentBus with existing orchestrator.

    Allows gradual migration from orchestrator.process_request()
    to agent_bus.send_request().
    """

    def __init__(self, agent_bus: AgentBus):
        """
        Initialize adapter.

        Args:
            agent_bus: AgentBus instance
        """
        self.agent_bus = agent_bus
        self.middleware = AgentBusMiddleware(agent_bus)
        self.resilient_caller = ResilientAgentCaller()
        self.logger = logging.getLogger(__name__)

        # Legacy support
        self._legacy_handlers: Dict[str, Callable] = {}

    def register_legacy_handler(self, agent_name: str, handler: Callable) -> None:
        """
        Register legacy orchestrator-style handler.

        Args:
            agent_name: Agent name
            handler: Sync or async handler
        """
        self._legacy_handlers[agent_name] = handler
        self.logger.info(f"Registered legacy handler for {agent_name}")

    async def call_agent(
        self,
        agent_name: str,
        request: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Call agent using bus (replacing orchestrator.process_request).

        Args:
            agent_name: Target agent name
            request: Request payload
            timeout: Request timeout

        Returns:
            Response from agent
        """
        # Extract action if present
        action = request.pop("action", "process")

        try:
            # Try agent bus first
            return await self.agent_bus.send_request(
                target_agent=agent_name,
                action=action,
                payload=request,
                timeout=timeout,
            )
        except Exception as e:
            self.logger.warning(
                f"Agent bus failed for {agent_name}, falling back to legacy: {e}"
            )

            # Fallback to legacy handler if available
            if agent_name in self._legacy_handlers:
                handler = self._legacy_handlers[agent_name]
                request["action"] = action
                return handler(request)

            raise

    async def call_agent_resilient(
        self,
        agent_name: str,
        request: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Call agent with resilience patterns.

        Args:
            agent_name: Target agent name
            request: Request payload
            timeout: Request timeout

        Returns:
            Response from agent
        """
        async def call():
            return await self.call_agent(agent_name, request, timeout)

        return await self.resilient_caller.call(agent_name, call)

    def get_adapter_for_service(self, service_name: str) -> ServiceAgentAdapter:
        """
        Get service adapter for service-to-agent calls.

        Args:
            service_name: Name of service

        Returns:
            Service adapter
        """
        return ServiceAgentAdapter(self.agent_bus, service_name)

    def get_bus_stats(self) -> Dict[str, Any]:
        """
        Get agent bus statistics.

        Returns:
            Bus metrics
        """
        return self.agent_bus.get_metrics()

    def enable_tracing(self, enable: bool = True) -> None:
        """Enable message tracing for debugging"""
        if enable:
            self.logger.info("Agent bus tracing enabled")
            # Could implement detailed logging here
        else:
            self.logger.info("Agent bus tracing disabled")


class MigrationGuide:
    """
    Guide for migrating from orchestrator to agent bus.

    Shows patterns for gradual migration.
    """

    @staticmethod
    def legacy_pattern() -> str:
        """Show legacy orchestrator pattern"""
        return """
# Legacy pattern (orchestrator.process_request)
def process(self, request):
    quality = self.orchestrator.process_request(
        "quality_controller",
        {"project_id": project_id}
    )
    return quality
"""

    @staticmethod
    def new_pattern() -> str:
        """Show new agent bus pattern"""
        return """
# New pattern (agent bus)
async def process(self, request):
    quality = await self.agent_bus.send_request(
        target_agent="quality_controller",
        action="evaluate",
        payload={"project_id": project_id}
    )
    return quality
"""

    @staticmethod
    def migration_steps() -> list[str]:
        """Provide step-by-step migration guide"""
        return [
            "1. Create AgentBus instance",
            "2. Register agents with agent bus",
            "3. Update orchestrator to use agent bus internally",
            "4. Migrate agents one-by-one to use agent bus",
            "5. Add resilience patterns (retry, circuit breaker)",
            "6. Remove direct orchestrator references from agents",
        ]
