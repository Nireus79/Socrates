"""
Agent Bus - Message router for agent-to-agent communication.

Enables decoupled communication between agents without direct references.
Replaces orchestrator.process_request() calls with async messaging.

Features:
- Request-response pattern with timeouts
- Fire-and-forget messaging
- Circuit breaker for resilience
- Message persistence
- Response caching
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from socratic_system.events import EventEmitter

if TYPE_CHECKING:
    from socratic_system.messaging.agent_registry import AgentRegistry
from socratic_system.messaging.exceptions import (
    AgentTimeoutError,
    AgentNotFoundError,
    CircuitBreakerOpenError,
)
from socratic_system.messaging.messages import (
    RequestMessage,
    ResponseMessage,
    ErrorMessage,
    MessageStatus,
)


class CircuitBreaker:
    """Circuit breaker for agent request resilience"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            success_threshold: Number of successes to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open

    def record_success(self) -> None:
        """Record successful request"""
        self.failure_count = 0

        if self.state == "half-open":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "closed"
                self.success_count = 0

    def record_failure(self) -> None:
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def can_attempt(self) -> bool:
        """Check if request can be attempted"""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Try recovery after timeout
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                self.success_count = 0
                return True
            return False

        # Half-open state
        return True

    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == "open"


class AgentBus:
    """
    Message bus for agent-to-agent communication.

    Replaces direct orchestrator.process_request() calls with decoupled
    messaging. Supports both synchronous and asynchronous patterns.
    """

    def __init__(
        self,
        event_emitter: EventEmitter,
        registry: Optional["AgentRegistry"] = None,
        max_concurrent_requests: int = 100,
        default_timeout: float = 30.0,
    ):
        """
        Initialize agent bus.

        Args:
            event_emitter: EventEmitter for decoupled communication
            registry: AgentRegistry for agent discovery (Phase 2)
            max_concurrent_requests: Maximum concurrent request limit
            default_timeout: Default timeout for requests
        """
        self.event_emitter = event_emitter
        self.registry = registry  # Phase 2: Agent registry for discovery
        self.max_concurrent_requests = max_concurrent_requests
        self.default_timeout = default_timeout

        self.logger = logging.getLogger(__name__)

        # Request tracking
        self.request_queue: Dict[str, asyncio.Future] = {}
        self.request_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Message history for debugging
        self.message_history: List[Dict[str, Any]] = []
        self.max_history: int = 1000

        # Response cache
        self.response_cache: Dict[str, ResponseMessage] = {}
        self.cache_enabled = False

        # Metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "fire_and_forget": 0,
            "direct_handler_invocations": 0,  # Phase 2: Direct calls via registry
        }

    async def send_request(
        self,
        target_agent: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        fire_and_forget: bool = False,
    ) -> Dict[str, Any]:
        """
        Send request to another agent.

        Args:
            target_agent: Name of target agent
            action: Action to perform
            payload: Request payload
            timeout: Request timeout (uses default if None)
            fire_and_forget: If True, don't wait for response

        Returns:
            Response payload from agent

        Raises:
            AgentTimeoutError: If request times out
            AgentNotFoundError: If agent not found
            CircuitBreakerOpenError: If circuit breaker is open
        """
        if timeout is None:
            timeout = self.default_timeout

        # Phase 2: Check registry for direct handler invocation (faster than events)
        if self.registry and self.registry.is_available(target_agent):
            handler = self.registry.get_handler(target_agent)
            if handler and not fire_and_forget:
                try:
                    # Create request and invoke handler directly
                    request = RequestMessage(
                        sender="bus",
                        target_agent=target_agent,
                        action=action,
                        payload=payload or {},
                        timeout=timeout,
                    )

                    self._store_message_history(request.to_dict())
                    self.metrics["direct_handler_invocations"] += 1

                    # Invoke handler with timeout
                    try:
                        response = await asyncio.wait_for(
                            handler.invoke(request),
                            timeout=timeout
                        )
                        self.metrics["successful_requests"] += 1
                        self._get_circuit_breaker(target_agent).record_success()
                        return response
                    except asyncio.TimeoutError:
                        self._get_circuit_breaker(target_agent).record_failure()
                        self.metrics["timeout_requests"] += 1
                        raise AgentTimeoutError(target_agent, timeout)

                except Exception as e:
                    # Fallback to event-based routing
                    self.logger.debug(
                        f"Direct invocation failed for {target_agent}, "
                        f"falling back to events: {e}"
                    )

        # Check circuit breaker
        breaker = self._get_circuit_breaker(target_agent)
        if not breaker.can_attempt():
            if breaker.is_open():
                raise CircuitBreakerOpenError(target_agent)

        # Update metrics
        self.metrics["total_requests"] += 1

        # Create request message
        request = RequestMessage(
            sender="bus",
            target_agent=target_agent,
            action=action,
            payload=payload or {},
            timeout=timeout,
            fire_and_forget=fire_and_forget,
        )

        # Store in history
        self._store_message_history(request.to_dict())

        try:
            if fire_and_forget:
                # Emit without waiting for response
                self.event_emitter.emit(f"agent.{target_agent}.request", request.to_dict())
                self.metrics["fire_and_forget"] += 1
                return {"request_id": request.message_id, "status": "accepted"}

            # Request-response pattern
            future = asyncio.Future()
            self.request_queue[request.message_id] = future

            # Emit request event
            self.event_emitter.emit(f"agent.{target_agent}.request", request.to_dict())

            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(future, timeout=timeout)
                breaker.record_success()
                self.metrics["successful_requests"] += 1
                return response

            except asyncio.TimeoutError:
                breaker.record_failure()
                self.metrics["timeout_requests"] += 1
                raise AgentTimeoutError(target_agent, timeout)

        except AgentTimeoutError:
            raise
        except CircuitBreakerOpenError:
            raise
        except Exception as e:
            breaker.record_failure()
            self.metrics["failed_requests"] += 1
            self.logger.error(f"Request to {target_agent} failed: {e}")
            raise
        finally:
            # Clean up request queue
            self.request_queue.pop(request.message_id, None)

    def register_handler(
        self,
        agent_name: str,
        handler: Callable,
    ) -> None:
        """
        Register handler for agent requests.

        Args:
            agent_name: Name of agent handling requests
            handler: Async callable that handles requests
        """
        self.request_handlers[agent_name].append(handler)
        self.logger.debug(f"Registered handler for agent '{agent_name}'")

    def unregister_handler(self, agent_name: str, handler: Callable) -> None:
        """
        Unregister handler for agent.

        Args:
            agent_name: Name of agent
            handler: Handler to remove
        """
        if agent_name in self.request_handlers:
            self.request_handlers[agent_name].remove(handler)

    async def handle_response(
        self,
        request_id: str,
        response: Dict[str, Any],
    ) -> None:
        """
        Handle response from agent.

        Args:
            request_id: ID of original request
            response: Response payload
        """
        if request_id in self.request_queue:
            future = self.request_queue[request_id]
            if not future.done():
                future.set_result(response)

        # Store in history
        self._store_message_history({"type": "response", "request_id": request_id})

    async def handle_error(
        self,
        request_id: str,
        error: str,
        agent_name: str = "",
    ) -> None:
        """
        Handle error response from agent.

        Args:
            request_id: ID of original request
            error: Error message
            agent_name: Name of agent that errored
        """
        if request_id in self.request_queue:
            future = self.request_queue[request_id]
            if not future.done():
                future.set_exception(Exception(error))

        # Record failure for circuit breaker
        if agent_name:
            breaker = self._get_circuit_breaker(agent_name)
            breaker.record_failure()

    async def broadcast(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        capability_filter: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Broadcast message to multiple agents (Phase 2).

        Sends same action to all agents, optionally filtered by capability.
        Uses fire-and-forget pattern for efficiency.

        Args:
            action: Action to broadcast
            payload: Message payload
            capability_filter: Optional capability to filter agents
            timeout: Request timeout (uses default if None)

        Returns:
            Dictionary with broadcast results

        Example:
            >>> result = await bus.broadcast(
            ...     action="refresh_cache",
            ...     capability_filter="cache_aware"
            ... )
            >>> print(result["agents_notified"])  # List of agents that received message
        """
        if not self.registry:
            self.logger.warning("Broadcast called but registry not available")
            return {"status": "error", "message": "Registry not available"}

        # Find target agents
        agents = self.registry.find_by_capability(
            capability_filter
        ) if capability_filter else self.registry.list_agents()

        if not agents:
            return {
                "status": "success",
                "agents_notified": [],
                "message": "No matching agents found"
            }

        # Send to all agents (fire-and-forget)
        tasks = []
        for agent_name in agents:
            task = self.send_request(
                target_agent=agent_name,
                action=action,
                payload=payload,
                timeout=timeout,
                fire_and_forget=True
            )
            tasks.append(task)

        # Wait for all broadcasts
        await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "status": "success",
            "agents_notified": agents,
            "count": len(agents)
        }

    def enable_caching(self) -> None:
        """Enable response caching"""
        self.cache_enabled = True
        self.logger.info("Response caching enabled")

    def disable_caching(self) -> None:
        """Disable response caching"""
        self.cache_enabled = False

    def clear_cache(self) -> None:
        """Clear response cache"""
        self.response_cache.clear()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get bus metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            **self.metrics,
            "active_requests": len(self.request_queue),
            "cached_responses": len(self.response_cache),
            "circuit_breakers": {
                agent: {
                    "state": cb.state,
                    "failures": cb.failure_count,
                    "successes": cb.success_count,
                }
                for agent, cb in self.circuit_breakers.items()
            },
        }

    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent message history.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self.message_history[-limit:]

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "fire_and_forget": 0,
        }

    # Private methods

    def _get_circuit_breaker(self, agent_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for agent"""
        if agent_name not in self.circuit_breakers:
            self.circuit_breakers[agent_name] = CircuitBreaker()
        return self.circuit_breakers[agent_name]

    def _store_message_history(self, message: Dict[str, Any]) -> None:
        """Store message in history"""
        if len(self.message_history) >= self.max_history:
            self.message_history.pop(0)
        self.message_history.append(message)
