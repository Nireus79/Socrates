"""
Messaging module for agent-to-agent communication.

Phase 2: Agent Bus Implementation

Provides:
- AgentBus for message routing and agent communication
- Message types and serialization
- Request-response patterns with timeouts
- Fire-and-forget messaging
- Circuit breaker for resilience
- Retry logic with exponential backoff
- Bulkhead isolation for concurrent limits
- Integration with existing orchestrator

Components:
- agent_bus: Core message routing and agent communication
- messages: Message types and formats
- exceptions: Messaging-specific exceptions
- middleware: Integration layers for services and agents
- resilience: Retry, circuit breaker, bulkhead patterns
- integration: Orchestrator compatibility and migration support
"""

from socratic_system.messaging.agent_bus import AgentBus, CircuitBreaker
from socratic_system.messaging.messages import (
    AgentMessage,
    RequestMessage,
    ResponseMessage,
    ErrorMessage,
    MessageType,
    MessageStatus,
)
from socratic_system.messaging.exceptions import (
    AgentTimeoutError,
    AgentError,
    AgentNotFoundError,
    CircuitBreakerOpenError,
    MessagingError,
    InvalidMessageError,
)
from socratic_system.messaging.middleware import (
    AgentBusMiddleware,
    ServiceAgentAdapter,
)
from socratic_system.messaging.resilience import (
    RetryPolicy,
    Fallback,
    BulkheadPolicy,
    TimeoutPolicy,
    ResilientAgentCaller,
)
from socratic_system.messaging.integration import (
    OrchestratorAgentBusAdapter,
    MigrationGuide,
)

__all__ = [
    # Core Agent Bus
    "AgentBus",
    "CircuitBreaker",
    # Messages
    "AgentMessage",
    "RequestMessage",
    "ResponseMessage",
    "ErrorMessage",
    "MessageType",
    "MessageStatus",
    # Exceptions
    "AgentTimeoutError",
    "AgentError",
    "AgentNotFoundError",
    "CircuitBreakerOpenError",
    "MessagingError",
    "InvalidMessageError",
    # Middleware
    "AgentBusMiddleware",
    "ServiceAgentAdapter",
    # Resilience
    "RetryPolicy",
    "Fallback",
    "BulkheadPolicy",
    "TimeoutPolicy",
    "ResilientAgentCaller",
    # Integration
    "OrchestratorAgentBusAdapter",
    "MigrationGuide",
]
