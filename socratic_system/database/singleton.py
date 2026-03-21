"""
Database Singleton - Ensures single database instance across the application.

Provides a unified interface for both CLI and API to access the database
with guaranteed single instance semantics.
"""

from typing import Optional

from .project_db import ProjectDatabase


class DatabaseSingleton:
    """Singleton pattern for database access."""

    _instance: Optional[ProjectDatabase] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, db_path: str) -> None:
        """
        Initialize the database singleton with the given path.

        Args:
            db_path: Path to the SQLite database file

        Raises:
            RuntimeError: If already initialized
        """
        if cls._initialized and cls._instance is not None:
            return  # Already initialized, skip

        cls._instance = ProjectDatabase(db_path)
        cls._initialized = True

    @classmethod
    def get_instance(cls) -> ProjectDatabase:
        """
        Get the database instance.

        Returns:
            ProjectDatabase singleton instance

        Raises:
            RuntimeError: If not yet initialized
        """
        if cls._instance is None:
            raise RuntimeError(
                "DatabaseSingleton not initialized. Call initialize() first."
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._initialized = False
