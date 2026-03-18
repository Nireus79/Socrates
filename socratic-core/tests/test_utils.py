"""Tests for socratic_core.utils module."""

import time
from datetime import datetime

import pytest

from socratic_core.utils import ProjectIDGenerator, UserIDGenerator, cached


class TestProjectIDGenerator:
    """Tests for ProjectIDGenerator."""

    def test_generate_project_id(self):
        """Test generating a project ID."""
        project_id = ProjectIDGenerator.generate()
        assert project_id is not None
        assert len(project_id) > 0

    def test_project_id_format(self):
        """Test project ID follows expected format."""
        project_id = ProjectIDGenerator.generate()
        # Should start with 'proj_'
        assert project_id.startswith("proj_")

    def test_project_id_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [ProjectIDGenerator.generate() for _ in range(100)]
        assert len(ids) == len(set(ids))  # All unique

    def test_project_id_is_string(self):
        """Test that project ID is a string."""
        project_id = ProjectIDGenerator.generate()
        assert isinstance(project_id, str)

    def test_project_id_length(self):
        """Test project ID has reasonable length."""
        project_id = ProjectIDGenerator.generate()
        assert 10 < len(project_id) < 100

    def test_multiple_generations(self):
        """Test generating multiple IDs in succession."""
        id1 = ProjectIDGenerator.generate()
        id2 = ProjectIDGenerator.generate()
        id3 = ProjectIDGenerator.generate()

        assert id1 != id2 != id3


class TestUserIDGenerator:
    """Tests for UserIDGenerator."""

    def test_generate_user_id(self):
        """Test generating a user ID."""
        user_id = UserIDGenerator.generate()
        assert user_id is not None
        assert len(user_id) > 0

    def test_user_id_format(self):
        """Test user ID follows expected format."""
        user_id = UserIDGenerator.generate()
        # Should start with 'user_'
        assert user_id.startswith("user_")

    def test_user_id_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [UserIDGenerator.generate() for _ in range(100)]
        assert len(ids) == len(set(ids))  # All unique

    def test_user_id_is_string(self):
        """Test that user ID is a string."""
        user_id = UserIDGenerator.generate()
        assert isinstance(user_id, str)

    def test_user_id_length(self):
        """Test user ID has reasonable length."""
        user_id = UserIDGenerator.generate()
        assert 10 < len(user_id) < 100

    def test_project_and_user_ids_different(self):
        """Test that project and user IDs are different."""
        project_id = ProjectIDGenerator.generate()
        user_id = UserIDGenerator.generate()

        assert project_id != user_id
        assert project_id.startswith("proj_")
        assert user_id.startswith("user_")


class TestCachedDecorator:
    """Tests for cached decorator."""

    def test_cached_basic(self):
        """Test basic caching functionality."""
        call_count = 0

        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should use cache

    def test_cached_different_arguments(self):
        """Test caching with different arguments."""
        call_count = 0

        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        assert call_count == 1

        result2 = expensive_function(10)
        assert call_count == 2  # Different arg, should call again

    def test_cached_ttl_expiration(self):
        """Test cache TTL expiration."""
        call_count = 0

        @cached(ttl=1)  # 1 second TTL
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        assert call_count == 1

        time.sleep(1.1)

        result2 = expensive_function(5)
        assert call_count == 2  # Cache expired

    def test_cached_with_kwargs(self):
        """Test caching with keyword arguments."""
        call_count = 0

        @cached(ttl=60)
        def function(a, b=10):
            nonlocal call_count
            call_count += 1
            return a + b

        result1 = function(5, b=10)
        assert call_count == 1

        result2 = function(5, b=10)
        assert call_count == 1  # Should use cache

        result3 = function(5, b=20)
        assert call_count == 2  # Different kwargs

    def test_cached_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @cached(ttl=60)
        def my_function():
            return 42

        assert my_function.__name__ == "my_function"

    def test_cached_with_none_result(self):
        """Test caching None results."""
        call_count = 0

        @cached(ttl=60)
        def returns_none():
            nonlocal call_count
            call_count += 1
            return None

        result1 = returns_none()
        assert result1 is None
        assert call_count == 1

        result2 = returns_none()
        assert result2 is None
        assert call_count == 1  # Should use cache even for None

    def test_cached_with_exception(self):
        """Test that exceptions aren't cached."""
        call_count = 0

        @cached(ttl=60)
        def raises_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Error")
            return "success"

        with pytest.raises(ValueError):
            raises_error()

        result = raises_error()
        assert result == "success"
        assert call_count == 2

    def test_cache_multiple_arguments(self):
        """Test caching with multiple arguments."""
        call_count = 0

        @cached(ttl=60)
        def function(a, b, c):
            nonlocal call_count
            call_count += 1
            return a + b + c

        result1 = function(1, 2, 3)
        assert result1 == 6
        assert call_count == 1

        result2 = function(1, 2, 3)
        assert call_count == 1

        result3 = function(1, 2, 4)
        assert call_count == 2

    def test_cache_string_arguments(self):
        """Test caching with string arguments."""
        call_count = 0

        @cached(ttl=60)
        def concat(a, b):
            nonlocal call_count
            call_count += 1
            return a + b

        result1 = concat("hello", "world")
        assert call_count == 1

        result2 = concat("hello", "world")
        assert call_count == 1

        result3 = concat("hello", "there")
        assert call_count == 2

    def test_cache_list_arguments(self):
        """Test caching with unhashable arguments fails gracefully."""
        call_count = 0

        @cached(ttl=60)
        def process_list(lst):
            nonlocal call_count
            call_count += 1
            return len(lst)

        # Lists aren't hashable, so caching won't work
        # This tests that the decorator handles it gracefully
        result1 = process_list([1, 2, 3])
        result2 = process_list([1, 2, 3])
        # Even if cache doesn't work, should return correct result
        assert result1 == 3
        assert result2 == 3


class TestIDGeneratorThreadSafety:
    """Tests for thread safety of ID generators."""

    def test_project_id_concurrent_generation(self):
        """Test that concurrent ID generation produces unique IDs."""
        import threading

        ids = []
        lock = threading.Lock()

        def generate_ids():
            for _ in range(10):
                id = ProjectIDGenerator.generate()
                with lock:
                    ids.append(id)

        threads = [threading.Thread(target=generate_ids) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_user_id_concurrent_generation(self):
        """Test that concurrent user ID generation produces unique IDs."""
        import threading

        ids = []
        lock = threading.Lock()

        def generate_ids():
            for _ in range(10):
                id = UserIDGenerator.generate()
                with lock:
                    ids.append(id)

        threads = [threading.Thread(target=generate_ids) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All IDs should be unique
        assert len(ids) == len(set(ids))
