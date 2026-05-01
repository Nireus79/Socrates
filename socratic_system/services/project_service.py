"""
ProjectService - Business logic for project management.

Phase 1: Service Layer - Extracts project management logic from ProjectManager agent.
"""

import datetime
import logging
from typing import TYPE_CHECKING, Optional

from socratic_system.models import ProjectContext
from socratic_system.repositories.project_repository import ProjectRepository

from .base_service import BaseService

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig
    from socratic_system.database import ProjectDatabase


class ProjectService(BaseService):
    """Service for project management business logic."""

    def __init__(self, config: "SocratesConfig", database: "ProjectDatabase"):
        """Initialize project service."""
        super().__init__(config)
        self.repository = ProjectRepository(database)
        self.logger = logging.getLogger("ProjectService")

    def create_project(
        self,
        name: str,
        description: str = "",
        owner: str = "anonymous",
        **kwargs,
    ) -> Optional[ProjectContext]:
        """Create a new project."""
        self._log_operation("create_project", {"name": name, "owner": owner})

        try:
            if not name or not name.strip():
                self.logger.error("Project name is required")
                return None

            now = datetime.datetime.now()

            project = ProjectContext(
                project_id=f"proj_{int(now.timestamp())}",
                name=name.strip(),
                description=description.strip(),
                owner=owner,
                phase="discovery",
                created_at=now,
                updated_at=now,
                **kwargs,
            )

            if self.repository.save_project(project):
                self.logger.info(f"Created project: {project.project_id} ({name})")
                return project
            else:
                self.logger.error(f"Failed to save project: {name}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            return None

    def get_project(self, project_id: str) -> Optional[ProjectContext]:
        """Get a project by ID."""
        self._log_operation("get_project", {"project_id": project_id})

        if not project_id:
            self.logger.error("Project ID is required")
            return None

        project = self.repository.load_project(project_id)
        if project:
            self.logger.debug(f"Retrieved project: {project_id}")
        return project

    def update_project(self, project_id: str, **updates) -> Optional[ProjectContext]:
        """Update a project."""
        self._log_operation("update_project", {"project_id": project_id})

        try:
            project = self.repository.load_project(project_id)
            if not project:
                self.logger.error(f"Project not found: {project_id}")
                return None

            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)
                    self.logger.debug(f"Updated {key} for project {project_id}")

            project.updated_at = datetime.datetime.now()

            if self.repository.save_project(project):
                self.logger.info(f"Updated project: {project_id}")
                return project
            else:
                self.logger.error(f"Failed to save project: {project_id}")
                return None

        except Exception as e:
            self.logger.error(f"Error updating project: {e}")
            return None

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        self._log_operation("delete_project", {"project_id": project_id})

        if not project_id:
            self.logger.error("Project ID is required")
            return False

        if self.repository.delete_project(project_id):
            self.logger.info(f"Deleted project: {project_id}")
            return True
        else:
            self.logger.error(f"Failed to delete project: {project_id}")
            return False

    def project_exists(self, project_id: str) -> bool:
        """Check if a project exists."""
        return self.repository.project_exists(project_id)
