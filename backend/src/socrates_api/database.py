"""Database initialization and session management for Socrates.

This module handles database connections, session creation, and initialization
for both PostgreSQL (production) and SQLite (development/testing).
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration."""

    def __init__(
        self,
        url: Optional[str] = None,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_pre_ping: bool = True,
    ):
        """Initialize database config.

        Args:
            url: Database URL. If None, uses DATABASE_URL env var or SQLite
            echo: Whether to log SQL statements
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            pool_pre_ping: Test connection before using
        """
        self.url = url or os.getenv("DATABASE_URL", "sqlite:///./socrates.db")
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_pre_ping = pool_pre_ping
        self.is_async = "aiosqlite" in self.url or "+asyncpg" in self.url
        self.is_sqlite = "sqlite" in self.url

    def get_sync_url(self) -> str:
        """Get synchronous database URL."""
        if self.is_async:
            return self.url.replace("sqlite+aiosqlite", "sqlite").replace("+asyncpg", "")
        return self.url

    def get_async_url(self) -> str:
        """Get asynchronous database URL."""
        if self.url.startswith("sqlite"):
            return "sqlite+aiosqlite:///" + self.url.split("///")[-1]
        return self.url.replace("postgresql://", "postgresql+asyncpg://")


class Database:
    """Database connection manager."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database connection manager.

        Args:
            config: Database configuration
        """
        self.config = config
        self._async_engine = None
        self._sync_engine = None
        self._async_session_maker = None
        self._sync_session_maker = None

    def init_sync(self) -> sessionmaker:
        """Initialize synchronous database engine and session maker.

        Returns:
            Session maker for synchronous sessions
        """
        if self._sync_session_maker is None:
            sync_url = self.config.get_sync_url()
            self._sync_engine = create_engine(
                sync_url,
                echo=self.config.echo,
                pool_size=self.config.pool_size if not self.config.is_sqlite else 0,
                max_overflow=self.config.max_overflow if not self.config.is_sqlite else 0,
                pool_pre_ping=self.config.pool_pre_ping if not self.config.is_sqlite else False,
                connect_args={"check_same_thread": False} if self.config.is_sqlite else {},
            )

            # Enable foreign keys for SQLite
            if self.config.is_sqlite:
                @event.listens_for(self._sync_engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            self._sync_session_maker = sessionmaker(
                bind=self._sync_engine,
                class_=Session,
                expire_on_commit=False,
            )
            logger.info(f"Initialized synchronous database: {sync_url}")

        return self._sync_session_maker

    async def init_async(self) -> async_sessionmaker:
        """Initialize asynchronous database engine and session maker.

        Returns:
            Session maker for asynchronous sessions
        """
        if self._async_session_maker is None:
            async_url = self.config.get_async_url()
            self._async_engine = create_async_engine(
                async_url,
                echo=self.config.echo,
                pool_size=self.config.pool_size if not self.config.is_sqlite else 0,
                max_overflow=self.config.max_overflow if not self.config.is_sqlite else 0,
                pool_pre_ping=self.config.pool_pre_ping if not self.config.is_sqlite else False,
                connect_args={"check_same_thread": False} if self.config.is_sqlite else {},
            )

            self._async_session_maker = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            logger.info(f"Initialized asynchronous database: {async_url}")

        return self._async_session_maker

    def get_sync_session(self) -> Session:
        """Get a synchronous database session.

        Returns:
            Database session
        """
        session_maker = self.init_sync()
        return session_maker()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session.

        Yields:
            Async database session
        """
        session_maker = await self.init_async()
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def create_tables(self) -> None:
        """Create all database tables (for development/testing)."""
        session_maker = self.init_sync()
        engine = session_maker.kw["bind"]
        Base.metadata.create_all(bind=engine)
        logger.info("Created all database tables")

    async def create_tables_async(self) -> None:
        """Create all database tables asynchronously."""
        session_maker = await self.init_async()
        engine = session_maker.sync_engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Created all database tables asynchronously")

    def drop_tables(self) -> None:
        """Drop all database tables (for testing)."""
        session_maker = self.init_sync()
        engine = session_maker.kw["bind"]
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all database tables")

    async def drop_tables_async(self) -> None:
        """Drop all database tables asynchronously."""
        session_maker = await self.init_async()
        engine = session_maker.sync_engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Dropped all database tables asynchronously")

    def close(self) -> None:
        """Close database connections."""
        if self._sync_engine:
            self._sync_engine.dispose()
            logger.info("Closed synchronous database connection")

    async def close_async(self) -> None:
        """Close asynchronous database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Closed asynchronous database connection")


# Global database instance
_db: Optional[Database] = None


def init_database(config: Optional[DatabaseConfig] = None) -> Database:
    """Initialize the global database instance.

    Args:
        config: Database configuration. If None, uses defaults.

    Returns:
        Global Database instance
    """
    global _db
    if _db is None:
        if config is None:
            config = DatabaseConfig()
        _db = Database(config)
    return _db


def get_database() -> Database:
    """Get the global database instance.

    Returns:
        Global Database instance
    """
    global _db
    if _db is None:
        _db = Database(DatabaseConfig())
    return _db


def get_sync_session() -> Session:
    """Get a synchronous database session.

    Returns:
        Database session
    """
    db = get_database()
    return db.get_sync_session()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an asynchronous database session.

    Yields:
        Async database session
    """
    db = get_database()
    async with db.get_async_session() as session:
        yield session


__all__ = [
    "DatabaseConfig",
    "Database",
    "init_database",
    "get_database",
    "get_sync_session",
    "get_async_session",
    "Base",
]
