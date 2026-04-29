"""
Result cache for async operation results.

Provides:
- TTL-based result caching
- Polling-friendly result storage
- Cache statistics and cleanup
"""

import logging
import time
from typing import Any, Dict, Optional


class CacheEntry:
    """Cache entry with TTL"""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: float = 3600.0,
    ):
        """
        Initialize cache entry.

        Args:
            key: Cache key
            value: Cached value
            ttl: Time to live in seconds
        """
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
        self.access_count = 0

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return (time.time() - self.created_at) > self.ttl

    def access(self) -> Any:
        """Access entry and return value"""
        self.access_count += 1
        return self.value


class ResultCache:
    """Cache for async operation results"""

    def __init__(self, default_ttl: float = 3600.0):
        """
        Initialize result cache.

        Args:
            default_ttl: Default TTL for entries in seconds
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(__name__)

        # Metrics
        self.metrics = {
            "total_sets": 0,
            "total_gets": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Set cache value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        ttl = ttl or self.default_ttl
        self.cache[key] = CacheEntry(key, value, ttl)
        self.metrics["total_sets"] += 1

        self.logger.debug(f"Cached result for key: {key}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        self.metrics["total_gets"] += 1

        if key not in self.cache:
            self.metrics["cache_misses"] += 1
            return None

        entry = self.cache[key]

        if entry.is_expired():
            del self.cache[key]
            self.metrics["cache_misses"] += 1
            self.logger.debug(f"Cache entry expired: {key}")
            return None

        self.metrics["cache_hits"] += 1
        return entry.access()

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if valid entry exists
        """
        if key not in self.cache:
            return False

        if self.cache[key].is_expired():
            del self.cache[key]
            return False

        return True

    def delete(self, key: str) -> bool:
        """
        Delete cache entry.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        if key in self.cache:
            del self.cache[key]
            self.logger.debug(f"Deleted cache entry: {key}")
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        self.logger.info(f"Cleared {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]

        self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary
        """
        hit_rate = 0.0
        if self.metrics["total_gets"] > 0:
            hit_rate = (
                self.metrics["cache_hits"] / self.metrics["total_gets"] * 100
            )

        return {
            **self.metrics,
            "cached_entries": len(self.cache),
            "hit_rate_percent": hit_rate,
        }

    def set_ttl(self, key: str, ttl: float) -> bool:
        """
        Update TTL for existing entry.

        Args:
            key: Cache key
            ttl: New TTL in seconds

        Returns:
            True if updated
        """
        if key in self.cache and not self.cache[key].is_expired():
            self.cache[key].ttl = ttl
            return True
        return False

    def get_all_valid(self) -> Dict[str, Any]:
        """
        Get all non-expired cached values.

        Returns:
            Dictionary of valid entries
        """
        self.cleanup_expired()
        return {
            key: entry.value
            for key, entry in self.cache.items()
        }
