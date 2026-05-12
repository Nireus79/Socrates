"""
Maturity Repository - Data access layer for project maturity/quality metrics.

Encapsulates all maturity and quality score persistence operations, providing
a clean interface for quality-related services.
"""

from typing import Any

from socratic_system.database import ProjectDatabase
from socratic_system.services.repositories.base import Repository


class MaturityRepository(Repository[dict[str, Any]]):
    """
    Repository for maturity and quality metrics persistence.

    Manages storing and retrieving project maturity scores, quality metrics,
    and related analysis results.
    """

    def __init__(self, database: ProjectDatabase):
        """
        Initialize maturity repository.

        Args:
            database: ProjectDatabase instance for data access
        """
        self.database = database

    def save(self, maturity_data: dict[str, Any]) -> dict[str, Any]:
        """
        Save maturity/quality metrics.

        Args:
            maturity_data: Dictionary containing maturity metrics

        Returns:
            The saved maturity data
        """
        project_id = maturity_data.get("project_id")
        if not project_id:
            raise ValueError("maturity_data must contain 'project_id'")

        self.database.save_maturity_metrics(project_id, maturity_data)  # type: ignore
        return maturity_data

    def find_by_id(self, project_id: str) -> dict[str, Any] | None:
        """
        Find maturity metrics by project ID.

        Args:
            project_id: The project ID

        Returns:
            The maturity metrics if found, None otherwise
        """
        return self.database.get_maturity_metrics(project_id)  # type: ignore

    def find_all(self, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        """
        Find all maturity records with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of maturity records
        """
        # Get all projects and their maturity metrics
        projects = self.database.get_all_projects()  # type: ignore
        results = []

        for project in projects:
            metrics = self.database.get_maturity_metrics(project.project_id)  # type: ignore
            if metrics:
                results.append(metrics)

        if offset > 0:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]

        return results

    def delete(self, project_id: str) -> bool:
        """
        Delete maturity metrics for a project.

        Args:
            project_id: The project ID

        Returns:
            True if deleted, False if not found
        """
        try:
            self.database.delete_maturity_metrics(project_id)  # type: ignore
            return True
        except Exception:
            return False

    def exists(self, project_id: str) -> bool:
        """
        Check if maturity metrics exist for a project.

        Args:
            project_id: The project ID to check

        Returns:
            True if metrics exist, False otherwise
        """
        return self.find_by_id(project_id) is not None

    def get_category_scores(self, project_id: str) -> dict[str, float] | None:
        """
        Get category-specific maturity scores.

        Args:
            project_id: The project ID

        Returns:
            Dictionary of category scores, or None if not found
        """
        metrics = self.find_by_id(project_id)
        if metrics:
            return metrics.get("category_scores", {})
        return None

    def get_overall_score(self, project_id: str) -> float | None:
        """
        Get overall maturity score.

        Args:
            project_id: The project ID

        Returns:
            The overall score (0-100), or None if not found
        """
        metrics = self.find_by_id(project_id)
        if metrics:
            return metrics.get("overall_score")
        return None

    def update_category_score(self, project_id: str, category: str, score: float) -> bool:
        """
        Update a specific category score.

        Args:
            project_id: The project ID
            category: The category name
            score: The new score

        Returns:
            True if updated, False if project not found
        """
        metrics = self.find_by_id(project_id)
        if not metrics:
            return False

        if "category_scores" not in metrics:
            metrics["category_scores"] = {}

        metrics["category_scores"][category] = score

        # Recalculate overall score
        if metrics["category_scores"]:
            metrics["overall_score"] = sum(metrics["category_scores"].values()) / len(
                metrics["category_scores"]
            )

        self.save(metrics)
        return True
