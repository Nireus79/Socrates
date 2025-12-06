"""
Socrates AI - A Socratic method tutoring system powered by Claude AI.

This package provides the main entry point for importing socratic_system modules.
"""

# Re-export socratic_system modules for backward compatibility
from socratic_system import *  # noqa: F401, F403
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

__all__ = [
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
