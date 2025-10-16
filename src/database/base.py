#!/usr/bin/env python3
"""
Base Repository - Abstract Repository Pattern
==============================================
Provides base repository class with common CRUD operations and type safety.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic

# Core imports with fallbacks
try:
    from src import get_logger

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    import logging


    def get_logger(name):
        return logging.getLogger(name)

# Type variable for generic repository
T = TypeVar('T')


# ==============================================================================
# BASE REPOSITORY
# ==============================================================================

class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository with type-safe operations.

    All concrete repositories must implement:
    - create()
    - get_by_id()
    - update()
    - delete()

    Provides default implementations for:
    - get_all()
    - _row_to_model() (basic conversion)
    - _model_to_dict() (static helper)
    """

    def __init__(self, db_manager, model_class: Type[T]):
        """
        Initialize repository.

        Args:
            db_manager: DatabaseManager instance
            model_class: Model class type for this repository
        """
        self.db_manager = db_manager
        self.model_class = model_class
        self.table_name = self._get_table_name()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def _get_table_name(self) -> str:
        """
        Get table name from model class.

        Default: lowercase model name + 's'
        Override in subclass for custom table names.
        """
        return self.model_class.__name__.lower() + 's'

    @staticmethod
    def _to_iso_safe(value: Any, default: Any = None) -> Any:
        """
        Safely convert value to ISO string format.

        Handles:
        - None values (returns default)
        - Strings (returns as-is, already converted)
        - Datetime objects (converts to ISO string)
        - Other types (converts to string)

        This prevents double-conversion errors when models
        already have converted datetime to strings via to_dict().
        """
        if value is None:
            return default
        if isinstance(value, str):
            return value  # Already a string
        if hasattr(value, 'isoformat'):  # It's a datetime
            return value.isoformat()
        return str(value)

    # ==========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ==========================================================================

    @abstractmethod
    def create(self, entity: T) -> bool:
        """
        Create new entity in database.

        Args:
            entity: Model instance to create

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Model instance or None if not found
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> bool:
        """
        Update existing entity.

        Args:
            entity: Model instance with updated data

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    # ==========================================================================
    # DEFAULT IMPLEMENTATIONS - Can be used or overridden
    # ==========================================================================

    def get_all(self) -> List[T]:
        """
        Get all entities from table.

        Returns:
            List of model instances
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            results = self.db_manager.execute_query(query)
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting all {self.table_name}: {e}")
            return []

    def _row_to_model(self, row: Dict[str, Any]) -> T:
        """
        Convert database row to model instance.

        Default implementation uses direct dictionary unpacking.
        Override in subclass for complex conversions (JSON parsing, datetime conversion, etc.)

        Args:
            row: Database row as dictionary

        Returns:
            Model instance
        """
        try:
            # Basic conversion - override in subclasses for complex models
            return self.model_class(**row)
        except Exception as e:
            self.logger.error(f"Error converting row to model: {e}")
            # Return empty instance on error
            return self.model_class()

    @staticmethod
    def _model_to_dict(entity: T) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Handles:
        - Models with to_dict() method
        - Models with __dict__ attribute
        - Enum values (converts to string)
        - Datetime values (converts to ISO string)

        Args:
            entity: Model instance

        Returns:
            Dictionary representation
        """
        from datetime import datetime

        # Try to_dict() method first
        if hasattr(entity, 'to_dict'):
            data = entity.to_dict()
        # Fall back to __dict__
        elif hasattr(entity, '__dict__'):
            data = entity.__dict__.copy()
        else:
            data = {}

        # Convert all enum values to strings and datetime objects to ISO strings
        for key, value in data.items():
            if hasattr(value, 'value'):  # It's an enum
                data[key] = value.value
            elif isinstance(value, datetime):  # It's a datetime object
                data[key] = value.isoformat()

        return data

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def exists(self, entity_id: str) -> bool:
        """
        Check if entity exists by ID.

        Args:
            entity_id: Entity ID

        Returns:
            bool: True if exists, False otherwise
        """
        return self.get_by_id(entity_id) is not None

    def count(self) -> int:
        """
        Count total entities in table.

        Returns:
            int: Total count
        """
        try:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            results = self.db_manager.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception as e:
            self.logger.error(f"Error counting {self.table_name}: {e}")
            return 0


# ==============================================================================
# HELPER FUNCTIONS FOR REPOSITORIES
# ==============================================================================

def parse_json_field(value: Any, default: Any = None) -> Any:
    """
    Safely parse JSON field from database.

    Args:
        value: JSON string or None
        default: Default value if parsing fails

    Returns:
        Parsed value or default
    """
    import json

    if value is None:
        return default if default is not None else []

    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default if default is not None else []

    return value


def dump_json_field(value: Any) -> str:
    """
    Convert value to JSON string for database storage.

    Args:
        value: Value to convert

    Returns:
        JSON string
    """
    import json

    if value is None:
        return json.dumps([])

    if isinstance(value, str):
        return value

    return json.dumps(value)
