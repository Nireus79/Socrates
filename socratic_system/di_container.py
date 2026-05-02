"""Dependency injection container for managing service lifecycles.

Central registry for creating and managing service instances with all dependencies.
"""

import logging
from typing import Any, Callable, Dict, Optional, TypeVar

from socratic_system.services import (
    ProjectService,
    QualityService,
    KnowledgeService,
    InsightService,
    CodeService,
    ConflictService,
    ValidationService,
    LearningService,
)
from socratic_system.repositories.base_repository import (
    ProjectRepository,
    UserRepository,
    KnowledgeRepository,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


class DIContainer:
    """Dependency injection container.

    Manages service lifecycles and dependencies.
    Provides single point for creating services with all required dependencies.
    """

    def __init__(self, config, database, vector_db, claude_client, event_emitter, orchestrator):
        """Initialize DI container.

        Args:
            config: Application configuration
            database: Database connection
            vector_db: Vector database connection
            claude_client: Claude API client
            event_emitter: Event emitter
            orchestrator: Agent orchestrator
        """
        self.config = config
        self.database = database
        self.vector_db = vector_db
        self.claude_client = claude_client
        self.event_emitter = event_emitter
        self.orchestrator = orchestrator

        # Service cache (singleton pattern)
        self._services: Dict[str, Any] = {}

        # Repository cache
        self._repositories: Dict[str, Any] = {}

        logger.info("DIContainer initialized")

    # Services

    def get_project_service(self) -> ProjectService:
        """Get ProjectService (singleton)."""
        if "project_service" not in self._services:
            self._services["project_service"] = ProjectService(
                self.config,
                self.database,
                self.claude_client,
                self.event_emitter,
            )
        return self._services["project_service"]

    def get_quality_service(self) -> QualityService:
        """Get QualityService (singleton)."""
        if "quality_service" not in self._services:
            self._services["quality_service"] = QualityService(
                self.config,
                self.orchestrator,
            )
        return self._services["quality_service"]

    def get_knowledge_service(self) -> KnowledgeService:
        """Get KnowledgeService (singleton)."""
        if "knowledge_service" not in self._services:
            self._services["knowledge_service"] = KnowledgeService(
                self.config,
                self.database,
                self.vector_db,
            )
        return self._services["knowledge_service"]

    def get_insight_service(self) -> InsightService:
        """Get InsightService (singleton)."""
        if "insight_service" not in self._services:
            self._services["insight_service"] = InsightService(
                self.config,
                self.claude_client,
            )
        return self._services["insight_service"]

    def get_code_service(self) -> CodeService:
        """Get CodeService (singleton)."""
        if "code_service" not in self._services:
            self._services["code_service"] = CodeService(
                self.config,
                self.orchestrator,
            )
        return self._services["code_service"]

    def get_conflict_service(self) -> ConflictService:
        """Get ConflictService (singleton)."""
        if "conflict_service" not in self._services:
            self._services["conflict_service"] = ConflictService(
                self.config,
                self.orchestrator,
            )
        return self._services["conflict_service"]

    def get_validation_service(self) -> ValidationService:
        """Get ValidationService (singleton)."""
        if "validation_service" not in self._services:
            self._services["validation_service"] = ValidationService(
                self.config,
                self.orchestrator,
            )
        return self._services["validation_service"]

    def get_learning_service(self) -> LearningService:
        """Get LearningService (singleton)."""
        if "learning_service" not in self._services:
            self._services["learning_service"] = LearningService(
                self.config,
                self.orchestrator,
            )
        return self._services["learning_service"]

    # Repositories

    def get_project_repository(self) -> ProjectRepository:
        """Get ProjectRepository (singleton)."""
        if "project_repo" not in self._repositories:
            self._repositories["project_repo"] = ProjectRepository(self.database)
        return self._repositories["project_repo"]

    def get_user_repository(self) -> UserRepository:
        """Get UserRepository (singleton)."""
        if "user_repo" not in self._repositories:
            self._repositories["user_repo"] = UserRepository(self.database)
        return self._repositories["user_repo"]

    def get_knowledge_repository(self) -> KnowledgeRepository:
        """Get KnowledgeRepository (singleton)."""
        if "knowledge_repo" not in self._repositories:
            self._repositories["knowledge_repo"] = KnowledgeRepository(self.database)
        return self._repositories["knowledge_repo"]

    # Utility methods

    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        return {
            "project_service": self.get_project_service(),
            "quality_service": self.get_quality_service(),
            "knowledge_service": self.get_knowledge_service(),
            "insight_service": self.get_insight_service(),
            "code_service": self.get_code_service(),
            "conflict_service": self.get_conflict_service(),
            "validation_service": self.get_validation_service(),
            "learning_service": self.get_learning_service(),
        }

    def get_all_repositories(self) -> Dict[str, Any]:
        """Get all registered repositories."""
        return {
            "project_repo": self.get_project_repository(),
            "user_repo": self.get_user_repository(),
            "knowledge_repo": self.get_knowledge_repository(),
        }

    def clear_cache(self) -> None:
        """Clear all service and repository caches."""
        self._services.clear()
        self._repositories.clear()
        logger.info("DIContainer caches cleared")
