"""
ConflictService - Business logic for conflict detection and resolution.

Extracted from ConflictDetectorAgent.
Uses ConflictRepository for all data access (not direct database calls).
Focuses on conflict detection, resolution, and suggestion generation.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from socratic_system.repositories.conflict_repository import ConflictRepository

try:
    from socratic_conflict import (
        ConstraintsConflictChecker,
        GoalsConflictChecker,
        RequirementsConflictChecker,
        TechStackConflictChecker,
    )
    CONFLICT_CHECKERS_AVAILABLE = True
except ImportError:
    CONFLICT_CHECKERS_AVAILABLE = False

from .base_service import BaseService

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig
    from socratic_system.models import ProjectContext


class ConflictService(BaseService):
    """
    Service for conflict detection and resolution.

    Receives only required dependencies via DI (no orchestrator coupling).
    Uses repository pattern for all data access.
    """

    def __init__(self, config: "SocratesConfig", database):
        """
        Initialize conflict service.

        Args:
            config: SocratesConfig instance
            database: ProjectDatabase instance for repository initialization
        """
        super().__init__(config)
        self.repository = ConflictRepository(database)

        # Initialize conflict checkers from socratic_conflict library
        self.checkers = []
        if CONFLICT_CHECKERS_AVAILABLE:
            # Note: Checkers may need orchestrator; we'll pass None for now
            # and let them handle gracefully or use alternative approach
            try:
                self.checkers = [
                    TechStackConflictChecker(None),
                    RequirementsConflictChecker(None),
                    GoalsConflictChecker(None),
                    ConstraintsConflictChecker(None),
                ]
                self.logger.info(
                    f"Initialized {len(self.checkers)} conflict checkers"
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to initialize conflict checkers: {e}"
                )
                self.checkers = []
        else:
            self.logger.warning(
                "socratic_conflict library not available for conflict detection"
            )

    def detect_conflicts(
        self,
        project_id: str,
        project: "ProjectContext",
        new_insights: Dict[str, Any],
        current_user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect conflicts in new insights.

        Uses pluggable checkers in parallel for efficient detection.

        Args:
            project_id: Project ID
            project: ProjectContext object
            new_insights: Dict of new insights to check
            current_user: User ID for context

        Returns:
            Dict with detected conflicts
        """
        self._log_operation(
            "detect_conflicts",
            {"project_id": project_id, "insights_count": len(new_insights)},
        )

        try:
            if not new_insights or not isinstance(new_insights, dict):
                self.logger.debug("No insights to check for conflicts")
                return {"status": "success", "conflicts": []}

            all_conflicts = []

            # Run checkers in parallel if available
            if self.checkers:
                with ThreadPoolExecutor(max_workers=len(self.checkers)) as executor:
                    futures = {
                        executor.submit(
                            checker.check_conflicts,
                            project,
                            new_insights,
                            current_user,
                        ): checker
                        for checker in self.checkers
                    }

                    for future in as_completed(futures):
                        checker = futures[future]
                        try:
                            conflicts = future.result()
                            if conflicts:
                                all_conflicts.extend(conflicts)
                                self.logger.debug(
                                    f"Found {len(conflicts)} conflicts from "
                                    f"{checker.__class__.__name__}"
                                )
                        except Exception as e:
                            self.logger.warning(
                                f"Error in checker {checker.__class__.__name__}: {e}"
                            )

            # Store detected conflicts in repository
            for conflict in all_conflicts:
                conflict_type = conflict.get("type", "unknown")
                severity = conflict.get("severity", "medium")
                description = conflict.get("description", "")
                details = {
                    k: v for k, v in conflict.items()
                    if k not in ["type", "severity", "description"]
                }
                self.repository.add_conflict(
                    project_id,
                    conflict_type,
                    severity,
                    description,
                    details,
                )

            self.logger.info(
                f"Detected {len(all_conflicts)} conflicts for project {project_id}"
            )

            return {
                "status": "success",
                "conflicts": all_conflicts,
                "count": len(all_conflicts),
            }

        except Exception as e:
            self.logger.error(f"Error detecting conflicts: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def resolve_conflict(
        self,
        project_id: str,
        conflict_index: int,
        resolution: str,
        resolution_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a detected conflict.

        Args:
            project_id: Project ID
            conflict_index: Index of conflict to resolve
            resolution: Resolution description
            resolution_details: Additional resolution details

        Returns:
            Dict with resolution status
        """
        self._log_operation(
            "resolve_conflict",
            {"project_id": project_id, "conflict_index": conflict_index},
        )

        try:
            result = self.repository.resolve_conflict(
                project_id,
                conflict_index,
                resolution,
                resolution_details,
            )

            if result:
                self.logger.info(
                    f"Resolved conflict {conflict_index} for project {project_id}"
                )
                return {
                    "status": "success",
                    "message": "Conflict resolved",
                    "conflict_index": conflict_index,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to resolve conflict {conflict_index}",
                }

        except Exception as e:
            self.logger.error(f"Error resolving conflict: {type(e).__name__}: {e}")
            return {"status": "error", "message": str(e)}

    def get_conflict_suggestions(
        self,
        project_id: str,
        conflict_index: int,
    ) -> Dict[str, Any]:
        """
        Get suggestions for resolving a conflict.

        Args:
            project_id: Project ID
            conflict_index: Index of conflict

        Returns:
            Dict with suggestions
        """
        self._log_operation(
            "get_conflict_suggestions",
            {"project_id": project_id, "conflict_index": conflict_index},
        )

        try:
            conflicts = self.repository.get_project_conflicts(project_id)

            if (
                not conflicts
                or conflict_index < 0
                or conflict_index >= len(conflicts)
            ):
                return {
                    "status": "error",
                    "message": f"Conflict {conflict_index} not found",
                }

            conflict = conflicts[conflict_index]
            suggestions = conflict.get("details", {}).get("suggestions", [])

            self.logger.debug(
                f"Retrieved {len(suggestions)} suggestions for conflict {conflict_index}"
            )

            return {
                "status": "success",
                "suggestions": suggestions,
                "conflict": conflict,
            }

        except Exception as e:
            self.logger.error(
                f"Error getting conflict suggestions: {type(e).__name__}: {e}"
            )
            return {"status": "error", "message": str(e)}

    def get_project_conflicts(
        self, project_id: str
    ) -> Dict[str, Any]:
        """
        Get all conflicts for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with all conflicts organized by type
        """
        self._log_operation("get_project_conflicts", {"project_id": project_id})

        try:
            conflicts = self.repository.get_project_conflicts(project_id)

            # Organize by type
            by_type = {}
            for conflict in conflicts:
                conflict_type = conflict.get("conflict_type", "unknown")
                if conflict_type not in by_type:
                    by_type[conflict_type] = []
                by_type[conflict_type].append(conflict)

            self.logger.debug(
                f"Retrieved {len(conflicts)} total conflicts for {project_id}"
            )

            return {
                "status": "success",
                "total": len(conflicts),
                "by_type": by_type,
                "conflicts": conflicts,
            }

        except Exception as e:
            self.logger.error(
                f"Error getting project conflicts: {type(e).__name__}: {e}"
            )
            return {"status": "error", "message": str(e)}

    def get_unresolved_conflicts(
        self, project_id: str
    ) -> Dict[str, Any]:
        """
        Get all unresolved conflicts for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with unresolved conflicts
        """
        self._log_operation(
            "get_unresolved_conflicts", {"project_id": project_id}
        )

        try:
            conflicts = self.repository.get_unresolved_conflicts(project_id)
            self.logger.debug(
                f"Found {len(conflicts)} unresolved conflicts for {project_id}"
            )
            return {
                "status": "success",
                "count": len(conflicts),
                "conflicts": conflicts,
            }

        except Exception as e:
            self.logger.error(
                f"Error getting unresolved conflicts: {type(e).__name__}: {e}"
            )
            return {"status": "error", "message": str(e)}

    def get_high_severity_conflicts(
        self, project_id: str
    ) -> Dict[str, Any]:
        """
        Get high severity conflicts (high and critical).

        Args:
            project_id: Project ID

        Returns:
            Dict with high severity conflicts
        """
        self._log_operation(
            "get_high_severity_conflicts", {"project_id": project_id}
        )

        try:
            conflicts = self.repository.get_high_severity_conflicts(project_id)
            self.logger.debug(
                f"Found {len(conflicts)} high severity conflicts for {project_id}"
            )
            return {
                "status": "success",
                "count": len(conflicts),
                "conflicts": conflicts,
            }

        except Exception as e:
            self.logger.error(
                f"Error getting high severity conflicts: {type(e).__name__}: {e}"
            )
            return {"status": "error", "message": str(e)}

    def clear_project_conflicts(self, project_id: str) -> Dict[str, Any]:
        """
        Clear all conflicts for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with operation status
        """
        self._log_operation("clear_project_conflicts", {"project_id": project_id})

        try:
            result = self.repository.clear_conflicts(project_id)

            if result:
                self.logger.info(f"Cleared all conflicts for project {project_id}")
                return {
                    "status": "success",
                    "message": "All conflicts cleared",
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to clear conflicts",
                }

        except Exception as e:
            self.logger.error(
                f"Error clearing conflicts: {type(e).__name__}: {e}"
            )
            return {"status": "error", "message": str(e)}
