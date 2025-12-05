"""Collaboration and team management commands"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class CollabAddCommand(BaseCommand):
    """Add a collaborator to the current project"""

    def __init__(self):
        super().__init__(
            name="collab add",
            description="Add a collaborator to the current project",
            usage="collab add <username>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collab add command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        if not self.validate_args(args, min_count=1):
            username = input(f"{Fore.WHITE}Username to add: ").strip()
        else:
            username = args[0]

        if not username:
            return self.error("Username cannot be empty")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project or not user:
            return self.error("Required context not available")

        # Only owner can add collaborators
        if user.username != project.owner:
            return self.error("Only the project owner can add collaborators")

        # Check if user exists
        if not orchestrator.database.user_exists(username):
            return self.error(f"User '{username}' does not exist in the system")

        # Check if already owner
        if username == project.owner:
            return self.error("User is already the project owner")

        # Check if already collaborator
        if username in project.collaborators:
            return self.error(f"User '{username}' is already a collaborator")

        # Add collaborator
        result = orchestrator.process_request(
            "project_manager",
            {"action": "add_collaborator", "project": project, "username": username},
        )

        if result["status"] == "success":
            self.print_success(f"Added '{username}' as collaborator!")
            project.collaborators.append(username)

            # Save project
            orchestrator.process_request(
                "project_manager", {"action": "save_project", "project": project}
            )

            return self.success(data={"collaborator": username})
        else:
            return self.error(result.get("message", "Failed to add collaborator"))


class CollabRemoveCommand(BaseCommand):
    """Remove a collaborator from the current project"""

    def __init__(self):
        super().__init__(
            name="collab remove",
            description="Remove a collaborator from the current project",
            usage="collab remove <username>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collab remove command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project or not user:
            return self.error("Required context not available")

        # Only owner can remove collaborators
        if user.username != project.owner:
            return self.error("Only the project owner can remove collaborators")

        if not project.collaborators:
            self.print_info("No collaborators to remove")
            return self.success()

        # Get username from args or interactive selection
        if self.validate_args(args, min_count=1):
            username = args[0]
        else:
            print(f"\n{Fore.YELLOW}Current Collaborators:{Style.RESET_ALL}")
            for i, collaborator in enumerate(project.collaborators, 1):
                print(f"{i}. {collaborator}")

            try:
                choice = (
                    int(
                        input(
                            f"\n{Fore.WHITE}Select collaborator to remove (1-{len(project.collaborators)}): "
                        )
                    )
                    - 1
                )
                if 0 <= choice < len(project.collaborators):
                    username = project.collaborators[choice]
                else:
                    return self.error("Invalid selection")
            except ValueError:
                return self.error("Invalid input")

        if username not in project.collaborators:
            return self.error(f"User '{username}' is not a collaborator")

        confirm = input(f"{Fore.YELLOW}Remove '{username}'? (y/n): ").lower()
        if confirm != "y":
            self.print_info("Removal cancelled")
            return self.success()

        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "remove_collaborator",
                "project": project,
                "username": username,
                "requester": user.username,
            },
        )

        if result["status"] == "success":
            self.print_success(f"Removed '{username}' from project!")
            # Only remove from local list if still present
            if username in project.collaborators:
                project.collaborators.remove(username)

                # Save project
                orchestrator.process_request(
                    "project_manager", {"action": "save_project", "project": project}
                )

            return self.success(data={"removed_user": username})
        else:
            return self.error(result.get("message", "Failed to remove collaborator"))


class CollabListCommand(BaseCommand):
    """List all collaborators for the current project"""

    def __init__(self):
        super().__init__(
            name="collab list",
            description="List all collaborators for the current project",
            usage="collab list",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collab list command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator or not project:
            return self.error("Required context not available")

        # Get collaborators
        result = orchestrator.process_request(
            "project_manager", {"action": "list_collaborators", "project": project}
        )

        if result["status"] == "success":
            print(f"\n{Fore.CYAN}Collaborators for '{project.name}':{Style.RESET_ALL}")

            members = result.get("collaborators", [])

            if not members:
                self.print_info("No collaborators")
                return self.success()

            for member in members:
                role_color = Fore.GREEN if member["role"] == "owner" else Fore.WHITE
                role_symbol = "[USER]" if member["role"] == "collaborator" else "[OWNER]"
                print(
                    f"{role_color}{role_symbol} {member['username']:20} ({member['role']}){Style.RESET_ALL}"
                )

            print()
            return self.success(data={"collaborators": members})
        else:
            return self.error(result.get("message", "Failed to list collaborators"))
