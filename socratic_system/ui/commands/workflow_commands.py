"""
Workflow approval and management commands for the CLI interface

Commands:
  /workflow approvals       - Show pending workflow approval requests
  /workflow approve <id> <path_id> - Approve a workflow with specified path
  /workflow reject <id> [reason]   - Reject a workflow approval
  /workflow info <id>      - Show detailed workflow information
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class WorkflowApprovalsCommand(BaseCommand):
    """
    Show pending workflow approval requests.

    Displays all pending approvals awaiting user decision, with summary
    information about each path and recommendations.
    """

    def __init__(self):
        super().__init__(
            name="workflow approvals",
            description="Show pending workflow approval requests",
            usage="workflow approvals",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow approvals command"""
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get pending approvals
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "quality_controller",
                {
                    "action": "get_pending_approvals",
                    "project_id": project.project_id,
                },
                operation_name="get pending approvals",
            )

            pending_approvals = result.get("pending_approvals", [])

            if not pending_approvals:
                return self.success("No pending workflow approvals")

            # Display approvals in table format
            self._display_pending_approvals(pending_approvals)
            return self.success()
        except ValueError as e:
            return self.error(str(e))

    def _display_pending_approvals(self, approvals: List[Dict[str, Any]]) -> None:
        """Display pending approvals in table format"""
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(
            f"{Fore.CYAN}PENDING WORKFLOW APPROVALS{Style.RESET_ALL}"
        )
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

        for approval in approvals:
            request_id = approval.get("request_id", "unknown")
            phase = approval.get("phase", "unknown")
            path_count = len(approval.get("all_paths", []))
            created_at = approval.get("created_at", "")

            print(f"{Fore.YELLOW}Request ID:{Style.RESET_ALL} {request_id}")
            print(f"{Fore.YELLOW}Phase:{Style.RESET_ALL} {phase}")
            print(f"{Fore.YELLOW}Available Paths:{Style.RESET_ALL} {path_count}")
            print(f"{Fore.YELLOW}Created:{Style.RESET_ALL} {created_at}\n")

            # Display recommended path
            recommended = approval.get("recommended_path", {})
            if recommended:
                print(f"{Fore.GREEN}[RECOMMENDED]{Style.RESET_ALL}")
                self._display_path_info(recommended, is_recommended=True)

            # Display alternative paths
            all_paths = approval.get("all_paths", [])
            if len(all_paths) > 1:
                print(f"\n{Fore.YELLOW}Alternative Paths:{Style.RESET_ALL}")
                for path in all_paths:
                    if path.get("path_id") != recommended.get("path_id"):
                        self._display_path_info(path, is_recommended=False)

            print(f"\n{Fore.CYAN}{'-'*100}{Style.RESET_ALL}\n")

    def _display_path_info(
        self, path: Dict[str, Any], is_recommended: bool = False
    ) -> None:
        """Display detailed path information"""
        path_id = path.get("path_id", "unknown")
        total_cost = path.get("total_cost_tokens", 0)
        total_cost_usd = path.get("total_cost_usd", 0.0)
        risk_score = path.get("risk_score", 0.0)
        quality_score = path.get("quality_score", 0.0)
        roi_score = path.get("roi_score", 0.0)
        node_count = len(path.get("nodes", []))

        marker = ">> " if is_recommended else "   "
        print(f"{marker}Path ID: {path_id}")
        print(f"    Nodes: {node_count} | Cost: {total_cost} tokens (${total_cost_usd:.3f})")
        print(
            f"    Risk: {risk_score:.1f}% | Quality: {quality_score:.1f} | ROI: {roi_score:.2f}"
        )

        missing = path.get("missing_categories", [])
        if missing:
            print(f"    Missing Categories: {', '.join(missing[:3])}")


class WorkflowApproveCommand(BaseCommand):
    """
    Approve a workflow path.

    Approves a pending workflow approval request by selecting one of the
    available paths. Execution resumes after approval.

    Usage: /workflow approve <request_id> <path_id>
    """

    def __init__(self):
        super().__init__(
            name="workflow approve",
            description="Approve a workflow path",
            usage="workflow approve <request_id> <path_id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow approve command"""
        if not self.validate_args(args, min_count=2):
            return self.error("Usage: workflow approve <request_id> <path_id>")

        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        request_id = args[0]
        path_id = args[1]

        # Approve workflow
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "quality_controller",
                {
                    "action": "approve_workflow",
                    "request_id": request_id,
                    "approved_path_id": path_id,
                },
                operation_name="approve workflow",
            )

            print(
                f"\n{Fore.GREEN}✓ Workflow approved!{Style.RESET_ALL}"
            )
            print(f"  Path ID: {path_id}")
            print(f"  Execution will resume with this path\n")
            return self.success()
        except ValueError as e:
            return self.error(str(e))


class WorkflowRejectCommand(BaseCommand):
    """
    Reject a workflow approval.

    Rejects a pending workflow approval request and optionally provides
    a reason for the rejection.

    Usage: /workflow reject <request_id> [reason]
    """

    def __init__(self):
        super().__init__(
            name="workflow reject",
            description="Reject a workflow approval",
            usage="workflow reject <request_id> [reason]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow reject command"""
        if not self.validate_args(args, min_count=1):
            return self.error("Usage: workflow reject <request_id> [reason]")

        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        request_id = args[0]
        reason = " ".join(args[1:]) if len(args) > 1 else "User rejection"

        # Reject workflow
        try:
            result = safe_orchestrator_call(
                orchestrator,
                "quality_controller",
                {
                    "action": "reject_workflow",
                    "request_id": request_id,
                    "reason": reason,
                },
                operation_name="reject workflow",
            )

            print(f"\n{Fore.YELLOW}⚠ Workflow rejected{Style.RESET_ALL}")
            print(f"  Reason: {reason}")
            print(f"  Alternative workflows may be requested\n")
            return self.success()
        except ValueError as e:
            return self.error(str(e))


class WorkflowInfoCommand(BaseCommand):
    """
    Show detailed workflow approval information.

    Displays full details about a specific pending workflow approval
    including all paths, metrics, and recommendations.

    Usage: /workflow info <request_id>
    """

    def __init__(self):
        super().__init__(
            name="workflow info",
            description="Show detailed workflow information",
            usage="workflow info <request_id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow info command"""
        if not self.validate_args(args, min_count=1):
            return self.error("Usage: workflow info <request_id>")

        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not project:
            return self.error("No project loaded")

        if not orchestrator:
            return self.error("Orchestrator not available")

        request_id = args[0]

        # Get pending approvals
        result = safe_orchestrator_call(
            orchestrator,
            "quality_controller",
            {
                "action": "get_pending_approvals",
                "project_id": project.project_id,
            },
            operation_name="get pending approvals",
        )

        try:
            pending_approvals = result.get("pending_approvals", [])

            # Find matching approval
            approval = next(
                (a for a in pending_approvals if a.get("request_id") == request_id),
                None,
            )

            if not approval:
                return self.error(f"Approval request not found: {request_id}")

            self._display_detailed_approval(approval)
            return self.success()
        except ValueError as e:
            return self.error(str(e))

    def _display_detailed_approval(self, approval: Dict[str, Any]) -> None:
        """Display detailed approval information"""
        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}WORKFLOW APPROVAL DETAILS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

        # Header info
        print(f"{Fore.YELLOW}Request ID:{Style.RESET_ALL} {approval.get('request_id')}")
        print(f"{Fore.YELLOW}Phase:{Style.RESET_ALL} {approval.get('phase')}")
        print(f"{Fore.YELLOW}Strategy:{Style.RESET_ALL} {approval.get('strategy')}")
        print(f"{Fore.YELLOW}Created:{Style.RESET_ALL} {approval.get('created_at')}\n")

        # All paths comparison table
        all_paths = approval.get("all_paths", [])
        recommended = approval.get("recommended_path", {})

        print(f"{Fore.YELLOW}Available Paths ({len(all_paths)} total):{Style.RESET_ALL}\n")
        print(
            f"{'Path':<6} {'Cost (tokens)':<15} {'Cost (USD)':<12} {'Risk':<8} "
            f"{'Quality':<10} {'ROI':<8} {'Status':<15}"
        )
        print("-" * 100)

        for i, path in enumerate(all_paths, 1):
            is_recommended = path.get("path_id") == recommended.get("path_id")
            marker = "✓ " if is_recommended else "  "

            status_str = "RECOMMENDED" if is_recommended else "alternative"
            status_color = Fore.GREEN if is_recommended else Fore.WHITE

            print(
                f"{marker}{i:<4} "
                f"{path.get('total_cost_tokens', 0):<15} "
                f"${path.get('total_cost_usd', 0.0):<11.3f} "
                f"{path.get('risk_score', 0.0):<7.1f} "
                f"{path.get('quality_score', 0.0):<9.1f} "
                f"{path.get('roi_score', 0.0):<7.2f} "
                f"{status_color}{status_str:<15}{Style.RESET_ALL}"
            )

        print(f"\n{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
