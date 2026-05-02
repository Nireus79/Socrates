"""Analysis result caching layer for Phase 3 event-driven architecture.

Implements result caching with TTL support to enable non-blocking
response processing in SocraticCounselor.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)


class AnalysisCache(ABC):
    """Base class for analysis result caching"""

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        """Set cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default 1 hour)
        """
        pass

    @abstractmethod
    def delete(self, key: str):
        """Delete cache entry.

        Args:
            key: Cache key
        """
        pass

    @abstractmethod
    def clear_expired(self):
        """Remove all expired entries"""
        pass

    @abstractmethod
    def clear(self):
        """Clear entire cache"""
        pass


class InMemoryAnalysisCache(AnalysisCache):
    """In-memory cache with TTL support and thread safety.

    Used for caching analysis results (quality, conflicts, insights)
    to enable polling by clients while background processing occurs.
    """

    def __init__(self):
        """Initialize in-memory cache"""
        self._cache: Dict[str, tuple] = {}  # {key: (value, expiry_time)}
        self._lock = Lock()
        self._max_size = 10000  # Max cache entries
        logger.info("InMemoryAnalysisCache initialized")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value by key, respecting TTL.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if valid, None if expired or missing
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]
            current_time = time.time()

            # Check if expired
            if current_time > expiry:
                del self._cache[key]
                logger.debug(f"Cache hit expired: {key}")
                return None

            logger.debug(f"Cache hit: {key}")
            return value

    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        """Set cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache (should be dict for serialization)
            ttl: Time-to-live in seconds
        """
        with self._lock:
            # Implement simple LRU by clearing oldest if at capacity
            if len(self._cache) >= self._max_size:
                # Remove oldest entry (lowest expiry time)
                oldest_key = min(self._cache.keys(),
                               key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
                logger.debug(f"Cache capacity reached, evicted: {oldest_key}")

            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)
            logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def delete(self, key: str):
        """Delete specific cache entry.

        Args:
            key: Cache key to delete
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")

    def clear_expired(self):
        """Remove all expired entries from cache"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, (_, exp) in self._cache.items()
                if exp < current_time
            ]

            for k in expired_keys:
                del self._cache[k]

            if expired_keys:
                logger.debug(f"Cache cleaned {len(expired_keys)} expired entries")

    def clear(self):
        """Clear entire cache"""
        with self._lock:
            size = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared ({size} entries removed)")

    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for _, exp in self._cache.values()
                if exp < current_time
            )

            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "valid_entries": len(self._cache) - expired_count,
                "max_size": self._max_size
            }
