"""Quality service - encapsulates quality control and maturity tracking."""

from typing import TYPE_CHECKING, Dict, Any, Optional

from socratic_system.core.maturity_calculator import MaturityCalculator
from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.repositories.quality_repository import QualityRepository

from .base import Service

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext
    from socratic_system.database import ProjectDatabase


class QualityService(Service):
    """Service for quality control and phase maturity tracking.

    Uses pure calculation logic (MaturityCalculator, AnalyticsCalculator)
    with repository pattern for data access.
    """

    def __init__(self, config, database: "ProjectDatabase", project_type: str = "software"):
        """Initialize quality service.

        Args:
            config: Socrates configuration
            database: ProjectDatabase instance
            project_type: Type of project (software, business, creative, etc.)
        """
        super().__init__(config)
        self.database = database
        self.repository = QualityRepository(database)
        self.calculator = MaturityCalculator(project_type=project_type)
        self.analytics = AnalyticsCalculator(project_type=project_type)
        self.project_type = project_type

    def calculate_maturity(self, project: "ProjectContext") -> Dict[str, Any]:
        """Calculate phase maturity for project.

        Args:
            project: ProjectContext

        Returns:
            Maturity metrics dict
        """
        self.logger.info(f"Calculating maturity for project {project.project_id}")

        # Get specs for current phase
        phase_specs = self.repository.get_categorized_specs(project.project_id, project.phase)

        # Calculate maturity
        maturity = self.calculator.calculate_phase_maturity(phase_specs, project.phase)

        # Store result
        self.repository.update_phase_maturity_score(
            project.project_id,
            project.phase,
            maturity.overall_score
        )

        return {
            "phase": maturity.phase,
            "overall_score": maturity.overall_score,
            "is_ready_to_advance": maturity.is_ready_to_advance,
            "warnings": maturity.warnings,
            "missing_categories": maturity.missing_categories,
        }

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

        # Categorize insights
        if insights:
            specs = self.calculator.categorize_insights(insights, project.phase)
            for spec in specs:
                self.repository.add_categorized_specs(project.project_id, spec)

        # Recalculate maturity
        return self.calculate_maturity(project)

    def update_maturity_after_response(
        self, project: "ProjectContext", insights: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Update maturity after processing user response.

        Args:
            project: ProjectContext
            insights: Insights extracted from response

        Returns:
            Updated maturity metrics
        """
        return self.calculate_post_response_maturity(project, insights)

    def get_maturity_summary(self, project_id: str) -> Dict[str, Any]:
        """Get complete maturity summary for project.

        Args:
            project_id: Project ID

        Returns:
            Summary dict with all maturity metrics
        """
        self.logger.info(f"Getting maturity summary for {project_id}")
        scores = self.repository.get_phase_maturity_scores(project_id)
        return {
            "project_id": project_id,
            "phase_scores": scores,
            "overall_maturity": sum(scores.values()) / len(scores) if scores else 0,
        }

    def get_maturity_history(self, project_id: str) -> Dict[str, Any]:
        """Get maturity history for project.

        Args:
            project_id: Project ID

        Returns:
            History dict
        """
        self.logger.info(f"Getting maturity history for {project_id}")
        return self.repository.get_maturity_history(project_id)

    def update_analytics_metrics(self, project: "ProjectContext") -> Dict[str, Any]:
        """Update analytics metrics for project.

        Args:
            project: ProjectContext

        Returns:
            Analytics metrics dict
        """
        self.logger.info(f"Updating analytics metrics for {project.project_id}")
        analytics = self.analytics.analyze_category_performance(project)
        self.repository.update_analytics_metrics(project.project_id, analytics)
        return analytics
