"""
Resilience patterns for agent communication.

Provides:
- Retry logic with exponential backoff
- Fallback patterns
- Bulkhead isolation
- Timeout management
"""

import asyncio
import logging
import random
from typing import Any, Callable, Dict, Optional, TypeVar

from socratic_system.messaging.exceptions import AgentTimeoutError, AgentError

T = TypeVar("T")


class RetryPolicy:
    """Retry policy for failed requests"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry policy.

        Args:
            max_retries: Maximum number of retries
            base_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )

        if self.jitter:
            # Add jitter (±20%)
            jitter_factor = 1.0 + random.uniform(-0.2, 0.2)
            delay *= jitter_factor

        return delay

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        logger = logging.getLogger(__name__)
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (AgentTimeoutError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
            except AgentError as e:
                # Don't retry on agent-specific errors
                raise

        raise last_error


class Fallback:
    """Fallback pattern for failed operations"""

    def __init__(self):
        """Initialize fallback"""
        self.fallbacks: Dict[type, Callable] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, error_type: type, handler: Callable) -> None:
        """
        Register fallback handler.

        Args:
            error_type: Exception type to handle
            handler: Async handler function
        """
        self.fallbacks[error_type] = handler

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute with fallback.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback result
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Find matching fallback
            for error_type, handler in self.fallbacks.items():
                if isinstance(e, error_type):
                    self.logger.info(f"Using fallback for {error_type.__name__}")
                    return await handler(*args, **kwargs)

            # No fallback found, re-raise
            raise


class BulkheadPolicy:
    """Bulkhead isolation for concurrent requests"""

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize bulkhead.

        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute with bulkhead isolation.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        async with self.semaphore:
            return await func(*args, **kwargs)

    def get_available_slots(self) -> int:
        """Get available bulkhead slots"""
        return self.max_concurrent - (self.max_concurrent - self.semaphore._value)


class TimeoutPolicy:
    """Timeout management for requests"""

    def __init__(self, default_timeout: float = 30.0):
        """
        Initialize timeout policy.

        Args:
            default_timeout: Default timeout in seconds
        """
        self.default_timeout = default_timeout
        self.timeouts: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    def set_timeout(self, agent_name: str, timeout: float) -> None:
        """
        Set timeout for specific agent.

        Args:
            agent_name: Agent name
            timeout: Timeout in seconds
        """
        self.timeouts[agent_name] = timeout
        self.logger.debug(f"Set timeout for {agent_name} to {timeout}s")

    def get_timeout(self, agent_name: str) -> float:
        """
        Get timeout for agent.

        Args:
            agent_name: Agent name

        Returns:
            Timeout in seconds
        """
        return self.timeouts.get(agent_name, self.default_timeout)

    async def execute_with_timeout(
        self,
        agent_name: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with timeout.

        Args:
            agent_name: Name of agent
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        timeout = self.get_timeout(agent_name)

        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.error(f"Request to {agent_name} timed out after {timeout}s")
            raise AgentTimeoutError(agent_name, timeout)


class ResilientAgentCaller:
    """Combines multiple resilience patterns"""

    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        bulkhead: Optional[BulkheadPolicy] = None,
        timeout_policy: Optional[TimeoutPolicy] = None,
    ):
        """
        Initialize resilient caller.

        Args:
            retry_policy: Retry policy
            bulkhead: Bulkhead isolation
            timeout_policy: Timeout policy
        """
        self.retry_policy = retry_policy or RetryPolicy()
        self.bulkhead = bulkhead or BulkheadPolicy()
        self.timeout_policy = timeout_policy or TimeoutPolicy()
        self.fallbacks = Fallback()
        self.logger = logging.getLogger(__name__)

    async def call(
        self,
        agent_name: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Call with all resilience patterns.

        Args:
            agent_name: Name of agent
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        async def with_timeout():
            return await self.timeout_policy.execute_with_timeout(
                agent_name, func, *args, **kwargs
            )

        async def with_retry():
            return await self.retry_policy.execute_with_retry(with_timeout)

        async def with_bulkhead():
            return await self.bulkhead.execute(with_retry)

        return await self.fallbacks.execute(with_bulkhead)
