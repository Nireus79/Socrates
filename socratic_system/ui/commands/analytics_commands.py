"""
Analytics CLI commands for maturity insights and recommendations.

Provides user-facing commands for analyzing category performance,
getting recommendations, and viewing progression trends.
"""

import logging
from typing import Any, Dict, List

from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.ui.analytics_display import AnalyticsDisplay
from socratic_system.ui.commands.base import BaseCommand

logger = logging.getLogger(__name__)


class AnalyticsAnalyzeCommand(BaseCommand):
    """
    /analytics analyze [phase]

    Show detailed category analysis for current or specified phase.
    Displays weak/strong categories, balance, and metrics.

    Usage:
        /analytics analyze           # Analyze current phase
        /analytics analyze discovery # Analyze specific phase
    """

    def __init__(self, orchestrator: Any):
        super().__init__("analytics analyze")
        self.orchestrator = orchestrator
        logger.debug("AnalyticsAnalyzeCommand initialized")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute category analysis command."""
        logger.debug(f"AnalyticsAnalyzeCommand.execute called with args: {args}")
        try:
            project = context.get("project")
            if not project:
                logger.warning("No active project found")
                return {"status": "error", "message": "No active project"}

            # Determine phase to analyze
            phase = args[0] if args else project.phase
            logger.debug(f"Analyzing phase: {phase}")

            # Validate phase
            valid_phases = ["discovery", "analysis", "design", "implementation"]
            if phase not in valid_phases:
                logger.error(f"Invalid phase: {phase}")
                return {
                    "status": "error",
                    "message": f"Invalid phase: {phase}. Must be one of: {', '.join(valid_phases)}",
                }

            # Calculate analysis
            logger.debug(f"Creating AnalyticsCalculator for project type: {project.project_type}")
            calculator = AnalyticsCalculator(project.project_type)
            analysis = calculator.analyze_category_performance(project)

            logger.info(
                f"Category analysis complete for {phase}: {len(analysis.get('weak_categories', []))} weak, {len(analysis.get('strong_categories', []))} strong"
            )

            # Display results
            logger.debug("Displaying category analysis")
            AnalyticsDisplay.display_category_analysis(analysis, phase)

            return {"status": "success", "analysis": analysis}

        except Exception as e:
            logger.error(f"Analysis failed: {type(e).__name__}: {e}")
            return {"status": "error", "message": f"Analysis failed: {str(e)}"}


class AnalyticsRecommendCommand(BaseCommand):
    """
    /analytics recommend

    Generate AI-powered recommendations for improving maturity.
    Shows weak categories, missing areas, and suggested questions.
    """

    def __init__(self, orchestrator: Any):
        super().__init__("analytics recommend")
        self.orchestrator = orchestrator
        logger.debug("AnalyticsRecommendCommand initialized")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recommendations command."""
        logger.debug("AnalyticsRecommendCommand.execute called")
        try:
            project = context.get("project")
            if not project:
                logger.warning("No active project found")
                return {"status": "error", "message": "No active project"}

            # Generate recommendations
            logger.debug(f"Generating recommendations for project type: {project.project_type}")
            calculator = AnalyticsCalculator(project.project_type)
            recommendations = calculator.generate_recommendations(project)
            questions = calculator.suggest_next_questions(project, count=5)

            logger.info(
                f"Generated {len(recommendations)} recommendations and {len(questions)} suggested questions"
            )

            # Display results
            logger.debug("Displaying recommendations")
            AnalyticsDisplay.display_recommendations(recommendations, questions)

            return {
                "status": "success",
                "recommendations": recommendations,
                "suggestions": questions,
            }

        except Exception as e:
            logger.error(f"Recommendation generation failed: {type(e).__name__}: {e}")
            return {"status": "error", "message": f"Recommendation failed: {str(e)}"}


class AnalyticsTrendsCommand(BaseCommand):
    """
    /analytics trends

    Show maturity progression trends over time.
    Displays velocity, progression chart, and insights about patterns.
    """

    def __init__(self, orchestrator: Any):
        super().__init__("analytics trends")
        self.orchestrator = orchestrator
        logger.debug("AnalyticsTrendsCommand initialized")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trends analysis command."""
        logger.debug("AnalyticsTrendsCommand.execute called")
        try:
            project = context.get("project")
            if not project:
                logger.warning("No active project found")
                return {"status": "error", "message": "No active project"}

            # Analyze trends
            logger.debug(f"Analyzing progression trends for project type: {project.project_type}")
            calculator = AnalyticsCalculator(project.project_type)
            trends = calculator.analyze_progression_trends(project)

            logger.info(
                f"Trends analysis: velocity={trends.get('velocity', 0):.2f}, sessions={trends.get('total_sessions', 0)}"
            )

            # Display results
            logger.debug("Displaying trends")
            AnalyticsDisplay.display_trends(trends, project.maturity_history)

            return {"status": "success", "trends": trends}

        except Exception as e:
            logger.error(f"Trend analysis failed: {type(e).__name__}: {e}")
            return {"status": "error", "message": f"Trend analysis failed: {str(e)}"}


class AnalyticsSummaryCommand(BaseCommand):
    """
    /analytics summary

    Quick overview of all analytics metrics.
    Shows velocity, weak/strong categories, and phase status.
    """

    def __init__(self, orchestrator: Any):
        super().__init__("analytics summary")
        self.orchestrator = orchestrator
        logger.debug("AnalyticsSummaryCommand initialized")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute summary command."""
        logger.debug("AnalyticsSummaryCommand.execute called")
        try:
            project = context.get("project")
            if not project:
                logger.warning("No active project found")
                return {"status": "error", "message": "No active project"}

            logger.info(f"Displaying analytics summary for project: {project.name}")
            logger.debug(
                f"Analytics metrics: velocity={project.analytics_metrics.get('velocity', 0):.2f}, "
                + f"sessions={project.analytics_metrics.get('total_qa_sessions', 0)}, "
                + f"confidence={project.analytics_metrics.get('avg_confidence', 0):.3f}"
            )

            # Display summary from real-time metrics
            logger.debug("Displaying analytics summary")
            AnalyticsDisplay.display_summary(project.analytics_metrics, project)

            return {"status": "success", "metrics": project.analytics_metrics}

        except Exception as e:
            logger.error(f"Summary display failed: {type(e).__name__}: {e}")
            return {"status": "error", "message": f"Summary display failed: {str(e)}"}


class AnalyticsBreakdownCommand(BaseCommand):
    """
    /analytics breakdown

    Display detailed breakdown of all categories across all phases.
    Useful for comprehensive assessment of project maturity.
    """

    def __init__(self, orchestrator: Any):
        super().__init__("analytics breakdown")
        self.orchestrator = orchestrator
        logger.debug("AnalyticsBreakdownCommand initialized")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute breakdown command."""
        logger.debug("AnalyticsBreakdownCommand.execute called")
        try:
            project = context.get("project")
            if not project:
                logger.warning("No active project found")
                return {"status": "error", "message": "No active project"}

            logger.info(f"Displaying detailed breakdown for project: {project.name}")

            # Display detailed breakdown
            logger.debug("Displaying detailed breakdown")
            AnalyticsDisplay.display_detailed_breakdown(project)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Breakdown display failed: {type(e).__name__}: {e}")
            return {"status": "error", "message": f"Breakdown display failed: {str(e)}"}


class AnalyticsStatusCommand(BaseCommand):
    """
    /analytics status

    Display phase completion status and readiness.
    Shows progress toward goals and next recommended actions.
    """

    def __init__(self, orchestrator: Any):
        super().__init__("analytics status")
        self.orchestrator = orchestrator
        logger.debug("AnalyticsStatusCommand initialized")

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute status command."""
        logger.debug("AnalyticsStatusCommand.execute called")
        try:
            project = context.get("project")
            if not project:
                logger.warning("No active project found")
                return {"status": "error", "message": "No active project"}

            logger.info(f"Displaying completion status for project: {project.name}")

            # Display completion status
            logger.debug("Displaying completion status")
            AnalyticsDisplay.display_completion_status(project)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Status display failed: {type(e).__name__}: {e}")
            return {"status": "error", "message": f"Status display failed: {str(e)}"}
