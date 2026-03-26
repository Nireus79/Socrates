"""Orchestration layer for Socrates AI"""

from .orchestrator import AgentOrchestrator
from .library_manager import SocraticLibraryManager, get_library_manager, reset_library_manager

__all__ = [
    "AgentOrchestrator",
    "SocraticLibraryManager",
    "get_library_manager",
    "reset_library_manager",
]
