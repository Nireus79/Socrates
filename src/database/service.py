#!/usr/bin/env python3
"""
Database Service - Main Database Interface
===========================================
Provides unified interface to all repositories and database operations.
"""

from typing import Dict, Any

# Import manager and repositories
from .manager import DatabaseManager
from .repositories import (
    UserRepository,
    ProjectRepository,
    GeneratedCodebaseRepository,
    GeneratedFileRepository,
    ProjectCollaboratorRepository,
    SocraticSessionRepository,
    QuestionRepository,
    ConversationMessageRepository,
    TechnicalSpecificationRepository,
    ProjectContextRepository,
    ModuleContextRepository,
    TaskContextRepository,
    ConflictRepository
)

# Core imports with fallbacks
try:
    from src import get_config, get_logger

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    import logging


    def get_config():
        return {'database': {'path': 'data/socratic.db'}}


    def get_logger(name):
        return logging.getLogger(name)

# Model imports with fallbacks
try:
    from src.models import (
        User, Project, GeneratedCodebase, GeneratedFile, ProjectCollaborator,
        SocraticSession, Question, ConversationMessage, TechnicalSpec,
        ProjectContext, ModuleContext, TaskContext, Conflict
    )

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    from dataclasses import dataclass


    @dataclass
    class User:
        pass


    @dataclass
    class Project:
        pass


    @dataclass
    class GeneratedCodebase:
        pass


    @dataclass
    class GeneratedFile:
        pass


    @dataclass
    class ProjectCollaborator:
        pass


    @dataclass
    class SocraticSession:
        pass


    @dataclass
    class Question:
        pass


    @dataclass
    class ConversationMessage:
        pass


    @dataclass
    class TechnicalSpec:
        pass


    @dataclass
    class ProjectContext:
        pass


    @dataclass
    class ModuleContext:
        pass


    @dataclass
    class TaskContext:
        pass


    @dataclass
    class Conflict:
        id: str = ""
        project_id: str = ""


# ==============================================================================
# DATABASE SERVICE
# ==============================================================================

class DatabaseService:
    """
    Main database service providing access to all repositories.

    This is the primary interface for all database operations in the application.
    Each repository is initialized and accessible as a property.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database service with all repositories.

        Args:
            db_path: Optional custom database path. If None, uses config default.
        """
        if db_path is None:
            config = get_config()
            db_path = config.get('database', {}).get('path', 'data/socratic.db')

        self.db_manager = DatabaseManager(db_path)
        self.logger = get_logger(f"{__name__}.DatabaseService")

        # Initialize all repositories
        self._init_repositories()

    def _init_repositories(self):
        """Initialize all repository instances"""

        # Core repositories
        self.users = UserRepository(self.db_manager, User)
        self.projects = ProjectRepository(self.db_manager, Project)
        self.generated_codebases = GeneratedCodebaseRepository(self.db_manager, GeneratedCodebase)
        self.generated_files = GeneratedFileRepository(self.db_manager, GeneratedFile)
        self.project_collaborators = ProjectCollaboratorRepository(self.db_manager, ProjectCollaborator)

        # Session repositories
        self.socratic_sessions = SocraticSessionRepository(self.db_manager, SocraticSession)
        self.questions = QuestionRepository(self.db_manager, Question)
        self.conversation_messages = ConversationMessageRepository(self.db_manager, ConversationMessage)

        # Specification repository
        self.technical_specifications = TechnicalSpecificationRepository(self.db_manager, TechnicalSpec)

        # Context repositories
        self.project_contexts = ProjectContextRepository(self.db_manager, ProjectContext)
        self.module_contexts = ModuleContextRepository(self.db_manager, ModuleContext)
        self.task_contexts = TaskContextRepository(self.db_manager, TaskContext)
        self.conflicts = ConflictRepository(self.db_manager, Conflict)

    # ==========================================================================
    # BACKWARD COMPATIBILITY ALIASES
    # ==========================================================================

    @property
    def codebases(self):
        """Alias for generated_codebases (backward compatibility)"""
        return self.generated_codebases

    @property
    def files(self):
        """Alias for generated_files (backward compatibility)"""
        return self.generated_files

    @property
    def sessions(self):
        """Alias for socratic_sessions (backward compatibility)"""
        return self.socratic_sessions

    @property
    def specifications(self):
        """Alias for technical_specifications (backward compatibility)"""
        return self.technical_specifications

    # ==========================================================================
    # CONVENIENCE METHODS
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Check database health and return status.

        Returns:
            Dict with health status information
        """
        db_health = self.db_manager.health_check()

        return {
            'database': db_health,
            'repositories': {
                'users': self.users is not None,
                'projects': self.projects is not None,
                'sessions': self.socratic_sessions is not None,
                'specifications': self.technical_specifications is not None,
                'contexts': {
                    'project': self.project_contexts is not None,
                    'module': self.module_contexts is not None,
                    'task': self.task_contexts is not None
                }
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with counts for all major entities
        """
        try:
            return {
                'users': self.users.count(),
                'projects': self.projects.count(),
                'codebases': self.generated_codebases.count(),
                'files': self.generated_files.count(),
                'collaborators': self.project_collaborators.count(),
                'sessions': self.socratic_sessions.count(),
                'questions': self.questions.count(),
                'messages': self.conversation_messages.count(),
                'specifications': self.technical_specifications.count(),
                'project_contexts': self.project_contexts.count(),
                'module_contexts': self.module_contexts.count(),
                'task_contexts': self.task_contexts.count()
            }
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

    def backup(self, backup_path: str) -> bool:
        """
        Create database backup.

        Args:
            backup_path: Path for backup file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import shutil
            shutil.copy2(self.db_manager.db_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False


# ==============================================================================
# REPOSITORY MANAGER (Optional convenience class)
# ==============================================================================

class RepositoryManager:
    """
    Centralized repository management and access.

    Provides dictionary-like access to repositories by name.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize repository manager.

        Args:
            db_service: DatabaseService instance
        """
        self.db_service = db_service
        self.logger = get_logger(f"{__name__}.RepositoryManager")

    def get_repository(self, model_type: str):
        """
        Get repository by model type name.

        Args:
            model_type: Model type name (e.g., 'user', 'project')

        Returns:
            Repository instance or None
        """
        repository_mapping = {
            'user': self.db_service.users,
            'project': self.db_service.projects,
            'generated_codebase': self.db_service.generated_codebases,
            'codebase': self.db_service.generated_codebases,
            'generated_file': self.db_service.generated_files,
            'file': self.db_service.generated_files,
            'project_collaborator': self.db_service.project_collaborators,
            'collaborator': self.db_service.project_collaborators,
            'socratic_session': self.db_service.socratic_sessions,
            'session': self.db_service.socratic_sessions,
            'question': self.db_service.questions,
            'conversation_message': self.db_service.conversation_messages,
            'message': self.db_service.conversation_messages,
            'technical_specification': self.db_service.technical_specifications,
            'specification': self.db_service.technical_specifications,
            'project_context': self.db_service.project_contexts,
            'module_context': self.db_service.module_contexts,
            'task_context': self.db_service.task_contexts,
            'conflict': self.db_service.conflicts
        }

        return repository_mapping.get(model_type.lower())

    def get_all_repositories(self) -> Dict[str, Any]:
        """
        Get all available repositories.

        Returns:
            Dict mapping repository names to instances
        """
        return {
            'users': self.db_service.users,
            'projects': self.db_service.projects,
            'generated_codebases': self.db_service.generated_codebases,
            'generated_files': self.db_service.generated_files,
            'project_collaborators': self.db_service.project_collaborators,
            'socratic_sessions': self.db_service.socratic_sessions,
            'questions': self.db_service.questions,
            'conversation_messages': self.db_service.conversation_messages,
            'technical_specifications': self.db_service.technical_specifications,
            'project_contexts': self.db_service.project_contexts,
            'module_contexts': self.db_service.module_contexts,
            'task_contexts': self.db_service.task_contexts
        }


# ==============================================================================
# GLOBAL INSTANCES AND FACTORY FUNCTIONS
# ==============================================================================

_database_service_instance = None
_repository_manager_instance = None


def get_database(db_path: str = None) -> DatabaseService:
    """
    Get global database service instance (singleton pattern).

    Args:
        db_path: Optional custom database path

    Returns:
        DatabaseService instance
    """
    global _database_service_instance
    if _database_service_instance is None:
        _database_service_instance = DatabaseService(db_path)
    return _database_service_instance


def get_repository_manager() -> RepositoryManager:
    """
    Get global repository manager instance.

    Returns:
        RepositoryManager instance
    """
    global _repository_manager_instance
    if _repository_manager_instance is None:
        _repository_manager_instance = RepositoryManager(get_database())
    return _repository_manager_instance


def init_database(db_path: str = None) -> DatabaseService:
    """
    Initialize database with custom path (replaces singleton).

    Args:
        db_path: Custom database path

    Returns:
        New DatabaseService instance
    """
    global _database_service_instance
    _database_service_instance = DatabaseService(db_path)
    return _database_service_instance


def reset_database():
    """Reset global database instances (useful for testing)"""
    global _database_service_instance, _repository_manager_instance
    _database_service_instance = None
    _repository_manager_instance = None
