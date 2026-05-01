"""
Repository Layer - Phase 1 abstraction of database access.

Repositories provide a single point of change for database schema updates.
Services use repositories instead of calling database directly.

Available Repositories:
- ProjectRepository: All project database operations
"""

from .base_repository import BaseRepository
from .project_repository import ProjectRepository

__all__ = [
    "BaseRepository",
    "ProjectRepository",
]
