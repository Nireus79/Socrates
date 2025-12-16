"""
TTL-based Method Caching Decorator for Phase 3

Implements a function decorator for automatic memoization with time-to-live.
"""

import functools
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple


class TTLCache:
    """
    Time-based cache decorator for memoizing function results.

    Caches function return values and automatically expires old entries.
    Thread-safe for concurrent access.

    Typical usage:
        >>> @TTLCache(ttl_minutes=5)
        ... def expensive_operation(project_id: str) -> str:
        ...     # This will be cached for 5 minutes
        ...     return analyze_project(project_id)
        >>>
        >>> result1 = expensive_operation("proj_123")  # Computed (slow)
        >>> result2 = expensive_operation("proj_123")  # Cached (fast)
    """

    def __init__(self, ttl_minutes: int = 5):
        """
        Initialize TTL cache decorator.

        Args:
            ttl_minutes: Time-to-live for cached results in minutes (default: 5)
        """
        self._ttl = timedelta(minutes=ttl_minutes)
        self._cache: Dict[Any, Tuple[Any, datetime]] = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()
        self._logger = logging.getLogger("ttl_cache")

    def __call__(self, func: Callable) -> Callable:
        """
        Wrap a function with caching.

        Args:
            func: Function to cache

        Returns:
            Wrapped function with caching
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from args/kwargs
            try:
                key = (args, tuple(sorted(kwargs.items())))
            except TypeError:
                # If args/kwargs not hashable, skip caching
                self._logger.debug(
                    f"Skipping cache for {func.__name__} - unhashable arguments"
                )
                return func(*args, **kwargs)

            try:
                with self._lock:
                    # Check if cached and not expired
                    if key in self._cache:
                        result, timestamp = self._cache[key]
                        if datetime.now() - timestamp < self._ttl:
                            self._hits += 1
                            self._logger.debug(
                                f"Cache hit for {func.__name__} "
                                f"(age: {(datetime.now()-timestamp).total_seconds():.1f}s)"
                            )
                            return result
                        else:
                            # Expired
                            del self._cache[key]

                    # Cache miss - compute result
                    self._misses += 1

                # Call function outside lock to avoid blocking
                result = func(*args, **kwargs)

                # Store result
                with self._lock:
                    self._cache[key] = (result, datetime.now())
                    self._logger.debug(
                        f"Cached result for {func.__name__} "
                        f"(cache size: {len(self._cache)})"
                    )

                return result
            except TypeError:
                # If key is unhashable (e.g., contains list), skip caching
                self._logger.debug(
                    f"Skipping cache for {func.__name__} - unhashable key"
                )
                return func(*args, **kwargs)

        # Attach cache management methods
        wrapper.cache_clear = self.clear
        wrapper.cache_stats = self.stats
        wrapper.cache_info = self.info
        wrapper._cache = self

        return wrapper

    def clear(self) -> None:
        """Clear all cached results."""
        with self._lock:
            self._cache.clear()
            self._logger.info("TTL cache cleared")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        count = 0
        current_time = datetime.now()

        with self._lock:
            expired_keys = [
                key
                for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp >= self._ttl
            ]

            for key in expired_keys:
                del self._cache[key]
                count += 1

        if count > 0:
            self._logger.info(f"Cleaned up {count} expired cache entries")

        return count

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hit/miss counts and hit rate
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_calls": total,
                "hit_rate": f"{hit_rate:.1f}%",
                "cache_size": len(self._cache),
                "ttl_minutes": self._ttl.total_seconds() / 60,
            }

    def info(self) -> str:
        """Get human-readable cache info."""
        stats = self.stats()
        return (
            f"Cache: {stats['cache_size']} entries, "
            f"{stats['hit_rate']} hit rate, "
            f"TTL: {stats['ttl_minutes']} minutes"
        )

    def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0

    def __repr__(self) -> str:
        """String representation."""
        return f"<TTLCache ttl={self._ttl.total_seconds()/60:.0f}min size={len(self._cache)}>"


def cached(ttl_minutes: int = 5) -> TTLCache:
    """
    Decorator factory for caching function results with TTL.

    Args:
        ttl_minutes: Time-to-live in minutes (default: 5)

    Returns:
        TTLCache decorator instance

    Example:
        >>> @cached(ttl_minutes=10)
        ... def get_project_summary(project_id: str) -> dict:
        ...     return expensive_computation(project_id)
        >>>
        >>> summary1 = get_project_summary("proj_123")  # Computed
        >>> summary2 = get_project_summary("proj_123")  # Cached (10 min)
        >>>
        >>> stats = get_project_summary.cache_stats()
        >>> print(stats)  # {'hits': 1, 'misses': 1, 'hit_rate': '50.0%', ...}
    """
    return TTLCache(ttl_minutes=ttl_minutes)
