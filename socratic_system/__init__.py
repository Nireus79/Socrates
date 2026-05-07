"""
Socrates AI - A Socratic method tutoring system powered by Claude AI

A production-ready library for building intelligent tutoring systems that guide users
through the Socratic method using Claude AI. Combines RAG (Retrieval-Augmented Generation)
with multi-agent orchestration to help developers think through architectural and design
decisions for their software projects.

Key Features:
- Event-driven architecture for plugin integration
- Async/await support for long-running operations
- Flexible configuration system (environment variables, files, code)
- Structured error handling and logging
- Cross-platform compatible (Windows, Linux, macOS)
- Token tracking and cost estimation
- Knowledge base management with vector search

Main Components:
- Models: Data models for users, projects, knowledge, notes
- Database: SQLite and vector database persistence
- Agents: Specialized agents for projects, code generation, Socratic dialogue
- Clients: Claude API integration with async support
- Orchestration: Central agent coordination and event emission
- Configuration: Flexible config system with environment variable support
- Events: Event-driven communication for decoupled components
- Exceptions: Structured error handling

Quick Start:
    >>> import socrates
    >>> system = socrates.quick_start_system(api_key="sk-ant-...")
    >>> result = system.process_request('project_manager', {
    ...     'action': 'create_project',
    ...     'project_name': 'My API',
    ...     'owner': 'alice'
    ... })

Full Example (with configuration):
    >>> import socrates
    >>> config = socrates.SocratesConfig.from_dict({
    ...     "api_key": "sk-ant-...",
    ...     "data_dir": "/path/to/data",
    ...     "log_level": "DEBUG"
    ... })
    >>> system = socrates.create_socratic_system(config)
    >>>
    >>> # Process requests
    >>> result = await system.process_request_async('code_generator', {...})

Documentation: https://github.com/socrates-ai/socrates-ai (placeholder)
GitHub: https://github.com/socrates-ai/socrates-ai (placeholder)
"""

__version__ = "1.3.3"
__author__ = "Socrates AI Contributors"
__license__ = "MIT"

# Core Configuration API
# Core Components - Phase 3 transition to SocraticAgentsSystem
# Import both for backward compatibility during migration
from socratic_agents import SocraticAgentsSystem

from .clients import ClaudeClient
from .config import SocratesConfig

# Event System
from .events import EventEmitter, EventType

# Custom Exceptions
from .exceptions import (
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

# Data Models
from .models import (
    ConflictInfo,
    KnowledgeEntry,
    ProjectContext,
    ProjectNote,
    TokenUsage,
    User,
)
from .orchestration import AgentOrchestrator

# Legacy UI (for CLI)
from .ui import SocraticRAGSystem

# ============================================================================
# Convenience Functions
# ============================================================================


def create_socratic_system(config: SocratesConfig) -> SocraticAgentsSystem:
    """
    Create and initialize a SocraticAgentsSystem with a configuration object.

    This is the new primary way to initialize the Socrates library.
    Uses the independent socratic-agents library for agent management.

    Args:
        config: A SocratesConfig object with all settings

    Returns:
        Initialized SocraticAgentsSystem ready for use

    Raises:
        ConfigurationError: If configuration is invalid

    Example:
        >>> config = SocratesConfig(
        ...     api_key="sk-ant-...",
        ...     data_dir="/path/to/data",
        ...     log_level="INFO"
        ... )
        >>> system = create_socratic_system(config)
        >>> result = system.process_request('project_manager', {...})
    """
    return SocraticAgentsSystem(
        api_key=config.api_key,
        data_dir=str(config.data_dir),
        claude_model=config.claude_model,
    )


def quick_start_system(
    api_key: str, data_dir: str = None, log_level: str = "INFO"
) -> SocraticAgentsSystem:
    """
    Quick start with SocraticAgentsSystem and minimal configuration.

    Ideal for getting started quickly with sensible defaults. All other settings
    can be customized via environment variables if needed.

    Args:
        api_key: Claude API key (or set ANTHROPIC_API_KEY env var)
        data_dir: Optional custom data directory (defaults to ~/.socrates)
        log_level: Optional logging level (DEBUG, INFO, WARNING, ERROR) [not yet used by system]

    Returns:
        Initialized SocraticAgentsSystem ready to use

    Example:
        >>> system = quick_start_system("sk-ant-...")
        >>> result = system.process_request('project_manager', {
        ...     'action': 'create_project',
        ...     'name': 'My Project'
        ... })
    """
    from pathlib import Path
    from typing import Any

    config_dict: dict[str, Any] = {"api_key": api_key}

    if data_dir:
        config_dict["data_dir"] = Path(data_dir)

    if log_level:
        config_dict["log_level"] = log_level

    config = SocratesConfig.from_dict(config_dict)
    return create_socratic_system(config)


# ============================================================================
# Public API Exports
# ============================================================================

__all__ = [
    # Version
    "__version__",
    "__author__",
    "__license__",
    # Configuration
    "SocratesConfig",
    # Core Components
    "AgentOrchestrator",
    "SocraticAgentsSystem",
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
    # Convenience Functions (Phase 3 migration to SocraticAgentsSystem)
    "create_socratic_system",
    "quick_start_system",
    # Legacy (CLI)
    "SocraticRAGSystem",
]
