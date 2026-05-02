"""Agent bus - message routing for agent-to-agent communication.

Replaces direct orchestrator.process_request() calls with event-driven
async messaging. Eliminates direct agent coupling and enables resilience patterns.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, List
from uuid import uuid4

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for resilient agent communication.

    Prevents cascading failures by stopping requests to failing agents.
    States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes in HALF_OPEN before closing
            timeout_seconds: Time before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger = logging.getLogger(__name__)

    def record_success(self) -> None:
        """Record successful request."""
        self.failure_count = 0

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.logger.info(f"Circuit breaker CLOSED after {self.success_count} successes")

    def record_failure(self) -> None:
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")

    def allow_request(self) -> bool:
        """Check if request should be allowed.

        Returns:
            True if request should proceed, False if circuit is open
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Try recovery after timeout
            if time.time() - self.last_failure_time >= self.timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.logger.info("Circuit breaker HALF_OPEN - testing recovery")
                return True
            return False

        # HALF_OPEN: allow test request
        return True

    def get_state(self) -> str:
        """Get current state as string."""
        return self.state.value


class RetryPolicy:
    """Retry policy with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 0.1,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
    ):
        """Initialize retry policy.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            backoff_factor: Exponential backoff multiplier
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds with exponential backoff
        """
        delay = min(
            self.initial_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )
        return delay


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
    Includes resilience patterns: circuit breaker and retry logic.
    """

    def __init__(
        self,
        event_emitter,
        registry=None,
        max_concurrent_requests: int = 100,
        default_timeout: float = 30.0,
        enable_circuit_breaker: bool = True,
        enable_retry: bool = True,
    ):
        """Initialize agent bus.

        Args:
            event_emitter: Event emitter for routing messages
            registry: Optional agent registry for discovery
            max_concurrent_requests: Max concurrent requests allowed
            default_timeout: Default timeout for requests in seconds
            enable_circuit_breaker: Enable circuit breaker pattern
            enable_retry: Enable retry with exponential backoff
        """
        self.event_emitter = event_emitter
        self.registry = registry
        self.max_concurrent_requests = max_concurrent_requests
        self.default_timeout = default_timeout
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_retry = enable_retry
        self.request_queue: Dict[str, asyncio.Future] = {}
        self.response_listeners: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

        # Circuit breakers per agent
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Retry policies
        self.retry_policy = RetryPolicy(
            max_retries=3,
            initial_delay=0.1,
            max_delay=5.0,
            backoff_factor=2.0,
        )

        # Set up event routing for agent requests
        self._setup_event_routing()

    def _get_circuit_breaker(self, agent_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for agent.

        Args:
            agent_name: Agent name

        Returns:
            CircuitBreaker instance
        """
        if agent_name not in self.circuit_breakers:
            self.circuit_breakers[agent_name] = CircuitBreaker()
        return self.circuit_breakers[agent_name]

    def _setup_event_routing(self) -> None:
        """Set up event routing for agent requests.

        Creates a wrapper around event_emitter.emit() to intercept and route
        agent request events to registered handlers. This ensures that when
        send_request() emits an "agent.{name}.request" event, the handler is
        invoked and the response is returned to the caller via handle_response().
        """
        # Store the original emit method
        self._original_emit = self.event_emitter.emit

        # Create a wrapper that intercepts agent request events
        def wrapped_emit(event_type, data=None, skip_logging=False):
            """Wrapper around event_emitter.emit that routes agent requests."""
            # Convert event_type to string for pattern matching
            from socratic_system.events import EventType

            event_name = (
                event_type.value if isinstance(event_type, EventType) else str(event_type)
            )

            # Check if this is an agent request event: "agent.{agent_name}.request"
            if event_name.startswith("agent.") and event_name.endswith(".request"):
                parts = event_name.split(".")
                if len(parts) == 3:
                    agent_name = parts[1]
                    # Schedule async handler without blocking emit
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self._handle_agent_request(agent_name, data)
                            )
                        else:
                            # Fallback: run synchronously if no event loop
                            asyncio.run(self._handle_agent_request(agent_name, data))
                    except RuntimeError:
                        # No event loop available, run synchronously
                        asyncio.run(self._handle_agent_request(agent_name, data))

            # Continue with normal event emission
            self._original_emit(event_type, data, skip_logging)

        # Replace the emit method with the wrapper
        self.event_emitter.emit = wrapped_emit

    async def _handle_agent_request(self, agent_name: str, request_data: Dict[str, Any]) -> None:
        """Handle an incoming agent request by invoking the registered handler.

        Routes the request to the appropriate agent handler via the registry,
        executes it, and returns the response to the requester via handle_response().

        Args:
            agent_name: Name of the target agent
            request_data: Request data containing request_id and payload
        """
        request_id = request_data.get("request_id")
        payload = request_data.get("payload", {})

        if not request_id:
            self.logger.error(f"[AgentBus] Request missing request_id")
            return

        try:
            # Look up the handler from the registry
            if not self.registry:
                self.logger.error(f"[AgentBus] No registry available for request routing")
                self.handle_response(
                    request_id,
                    {"status": "error", "message": "Agent bus registry not configured"},
                )
                return

            handler = self.registry.get_handler(agent_name)
            if not handler:
                self.logger.warning(
                    f"[AgentBus] No handler registered for agent '{agent_name}'"
                )
                self.handle_response(
                    request_id,
                    {
                        "status": "error",
                        "message": f"Agent '{agent_name}' not found or not registered",
                    },
                )
                return

            self.logger.debug(
                f"[AgentBus] Routing request to agent '{agent_name}' (id: {request_id})"
            )

            # Invoke the handler
            response = await handler.invoke(payload)

            # Ensure response has proper structure
            if not isinstance(response, dict):
                response = {"status": "success", "data": response}
            if "status" not in response:
                response["status"] = "success"

            self.logger.debug(
                f"[AgentBus] Agent '{agent_name}' returned response (id: {request_id})"
            )

            # Send response back to the requester
            self.handle_response(request_id, response)

        except Exception as e:
            self.logger.error(
                f"[AgentBus] Error handling request for agent '{agent_name}': {e}"
            )
            self.handle_response(
                request_id,
                {"status": "error", "message": f"Agent processing error: {str(e)}"},
            )

    async def send_request(
        self,
        target_agent: str,
        request: Dict[str, Any],
        timeout: Optional[float] = None,
        fire_and_forget: bool = False,
    ) -> Dict[str, Any]:
        """Send request to another agent with resilience patterns.

        Replaces orchestrator.process_request() calls.
        Includes circuit breaker and retry logic for resilience.

        Args:
            target_agent: Name of target agent
            request: Request data dict
            timeout: Timeout in seconds (uses default_timeout if not specified)
            fire_and_forget: If True, don't wait for response

        Returns:
            Response dict from agent

        Raises:
            AgentTimeoutError: If request times out
            AgentError: If agent encounters an error
        """
        # Use default timeout if not specified
        if timeout is None:
            timeout = self.default_timeout

        # Check circuit breaker
        if self.enable_circuit_breaker:
            breaker = self._get_circuit_breaker(target_agent)
            if not breaker.allow_request():
                self.logger.error(
                    f"[AgentBus] Circuit breaker OPEN for {target_agent} - rejecting request"
                )
                raise AgentError(
                    f"Agent {target_agent} is unavailable (circuit breaker open)"
                )

        # Fire-and-forget doesn't use retry
        if fire_and_forget:
            request_id = str(uuid4())
            self.event_emitter.emit(
                f"agent.{target_agent}.request",
                {
                    "request_id": request_id,
                    "payload": request,
                },
            )
            return {"request_id": request_id, "status": "queued"}

        # Request-response with retry
        last_error = None
        retry_count = 0
        max_retries = self.retry_policy.max_retries if self.enable_retry else 0

        while retry_count <= max_retries:
            request_id = str(uuid4())

            try:
                self.logger.debug(
                    f"[AgentBus] Sending request to {target_agent} (attempt {retry_count + 1})"
                )

                # Request-response pattern
                future = asyncio.Future()
                self.request_queue[request_id] = future

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

                # Record success in circuit breaker
                if self.enable_circuit_breaker:
                    self._get_circuit_breaker(target_agent).record_success()

                return response

            except asyncio.TimeoutError as e:
                last_error = e
                self.logger.warning(
                    f"[AgentBus] Request to {target_agent} timed out after {timeout}s "
                    f"(attempt {retry_count + 1}/{max_retries + 1})"
                )

                # Record failure in circuit breaker
                if self.enable_circuit_breaker:
                    self._get_circuit_breaker(target_agent).record_failure()

                # Retry with exponential backoff
                if retry_count < max_retries and self.enable_retry:
                    delay = self.retry_policy.get_delay(retry_count)
                    self.logger.info(
                        f"[AgentBus] Retrying in {delay:.2f}s (attempt {retry_count + 2})"
                    )
                    await asyncio.sleep(delay)
                    retry_count += 1
                else:
                    break

            except Exception as e:
                last_error = e
                self.logger.error(f"[AgentBus] Error in request to {target_agent}: {e}")

                # Record failure in circuit breaker
                if self.enable_circuit_breaker:
                    self._get_circuit_breaker(target_agent).record_failure()

                # Don't retry on non-timeout errors
                break

            finally:
                # Clean up
                if request_id in self.request_queue:
                    del self.request_queue[request_id]

        # All retries exhausted
        if isinstance(last_error, asyncio.TimeoutError):
            raise AgentTimeoutError(
                f"{target_agent} timed out after {max_retries + 1} attempts"
            )
        else:
            raise AgentError(f"Agent {target_agent} request failed: {last_error}")

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

    def send_request_sync(
        self,
        target_agent: str,
        request: Dict[str, Any],
        timeout: Optional[float] = None,
        fire_and_forget: bool = False,
        orchestrator=None,
    ) -> Dict[str, Any]:
        """Send request to another agent synchronously.

        Routes through orchestrator if available (backward compatible),
        otherwise tries async path via asyncio.run().

        Args:
            target_agent: Name of target agent
            request: Request data dict
            timeout: Timeout in seconds (uses default_timeout if not specified)
            fire_and_forget: If True, don't wait for response
            orchestrator: Optional orchestrator to use for routing

        Returns:
            Response dict from agent

        Raises:
            AgentTimeoutError: If request times out
            AgentError: If agent encounters an error
        """
        # If orchestrator is available, use it for backward compatibility
        if orchestrator is not None:
            self.logger.debug(
                f"[AgentBus] Routing {target_agent} request through orchestrator"
            )
            return orchestrator.process_request(target_agent, request)

        # Try to run async send_request
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create one
            return asyncio.run(
                self.send_request(
                    target_agent,
                    request,
                    timeout=timeout,
                    fire_and_forget=fire_and_forget,
                )
            )
        else:
            # Already in async context, shouldn't call sync version
            raise RuntimeError(
                "send_request_sync() called from async context. Use send_request() instead."
            )

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
