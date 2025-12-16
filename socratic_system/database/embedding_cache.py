"""
Embedding Cache for Phase 3 Optimization

Implements LRU cache for text embeddings to avoid redundant encoding.
Typical speedup: 50ms → 0.5ms (100x improvement) for cached embeddings.
"""

import hashlib
import logging
import threading
from typing import Dict, List, Optional


class EmbeddingCache:
    """
    LRU (Least Recently Used) cache for text embeddings.

    Caches embedding vectors to avoid redundant encoding operations.
    Automatically evicts oldest entries when capacity is reached.

    Typical usage:
        >>> cache = EmbeddingCache(max_size=10000)
        >>>
        >>> # On cache miss, compute and store
        >>> embedding = model.encode("sample text")
        >>> cache.put("sample text", embedding)
        >>>
        >>> # On cache hit, retrieve immediately
        >>> cached = cache.get("sample text")
        >>> if cached:
        ...     embedding = cached  # 100x faster than re-encoding
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize embedding cache.

        Args:
            max_size: Maximum number of embeddings to cache (default: 10000)
                Recommended: 10000 for 6-15MB memory usage with typical embeddings
        """
        self._cache: Dict[str, List[float]] = {}
        self._access_order: List[str] = []
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()
        self._logger = logging.getLogger("embedding_cache")

    def get(self, text: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding for text.

        Args:
            text: Text to look up

        Returns:
            Embedding vector if cached, None otherwise

        Performance:
            - Cache hit: ~0.1ms
            - Cache miss: 0ms (just lookup)
        """
        text_hash = self._hash_text(text)

        with self._lock:
            if text_hash in self._cache:
                # Move to end (most recently used)
                self._access_order.remove(text_hash)
                self._access_order.append(text_hash)
                self._hits += 1
                return self._cache[text_hash]

            self._misses += 1
            return None

    def put(self, text: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.

        Args:
            text: Text that was encoded
            embedding: The embedding vector

        Performance:
            - Always: <1ms (just hash and store)
        """
        text_hash = self._hash_text(text)

        with self._lock:
            # Evict LRU entry if cache full
            if len(self._cache) >= self._max_size:
                if self._access_order:
                    oldest = self._access_order.pop(0)
                    del self._cache[oldest]
                    self._logger.debug(f"Evicted oldest embedding from cache")

            # Store or update
            if text_hash in self._cache:
                # Update existing - move to end
                self._access_order.remove(text_hash)
            else:
                # New entry
                self._logger.debug(f"Caching new embedding (cache size: {len(self._cache)+1})")

            self._cache[text_hash] = embedding
            self._access_order.append(text_hash)

    def clear(self) -> None:
        """Clear all cached embeddings."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._logger.info("Embedding cache cleared")

    def stats(self) -> Dict[str, any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hit/miss counts and hit rate percentage
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "hit_rate": f"{hit_rate:.1f}%",
                "cache_size": len(self._cache),
                "max_size": self._max_size,
                "memory_estimate_mb": self._estimate_memory_mb(),
            }

    def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0

    def _estimate_memory_mb(self) -> float:
        """Estimate memory usage in MB."""
        # Typical embedding: 384 dimensions × 4 bytes (float32) = 1536 bytes
        # + overhead = ~2KB per embedding
        avg_bytes_per_embedding = 2000
        total_bytes = len(self._cache) * avg_bytes_per_embedding
        return total_bytes / (1024 * 1024)

    @staticmethod
    def _hash_text(text: str) -> str:
        """Hash text for cache key."""
        return hashlib.sha256(text.encode()).hexdigest()

    def __repr__(self) -> str:
        """String representation with stats."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return (
                f"<EmbeddingCache size={len(self._cache)}/{self._max_size} "
                f"hit_rate={hit_rate:.1f}% memory={self._estimate_memory_mb():.1f}MB>"
            )
