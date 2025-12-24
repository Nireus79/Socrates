"""
Unified database singleton for both CLI and API.

This module provides the DatabaseSingleton class that ensures both CLI
(orchestrator) and API use the same database instance, preventing data
corruption from dual database access.

All components should use DatabaseSingleton.get_instance() to access the database.
"""

import os
import logging
from pathlib import Path
from socratic_system.database import ProjectDatabaseV2

logger = logging.getLogger(__name__)


class DatabaseSingleton:
    """
    Unified database singleton for CLI + API.

    Ensures both the orchestrator and API use the same database instance,
    preventing data inconsistencies from accessing different databases.
    """

    _instance: ProjectDatabaseV2 = None
    _db_path: str = None

    @classmethod
    def initialize(cls, db_path: str = None) -> None:
        """
        Initialize the database singleton with a specific path.

        Should be called once at application startup (before get_instance is used).

        Args:
            db_path: Path to projects.db. If None, uses environment or default.
        """
        if db_path:
            cls._db_path = db_path
        else:
            # Get from environment or use default
            data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            cls._db_path = os.path.join(data_dir, "projects.db")

        # Reset instance so next get_instance() call creates new one with new path
        cls._instance = None

    @classmethod
    def get_instance(cls) -> ProjectDatabaseV2:
        """
        Get or create the global database instance.

        This is used by both CLI (orchestrator) and API to ensure
        they access the same database.

        Returns:
            ProjectDatabaseV2: The shared database instance
        """
        if cls._instance is None:
            # Initialize path if not already done
            if cls._db_path is None:
                cls.initialize()

            # Create database instance
            try:
                cls._instance = ProjectDatabaseV2(cls._db_path)
                logger.info(f"Database singleton initialized at {cls._db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing purposes)"""
        cls._instance = None
        cls._db_path = None


# FastAPI dependency that uses the singleton
def get_database() -> ProjectDatabaseV2:
    """
    FastAPI dependency that gets the shared database instance.

    Returns:
        ProjectDatabaseV2: The shared database instance from DatabaseSingleton
    """
    return DatabaseSingleton.get_instance()


def close_database() -> None:
    """
    Close the global database connection.

    This should be called during application shutdown to properly clean up
    database connections.
    """
    # DatabaseSingleton.reset() clears the cached instance
    try:
        DatabaseSingleton.reset()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


def reset_database() -> None:
    """
    Reset the database instance (mainly for testing).

    This closes the current connection and clears the cached instance,
    forcing a new connection to be created on the next request.
    """
    close_database()
