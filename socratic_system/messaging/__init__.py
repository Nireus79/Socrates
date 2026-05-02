"""Messaging layer for agent communication.

Provides event-driven agent-to-agent messaging without direct coupling.
Includes resilience patterns: circuit breaker and retry logic.
"""

from .agent_bus import (
    AgentBus,
    AgentError,
    AgentTimeoutError,
    CircuitBreaker,
    CircuitBreakerState,
    RetryPolicy,
)

__all__ = [
    "AgentBus",
    "AgentError",
    "AgentTimeoutError",
    "CircuitBreaker",
    "CircuitBreakerState",
    "RetryPolicy",
]
