"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Learning recommendations and pattern analysis commands
"""

from typing import Any, Dict, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class LearningRecommendationsCommand(BaseCommand):
    """Display learning recommendations for an agent"""

    def __init__(self):
        super().__init__(
            name="learning recommendations",
            description="Get improvement recommendations for an agent",
            usage="learning recommendations <agent_name> [limit]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute learning recommendations command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.learning:
            return self.error("Learning engine not available")

        agent_name = args[0] if args else input(f"{Fore.WHITE}Agent name: ").strip()
        if not agent_name:
            return self.error("Agent name cannot be empty")

        limit = 5
        if len(args) > 1:
            try:
                limit = int(args[1])
            except ValueError:
                return self.error("Limit must be a number")

        try:
            recommendations = library_manager.learning.get_recommendations(
                agent_name=agent_name, limit=limit
            )

            self.print_header(f"Learning Recommendations for {agent_name}")

            if not recommendations:
                self.print_info("No recommendations available")
                return self.success(data={"agent_name": agent_name, "recommendations": []})

            recommendations_data = []
            for i, rec in enumerate(recommendations, 1):
                rec_dict = {
                    "id": rec.get("recommendation_id"),
                    "title": rec.get("title"),
                    "confidence": rec.get("confidence"),
                    "impact": rec.get("impact"),
                }
                recommendations_data.append(rec_dict)

                confidence = rec_dict["confidence"]
                color = Fore.GREEN if confidence > 0.8 else Fore.YELLOW
                print(f"\n{Fore.CYAN}[{i}] {rec_dict['title']}{Style.RESET_ALL}")
                print(f"  Confidence: {color}{confidence:.1%}{Style.RESET_ALL}")
                print(f"  Impact: {rec_dict['impact']}")
                if rec.get("description"):
                    print(f"  {rec.get('description')}")

            return self.success(data={
                "agent_name": agent_name,
                "recommendations": recommendations_data,
                "count": len(recommendations_data),
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class LearningPatternsCommand(BaseCommand):
    """Analyze and display learning patterns for an agent"""

    def __init__(self):
        super().__init__(
            name="learning patterns",
            description="Detect usage and error patterns in agent interactions",
            usage="learning patterns <agent_name> [pattern_type]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute learning patterns command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.learning:
            return self.error("Learning engine not available")

        agent_name = args[0] if args else input(f"{Fore.WHITE}Agent name: ").strip()
        if not agent_name:
            return self.error("Agent name cannot be empty")

        pattern_type = args[1].lower() if len(args) > 1 else "all"
        if pattern_type not in ["usage", "error", "performance", "all"]:
            return self.error("Pattern type must be: usage, error, performance, or all")

        try:
            patterns_data = {}

            if pattern_type in ["usage", "all"]:
                usage_patterns = library_manager.learning.detect_patterns(agent_name)
                if usage_patterns:
                    patterns_data["usage"] = usage_patterns

            if pattern_type in ["error", "all"]:
                error_patterns = library_manager.learning.detect_error_patterns(agent_name)
                if error_patterns:
                    patterns_data["error"] = error_patterns

            if pattern_type in ["performance", "all"]:
                perf_patterns = library_manager.learning.detect_performance_patterns(agent_name)
                if perf_patterns:
                    patterns_data["performance"] = perf_patterns

            self.print_header(f"Learning Patterns for {agent_name}")

            if not patterns_data:
                self.print_info("No patterns detected")
                return self.success(data={
                    "agent_name": agent_name,
                    "pattern_type": pattern_type,
                    "patterns": {},
                })

            if "usage" in patterns_data:
                print(f"\n{Fore.CYAN}Usage Patterns:{Style.RESET_ALL}")
                for pattern_name, pattern_info in patterns_data["usage"].items():
                    print(f"  {pattern_name}: {pattern_info.get('frequency', 'N/A')}")

            if "error" in patterns_data:
                print(f"\n{Fore.CYAN}Error Patterns:{Style.RESET_ALL}")
                for error_type, count in patterns_data["error"].items():
                    print(f"  {error_type}: {count} occurrences")

            if "performance" in patterns_data:
                print(f"\n{Fore.CYAN}Performance Patterns:{Style.RESET_ALL}")
                for metric, value in patterns_data["performance"].items():
                    print(f"  {metric}: {value}")

            return self.success(data={
                "agent_name": agent_name,
                "pattern_type": pattern_type,
                "patterns": patterns_data,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class LearningSessionCommand(BaseCommand):
    """Start or manage learning sessions"""

    def __init__(self):
        super().__init__(
            name="learning session",
            description="Start a new learning session to track interactions",
            usage="learning session <user_id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute learning session command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.learning:
            return self.error("Learning engine not available")

        user_id = args[0] if args else input(f"{Fore.WHITE}User ID: ").strip()
        if not user_id:
            return self.error("User ID cannot be empty")

        context_info = input(f"{Fore.WHITE}Session context (optional): ").strip()

        try:
            session = library_manager.learning.start_session(
                user_id=user_id,
                context=context_info or None
            )

            if not session:
                return self.error("Failed to start session")

            session_data = {
                "session_id": session.get("session_id"),
                "user_id": user_id,
                "started_at": session.get("created_at"),
            }

            self.print_header("Learning Session Started")
            self.print_success(f"Session ID: {session_data['session_id']}")
            print(f"  User: {user_id}")
            if context_info:
                print(f"  Context: {context_info}")

            if hasattr(orchestrator.database, "save_learning_session"):
                orchestrator.database.save_learning_session(
                    session_id=session_data["session_id"],
                    user_id=user_id,
                    context=context_info or None
                )

            return self.success(data=session_data)

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class LearningAnalyzeCommand(BaseCommand):
    """Analyze agent performance and generate insights"""

    def __init__(self):
        super().__init__(
            name="learning analyze",
            description="Generate detailed learning insights for an agent",
            usage="learning analyze <agent_name> [confidence_threshold]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute learning analyze command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.learning:
            return self.error("Learning engine not available")

        agent_name = args[0] if args else input(f"{Fore.WHITE}Agent name: ").strip()
        if not agent_name:
            return self.error("Agent name cannot be empty")

        min_confidence = 0.7
        if len(args) > 1:
            try:
                min_confidence = float(args[1])
            except ValueError:
                return self.error("Confidence threshold must be a number (0-1)")

        try:
            # Get comprehensive analysis
            patterns = library_manager.learning.detect_patterns(agent_name)
            error_patterns = library_manager.learning.detect_error_patterns(agent_name)
            perf_patterns = library_manager.learning.detect_performance_patterns(agent_name)
            recommendations = library_manager.learning.generate_recommendations(
                agent_name=agent_name,
                min_confidence=min_confidence
            )

            self.print_header(f"Learning Analysis for {agent_name}")

            analysis_data = {
                "agent_name": agent_name,
                "confidence_threshold": min_confidence,
                "patterns": patterns or {},
                "error_patterns": error_patterns or {},
                "performance_patterns": perf_patterns or {},
                "recommendations_count": len(recommendations) if recommendations else 0,
            }

            # Print summary
            print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
            print(f"  Patterns Detected: {len(patterns) if patterns else 0}")
            print(f"  Error Patterns: {len(error_patterns) if error_patterns else 0}")
            print(f"  Performance Issues: {len(perf_patterns) if perf_patterns else 0}")
            print(f"  Recommendations: {analysis_data['recommendations_count']}")

            # Print top recommendations
            if recommendations:
                print(f"\n{Fore.CYAN}Top Recommendations:{Style.RESET_ALL}")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec.get('title', 'N/A')}")
                    print(f"     Confidence: {rec.get('confidence', 0):.1%}")

            return self.success(data=analysis_data)

        except Exception as e:
            return self.error(f"Failed: {str(e)}")
