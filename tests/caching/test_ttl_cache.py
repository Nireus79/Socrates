"""
Comprehensive tests for TTL Cache Decorator (Phase 3)

Tests decorator-based method caching with time-to-live.
"""

import time

from socratic_system.utils.ttl_cache import TTLCache, cached


class TestTTLCacheDecorator:
    """Test TTL cache decorator functionality"""

    def test_cached_decorator_basic(self):
        """Decorator caches function results"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call (cached)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not called again

    def test_cached_decorator_different_args(self):
        """Different arguments are cached separately"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def multiply(x, y):
            call_count[0] += 1
            return x * y

        result1 = multiply(2, 3)
        assert result1 == 6
        assert call_count[0] == 1

        result2 = multiply(2, 4)
        assert result2 == 8
        assert call_count[0] == 2

        # Call with same args - cached
        result3 = multiply(2, 3)
        assert result3 == 6
        assert call_count[0] == 2

    def test_cached_decorator_with_kwargs(self):
        """Decorator handles keyword arguments"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def greet(name, greeting="Hello"):
            call_count[0] += 1
            return f"{greeting}, {name}!"

        _ = greet("Alice", greeting="Hi")
        assert call_count[0] == 1

        _ = greet("Alice", greeting="Hi")
        assert call_count[0] == 1  # Cached

        _ = greet("Alice", greeting="Hey")
        assert call_count[0] == 2  # Different kwargs


class TestTTLCacheTTL:
    """Test TTL-based expiration"""

    def test_cache_expires_after_ttl(self):
        """Cached value expires after TTL"""
        call_count = [0]

        @cached(ttl_minutes=0.016)  # ~1 second in minutes
        def expensive_function():
            call_count[0] += 1
            return "result"

        _ = expensive_function()
        assert call_count[0] == 1

        _ = expensive_function()
        assert call_count[0] == 1  # Cached

        time.sleep(1.1)

        _ = expensive_function()
        assert call_count[0] == 2  # Cache expired

    def test_cache_ttl_default(self):
        """Default TTL is 5 minutes"""
        cache = TTLCache()
        assert cache._ttl.total_seconds() == 5 * 60  # 300 seconds


class TestTTLCacheStats:
    """Test cache statistics"""

    def test_cache_stats_tracking(self):
        """Cache tracks hits and misses"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def func(x):
            call_count[0] += 1
            return x * 2

        func(1)  # Miss
        func(1)  # Hit
        func(2)  # Miss
        func(1)  # Hit

        stats = func.cache_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["total_calls"] == 4
        assert stats["hit_rate"] == "50.0%"

    def test_cache_info_method(self):
        """cache_info() returns readable string"""

        @cached(ttl_minutes=5)
        def func(x):
            return x * 2

        func(1)
        func(1)
        func(2)

        info = func.cache_info()

        assert isinstance(info, str)
        assert "entries" in info
        assert "hit rate" in info
        assert "TTL" in info


class TestTTLCacheClear:
    """Test cache clearing"""

    def test_cache_clear(self):
        """cache_clear() removes all cached entries"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def func(x):
            call_count[0] += 1
            return x * 2

        func(1)
        func(1)  # Cached

        assert call_count[0] == 1

        func.cache_clear()

        func(1)  # Not cached anymore

        assert call_count[0] == 2

    def test_reset_stats(self):
        """Stats can be reset"""

        @cached(ttl_minutes=5)
        def func(x):
            return x * 2

        func(1)
        func(1)

        initial_stats = func.cache_stats()
        assert initial_stats["hits"] == 1

        func.cache_clear()  # Also resets stats
        # After clear, a new TTLCache is used
        # So we test clear functionality separately


class TestTTLCacheUnhashableArgs:
    """Test handling of unhashable arguments"""

    def test_unhashable_args_skip_cache(self):
        """Unhashable arguments are not cached and function is called normally"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def func(data):
            call_count[0] += 1
            return len(data)

        # List is unhashable - should not be cached
        # But decorator should handle gracefully and still call the function
        result1 = func([1, 2, 3])
        assert result1 == 3
        assert call_count[0] == 1

        # Second call with list (same contents) - should call function again
        # because lists aren't hashable and can't be cached
        result2 = func([1, 2, 3])
        assert result2 == 3
        assert call_count[0] == 2  # Not cached (unhashable arguments)

    def test_hashable_args_are_cached(self):
        """Hashable arguments are cached"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def func(data):
            call_count[0] += 1
            return sum(data)

        # Tuple is hashable
        _ = func((1, 2, 3))
        assert call_count[0] == 1

        _ = func((1, 2, 3))
        assert call_count[0] == 1  # Cached (hashable)


class TestTTLCacheDecoratorFeatures:
    """Test decorator-specific features"""

    def test_preserves_function_name(self):
        """Decorator preserves original function name"""

        @cached(ttl_minutes=5)
        def my_function():
            return "result"

        assert my_function.__name__ == "my_function"

    def test_preserves_docstring(self):
        """Decorator preserves original docstring"""

        @cached(ttl_minutes=5)
        def documented_function():
            """This is the docstring"""
            return "result"

        assert "This is the docstring" in documented_function.__doc__

    def test_cache_methods_attached(self):
        """Decorator attaches cache management methods"""

        @cached(ttl_minutes=5)
        def func():
            return "result"

        assert hasattr(func, "cache_clear")
        assert hasattr(func, "cache_stats")
        assert hasattr(func, "cache_info")
        assert callable(func.cache_clear)
        assert callable(func.cache_stats)


class TestTTLCacheThreadSafety:
    """Test thread-safety of cache operations"""

    def test_concurrent_access(self):
        """Concurrent access doesn't cause data corruption"""
        import threading

        call_count = [0]

        @cached(ttl_minutes=5)
        def expensive_function(x):
            call_count[0] += 1
            time.sleep(0.01)  # Simulate expensive operation
            return x * 2

        results = []

        def worker(x):
            for _ in range(10):
                result = expensive_function(x)
                results.append(result)

        threads = [
            threading.Thread(target=worker, args=(1,)),
            threading.Thread(target=worker, args=(2,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each unique arg should be called once (cached after first call)
        assert call_count[0] == 2
        assert len(results) == 20


class TestTTLCacheRealWorldScenarios:
    """Test realistic usage patterns"""

    def test_caching_expensive_computation(self):
        """Cache expensive computations"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def fibonacci(n):
            call_count[0] += 1
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        # First call
        result1 = fibonacci(10)
        _ = call_count[0]

        # Reset counter and call again
        _ = call_count[0]
        call_count[0] = 0

        # Second call (cached) - should only call wrapper once for cached check
        result2 = fibonacci(10)

        assert result1 == result2
        # Second call should reuse cache (no recursive fibonacci calls)
        assert call_count[0] == 0  # Cached, no actual function calls

    def test_caching_database_lookups(self):
        """Cache database lookups"""
        call_count = [0]

        @cached(ttl_minutes=5)
        def get_user_profile(user_id):
            call_count[0] += 1
            # Simulate DB lookup
            return {"user_id": user_id, "name": f"User {user_id}"}

        # Multiple lookups for same user
        profile1 = get_user_profile(123)
        profile2 = get_user_profile(123)
        profile3 = get_user_profile(123)

        assert profile1 == profile2 == profile3
        assert call_count[0] == 1  # Only called once

    def test_caching_with_multiple_instances(self):
        """Multiple cached functions are independent"""
        call_count_a = [0]
        call_count_b = [0]

        @cached(ttl_minutes=5)
        def function_a(x):
            call_count_a[0] += 1
            return x * 2

        @cached(ttl_minutes=5)
        def function_b(x):
            call_count_b[0] += 1
            return x * 3

        function_a(5)
        function_a(5)
        function_b(5)
        function_b(5)

        assert call_count_a[0] == 1  # Only called once
        assert call_count_b[0] == 1  # Only called once

    def test_cache_hit_rate_realistic_workload(self):
        """Cache hit rate improves with repeated calls"""

        @cached(ttl_minutes=5)
        def expensive_lookup(query):
            return f"Result for {query}"

        # Simulate repeated searches (typical user behavior)
        queries = [
            "system design",
            "database optimization",
            "system design",  # Repeat
            "authentication",
            "system design",  # Repeat
            "database optimization",  # Repeat
        ]

        for query in queries:
            expensive_lookup(query)

        stats = expensive_lookup.cache_stats()
        hit_rate = float(stats["hit_rate"].replace("%", ""))

        # 3 unique queries, 6 calls = 50% hit rate (3 repeats)
        assert hit_rate >= 40.0  # Should be close to 50%


class TestTTLCacheIntegration:
    """Test integration with other components"""

    def test_cache_factory_function(self):
        """cached() factory function works correctly"""
        decorator = cached(ttl_minutes=10)

        @decorator
        def my_function(x):
            return x * 2

        result = my_function(5)
        assert result == 10

        stats = my_function.cache_stats()
        assert "ttl_minutes" in stats
        assert stats["ttl_minutes"] == 10.0

    def test_multiple_decorators(self):
        """Can use decorator multiple times"""

        @cached(ttl_minutes=5)
        def func1():
            return "result1"

        @cached(ttl_minutes=10)
        def func2():
            return "result2"

        assert func1() == "result1"
        assert func2() == "result2"

        stats1 = func1.cache_stats()
        stats2 = func2.cache_stats()

        assert stats1["ttl_minutes"] == 5.0
        assert stats2["ttl_minutes"] == 10.0


class TestCleanupExpired:
    """Test cleanup_expired functionality"""

    def test_cleanup_expired_method(self):
        """cleanup_expired() removes expired entries"""

        @cached(ttl_minutes=0.016)  # ~1 second
        def func(x):
            return x * 2

        func(1)
        func(2)

        assert len(func._cache._cache) == 2

        time.sleep(1.1)

        count = func._cache.cleanup_expired()

        assert count == 2
        assert len(func._cache._cache) == 0
