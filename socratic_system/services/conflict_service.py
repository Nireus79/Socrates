"""Conflict service - encapsulates conflict detection."""

from typing import TYPE_CHECKING, Dict, Any, Optional, List

from .base import Service

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext
    from socratic_system.orchestration import AgentOrchestrator


class ConflictService(Service):
    """Service for detecting and managing conflicts in project specifications."""

    def __init__(self, config, orchestrator: "AgentOrchestrator"):
        """Initialize conflict service.

        Args:
            config: Socrates configuration
            orchestrator: Agent orchestrator
        """
        super().__init__(config)
        self.orchestrator = orchestrator

    def detect_conflicts(
        self,
        project: "ProjectContext",
        new_insights: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Detect conflicts in project specifications.

        Args:
            project: ProjectContext
            new_insights: New insights to check for conflicts
            user_id: User identifier

        Returns:
            List of detected conflicts
        """
        self.logger.info(f"Detecting conflicts for project {project.project_id}")

        result = self.orchestrator.process_request(
            "conflict_detector",
            {
                "action": "detect_conflicts",
                "project": project,
                "new_insights": new_insights,
                "user_id": user_id,
            },
        )

        return result.get("conflicts", [])

    def resolve_conflict(
        self,
        project: "ProjectContext",
        conflict_id: str,
        resolution: str,
    ) -> bool:
        """Resolve a specific conflict.

        Args:
            project: ProjectContext
            conflict_id: Conflict identifier
            resolution: Chosen resolution

        Returns:
            True if resolved successfully
        """
        self.logger.info(f"Resolving conflict {conflict_id}")

        # Update project with resolution
        self.orchestrator.process_request(
            "conflict_detector",
            {
                "action": "resolve_conflict",
                "project": project,
                "conflict_id": conflict_id,
                "resolution": resolution,
            },
        )

        return True
