"""
InsightRepository - Data access for project insights.

Abstracts all insight database operations.
Used by InsightService instead of direct database calls.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base_repository import BaseRepository

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase


class InsightRepository(BaseRepository):
    """Repository for insight data access."""

    def __init__(self, database: "ProjectDatabase"):
        """Initialize insight repository."""
        super().__init__(database)

    def get_project_insights(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all insights for a project."""
        self._log_operation("get_project_insights", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project and hasattr(project, "insights"):
                return project.insights if project.insights else []
            return []
        except Exception as e:
            self.logger.error(f"Failed to get insights for {project_id}: {e}")
            return []

    def add_insight(
        self,
        project_id: str,
        content: str,
        category: str,
        confidence: float = 0.9,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add an insight to project."""
        self._log_operation("add_insight", {"project_id": project_id, "category": category})
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            if not hasattr(project, "insights"):
                project.insights = []

            insight = {
                "content": content,
                "category": category,
                "confidence": min(1.0, max(0.0, confidence)),
                "metadata": metadata or {},
                "created_at": __import__("datetime").datetime.now().isoformat(),
            }

            project.insights.append(insight)
            self.database.save_project(project)
            self.logger.debug(f"Added {category} insight to project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add insight for {project_id}: {e}")
            return False

    def get_insights_by_category(
        self, project_id: str, category: str
    ) -> List[Dict[str, Any]]:
        """Get insights filtered by category."""
        self._log_operation("get_insights_by_category", {"project_id": project_id, "category": category})
        try:
            insights = self.get_project_insights(project_id)
            filtered = [i for i in insights if i.get("category") == category]
            return filtered
        except Exception as e:
            self.logger.error(f"Failed to get {category} insights: {e}")
            return []

    def get_high_confidence_insights(
        self, project_id: str, min_confidence: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Get insights above confidence threshold."""
        self._log_operation("get_high_confidence_insights", {"project_id": project_id})
        try:
            insights = self.get_project_insights(project_id)
            filtered = [i for i in insights if i.get("confidence", 0.0) >= min_confidence]
            return filtered
        except Exception as e:
            self.logger.error(f"Failed to get high confidence insights: {e}")
            return []

    def get_insight_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get statistics about project insights."""
        self._log_operation("get_insight_statistics", {"project_id": project_id})
        try:
            insights = self.get_project_insights(project_id)
            stats = {
                "total_insights": len(insights),
                "by_category": {},
                "avg_confidence": 0.0,
            }

            if insights:
                total_confidence = 0.0
                for insight in insights:
                    category = insight.get("category", "unknown")
                    if category not in stats["by_category"]:
                        stats["by_category"][category] = 0
                    stats["by_category"][category] += 1
                    total_confidence += insight.get("confidence", 0.9)

                stats["avg_confidence"] = total_confidence / len(insights)

            return stats
        except Exception as e:
            self.logger.error(f"Failed to get insight statistics: {e}")
            return {"total_insights": 0}

    def clear_insights(self, project_id: str) -> bool:
        """Clear all insights for a project."""
        self._log_operation("clear_insights", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if not project:
                return False
            project.insights = []
            self.database.save_project(project)
            self.logger.debug(f"Cleared insights for {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear insights: {e}")
            return False
