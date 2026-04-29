"""
Services module for Socrates AI.

Provides specialized services for document analysis, understanding, processing,
and orchestrator management for both CLI and web API.

Phase 1 Implementation: Service Layer with Dependency Injection
- Base service class for all services
- Repository pattern for data access abstraction
- Decoupled services for business logic
- Dependency injection container for service wiring
"""

# Legacy services
from socratic_system.services.document_understanding import DocumentUnderstandingService
from socratic_system.services.orchestrator_service import (
    OrchestratorService,
    get_orchestrator_service,
)

# Phase 1: Service Layer
from socratic_system.services.base import Service
from socratic_system.services.code_service import CodeService
from socratic_system.services.insight_service import InsightService
from socratic_system.services.knowledge_service import KnowledgeService
from socratic_system.services.project_service import ProjectService
from socratic_system.services.quality_service import QualityService

# Repositories
from socratic_system.services.repositories import (
    KnowledgeRepository,
    MaturityRepository,
    ProjectRepository,
    Repository,
)

# Dependency Injection
from socratic_system.services.dependency_injection import (
    ServiceContainer,
    get_service_container,
    initialize_container,
    reset_container,
)

__all__ = [
    # Legacy
    "DocumentUnderstandingService",
    "OrchestratorService",
    "get_orchestrator_service",
    # Phase 1: Base
    "Service",
    # Phase 1: Services
    "ProjectService",
    "QualityService",
    "KnowledgeService",
    "InsightService",
    "CodeService",
    # Phase 1: Repositories
    "Repository",
    "ProjectRepository",
    "KnowledgeRepository",
    "MaturityRepository",
    # Phase 1: DI Container
    "ServiceContainer",
    "initialize_container",
    "get_service_container",
    "reset_container",
]
