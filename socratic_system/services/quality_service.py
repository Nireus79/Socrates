"""Quality service - encapsulates quality control and maturity tracking."""

from typing import TYPE_CHECKING, Dict, Any, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_agents import SocraticAgentsSystem
    from socratic_system.models import ProjectContext


class QualityService(Service):
    """Service for quality control and phase maturity tracking.

    Phase 3: Refactored to use SocraticAgentsSystem instead of orchestrator.
    """

    def __init__(self, config, system: "SocraticAgentsSystem"):
        """Initialize quality service.

        Args:
            config: Socrates configuration
            system: SocraticAgentsSystem instance
        """
        super().__init__(config)
        self.system = system

    def calculate_maturity(self, project: "ProjectContext") -> Dict[str, Any]:
        """Calculate phase maturity for project.

        Args:
            project: ProjectContext

        Returns:
            Maturity metrics dict
        """
        self.logger.info(f"Calculating maturity for project {project.project_id}")

        result = self.system.process_request(
            "quality_controller",
            {
                "action": "get_phase_maturity",
                "project": project,
            },
        )

        return result.get("maturity", {})

    def calculate_post_response_maturity(
        self, project: "ProjectContext", insights: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Calculate maturity after user response.

        Args:
            project: ProjectContext
            insights: Extracted insights from response

        Returns:
            Updated maturity metrics
        """
        self.logger.info(f"Calculating post-response maturity for {project.project_id}")

        result = self.system.process_request(
            "quality_controller",
            {
                "action": "update_after_response",
                "project": project,
                "insights": insights,
            },
        )

        return result.get("maturity", {})
