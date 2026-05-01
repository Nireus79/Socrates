"""Agent bus - message routing for agent-to-agent communication.

Replaces direct orchestrator.process_request() calls with event-driven
async messaging. Eliminates direct agent coupling and enables resilience patterns.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, List
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentTimeoutError(Exception):
    """Raised when agent request times out."""

    pass


class AgentError(Exception):
    """Raised when agent encounters an error."""

    pass


class AgentBus:
    """Message bus for agent-to-agent communication.

    Provides request-response and fire-and-forget patterns for agents
    to communicate without direct coupling through orchestrator.
    """

    def __init__(self, event_emitter):
        """Initialize agent bus.

        Args:
            event_emitter: Event emitter for routing messages
        """
        self.event_emitter = event_emitter
        self.request_queue: Dict[str, asyncio.Future] = {}
        self.response_listeners: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

    async def send_request(
        self,
        target_agent: str,
        request: Dict[str, Any],
        timeout: float = 30.0,
        fire_and_forget: bool = False,
    ) -> Dict[str, Any]:
        """Send request to another agent.

        Replaces orchestrator.process_request() calls.

        Args:
            target_agent: Name of target agent
            request: Request data dict
            timeout: Timeout in seconds
            fire_and_forget: If True, don't wait for response

        Returns:
            Response dict from agent

        Raises:
            AgentTimeoutError: If request times out
            AgentError: If agent encounters an error
        """
        request_id = str(uuid4())

        self.logger.debug(
            f"[AgentBus] Sending request to {target_agent} (id: {request_id})"
        )

        if fire_and_forget:
            # Fire and forget - emit event, don't wait
            self.event_emitter.emit(
                f"agent.{target_agent}.request",
                {
                    "request_id": request_id,
                    "payload": request,
                },
            )
            return {"request_id": request_id, "status": "queued"}

        # Request-response pattern
        future = asyncio.Future()
        self.request_queue[request_id] = future

        try:
            self.event_emitter.emit(
                f"agent.{target_agent}.request",
                {
                    "request_id": request_id,
                    "payload": request,
                    "reply_to": "agent_bus",
                },
            )

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            self.logger.debug(f"[AgentBus] Received response for {request_id}")
            return response

        except asyncio.TimeoutError:
            self.logger.error(
                f"[AgentBus] Request to {target_agent} timed out after {timeout}s"
            )
            raise AgentTimeoutError(
                f"{target_agent} timed out after {timeout}s (request_id: {request_id})"
            )

        finally:
            # Clean up
            if request_id in self.request_queue:
                del self.request_queue[request_id]

    def handle_response(self, request_id: str, response: Dict[str, Any]) -> None:
        """Handle response from agent.

        Called by agents to send responses back.

        Args:
            request_id: Request identifier
            response: Response data
        """
        if request_id not in self.request_queue:
            self.logger.warning(f"[AgentBus] Unknown request_id: {request_id}")
            return

        future = self.request_queue[request_id]
        if not future.done():
            future.set_result(response)
            self.logger.debug(f"[AgentBus] Response queued for {request_id}")

    def register_handler(
        self, agent_name: str, handler_func: Callable
    ) -> None:
        """Register handler for agent responses.

        Args:
            agent_name: Agent name
            handler_func: Handler function
        """
        event_name = f"agent.{agent_name}.response"
        self.event_emitter.on(event_name, handler_func)
        self.logger.debug(f"[AgentBus] Handler registered for {agent_name}")

    def emit_event(
        self, agent_name: str, event_type: str, data: Dict[str, Any]
    ) -> None:
        """Emit event from agent.

        Args:
            agent_name: Agent name
            event_type: Event type
            data: Event data
        """
        event_name = f"agent.{agent_name}.{event_type}"
        self.event_emitter.emit(event_name, data)

    def get_stats(self) -> Dict[str, Any]:
        """Get agent bus statistics.

        Returns:
            Statistics dict
        """
        return {
            "pending_requests": len(self.request_queue),
            "registered_handlers": sum(
                len(handlers) for handlers in self.response_listeners.values()
            ),
        }
