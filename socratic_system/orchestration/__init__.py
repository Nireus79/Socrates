"""Orchestration layer for Socrates AI

Note: Main orchestration now handled by backend/src/socrates_api/orchestrator.py
This module is kept for backward compatibility with CLI and local services.
"""

# Legacy orchestration removed - now use backend API orchestrator
try:
    # For backward compatibility, try to provide a stub
    from socrates_api.orchestrator import APIOrchestrator as AgentOrchestrator
except ImportError:
    # Fallback if API not available
    AgentOrchestrator = None

# Library manager removed - use direct library imports instead
SocraticLibraryManager = None
get_library_manager = None
reset_library_manager = None

__all__ = [
    "AgentOrchestrator",
    "SocraticLibraryManager",
    "get_library_manager",
    "reset_library_manager",
]
