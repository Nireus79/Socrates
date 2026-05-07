"""Quality service - encapsulates quality control and maturity tracking."""

from typing import TYPE_CHECKING, Any, Dict, Optional

from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.core.maturity_calculator import MaturityCalculator
from socratic_system.repositories.quality_repository import QualityRepository

from .base import Service

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase
    from socratic_system.models import ProjectContext


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

    def calculate_phase_maturity(self, project_id: str, project: "ProjectContext") -> Dict[str, Any]:
        """Calculate phase maturity for project.

        Args:
            project_id: Project ID
            project: ProjectContext

        Returns:
            Maturity metrics dict
        """
        self.logger.info(f"Calculating maturity for project {project_id}")

        # Get specs for current phase
        all_specs = self.repository.get_categorized_specs(project_id)
        phase_specs = all_specs.get(project.phase, [])

        # Calculate maturity
        maturity = self.calculator.calculate_phase_maturity(phase_specs, project.phase)

        # Store result
        self.repository.update_phase_maturity_score(
            project_id,
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

    def update_maturity_after_response(
        self, project_id: str, project: "ProjectContext", insights: Optional[Dict] = None, user_id: str = None
    ) -> Dict[str, Any]:
        """Update maturity after processing user response.

        Args:
            project_id: Project ID
            project: ProjectContext
            insights: Insights extracted from response
            user_id: Optional user ID for API key lookup

        Returns:
            Updated maturity metrics dict
        """
        self.logger.info(f"Updating maturity after response for {project_id}")

        # Get score before (from project object if available, otherwise from repository)
        if hasattr(project, "phase_maturity_scores"):
            score_before = project.phase_maturity_scores.get(project.phase, 0.0)
        else:
            score_before = self.repository.get_phase_maturity_scores(project_id).get(project.phase, 0.0)
        answer_score = 0.0

        # Categorize insights if provided
        if insights:
            specs = self.calculator.categorize_insights(insights, project.phase, user_id=user_id)
            if specs:
                self.repository.add_categorized_specs(project_id, project.phase, specs)
                # Calculate answer score as sum of confidence-weighted values
                answer_score = sum(s.get("value", 1.0) * s.get("confidence", 0.9) for s in specs)
            else:
                return {
                    "status": "success",
                    "message": "No new specs added"
                }

        # Recalculate maturity
        maturity_result = self.calculate_phase_maturity(project_id, project)

        # Get score after (from project's overall maturity if available, otherwise from maturity result)
        if hasattr(project, "_calculate_overall_maturity") and callable(project._calculate_overall_maturity):
            score_after = project._calculate_overall_maturity()
        else:
            score_after = maturity_result.get("overall_score", score_before)

        # Update analytics
        self.update_analytics_metrics(project_id, project)

        return {
            "status": "success",
            "score_before": score_before,
            "answer_score": answer_score,
            "score_after": score_after,
            "project_id": project_id,
            "phase": project.phase,
        }

    def get_maturity_summary(self, project_id: str, project: "ProjectContext" = None) -> Dict[str, Any]:
        """Get complete maturity summary for project.

        Args:
            project_id: Project ID
            project: Optional ProjectContext (for getting thresholds)

        Returns:
            Summary dict with all maturity metrics
        """
        self.logger.info(f"Getting maturity summary for {project_id}")

        # Get scores from project object if available, otherwise from repository
        if project and hasattr(project, "phase_maturity_scores"):
            scores = project.phase_maturity_scores
        else:
            scores = self.repository.get_phase_maturity_scores(project_id)

        # Build summary with thresholds
        summary = {}
        for phase, score in scores.items():
            summary[phase] = {
                "score": score,
                "ready": score >= self.calculator.READY_THRESHOLD,
                "complete": score >= self.calculator.COMPLETE_THRESHOLD,
            }

        return {
            "status": "success",
            "project_id": project_id,
            "summary": summary,
        }

    def get_maturity_history(self, project_id: str) -> Dict[str, Any]:
        """Get maturity history for project.

        Args:
            project_id: Project ID

        Returns:
            Dict with status, total_events, and history list
        """
        self.logger.info(f"Getting maturity history for {project_id}")
        events = self.repository.get_maturity_history(project_id)
        return {
            "status": "success",
            "total_events": len(events),
            "history": events,
        }

    def update_analytics_metrics(self, project_id: str, project: "ProjectContext") -> bool:
        """Update analytics metrics for project.

        Args:
            project_id: Project ID
            project: ProjectContext

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating analytics metrics for {project_id}")
        try:
            # Calculate metrics from project data
            metrics = self._calculate_analytics_metrics(project)
            self.repository.update_analytics_metrics(project_id, metrics)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update analytics metrics for {project_id}: {e}")
            return False

    def _calculate_analytics_metrics(self, project: "ProjectContext") -> Dict[str, Any]:
        """Calculate analytics metrics from project data.

        Args:
            project: ProjectContext

        Returns:
            Dict of analytics metrics
        """
        metrics = {}

        # Calculate velocity from maturity history
        if hasattr(project, "maturity_history") and project.maturity_history:
            deltas = [e.get("delta", 0) for e in project.maturity_history if e.get("event_type") == "response_processed"]
            if deltas:
                metrics["velocity"] = sum(deltas) / len(deltas)
                metrics["total_qa_sessions"] = len(deltas)

        # Calculate average confidence from categorized specs
        if hasattr(project, "categorized_specs") and project.categorized_specs:
            all_specs = []
            for phase_specs in project.categorized_specs.values():
                all_specs.extend(phase_specs)
            if all_specs:
                avg_confidence = sum(s.get("confidence", 0.9) for s in all_specs) / len(all_specs)
                metrics["avg_confidence"] = avg_confidence

        # Use analytics calculator for additional metrics
        try:
            additional_metrics = self.analytics.analyze_category_performance(project)
            if isinstance(additional_metrics, dict):
                metrics.update(additional_metrics)
        except Exception:
            pass  # Fall back to calculated metrics

        return metrics
