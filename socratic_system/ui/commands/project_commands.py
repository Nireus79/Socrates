"""Project management commands"""

import datetime
from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.core import get_all_project_types, get_project_type_description
from socratic_system.ui.commands.base import BaseCommand


class ProjectCreateCommand(BaseCommand):
    """Create a new project"""

    def __init__(self):
        super().__init__(
            name="project create", description="Create a new project", usage="project create <name>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project create command"""
        if not self.require_user(context):
            return self.error("Must be logged in to create a project")

        if not self.validate_args(args, min_count=1):
            project_name = input(f"{Fore.WHITE}Project name: ").strip()
        else:
            project_name = " ".join(args)  # Allow spaces in project name

        if not project_name:
            return self.error("Project name cannot be empty")

        # Ask about project type
        project_type = self._ask_project_type()

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        if not orchestrator or not app or not user:
            return self.error("Required context not available")

        # Create project using orchestrator
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": project_name,
                "owner": user.username,
                "project_type": project_type,
            },
        )

        if result["status"] == "success":
            project = result["project"]
            app.current_project = project
            app.context_display.set_context(project=project)

            self.print_success(f"Project '{project_name}' created successfully!")
            print(
                f"{Fore.CYAN}Project Type: {Style.RESET_ALL}{get_project_type_description(project_type)}"
            )
            print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
            print("  • Use /chat to start the Socratic session")
            print("  • Use /collab add <username> to invite collaborators")
            print("  • Use /docs import <path> to import documents")

            return self.success(data={"project": project})
        else:
            return self.error(result.get("message", "Failed to create project"))

    def _ask_project_type(self) -> str:
        """Ask user to select project type"""
        project_types = get_all_project_types()

        print(f"\n{Fore.CYAN}What type of project are you building?{Style.RESET_ALL}")
        for i, ptype in enumerate(project_types, 1):
            description = get_project_type_description(ptype)
            print(f"{i}. {description}")

        while True:
            choice = input(f"\n{Fore.WHITE}Select project type (1-{len(project_types)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(project_types):
                return project_types[int(choice) - 1]
            print(
                f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(project_types)}.{Style.RESET_ALL}"
            )


class ProjectLoadCommand(BaseCommand):
    """Load an existing project"""

    def __init__(self):
        super().__init__(
            name="project load", description="Load an existing project", usage="project load"
        )

    def _display_projects(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Display projects organized by status (active/archived).

        Args:
            result: Result dict with projects list

        Returns:
            Flattened list of all projects for selection
        """
        # Separate active and archived
        active_projects = [p for p in result["projects"] if p.get("status") != "archived"]
        archived_projects = [p for p in result["projects"] if p.get("status") == "archived"]

        print(f"\n{Fore.CYAN}Your Projects:{Style.RESET_ALL}")

        all_projects = []

        if active_projects:
            print(f"{Fore.GREEN}Active Projects:{Style.RESET_ALL}")
            for project in active_projects:
                all_projects.append(project)
                print(
                    f"{len(all_projects)}. 📁 {project['name']} ({project['phase']}) - {project['updated_at']}"
                )

        if archived_projects:
            print(f"{Fore.YELLOW}Archived Projects:{Style.RESET_ALL}")
            for project in archived_projects:
                all_projects.append(project)
                print(
                    f"{len(all_projects)}. 🗄️ {project['name']} ({project['phase']}) - {project['updated_at']}"
                )

        return all_projects

    def _load_selected_project(
        self, project_info: Dict[str, Any], orchestrator, app
    ) -> Dict[str, Any]:
        """
        Load selected project and update app context.

        Args:
            project_info: Selected project info
            orchestrator: Orchestrator instance
            app: App instance

        Returns:
            Result dict with project or error
        """
        project_id = project_info["project_id"]

        # Load project
        result = orchestrator.process_request(
            "project_manager", {"action": "load_project", "project_id": project_id}
        )

        if result["status"] == "success":
            project = result["project"]
            app.current_project = project
            app.context_display.set_context(project=project)

            if getattr(project, "is_archived", False):
                self.print_warning(f"Archived project loaded: {project.name}")
                print(
                    f"{Fore.YELLOW}Note: This project is archived. Some features may be limited.{Style.RESET_ALL}"
                )
            else:
                self.print_success(f"Project loaded: {project.name}")

            return self.success(data={"project": project})
        else:
            return self.error(result.get("message", "Failed to load project"))

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project load command"""
        if not self.require_user(context):
            return self.error("Must be logged in to load a project")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        if not orchestrator or not app or not user:
            return self.error("Required context not available")

        # Get user's projects
        result = orchestrator.process_request(
            "project_manager", {"action": "list_projects", "username": user.username}
        )

        if result["status"] != "success" or not result.get("projects"):
            self.print_info("No projects found")
            return self.success()

        # Display projects and get selection
        all_projects = self._display_projects(result)

        try:
            choice = int(input(f"\n{Fore.WHITE}Select project (1-{len(all_projects)}): ")) - 1
            if 0 <= choice < len(all_projects):
                project_info = all_projects[choice]
                return self._load_selected_project(project_info, orchestrator, app)
            else:
                return self.error("Invalid selection")
        except ValueError:
            return self.error("Invalid input")


class ProjectListCommand(BaseCommand):
    """List all projects"""

    def __init__(self):
        super().__init__(
            name="project list", description="List all your projects", usage="project list"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project list command"""
        if not self.require_user(context):
            return self.error("Must be logged in to list projects")

        orchestrator = context.get("orchestrator")
        user = context.get("user")

        if not orchestrator or not user:
            return self.error("Required context not available")

        result = orchestrator.process_request(
            "project_manager", {"action": "list_projects", "username": user.username}
        )

        if result["status"] != "success" or not result.get("projects"):
            self.print_info("No projects found")
            return self.success()

        print(f"\n{Fore.CYAN}All Your Projects:{Style.RESET_ALL}")
        for project in result["projects"]:
            status_indicator = "🗄️" if project.get("status") == "archived" else "📁"
            status_color = Fore.YELLOW if project.get("status") == "archived" else Fore.WHITE
            print(
                f"{status_color}{status_indicator} {project['name']:30} ({project['phase']:15}) - {project['updated_at']}"
            )

        print()
        return self.success()


class ProjectArchiveCommand(BaseCommand):
    """Archive the current project"""

    def __init__(self):
        super().__init__(
            name="project archive",
            description="Archive the current project",
            usage="project archive",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project archive command"""
        if not self.require_project(context):
            return self.error("No project loaded")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")
        project = context.get("project")

        if not orchestrator or not app or not user or not project:
            return self.error("Required context not available")

        if user.username != project.owner:
            return self.error("Only the project owner can archive projects")

        print(f"\n{Fore.YELLOW}Archive project '{project.name}'?{Style.RESET_ALL}")
        print("This will hide it from normal view but preserve all data.")

        confirm = input(f"{Fore.CYAN}Continue? (y/n): ").lower()
        if confirm != "y":
            self.print_info("Archiving cancelled")
            return self.success()

        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "archive_project",
                "project_id": project.project_id,
                "requester": user.username,
            },
        )

        if result["status"] == "success":
            self.print_success(result["message"])
            app.current_project = None
            app.context_display.set_context(project=None)

            return self.success()
        else:
            return self.error(result.get("message", "Failed to archive project"))


class ProjectRestoreCommand(BaseCommand):
    """Restore an archived project"""

    def __init__(self):
        super().__init__(
            name="project restore",
            description="Restore an archived project",
            usage="project restore",
        )

    def _display_archived_projects(self, archived_projects: List[Dict[str, Any]]) -> None:
        """
        Display archived projects with formatted dates.

        Args:
            archived_projects: List of archived project dictionaries
        """
        print(f"\n{Fore.CYAN}Archived Projects:{Style.RESET_ALL}")

        for i, project_info in enumerate(archived_projects, 1):
            archived_date = project_info.get("archived_at", "Unknown")
            if isinstance(archived_date, str):
                try:
                    archived_date = datetime.datetime.fromisoformat(archived_date).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                except (ValueError, TypeError):
                    pass

            print(
                f"{i}. {project_info['name']} by {project_info['owner']} (archived: {archived_date})"
            )

    def _restore_selected_project(
        self, project: Dict[str, Any], user, orchestrator
    ) -> Dict[str, Any]:
        """
        Restore a selected archived project.

        Args:
            project: Selected project dictionary
            user: Current user
            orchestrator: Orchestrator instance

        Returns:
            Result dictionary with success/error status
        """
        # Check if user has permission
        if user.username != project["owner"]:
            return self.error("Only the project owner can restore projects")

        confirm = input(f"{Fore.CYAN}Restore project '{project['name']}'? (y/n): ").lower()
        if confirm != "y":
            self.print_info("Restoration cancelled")
            return self.success()

        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "restore_project",
                "project_id": project["project_id"],
                "requester": user.username,
            },
        )

        if result["status"] == "success":
            self.print_success(f"Project '{project['name']}' restored successfully!")
            return self.success()
        else:
            return self.error(result.get("message", "Failed to restore project"))

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project restore command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        orchestrator = context.get("orchestrator")
        user = context.get("user")

        if not orchestrator or not user:
            return self.error("Required context not available")

        result = orchestrator.process_request(
            "project_manager", {"action": "get_archived_projects"}
        )

        if result["status"] != "success" or not result.get("archived_projects"):
            self.print_info("No archived projects found")
            return self.success()

        archived_projects = result["archived_projects"]
        self._display_archived_projects(archived_projects)

        try:
            choice = input(
                f"\n{Fore.WHITE}Select project to restore (1-{len(archived_projects)}, or 0 to cancel): "
            ).strip()

            if choice == "0":
                return self.success()

            index = int(choice) - 1
            if 0 <= index < len(archived_projects):
                project = archived_projects[index]
                return self._restore_selected_project(project, user, orchestrator)
            else:
                return self.error("Invalid selection")

        except ValueError:
            return self.error("Invalid input")


class ProjectDeleteCommand(BaseCommand):
    """Permanently delete a project"""

    def __init__(self):
        super().__init__(
            name="project delete",
            description="Permanently delete a project (cannot be undone)",
            usage="project delete",
        )

    def _get_owned_projects(
        self, user, orchestrator, result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get list of projects owned by the user.

        Args:
            user: Current user
            orchestrator: Orchestrator instance
            result: Result dict with projects list

        Returns:
            List of owned project dictionaries
        """
        owned_projects = []
        for project_info in result["projects"]:
            project = orchestrator.database.load_project(project_info["project_id"])
            if project and project.owner == user.username:
                owned_projects.append(
                    {
                        "project_id": project.project_id,
                        "name": project.name,
                        "status": project_info.get("status", "active"),
                        "collaborator_count": len(project.collaborators),
                    }
                )
        return owned_projects

    def _display_owned_projects(self, owned_projects: List[Dict[str, Any]]) -> None:
        """
        Display owned projects for deletion selection.

        Args:
            owned_projects: List of owned project dictionaries
        """
        print(f"\n{Fore.RED}⚠️  PERMANENT PROJECT DELETION{Style.RESET_ALL}")
        print("Select a project to permanently delete:")

        for i, project in enumerate(owned_projects, 1):
            status_indicator = "🗄️" if project["status"] == "archived" else "📁"
            collab_text = (
                f"({project['collaborator_count']} collaborators)"
                if project["collaborator_count"] > 0
                else "(no collaborators)"
            )
            print(f"{i}. {status_indicator} {project['name']} {collab_text}")

    def _confirm_delete(self, project: Dict[str, Any]) -> bool:
        """
        Get double confirmation for project deletion.

        Args:
            project: Project to delete

        Returns:
            True if user confirmed deletion, False otherwise
        """
        print(f"\n{Fore.RED}⚠️  You are about to PERMANENTLY DELETE:{Style.RESET_ALL}")
        print(f"Project: {project['name']}")
        print(f"Status: {project['status']}")
        print(f"Collaborators: {project['collaborator_count']}")
        print(f"\n{Fore.YELLOW}This action CANNOT be undone!{Style.RESET_ALL}")
        print("All conversation history, context, and project data will be lost forever.")

        confirm1 = input(f"\n{Fore.RED}Type the project name to continue: ").strip()
        if confirm1 != project["name"]:
            self.print_info("Deletion cancelled")
            return False

        confirm2 = input(f"{Fore.RED}Type 'DELETE' to confirm permanent deletion: ").strip()
        if confirm2 != "DELETE":
            self.print_info("Deletion cancelled")
            return False

        return True

    def _delete_selected_project(
        self, project: Dict[str, Any], user, orchestrator, app
    ) -> Dict[str, Any]:
        """
        Delete selected project after confirmation.

        Args:
            project: Project to delete
            user: Current user
            orchestrator: Orchestrator instance
            app: App instance

        Returns:
            Result dictionary with success/error status
        """
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "delete_project_permanently",
                "project_id": project["project_id"],
                "requester": user.username,
                "confirmation": "DELETE",
            },
        )

        if result["status"] == "success":
            self.print_success(result["message"])

            # Clear current project if it was the deleted one
            if app.current_project and app.current_project.project_id == project["project_id"]:
                app.current_project = None
                app.context_display.set_context(project=None)

            return self.success()
        else:
            return self.error(result.get("message", "Failed to delete project"))

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project delete command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        if not orchestrator or not app or not user:
            return self.error("Required context not available")

        # Get user's owned projects
        result = orchestrator.process_request(
            "project_manager", {"action": "list_projects", "username": user.username}
        )

        if result["status"] != "success" or not result.get("projects"):
            self.print_info("No projects found")
            return self.success()

        # Filter to only owned projects
        owned_projects = self._get_owned_projects(user, orchestrator, result)

        if not owned_projects:
            self.print_info("You don't own any projects")
            return self.success()

        # Display projects and get selection
        self._display_owned_projects(owned_projects)

        try:
            choice = input(
                f"\n{Fore.WHITE}Select project (1-{len(owned_projects)}, or 0 to cancel): "
            ).strip()

            if choice == "0":
                return self.success()

            index = int(choice) - 1
            if 0 <= index < len(owned_projects):
                project = owned_projects[index]

                # Get confirmation from user
                if not self._confirm_delete(project):
                    return self.success()

                # Delete the project
                return self._delete_selected_project(project, user, orchestrator, app)
            else:
                return self.error("Invalid selection")

        except ValueError:
            return self.error("Invalid input")
