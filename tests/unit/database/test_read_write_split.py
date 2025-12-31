"""Unit tests for database read/write split routing.

Tests cover:
- DatabaseRole enum
- DatabaseRouter initialization and configuration
- Primary/replica session routing
- Round-robin replica selection
- Replica fallback on failure
- Context-aware role management
- Decorators (@use_primary, @use_replica)
- Module-level router functions
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from socratic_system.database.read_write_split import (
    DatabaseRole,
    DatabaseRouter,
    _db_role,
    get_db_role,
    get_router,
    initialize_router,
    set_db_role,
    use_primary,
    use_replica,
)


class TestDatabaseRole:
    """Test DatabaseRole enum."""

    def test_role_values(self):
        """Test enum values are correctly defined."""
        assert DatabaseRole.PRIMARY.value == "primary"
        assert DatabaseRole.REPLICA.value == "replica"

    def test_role_comparison(self):
        """Test role comparison."""
        assert DatabaseRole.PRIMARY == DatabaseRole.PRIMARY
        assert DatabaseRole.PRIMARY != DatabaseRole.REPLICA


class TestDatabaseRouterInitialization:
    """Test DatabaseRouter initialization."""

    def test_router_init_primary_only(self):
        """Test router initialization with primary only."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            router = DatabaseRouter("postgresql://localhost/db")

            assert router is not None
            assert router.read_preference == DatabaseRole.REPLICA
            assert len(router.replica_pools) == 0

    def test_router_init_with_replicas(self):
        """Test router initialization with primary and replicas."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            replica_urls = [
                "postgresql://replica1/db",
                "postgresql://replica2/db",
            ]

            router = DatabaseRouter("postgresql://primary/db", replica_urls)

            assert len(router.replica_pools) == 2
            assert router.current_replica == 0

    def test_router_init_custom_read_preference(self):
        """Test router initialization with custom read preference."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            router = DatabaseRouter(
                "postgresql://primary/db",
                read_preference=DatabaseRole.PRIMARY,
            )

            assert router.read_preference == DatabaseRole.PRIMARY

    def test_router_init_invalid_primary_url(self):
        """Test router initialization with invalid primary URL."""
        with pytest.raises(ValueError, match="primary_url is required"):
            DatabaseRouter("")

    def test_router_init_invalid_replica_urls(self):
        """Test router initialization with invalid replica URLs."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            with pytest.raises(ValueError, match="replica_urls must be a list"):
                DatabaseRouter("postgresql://primary/db", replica_urls="not_a_list")

    def test_router_init_empty_replica_url(self):
        """Test router initialization with empty replica URL in list."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            with pytest.raises(ValueError, match="replica_urls contains empty URL"):
                DatabaseRouter("postgresql://primary/db", ["postgresql://replica/db", ""])


class TestDatabaseRouterSession:
    """Test session routing behavior."""

    @pytest.mark.asyncio
    async def test_get_session_primary_only(self):
        """Test getting session when only primary is configured."""
        from contextlib import asynccontextmanager

        mock_pool = MagicMock()
        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        # side_effect with a function returns a new context manager each time
        mock_pool.get_session = MagicMock(side_effect=lambda: mock_get_session())

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            return_value=mock_pool,
        ):
            router = DatabaseRouter("postgresql://primary/db")

            async with router.get_session() as session:
                assert session == mock_session

            mock_pool.get_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_explicit_primary(self):
        """Test explicitly requesting primary database."""
        from contextlib import asynccontextmanager

        mock_primary = MagicMock()
        mock_replica = MagicMock()
        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_primary.get_session = MagicMock(side_effect=lambda: mock_get_session())

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            side_effect=[mock_primary, mock_replica],
        ):
            router = DatabaseRouter(
                "postgresql://primary/db",
                ["postgresql://replica/db"],
            )

            async with router.get_session(role=DatabaseRole.PRIMARY) as session:
                assert session == mock_session

            mock_primary.get_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_replica_round_robin(self):
        """Test round-robin replica selection."""
        from contextlib import asynccontextmanager

        mock_primary = MagicMock()
        mock_replica1 = MagicMock()
        mock_replica2 = MagicMock()

        mock_session1 = AsyncMock()
        mock_session2 = AsyncMock()

        @asynccontextmanager
        async def make_session_ctx(session):
            yield session

        mock_replica1.get_session = MagicMock(side_effect=lambda: make_session_ctx(mock_session1))
        mock_replica2.get_session = MagicMock(side_effect=lambda: make_session_ctx(mock_session2))

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            side_effect=[mock_primary, mock_replica1, mock_replica2],
        ):
            router = DatabaseRouter(
                "postgresql://primary/db",
                ["postgresql://replica1/db", "postgresql://replica2/db"],
            )

            # First call should use replica 0
            async with router.get_session(role=DatabaseRole.REPLICA) as session:
                assert session == mock_session1
            assert router.current_replica == 1

            # Second call should use replica 1
            async with router.get_session(role=DatabaseRole.REPLICA) as session:
                assert session == mock_session2
            assert router.current_replica == 0

            # Third call should wrap around to replica 0
            async with router.get_session(role=DatabaseRole.REPLICA) as session:
                assert session == mock_session1
            assert router.current_replica == 1

    @pytest.mark.asyncio
    async def test_get_session_replica_fallback(self):
        """Test fallback to primary when replica fails."""
        from contextlib import asynccontextmanager

        mock_primary = MagicMock()
        mock_replica = MagicMock()
        mock_session = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_replica.get_session.side_effect = Exception("Connection failed")
        mock_primary.get_session = MagicMock(side_effect=lambda: mock_get_session())

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            side_effect=[mock_primary, mock_replica],
        ):
            router = DatabaseRouter(
                "postgresql://primary/db",
                ["postgresql://replica/db"],
            )

            # Should get session from primary due to replica failure
            async with router.get_session(role=DatabaseRole.REPLICA) as session:
                assert session == mock_session

            mock_primary.get_session.assert_called_once()


class TestDatabaseRouterStatus:
    """Test router status and monitoring."""

    @pytest.mark.asyncio
    async def test_get_replica_status_healthy(self):
        """Test getting status of healthy replicas."""
        mock_primary = AsyncMock()
        mock_replica1 = AsyncMock()
        mock_replica2 = AsyncMock()

        mock_replica1.get_pool_health.return_value = {
            "status": "healthy",
            "latency_ms": 5.2,
        }
        mock_replica2.get_pool_health.return_value = {
            "status": "healthy",
            "latency_ms": 6.1,
        }

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            side_effect=[mock_primary, mock_replica1, mock_replica2],
        ):
            router = DatabaseRouter(
                "postgresql://primary/db",
                ["postgresql://replica1/db", "postgresql://replica2/db"],
            )

            status = await router.get_replica_status()

            assert status["0"]["status"] == "healthy"
            assert status["0"]["latency_ms"] == 5.2
            assert status["1"]["status"] == "healthy"
            assert status["1"]["latency_ms"] == 6.1

    @pytest.mark.asyncio
    async def test_get_replica_status_unhealthy(self):
        """Test getting status when replica is unhealthy."""
        mock_primary = AsyncMock()
        mock_replica = AsyncMock()

        mock_replica.get_pool_health.side_effect = Exception("Connection timeout")

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            side_effect=[mock_primary, mock_replica],
        ):
            router = DatabaseRouter(
                "postgresql://primary/db",
                ["postgresql://replica/db"],
            )

            status = await router.get_replica_status()

            assert status["0"]["status"] == "unhealthy"
            assert "Connection timeout" in status["0"]["error"]

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing router connections."""
        mock_primary = AsyncMock()
        mock_replica = AsyncMock()

        with patch(
            "socratic_system.database.connection_pool.DatabaseConnectionPool",
            side_effect=[mock_primary, mock_replica],
        ):
            router = DatabaseRouter(
                "postgresql://primary/db",
                ["postgresql://replica/db"],
            )

            await router.close()

            mock_primary.close.assert_called_once()
            mock_replica.close.assert_called_once()


class TestUsePrimaryDecorator:
    """Test @use_primary() decorator."""

    @pytest.mark.asyncio
    async def test_use_primary_async_function(self):
        """Test @use_primary on async function."""

        @use_primary()
        async def async_func():
            return get_db_role()

        role = await async_func()
        assert role == DatabaseRole.PRIMARY

    def test_use_primary_sync_function(self):
        """Test @use_primary on sync function."""

        @use_primary()
        def sync_func():
            return get_db_role()

        role = sync_func()
        assert role == DatabaseRole.PRIMARY

    @pytest.mark.asyncio
    async def test_use_primary_restores_context(self):
        """Test @use_primary restores previous context."""
        set_db_role(DatabaseRole.REPLICA)

        @use_primary()
        async def async_func():
            return get_db_role()

        await async_func()
        assert get_db_role() == DatabaseRole.REPLICA

    @pytest.mark.asyncio
    async def test_use_primary_preserves_return_value(self):
        """Test @use_primary preserves function return value."""

        @use_primary()
        async def returns_value():
            return "test_value"

        result = await returns_value()
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_use_primary_with_args_kwargs(self):
        """Test @use_primary with function arguments."""

        @use_primary()
        async def func_with_args(a, b, c=None):
            return (a, b, c, get_db_role())

        result = await func_with_args(1, 2, c=3)
        assert result == (1, 2, 3, DatabaseRole.PRIMARY)


class TestUseReplicaDecorator:
    """Test @use_replica() decorator."""

    @pytest.mark.asyncio
    async def test_use_replica_async_function(self):
        """Test @use_replica on async function."""

        @use_replica()
        async def async_func():
            return get_db_role()

        role = await async_func()
        assert role == DatabaseRole.REPLICA

    def test_use_replica_sync_function(self):
        """Test @use_replica on sync function."""

        @use_replica()
        def sync_func():
            return get_db_role()

        role = sync_func()
        assert role == DatabaseRole.REPLICA

    @pytest.mark.asyncio
    async def test_use_replica_restores_context(self):
        """Test @use_replica restores previous context."""
        set_db_role(DatabaseRole.PRIMARY)

        @use_replica()
        async def async_func():
            return get_db_role()

        await async_func()
        assert get_db_role() == DatabaseRole.PRIMARY

    @pytest.mark.asyncio
    async def test_use_replica_preserves_return_value(self):
        """Test @use_replica preserves function return value."""

        @use_replica()
        async def returns_value():
            return "replica_value"

        result = await returns_value()
        assert result == "replica_value"


class TestContextManagement:
    """Test context variable management."""

    def test_set_get_db_role(self):
        """Test setting and getting database role."""
        set_db_role(DatabaseRole.PRIMARY)
        assert get_db_role() == DatabaseRole.PRIMARY

        set_db_role(DatabaseRole.REPLICA)
        assert get_db_role() == DatabaseRole.REPLICA

    def test_db_role_default(self):
        """Test default database role."""
        # Reset context to default
        _db_role.set(DatabaseRole.PRIMARY)
        role = _db_role.get()
        assert role == DatabaseRole.PRIMARY

    @pytest.mark.asyncio
    async def test_context_isolation_async(self):
        """Test that context is isolated between async tasks."""

        async def task1():
            set_db_role(DatabaseRole.PRIMARY)
            await asyncio.sleep(0.01)
            return get_db_role()

        async def task2():
            set_db_role(DatabaseRole.REPLICA)
            await asyncio.sleep(0.005)
            return get_db_role()

        result1, result2 = await asyncio.gather(task1(), task2())

        assert result1 == DatabaseRole.PRIMARY
        assert result2 == DatabaseRole.REPLICA


class TestModuleLevelFunctions:
    """Test module-level router functions."""

    @pytest.mark.asyncio
    async def test_initialize_router(self):
        """Test initializing global router."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            router = await initialize_router("postgresql://primary/db")

            assert router is not None
            assert isinstance(router, DatabaseRouter)

    @pytest.mark.asyncio
    async def test_get_router_after_init(self):
        """Test getting router after initialization."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            await initialize_router("postgresql://primary/db")
            router = get_router()

            assert router is not None
            assert isinstance(router, DatabaseRouter)

    def test_get_router_before_init(self):
        """Test getting router before initialization raises error."""
        # Reset global router
        import socratic_system.database.read_write_split as module

        original_router = module._router
        module._router = None

        try:
            with pytest.raises(RuntimeError, match="Database router not initialized"):
                get_router()
        finally:
            # Restore original state
            module._router = original_router

    @pytest.mark.asyncio
    async def test_initialize_with_replicas(self):
        """Test initializing router with replicas."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            replica_urls = ["postgresql://replica1/db", "postgresql://replica2/db"]

            router = await initialize_router(
                "postgresql://primary/db",
                replica_urls=replica_urls,
            )

            assert len(router.replica_pools) == 2


class TestRoundRobinSelection:
    """Test round-robin replica selection strategy."""

    def test_round_robin_rotation(self):
        """Test round-robin rotates through all replicas."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool") as mock_pool:
            mock1 = MagicMock()
            mock2 = MagicMock()
            mock3 = MagicMock()

            with patch(
                "socratic_system.database.connection_pool.DatabaseConnectionPool",
                side_effect=[mock_pool, mock1, mock2, mock3],
            ):
                router = DatabaseRouter(
                    "postgresql://primary/db",
                    [
                        "postgresql://replica1/db",
                        "postgresql://replica2/db",
                        "postgresql://replica3/db",
                    ],
                )

                # Manually call _select_replica to test round-robin
                assert router._select_replica() == mock1
                assert router.current_replica == 1

                assert router._select_replica() == mock2
                assert router.current_replica == 2

                assert router._select_replica() == mock3
                assert router.current_replica == 0

                assert router._select_replica() == mock1
                assert router.current_replica == 1

    def test_select_replica_no_replicas(self):
        """Test selecting replica when none configured raises error."""
        with patch("socratic_system.database.connection_pool.DatabaseConnectionPool"):
            router = DatabaseRouter("postgresql://primary/db")

            with pytest.raises(IndexError, match="No replicas configured"):
                router._select_replica()
