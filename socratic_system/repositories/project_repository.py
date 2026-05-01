"""
ProjectRepository - Data access for projects.

Abstracts all project database operations.
Used by ProjectService instead of direct database calls.

This is the single point of change for project schema updates.
"""

import logging
from typing import TYPE_CHECKING, Any, List, Optional

from socratic_system.models import ProjectContext

from .base_repository import BaseRepository

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase


class ProjectRepository(BaseRepository):
    """
    Repository for project data access.

    Encapsulates all project database operations.
    Services use this instead of calling database directly.
    """

    def __init__(self, database: "ProjectDatabase"):
        """
        Initialize project repository.

        Args:
            database: ProjectDatabase instance
        """
        super().__init__(database)

    def save_project(self, project: ProjectContext) -> bool:
        """
        Save or update a project.

        Args:
            project: ProjectContext to save

        Returns:
            True if successful, False otherwise
        """
        self._log_operation("save_project", {"project_id": project.project_id})
        try:
            self.database.save_project(project)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save project {project.project_id}: {e}")
            return False

    def load_project(self, project_id: str) -> Optional[ProjectContext]:
        """
        Load a project by ID.

        Args:
            project_id: Project ID to load

        Returns:
            ProjectContext if found, None otherwise
        """
        self._log_operation("load_project", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project:
                self.logger.debug(f"Loaded project {project_id}")
            else:
                self.logger.debug(f"Project {project_id} not found")
            return project
        except Exception as e:
            self.logger.error(f"Failed to load project {project_id}: {e}")
            return None

    def get_all_projects(self, user_id: str = None) -> List[ProjectContext]:
        """
        Get all projects, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of ProjectContext objects
        """
        self._log_operation("get_all_projects", {"user_id": user_id})
        try:
            # Get all projects from database
            projects = self.database.get_all_projects()
            if user_id:
                # Filter by user_id if provided
                projects = [p for p in projects if p.owner_id == user_id]
            self.logger.debug(f"Retrieved {len(projects)} projects")
            return projects
        except Exception as e:
            self.logger.error(f"Failed to get projects: {e}")
            return []

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete

        Returns:
            True if successful, False otherwise
        """
        self._log_operation("delete_project", {"project_id": project_id})
        try:
            self.database.delete_project(project_id)
            self.logger.debug(f"Deleted project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete project {project_id}: {e}")
            return False

    def project_exists(self, project_id: str) -> bool:
        """
        Check if a project exists.

        Args:
            project_id: Project ID to check

        Returns:
            True if project exists, False otherwise
        """
        try:
            project = self.database.load_project(project_id)
            return project is not None
        except Exception as e:
            self.logger.error(f"Failed to check if project exists: {e}")
            return False
