"""Database layer for Socrates AI"""

from .knowledge_manager import KnowledgeManager
from .project_db import ProjectDatabase
from .singleton import DatabaseSingleton
from .vector_db import VectorDatabase

__all__ = ["DatabaseSingleton", "VectorDatabase", "ProjectDatabase", "KnowledgeManager"]
