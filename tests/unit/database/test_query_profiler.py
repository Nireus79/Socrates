"""Unit tests for database query performance profiler.

Tests cover:
- Query profiler initialization
- Decorator for sync and async functions
- Statistics collection and aggregation
- Slow query detection
- Performance metrics and reporting
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock

from socratic_system.database.query_profiler import (
    QueryStats,
    QueryProfiler,
    get_profiler,
    profile_query,
)


class TestQueryStats:
    """Test QueryStats class for tracking individual queries."""

    def test_stats_initialization(self):
        """Test QueryStats initializes with correct defaults."""
        stats = QueryStats("test_query")

        assert stats.name == "test_query"
        assert stats.count == 0
        assert stats.total_time == 0.0
        assert stats.min_time == float("inf")
        assert stats.max_time == 0.0
        assert stats.slow_count == 0
        assert stats.error_count == 0

    def test_add_execution_success(self):
        """Test recording successful query execution."""
        stats = QueryStats("test_query")

        stats.add_execution(0.05, is_slow=False, error=False)

        assert stats.count == 1
        assert stats.total_time == 0.05
        assert stats.min_time == 0.05
        assert stats.max_time == 0.05
        assert stats.slow_count == 0
        assert stats.error_count == 0

    def test_add_execution_multiple(self):
        """Test recording multiple executions."""
        stats = QueryStats("test_query")

        stats.add_execution(0.05)
        stats.add_execution(0.10)
        stats.add_execution(0.07)

        assert stats.count == 3
        assert stats.total_time == 0.22
        assert stats.min_time == 0.05
        assert stats.max_time == 0.10

    def test_add_execution_slow(self):
        """Test recording slow query execution."""
        stats = QueryStats("test_query")

        stats.add_execution(0.15, is_slow=True)
        stats.add_execution(0.05, is_slow=False)

        assert stats.count == 2
        assert stats.slow_count == 1

    def test_add_execution_error(self):
        """Test recording query with error."""
        stats = QueryStats("test_query")

        stats.add_execution(0.02, error=True)
        stats.add_execution(0.05, error=False)

        assert stats.count == 2
        assert stats.error_count == 1

    def test_avg_time_ms_property(self):
        """Test average time calculation in milliseconds."""
        stats = QueryStats("test_query")

        stats.add_execution(0.100)
        stats.add_execution(0.200)

        assert stats.avg_time_ms == 150.0

    def test_slow_percentage_property(self):
        """Test slow query percentage calculation."""
        stats = QueryStats("test_query")

        stats.add_execution(0.150, is_slow=True)
        stats.add_execution(0.050, is_slow=False)
        stats.add_execution(0.150, is_slow=True)

        assert stats.slow_percentage == pytest.approx(66.67, rel=0.1)

    def test_to_dict_representation(self):
        """Test converting stats to dictionary."""
        stats = QueryStats("test_query")

        stats.add_execution(0.100)
        stats.add_execution(0.200)
        stats.add_execution(0.150, is_slow=True)

        stats_dict = stats.to_dict()

        assert stats_dict["name"] == "test_query"
        assert stats_dict["count"] == 3
        assert stats_dict["slow_count"] == 1
        assert "avg_time_ms" in stats_dict
        assert "min_time_ms" in stats_dict
        assert "max_time_ms" in stats_dict


class TestQueryProfiler:
    """Test QueryProfiler class for tracking all queries."""

    def test_profiler_initialization(self):
        """Test QueryProfiler initializes with correct defaults."""
        profiler = QueryProfiler(slow_query_threshold_ms=100)

        assert profiler.slow_query_threshold == 0.1
        assert len(profiler.stats) == 0

    def test_profile_async_function(self):
        """Test profiling async function."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("async_query")
        async def async_function():
            await asyncio.sleep(0.01)
            return "result"

        # Function should be wrapped
        assert asyncio.iscoroutinefunction(async_function)

    def test_profile_sync_function(self):
        """Test profiling sync function."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("sync_query")
        def sync_function():
            time.sleep(0.01)
            return "result"

        # Function should be wrapped
        assert not asyncio.iscoroutinefunction(sync_function)

    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """Test executing profiled async function."""
        profiler = QueryProfiler(slow_query_threshold_ms=100)

        @profiler.profile("test_async")
        async def async_query():
            await asyncio.sleep(0.01)
            return "success"

        result = await async_query()

        assert result == "success"
        assert "test_async" in profiler.stats
        assert profiler.stats["test_async"].count == 1

    def test_sync_function_execution(self):
        """Test executing profiled sync function."""
        profiler = QueryProfiler(slow_query_threshold_ms=100)

        @profiler.profile("test_sync")
        def sync_query():
            time.sleep(0.01)
            return "success"

        result = sync_query()

        assert result == "success"
        assert "test_sync" in profiler.stats
        assert profiler.stats["test_sync"].count == 1

    @pytest.mark.asyncio
    async def test_slow_async_query_detection(self):
        """Test detecting slow async queries."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("slow_async")
        async def slow_query():
            await asyncio.sleep(0.1)
            return "result"

        await slow_query()

        assert profiler.stats["slow_async"].slow_count == 1

    def test_slow_sync_query_detection(self):
        """Test detecting slow sync queries."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("slow_sync")
        def slow_query():
            time.sleep(0.1)
            return "result"

        slow_query()

        assert profiler.stats["slow_sync"].slow_count == 1

    @pytest.mark.asyncio
    async def test_async_query_error_tracking(self):
        """Test tracking errors in async queries."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("failing_async")
        async def failing_query():
            raise ValueError("Query failed")

        with pytest.raises(ValueError):
            await failing_query()

        assert profiler.stats["failing_async"].error_count == 1

    def test_sync_query_error_tracking(self):
        """Test tracking errors in sync queries."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("failing_sync")
        def failing_query():
            raise ValueError("Query failed")

        with pytest.raises(ValueError):
            failing_query()

        assert profiler.stats["failing_sync"].error_count == 1

    def test_manual_tracking(self):
        """Test manually tracking queries without decorator."""
        profiler = QueryProfiler()

        profiler.manual_track("manual_query", duration=0.05)
        profiler.manual_track("manual_query", duration=0.15, is_slow=True)

        assert profiler.stats["manual_query"].count == 2
        assert profiler.stats["manual_query"].slow_count == 1

    def test_get_stats(self):
        """Test getting all statistics."""
        profiler = QueryProfiler(slow_query_threshold_ms=100)

        @profiler.profile("query1")
        def query1():
            time.sleep(0.01)

        @profiler.profile("query2")
        def query2():
            time.sleep(0.01)

        query1()
        query2()

        stats = profiler.get_stats()

        assert len(stats) == 2
        assert "query1" in stats
        assert "query2" in stats

    def test_get_slow_queries(self):
        """Test getting queries with slow executions."""
        profiler = QueryProfiler(slow_query_threshold_ms=50)

        @profiler.profile("slow_query")
        def slow_query():
            time.sleep(0.1)

        @profiler.profile("fast_query")
        def fast_query():
            time.sleep(0.01)

        # Execute slow query multiple times
        for _ in range(3):
            slow_query()

        # Execute fast query
        fast_query()

        slow_queries = profiler.get_slow_queries(min_slow_count=1)

        assert len(slow_queries) == 1
        assert slow_queries[0]["name"] == "slow_query"
        assert slow_queries[0]["slow_count"] == 3

    def test_get_slowest_queries(self):
        """Test getting slowest queries by average time."""
        profiler = QueryProfiler(slow_query_threshold_ms=1)

        profiler.manual_track("query1", 0.100)
        profiler.manual_track("query2", 0.050)
        profiler.manual_track("query3", 0.200)

        slowest = profiler.get_slowest_queries(limit=2)

        assert len(slowest) == 2
        assert slowest[0]["name"] == "query3"
        assert slowest[1]["name"] == "query1"

    def test_reset_stats_all(self):
        """Test resetting all statistics."""
        profiler = QueryProfiler()

        profiler.manual_track("query1", 0.05)
        profiler.manual_track("query2", 0.05)

        assert len(profiler.stats) == 2

        profiler.reset_stats()

        assert len(profiler.stats) == 0

    def test_reset_stats_single(self):
        """Test resetting statistics for single query."""
        profiler = QueryProfiler()

        profiler.manual_track("query1", 0.05)
        profiler.manual_track("query2", 0.05)

        profiler.reset_stats("query1")

        assert len(profiler.stats) == 1
        assert "query1" not in profiler.stats
        assert "query2" in profiler.stats


class TestModuleLevelProfiler:
    """Test module-level profiler functions."""

    def test_get_global_profiler(self):
        """Test getting global profiler instance."""
        profiler = get_profiler()

        assert profiler is not None
        assert isinstance(profiler, QueryProfiler)

    def test_profile_query_decorator(self):
        """Test module-level profile_query decorator."""

        @profile_query("decorated_query")
        def decorated_function():
            return "result"

        result = decorated_function()

        assert result == "result"

        profiler = get_profiler()
        assert "decorated_query" in profiler.stats
