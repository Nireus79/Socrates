"""Database read/write split routing for high-load scenarios.

This module implements primary/replica routing for read-heavy workloads.
It allows distributing read queries to replicas while routing writes to primary.

Features:
- DatabaseRole enum (PRIMARY, REPLICA)
- DatabaseRouter for managing primary and replica pools
- Context-aware routing via ContextVar
- Decorators for explicit role selection (@use_primary, @use_replica)
- Round-robin replica selection
- Fallback to primary on replica failure

Usage:
    ```python
    # Initialize router with primary and replicas
    db_router = DatabaseRouter(
        primary_url="postgresql://user:pass@primary:5432/db",
        replica_urls=[
            "postgresql://user:pass@replica1:5432/db",
            "postgresql://user:pass@replica2:5432/db",
        ]
    )

    # Reads go to replica by default
    @use_replica()
    async def list_projects(user: str):
        async with db_router.get_session() as session:
            result = await session.execute(query)
            return result

    # Writes always go to primary
    @use_primary()
    async def create_project(project: ProjectContext):
        async with db_router.get_session() as session:
            await session.merge(project)
            await session.commit()
    ```

Examples:
    ```python
    # Manual role selection
    token = _db_role.set(DatabaseRole.REPLICA)
    try:
        async with db_router.get_session() as session:
            # Uses replica
            pass
    finally:
        _db_role.reset(token)

    # Force primary (useful for critical reads after writes)
    async with db_router.get_session(role=DatabaseRole.PRIMARY) as session:
        # Uses primary, guarantees latest data
        pass
    ```
"""

import logging
from enum import Enum
from contextvars import ContextVar
from functools import wraps
from contextlib import asynccontextmanager
from typing import Optional, List, Callable, Any, AsyncGenerator, AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseRole(Enum):
    """Database role enum for read/write split."""

    PRIMARY = "primary"
    REPLICA = "replica"


# Context variable to track current database role per async task
_db_role: ContextVar[DatabaseRole] = ContextVar("db_role", default=DatabaseRole.PRIMARY)


class DatabaseRouter:
    """Route database queries to primary or read replicas.

    This class manages multiple database connections (primary + replicas)
    and routes queries based on operation type and role context.

    Attributes:
        primary_pool: DatabaseConnectionPool for primary database (writes)
        replica_pools: List of DatabaseConnectionPool instances for replicas (reads)
        current_replica: Round-robin index for replica selection
        read_preference: Default role for reads (REPLICA or PRIMARY)

    Example:
        ```python
        router = DatabaseRouter(
            primary_url="postgresql://user:pass@primary:5432/db",
            replica_urls=[
                "postgresql://user:pass@replica1:5432/db",
                "postgresql://user:pass@replica2:5432/db",
            ]
        )

        # Get session for reading
        async with router.get_session(role=DatabaseRole.REPLICA) as session:
            result = await session.execute(query)

        # Get session for writing
        async with router.get_session(role=DatabaseRole.PRIMARY) as session:
            await session.merge(entity)
            await session.commit()
        ```
    """

    def __init__(
        self,
        primary_url: str,
        replica_urls: Optional[List[str]] = None,
        read_preference: DatabaseRole = DatabaseRole.REPLICA,
    ):
        """Initialize database router with primary and replica connections.

        Args:
            primary_url: Connection string for primary database
            replica_urls: List of connection strings for replica databases
            read_preference: Default role for read operations

        Raises:
            ValueError: If primary_url is empty or replica_urls contains invalid URLs
        """
        if not primary_url:
            raise ValueError("primary_url is required")

        # Import here to avoid circular dependency
        from socratic_system.database.connection_pool import DatabaseConnectionPool

        self.primary_pool = DatabaseConnectionPool(primary_url)
        self.read_preference = read_preference

        # Initialize replica pools
        self.replica_pools: List[DatabaseConnectionPool] = []
        if replica_urls:
            if not isinstance(replica_urls, list):
                raise ValueError("replica_urls must be a list")

            for url in replica_urls:
                if not url:
                    raise ValueError("replica_urls contains empty URL")
                self.replica_pools.append(DatabaseConnectionPool(url))

        self.current_replica = 0

        logger.info(
            f"DatabaseRouter initialized with primary and {len(self.replica_pools)} "
            f"replica(s). Default read preference: {read_preference.value}"
        )

    def get_session(self, role: Optional[DatabaseRole] = None) -> "AsyncContextManager[AsyncSession]":
        """Get a database session from appropriate pool.

        Routes to primary or replica based on role parameter or context variable.
        If replica is unavailable and read_preference is REPLICA, falls back to primary.

        Args:
            role: Explicit role (PRIMARY or REPLICA). If None, uses context variable or default

        Returns:
            Async context manager for database session

        Example:
            ```python
            # Use context-aware role
            async with router.get_session() as session:
                result = await session.execute(query)

            # Explicit role override
            async with router.get_session(role=DatabaseRole.PRIMARY) as session:
                result = await session.execute(query)
            ```
        """
        @asynccontextmanager
        async def _get_session_impl():
            # Determine which role to use
            actual_role = role if role is not None else _db_role.get()

            # Always use primary for writes
            if actual_role == DatabaseRole.PRIMARY or not self.replica_pools:
                logger.debug("Routing to primary database")
                async with self.primary_pool.get_session() as session:
                    yield session
                return

            # Use round-robin replica selection for reads
            try:
                pool = self._select_replica()
                logger.debug(f"Routing to replica {self.current_replica}")
                async with pool.get_session() as session:
                    yield session
            except Exception as e:
                logger.warning(
                    f"Replica {self.current_replica} unavailable, falling back to primary: {e}"
                )
                # Fallback to primary on replica failure
                async with self.primary_pool.get_session() as session:
                    yield session

        return _get_session_impl()

    def _select_replica(self) -> "DatabaseConnectionPool":
        """Select next replica using round-robin strategy.

        Returns:
            DatabaseConnectionPool: Next replica in rotation

        Raises:
            IndexError: If no replicas configured
        """
        if not self.replica_pools:
            raise IndexError("No replicas configured")

        pool = self.replica_pools[self.current_replica]
        self.current_replica = (self.current_replica + 1) % len(self.replica_pools)
        return pool

    async def get_replica_status(self) -> dict:
        """Get status of all replicas.

        Returns status information for all configured replicas, useful for
        monitoring replica health and connectivity.

        Returns:
            dict: Status of each replica with index as key
                {
                    "0": {"status": "healthy", "latency_ms": 5.2},
                    "1": {"status": "healthy", "latency_ms": 6.1},
                    "2": {"status": "unhealthy", "error": "Connection timeout"}
                }

        Example:
            ```python
            status = await router.get_replica_status()
            for idx, replica_status in status.items():
                if replica_status["status"] == "unhealthy":
                    logger.warning(f"Replica {idx} is down")
            ```
        """
        status = {}

        for idx, pool in enumerate(self.replica_pools):
            try:
                health = await pool.get_pool_health()
                status[str(idx)] = {
                    "status": health.get("status", "unknown"),
                    "latency_ms": health.get("latency_ms", 0),
                }
            except Exception as e:
                status[str(idx)] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return status

    async def close(self):
        """Close all database connections.

        Closes primary and all replica pools gracefully. Called on application shutdown.

        Example:
            ```python
            @app.on_event("shutdown")
            async def shutdown():
                await db_router.close()
            ```
        """
        logger.info("Closing database router connections")
        await self.primary_pool.close()

        for idx, pool in enumerate(self.replica_pools):
            try:
                await pool.close()
            except Exception as e:
                logger.error(f"Error closing replica {idx}: {e}")

        logger.info("Database router connections closed")


def use_primary() -> Callable:
    """Decorator to force primary database for a function.

    Ensures the decorated function always uses the primary database,
    useful for critical reads that require latest data after writes.

    Returns:
        Callable: Decorator function

    Example:
        ```python
        @use_primary()
        async def get_user_latest(user_id: str):
            # Always reads from primary to guarantee latest data
            async with db_router.get_session() as session:
                return await session.get(User, user_id)
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            token = _db_role.set(DatabaseRole.PRIMARY)
            try:
                logger.debug(f"Running {func.__name__} on PRIMARY")
                return await func(*args, **kwargs)
            finally:
                _db_role.reset(token)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            token = _db_role.set(DatabaseRole.PRIMARY)
            try:
                logger.debug(f"Running {func.__name__} on PRIMARY")
                return func(*args, **kwargs)
            finally:
                _db_role.reset(token)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def use_replica() -> Callable:
    """Decorator to route function to read replica.

    Directs the decorated function to use a read replica if available,
    otherwise falls back to primary. Useful for read-heavy operations
    to distribute load away from primary.

    Returns:
        Callable: Decorator function

    Example:
        ```python
        @use_replica()
        async def list_projects(owner: str):
            # Routes to replica for read distribution
            async with db_router.get_session() as session:
                return await session.execute(
                    select(Project).where(Project.owner == owner)
                )
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            token = _db_role.set(DatabaseRole.REPLICA)
            try:
                logger.debug(f"Running {func.__name__} on REPLICA")
                return await func(*args, **kwargs)
            finally:
                _db_role.reset(token)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            token = _db_role.set(DatabaseRole.REPLICA)
            try:
                logger.debug(f"Running {func.__name__} on REPLICA")
                return func(*args, **kwargs)
            finally:
                _db_role.reset(token)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Module-level global router instance
_router: Optional[DatabaseRouter] = None


async def initialize_router(
    primary_url: str,
    replica_urls: Optional[List[str]] = None,
    read_preference: DatabaseRole = DatabaseRole.REPLICA,
) -> DatabaseRouter:
    """Initialize global database router instance.

    Sets up the global router singleton for use throughout the application.
    Should be called during application startup.

    Args:
        primary_url: Connection string for primary database
        replica_urls: List of connection strings for replica databases
        read_preference: Default role for read operations

    Returns:
        DatabaseRouter: Initialized router instance

    Raises:
        ValueError: If primary_url is empty

    Example:
        ```python
        @app.on_event("startup")
        async def startup():
            global _router
            _router = await initialize_router(
                primary_url=os.getenv("DATABASE_URL"),
                replica_urls=os.getenv("DATABASE_REPLICA_URLS", "").split(","),
            )
        ```
    """
    global _router
    _router = DatabaseRouter(primary_url, replica_urls, read_preference)
    return _router


def get_router() -> DatabaseRouter:
    """Get global database router instance.

    Returns the initialized router singleton. Must be called after
    initialize_router() during application startup.

    Returns:
        DatabaseRouter: Global router instance

    Raises:
        RuntimeError: If router not initialized

    Example:
        ```python
        router = get_router()
        async with router.get_session() as session:
            result = await session.execute(query)
        ```
    """
    if _router is None:
        raise RuntimeError("Database router not initialized. Call initialize_router() first")
    return _router


def set_db_role(role: DatabaseRole) -> None:
    """Manually set database role for current async context.

    This is an alternative to decorators for fine-grained role control.

    Args:
        role: DatabaseRole (PRIMARY or REPLICA)

    Example:
        ```python
        # Use replica
        set_db_role(DatabaseRole.REPLICA)
        async with db_router.get_session() as session:
            result = await session.execute(query)

        # Use primary
        set_db_role(DatabaseRole.PRIMARY)
        async with db_router.get_session() as session:
            result = await session.execute(query)
        ```
    """
    _db_role.set(role)
    logger.debug(f"Database role set to {role.value}")


def get_db_role() -> DatabaseRole:
    """Get current database role from context.

    Returns the role configured for the current async context.

    Returns:
        DatabaseRole: Current role (PRIMARY or REPLICA)

    Example:
        ```python
        current_role = get_db_role()
        if current_role == DatabaseRole.PRIMARY:
            logger.info("Using primary database")
        ```
    """
    return _db_role.get()
