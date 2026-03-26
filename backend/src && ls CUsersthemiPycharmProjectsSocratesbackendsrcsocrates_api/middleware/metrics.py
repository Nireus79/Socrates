"""
Metrics Middleware - Collect and expose Prometheus metrics.

Provides:
- HTTP request metrics (count, latency, status codes)
- Database query metrics (count, latency, errors)
- System metrics (uptime, memory usage)
- Custom application metrics

Metrics are exposed at /metrics endpoint in Prometheus format.
"""

import logging
import time
from typing import Dict

from fastapi import Request
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Create custom registry for metrics
_registry = CollectorRegistry()

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=_registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=_registry,
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=_registry,
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint", "status"],
    registry=_registry,
)

# Database Metrics
db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["query_type", "status"],
    registry=_registry,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=_registry,
)

# Connection Pool Metrics
connection_pool_size = Gauge(
    "connection_pool_size",
    "Current size of connection pool",
    registry=_registry,
)

connection_pool_active = Gauge(
    "connection_pool_active",
    "Number of active connections in pool",
    registry=_registry,
)

# System Metrics
app_requests_in_progress = Gauge(
    "app_requests_in_progress",
    "Number of requests currently being processed",
    registry=_registry,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for all HTTP requests.

    Tracks:
    - Total request count by method/endpoint/status
    - Request latency (histogram with multiple buckets)
    - Request/response sizes
    - Requests in progress
    """

    def __init__(self, app):
        """
        Initialize metrics middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response with metrics collected
        """
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track request start
        start_time = time.time()
        app_requests_in_progress.inc()

        # Normalize endpoint path for metrics (remove IDs to reduce cardinality)
        endpoint = self._normalize_endpoint(request.url.path)

        # Track request size if available
        request_size = 0
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                if request.headers.get("content-length"):
                    request_size = int(request.headers["content-length"])
            except (ValueError, KeyError):
                pass

        try:
            response = await call_next(request)
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
                status="error",
            ).observe(duration)
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status="error",
            ).inc()
            app_requests_in_progress.dec()
            logger.error(f"Request error: {request.method} {request.url.path}: {e}")
            raise

        # Collect metrics
        duration = time.time() - start_time

        # Handle both regular and streaming responses
        try:
            status_code = response.status
        except AttributeError:
            # Streaming responses don't have a status attribute until sent
            status_code = 200  # Default to 200 for streaming responses

        # Record request metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
            status=status_code,
        ).observe(duration)

        # Record request size
        if request_size > 0:
            http_request_size_bytes.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(request_size)

        # Record response size if available
        response_size = 0
        if response.headers.get("content-length"):
            try:
                response_size = int(response.headers["content-length"])
                http_response_size_bytes.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=status_code,
                ).observe(response_size)
            except ValueError:
                pass

        app_requests_in_progress.dec()

        # Add request timing header (if response headers are mutable)
        try:
            response.headers["X-Process-Time"] = f"{duration:.4f}"
        except (AttributeError, TypeError):
            # Some response types don't allow header modification
            pass

        # Log slow requests
        if duration > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration:.2f}s (status: {status_code})"
            )

        return response

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        Normalize endpoint path for metrics.

        Replaces UUIDs and IDs with placeholders to reduce metric cardinality.

        Args:
            path: Original request path

        Returns:
            Normalized path for use in metrics labels
        """
        import re

        # Replace UUID patterns with {id}
        normalized = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs with {id}
        normalized = re.sub(r"/\d+(?=/|$)", "/{id}", normalized)

        return normalized


def add_metrics_middleware(app):
    """
    Add metrics middleware to FastAPI application.

    Args:
        app: FastAPI application instance

    Example:
        ```python
        from fastapi import FastAPI
        from socrates_api.middleware.metrics import add_metrics_middleware

        app = FastAPI()
        add_metrics_middleware(app)
        ```
    """
    app.add_middleware(MetricsMiddleware)
    logger.info("Metrics middleware added")


def get_metrics_registry():
    """
    Get the Prometheus metrics registry.

    Returns:
        CollectorRegistry instance
    """
    return _registry


def get_metrics_text() -> str:
    """
    Get metrics in Prometheus text format.

    Returns:
        Prometheus-formatted metrics text
    """
    return generate_latest(_registry).decode("utf-8")


# Utility functions for recording custom metrics


def record_db_query(query_type: str, duration: float, success: bool = True):
    """
    Record a database query metric.

    Args:
        query_type: Type of query (select, insert, update, delete)
        duration: Query duration in seconds
        success: Whether query succeeded
    """
    status = "success" if success else "error"
    db_queries_total.labels(query_type=query_type, status=status).inc()
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def set_connection_pool_metrics(size: int, active: int):
    """
    Update connection pool metrics.

    Args:
        size: Total pool size
        active: Number of active connections
    """
    connection_pool_size.set(size)
    connection_pool_active.set(active)


def get_metrics_summary() -> Dict:
    """
    Get a summary of current metrics.

    Returns:
        Dictionary with metric summaries
    """
    return {
        "http_requests_total": _get_counter_value(http_requests_total),
        "http_request_duration_seconds": "See /metrics endpoint",
        "db_queries_total": _get_counter_value(db_queries_total),
        "connection_pool_active": connection_pool_active._value.get(),
        "app_requests_in_progress": app_requests_in_progress._value.get(),
    }


def _get_counter_value(counter) -> int:
    """
    Get total value from a Counter metric (sum of all labels).

    Args:
        counter: Counter metric instance

    Returns:
        Total count value
    """
    try:
        total = 0
        for sample in counter.collect():
            for s in sample.samples:
                total += s.value
        return int(total)
    except Exception:
        return 0
