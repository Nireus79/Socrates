"""Production-grade database connection pool with monitoring and health checks.

Features:
- SQLAlchemy async engine with configurable pool size
- Connection pool statistics and monitoring
- Health checks with connection validation (pre-ping)
- Automatic connection recycling to prevent stale connections
- Support for both SQLite (development) and PostgreSQL (production)
- Connection exhaustion detection and warnings
"""

import logging
import time
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Production-grade connection pool with monitoring capabilities.

    Manages database connections with health checks, performance monitoring,
    and graceful handling of connection exhaustion.

    Example:
        ```python
        pool = DatabaseConnectionPool(
            "postgresql+asyncpg://user:pass@localhost/socrates",
            pool_size=20,
            max_overflow=10
        )

        async with pool.get_session() as session:
            result = await session.execute("SELECT 1")

        status = await pool.get_pool_status()
        ```
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        slow_query_threshold_ms: float = 100.0,
    ) -> None:
        """Initialize database connection pool.

        Args:
            database_url: SQLAlchemy database URL (async driver required)
            pool_size: Number of connections to maintain in pool (default: 20)
            max_overflow: Maximum overflow connections (default: 10)
            pool_recycle: Recycle connections after N seconds (default: 3600 = 1 hour)
            slow_query_threshold_ms: Threshold for slow query warnings (default: 100ms)

        Raises:
            ValueError: If database_url is invalid or missing
        """
        if not database_url:
            raise ValueError("database_url is required")

        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.slow_query_threshold = slow_query_threshold_ms / 1000.0
        self._slow_query_count = 0

        # Determine pool class and connection parameters based on database type
        if "postgresql" in database_url:
            poolclass = QueuePool
            pool_pre_ping = True  # Verify connections before using them
            connect_args = {
                "server_settings": {"application_name": "socrates_api"},
                "command_timeout": 60,
            }
            logger.info(f"Initializing PostgreSQL connection pool: {pool_size}+{max_overflow}")
        elif "sqlite" in database_url:
            poolclass = StaticPool  # SQLite works best with StaticPool or NullPool
            pool_pre_ping = False
            connect_args = {}
            logger.info("Initializing SQLite connection pool")
        else:
            raise ValueError(f"Unsupported database type: {database_url}")

        # Create async engine with configured pool
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,
            poolclass=poolclass,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
            connect_args=connect_args,
        )

        # Create session factory
        self.async_session_maker = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Add event listeners for monitoring
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """Set up event listeners for connection monitoring.

        Tracks:
        - Slow query warnings (>threshold)
        - Connection pool status
        - Connection lifecycle events
        """

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query execution start time."""
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Log slow queries and track execution time."""
            total_time = time.time() - conn.info["query_start_time"].pop(-1)

            if total_time > self.slow_query_threshold:
                self._slow_query_count += 1
                logger.warning(
                    f"Slow query detected ({total_time*1000:.2f}ms, threshold: {self.slow_query_threshold*1000:.0f}ms): {statement[:100]}..."
                )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session from the pool.

        Yields:
            AsyncSession: Database session for use in async context

        Example:
            ```python
            async with pool.get_session() as session:
                result = await session.execute("SELECT * FROM users")
            ```
        """
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get detailed connection pool statistics.

        Returns:
            Dict with pool statistics:
            - size: Number of connections in pool
            - checked_in: Connections available for checkout
            - checked_out: Connections currently in use
            - overflow: Number of overflow connections
            - total: Total active connections
            - utilization_percent: Percentage of pool in use
            - slow_query_count: Number of slow queries detected

        Example:
            ```python
            status = await pool.get_pool_status()
            print(f"Pool utilization: {status['utilization_percent']:.1f}%")
            ```
        """
        pool = self.engine.pool

        # Get pool statistics
        try:
            # For QueuePool (PostgreSQL)
            if hasattr(pool, "size"):
                size = pool.size()
            else:
                size = 0

            if hasattr(pool, "checkedin"):
                checked_in = pool.checkedin()
            else:
                checked_in = 0

            if hasattr(pool, "checkedout"):
                checked_out = pool.checkedout()
            else:
                checked_out = 0

            if hasattr(pool, "overflow"):
                overflow = pool.overflow()
            else:
                overflow = 0
        except Exception as e:
            logger.warning(f"Error getting pool statistics: {e}")
            size = checked_in = checked_out = overflow = 0

        total = size + overflow
        utilization = (checked_out / total * 100) if total > 0 else 0

        return {
            "size": size,
            "checked_in": checked_in,
            "checked_out": checked_out,
            "overflow": overflow,
            "total": total,
            "utilization_percent": round(utilization, 2),
            "slow_query_count": self._slow_query_count,
        }

    async def get_pool_health(self) -> Dict[str, Any]:
        """Get health status of connection pool.

        Checks:
        - Pool utilization (healthy <90%, degraded 90-95%, unhealthy >95%)
        - Database connectivity with ping
        - Connection latency

        Returns:
            Dict with health information:
            - status: 'healthy', 'degraded', or 'unhealthy'
            - latency_ms: Database round-trip latency
            - pool_status: Detailed pool statistics
            - error: Error message if health check failed

        Example:
            ```python
            health = await pool.get_pool_health()
            if health['status'] != 'healthy':
                logger.warning(f"Database health degraded: {health}")
            ```
        """
        start_time = time.time()

        try:
            # Test connectivity with a simple query
            async with self.async_session_maker() as session:
                await session.execute(text("SELECT 1"))

            latency_ms = (time.time() - start_time) * 1000

            # Get pool status
            pool_status = await self.get_pool_status()
            utilization = pool_status["utilization_percent"]

            # Determine health based on pool utilization
            if utilization > 95:
                health_status = "unhealthy"
            elif utilization > 90:
                health_status = "degraded"
            else:
                health_status = "healthy"

            return {
                "status": health_status,
                "latency_ms": round(latency_ms, 2),
                "pool_status": pool_status,
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

    async def test_connection(self) -> bool:
        """Test database connectivity.

        Returns:
            bool: True if connection is successful, False otherwise

        Example:
            ```python
            if not await pool.test_connection():
                raise RuntimeError("Database connection failed")
            ```
        """
        try:
            async with self.async_session_maker() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def close(self) -> None:
        """Close all connections and dispose engine.

        Called on application shutdown to clean up resources.

        Example:
            ```python
            @app.on_event("shutdown")
            async def shutdown_db():
                await pool.close()
            ```
        """
        await self.engine.dispose()
        logger.info("Database connection pool closed")

    async def __aenter__(self) -> "DatabaseConnectionPool":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes pool."""
        await self.close()


# Singleton instance for application use
_pool: Optional[DatabaseConnectionPool] = None


async def initialize_pool(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
) -> DatabaseConnectionPool:
    """Initialize the global connection pool.

    Should be called once during application startup.

    Args:
        database_url: SQLAlchemy database URL
        pool_size: Number of connections in pool
        max_overflow: Maximum overflow connections

    Returns:
        DatabaseConnectionPool: Initialized connection pool

    Example:
        ```python
        @app.on_event("startup")
        async def startup():
            global _pool
            _pool = await initialize_pool(os.getenv("DATABASE_URL"))
        ```
    """
    global _pool
    _pool = DatabaseConnectionPool(database_url, pool_size, max_overflow)
    return _pool


def get_pool() -> DatabaseConnectionPool:
    """Get the global connection pool instance.

    Returns:
        DatabaseConnectionPool: The initialized pool

    Raises:
        RuntimeError: If pool not initialized

    Example:
        ```python
        pool = get_pool()
        async with pool.get_session() as session:
            ...
        ```
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call initialize_pool() first.")
    return _pool
