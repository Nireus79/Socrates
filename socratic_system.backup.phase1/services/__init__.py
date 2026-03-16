"""
Services module for Socrates AI.

Provides specialized services for document analysis, understanding, processing,
and orchestrator management for both CLI and web API.
"""

from socratic_system.services.document_understanding import DocumentUnderstandingService
from socratic_system.services.orchestrator_service import (
    OrchestratorService,
    get_orchestrator_service,
)

__all__ = [
    "DocumentUnderstandingService",
    "OrchestratorService",
    "get_orchestrator_service",
]
