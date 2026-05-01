"""Base repository class for data access abstraction.

Repository pattern provides single point of change for database access.
Services depend on repository interfaces, not database implementation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for all domain models.

    Provides interface for data access without exposing database details.
    """

    def __init__(self, database):
        """Initialize repository.

        Args:
            database: Database connection/session
        """
        self.database = database
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def save(self, entity: T) -> T:
        """Save entity to database.

        Args:
            entity: Entity to save

        Returns:
            Saved entity
        """
        pass

    @abstractmethod
    def load(self, entity_id: str) -> Optional[T]:
        """Load entity from database.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity from database.

        Args:
            entity_id: Entity identifier

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    def list_all(self) -> List[T]:
        """List all entities.

        Returns:
            List of entities
        """
        pass


class ProjectRepository(BaseRepository):
    """Repository for ProjectContext entities."""

    def save(self, entity) -> Any:
        """Save project to database."""
        self.database.save_project(entity)
        return entity

    def load(self, entity_id: str) -> Optional[Any]:
        """Load project from database."""
        return self.database.load_project(entity_id)

    def delete(self, entity_id: str) -> bool:
        """Delete project from database."""
        try:
            self.database.delete_project(entity_id)
            return True
        except Exception:
            return False

    def list_all(self) -> List[Any]:
        """List all projects."""
        return self.database.list_projects()


class UserRepository(BaseRepository):
    """Repository for User entities."""

    def save(self, entity) -> Any:
        """Save user to database."""
        self.database.save_user(entity)
        return entity

    def load(self, entity_id: str) -> Optional[Any]:
        """Load user from database."""
        return self.database.load_user(entity_id)

    def delete(self, entity_id: str) -> bool:
        """Delete user from database."""
        try:
            self.database.delete_user(entity_id)
            return True
        except Exception:
            return False

    def list_all(self) -> List[Any]:
        """List all users."""
        return self.database.list_users()


class KnowledgeRepository(BaseRepository):
    """Repository for Knowledge documents."""

    def save(self, entity) -> Any:
        """Save knowledge document."""
        return entity

    def load(self, entity_id: str) -> Optional[Any]:
        """Load knowledge document."""
        return None

    def delete(self, entity_id: str) -> bool:
        """Delete knowledge document."""
        return False

    def list_all(self) -> List[Any]:
        """List all knowledge documents."""
        return []
