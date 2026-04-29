"""
Quality Service - Encapsulates quality control and maturity tracking.

Extracted from QualityController agent, this service handles:
- Maturity calculations
- Quality metrics
- Phase advancement logic

No orchestrator dependency - uses dependency injection for all external services.
"""

from typing import Any, Dict, Optional

from socratic_system.config import SocratesConfig
from socratic_system.models import ProjectContext
from socratic_system.services.base import Service
from socratic_system.services.repositories import MaturityRepository


class QualityService(Service):
    """
    Service for quality control and maturity tracking.

    Calculates and manages project maturity metrics without direct
    orchestrator dependency.
    """

    def __init__(
        self,
        config: SocratesConfig,
        repository: MaturityRepository,
    ):
        """
        Initialize quality service.

        Args:
            config: SocratesConfig instance
            repository: MaturityRepository for maturity data persistence
        """
        super().__init__(config)
        self.repository = repository

    def calculate_maturity(self, project: ProjectContext) -> Dict[str, Any]:
        """
        Calculate phase maturity for a project.

        Evaluates project completeness across various categories
        to determine overall maturity level.

        Args:
            project: The ProjectContext to evaluate

        Returns:
            Dictionary containing maturity metrics
        """
        self.log_info(f"Calculating maturity for project {project.project_id}")

        # Initialize metrics
        metrics = {
            "project_id": project.project_id,
            "category_scores": {},
            "overall_score": 0.0,
            "phase": project.phase if hasattr(project, "phase") else "discovery",
            "timestamp": self._get_timestamp(),
        }

        # Calculate category scores
        metrics["category_scores"]["requirements"] = self._score_requirements(project)
        metrics["category_scores"]["architecture"] = self._score_architecture(project)
        metrics["category_scores"]["implementation"] = self._score_implementation(project)
        metrics["category_scores"]["testing"] = self._score_testing(project)
        metrics["category_scores"]["documentation"] = self._score_documentation(project)

        # Calculate overall score
        if metrics["category_scores"]:
            metrics["overall_score"] = sum(metrics["category_scores"].values()) / len(
                metrics["category_scores"]
            )

        # Determine maturity level
        metrics["maturity_level"] = self._determine_maturity_level(metrics["overall_score"])

        # Save metrics
        self.repository.save(metrics)

        self.log_info(
            f"Maturity calculated: {metrics['overall_score']:.1f}% "
            f"({metrics['maturity_level']})"
        )

        return metrics

    def get_maturity(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached maturity metrics for a project.

        Args:
            project_id: The project ID

        Returns:
            Maturity metrics if available, None otherwise
        """
        return self.repository.find_by_id(project_id)

    def update_category_score(
        self, project_id: str, category: str, score: float
    ) -> bool:
        """
        Update a specific category score.

        Args:
            project_id: The project ID
            category: Category name (requirements, architecture, etc.)
            score: New score (0-100)

        Returns:
            True if updated successfully, False otherwise
        """
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100")

        success = self.repository.update_category_score(project_id, category, score)

        if success:
            self.log_info(f"Updated {category} score for {project_id}: {score}")

        return success

    def can_advance_phase(self, project: ProjectContext) -> bool:
        """
        Determine if project can advance to next phase.

        Args:
            project: The ProjectContext to evaluate

        Returns:
            True if project meets criteria for phase advancement
        """
        metrics = self.get_maturity(project.project_id)
        if not metrics:
            return False

        # Minimum maturity required to advance
        required_score = 60.0

        return metrics.get("overall_score", 0) >= required_score

    # Private helper methods

    def _score_requirements(self, project: ProjectContext) -> float:
        """Score completeness of requirements gathering."""
        score = 0.0

        if hasattr(project, "description") and project.description:
            score += 25.0
        if hasattr(project, "goals") and project.goals:
            score += 25.0
        if hasattr(project, "constraints") and project.constraints:
            score += 25.0
        if hasattr(project, "tech_stack") and project.tech_stack:
            score += 25.0

        return min(score, 100.0)

    def _score_architecture(self, project: ProjectContext) -> float:
        """Score architecture design completeness."""
        score = 0.0

        if hasattr(project, "architecture_notes") and project.architecture_notes:
            score += 50.0
        if hasattr(project, "system_design") and project.system_design:
            score += 50.0

        return min(score, 100.0)

    def _score_implementation(self, project: ProjectContext) -> float:
        """Score implementation progress."""
        score = 0.0

        if hasattr(project, "generated_files") and project.generated_files:
            file_count = len(project.generated_files)
            score += min(file_count * 10, 50.0)

        if hasattr(project, "code_sections") and project.code_sections:
            score += 50.0

        return min(score, 100.0)

    def _score_testing(self, project: ProjectContext) -> float:
        """Score testing coverage."""
        score = 0.0

        if hasattr(project, "test_cases") and project.test_cases:
            test_count = len(project.test_cases)
            score += min(test_count * 5, 100.0)

        return min(score, 100.0)

    def _score_documentation(self, project: ProjectContext) -> float:
        """Score documentation completeness."""
        score = 0.0

        if hasattr(project, "documentation") and project.documentation:
            score += 50.0
        if hasattr(project, "readme") and project.readme:
            score += 50.0

        return min(score, 100.0)

    def _determine_maturity_level(self, score: float) -> str:
        """Determine maturity level from score."""
        if score < 20:
            return "initial"
        elif score < 40:
            return "developing"
        elif score < 60:
            return "intermediate"
        elif score < 80:
            return "advanced"
        else:
            return "mature"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
