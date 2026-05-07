"""Insight service - encapsulates insight extraction and analysis."""

from typing import TYPE_CHECKING, Dict, Any, Optional, List

from .base import Service
from socratic_system.repositories.insight_repository import InsightRepository

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext
    from socratic_system.claude_client import ClaudeClient
    from socratic_agents import DocumentContextAnalyzer


class InsightService(Service):
    """Service for extracting and analyzing insights from user responses."""

    def __init__(
        self,
        config,
        claude_client: "ClaudeClient",
        context_analyzer: Optional["DocumentContextAnalyzer"] = None,
    ):
        """Initialize insight service.

        Args:
            config: Socrates configuration
            claude_client: Claude API client
            context_analyzer: Context analyzer for document understanding
        """
        super().__init__(config)
        self.claude_client = claude_client
        self.context_analyzer = context_analyzer
        # Initialize repository with a mock database for now
        from unittest.mock import MagicMock
        mock_database = MagicMock()
        self.repository = InsightRepository(mock_database)

    def extract_insights(
        self,
        context: str,
        project: "ProjectContext",
        user_id: Optional[str] = None,
        user_auth_method: str = "api_key",
    ) -> Dict[str, Any]:
        """Extract insights from user response using Claude.

        Args:
            context: User response text
            project: ProjectContext
            user_id: User identifier
            user_auth_method: User's auth method for API

        Returns:
            Extracted insights dict with goals, requirements, tech_stack, constraints
        """
        self.logger.info(f"Extracting insights from user response ({len(context)} chars)")

        insights = self.claude_client.extract_insights(
            context,
            project,
            user_auth_method=user_auth_method,
            user_id=user_id,
        )

        # Validate insights before returning
        validated_insights = self._validate_insights(insights)
        self.logger.debug(f"Extracted insights: {len(validated_insights)} keys (validated)")
        return validated_insights

    def analyze_context(self, project: "ProjectContext") -> Dict[str, Any]:
        """Analyze project context for insights.

        Args:
            project: ProjectContext

        Returns:
            Context analysis dict
        """
        self.logger.info(f"Analyzing context for project {project.project_id}")

        if not self.context_analyzer:
            return {}

        return self.context_analyzer.analyze(project)

    def analyze_insights(self, project_id: str, insights_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and categorize insights from dict.

        Args:
            project_id: Project identifier
            insights_dict: Dictionary of insights by type

        Returns:
            Analysis result with categorized insights
        """
        self.logger.info(f"Analyzing insights for project {project_id}")

        insights = []
        for key, content in insights_dict.items():
            if content:
                category = self._categorize_insight(key)
                confidence = self._calculate_confidence(str(content))
                insights.append({
                    "content": content,
                    "category": category,
                    "confidence": confidence,
                })

        return {
            "status": "success",
            "analyzed": len(insights),
            "insights": insights,
        }

    def _categorize_insight(self, key: str) -> str:
        """Categorize insight by key.

        Args:
            key: Insight key/type

        Returns:
            Category name
        """
        key_lower = key.lower()

        # Requirement categories
        if any(word in key_lower for word in ["requirement", "feature", "spec", "functional", "system_features"]):
            return "requirement"

        # Architecture categories
        if any(word in key_lower for word in ["architecture", "design", "pattern", "structure"]):
            return "architecture"

        # Risk categories
        if any(word in key_lower for word in ["risk", "issue", "concern", "problem", "constraint"]):
            return "risk"

        # Default
        return "requirement"

    def _calculate_confidence(self, content: str) -> float:
        """Calculate confidence score based on content.

        Args:
            content: Content to score

        Returns:
            Confidence score between 0 and 1
        """
        if not content:
            return 0.5

        # Base confidence on content length
        length = len(content.split())
        if length < 5:
            return 0.6
        elif length < 20:
            return 0.75
        elif length < 50:
            return 0.85
        else:
            return min(0.95, 0.7 + (length / 200))

    def _validate_insights(self, insights: Any) -> Dict[str, Any]:
        """Validate extracted insights, filtering out null/empty values.

        Args:
            insights: Extracted insights from Claude client

        Returns:
            Validated insights dict with null/empty values removed
        """
        # Handle None or non-dict returns
        if not insights or not isinstance(insights, dict):
            self.logger.warning(f"Invalid insights returned: {type(insights)}")
            return {}

        validated = {}
        for key, value in insights.items():
            # Skip None values
            if value is None:
                self.logger.debug(f"Skipping null insight: {key}")
                continue

            # Skip empty strings
            if isinstance(value, str) and not value.strip():
                self.logger.debug(f"Skipping empty insight: {key}")
                continue

            # Skip empty lists
            if isinstance(value, list) and len(value) == 0:
                self.logger.debug(f"Skipping empty list insight: {key}")
                continue

            # Keep non-empty values
            validated[key] = value

        return validated

    def store_insights(self, project_id: str, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store analyzed insights to repository.

        Args:
            project_id: Project identifier
            insights: List of insight dicts

        Returns:
            Storage result
        """
        self.logger.info(f"Storing {len(insights)} insights for project {project_id}")

        stored = 0
        for insight in insights:
            result = self.repository.add_insight(
                project_id=project_id,
                content=insight.get("content", ""),
                category=insight.get("category", "requirement"),
                confidence=insight.get("confidence", 0.9),
                metadata=insight.get("metadata", {}),
            )
            if result:
                stored += 1

        return {
            "status": "success",
            "stored": stored,
            "total": len(insights),
        }

    def get_project_insights(self, project_id: str) -> Dict[str, Any]:
        """Get all insights for a project.

        Args:
            project_id: Project identifier

        Returns:
            Insights and statistics
        """
        self.logger.info(f"Getting insights for project {project_id}")

        insights = self.repository.get_project_insights(project_id)
        stats = self.repository.get_insight_statistics(project_id)

        return {
            "status": "success",
            "total": len(insights),
            "insights": insights,
            "statistics": stats,
        }

    def get_insights_by_category(self, project_id: str, category: str) -> Dict[str, Any]:
        """Get insights filtered by category.

        Args:
            project_id: Project identifier
            category: Category to filter by

        Returns:
            Filtered insights
        """
        self.logger.info(f"Getting {category} insights for project {project_id}")

        insights = self.repository.get_insights_by_category(project_id, category)

        return {
            "status": "success",
            "category": category,
            "count": len(insights),
            "insights": insights,
        }

    def generate_recommendations(self, project_id: str) -> Dict[str, Any]:
        """Generate recommendations from high-confidence insights.

        Args:
            project_id: Project identifier

        Returns:
            Recommendations
        """
        self.logger.info(f"Generating recommendations for project {project_id}")

        all_insights = self.repository.get_project_insights(project_id)
        high_conf_insights = self.repository.get_high_confidence_insights(project_id, min_confidence=0.8)

        # Group by category
        by_category = {}
        for insight in high_conf_insights:
            cat = insight.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(insight)

        # Generate recommendations
        recommendations = []
        for category, insights in by_category.items():
            if len(insights) >= 2:  # Only recommend if 2+ insights
                priority = self._calculate_priority(insights)
                recommendation = self._generate_recommendation_text(category, insights)
                recommendations.append({
                    "category": category,
                    "priority": priority,
                    "insight_count": len(insights),
                    "recommendation": recommendation,
                })

        return {
            "status": "success",
            "count": len(recommendations),
            "recommendations": recommendations,
        }

    def _calculate_priority(self, insights: List[Dict[str, Any]]) -> str:
        """Calculate priority based on confidence scores.

        Args:
            insights: List of insights

        Returns:
            Priority level: high, medium, or low
        """
        if not insights:
            return "low"

        avg_confidence = sum(i.get("confidence", 0.5) for i in insights) / len(insights)

        if avg_confidence >= 0.85:
            return "high"
        elif avg_confidence >= 0.70:
            return "medium"
        else:
            return "low"

    def _generate_recommendation_text(self, category: str, insights: List[Dict[str, Any]]) -> str:
        """Generate recommendation text for a category.

        Args:
            category: Insight category
            insights: List of insights in category

        Returns:
            Recommendation text
        """
        count = len(insights)

        if category == "requirement":
            return f"Consolidate and refine {count} functional requirements"
        elif category == "architecture":
            return f"Implement {count} architectural patterns and design decisions"
        elif category == "risk":
            return f"Address and mitigate {count} identified risks and concerns"
        else:
            return f"Review and process {count} insights for {category}"
