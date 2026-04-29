"""
Base Repository class for generic CRUD operations.

Repositories abstract the data access layer, providing a clean interface
for services to work with domain models without knowing about the underlying
database implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """
    Generic repository interface for data access operations.

    Provides abstract methods for CRUD operations that all repositories
    should implement. This enables dependency injection and loose coupling
    between services and data access logic.
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Save or update an entity.

        Args:
            entity: The entity to save

        Returns:
            The saved entity (potentially with generated IDs)
        """
        pass

    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Find entity by ID.

        Args:
            entity_id: The ID of the entity to find

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Find all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """
        Delete entity by ID.

        Args:
            entity_id: The ID of the entity to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, entity_id: Any) -> bool:
        """
        Check if entity exists.

        Args:
            entity_id: The ID to check

        Returns:
            True if exists, False otherwise
        """
        pass
