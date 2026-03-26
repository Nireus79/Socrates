"""
Performance Monitoring Middleware

Automatically profiles all API requests using socratic-performance.
Tracks response times, request counts, and identifies slow requests.
"""

import logging
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track API request performance"""

    def __init__(self, app):
        super().__init__(app)
        self.profiler = None
        self._initialize_profiler()

    def _initialize_profiler(self):
        """Initialize profiler from socratic-performance"""
        try:
            from socratic_performance import QueryProfiler
            self.profiler = QueryProfiler()
            logger.info("Performance profiler initialized in middleware")
        except Exception as e:
            logger.debug(f"Performance profiler not available: {e}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Profile each request"""
        # Generate route name for profiling
        route_name = f"{request.method} {request.url.path}"

        # Profile the request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log to profiler if available
        if self.profiler:
            try:
                # Store execution time in internal storage
                if not hasattr(self.profiler, '_executions'):
                    self.profiler._executions = {}
                if route_name not in self.profiler._executions:
                    self.profiler._executions[route_name] = []
                self.profiler._executions[route_name].append(duration * 1000)  # ms
            except Exception as e:
                logger.debug(f"Failed to log performance metric: {e}")

        # Add performance header
        response.headers["X-Response-Time-Ms"] = f"{duration * 1000:.2f}"

        # Log slow requests (> 1 second)
        if duration > 1.0:
            logger.info(f"Slow request: {route_name} took {duration * 1000:.2f}ms")

        return response
