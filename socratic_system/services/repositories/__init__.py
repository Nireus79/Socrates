"""
Repository pattern implementation for data access layer.

Repositories provide a clean abstraction over database operations,
allowing services to work with domain models without knowing
about the underlying database schema.
"""

from socratic_system.services.repositories.base import Repository
from socratic_system.services.repositories.project_repository import ProjectRepository
from socratic_system.services.repositories.knowledge_repository import KnowledgeRepository
from socratic_system.services.repositories.maturity_repository import MaturityRepository

__all__ = [
    "Repository",
    "ProjectRepository",
    "KnowledgeRepository",
    "MaturityRepository",
]
