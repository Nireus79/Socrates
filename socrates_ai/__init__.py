"""
Socrates AI - A Socratic method tutoring system powered by Claude AI.

This package provides the main entry point for importing socratic_system modules.
"""

# Re-export everything from socratic_system
from socratic_system import *  # noqa: F401, F403
from socratic_system import __all__ as _socratic_system_all

# Also provide submodule access
from socratic_system import (
    agents,
    clients,
    config,
    conflict_resolution,
    database,
    events,
    exceptions,
    models,
    orchestration,
    ui,
    utils,
)

# Export all public API from socratic_system
__all__ = _socratic_system_all + [
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
