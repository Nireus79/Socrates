"""
Circuit Breaker Pattern for Agent Calls

CRITICAL FIX #12: Prevents cascade failures by tracking agent call failures and
temporarily disabling failing agents. Uses the Circuit Breaker pattern with
CLOSED/OPEN/HALF_OPEN states.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker for agent calls.

    Tracks failures and opens circuit after threshold is exceeded.
    After timeout, enters half-open state to test recovery.

    States:
    - CLOSED: Normal operation, calls are passed through
    - OPEN: Failure threshold exceeded, calls are rejected immediately
    - HALF_OPEN: Testing recovery after timeout, limited calls allowed
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the circuit breaker (e.g., 'socratic_counselor')
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before trying half-open
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_calls = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if circuit should transition from open to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker {self.name}: Transitioning to HALF_OPEN"
                )
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                time_until_reset = (
                    self.opened_at + timedelta(seconds=self.timeout_seconds) - datetime.now()
                ).total_seconds()
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Retry in {time_until_reset:.0f}s"
                )

        # Limit calls in half-open state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise Exception(
                    f"Circuit breaker {self.name} is HALF_OPEN and at max test calls"
                )
            self.half_open_calls += 1

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Record successful call"""
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            logger.info(
                f"Circuit breaker {self.name}: Successful call in HALF_OPEN "
                f"({self.success_count}/{self.half_open_max_calls})"
            )
            if self.success_count >= self.half_open_max_calls:
                logger.info(
                    f"Circuit breaker {self.name}: Transitioning to CLOSED (recovered)"
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0

    def _on_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker {self.name}: Failed in HALF_OPEN, reopening circuit"
            )
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker {self.name}: Failure threshold exceeded "
                f"({self.failure_count}/{self.failure_threshold}), opening circuit"
            )
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.opened_at:
            return True

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.timeout_seconds

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }


class CircuitBreakerRegistry:
    """Global registry of circuit breakers"""

    _breakers: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_breaker(cls, name: str, **kwargs) -> CircuitBreaker:
        """Get or create circuit breaker by name"""
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name, **kwargs)
        return cls._breakers[name]

    @classmethod
    def get_all_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in cls._breakers.items()}

    @classmethod
    def reset_breaker(cls, name: str) -> bool:
        """Manually reset a circuit breaker"""
        if name in cls._breakers:
            cls._breakers[name].state = CircuitState.CLOSED
            cls._breakers[name].failure_count = 0
            cls._breakers[name].success_count = 0
            logger.info(f"Circuit breaker {name} manually reset")
            return True
        return False
