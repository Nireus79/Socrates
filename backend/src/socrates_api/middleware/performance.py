"""
Production Performance Monitoring Middleware

Uses socratic-performance library for:
- QueryProfiler: Automatic request profiling and analysis
- TTLCache: High-performance response caching with time-to-live
- Decorators: @profile for methods, @cached for metrics

Tracks response times, caching, and identifies performance bottlenecks.
"""

import logging
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Import production-grade performance monitoring (required)
from socratic_performance import QueryProfiler, TTLCache

logger = logging.getLogger(__name__)

# Global cache with 5-minute default TTL (300 seconds = 5 minutes)
_PERFORMANCE_CACHE = TTLCache(ttl_minutes=5)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track and optimize API request performance"""

    def __init__(self, app):
        super().__init__(app)
        # Initialize profiler from socratic-performance (required)
        self.profiler = QueryProfiler()
        logger.info("Production-grade QueryProfiler initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Profile and cache request performance"""
        # Generate cache key for this route
        route_name = f"{request.method} {request.url.path}"
        cache_key = f"perf:{route_name}"

        # Check if this is a cacheable request (GET only)
        is_cacheable = request.method == "GET"

        # Check cache first
        if is_cacheable and cache_key in _PERFORMANCE_CACHE:
            logger.debug(f"Cache hit for {route_name}")
            # Return cached response metrics
            cached_metrics = _PERFORMANCE_CACHE[cache_key]
            response = await call_next(request)
            response.headers["X-Response-Time-Ms"] = f"{cached_metrics['duration']:.2f}"
            response.headers["X-Cache-Hit"] = "true"
            return response

        # Profile the request execution
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # Record request performance with QueryProfiler
        try:
            self.profiler.record_query(
                query_name=route_name,
                duration=duration_ms,
                success=response.status_code < 400,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record profile: {e}")

        # Cache performance metrics for subsequent requests
        if is_cacheable:
            try:
                _PERFORMANCE_CACHE[cache_key] = {
                    "duration": duration_ms,
                    "route": route_name,
                    "status": response.status_code
                }
            except Exception as e:
                logger.debug(f"Failed to cache performance data: {e}")

        # Add performance headers
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Cache-Hit"] = "false"

        # Log slow requests (> 1 second)
        if duration > 1.0:
            logger.warning(
                f"SLOW REQUEST: {route_name} took {duration_ms:.2f}ms "
                f"[{response.status_code}]"
            )

        # Log extremely slow requests with profiler analysis
        if duration > 5.0:
            try:
                # Get profiler stats for analysis
                stats = self.profiler.get_slowest_queries(limit=5)
                logger.error(
                    f"CRITICAL PERFORMANCE: {route_name} took {duration_ms:.2f}ms | "
                    f"Top slow queries: {len(stats) if stats else 0}"
                )
            except Exception as e:
                logger.debug(f"Failed to get profiler stats: {e}")

        return response

    def get_performance_stats(self):
        """Get current performance statistics"""
        try:
            return {
                "slowest_queries": self.profiler.get_slowest_queries(limit=10),
                "cache_size": len(_PERFORMANCE_CACHE),
                "cache_ttl": _PERFORMANCE_CACHE.ttl if hasattr(_PERFORMANCE_CACHE, 'ttl') else 300
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
