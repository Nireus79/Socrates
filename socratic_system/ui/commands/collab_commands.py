"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.Collaboration and team management commands"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.models import VALID_ROLES
from socratic_system.ui.commands.base import BaseCommand
from socratic_system.utils.orchestrator_helper import safe_orchestrator_call


class CollabAddCommand(BaseCommand):
    """Add a collaborator to the current project with optional role"""

    def __init__(self):
        super().__init__(
            name="collab add",
            description="Add a collaborator to the current project with specified role",
            usage="collab add <username> [role]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collab add command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        username, role = self._get_collaborator_inputs(args)
        if not username or not self._validate_role(role):
            return self.error(f"Invalid role. Valid roles: {', '.join(VALID_ROLES)}")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project or not user:
            return self.error("Required context not available")

        if user.username != project.owner:
            return self.error("Only the project owner can add collaborators")

        is_valid, error_msg = self._validate_collaborator_addition(username, project, orchestrator)
        if not is_valid:
            return self.error(error_msg)

        result = safe_orchestrator_call(
            orchestrator,
            "project_manager",
            {"action": "add_collaborator", "project": project, "username": username, "role": role},
            operation_name="add collaborator"
        )

        if result.get("data", {}).get("status") == "success":
            self.print_success(f"Added '{username}' as {role}!")
            safe_orchestrator_call(
                orchestrator,
                "project_manager",
                {"action": "save_project", "project": project},
                operation_name="save project"
            )
            return self.success(data={"collaborator": username, "role": role})
        else:
            return self.error(result.get("message", "Failed to add collaborator"))

    def _get_collaborator_inputs(self, args: List[str]) -> tuple:
        """Get username and role from args or interactive input"""
        if self.validate_args(args, min_count=1):
            username = args[0]
            role = args[1] if len(args) > 1 else "creator"
        else:
            username = input(f"{Fore.WHITE}Username to add: ").strip()
            print(f"{Fore.YELLOW}Available roles: {', '.join(VALID_ROLES)}")
            role = input(f"{Fore.WHITE}Role [{VALID_ROLES[0]}]: ").strip() or VALID_ROLES[0]
        return username, role

    def _validate_role(self, role: str) -> bool:
        """Validate role against VALID_ROLES"""
        return role in VALID_ROLES

    def _validate_collaborator_addition(self, username: str, project, orchestrator) -> tuple:
        """Validate that collaborator can be added. Returns (is_valid, error_msg)"""
        if not username:
            return False, "Username cannot be empty"
        if not orchestrator.database.user_exists(username):
            return False, f"User '{username}' does not exist in the system"
        if username == project.owner:
            return False, "User is already the project owner"
        for member in project.team_members or []:
            if member.username == username:
                return False, f"User '{username}' is already a team member"
        return True, ""


class CollabRemoveCommand(BaseCommand):
    """Remove a collaborator from the current project"""

    def __init__(self):
        super().__init__(
            name="collab remove",
            description="Remove a collaborator from the current project",
            usage="collab remove <username>",
        )

    def _select_collaborator(self, project) -> str:
        """
        Interactively select a collaborator from the project.

        Args:
            project: Project object with collaborators list

        Returns:
            Selected username or None if invalid input
        """
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
                return project.collaborators[choice]
            else:
                return None
        except ValueError:
            return None

    def _remove_collaborator(self, username: str, project, user, orchestrator) -> Dict[str, Any]:
        """
        Remove a collaborator from the project after confirmation.

        Args:
            username: Username to remove
            project: Project object
            user: Current user
            orchestrator: Orchestrator instance

        Returns:
            Result dictionary with success/error status
        """
        confirm = input(f"{Fore.YELLOW}Remove '{username}'? (y/n): ").lower()
        if confirm != "y":
            self.print_info("Removal cancelled")
            return self.success()

        result = safe_orchestrator_call(
            orchestrator,
            "project_manager",
            {
                "action": "remove_collaborator",
                "project": project,
                "username": username,
                "requester": user.username,
            },
            operation_name="remove collaborator"
        )

        if result.get("data", {}).get("status") == "success":
            self.print_success(f"Removed '{username}' from project!")
            # Only remove from local list if still present
            if username in project.collaborators:
                project.collaborators.remove(username)

                # Save project
                safe_orchestrator_call(
                    orchestrator,
                    "project_manager",
                    {"action": "save_project", "project": project},
                    operation_name="save project"
                )

            return self.success(data={"removed_user": username})
        else:
            return self.error(result.get("message", "Failed to remove collaborator"))

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
            username = self._select_collaborator(project)
            if username is None:
                return self.error("Invalid input")

        if username not in project.collaborators:
            return self.error(f"User '{username}' is not a collaborator")

        # Remove the collaborator
        return self._remove_collaborator(username, project, user, orchestrator)


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
        result = safe_orchestrator_call(
            orchestrator,
            "project_manager",
            {"action": "list_collaborators", "project": project},
            operation_name="list collaborators"
        )

        if result.get("data", {}).get("status") == "success":
            print(f"\n{Fore.CYAN}Team Members for '{project.name}':{Style.RESET_ALL}\n")

            members = result.get("collaborators", [])

            if not members:
                self.print_info("No team members")
                return self.success()

            # Display header
            print(f"{Fore.WHITE}{'Username':<20} {'Role':<15} {'Status':<15}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{'-'*50}{Style.RESET_ALL}")

            for member in members:
                username = member["username"]
                role = member["role"]
                is_owner = member.get("is_owner", False)

                # Format role with color
                role_display = (
                    f"{Fore.GREEN}{role}{Style.RESET_ALL}"
                    if role == "lead"
                    else f"{Fore.CYAN}{role}{Style.RESET_ALL}"
                )

                # Format status
                status = (
                    f"{Fore.YELLOW}OWNER{Style.RESET_ALL}"
                    if is_owner
                    else f"{Fore.WHITE}Member{Style.RESET_ALL}"
                )

                print(f"{username:<20} {role_display:<30} {status}")

            print()
            return self.success(data={"collaborators": members})
        else:
            return self.error(result.get("message", "Failed to list collaborators"))


class CollabRoleCommand(BaseCommand):
    """Update a team member's role"""

    def __init__(self):
        super().__init__(
            name="collab role",
            description="Update a team member's role",
            usage="collab role <username> <new_role>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collab role command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        username, new_role = self._get_username_and_role(args)

        if not username or not new_role:
            return self.error("Username and role cannot be empty")

        if not self._validate_role(new_role):
            return self.error(f"Invalid role '{new_role}'. Valid roles: {', '.join(VALID_ROLES)}")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        user = context.get("user")

        if not orchestrator or not project or not user:
            return self.error("Required context not available")

        if user.username != project.owner:
            return self.error("Only the project owner can change roles")

        member_error = self._verify_member_exists(username, project)
        if member_error:
            return self.error(member_error)

        result = safe_orchestrator_call(
            orchestrator,
            "project_manager",
            {
                "action": "update_member_role",
                "project": project,
                "username": username,
                "role": new_role,
            },
            operation_name="update member role"
        )

        if result.get("data", {}).get("status") == "success":
            self.print_success(f"Updated '{username}' role to {new_role}!")
            safe_orchestrator_call(
                orchestrator,
                "project_manager",
                {"action": "save_project", "project": project},
                operation_name="save project"
            )
            return self.success(data={"username": username, "new_role": new_role})
        else:
            return self.error(result.get("message", "Failed to update role"))

    def _get_username_and_role(self, args: List[str]) -> tuple:
        """Get username and role from args or interactive input"""
        if self.validate_args(args, min_count=2):
            username = args[0]
            new_role = args[1]
        else:
            print(f"{Fore.YELLOW}Available roles: {', '.join(VALID_ROLES)}")
            username = input(f"{Fore.WHITE}Username: ").strip()
            new_role = input(f"{Fore.WHITE}New role: ").strip()
        return username, new_role

    def _validate_role(self, role: str) -> bool:
        """Validate role against VALID_ROLES"""
        return role in VALID_ROLES

    def _verify_member_exists(self, username: str, project) -> str:
        """Verify member exists in project. Returns error message or empty string if valid"""
        for member in project.team_members or []:
            if member.username == username:
                return ""
        return f"User '{username}' is not a team member in this project"
