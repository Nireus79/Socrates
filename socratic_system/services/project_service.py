"""Project service - encapsulates project creation and management logic."""

from typing import TYPE_CHECKING, Any, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_system.claude_client import ClaudeClient
    from socratic_system.database import ProjectDatabase
    from socratic_system.events import EventEmitter
    from socratic_system.models import ProjectContext


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

    def create_project(self, spec: dict[str, Any]) -> "ProjectContext":
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
        import datetime
        import uuid

        from socratic_system.models import ProjectContext

        now = datetime.datetime.now()
        project = ProjectContext(
            project_id=str(uuid.uuid4()),
            name=spec["name"],
            description=spec.get("description", ""),
            owner=spec.get("user_id", ""),
            phase="discovery",
            created_at=now,
            updated_at=now,
            knowledge_base_content=spec.get("knowledge_base_content", ""),
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
                "owner": project.owner,
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
