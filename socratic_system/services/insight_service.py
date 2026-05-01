"""
InsightService - Business logic for insight analysis and extraction.

Extracts insight analysis logic into reusable service.
Uses InsightRepository for all data access.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from socratic_system.repositories.insight_repository import InsightRepository

from .base_service import BaseService

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig


class InsightService(BaseService):
    """Service for insight analysis, categorization, and recommendations."""

    def __init__(self, config: "SocratesConfig", database):
        """Initialize insight service."""
        super().__init__(config)
        self.repository = InsightRepository(database)
        self.default_categories = {
            "requirement", "architecture", "constraint", "risk",
            "opportunity", "dependency",
        }
        self.logger.info("InsightService initialized")

    def analyze_insights(
        self, project_id: str, insights_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze insights and extract structured information."""
        self._log_operation("analyze_insights", {"project_id": project_id})
        try:
            if not insights_dict:
                return {"status": "success", "analyzed": 0, "insights": []}
            analyzed_insights = []
            for key, value in insights_dict.items():
                if isinstance(value, str) and value.strip():
                    insight = {
                        "key": key,
                        "content": value,
                        "category": self._categorize_insight(key),
                        "confidence": self._calculate_confidence(value),
                    }
                    analyzed_insights.append(insight)
            self.logger.info(
                f"Analyzed {len(analyzed_insights)} insights for {project_id}"
            )
            return {
                "status": "success",
                "analyzed": len(analyzed_insights),
                "insights": analyzed_insights,
            }
        except Exception as e:
            self.logger.error(f"Error analyzing insights: {e}")
            return {"status": "error", "message": str(e)}

    def store_insights(
        self, project_id: str, insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Store analyzed insights in repository."""
        self._log_operation("store_insights", {"project_id": project_id})
        try:
            stored = 0
            for insight in insights:
                result = self.repository.add_insight(
                    project_id,
                    insight.get("content", ""),
                    insight.get("category", "unknown"),
                    insight.get("confidence", 0.9),
                    insight.get("metadata", {}),
                )
                if result:
                    stored += 1
            self.logger.info(f"Stored {stored} insights for {project_id}")
            return {"status": "success", "stored": stored, "total": len(insights)}
        except Exception as e:
            self.logger.error(f"Error storing insights: {e}")
            return {"status": "error", "message": str(e)}

    def get_project_insights(self, project_id: str) -> Dict[str, Any]:
        """Get all insights for a project."""
        self._log_operation("get_project_insights", {"project_id": project_id})
        try:
            insights = self.repository.get_project_insights(project_id)
            stats = self.repository.get_insight_statistics(project_id)
            return {
                "status": "success",
                "insights": insights,
                "total": len(insights),
                "statistics": stats,
            }
        except Exception as e:
            self.logger.error(f"Error getting insights: {e}")
            return {"status": "error", "message": str(e)}

    def get_insights_by_category(
        self, project_id: str, category: str
    ) -> Dict[str, Any]:
        """Get insights filtered by category."""
        self._log_operation("get_insights_by_category", {"project_id": project_id})
        try:
            insights = self.repository.get_insights_by_category(project_id, category)
            return {
                "status": "success",
                "category": category,
                "insights": insights,
                "count": len(insights),
            }
        except Exception as e:
            self.logger.error(f"Error getting category insights: {e}")
            return {"status": "error", "message": str(e)}

    def generate_recommendations(self, project_id: str) -> Dict[str, Any]:
        """Generate recommendations based on insights."""
        self._log_operation("generate_recommendations", {"project_id": project_id})
        try:
            insights = self.repository.get_project_insights(project_id)
            high_conf = self.repository.get_high_confidence_insights(project_id)
            recommendations = []
            by_category = {}
            for insight in high_conf:
                cat = insight.get("category", "unknown")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(insight)
            for category, category_insights in by_category.items():
                if len(category_insights) >= 2:
                    rec = {
                        "category": category,
                        "priority": self._calculate_priority(category_insights),
                        "insight_count": len(category_insights),
                        "recommendation": self._generate_recommendation_text(
                            category, category_insights
                        ),
                    }
                    recommendations.append(rec)
            self.logger.info(
                f"Generated {len(recommendations)} recommendations for {project_id}"
            )
            return {
                "status": "success",
                "recommendations": recommendations,
                "count": len(recommendations),
            }
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return {"status": "error", "message": str(e)}

    def _categorize_insight(self, key: str) -> str:
        """Categorize insight based on key."""
        key_lower = key.lower()
        if any(w in key_lower for w in ["requirement", "spec", "feature"]):
            return "requirement"
        elif any(w in key_lower for w in ["architecture", "design"]):
            return "architecture"
        elif any(w in key_lower for w in ["constraint", "limit"]):
            return "constraint"
        elif any(w in key_lower for w in ["risk", "issue"]):
            return "risk"
        elif any(w in key_lower for w in ["opportunity", "improvement"]):
            return "opportunity"
        elif any(w in key_lower for w in ["dependency", "depend"]):
            return "dependency"
        return "unknown"

    def _calculate_confidence(self, content: str) -> float:
        """Calculate confidence based on content length."""
        if not content:
            return 0.0
        word_count = len(content.split())
        confidence = min(0.95, 0.5 + (word_count / 100.0))
        return round(confidence, 2)

    def _calculate_priority(self, insights: List[Dict[str, Any]]) -> str:
        """Calculate priority based on insights."""
        if not insights:
            return "low"
        avg_confidence = sum(i.get("confidence", 0.5) for i in insights) / len(insights)
        if avg_confidence >= 0.8:
            return "high"
        elif avg_confidence >= 0.6:
            return "medium"
        return "low"

    def _generate_recommendation_text(
        self, category: str, insights: List[Dict[str, Any]]
    ) -> str:
        """Generate recommendation text."""
        if category == "requirement":
            return f"Document {len(insights)} identified requirements in detail"
        elif category == "risk":
            return f"Address {len(insights)} identified risks and mitigation strategies"
        elif category == "opportunity":
            return f"Evaluate {len(insights)} improvement opportunities"
        elif category == "architecture":
            return f"Refine architecture based on {len(insights)} design insights"
        elif category == "constraint":
            return f"Review {len(insights)} constraints and their implications"
        return f"Address {len(insights)} insights for {category}"
