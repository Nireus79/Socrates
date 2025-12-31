"""
Redis Caching Layer - Distributed cache for frequently accessed data.

Provides:
- User session caching
- Project metadata caching
- Search result caching
- Rate limit counter storage
- Real-time presence tracking

Falls back to in-memory cache if Redis unavailable.
"""

import json
import logging
import os
from typing import Any, Optional, Dict
import hashlib

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed - caching will be in-memory only")


class InMemoryCache:
    """Simple in-memory cache fallback."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (ignored for in-memory)."""
        self.cache[key] = value

    async def delete(self, key: str):
        """Delete value from cache."""
        self.cache.pop(key, None)

    async def clear(self, pattern: str = "*"):
        """Clear cache entries matching pattern."""
        if pattern == "*":
            self.cache.clear()
        else:
            # Simple pattern matching for in-memory
            import fnmatch

            keys_to_delete = [k for k in self.cache if fnmatch.fnmatch(k, pattern)]
            for k in keys_to_delete:
                del self.cache[k]

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self.cache


class RedisCache:
    """Distributed Redis-backed cache."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379")
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.client = None
        self._connect()

    def _connect(self):
        """Establish Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - using in-memory cache")
            return

        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis cache connected: {self.redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e} - using in-memory cache")
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if self.client is None:
            return None

        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 300)
        """
        if self.client is None:
            return

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if self.client is None:
            return

        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    async def clear(self, pattern: str = "*"):
        """
        Clear cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*", "project:*")
        """
        if self.client is None:
            return

        try:
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    self.client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if self.client is None:
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value
        """
        if self.client is None:
            return 0

        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.client is None:
            return {"type": "in-memory", "status": "unavailable"}

        try:
            info = self.client.info("stats")
            return {
                "type": "redis",
                "status": "connected",
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"type": "redis", "status": "error", "error": str(e)}


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """
    Get or create global cache instance.

    Returns:
        RedisCache instance (uses in-memory fallback if Redis unavailable)
    """
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


# Cache key builders
def cache_key_user(username: str) -> str:
    """Build cache key for user."""
    return f"user:{username}"


def cache_key_project(project_id: str) -> str:
    """Build cache key for project."""
    return f"project:{project_id}"


def cache_key_project_list(username: str) -> str:
    """Build cache key for user's project list."""
    return f"projects:{username}"


def cache_key_search(query: str, limit: int = 10) -> str:
    """Build cache key for search results."""
    query_hash = hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()
    return f"search:{query_hash}:{limit}"


def cache_key_session(session_id: str) -> str:
    """Build cache key for session."""
    return f"session:{session_id}"


def cache_key_rate_limit(key: str) -> str:
    """Build cache key for rate limit counter."""
    return f"ratelimit:{key}"


def cache_key_presence(project_id: str) -> str:
    """Build cache key for active user presence."""
    return f"presence:{project_id}"


# Cache expiration times (in seconds)
CACHE_TTL_USER = 3600  # 1 hour
CACHE_TTL_PROJECT = 1800  # 30 minutes
CACHE_TTL_PROJECT_LIST = 600  # 10 minutes
CACHE_TTL_SEARCH = 1800  # 30 minutes
CACHE_TTL_SESSION = 86400  # 24 hours
CACHE_TTL_PRESENCE = 300  # 5 minutes
