#!/usr/bin/env python3
"""
Database Package - Unified Database Interface
==============================================
Provides complete database functionality for the Socratic RAG Enhanced system.

This package replaces the old monolithic database.py file with a modular structure:
- manager.py: Database connection and schema management
- base.py: Base repository pattern
- repositories.py: All concrete repository implementations
- service.py: Main database service interface

Usage:
    from src.Database import get_database

    db = get_database()
    user = db.users.get_by_id(user_id)
    project = db.projects.get_by_id(project_id)
"""

# ==============================================================================
# CORE IMPORTS
# ==============================================================================

# Manager and error classes
from .manager import DatabaseManager, DatabaseError

# Base repository
from .base import BaseRepository, parse_json_field, dump_json_field

# All repositories
from .repositories import (
    UserRepository,
    ProjectRepository,
    ModuleRepository,
    TaskRepository,
    GeneratedCodebaseRepository,
    GeneratedFileRepository,
    ProjectCollaboratorRepository,
    SocraticSessionRepository,
    ChatSessionRepository,
    QuestionRepository,
    ConversationMessageRepository,
    TechnicalSpecificationRepository,
    ProjectContextRepository,
    ModuleContextRepository,
    TaskContextRepository,
    ConflictRepository
)

# Service and factory functions
from .service import (
    DatabaseService,
    RepositoryManager,
    get_database,
    get_repository_manager,
    init_database,
    reset_database
)

# ==============================================================================
# VERSION INFO
# ==============================================================================

__version__ = "2.0.0"
__author__ = "Socratic RAG Enhanced Team"

# ==============================================================================
# PUBLIC API EXPORTS
# ==============================================================================

__all__ = [
    # Core classes
    'DatabaseManager',
    'DatabaseService',
    'RepositoryManager',
    'BaseRepository',

    # Exceptions
    'DatabaseError',

    # Factory functions (most commonly used)
    'get_database',
    'get_repository_manager',
    'init_database',
    'reset_database',

    # Helper functions
    'parse_json_field',
    'dump_json_field',

    # Repository classes (if needed for type hints)
    'UserRepository',
    'ProjectRepository',
    'GeneratedCodebaseRepository',
    'GeneratedFileRepository',
    'ProjectCollaboratorRepository',
    'SocraticSessionRepository',
    'ChatSessionRepository',
    'QuestionRepository',
    'ConversationMessageRepository',
    'TechnicalSpecificationRepository',
    'ProjectContextRepository',
    'ModuleContextRepository',
    'TaskContextRepository',
    'ConflictRepository',
    'ModuleRepository',

    # Version
    '__version__',
]


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def get_version() -> str:
    """Get database package version"""
    return __version__


def get_info() -> dict:
    """Get database package information"""
    return {
        'version': __version__,
        'author': __author__,
        'description': 'Modular database layer for Socratic RAG Enhanced',
        'components': {
            'manager': 'Database connection and schema management',
            'repositories': 'Data access layer with 12 repositories',
            'service': 'Unified database service interface',
            'base': 'Abstract repository pattern'
        }
    }


# ==============================================================================
# PACKAGE INITIALIZATION
# ==============================================================================

def _check_imports():
    """Verify all critical imports loaded successfully"""
    critical_components = [
        DatabaseManager,
        DatabaseService,
        BaseRepository,
        get_database,
    ]

    for component in critical_components:
        if component is None:
            raise ImportError(f"Failed to import critical component: {component}")


# Run import check on package load
try:
    _check_imports()
except ImportError as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Database package initialization error: {e}")
    raise

# ==============================================================================
# MIGRATION NOTES
# ==============================================================================

"""
MIGRATION FROM OLD database.py:

OLD CODE:
    from src.database import get_database
    db = get_database()
    user = db.users.get_by_id(user_id)

NEW CODE:
    from src.database import get_database  # ← SAME!
    db = get_database()                     # ← SAME!
    user = db.users.get_by_id(user_id)     # ← SAME!

No changes needed! All existing code continues to work.

NEW FEATURES:
    - Modular structure (easier to maintain)
    - Better organization (12 repositories in separate file)
    - Improved performance (database indexes)
    - Helper functions (parse_json_field, dump_json_field)
    - Statistics and monitoring (db.get_statistics())
    - Database backup (db.backup(path))

WHAT CHANGED:
    ✓ database.py split into 4 files (manager, base, repositories, service)
    ✓ Context repositories fixed (no longer nested incorrectly)
    ✓ All repositories use consistent JSON/datetime handling
    ✓ Added database indexes for better query performance
    ✓ Better error handling throughout

BACKWARD COMPATIBILITY:
    ✓ All imports work exactly as before
    ✓ All method names unchanged
    ✓ All properties unchanged (db.users, db.projects, etc.)
    ✓ Aliases maintained (db.codebases → db.generated_codebases)
"""