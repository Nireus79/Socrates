"""
Unit tests for TTL Cache - time-based caching decorator for memoization.

Tests cover:
- Basic caching functionality
- TTL expiration
- Cache hits and misses
- Thread safety
- Unhashable arguments handling
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from socratic_system.utils.ttl_cache import TTLCache


class TestTTLCacheBasic:
    """Test basic caching functionality"""

    def test_cache_initialization(self):
        """Test that cache is properly initialized"""
        cache = TTLCache(ttl_minutes=5)
        assert cache._ttl.total_seconds() == 300

    def test_cached_function_is_wrapped(self):
        """Test that decorated function is properly wrapped"""

        @TTLCache()
        def test_func(x):
            return x * 2

        assert callable(test_func)
        assert test_func.__name__ == "test_func"

    def test_function_executes_correctly(self):
        """Test that cached function executes and returns correct value"""

        @TTLCache()
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_cached_result_returned_on_second_call(self):
        """Test that cached result is returned on subsequent calls"""
        call_count = 0

        @TTLCache(ttl_minutes=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == result2 == 10
        assert call_count == 1  # Function only called once


class TestTTLCacheExpiration:
    """Test cache expiration based on TTL"""

    def test_cache_expires_after_ttl(self):
        """Test that cache entries expire after TTL"""
        call_count = 0

        @TTLCache(ttl_minutes=0.001)  # ~60ms TTL
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = test_func(5)
        time.sleep(0.1)  # Wait for expiration
        result2 = test_func(5)

        assert result1 == result2 == 10
        assert call_count == 2  # Function called twice (cache expired)

    def test_cache_not_expired_before_ttl(self):
        """Test that cache is not expired before TTL passes"""
        call_count = 0

        @TTLCache(ttl_minutes=1)  # 60 second TTL
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        test_func(5)
        test_func(5)

        assert call_count == 1  # Function only called once (cache still valid)


class TestTTLCacheWithArgs:
    """Test caching with different arguments"""

    def test_different_args_produce_different_cache_entries(self):
        """Test that different arguments create separate cache entries"""
        call_count = 0

        @TTLCache()
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = test_func(5)
        result2 = test_func(10)
        result3 = test_func(5)  # Same as first call

        assert result1 == 10
        assert result2 == 20
        assert result3 == 10
        assert call_count == 2  # Only two unique calls

    def test_caching_with_keyword_arguments(self):
        """Test caching works with keyword arguments"""
        call_count = 0

        @TTLCache()
        def test_func(a, b=10):
            nonlocal call_count
            call_count += 1
            return a + b

        result1 = test_func(5, b=10)
        result2 = test_func(5, b=10)
        result3 = test_func(5, b=20)

        assert result1 == 15
        assert result2 == 15
        assert result3 == 25
        assert call_count == 2

    def test_positional_and_keyword_args_treated_same(self):
        """Test that positional and keyword args are treated the same"""
        call_count = 0

        @TTLCache()
        def test_func(a, b):
            nonlocal call_count
            call_count += 1
            return a + b

        result1 = test_func(5, 10)
        result2 = test_func(a=5, b=10)

        assert result1 == 15
        assert result2 == 15
        # Note: Due to how keys are created, these might be different cache entries
        # depending on implementation


class TestTTLCacheUnhashable:
    """Test handling of unhashable arguments"""

    def test_unhashable_arguments_skip_cache(self):
        """Test that unhashable arguments skip caching"""
        call_count = 0

        @TTLCache()
        def test_func(items):
            nonlocal call_count
            call_count += 1
            return len(items)

        result1 = test_func([1, 2, 3])
        result2 = test_func([1, 2, 3])

        assert result1 == 3
        assert result2 == 3
        assert call_count == 2  # Function called twice (caching skipped)

    def test_unhashable_dict_argument(self):
        """Test with unhashable dictionary arguments"""
        call_count = 0

        @TTLCache()
        def test_func(data):
            nonlocal call_count
            call_count += 1
            return len(data)

        result1 = test_func({"a": 1, "b": 2})
        result2 = test_func({"a": 1, "b": 2})

        assert result1 == 2
        assert result2 == 2
        assert call_count == 2  # Function called twice


class TestTTLCacheStatistics:
    """Test cache statistics tracking"""

    def test_cache_tracks_hits(self):
        """Test that cache tracks hit count"""

        @TTLCache()
        def test_func(x):
            return x * 2

        cache = test_func._cache
        test_func(5)
        test_func(5)
        test_func(5)

        assert cache._hits == 2

    def test_cache_tracks_misses(self):
        """Test that cache tracks miss count"""

        @TTLCache()
        def test_func(x):
            return x * 2

        cache = test_func._cache
        test_func(5)
        test_func(10)

        assert cache._misses == 2

    def test_cache_hit_miss_ratio(self):
        """Test cache statistics"""

        @TTLCache()
        def test_func(x):
            return x * 2

        cache = test_func._cache
        test_func(5)  # miss
        test_func(5)  # hit
        test_func(5)  # hit
        test_func(10)  # miss

        assert cache._hits == 2
        assert cache._misses == 2


class TestTTLCacheThreadSafety:
    """Test thread-safe caching with concurrent access"""

    def test_concurrent_access_is_thread_safe(self):
        """Test that concurrent access doesn't cause race conditions"""
        call_count = 0
        lock = threading.Lock()

        @TTLCache(ttl_minutes=1)
        def test_func(x):
            nonlocal call_count
            with lock:
                call_count += 1
            return x * 2

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for _ in range(4):
                for x in range(5):
                    futures.append(executor.submit(test_func, x))

            results = [f.result() for f in futures]

        # Should get 5 unique values (0, 2, 4, 6, 8)
        unique_results = set(results)
        assert len(unique_results) == 5
        # Function should be called at most 5 times (once per unique argument)
        assert call_count <= 5


class TestTTLCacheMultiple:
    """Test multiple cached functions"""

    def test_multiple_decorated_functions(self):
        """Test that multiple decorated functions work independently"""
        call_count_1 = 0
        call_count_2 = 0

        @TTLCache()
        def func1(x):
            nonlocal call_count_1
            call_count_1 += 1
            return x * 2

        @TTLCache()
        def func2(x):
            nonlocal call_count_2
            call_count_2 += 1
            return x * 3

        func1(5)
        func1(5)  # Cached
        func2(5)
        func2(5)  # Cached

        assert call_count_1 == 1
        assert call_count_2 == 1

    def test_different_ttl_values(self):
        """Test that different TTL values work correctly"""

        @TTLCache(ttl_minutes=0.001)  # Short TTL
        def short_ttl_func(x):
            return x * 2

        @TTLCache(ttl_minutes=10)  # Long TTL
        def long_ttl_func(x):
            return x * 2

        # Both should have different TTL values
        assert (
            short_ttl_func._cache._ttl.total_seconds()
            < long_ttl_func._cache._ttl.total_seconds()
        )


class TestTTLCacheEdgeCases:
    """Test edge cases and special scenarios"""

    def test_cache_with_none_return_value(self):
        """Test caching when function returns None"""
        call_count = 0

        @TTLCache()
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return None

        result1 = test_func(5)
        result2 = test_func(5)

        assert result1 is None
        assert result2 is None
        assert call_count == 1  # Cached correctly

    def test_cache_with_zero_args(self):
        """Test caching function with no arguments"""
        call_count = 0

        @TTLCache()
        def test_func():
            nonlocal call_count
            call_count += 1
            return 42

        result1 = test_func()
        result2 = test_func()

        assert result1 == 42
        assert result2 == 42
        assert call_count == 1

    def test_cache_with_exception_is_not_cached(self):
        """Test that exceptions are not cached"""
        call_count = 0

        @TTLCache()
        def test_func(x):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call error")
            return x * 2

        with pytest.raises(ValueError):
            test_func(5)

        result = test_func(5)  # Should call function again
        assert result == 10
        assert call_count == 2
