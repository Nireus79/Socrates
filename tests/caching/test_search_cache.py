"""
Comprehensive tests for Search Result Cache (Phase 3)

Tests TTL-based cache for vector search results with invalidation.
"""

import pytest
import time
from socratic_system.database.search_cache import SearchResultCache


class TestSearchCacheBasics:
    """Test basic cache functionality"""

    def test_cache_initialization(self):
        """Cache initializes with correct parameters"""
        cache = SearchResultCache(ttl_seconds=300)
        assert cache._ttl == 300
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_cache_default_ttl(self):
        """Cache uses default TTL of 300 seconds"""
        cache = SearchResultCache()
        assert cache._ttl == 300

    def test_put_and_get_basic(self):
        """Basic put and get operations work"""
        cache = SearchResultCache(ttl_seconds=60)
        results = [
            {"id": "doc1", "score": 0.95, "content": "result 1"},
            {"id": "doc2", "score": 0.87, "content": "result 2"},
        ]
        query = "test query"
        top_k = 5

        cache.put(query, top_k, None, results)
        result = cache.get(query, top_k, None)

        assert result == results
        assert cache._hits == 1
        assert cache._misses == 0

    def test_cache_miss(self):
        """Cache miss returns None"""
        cache = SearchResultCache()

        result = cache.get("nonexistent query", 5, None)

        assert result is None
        assert cache._misses == 1
        assert cache._hits == 0

    def test_different_top_k_values(self):
        """Different top_k values are cached separately"""
        cache = SearchResultCache()

        results_5 = [{"id": "1"}] * 5
        results_10 = [{"id": "1"}] * 10

        cache.put("query", 5, None, results_5)
        cache.put("query", 10, None, results_10)

        assert cache.get("query", 5, None) == results_5
        assert cache.get("query", 10, None) == results_10

    def test_different_projects(self):
        """Different project_ids are cached separately"""
        cache = SearchResultCache()

        results_proj1 = [{"id": "1", "project_id": "proj_1"}]
        results_proj2 = [{"id": "2", "project_id": "proj_2"}]

        cache.put("query", 5, "proj_1", results_proj1)
        cache.put("query", 5, "proj_2", results_proj2)

        assert cache.get("query", 5, "proj_1") == results_proj1
        assert cache.get("query", 5, "proj_2") == results_proj2


class TestSearchCacheTTL:
    """Test TTL-based expiration"""

    def test_ttl_expiration(self):
        """Entry expires after TTL seconds"""
        cache = SearchResultCache(ttl_seconds=1)
        results = [{"id": "1"}]

        cache.put("query", 5, None, results)

        # Immediately: should be cached
        assert cache.get("query", 5, None) == results

        # After TTL: should be expired
        time.sleep(1.1)
        assert cache.get("query", 5, None) is None

    def test_ttl_not_expired_yet(self):
        """Entry available before TTL expires"""
        cache = SearchResultCache(ttl_seconds=5)
        results = [{"id": "1"}]

        cache.put("query", 5, None, results)

        # Sleep less than TTL
        time.sleep(0.5)

        # Should still be cached
        assert cache.get("query", 5, None) == results
        assert cache._hits == 1

    def test_expired_entry_is_removed(self):
        """Expired entries are deleted from cache"""
        cache = SearchResultCache(ttl_seconds=1)
        results = [{"id": "1"}]

        cache.put("query", 5, None, results)
        cache._expires = 0  # Reset expiration counter

        time.sleep(1.1)
        result = cache.get("query", 5, None)

        assert result is None
        # Entry should have been deleted
        assert "query:5:None" not in cache._cache

    def test_multiple_ttl_values(self):
        """Different caches can have different TTLs"""
        cache1 = SearchResultCache(ttl_seconds=1)
        cache2 = SearchResultCache(ttl_seconds=10)

        results = [{"id": "1"}]

        cache1.put("query", 5, None, results)
        cache2.put("query", 5, None, results)

        time.sleep(1.1)

        # cache1 should expire
        assert cache1.get("query", 5, None) is None

        # cache2 should still be valid
        assert cache2.get("query", 5, None) == results


class TestSearchCacheInvalidation:
    """Test cache invalidation"""

    def test_invalidate_query_specific_top_k(self):
        """Invalidate specific query with specific top_k"""
        cache = SearchResultCache()

        cache.put("query", 5, None, [{"id": "1"}])
        cache.put("query", 10, None, [{"id": "2"}])

        count = cache.invalidate_query("query", top_k=5)

        assert count == 1
        assert cache.get("query", 5, None) is None
        assert cache.get("query", 10, None) == [{"id": "2"}]

    def test_invalidate_query_all_top_k(self):
        """Invalidate all top_k values for a query"""
        cache = SearchResultCache()

        cache.put("query", 5, None, [{"id": "1"}])
        cache.put("query", 10, None, [{"id": "2"}])
        cache.put("query", 20, None, [{"id": "3"}])

        count = cache.invalidate_query("query")

        assert count == 3
        assert cache.get("query", 5, None) is None
        assert cache.get("query", 10, None) is None
        assert cache.get("query", 20, None) is None

    def test_invalidate_project_removes_project_entries(self):
        """Invalidate project removes all entries for that project"""
        cache = SearchResultCache()

        cache.put("query1", 5, "proj_123", [{"id": "1"}])
        cache.put("query2", 5, "proj_123", [{"id": "2"}])
        cache.put("query3", 5, "proj_456", [{"id": "3"}])

        count = cache.invalidate_project("proj_123")

        assert count == 2
        assert cache.get("query1", 5, "proj_123") is None
        assert cache.get("query2", 5, "proj_123") is None
        assert cache.get("query3", 5, "proj_456") == [{"id": "3"}]

    def test_invalidate_nonexistent_removes_nothing(self):
        """Invalidating nonexistent entry returns 0"""
        cache = SearchResultCache()

        cache.put("query", 5, None, [{"id": "1"}])

        count = cache.invalidate_query("nonexistent")

        assert count == 0


class TestSearchCacheStats:
    """Test cache statistics"""

    def test_stats_initial_state(self):
        """Stats initialized to zero"""
        cache = SearchResultCache()
        stats = cache.stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["expires"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == "0.0%"
        assert stats["cache_size"] == 0

    def test_stats_hit_miss_expire_tracking(self):
        """Stats accurately track hits, misses, and expirations"""
        cache = SearchResultCache(ttl_seconds=1)
        results = [{"id": "1"}]

        cache.put("query", 5, None, results)

        # Hit
        cache.get("query", 5, None)
        assert cache._hits == 1

        # Miss
        cache.get("nonexistent", 5, None)
        assert cache._misses == 1

        # Expiration
        time.sleep(1.1)
        cache.get("query", 5, None)
        assert cache._expires == 1

    def test_stats_hit_rate_calculation(self):
        """Hit rate calculated correctly"""
        cache = SearchResultCache()

        cache.put("q1", 5, None, [{"id": "1"}])
        cache.put("q2", 5, None, [{"id": "2"}])

        # 2 hits, 1 miss = 66.7%
        cache.get("q1", 5, None)
        cache.get("q2", 5, None)
        cache.get("nonexistent", 5, None)

        stats = cache.stats()
        assert "66.7%" in stats["hit_rate"]

    def test_stats_memory_estimation(self):
        """Memory estimation included in stats"""
        cache = SearchResultCache()

        results = [{"id": f"doc_{i}", "content": "x" * 100} for i in range(10)]
        cache.put("query", 5, None, results)

        stats = cache.stats()

        assert "memory_estimate_mb" in stats
        assert stats["memory_estimate_mb"] > 0

    def test_reset_stats(self):
        """Stats can be reset"""
        cache = SearchResultCache()

        cache.put("query", 5, None, [{"id": "1"}])
        cache.get("query", 5, None)
        cache.get("query", 5, None)

        assert cache._hits == 2

        cache.reset_stats()

        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._expires == 0


class TestSearchCacheClear:
    """Test cache clearing"""

    def test_clear_removes_all_entries(self):
        """clear() removes all cached entries"""
        cache = SearchResultCache()

        cache.put("q1", 5, None, [{"id": "1"}])
        cache.put("q2", 5, None, [{"id": "2"}])
        cache.put("q3", 5, None, [{"id": "3"}])

        assert len(cache._cache) == 3

        cache.clear()

        assert len(cache._cache) == 0
        assert cache.get("q1", 5, None) is None


class TestSearchCacheCleanupExpired:
    """Test cleanup of expired entries"""

    def test_cleanup_expired_removes_old_entries(self):
        """cleanup_expired() removes expired entries"""
        cache = SearchResultCache(ttl_seconds=1)

        cache.put("q1", 5, None, [{"id": "1"}])

        time.sleep(1.1)

        count = cache.cleanup_expired()

        assert count == 1
        assert cache.get("q1", 5, None) is None

    def test_cleanup_keeps_valid_entries(self):
        """cleanup_expired() keeps entries that haven't expired"""
        cache = SearchResultCache(ttl_seconds=10)

        cache.put("q1", 5, None, [{"id": "1"}])

        count = cache.cleanup_expired()

        assert count == 0
        assert cache.get("q1", 5, None) == [{"id": "1"}]

    def test_cleanup_mixed_expired_valid(self):
        """cleanup_expired() correctly handles mix of expired and valid"""
        cache = SearchResultCache(ttl_seconds=1)

        cache.put("q1", 5, None, [{"id": "1"}])

        time.sleep(1.1)

        cache.put("q2", 5, None, [{"id": "2"}])  # Fresh entry

        count = cache.cleanup_expired()

        assert count == 1
        assert cache.get("q1", 5, None) is None
        assert cache.get("q2", 5, None) == [{"id": "2"}]


class TestSearchCacheThreadSafety:
    """Test thread-safety of cache operations"""

    def test_concurrent_puts_and_gets(self):
        """Concurrent operations don't corrupt cache"""
        import threading

        cache = SearchResultCache()

        def put_and_get(thread_id):
            for i in range(50):
                cache.put(f"query_{thread_id}_{i}", 5, None, [{"id": str(i)}])
                result = cache.get(f"query_{thread_id}_{i}", 5, None)
                assert result is not None

        threads = [threading.Thread(target=put_and_get, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Cache should have all entries
        assert len(cache._cache) >= 200


class TestSearchCacheKeyGeneration:
    """Test cache key generation"""

    def test_make_key_format(self):
        """Cache key includes all parameters"""
        cache = SearchResultCache()

        key1 = cache._make_key("query", 5, None)
        key2 = cache._make_key("query", 10, None)
        key3 = cache._make_key("query", 5, "proj_123")

        # Keys should be different
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

        # Keys should include all parameters
        assert "query" in key1
        assert "5" in key1
        assert "10" in key2
        assert "proj_123" in key3


class TestSearchCacheRepr:
    """Test string representation"""

    def test_repr_format(self):
        """__repr__ shows useful cache info"""
        cache = SearchResultCache()

        cache.put("query", 5, None, [{"id": "1"}] * 5)

        repr_str = repr(cache)

        assert "SearchResultCache" in repr_str
        assert "size=" in repr_str
        assert "hit_rate=" in repr_str
        assert "ttl=" in repr_str
        assert "memory=" in repr_str


class TestSearchCacheRealWorldScenarios:
    """Test realistic usage patterns"""

    def test_repeated_same_search(self):
        """Same search benefits from cache"""
        cache = SearchResultCache()

        query = "What is system design?"
        results = [{"id": f"doc_{i}", "score": 0.9 - i * 0.01} for i in range(5)]

        cache.put(query, 5, None, results)

        # Simulate repeated searches
        for _ in range(100):
            result = cache.get(query, 5, None)
            assert result == results

        stats = cache.stats()
        assert stats["hits"] == 100
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "100.0%"

    def test_cache_with_project_knowledge_update(self):
        """Cache invalidation on project knowledge update"""
        cache = SearchResultCache()

        # Add searches for a project
        cache.put("query1", 5, "proj_123", [{"id": "1"}])
        cache.put("query2", 5, "proj_123", [{"id": "2"}])
        cache.put("query1", 5, "proj_456", [{"id": "3"}])

        # Project 123's knowledge updated - invalidate its cache
        cache.invalidate_project("proj_123")

        # Project 123 searches are gone
        assert cache.get("query1", 5, "proj_123") is None
        assert cache.get("query2", 5, "proj_123") is None

        # Project 456 searches still cached
        assert cache.get("query1", 5, "proj_456") == [{"id": "3"}]

    def test_cache_with_varying_result_sizes(self):
        """Cache handles results of varying sizes"""
        cache = SearchResultCache()

        small_results = [{"id": "1"}]
        medium_results = [{"id": f"{i}"} for i in range(10)]
        large_results = [{"id": f"{i}", "content": "x" * 500} for i in range(50)]

        cache.put("small", 5, None, small_results)
        cache.put("medium", 5, None, medium_results)
        cache.put("large", 5, None, large_results)

        assert cache.get("small", 5, None) == small_results
        assert cache.get("medium", 5, None) == medium_results
        assert cache.get("large", 5, None) == large_results

    def test_realistic_concurrent_workload(self):
        """Realistic pattern: multiple users searching concurrently"""
        import threading

        cache = SearchResultCache()

        # Pre-populate some searches
        for i in range(100):
            cache.put(f"query_{i}", 5, f"proj_{i % 10}", [{"id": str(j)} for j in range(5)])

        hits = [0]
        hits_lock = threading.Lock()

        def user_session(user_id):
            """Simulate user searching"""
            for _ in range(20):
                # Random search (50% cache hit rate)
                query_id = (user_id + _) % 100
                result = cache.get(f"query_{query_id}", 5, f"proj_{query_id % 10}")

                if result:
                    with hits_lock:
                        hits[0] += 1

        threads = [threading.Thread(target=user_session, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have significant hit rate
        stats = cache.stats()
        hit_rate = float(stats["hit_rate"].replace("%", ""))
        assert hit_rate > 50.0  # Realistic hit rate
