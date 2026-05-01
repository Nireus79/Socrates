"""
Repository Layer - Phase 1 abstraction of database access.

Repositories provide a single point of change for database schema updates.
Services use repositories instead of calling database directly.

Available Repositories:
- ProjectRepository: All project database operations
- QualityRepository: Quality metrics and maturity data access
"""

from .base_repository import BaseRepository
from .project_repository import ProjectRepository
from .quality_repository import QualityRepository

__all__ = [
    "BaseRepository",
    "ProjectRepository",
    "QualityRepository",
]
