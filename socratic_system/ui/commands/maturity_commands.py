"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Maturity tracking commands for the CLI interface

Commands:
  /maturity [phase]       - Show detailed maturity breakdown for a phase
  /maturity summary       - Show maturity summary across all phases
  /maturity history       - Show maturity progression timeline
"""

from typing import Any, Dict

from socratic_system.ui.maturity_display import MaturityDisplay

from .base import BaseCommand
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class MaturityCommand(BaseCommand):
    """
    Display detailed phase maturity information.

    Usage:
      /maturity              - Show current phase maturity
      /maturity discovery    - Show discovery phase maturity
      /maturity analysis     - Show analysis phase maturity
      /maturity design       - Show design phase maturity
      /maturity implementation - Show implementation phase maturity
    """

    def __init__(self):
        super().__init__(
            name="maturity",
            description="Show detailed maturity breakdown for current or specified phase",
            usage="maturity [phase]",
        )

    def execute(self, args: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the maturity command"""
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get phase (current or specified)
        if args and args[0]:
            phase = args[0].lower()
            # Validate phase
            valid_phases = ["discovery", "analysis", "design", "implementation"]
            if phase not in valid_phases:
                return self.error(
                    f"Invalid phase '{phase}'. Valid phases: " f"{', '.join(valid_phases)}"
                )
        else:
            phase = project.phase

        # Calculate maturity
        result = safe_orchestrator_call(
            orchestrator,
            "quality_controller",
            {"action": "calculate_maturity", "project": project, "phase": phase},
            operation_name="calculate maturity"
        )

        if result.get("data", {}).get("status") == "success":
            maturity = result.get("maturity", {})
            MaturityDisplay.display_detailed_maturity(maturity)
            return self.success()

        return self.error(result.get("message", "Failed to calculate maturity"))


class MaturitySummaryCommand(BaseCommand):
    """
    Display maturity summary across all 4 phases.

    Shows one-line status for each phase with progress bar.
    """

    def __init__(self):
        super().__init__(
            name="maturity summary",
            description="Show maturity summary across all phases",
            usage="maturity summary",
        )

    def execute(self, args: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the maturity summary command"""
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get maturity summary
        result = safe_orchestrator_call(
            orchestrator,
            "quality_controller",
            {"action": "get_maturity_summary", "project": project},
            operation_name="get maturity summary"
        )

        if result.get("data", {}).get("status") == "success":
            summary = result.get("summary", {})
            MaturityDisplay.display_maturity_summary_all_phases(summary)
            return self.success()

        return self.error(result.get("message", "Failed to get maturity summary"))


class MaturityHistoryCommand(BaseCommand):
    """
    Display maturity progression history and timeline.

    Shows last 15 maturity events with timestamps, scores, and changes.
    """

    def __init__(self):
        super().__init__(
            name="maturity history",
            description="Show maturity progression timeline",
            usage="maturity history",
        )

    def execute(self, args: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the maturity history command"""
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get maturity history
        result = safe_orchestrator_call(
            orchestrator,
            "quality_controller",
            {"action": "get_history", "project": project},
            operation_name="get maturity history"
        )

        if result.get("data", {}).get("status") == "success":
            history = result.get("history", [])
            total_events = result.get("total_events", 0)

            if not history:
                print("\nNo maturity history available yet.\n")
            else:
                MaturityDisplay.display_maturity_history(history)
                print(f"Total maturity events: {total_events}\n")

            return self.success()

        return self.error(result.get("message", "Failed to get maturity history"))


class MaturityStatusCommand(BaseCommand):
    """
    Display current phase completion status.

    Shows which phases are complete, ready to advance, or still in progress.
    """

    def __init__(self):
        super().__init__(
            name="maturity status",
            description="Show phase completion status",
            usage="maturity status",
        )

    def execute(self, args: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the maturity status command"""
        project = context.get("project")

        if not project:
            return self.error("No project loaded")

        # Display current phase and completion status
        all_scores = project.phase_maturity_scores
        MaturityDisplay.display_phase_completion_status(all_scores)

        return self.success()
