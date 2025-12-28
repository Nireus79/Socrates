"""Database query performance profiling and monitoring.

Provides decorators and utilities for:
- Query execution time tracking
- Slow query detection and logging
- Performance statistics aggregation
- Development-mode detailed logging
"""

import asyncio
import functools
import logging
import time
from typing import Callable, TypeVar, Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])


class QueryStats:
    """Statistics for a single query or operation.

    Tracks execution counts, timing, and slow query occurrences.
    """

    def __init__(self, name: str) -> None:
        """Initialize query statistics.

        Args:
            name: Query or operation name
        """
        self.name = name
        self.count = 0
        self.total_time = 0.0
        self.min_time = float("inf")
        self.max_time = 0.0
        self.slow_count = 0
        self.error_count = 0
        self.last_executed_at: Optional[float] = None

    def add_execution(
        self, duration: float, is_slow: bool = False, error: bool = False
    ) -> None:
        """Record a query execution.

        Args:
            duration: Execution time in seconds
            is_slow: Whether query exceeded slow threshold
            error: Whether query resulted in error
        """
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.last_executed_at = time.time()

        if is_slow:
            self.slow_count += 1
        if error:
            self.error_count += 1

    @property
    def avg_time_ms(self) -> float:
        """Average execution time in milliseconds."""
        if self.count == 0:
            return 0.0
        return (self.total_time / self.count) * 1000

    @property
    def max_time_ms(self) -> float:
        """Maximum execution time in milliseconds."""
        return self.max_time * 1000

    @property
    def min_time_ms(self) -> float:
        """Minimum execution time in milliseconds."""
        return self.min_time * 1000 if self.min_time != float("inf") else 0.0

    @property
    def total_time_ms(self) -> float:
        """Total execution time in milliseconds."""
        return self.total_time * 1000

    @property
    def slow_percentage(self) -> float:
        """Percentage of executions that were slow."""
        if self.count == 0:
            return 0.0
        return (self.slow_count / self.count) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dict with all statistics
        """
        return {
            "name": self.name,
            "count": self.count,
            "avg_time_ms": round(self.avg_time_ms, 2),
            "min_time_ms": round(self.min_time_ms, 2),
            "max_time_ms": round(self.max_time_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2),
            "slow_count": self.slow_count,
            "slow_percentage": round(self.slow_percentage, 1),
            "error_count": self.error_count,
            "last_executed_at": self.last_executed_at,
        }


class QueryProfiler:
    """Database query performance profiler.

    Tracks execution time and performance metrics for database operations.
    Can be used as decorator or standalone.

    Example:
        ```python
        profiler = QueryProfiler(slow_query_threshold_ms=100)

        @profiler.profile("get_user")
        async def load_user(user_id: str):
            async with pool.get_session() as session:
                return await session.get(User, user_id)

        # Get statistics
        stats = profiler.get_stats()
        print(f"get_user avg time: {stats['get_user']['avg_time_ms']:.2f}ms")
        ```
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0) -> None:
        """Initialize query profiler.

        Args:
            slow_query_threshold_ms: Threshold above which queries are considered slow (default: 100ms)
        """
        self.slow_query_threshold = slow_query_threshold_ms / 1000.0
        self.stats: Dict[str, QueryStats] = {}
        logger.info(
            f"QueryProfiler initialized with slow query threshold: {slow_query_threshold_ms}ms"
        )

    def profile(
        self,
        query_name: str,
        slow_query_threshold_ms: Optional[float] = None,
    ) -> Callable[[F], F]:
        """Decorator to profile query execution time.

        Tracks both sync and async functions.

        Args:
            query_name: Name for the query/operation
            slow_query_threshold_ms: Optional override for slow query threshold

        Returns:
            Decorated function that tracks execution time

        Example:
            ```python
            @profiler.profile("list_projects")
            async def get_projects(db):
                return await db.query(Project).all()
            ```
        """
        threshold = (
            slow_query_threshold_ms / 1000.0
            if slow_query_threshold_ms is not None
            else self.slow_query_threshold
        )

        if query_name not in self.stats:
            self.stats[query_name] = QueryStats(query_name)

        def decorator(func: F) -> F:
            # Check if function is async
            if asyncio.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    """Async function wrapper."""
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        duration = time.time() - start_time
                        is_slow = duration > threshold

                        stats = self.stats[query_name]
                        stats.add_execution(duration, is_slow=is_slow)

                        if is_slow:
                            logger.warning(
                                f"Slow async query: {query_name} took {duration*1000:.2f}ms "
                                f"(threshold: {threshold*1000:.0f}ms)"
                            )
                        else:
                            logger.debug(
                                f"Query: {query_name} completed in {duration*1000:.2f}ms"
                            )

                        return result

                    except Exception as e:
                        duration = time.time() - start_time
                        stats = self.stats[query_name]
                        stats.add_execution(duration, error=True)

                        logger.error(
                            f"Query error: {query_name} failed after {duration*1000:.2f}ms: {e}"
                        )
                        raise

                return async_wrapper  # type: ignore

            else:

                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    """Sync function wrapper."""
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        duration = time.time() - start_time
                        is_slow = duration > threshold

                        stats = self.stats[query_name]
                        stats.add_execution(duration, is_slow=is_slow)

                        if is_slow:
                            logger.warning(
                                f"Slow query: {query_name} took {duration*1000:.2f}ms "
                                f"(threshold: {threshold*1000:.0f}ms)"
                            )
                        else:
                            logger.debug(
                                f"Query: {query_name} completed in {duration*1000:.2f}ms"
                            )

                        return result

                    except Exception as e:
                        duration = time.time() - start_time
                        stats = self.stats[query_name]
                        stats.add_execution(duration, error=True)

                        logger.error(
                            f"Query error: {query_name} failed after {duration*1000:.2f}ms: {e}"
                        )
                        raise

                return sync_wrapper  # type: ignore

        return decorator

    def manual_track(
        self,
        query_name: str,
        duration: float,
        is_slow: bool = False,
        error: bool = False,
    ) -> None:
        """Manually track a query execution without decorator.

        Useful for tracking operations not wrapped with @profile decorator.

        Args:
            query_name: Name of query/operation
            duration: Execution time in seconds
            is_slow: Whether query exceeded threshold
            error: Whether query resulted in error

        Example:
            ```python
            start = time.time()
            try:
                result = db.complex_operation()
                duration = time.time() - start
                profiler.manual_track("complex_op", duration)
            except Exception:
                duration = time.time() - start
                profiler.manual_track("complex_op", duration, error=True)
                raise
            ```
        """
        if query_name not in self.stats:
            self.stats[query_name] = QueryStats(query_name)

        self.stats[query_name].add_execution(duration, is_slow=is_slow, error=error)

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all collected statistics.

        Returns:
            Dict mapping query names to their statistics

        Example:
            ```python
            stats = profiler.get_stats()
            for name, metrics in stats.items():
                print(f"{name}: avg={metrics['avg_time_ms']:.1f}ms")
            ```
        """
        return {name: stats.to_dict() for name, stats in self.stats.items()}

    def get_slow_queries(self, min_slow_count: int = 1) -> List[Dict[str, Any]]:
        """Get list of queries with slow executions.

        Args:
            min_slow_count: Only return queries with at least this many slow executions

        Returns:
            List of query statistics, sorted by slow count descending

        Example:
            ```python
            slow = profiler.get_slow_queries(min_slow_count=5)
            for query in slow:
                print(f"Query {query['name']} had {query['slow_count']} slow executions")
            ```
        """
        slow_queries = [
            stats.to_dict()
            for stats in self.stats.values()
            if stats.slow_count >= min_slow_count
        ]
        # Sort by slow count descending
        return sorted(slow_queries, key=lambda x: x["slow_count"], reverse=True)

    def get_slowest_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get queries with highest average execution time.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of query statistics, sorted by avg time descending

        Example:
            ```python
            slowest = profiler.get_slowest_queries(limit=5)
            for query in slowest:
                print(f"Query {query['name']}: avg={query['avg_time_ms']:.1f}ms")
            ```
        """
        sorted_stats = sorted(
            [stats.to_dict() for stats in self.stats.values()],
            key=lambda x: x["avg_time_ms"],
            reverse=True,
        )
        return sorted_stats[:limit]

    def reset_stats(self, query_name: Optional[str] = None) -> None:
        """Reset statistics for one or all queries.

        Args:
            query_name: Specific query to reset, or None to reset all

        Example:
            ```python
            profiler.reset_stats()  # Reset all
            profiler.reset_stats("specific_query")  # Reset one
            ```
        """
        if query_name is None:
            self.stats.clear()
            logger.info("All query statistics reset")
        elif query_name in self.stats:
            del self.stats[query_name]
            logger.info(f"Statistics reset for query: {query_name}")

    def print_summary(self, limit: int = 10) -> None:
        """Print summary of query performance to logger.

        Args:
            limit: Number of slowest queries to show

        Example:
            ```python
            profiler.print_summary(limit=5)
            ```
        """
        if not self.stats:
            logger.info("No query statistics collected")
            return

        logger.info("=" * 80)
        logger.info("QUERY PERFORMANCE SUMMARY")
        logger.info("=" * 80)

        slowest = self.get_slowest_queries(limit=limit)
        logger.info(f"Top {len(slowest)} Slowest Queries:")
        for i, query in enumerate(slowest, 1):
            logger.info(
                f"  {i}. {query['name']}: "
                f"avg={query['avg_time_ms']:.1f}ms, "
                f"max={query['max_time_ms']:.1f}ms, "
                f"count={query['count']}, "
                f"slow={query['slow_count']}({query['slow_percentage']:.0f}%)"
            )

        slow = self.get_slow_queries(min_slow_count=1)
        logger.info(f"\nQueries with Slow Executions ({len(slow)} total):")
        for query in slow[:limit]:
            logger.info(
                f"  • {query['name']}: {query['slow_count']} slow out of {query['count']} executions"
            )

        logger.info("=" * 80)


# Global profiler instance
_profiler: Optional[QueryProfiler] = None


def get_profiler() -> QueryProfiler:
    """Get or create global query profiler instance.

    Returns:
        QueryProfiler: Global profiler instance

    Example:
        ```python
        profiler = get_profiler()
        stats = profiler.get_stats()
        ```
    """
    global _profiler
    if _profiler is None:
        _profiler = QueryProfiler()
    return _profiler


def profile_query(
    query_name: str,
    slow_query_threshold_ms: Optional[float] = None,
) -> Callable[[F], F]:
    """Module-level decorator using global profiler.

    Args:
        query_name: Name for the query
        slow_query_threshold_ms: Optional threshold override

    Returns:
        Decorated function

    Example:
        ```python
        @profile_query("get_user")
        async def load_user(db, user_id):
            ...
        ```
    """
    profiler = get_profiler()
    return profiler.profile(query_name, slow_query_threshold_ms)
