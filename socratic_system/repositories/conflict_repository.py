"""
ConflictRepository - Data access for project conflicts.

Abstracts all conflict detection and resolution database operations.
Used by ConflictService instead of direct database calls.

This is the single point of change for conflict schema updates.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base_repository import BaseRepository

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase


class ConflictRepository(BaseRepository):
    """
    Repository for conflict data access.

    Encapsulates all conflict detection and resolution database operations.
    Services use this instead of calling database directly.
    """

    def __init__(self, database: "ProjectDatabase"):
        """
        Initialize conflict repository.

        Args:
            database: ProjectDatabase instance
        """
        super().__init__(database)

    def get_project_conflicts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all conflicts for a project.

        Args:
            project_id: Project ID

        Returns:
            List of conflict dicts
        """
        self._log_operation("get_project_conflicts", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project and hasattr(project, "conflicts"):
                return project.conflicts if project.conflicts else []
            return []
        except Exception as e:
            self.logger.error(f"Failed to get conflicts for {project_id}: {e}")
            return []

    def add_conflict(
        self,
        project_id: str,
        conflict_type: str,
        severity: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a detected conflict to project.

        Args:
            project_id: Project ID
            conflict_type: Type of conflict (requirements, tech_stack, etc.)
            severity: Severity level (low, medium, high, critical)
            description: Conflict description
            details: Additional conflict details

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "add_conflict",
            {
                "project_id": project_id,
                "conflict_type": conflict_type,
                "severity": severity,
            },
        )
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            # Initialize conflicts list if not exists
            if not hasattr(project, "conflicts"):
                project.conflicts = []

            conflict = {
                "conflict_type": conflict_type,
                "severity": severity,
                "description": description,
                "details": details or {},
                "status": "unresolved",
                "created_at": __import__("datetime").datetime.now().isoformat(),
            }

            project.conflicts.append(conflict)
            self.database.save_project(project)
            self.logger.debug(
                f"Added {conflict_type} conflict to project {project_id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to add conflict for {project_id}: {e}")
            return False

    def resolve_conflict(
        self,
        project_id: str,
        conflict_index: int,
        resolution: str,
        resolution_details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark a conflict as resolved.

        Args:
            project_id: Project ID
            conflict_index: Index of conflict in project.conflicts list
            resolution: Resolution description
            resolution_details: Additional resolution details

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "resolve_conflict",
            {"project_id": project_id, "conflict_index": conflict_index},
        )
        try:
            project = self.database.load_project(project_id)
            if not project or not hasattr(project, "conflicts"):
                self.logger.error(f"Project {project_id} or conflicts not found")
                return False

            if conflict_index < 0 or conflict_index >= len(project.conflicts):
                self.logger.error(f"Invalid conflict index: {conflict_index}")
                return False

            conflict = project.conflicts[conflict_index]
            conflict["status"] = "resolved"
            conflict["resolution"] = resolution
            conflict["resolution_details"] = resolution_details or {}
            conflict["resolved_at"] = __import__("datetime").datetime.now().isoformat()

            self.database.save_project(project)
            self.logger.debug(
                f"Resolved conflict {conflict_index} in project {project_id}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to resolve conflict for {project_id}: {e}"
            )
            return False

    def get_unresolved_conflicts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all unresolved conflicts for a project.

        Args:
            project_id: Project ID

        Returns:
            List of unresolved conflict dicts
        """
        self._log_operation(
            "get_unresolved_conflicts", {"project_id": project_id}
        )
        try:
            conflicts = self.get_project_conflicts(project_id)
            unresolved = [c for c in conflicts if c.get("status") == "unresolved"]
            self.logger.debug(
                f"Found {len(unresolved)} unresolved conflicts for {project_id}"
            )
            return unresolved
        except Exception as e:
            self.logger.error(
                f"Failed to get unresolved conflicts for {project_id}: {e}"
            )
            return []

    def get_conflicts_by_type(
        self, project_id: str, conflict_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get conflicts of a specific type.

        Args:
            project_id: Project ID
            conflict_type: Type of conflict to filter by

        Returns:
            List of conflicts matching the type
        """
        self._log_operation(
            "get_conflicts_by_type",
            {"project_id": project_id, "conflict_type": conflict_type},
        )
        try:
            conflicts = self.get_project_conflicts(project_id)
            filtered = [c for c in conflicts if c.get("conflict_type") == conflict_type]
            self.logger.debug(
                f"Found {len(filtered)} {conflict_type} conflicts for {project_id}"
            )
            return filtered
        except Exception as e:
            self.logger.error(
                f"Failed to get {conflict_type} conflicts for {project_id}: {e}"
            )
            return []

    def get_high_severity_conflicts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get high severity conflicts (high and critical).

        Args:
            project_id: Project ID

        Returns:
            List of high severity conflicts
        """
        self._log_operation(
            "get_high_severity_conflicts", {"project_id": project_id}
        )
        try:
            conflicts = self.get_project_conflicts(project_id)
            high_severity = [
                c for c in conflicts
                if c.get("severity") in ["high", "critical"]
            ]
            self.logger.debug(
                f"Found {len(high_severity)} high severity conflicts for {project_id}"
            )
            return high_severity
        except Exception as e:
            self.logger.error(
                f"Failed to get high severity conflicts for {project_id}: {e}"
            )
            return []

    def clear_conflicts(self, project_id: str) -> bool:
        """
        Clear all conflicts for a project.

        Args:
            project_id: Project ID

        Returns:
            True if successful, False otherwise
        """
        self._log_operation("clear_conflicts", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            project.conflicts = []
            self.database.save_project(project)
            self.logger.debug(f"Cleared all conflicts for project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear conflicts for {project_id}: {e}")
            return False
