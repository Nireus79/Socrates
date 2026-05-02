"""
QualityRepository - Data access for quality and maturity metrics.

Abstracts all quality/maturity database operations.
Used by QualityService instead of direct database calls.

This is the single point of change for maturity schema updates.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from socratic_system.models import ProjectContext

from .base_repository import BaseRepository

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase


class QualityRepository(BaseRepository):
    """
    Repository for quality and maturity data access.

    Encapsulates all maturity calculation and analytics database operations.
    Services use this instead of calling database directly.
    """

    def __init__(self, database: "ProjectDatabase"):
        """
        Initialize quality repository.

        Args:
            database: ProjectDatabase instance
        """
        super().__init__(database)

    def get_phase_maturity_scores(self, project_id: str) -> Dict[str, float]:
        """
        Get all phase maturity scores for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict mapping phase to maturity score
        """
        self._log_operation("get_phase_maturity_scores", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project:
                return project.phase_maturity_scores
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get phase maturity scores for {project_id}: {e}")
            return {}

    def update_phase_maturity_score(
        self, project_id: str, phase: str, score: float
    ) -> bool:
        """
        Update maturity score for a specific phase.

        Args:
            project_id: Project ID
            phase: Phase name
            score: New maturity score (0-100)

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "update_phase_maturity_score",
            {"project_id": project_id, "phase": phase, "score": score},
        )
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            # Update the score (clamped to 0-100)
            project.phase_maturity_scores[phase] = min(100.0, max(0.0, score))

            # Recalculate overall maturity
            project.overall_maturity = project._calculate_overall_maturity()
            project.progress = int(project.overall_maturity)

            # Save updated project
            self.database.save_project(project)
            self.logger.debug(
                f"Updated phase {phase} maturity for project {project_id} to {score:.1f}%"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to update phase maturity for {project_id}/{phase}: {e}"
            )
            return False

    def get_category_scores(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get category scores for all phases.

        Args:
            project_id: Project ID

        Returns:
            Dict mapping phase to category scores
        """
        self._log_operation("get_category_scores", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project:
                return project.category_scores
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get category scores for {project_id}: {e}")
            return {}

    def update_category_scores(
        self, project_id: str, phase: str, category_scores: Dict[str, Any]
    ) -> bool:
        """
        Update category scores for a phase.

        Args:
            project_id: Project ID
            phase: Phase name
            category_scores: Dict of category -> score data

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "update_category_scores",
            {"project_id": project_id, "phase": phase},
        )
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            project.category_scores[phase] = category_scores
            self.database.save_project(project)
            self.logger.debug(f"Updated category scores for {project_id}/{phase}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update category scores for {project_id}: {e}")
            return False

    def get_analytics_metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Get analytics metrics for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict of analytics metrics
        """
        self._log_operation("get_analytics_metrics", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project:
                return project.analytics_metrics
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get analytics metrics for {project_id}: {e}")
            return {}

    def update_analytics_metrics(
        self, project_id: str, metrics: Dict[str, Any]
    ) -> bool:
        """
        Update analytics metrics for a project.

        Args:
            project_id: Project ID
            metrics: Dict of analytics metrics to update

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "update_analytics_metrics", {"project_id": project_id}
        )
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            project.analytics_metrics.update(metrics)
            self.database.save_project(project)
            self.logger.debug(f"Updated analytics metrics for {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update analytics metrics for {project_id}: {e}")
            return False

    def get_maturity_history(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get maturity history for a project.

        Args:
            project_id: Project ID

        Returns:
            List of maturity history events
        """
        self._log_operation("get_maturity_history", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project:
                return project.maturity_history
            return []
        except Exception as e:
            self.logger.error(f"Failed to get maturity history for {project_id}: {e}")
            return []

    def add_maturity_event(
        self, project_id: str, event: Dict[str, Any]
    ) -> bool:
        """
        Add a maturity event to history.

        Args:
            project_id: Project ID
            event: Maturity event dict with timestamp, phase, scores, etc.

        Returns:
            True if successful, False otherwise
        """
        self._log_operation("add_maturity_event", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            project.maturity_history.append(event)
            self.database.save_project(project)
            self.logger.debug(f"Added maturity event to project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add maturity event for {project_id}: {e}")
            return False

    def get_categorized_specs(self, project_id: str) -> Dict[str, List[Dict]]:
        """
        Get categorized specs for all phases.

        Args:
            project_id: Project ID

        Returns:
            Dict mapping phase to list of specs
        """
        self._log_operation("get_categorized_specs", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project:
                return project.categorized_specs
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get categorized specs for {project_id}: {e}")
            return {}

    def add_categorized_specs(
        self, project_id: str, phase: str, specs: List[Dict[str, Any]]
    ) -> bool:
        """
        Add categorized specs to a phase.

        Args:
            project_id: Project ID
            phase: Phase name
            specs: List of spec dicts to add

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "add_categorized_specs",
            {"project_id": project_id, "phase": phase, "spec_count": len(specs)},
        )
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            if phase not in project.categorized_specs:
                project.categorized_specs[phase] = []

            project.categorized_specs[phase].extend(specs)
            self.database.save_project(project)
            self.logger.debug(
                f"Added {len(specs)} specs to phase {phase} for project {project_id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to add categorized specs for {project_id}: {e}")
            return False
