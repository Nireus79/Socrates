"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Conflict detection and resolution commands
"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class ConflictAnalyzeCommand(BaseCommand):
    """Analyze conflicts in the current project"""

    def __init__(self):
        super().__init__(
            name="conflict analyze",
            description="Analyze conflicts in the current project",
            usage="conflict analyze",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conflict analyze command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get the conflict integration
        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.conflict:
            return self.error("Conflict detection not available")

        try:
            # Get project specifications that might have conflicts
            proposals = {
                "requirements": project.requirements or [],
                "tech_stack": project.tech_stack or [],
                "constraints": project.constraints or [],
                "goals": project.goals or [],
            }

            # Detect conflicts in proposals
            all_conflicts = []
            for field, values in proposals.items():
                if not values:
                    continue

                # Convert to dict format for conflict detection
                agent_values = {
                    f"agent_{i}": val for i, val in enumerate(values)
                }
                agents = list(agent_values.keys())

                conflict = library_manager.conflict.detect_and_resolve(
                    field_name=field,
                    values=agent_values,
                    agents=agents,
                )

                if conflict and conflict.get("conflict_detected"):
                    all_conflicts.append({
                        "field": field,
                        "type": "data_conflict",
                        "recommended_value": conflict.get("recommended_value"),
                        "confidence": conflict.get("confidence"),
                    })

            if not all_conflicts:
                self.print_info("No conflicts detected in project")
                return self.success(data={"conflicts": [], "count": 0})

            # Display conflicts
            self.print_header(f"Conflicts in '{project.name}'")
            print(f"\n{Fore.YELLOW}Found {len(all_conflicts)} conflict(s):{Style.RESET_ALL}\n")

            for i, conflict_data in enumerate(all_conflicts, 1):
                print(f"{Fore.CYAN}[{i}] Field: {conflict_data['field']}{Style.RESET_ALL}")
                print(f"    Type: {conflict_data['type']}")
                print(f"    Confidence: {conflict_data['confidence']:.1%}")
                if conflict_data['recommended_value']:
                    print(f"    Recommendation: {conflict_data['recommended_value']}")
                print()

            return self.success(data={
                "conflicts": all_conflicts,
                "count": len(all_conflicts),
            })

        except Exception as e:
            return self.error(f"Failed to analyze conflicts: {str(e)}")


class ConflictListCommand(BaseCommand):
    """List stored conflicts for the current project"""

    def __init__(self):
        super().__init__(
            name="conflict list",
            description="List detected conflicts for the current project",
            usage="conflict list",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conflict list command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        try:
            # Get conflicts from database (once implemented)
            # For now, we'll get from analyzer
            conflicts = orchestrator.database.get_project_conflicts(project.project_id) if hasattr(orchestrator.database, 'get_project_conflicts') else []

            if not conflicts:
                self.print_info("No conflicts stored for this project")
                return self.success(data={"conflicts": [], "count": 0})

            self.print_header(f"Conflicts for '{project.name}'")

            conflicts_data = []
            for conflict in conflicts:
                conflict_dict = {
                    "conflict_id": conflict.get("conflict_id"),
                    "type": conflict.get("conflict_type"),
                    "field": conflict.get("field"),
                    "severity": conflict.get("severity", "medium"),
                    "detected_at": conflict.get("detected_at"),
                    "status": conflict.get("status", "open"),
                }
                conflicts_data.append(conflict_dict)

                status_color = {
                    "open": Fore.RED,
                    "resolved": Fore.GREEN,
                    "ignored": Fore.YELLOW,
                }.get(conflict_dict["status"], Fore.WHITE)

                print(f"\n{Fore.CYAN}[{conflict_dict['conflict_id']}] {conflict_dict['field']}{Style.RESET_ALL}")
                print(f"    Type: {conflict_dict['type']}")
                print(f"    Severity: {conflict_dict['severity']}")
                print(f"    Status: {status_color}{conflict_dict['status']}{Style.RESET_ALL}")
                print(f"    Detected: {conflict_dict['detected_at']}")

            return self.success(data={
                "conflicts": conflicts_data,
                "count": len(conflicts_data),
            })

        except Exception as e:
            return self.error(f"Failed to list conflicts: {str(e)}")


class ConflictResolveCommand(BaseCommand):
    """Resolve a specific conflict"""

    def __init__(self):
        super().__init__(
            name="conflict resolve",
            description="Resolve a specific conflict using a resolution strategy",
            usage="conflict resolve <conflict_id> [strategy: voting|consensus]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conflict resolve command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Parse arguments
        if not args:
            conflict_id = input(f"{Fore.WHITE}Conflict ID to resolve: ").strip()
        else:
            conflict_id = args[0]

        if not conflict_id:
            return self.error("Conflict ID cannot be empty")

        strategy = args[1].lower() if len(args) > 1 else "voting"

        if strategy not in ["voting", "consensus"]:
            return self.error("Strategy must be 'voting' or 'consensus'")

        try:
            # Get conflict from database
            conflict_data = orchestrator.database.get_project_conflict(project.project_id, conflict_id) if hasattr(orchestrator.database, 'get_project_conflict') else None

            if not conflict_data:
                return self.error(f"Conflict {conflict_id} not found")

            # Resolve using library_manager
            library_manager = orchestrator.library_manager
            if not library_manager or not library_manager.conflict:
                return self.error("Conflict resolution not available")

            # For now, we'll use the voting strategy
            resolution_result = library_manager.conflict.resolve_with_strategy(
                conflict=conflict_data,
                strategy=strategy
            )

            # Update conflict status in database
            if hasattr(orchestrator.database, 'update_conflict_status'):
                orchestrator.database.update_conflict_status(
                    conflict_id=conflict_id,
                    status="resolved",
                    resolution=resolution_result
                )

            # Display result
            self.print_header(f"Conflict Resolution Result")
            print(f"\n{Fore.CYAN}Conflict ID:{Style.RESET_ALL} {conflict_id}")
            print(f"{Fore.CYAN}Strategy:{Style.RESET_ALL} {strategy}")
            print(f"{Fore.CYAN}Status:{Style.RESET_ALL} {Fore.GREEN}{resolution_result.get('status')}{Style.RESET_ALL}")

            if resolution_result.get("recommended_value"):
                print(f"{Fore.CYAN}Recommended Value:{Style.RESET_ALL} {resolution_result['recommended_value']}")

            if resolution_result.get("confidence"):
                confidence_pct = resolution_result['confidence']
                print(f"{Fore.CYAN}Confidence:{Style.RESET_ALL} {confidence_pct:.1%}")

            self.print_success(f"Conflict resolved successfully")

            return self.success(data={
                "conflict_id": conflict_id,
                "resolution": resolution_result,
            })

        except Exception as e:
            return self.error(f"Failed to resolve conflict: {str(e)}")


class ConflictIgnoreCommand(BaseCommand):
    """Ignore a detected conflict"""

    def __init__(self):
        super().__init__(
            name="conflict ignore",
            description="Mark a conflict as ignored",
            usage="conflict ignore <conflict_id>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conflict ignore command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        if not args:
            conflict_id = input(f"{Fore.WHITE}Conflict ID to ignore: ").strip()
        else:
            conflict_id = args[0]

        if not conflict_id:
            return self.error("Conflict ID cannot be empty")

        try:
            # Update conflict status to ignored
            if hasattr(orchestrator.database, 'update_conflict_status'):
                orchestrator.database.update_conflict_status(
                    conflict_id=conflict_id,
                    status="ignored"
                )

            self.print_success(f"Conflict {conflict_id} marked as ignored")
            return self.success(data={"conflict_id": conflict_id, "status": "ignored"})

        except Exception as e:
            return self.error(f"Failed to ignore conflict: {str(e)}")
