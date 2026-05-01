"""
Services Layer - Phase 1 extraction of business logic from agents.

Services encapsulate business logic that was previously scattered across agents.
They use repositories for data access and receive only required dependencies.

Available Services:
- BaseService: Base class for all services
- ProjectService: Project creation, loading, management
- QualityService: Maturity calculations and quality metrics
- ConflictService: Conflict detection and resolution
- DocumentUnderstandingService: Document analysis and summarization
"""

from .base_service import BaseService
from .conflict_service import ConflictService
from .document_understanding import DocumentUnderstandingService
from .project_service import ProjectService
from .quality_service import QualityService

__all__ = [
    "BaseService",
    "DocumentUnderstandingService",
    "ProjectService",
    "QualityService",
    "ConflictService",
]
