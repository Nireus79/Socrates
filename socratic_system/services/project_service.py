"""
Project Service - Encapsulates all project-related business logic.

Extracted from ProjectManager agent, this service handles:
- Project creation
- Project updates
- Project queries
- Project validation

No orchestrator dependency - uses dependency injection for all external services.
"""

from typing import Optional

from socratic_nexus.clients import ClaudeClient

from socratic_system.config import SocratesConfig
from socratic_system.events import EventEmitter
from socratic_system.models import ProjectContext
from socratic_system.services.base import Service
from socratic_system.services.repositories import ProjectRepository
from socratic_system.utils import id_generator


class ProjectService(Service):
    """
    Service for project management.

    Handles all project-related business logic without direct orchestrator
    dependency. Uses repositories for data access abstraction.
    """

    def __init__(
        self,
        config: SocratesConfig,
        repository: ProjectRepository,
        claude_client: ClaudeClient,
        event_emitter: EventEmitter,
    ):
        """
        Initialize project service.

        Args:
            config: SocratesConfig instance
            repository: ProjectRepository for data access
            claude_client: ClaudeClient for AI operations
            event_emitter: EventEmitter for decoupled communication
        """
        super().__init__(config)
        self.repository = repository
        self.claude_client = claude_client
        self.event_emitter = event_emitter

    def create_project(
        self,
        name: str,
        description: str,
        user_id: str,
        **kwargs
    ) -> ProjectContext:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            user_id: Owner user ID
            **kwargs: Additional project properties

        Returns:
            Created ProjectContext

        Raises:
            ValueError: If validation fails
        """
        # Validation
        if not name or not name.strip():
            raise ValueError("Project name is required")
        if not user_id:
            raise ValueError("User ID is required")

        self.log_info(f"Creating project '{name}' for user {user_id}")

        # Create project object
        project = ProjectContext(
            project_id=id_generator.generate_id(),
            name=name.strip(),
            description=description or "",
            owner_id=user_id,
            **kwargs
        )

        # Persist to repository
        saved_project = self.repository.save(project)

        # Emit event for decoupled listeners
        self.event_emitter.emit(
            "project.created",
            {
                "project_id": saved_project.project_id,
                "name": saved_project.name,
                "owner_id": user_id,
            },
        )

        self.log_info(f"Project created: {saved_project.project_id}")
        return saved_project

    def get_project(self, project_id: str) -> Optional[ProjectContext]:
        """
        Get project by ID.

        Args:
            project_id: The project ID

        Returns:
            ProjectContext if found, None otherwise
        """
        return self.repository.find_by_id(project_id)

    def update_project(self, project_id: str, **updates) -> Optional[ProjectContext]:
        """
        Update project properties.

        Args:
            project_id: The project ID
            **updates: Properties to update

        Returns:
            Updated ProjectContext if found, None otherwise
        """
        project = self.repository.find_by_id(project_id)
        if not project:
            self.log_warning(f"Project not found: {project_id}")
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)

        # Save updated project
        saved_project = self.repository.save(project)

        # Emit event
        self.event_emitter.emit(
            "project.updated",
            {
                "project_id": project_id,
                "updates": updates,
            },
        )

        self.log_info(f"Project updated: {project_id}")
        return saved_project

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: The project ID

        Returns:
            True if deleted, False if not found
        """
        project = self.repository.find_by_id(project_id)
        if not project:
            self.log_warning(f"Project not found: {project_id}")
            return False

        success = self.repository.delete(project_id)

        if success:
            self.event_emitter.emit(
                "project.deleted",
                {"project_id": project_id},
            )
            self.log_info(f"Project deleted: {project_id}")

        return success

    def get_user_projects(self, user_id: str) -> list[ProjectContext]:
        """
        Get all projects for a user.

        Args:
            user_id: The user ID

        Returns:
            List of ProjectContext objects
        """
        return self.repository.find_by_user(user_id)

    def project_exists(self, project_id: str) -> bool:
        """
        Check if project exists.

        Args:
            project_id: The project ID

        Returns:
            True if exists, False otherwise
        """
        return self.repository.exists(project_id)
