"""
Comprehensive tests for Embedding Cache (Phase 3)

Tests LRU cache for text embeddings with memory tracking.
"""

import pytest
from socratic_system.database.embedding_cache import EmbeddingCache


class TestEmbeddingCacheBasics:
    """Test basic cache functionality"""

    def test_cache_initialization(self):
        """Cache initializes with correct parameters"""
        cache = EmbeddingCache(max_size=100)
        assert cache._max_size == 100
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_cache_default_size(self):
        """Cache uses default max_size of 10000"""
        cache = EmbeddingCache()
        assert cache._max_size == 10000

    def test_put_and_get_basic(self):
        """Basic put and get operations work"""
        cache = EmbeddingCache(max_size=10)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        text = "test query"

        cache.put(text, embedding)
        result = cache.get(text)

        assert result == embedding
        assert cache._hits == 1
        assert cache._misses == 0

    def test_cache_miss(self):
        """Cache miss returns None"""
        cache = EmbeddingCache(max_size=10)

        result = cache.get("nonexistent")

        assert result is None
        assert cache._misses == 1
        assert cache._hits == 0

    def test_multiple_embeddings(self):
        """Multiple different embeddings can be cached"""
        cache = EmbeddingCache(max_size=100)

        cache.put("query1", [1.0, 2.0, 3.0])
        cache.put("query2", [4.0, 5.0, 6.0])
        cache.put("query3", [7.0, 8.0, 9.0])

        assert cache.get("query1") == [1.0, 2.0, 3.0]
        assert cache.get("query2") == [4.0, 5.0, 6.0]
        assert cache.get("query3") == [7.0, 8.0, 9.0]
        assert len(cache._cache) == 3


class TestEmbeddingCacheLRU:
    """Test LRU eviction behavior"""

    def test_lru_eviction_when_full(self):
        """LRU entry is evicted when cache reaches max_size"""
        cache = EmbeddingCache(max_size=3)

        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        cache.put("query3", [3.0])
        cache.put("query4", [4.0])  # Should evict query1 (oldest)

        assert cache.get("query1") is None  # Evicted
        assert cache.get("query4") == [4.0]  # Newest, present
        assert len(cache._cache) == 3

    def test_lru_access_order_updates(self):
        """Accessing entry updates its LRU position"""
        cache = EmbeddingCache(max_size=3)

        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        cache.put("query3", [3.0])

        # Access query1 - moves it to end (most recent)
        cache.get("query1")

        # Add new entry - should evict query2 (now oldest)
        cache.put("query4", [4.0])

        assert cache.get("query2") is None  # Evicted
        assert cache.get("query1") == [1.0]  # Still there (accessed, moved to end)

    def test_lru_update_existing_entry(self):
        """Updating existing entry moves it to end"""
        cache = EmbeddingCache(max_size=3)

        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        cache.put("query3", [3.0])

        # Update query1
        cache.put("query1", [1.5])

        # Add new - should evict query2
        cache.put("query4", [4.0])

        assert cache.get("query2") is None  # Evicted
        assert cache.get("query1") == [1.5]  # Updated and still present

    def test_empty_cache_lru_handling(self):
        """LRU eviction handles empty access_order gracefully"""
        cache = EmbeddingCache(max_size=1)

        cache.put("query1", [1.0])
        cache.put("query2", [2.0])  # Should evict safely

        assert cache.get("query1") is None
        assert cache.get("query2") == [2.0]


class TestEmbeddingCacheStats:
    """Test cache statistics tracking"""

    def test_stats_initial_state(self):
        """Stats initialized to zero"""
        cache = EmbeddingCache()
        stats = cache.stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == "0.0%"
        assert stats["cache_size"] == 0

    def test_stats_after_hits_and_misses(self):
        """Stats accurately reflect hits and misses"""
        cache = EmbeddingCache()

        cache.put("query1", [1.0])

        cache.get("query1")  # Hit
        cache.get("query1")  # Hit
        cache.get("query2")  # Miss

        stats = cache.stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_requests"] == 3
        assert stats["hit_rate"] == "66.7%"

    def test_stats_hit_rate_percentage(self):
        """Hit rate calculated as percentage"""
        cache = EmbeddingCache()

        cache.put("q1", [1.0])
        cache.put("q2", [2.0])
        cache.put("q3", [3.0])

        # 2 hits, 1 miss = 66.7%
        cache.get("q1")
        cache.get("q2")
        cache.get("nonexistent")

        stats = cache.stats()
        assert "66.7%" in stats["hit_rate"]

    def test_stats_memory_estimation(self):
        """Memory estimation included in stats"""
        cache = EmbeddingCache()

        cache.put("query1", [0.1] * 384)  # Typical embedding size

        stats = cache.stats()

        assert "memory_estimate_mb" in stats
        assert stats["memory_estimate_mb"] > 0
        assert stats["max_size"] == 10000

    def test_reset_stats(self):
        """Stats can be reset"""
        cache = EmbeddingCache()

        cache.put("query1", [1.0])
        cache.get("query1")
        cache.get("query1")

        assert cache._hits == 2

        cache.reset_stats()

        assert cache._hits == 0
        assert cache._misses == 0
        stats = cache.stats()
        assert stats["hit_rate"] == "0.0%"


class TestEmbeddingCacheClear:
    """Test cache clearing"""

    def test_clear_removes_all_entries(self):
        """clear() removes all cached entries"""
        cache = EmbeddingCache()

        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        cache.put("query3", [3.0])

        assert len(cache._cache) == 3

        cache.clear()

        assert len(cache._cache) == 0
        assert cache.get("query1") is None

    def test_clear_resets_access_order(self):
        """clear() resets access order tracking"""
        cache = EmbeddingCache()

        cache.put("query1", [1.0])
        cache.put("query2", [2.0])

        assert len(cache._access_order) == 2

        cache.clear()

        assert len(cache._access_order) == 0


class TestEmbeddingCacheThreadSafety:
    """Test thread-safety of cache operations"""

    def test_concurrent_puts(self):
        """Multiple puts don't corrupt cache"""
        import threading

        cache = EmbeddingCache(max_size=1000)

        def put_entries(start_id, count):
            for i in range(start_id, start_id + count):
                cache.put(f"query_{i}", [float(i)])

        threads = [
            threading.Thread(target=put_entries, args=(0, 100)),
            threading.Thread(target=put_entries, args=(100, 100)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have entries from both threads
        assert cache.get("query_0") == [0.0]
        assert cache.get("query_150") == [150.0]

    def test_concurrent_gets(self):
        """Multiple concurrent gets work correctly"""
        import threading

        cache = EmbeddingCache()

        for i in range(50):
            cache.put(f"query_{i}", [float(i)])

        results = []

        def get_entries():
            for i in range(50):
                result = cache.get(f"query_{i}")
                results.append(result)

        threads = [threading.Thread(target=get_entries) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should have gotten all entries
        assert len(results) == 250  # 5 threads × 50 entries


class TestEmbeddingCacheRepr:
    """Test string representation"""

    def test_repr_format(self):
        """__repr__ shows useful cache info"""
        cache = EmbeddingCache(max_size=100)

        cache.put("query1", [0.1] * 384)
        cache.get("query1")

        repr_str = repr(cache)

        assert "EmbeddingCache" in repr_str
        assert "size=" in repr_str
        assert "hit_rate=" in repr_str
        assert "memory=" in repr_str


class TestEmbeddingCacheRealWorldScenarios:
    """Test realistic usage patterns"""

    def test_repeated_same_query(self):
        """Same query benefits from cache"""
        cache = EmbeddingCache()

        query = "What is system design?"
        embedding = [0.1] * 384

        cache.put(query, embedding)

        # Simulate repeated queries
        for _ in range(100):
            result = cache.get(query)
            assert result == embedding

        stats = cache.stats()
        assert stats["hits"] == 100
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "100.0%"

    def test_cache_with_typical_workload(self):
        """Cache performance with 1000 unique embeddings"""
        cache = EmbeddingCache(max_size=10000)

        # Add 1000 embeddings
        for i in range(1000):
            cache.put(f"query_{i}", [float(i)] * 384)

        # Repeat some random queries (some hits, some misses)
        for i in range(100, 200):  # Queries 100-200 (in cache)
            cache.get(f"query_{i}")

        for i in range(5000, 5100):  # Queries 5000+ (not in cache)
            cache.get(f"query_{i}")

        stats = cache.stats()

        # 100 hits on existing queries
        assert stats["hits"] == 100
        # 100 misses on non-existent queries
        assert stats["misses"] == 100
        # Hit rate should be 50%
        assert stats["hit_rate"] == "50.0%"

    def test_cache_size_limit_enforcement(self):
        """Cache respects max_size limit"""
        cache = EmbeddingCache(max_size=50)

        # Add 100 embeddings
        for i in range(100):
            cache.put(f"query_{i}", [float(i)])

        # Cache size should not exceed 50
        assert len(cache._cache) == 50
        assert cache._max_size == 50

        # Oldest entries should be evicted
        # First entries should be gone
        for i in range(50):
            result = cache.get(f"query_{i}")
            assert result is None

        # Recent entries should be present
        for i in range(50, 100):
            result = cache.get(f"query_{i}")
            assert result == [float(i)]
