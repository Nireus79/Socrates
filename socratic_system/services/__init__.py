"""Service layer for Socrates system.

Decouples business logic from agents through service-oriented architecture.
Services receive only required dependencies via dependency injection.
"""

from .base import Service
from .project_service import ProjectService
from .quality_service import QualityService
from .knowledge_service import KnowledgeService
from .insight_service import InsightService
from .code_service import CodeService
from .conflict_service import ConflictService
from .validation_service import ValidationService
from .learning_service import LearningService
from .document_understanding import DocumentUnderstandingService

__all__ = [
    "Service",
    "ProjectService",
    "QualityService",
    "KnowledgeService",
    "InsightService",
    "CodeService",
    "ConflictService",
    "ValidationService",
    "LearningService",
    "DocumentUnderstandingService",
]
