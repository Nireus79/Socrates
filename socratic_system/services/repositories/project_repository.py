"""
Project Repository - Data access layer for project persistence.

Encapsulates all project-related database operations, providing a clean
interface for services to work with projects without knowing the underlying
database schema or operations.
"""

from typing import Any, List, Optional

from socratic_system.database import ProjectDatabase
from socratic_system.models import ProjectContext
from socratic_system.services.repositories.base import Repository


class ProjectRepository(Repository[ProjectContext]):
    """
    Repository for project persistence.

    Provides CRUD operations for projects while abstracting the database
    implementation details from services.
    """

    def __init__(self, database: ProjectDatabase):
        """
        Initialize project repository.

        Args:
            database: ProjectDatabase instance for data access
        """
        self.database = database

    def save(self, project: ProjectContext) -> ProjectContext:
        """
        Save or update a project.

        Args:
            project: The project to save

        Returns:
            The saved project
        """
        self.database.save_project(project)
        return project

    def find_by_id(self, project_id: str) -> Optional[ProjectContext]:
        """
        Find project by ID.

        Args:
            project_id: The ID of the project

        Returns:
            The project if found, None otherwise
        """
        return self.database.load_project(project_id)

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ProjectContext]:
        """
        Find all projects with optional pagination.

        Args:
            limit: Maximum number of projects to return
            offset: Number of projects to skip

        Returns:
            List of projects
        """
        # Delegate to database implementation
        projects = self.database.get_all_projects()

        # Apply pagination
        if offset > 0:
            projects = projects[offset:]
        if limit is not None:
            projects = projects[:limit]

        return projects

    def delete(self, project_id: str) -> bool:
        """
        Delete project by ID.

        Args:
            project_id: The ID of the project to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            self.database.delete_project(project_id)
            return True
        except Exception:
            return False

    def exists(self, project_id: str) -> bool:
        """
        Check if project exists.

        Args:
            project_id: The project ID to check

        Returns:
            True if exists, False otherwise
        """
        return self.find_by_id(project_id) is not None

    def find_by_user(self, user_id: str) -> List[ProjectContext]:
        """
        Find all projects for a user.

        Args:
            user_id: The user ID

        Returns:
            List of projects belonging to the user
        """
        return self.database.get_user_projects(user_id)

    def get_project_count(self) -> int:
        """
        Get total number of projects.

        Returns:
            Number of projects in the database
        """
        return len(self.database.get_all_projects())
