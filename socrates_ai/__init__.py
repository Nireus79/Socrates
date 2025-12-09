"""
Socrates AI - A Socratic method tutoring system powered by Claude AI.

This package provides the main entry point for importing socratic_system modules.
"""

from socratic_system import (
    __author__,
    __license__,
    __version__,
    agents,
    clients,
    config,
    conflict_resolution,
    create_orchestrator,
    database,
    events,
    exceptions,
    models,
    orchestration,
    quick_start,
    ui,
    utils,
)
from socratic_system.clients import ClaudeClient
from socratic_system.config import ConfigBuilder, SocratesConfig
from socratic_system.events import EventEmitter, EventType
from socratic_system.exceptions import (
    AgentError,
    APIError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    ProjectNotFoundError,
    SocratesError,
    UserNotFoundError,
    ValidationError,
)
from socratic_system.models import (
    ConflictInfo,
    KnowledgeEntry,
    ProjectContext,
    ProjectNote,
    TokenUsage,
    User,
)
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.ui import SocraticRAGSystem

# Export all public API
__all__ = [
    # Version
    "__version__",
    "__author__",
    "__license__",
    # Configuration
    "SocratesConfig",
    "ConfigBuilder",
    # Core Components
    "AgentOrchestrator",
    "ClaudeClient",
    # Models
    "User",
    "ProjectContext",
    "KnowledgeEntry",
    "TokenUsage",
    "ConflictInfo",
    "ProjectNote",
    # Events
    "EventEmitter",
    "EventType",
    # Exceptions
    "SocratesError",
    "ConfigurationError",
    "AgentError",
    "DatabaseError",
    "AuthenticationError",
    "ProjectNotFoundError",
    "UserNotFoundError",
    "ValidationError",
    "APIError",
    # Convenience Functions
    "create_orchestrator",
    "quick_start",
    # Legacy (CLI)
    "SocraticRAGSystem",
    # Submodules
    "agents",
    "clients",
    "config",
    "conflict_resolution",
    "database",
    "events",
    "exceptions",
    "models",
    "orchestration",
    "ui",
    "utils",
]
