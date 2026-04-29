"""
Insight Service - Encapsulates insight extraction and analysis.

Handles:
- Insight extraction from context using Claude
- Insight analysis and categorization
- Insight caching

No orchestrator dependency - uses dependency injection for all external services.
"""

from typing import Any, Dict, Optional

from socratic_nexus.clients import ClaudeClient

from socratic_system.config import SocratesConfig
from socratic_system.models import ProjectContext
from socratic_system.services.base import Service


class InsightService(Service):
    """
    Service for insight extraction and analysis.

    Centralizes Claude API usage for insight extraction with
    proper authentication and caching.
    """

    def __init__(
        self,
        config: SocratesConfig,
        claude_client: ClaudeClient,
    ):
        """
        Initialize insight service.

        Args:
            config: SocratesConfig instance
            claude_client: ClaudeClient for AI operations
        """
        super().__init__(config)
        self.claude_client = claude_client

    def extract_insights(
        self,
        context: str,
        project: Optional[ProjectContext] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Extract insights from context using Claude.

        Args:
            context: The context to analyze
            project: Optional ProjectContext for context
            user_id: Optional user ID for authentication
            **kwargs: Additional parameters

        Returns:
            Dictionary containing extracted insights
        """
        if not context or not context.strip():
            raise ValueError("Context cannot be empty")

        self.log_info("Extracting insights from context")

        # Call Claude API
        insights = self.claude_client.extract_insights(
            context=context,
            project=project,
            user_id=user_id,
            **kwargs,
        )

        self.log_info(f"Extracted {len(insights)} insights")
        return insights

    def analyze_requirements(
        self,
        description: str,
        project: Optional[ProjectContext] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze project requirements and extract structured insights.

        Args:
            description: Project description
            project: Optional ProjectContext
            user_id: Optional user ID

        Returns:
            Dictionary containing analyzed requirements
        """
        if not description:
            raise ValueError("Description required")

        self.log_info("Analyzing requirements")

        prompt = f"""Analyze the following project description and extract:
1. Core requirements
2. Key goals
3. Constraints
4. Success criteria

Description: {description}

Provide structured output."""

        insights = self.extract_insights(
            context=prompt,
            project=project,
            user_id=user_id,
        )

        return {
            "requirements": insights,
            "description": description,
        }

    def extract_architecture_insights(
        self,
        context: str,
        project: Optional[ProjectContext] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract architecture-specific insights.

        Args:
            context: Architecture context
            project: Optional ProjectContext
            user_id: Optional user ID

        Returns:
            Dictionary containing architecture insights
        """
        self.log_info("Extracting architecture insights")

        prompt = f"""Analyze the following architecture context and extract:
1. System components
2. Data flows
3. Integration points
4. Scalability considerations

Context: {context}

Provide structured output."""

        return self.extract_insights(
            context=prompt,
            project=project,
            user_id=user_id,
        )

    def extract_code_insights(
        self,
        code: str,
        language: str = "python",
        project: Optional[ProjectContext] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract insights from code.

        Args:
            code: The code to analyze
            language: Programming language
            project: Optional ProjectContext
            user_id: Optional user ID

        Returns:
            Dictionary containing code insights
        """
        self.log_info(f"Extracting {language} code insights")

        prompt = f"""Analyze the following {language} code and extract:
1. Main functionality
2. Key classes/functions
3. Dependencies
4. Potential improvements

Code:
```{language}
{code}
```

Provide structured output."""

        return self.extract_insights(
            context=prompt,
            project=project,
            user_id=user_id,
        )

    def categorize_insights(
        self,
        insights: Dict[str, Any],
    ) -> Dict[str, list]:
        """
        Categorize insights into functional groups.

        Args:
            insights: Dictionary of insights

        Returns:
            Dictionary with insights categorized
        """
        categorized = {
            "technical": [],
            "business": [],
            "user_experience": [],
            "operational": [],
        }

        # Simple categorization - could be enhanced
        for key, value in insights.items():
            if any(
                term in key.lower() for term in ["tech", "architecture", "code"]
            ):
                categorized["technical"].append((key, value))
            elif any(term in key.lower() for term in ["business", "goal", "requirement"]):
                categorized["business"].append((key, value))
            elif any(term in key.lower() for term in ["user", "experience", "ui"]):
                categorized["user_experience"].append((key, value))
            else:
                categorized["operational"].append((key, value))

        return categorized
