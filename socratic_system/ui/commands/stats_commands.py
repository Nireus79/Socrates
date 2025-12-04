"""Project statistics and progress commands"""

from typing import Dict, Any, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class ProjectStatsCommand(BaseCommand):
    """Display project statistics"""

    def __init__(self):
        super().__init__(
            name="project stats",
            description="View comprehensive project statistics",
            usage="project stats"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project stats command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get statistics
        result = orchestrator.process_request('context_analyzer', {
            'action': 'get_statistics',
            'project': project
        })

        if result['status'] == 'success':
            stats = result['statistics']

            self.print_header(f"Project Statistics: {stats['project_name']}")

            # Basic Info
            print(f"{Fore.CYAN}Project Information:{Style.RESET_ALL}")
            print(f"  Owner:             {stats['owner']}")
            print(f"  Phase:             {stats['current_phase']}")
            print(f"  Status:            {stats['status']}")
            print(f"  Progress:          {self._get_progress_bar(stats['progress'])} {stats['progress']}%")
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

            return self.success(data={'statistics': stats})
        else:
            return self.error(result.get('message', 'Failed to get statistics'))

    @staticmethod
    def _get_progress_bar(progress: int, width: int = 20) -> str:
        """Get a visual progress bar"""
        filled = int(width * progress / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"{Fore.GREEN}{bar}{Style.RESET_ALL}"


class ProjectProgressCommand(BaseCommand):
    """Update project progress percentage"""

    def __init__(self):
        super().__init__(
            name="project progress",
            description="Update project progress percentage (0-100)",
            usage="project progress <0-100>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project progress command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        project = context.get('project')
        if not project:
            return self.error("No project loaded")

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
        project.updated_at = __import__('datetime').datetime.now()

        # Save project
        orchestrator = context.get('orchestrator')
        if orchestrator:
            result = orchestrator.process_request('project_manager', {
                'action': 'save_project',
                'project': project
            })

            if result['status'] == 'success':
                print(f"{Fore.GREEN}Progress bar:{Style.RESET_ALL}")
                filled = int(20 * progress / 100)
                bar = '█' * filled + '░' * (20 - filled)
                print(f"  {Fore.GREEN}{bar}{Style.RESET_ALL} {progress}%")
                self.print_success(f"Project progress updated to {progress}%")
                return self.success(data={'progress': progress})
            else:
                return self.error("Failed to save project progress")
        else:
            return self.error("Orchestrator not available")


class ProjectStatusCommand(BaseCommand):
    """Set project status"""

    def __init__(self):
        super().__init__(
            name="project status",
            description="Set project status (active/completed/on-hold)",
            usage="project status <active|completed|on-hold>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project status command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        project = context.get('project')
        if not project:
            return self.error("No project loaded")

        valid_statuses = ['active', 'completed', 'on-hold']

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
        project.updated_at = __import__('datetime').datetime.now()

        # Save project
        orchestrator = context.get('orchestrator')
        if orchestrator:
            result = orchestrator.process_request('project_manager', {
                'action': 'save_project',
                'project': project
            })

            if result['status'] == 'success':
                self.print_success(f"Project status updated to '{status}'")
                return self.success(data={'status': status})
            else:
                return self.error("Failed to save project status")
        else:
            return self.error("Orchestrator not available")
