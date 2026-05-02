"""Insight service - encapsulates insight extraction and analysis."""

from typing import TYPE_CHECKING, Dict, Any, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext
    from socratic_system.claude_client import ClaudeClient
    from socratic_system.agents.document_context_analyzer import DocumentContextAnalyzer


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

        self.logger.debug(f"Extracted insights: {len(insights)} keys")
        return insights

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
