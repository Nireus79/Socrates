"""
Centralized database dependency for API.

All routers should use get_database() from this module to access the database,
rather than creating their own singletons. This ensures a single database
connection is used across the entire application.
"""

import os
import logging
from pathlib import Path
from socratic_system.database import ProjectDatabaseV2

logger = logging.getLogger(__name__)

# Global database instance
_database: ProjectDatabaseV2 = None


def get_database() -> ProjectDatabaseV2:
    """
    Get or create the global database instance.

    This is a FastAPI dependency that ensures only one database connection
    is used throughout the application.

    Returns:
        ProjectDatabaseV2: The shared database instance
    """
    global _database

    if _database is None:
        # Get data directory from environment or use default
        data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))

        # Ensure directory exists and is writable
        try:
            Path(data_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create data directory {data_dir}: {e}")

        # Create database path
        db_path = os.path.join(data_dir, "projects.db")

        # Initialize database
        try:
            _database = ProjectDatabaseV2(db_path)
            logger.info(f"Database initialized at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    return _database


def close_database() -> None:
    """
    Close the global database connection.

    This should be called during application shutdown to properly clean up
    database connections.
    """
    global _database

    if _database is not None:
        try:
            # If database has a close method, call it
            if hasattr(_database, 'close'):
                _database.close()
            _database = None
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
