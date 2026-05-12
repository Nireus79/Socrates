"""Conflict service - encapsulates conflict detection."""

from typing import TYPE_CHECKING, Any

from socratic_system.repositories.conflict_repository import ConflictRepository

from .base import Service

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase
    from socratic_system.models import ProjectContext


class ConflictService(Service):
    """Service for detecting and managing conflicts in project specifications."""

    def __init__(self, config, database: "ProjectDatabase" = None):
        """Initialize conflict service.

        Args:
            config: Socrates configuration
            database: ProjectDatabase instance (for Phase 1) or SocraticAgentsSystem (for Phase 3)
        """
        super().__init__(config)
        # Handle both Phase 1 (database) and Phase 3 (system) initialization
        self.database = database
        self.system = None

        # Check if database is actually a SocraticAgentsSystem (Phase 3)
        # Phase 3 system would have __module__ containing 'socratic_agents'
        if database:
            module_name = getattr(type(database), "__module__", "")
            if "socratic_agents" in module_name.lower():
                self.system = database
                self.database = None

        # Initialize repository for Phase 1 (or default to mock for Phase 3)
        if self.database:
            self.repository = ConflictRepository(self.database)
        else:
            # Mock repository for Phase 3 or when no database
            from unittest.mock import MagicMock

            self.repository = ConflictRepository(MagicMock())

    def detect_conflicts(
        self,
        project_id: str,
        project: "ProjectContext" = None,
        insights: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Detect conflicts in project specifications.

        Args:
            project_id: Project identifier
            project: ProjectContext (optional for Phase 3)
            insights: Insights to check for conflicts

        Returns:
            Dict with status and detected conflicts
        """
        self.logger.info(f"Detecting conflicts for project {project_id}")

        if self.system:
            # Phase 3: Use orchestrator
            result = self.system.process_request(  # type: ignore
                "conflict_detector",
                {
                    "action": "detect_conflicts",
                    "project": project,
                    "new_insights": insights,
                },
            )
            return result.get("conflicts", [])

        # Phase 1: Simple heuristic detection
        detected = []
        if insights:
            # Example: detect conflicting requirements
            for _key, value in insights.items():
                if isinstance(value, str) and "conflict" in value.lower():
                    detected.append(
                        {
                            "type": "requirement",
                            "severity": "medium",
                            "description": value,
                        }
                    )

        return {
            "status": "success",
            "conflicts": detected,
        }

    def resolve_conflict(
        self,
        project_id: str,
        conflict_index: int,
        resolution: str,
        resolution_details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve a specific conflict.

        Args:
            project_id: Project identifier
            conflict_index: Index of conflict in project's conflicts list
            resolution: Chosen resolution
            resolution_details: Additional resolution details

        Returns:
            Dict with status and result
        """
        self.logger.info(f"Resolving conflict at index {conflict_index}")

        if self.system:
            # Phase 3: Use orchestrator
            self.system.process_request(  # type: ignore
                "conflict_detector",
                {
                    "action": "resolve_conflict",
                    "conflict_index": conflict_index,
                    "resolution": resolution,
                    "details": resolution_details,
                },
            )
            return {"status": "success"}

        # Phase 1: Update repository
        result = self.repository.resolve_conflict(
            project_id, conflict_index, resolution, resolution_details
        )
        return {"status": "success" if result else "failed"}

    def get_project_conflicts(self, project_id: str) -> dict[str, Any]:
        """Get all conflicts for a project, organized by type.

        Args:
            project_id: Project identifier

        Returns:
            Dict with conflicts organized by type
        """
        self.logger.info(f"Getting conflicts for project {project_id}")

        conflicts = self.repository.get_project_conflicts(project_id)
        by_type: dict[str, list[dict[str, Any]]] = {}

        for conflict in conflicts:
            conflict_type = conflict.get("conflict_type", "unknown")
            if conflict_type not in by_type:
                by_type[conflict_type] = []
            by_type[conflict_type].append(conflict)

        return {
            "status": "success",
            "total": len(conflicts),
            "by_type": by_type,
            "conflicts": conflicts,
        }

    def get_unresolved_conflicts(self, project_id: str) -> dict[str, Any]:
        """Get unresolved conflicts for a project.

        Args:
            project_id: Project identifier

        Returns:
            Dict with unresolved conflicts
        """
        self.logger.info(f"Getting unresolved conflicts for project {project_id}")

        conflicts = self.repository.get_unresolved_conflicts(project_id)
        return {
            "status": "success",
            "count": len(conflicts),
            "conflicts": conflicts,
        }

    def get_high_severity_conflicts(self, project_id: str) -> dict[str, Any]:
        """Get high severity conflicts for a project.

        Args:
            project_id: Project identifier

        Returns:
            Dict with high severity conflicts
        """
        self.logger.info(f"Getting high severity conflicts for project {project_id}")

        conflicts = self.repository.get_high_severity_conflicts(project_id)
        return {
            "status": "success",
            "count": len(conflicts),
            "conflicts": conflicts,
        }

    def get_conflict_suggestions(
        self, project_id: str, conflict_index: int | None = None
    ) -> dict[str, Any]:
        """Get suggestions for resolving conflicts.

        Args:
            project_id: Project identifier
            conflict_index: Optional specific conflict index

        Returns:
            Dict with suggested resolutions
        """
        self.logger.info(f"Getting conflict suggestions for project {project_id}")

        conflicts = self.repository.get_project_conflicts(project_id)
        suggestions = []

        for i, conflict in enumerate(conflicts):
            if conflict_index is None or i == conflict_index:
                # Get suggestions from conflict details
                details = conflict.get("details", {})
                if "suggestions" in details:
                    suggestions.extend(details["suggestions"])
                else:
                    suggestions.append(
                        f"Review and resolve {conflict.get('conflict_type')} conflict"
                    )

        return {
            "status": "success",
            "count": len(suggestions),
            "suggestions": suggestions,
        }

    def clear_project_conflicts(self, project_id: str) -> dict[str, Any]:
        """Clear all conflicts for a project.

        Args:
            project_id: Project identifier

        Returns:
            Result dict
        """
        self.logger.info(f"Clearing conflicts for project {project_id}")

        result = self.repository.clear_conflicts(project_id)
        return {
            "status": "success" if result else "failed",
            "cleared": result,
        }
