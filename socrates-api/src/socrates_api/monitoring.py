"""
Monitoring and metrics collection for Socrates API.

Provides:
- Request/response metrics (latency, status codes)
- Database query performance tracking
- Error tracking and categorization
- User activity metrics
- Subscription usage tracking
"""

import logging
import time
from typing import Dict, Optional
from functools import wraps

from fastapi import Request, Response

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects API metrics for monitoring and observability."""

    # In-memory metrics storage (for development/small scale)
    # For production, integrate with Prometheus, DataDog, New Relic, etc.
    _metrics = {
        "requests": {},  # endpoint -> count
        "latencies": {},  # endpoint -> list of latencies (ms)
        "errors": {},  # error_type -> count
        "db_queries": {},  # query_type -> list of latencies
        "users": {},  # user_id -> activity_data
        "subscriptions": {},  # tier -> usage_data
    }

    @classmethod
    def record_request(
        cls,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Record HTTP request metrics."""
        endpoint = f"{method} {path}"

        # Track request count
        if endpoint not in cls._metrics["requests"]:
            cls._metrics["requests"][endpoint] = 0
        cls._metrics["requests"][endpoint] += 1

        # Track latency
        if endpoint not in cls._metrics["latencies"]:
            cls._metrics["latencies"][endpoint] = []
        cls._metrics["latencies"][endpoint].append(latency_ms)

        # Track user activity
        if user_id:
            if user_id not in cls._metrics["users"]:
                cls._metrics["users"][user_id] = {"requests": 0, "last_active": None}
            cls._metrics["users"][user_id]["requests"] += 1
            cls._metrics["users"][user_id]["last_active"] = time.time()

        # Log slow requests
        if latency_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow request: {method} {path} took {latency_ms:.2f}ms (status: {status_code})"
            )

    @classmethod
    def record_error(cls, error_type: str, error_message: str) -> None:
        """Record error metrics."""
        if error_type not in cls._metrics["errors"]:
            cls._metrics["errors"][error_type] = 0
        cls._metrics["errors"][error_type] += 1

        logger.error(f"Error recorded: {error_type} - {error_message}")

    @classmethod
    def record_db_query(cls, query_type: str, latency_ms: float) -> None:
        """Record database query metrics."""
        if query_type not in cls._metrics["db_queries"]:
            cls._metrics["db_queries"][query_type] = []
        cls._metrics["db_queries"][query_type].append(latency_ms)

        # Log slow queries
        if latency_ms > 500:  # > 500ms
            logger.warning(f"Slow database query: {query_type} took {latency_ms:.2f}ms")

    @classmethod
    def record_subscription_usage(
        cls, tier: str, feature: str, usage_amount: int = 1
    ) -> None:
        """Record subscription usage metrics."""
        if tier not in cls._metrics["subscriptions"]:
            cls._metrics["subscriptions"][tier] = {}
        if feature not in cls._metrics["subscriptions"][tier]:
            cls._metrics["subscriptions"][tier][feature] = 0
        cls._metrics["subscriptions"][tier][feature] += usage_amount

    @classmethod
    def get_metrics(cls) -> Dict:
        """Get all collected metrics."""
        return {
            "requests": cls._metrics["requests"],
            "latencies": {
                k: {
                    "count": len(v),
                    "avg_ms": sum(v) / len(v) if v else 0,
                    "min_ms": min(v) if v else 0,
                    "max_ms": max(v) if v else 0,
                }
                for k, v in cls._metrics["latencies"].items()
            },
            "errors": cls._metrics["errors"],
            "db_queries": {
                k: {
                    "count": len(v),
                    "avg_ms": sum(v) / len(v) if v else 0,
                    "min_ms": min(v) if v else 0,
                    "max_ms": max(v) if v else 0,
                }
                for k, v in cls._metrics["db_queries"].items()
            },
            "active_users": len(cls._metrics["users"]),
            "subscription_usage": cls._metrics["subscriptions"],
        }

    @classmethod
    def reset_metrics(cls) -> None:
        """Reset all metrics (for testing)."""
        cls._metrics = {
            "requests": {},
            "latencies": {},
            "errors": {},
            "db_queries": {},
            "users": {},
            "subscriptions": {},
        }


async def metrics_middleware(request: Request, call_next) -> Response:
    """FastAPI middleware for collecting request metrics."""
    start_time = time.time()

    try:
        response = await call_next(request)
        latency_ms = (time.time() - start_time) * 1000

        # Get user ID if available
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        # Record metrics
        MetricsCollector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
            user_id=user_id,
        )

        return response

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        MetricsCollector.record_error(type(e).__name__, str(e))
        raise


def track_db_query(query_type: str):
    """Decorator to track database query performance."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                MetricsCollector.record_db_query(query_type, latency_ms)
                return result
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                MetricsCollector.record_db_query(f"{query_type}_error", latency_ms)
                raise

        return wrapper

    return decorator


# Health check metrics
class HealthMetrics:
    """Health check metrics for monitoring."""

    @staticmethod
    def get_health_status() -> Dict:
        """Get current API health status."""
        metrics = MetricsCollector.get_metrics()

        # Calculate health indicators
        error_count = sum(metrics["errors"].values())
        total_requests = sum(metrics["requests"].values())
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

        # Average latencies
        latencies = metrics["latencies"]
        avg_latencies = {k: v["avg_ms"] for k, v in latencies.items()}

        return {
            "status": "healthy" if error_rate < 5 else "degraded" if error_rate < 10 else "unhealthy",
            "error_rate": error_rate,
            "total_requests": total_requests,
            "total_errors": error_count,
            "active_users": metrics["active_users"],
            "avg_latency_ms": sum(avg_latencies.values()) / len(avg_latencies)
            if avg_latencies
            else 0,
        }
