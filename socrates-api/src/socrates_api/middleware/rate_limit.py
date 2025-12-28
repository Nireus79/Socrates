"""
Rate Limiting Middleware - Protect API from abuse with slowapi.

Provides:
- Per-endpoint rate limiting
- Per-user rate limiting (authenticated endpoints)
- Per-IP rate limiting (unauthenticated endpoints)
- Redis backend for distributed rate limiting
- Graceful degradation if Redis unavailable
"""

import logging
from typing import Callable, Optional
import redis

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("slowapi not available - rate limiting disabled")

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limiting configuration."""

    # Default limits for endpoints
    DEFAULT_LIMIT = "100/minute"
    DEFAULT_HOURLY_LIMIT = "1000/hour"

    # Sensitive endpoint limits (login, registration, etc.)
    AUTH_LIMIT = "5/minute"
    AUTH_HOURLY_LIMIT = "50/hour"

    # Chat/LLM endpoint limits
    CHAT_LIMIT = "30/minute"
    CHAT_HOURLY_LIMIT = "500/hour"

    # Presession (free tier) limits
    PRESESSION_LIMIT = "20/minute"
    PRESESSION_HOURLY_LIMIT = "200/hour"

    # Professional tier limits
    PRO_CHAT_LIMIT = "100/minute"
    PRO_CHAT_HOURLY_LIMIT = "2000/hour"

    # Enterprise tier limits
    ENTERPRISE_CHAT_LIMIT = "500/minute"
    ENTERPRISE_CHAT_HOURLY_LIMIT = "10000/hour"

    # Health check endpoints (no limit)
    HEALTH_LIMIT = None


def get_limiter(redis_url: Optional[str] = None) -> Optional[Limiter]:
    """
    Initialize rate limiter with optional Redis backend.

    Args:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379")

    Returns:
        Configured Limiter instance or None if slowapi not available
    """
    if not SLOWAPI_AVAILABLE:
        logger.warning("slowapi not available - rate limiting disabled")
        return None

    try:
        # Try to use Redis backend for distributed rate limiting
        if redis_url:
            try:
                # Test connection
                r = redis.from_url(redis_url)
                r.ping()

                limiter = Limiter(
                    key_func=get_remote_address,
                    storage_uri=redis_url,
                    default_limits=[
                        RateLimitConfig.DEFAULT_LIMIT,
                        RateLimitConfig.DEFAULT_HOURLY_LIMIT,
                    ],
                )
                logger.info(f"Rate limiter initialized with Redis backend: {redis_url}")
                return limiter

            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis ({redis_url}), "
                    f"falling back to in-memory rate limiting: {e}"
                )

        # Fallback to in-memory rate limiting
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[
                RateLimitConfig.DEFAULT_LIMIT,
                RateLimitConfig.DEFAULT_HOURLY_LIMIT,
            ],
        )
        logger.info("Rate limiter initialized with in-memory backend")
        return limiter

    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        return None


# Global limiter instance
_limiter: Optional[Limiter] = None


def initialize_limiter(redis_url: Optional[str] = None) -> Optional[Limiter]:
    """
    Initialize global rate limiter instance.

    Args:
        redis_url: Optional Redis URL for distributed rate limiting

    Returns:
        Initialized Limiter or None
    """
    global _limiter
    _limiter = get_limiter(redis_url)
    return _limiter


def get_rate_limiter() -> Optional[Limiter]:
    """Get the global rate limiter instance."""
    return _limiter


def rate_limit_key_func(request) -> str:
    """
    Custom key function for rate limiting.

    For authenticated endpoints, use user ID.
    For unauthenticated endpoints, use IP address.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key (user ID or IP address)
    """
    try:
        # Try to get user from request state (set by auth dependency)
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user}"
    except Exception:
        pass

    # Fall back to IP address
    return get_remote_address(request)
