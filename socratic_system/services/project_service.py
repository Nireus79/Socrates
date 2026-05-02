"""Project service - encapsulates project creation and management logic."""

import logging
from typing import TYPE_CHECKING, Optional, Dict, Any

from .base import Service

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext
    from socratic_system.database import ProjectDatabase
    from socratic_system.claude_client import ClaudeClient
    from socratic_system.events import EventEmitter


class ProjectService(Service):
    """Service for project-related operations.

    Encapsulates business logic for project creation, loading, and management.
    """

    def __init__(
        self,
        config,
        database: "ProjectDatabase",
        claude_client: "ClaudeClient",
        event_emitter: "EventEmitter",
    ):
        """Initialize project service.

        Args:
            config: Socrates configuration
            database: Project database
            claude_client: Claude API client
            event_emitter: Event emitter for notifications
        """
        super().__init__(config)
        self.database = database
        self.claude_client = claude_client
        self.event_emitter = event_emitter

    def create_project(self, spec: Dict[str, Any]) -> "ProjectContext":
        """Create new project with initial specifications.

        Args:
            spec: Project specification dict with name, description, etc.

        Returns:
            Created ProjectContext
        """
        if not spec.get("name"):
            raise ValueError("Project name is required")

        self.logger.info(f"Creating project: {spec.get('name')}")

        # Create project context
        from socratic_system.models import ProjectContext
        from socratic_system.utils.helpers import generate_id

        project = ProjectContext(
            project_id=generate_id(),
            name=spec["name"],
            description=spec.get("description", ""),
            owner_id=spec.get("user_id"),
            phase="discovery",
        )

        # Save to database
        self.database.save_project(project)
        self.logger.info(f"Project created: {project.project_id}")

        # Emit event
        self.event_emitter.emit(
            "project.created",
            {
                "project_id": project.project_id,
                "name": project.name,
                "owner_id": project.owner_id,
            },
        )

        return project

    def load_project(self, project_id: str) -> Optional["ProjectContext"]:
        """Load project from database.

        Args:
            project_id: Project identifier

        Returns:
            ProjectContext if found, None otherwise
        """
        return self.database.load_project(project_id)

    def save_project(self, project: "ProjectContext") -> None:
        """Save project to database.

        Args:
            project: ProjectContext to save
        """
        self.database.save_project(project)
        self.logger.debug(f"Project saved: {project.project_id}")

        # Emit event
        self.event_emitter.emit(
            "project.saved",
            {"project_id": project.project_id},
        )
