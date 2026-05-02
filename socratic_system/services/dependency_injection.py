"""
Dependency Injection Container for Socrates Services.

Manages service creation and wiring of dependencies.
Provides a clean interface for getting properly configured service instances.

This enables:
- Testability (easy to mock dependencies)
- Loose coupling
- Single point of configuration
- Service lifecycle management
"""

from typing import Dict, Optional

from socratic_nexus.clients import ClaudeClient

from socratic_system.config import SocratesConfig
from socratic_system.database import ProjectDatabase, VectorDatabase
from socratic_system.events import EventEmitter
from socratic_system.services.base import Service
from socratic_system.services.code_service import CodeService
from socratic_system.services.insight_service import InsightService
from socratic_system.services.knowledge_service import KnowledgeService
from socratic_system.services.project_service import ProjectService
from socratic_system.services.quality_service import QualityService
from socratic_system.services.repositories import (
    KnowledgeRepository,
    MaturityRepository,
    ProjectRepository,
)


class ServiceContainer:
    """
    Dependency injection container for managing service creation and wiring.

    Provides lazy initialization of services with proper dependency injection.
    Services are created once and cached for reuse.
    """

    def __init__(
        self,
        config: SocratesConfig,
        database: ProjectDatabase,
        vector_db: VectorDatabase,
        claude_client: ClaudeClient,
        event_emitter: EventEmitter,
    ):
        """
        Initialize service container with core dependencies.

        Args:
            config: SocratesConfig instance
            database: ProjectDatabase instance
            vector_db: VectorDatabase instance
            claude_client: ClaudeClient instance
            event_emitter: EventEmitter instance
        """
        self.config = config
        self.database = database
        self.vector_db = vector_db
        self.claude_client = claude_client
        self.event_emitter = event_emitter

        # Service cache
        self._services: Dict[str, Service] = {}

    # Repository accessors

    def get_project_repository(self) -> ProjectRepository:
        """Get or create ProjectRepository."""
        if "project_repository" not in self._services:
            self._services["project_repository"] = ProjectRepository(self.database)
        return self._services["project_repository"]

    def get_knowledge_repository(self) -> KnowledgeRepository:
        """Get or create KnowledgeRepository."""
        if "knowledge_repository" not in self._services:
            self._services["knowledge_repository"] = KnowledgeRepository(
                self.database, self.vector_db
            )
        return self._services["knowledge_repository"]

    def get_maturity_repository(self) -> MaturityRepository:
        """Get or create MaturityRepository."""
        if "maturity_repository" not in self._services:
            self._services["maturity_repository"] = MaturityRepository(self.database)
        return self._services["maturity_repository"]

    # Service accessors

    def get_project_service(self) -> ProjectService:
        """Get or create ProjectService."""
        if "project_service" not in self._services:
            self._services["project_service"] = ProjectService(
                config=self.config,
                repository=self.get_project_repository(),
                claude_client=self.claude_client,
                event_emitter=self.event_emitter,
            )
        return self._services["project_service"]

    def get_quality_service(self) -> QualityService:
        """Get or create QualityService."""
        if "quality_service" not in self._services:
            self._services["quality_service"] = QualityService(
                config=self.config,
                repository=self.get_maturity_repository(),
            )
        return self._services["quality_service"]

    def get_knowledge_service(self) -> KnowledgeService:
        """Get or create KnowledgeService."""
        if "knowledge_service" not in self._services:
            self._services["knowledge_service"] = KnowledgeService(
                config=self.config,
                repository=self.get_knowledge_repository(),
            )
        return self._services["knowledge_service"]

    def get_insight_service(self) -> InsightService:
        """Get or create InsightService."""
        if "insight_service" not in self._services:
            self._services["insight_service"] = InsightService(
                config=self.config,
                claude_client=self.claude_client,
            )
        return self._services["insight_service"]

    def get_code_service(self) -> CodeService:
        """Get or create CodeService."""
        if "code_service" not in self._services:
            self._services["code_service"] = CodeService(
                config=self.config,
                claude_client=self.claude_client,
            )
        return self._services["code_service"]

    # Utility methods

    def get_service(self, service_name: str) -> Optional[Service]:
        """
        Get service by name.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            Service instance if found, None otherwise
        """
        service_getter = getattr(self, f"get_{service_name}_service", None)
        if service_getter:
            return service_getter()
        return None

    def register_service(self, name: str, service: Service) -> None:
        """
        Register a custom service instance.

        Args:
            name: Service name for caching
            service: The service instance
        """
        self._services[name] = service

    def clear_cache(self) -> None:
        """Clear all cached service instances."""
        self._services.clear()

    def get_service_stats(self) -> Dict[str, int]:
        """Get statistics about cached services."""
        return {
            "cached_services": len(self._services),
            "services": list(self._services.keys()),
        }


# Global singleton instance
_container: Optional[ServiceContainer] = None


def initialize_container(
    config: SocratesConfig,
    database: ProjectDatabase,
    vector_db: VectorDatabase,
    claude_client: ClaudeClient,
    event_emitter: EventEmitter,
) -> ServiceContainer:
    """
    Initialize the global service container.

    Args:
        config: SocratesConfig instance
        database: ProjectDatabase instance
        vector_db: VectorDatabase instance
        claude_client: ClaudeClient instance
        event_emitter: EventEmitter instance

    Returns:
        The initialized ServiceContainer
    """
    global _container
    _container = ServiceContainer(config, database, vector_db, claude_client, event_emitter)
    return _container


def get_service_container() -> Optional[ServiceContainer]:
    """
    Get the global service container.

    Returns:
        The ServiceContainer if initialized, None otherwise
    """
    return _container


def reset_container() -> None:
    """Reset the global service container (mainly for testing)."""
    global _container
    if _container:
        _container.clear_cache()
    _container = None
