"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.Project statistics and progress commands
"""

from datetime import datetime
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_core.utils import serialize_datetime
from socratic_system.constants import ErrorMessages, ProjectStatus
from socratic_system.ui.commands.base import BaseCommand


class ProjectStatsCommand(BaseCommand):
    """Display project statistics"""

    def __init__(self):
        super().__init__(
            name="project stats",
            description="View comprehensive project statistics",
            usage="project stats",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project stats command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        try:
            # Calculate statistics directly from project
            from datetime import datetime, timezone

            # Calculate days active
            created_at = getattr(project, "created_at", datetime.now(timezone.utc))
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except (ValueError, TypeError):
                    created_at = datetime.now(timezone.utc)

            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_active = (now - created_at).days

            # Count conversations
            conversation_history = getattr(project, "conversation_history", []) or []
            questions_asked = sum(
                1 for msg in conversation_history if msg.get("role") == "assistant"
            )
            responses_given = sum(1 for msg in conversation_history if msg.get("role") == "user")

            # Count collaborators
            collaborators = getattr(project, "collaborators", []) or []
            num_collaborators = len(collaborators) if isinstance(collaborators, list) else 0

            # Count tech stack
            tech_stack = getattr(project, "tech_stack", []) or []
            num_tech_stack = len(tech_stack) if isinstance(tech_stack, list) else 0

            # Count requirements
            requirements = getattr(project, "requirements", []) or []
            num_requirements = len(requirements) if isinstance(requirements, list) else 0

            # Count constraints
            constraints = getattr(project, "constraints", []) or []
            num_constraints = len(constraints) if isinstance(constraints, list) else 0

            stats = {
                "project_name": getattr(project, "name", "Unknown"),
                "owner": getattr(project, "owner", "Unknown"),
                "current_phase": getattr(project, "phase", "planning"),
                "status": getattr(project, "status", "active"),
                "progress": getattr(project, "progress", 0),
                "created_at": (
                    serialize_datetime(created_at) if isinstance(created_at, datetime) else str(created_at)
                ),
                "updated_at": (
                    serialize_datetime(getattr(project, "updated_at", datetime.now()))
                    if isinstance(getattr(project, "updated_at", None), datetime)
                    else str(getattr(project, "updated_at", ""))
                ),
                "days_active": max(0, days_active),
                "collaborators": num_collaborators,
                "requirements": num_requirements,
                "tech_stack": num_tech_stack,
                "constraints": num_constraints,
                "total_conversations": len(conversation_history),
                "questions_asked": questions_asked,
                "responses_given": responses_given,
                "notes": 0,
            }

            self.print_header(f"Project Statistics: {stats['project_name']}")

            # Basic Info
            print(f"{Fore.CYAN}Project Information:{Style.RESET_ALL}")
            print(f"  Owner:             {stats['owner']}")
            print(f"  Phase:             {stats['current_phase']}")
            print(f"  Status:            {stats['status']}")
            print(
                f"  Progress:          {self._get_progress_bar(stats['progress'])} {stats['progress']}%"
            )
            print()

            # Timeline
            print(f"{Fore.CYAN}Timeline:{Style.RESET_ALL}")
            print(f"  Created:           {stats['created_at']}")
            print(f"  Last Updated:      {stats['updated_at']}")
            print(f"  Days Active:       {stats['days_active']}")
            print()

            # Team
            print(f"{Fore.CYAN}Team:{Style.RESET_ALL}")
            print(f"  Collaborators:     {stats['collaborators']}")
            print()

            # Project Details
            print(f"{Fore.CYAN}Project Details:{Style.RESET_ALL}")
            print(f"  Requirements:      {stats['requirements']}")
            print(f"  Tech Stack Items:  {stats['tech_stack']}")
            print(f"  Constraints:       {stats['constraints']}")
            print()

            # Conversation Stats
            print(f"{Fore.CYAN}Conversation Activity:{Style.RESET_ALL}")
            print(f"  Total Messages:    {stats['total_conversations']}")
            print(f"  Questions Asked:   {stats['questions_asked']}")
            print(f"  User Responses:    {stats['responses_given']}")
            print()

            # Knowledge
            print(f"{Fore.CYAN}Knowledge:{Style.RESET_ALL}")
            print(f"  Notes:             {stats['notes']}")
            print()

            return self.success(data={"statistics": stats})
        except ValueError as e:
            return self.error(str(e))

    @staticmethod
    def _get_progress_bar(progress: int, width: int = 20) -> str:
        """Get a visual progress bar"""
        filled = int(width * progress / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"{Fore.GREEN}{bar}{Style.RESET_ALL}"


class ProjectProgressCommand(BaseCommand):
    """Update project progress percentage"""

    def __init__(self):
        super().__init__(
            name="project progress",
            description="Update project progress percentage (0-100)",
            usage="project progress <0-100>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project progress command"""
        if not self.require_project(context):
            return self.error(ErrorMessages.NO_PROJECT_LOADED)

        project = context.get("project")
        if not project:
            return self.error(ErrorMessages.NO_PROJECT_LOADED)

        # Get progress value
        if args:
            try:
                progress = int(args[0])
            except ValueError:
                return self.error("Progress must be a number between 0 and 100")
        else:
            try:
                progress = int(input(f"{Fore.WHITE}Project progress (0-100): "))
            except ValueError:
                return self.error("Progress must be a number between 0 and 100")

        # Validate
        if progress < 0 or progress > 100:
            return self.error("Progress must be between 0 and 100")

        # Update project
        project.progress = progress
        project.updated_at = datetime.now()

        # Save project to database
        orchestrator = context.get("orchestrator")
        app = context.get("app")
        if orchestrator:
            try:
                orchestrator.database.save_project(project)

                # Update app context if available
                if app:
                    app.current_project = project
                    app.context_display.set_context(project=project)

                print(f"{Fore.GREEN}Progress bar:{Style.RESET_ALL}")
                filled = int(20 * progress / 100)
                bar = "█" * filled + "░" * (20 - filled)
                print(f"  {Fore.GREEN}{bar}{Style.RESET_ALL} {progress}%")
                self.print_success(f"Project progress updated to {progress}%")
                return self.success(data={"progress": progress})
            except Exception as e:
                return self.error(str(e))
        else:
            return self.error(ErrorMessages.ORCHESTRATOR_NOT_AVAILABLE)


class ProjectStatusCommand(BaseCommand):
    """Set project status"""

    def __init__(self):
        super().__init__(
            name="project status",
            description="Set project status (active/completed/on-hold)",
            usage="project status <active|completed|on-hold>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project status command"""
        if not self.require_project(context):
            return self.error(ErrorMessages.NO_PROJECT_LOADED)

        project = context.get("project")
        if not project:
            return self.error(ErrorMessages.NO_PROJECT_LOADED)

        valid_statuses = ProjectStatus.ALL

        # Get status
        if args:
            status = args[0].lower()
        else:
            print(f"{Fore.YELLOW}Available statuses:{Style.RESET_ALL}")
            for i, s in enumerate(valid_statuses, 1):
                print(f"  {i}. {s}")
            try:
                choice = int(input(f"{Fore.WHITE}Select status (1-{len(valid_statuses)}): "))
                if 1 <= choice <= len(valid_statuses):
                    status = valid_statuses[choice - 1]
                else:
                    return self.error("Invalid choice")
            except ValueError:
                return self.error("Invalid input")

        # Validate
        if status not in valid_statuses:
            return self.error(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        # Update project
        project.status = status
        project.updated_at = datetime.now()

        # Save project
        orchestrator = context.get("orchestrator")
        app = context.get("app")
        if orchestrator:
            try:
                orchestrator.database.save_project(project)

                # Update app context if available
                if app:
                    app.current_project = project
                    app.context_display.set_context(project=project)

                self.print_success(f"Project status updated to '{status}'")
                return self.success(data={"status": status})
            except Exception as e:
                return self.error(str(e))
        else:
            return self.error(ErrorMessages.ORCHESTRATOR_NOT_AVAILABLE)
