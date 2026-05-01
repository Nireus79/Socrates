"""
Base Repository class for data access abstraction.

Phase 1: Service Layer - Repository pattern abstracts database access.

Repositories provide a single point of change for database schema updates.
Services use repositories instead of calling database directly.

This allows:
- Single place to update queries for schema changes
- Easy mocking for testing
- Clear separation of concerns
"""

import logging
from typing import TYPE_CHECKING, Any, Generic, List, Optional, TypeVar

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository for data access.

    Generic base class for all repositories.
    Subclasses implement domain-specific methods.

    Attributes:
        database: ProjectDatabase instance
        logger: Logger for this repository
    """

    def __init__(self, database: "ProjectDatabase"):
        """
        Initialize repository.

        Args:
            database: ProjectDatabase instance for data access
        """
        self.database = database
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"{self.__class__.__name__} initialized")

    def _log_operation(self, operation: str, details: dict = None):
        """
        Log a repository operation.

        Args:
            operation: Operation name
            details: Additional operation details
        """
        if details:
            self.logger.debug(f"{operation}: {details}")
        else:
            self.logger.debug(operation)
