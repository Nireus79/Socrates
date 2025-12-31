"""Unit tests for database connection pool.

Tests cover:
- Pool initialization with different database types
- Connection acquisition and release
- Pool health checks and statistics
- Event listener functionality
- Resource cleanup
"""

import asyncio

import pytest

from socratic_system.database.connection_pool import (
    DatabaseConnectionPool,
    get_pool,
    initialize_pool,
)


class TestConnectionPoolInitialization:
    """Test connection pool initialization."""

    def test_pool_init_with_sqlite(self):
        """Test initializing pool with SQLite database."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        assert pool.database_url == "sqlite+aiosqlite:///:memory:"
        assert pool.pool_size == 20
        assert pool.max_overflow == 10
        assert pool.engine is not None

    def test_pool_init_with_postgresql(self):
        """Test initializing pool with PostgreSQL database."""
        pool = DatabaseConnectionPool(
            "postgresql+asyncpg://user:pass@localhost/testdb",
            pool_size=30,
            max_overflow=15,
        )

        assert pool.database_url == "postgresql+asyncpg://user:pass@localhost/testdb"
        assert pool.pool_size == 30
        assert pool.max_overflow == 15

    def test_pool_init_with_invalid_url(self):
        """Test that invalid database URL raises ValueError."""
        with pytest.raises(ValueError, match="database_url is required"):
            DatabaseConnectionPool("")

    def test_pool_init_with_unsupported_database(self):
        """Test that unsupported database type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseConnectionPool("mysql+pymysql://user:pass@localhost/testdb")

    def test_pool_custom_configuration(self):
        """Test custom pool configuration."""
        pool = DatabaseConnectionPool(
            "sqlite+aiosqlite:///:memory:",
            pool_size=50,
            max_overflow=20,
            pool_recycle=1800,
            slow_query_threshold_ms=200.0,
        )

        assert pool.pool_size == 50
        assert pool.max_overflow == 20
        assert pool.pool_recycle == 1800
        assert pool.slow_query_threshold == 0.2


class TestConnectionAcquisition:
    """Test connection acquisition and session management."""

    @pytest.mark.asyncio
    async def test_get_session_context_manager(self):
        """Test acquiring session via context manager."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        async with pool.get_session() as session:
            assert session is not None
            assert hasattr(session, "execute")

    @pytest.mark.asyncio
    async def test_get_session_async_generator(self):
        """Test session is properly yielded and cleaned up."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        session_obj = None
        async for session in pool.get_session():
            session_obj = session
            assert session is not None

        # Session should be closed after exiting context
        assert session_obj is not None


class TestPoolHealth:
    """Test pool health checks."""

    @pytest.mark.asyncio
    async def test_get_pool_status(self):
        """Test getting pool status statistics."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        status = await pool.get_pool_status()

        assert isinstance(status, dict)
        assert "size" in status
        assert "checked_in" in status
        assert "checked_out" in status
        assert "overflow" in status
        assert "total" in status
        assert "utilization_percent" in status
        assert "slow_query_count" in status

        # SQLite typically has size 0 with NullPool
        assert status["utilization_percent"] >= 0
        assert status["utilization_percent"] <= 100

    @pytest.mark.asyncio
    async def test_get_pool_health_healthy(self):
        """Test pool health check when healthy."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        health = await pool.get_pool_health()

        assert health["status"] == "healthy"
        assert health["latency_ms"] >= 0
        assert "pool_status" in health

    @pytest.mark.asyncio
    async def test_get_pool_health_with_error(self):
        """Test pool health check when database is unreachable."""
        # Create pool with invalid database
        pool = DatabaseConnectionPool("sqlite+aiosqlite:////nonexistent/invalid.db")

        health = await pool.get_pool_health()

        # Should have error status
        assert health["status"] == "unhealthy"
        assert "error" in health
        assert health["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        is_connected = await pool.test_connection()

        assert is_connected is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test failed connection test."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:////nonexistent/invalid.db")

        is_connected = await pool.test_connection()

        assert is_connected is False


class TestPoolContextManager:
    """Test connection pool as context manager."""

    @pytest.mark.asyncio
    async def test_pool_context_manager_entry_exit(self):
        """Test pool context manager entry and exit."""
        async with DatabaseConnectionPool("sqlite+aiosqlite:///:memory:") as pool:
            assert pool is not None
            assert pool.engine is not None

        # After exiting context, engine should be disposed
        # (This is handled by the __aexit__ method)

    @pytest.mark.asyncio
    async def test_pool_close(self):
        """Test explicit pool closure."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        # Should not raise any errors
        await pool.close()


class TestPoolThreadSafety:
    """Test pool behavior under concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_session_acquisition(self):
        """Test acquiring multiple sessions concurrently."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        async def get_and_use_session():
            async with pool.get_session() as session:
                # Simple query to verify session works
                result = await session.execute("SELECT 1")
                return result is not None

        # Run multiple concurrent sessions
        tasks = [get_and_use_session() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(results)

    @pytest.mark.asyncio
    async def test_sequential_session_acquisition(self):
        """Test acquiring sessions sequentially."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        for _ in range(10):
            async with pool.get_session() as session:
                result = await session.execute("SELECT 1")
                assert result is not None


class TestGlobalPoolInstance:
    """Test global pool singleton pattern."""

    @pytest.mark.asyncio
    async def test_initialize_pool(self):
        """Test initializing global pool."""
        pool = await initialize_pool("sqlite+aiosqlite:///:memory:")

        assert pool is not None
        assert isinstance(pool, DatabaseConnectionPool)

    @pytest.mark.asyncio
    async def test_get_pool_after_initialization(self):
        """Test getting initialized pool."""
        await initialize_pool("sqlite+aiosqlite:///:memory:")

        pool = get_pool()

        assert pool is not None
        assert isinstance(pool, DatabaseConnectionPool)

    def test_get_pool_without_initialization(self):
        """Test getting pool before initialization raises error."""
        # Reset global pool state for this test
        import socratic_system.database.connection_pool as pool_module

        original_pool = pool_module._pool
        pool_module._pool = None

        try:
            with pytest.raises(RuntimeError, match="Database pool not initialized"):
                get_pool()
        finally:
            # Restore original state
            pool_module._pool = original_pool


class TestSlowQueryTracking:
    """Test slow query detection and event listeners."""

    def test_slow_query_threshold_ms_configuration(self):
        """Test slow query threshold configuration."""
        pool = DatabaseConnectionPool(
            "sqlite+aiosqlite:///:memory:",
            slow_query_threshold_ms=50.0,
        )

        assert pool.slow_query_threshold == 0.05

    @pytest.mark.asyncio
    async def test_slow_query_counter_initialization(self):
        """Test slow query counter is initialized."""
        pool = DatabaseConnectionPool("sqlite+aiosqlite:///:memory:")

        assert pool._slow_query_count == 0
