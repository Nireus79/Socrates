"""
Exceptions for agent messaging system.
"""


class MessagingError(Exception):
    """Base exception for messaging errors"""

    pass


class AgentError(MessagingError):
    """Base exception for agent-related errors"""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent request times out"""

    def __init__(self, agent_name: str, timeout: float):
        self.agent_name = agent_name
        self.timeout = timeout
        super().__init__(f"Agent '{agent_name}' timed out after {timeout}s")


class AgentNotFoundError(AgentError):
    """Raised when agent is not registered"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}' not found")


class CircuitBreakerOpenError(AgentError):
    """Raised when circuit breaker is open"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__(f"Circuit breaker open for agent '{agent_name}'")


class InvalidMessageError(MessagingError):
    """Raised when message format is invalid"""

    pass
