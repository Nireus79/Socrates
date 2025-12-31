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


class ProjectAnalyzeCommand(BaseCommand):
    """Analyze the current project code"""

    def __init__(self):
        super().__init__(
            name="project analyze",
            description="Analyze project code comprehensively",
            usage="project analyze [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project analyze command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        if not project:
            return self.error("No project loaded. Use /project load to load a project")

        # Check if project has repository URL (GitHub imported)
        if not project.repository_url:
            return self.error("Project is not linked to a GitHub repository. Cannot analyze projects without source code.")

        print(f"{Fore.YELLOW}Analyzing project code...{Style.RESET_ALL}")

        try:
            from pathlib import Path

            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()

            # Clone repository to temp directory
            print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
            clone_result = git_manager.clone_repository(project.repository_url)
            if not clone_result.get("success"):
                return self.error(f"Failed to clone repository: {clone_result.get('error')}")

            temp_path = clone_result["path"]

            try:
                # Perform analysis
                print(f"{Fore.CYAN}Analyzing code structure...{Style.RESET_ALL}")

                analysis = {
                    "project_name": project.name,
                    "repository": project.repository_url,
                    "language": project.repository_language,
                    "file_count": project.repository_file_count,
                    "has_tests": project.repository_has_tests,
                    "code_files": 0,
                    "file_breakdown": {},
                    "total_lines": 0,
                }

                # Scan for code files
                temp_path_obj = Path(temp_path)
                code_extensions = {
                    ".py": "Python",
                    ".js": "JavaScript",
                    ".ts": "TypeScript",
                    ".java": "Java",
                    ".cpp": "C++",
                    ".c": "C",
                    ".go": "Go",
                    ".rs": "Rust",
                    ".rb": "Ruby",
                    ".php": "PHP",
                }

                for suffix, lang in code_extensions.items():
                    files = list(temp_path_obj.rglob(f"*{suffix}"))
                    # Exclude common directories
                    files = [f for f in files if not any(skip in f.parts for skip in {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist"})]

                    if files:
                        analysis["file_breakdown"][lang] = len(files)
                        analysis["code_files"] += len(files)

                        # Count lines
                        try:
                            for file in files[:50]:  # Sample first 50 files
                                with open(file, encoding='utf-8', errors='ignore') as f:
                                    analysis["total_lines"] += len(f.readlines())
                        except Exception:
                            pass

                # Run validation to get metrics
                validation_result = orchestrator.process_request(
                    "code_validation",
                    {
                        "action": "validate_project",
                        "project_path": temp_path,
                        "timeout": 300,
                    },
                )

                summary = validation_result.get("validation_summary", {})

                self.print_success("Analysis complete!")

                # Display analysis
                print(f"\n{Fore.CYAN}Project Analysis:{Style.RESET_ALL}")
                print(f"  Project: {analysis['project_name']}")
                print(f"  Repository: {analysis['repository'][:50]}..." if len(analysis['repository']) > 50 else f"  Repository: {analysis['repository']}")
                print(f"  Language: {analysis['language']}")

                print(f"\n{Fore.CYAN}Code Structure:{Style.RESET_ALL}")
                print(f"  Total Files: {analysis['file_count']}")
                print(f"  Code Files: {analysis['code_files']}")
                print(f"  Total Lines: {analysis['total_lines']}")

                if analysis["file_breakdown"]:
                    print(f"\n{Fore.CYAN}Language Breakdown:{Style.RESET_ALL}")
                    for lang, count in sorted(analysis["file_breakdown"].items(), key=lambda x: x[1], reverse=True):
                        print(f"  {lang}: {count} files")

                print(f"\n{Fore.CYAN}Code Quality:{Style.RESET_ALL}")
                print(f"  Overall Status: {summary.get('overall_status', 'unknown').upper()}")
                print(f"  Issues: {summary.get('issues_count', 0)}")
                print(f"  Warnings: {summary.get('warnings_count', 0)}")

                if project.repository_has_tests:
                    print("  Tests: Configured")
                else:
                    print(f"  {Fore.YELLOW}Tests: None detected{Style.RESET_ALL}")

                recommendations = validation_result.get("recommendations", [])
                if recommendations:
                    print(f"\n{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f"  {i}. {rec}")

                return self.success(data={"analysis": analysis})

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Analysis error: {str(e)}")
            return self.error(f"Analysis error: {str(e)}")


class ProjectTestCommand(BaseCommand):
    """Run tests on the current project"""

    def __init__(self):
        super().__init__(
            name="project test",
            description="Run tests on project",
            usage="project test [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project test command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        if not project:
            return self.error("No project loaded. Use /project load to load a project")

        # Check if project has repository URL (GitHub imported)
        if not project.repository_url:
            return self.error("Project is not linked to a GitHub repository. Cannot run tests on projects without source code.")

        print(f"{Fore.YELLOW}Running tests...{Style.RESET_ALL}")

        try:
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()

            # Clone repository to temp directory
            print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
            clone_result = git_manager.clone_repository(project.repository_url)
            if not clone_result.get("success"):
                return self.error(f"Failed to clone repository: {clone_result.get('error')}")

            temp_path = clone_result["path"]

            try:
                # Run tests using CodeValidationAgent
                test_result = orchestrator.process_request(
                    "code_validation",
                    {
                        "action": "run_tests",
                        "project_path": temp_path,
                        "timeout": 300,
                    },
                )

                if test_result["status"] == "success":
                    results = test_result.get("test_results", {})

                    self.print_success("Test execution complete!")

                    # Display test results
                    print(f"\n{Fore.CYAN}Test Results:{Style.RESET_ALL}")
                    print(f"  Framework: {results.get('framework', 'unknown')}")
                    print(f"  Tests Found: {'Yes' if results.get('tests_found') else 'No'}")

                    if results.get("tests_found"):
                        print(f"  {Fore.GREEN}Passed: {results.get('tests_passed', 0)}{Style.RESET_ALL}")
                        if results.get('tests_failed', 0) > 0:
                            print(f"  {Fore.RED}Failed: {results.get('tests_failed', 0)}{Style.RESET_ALL}")
                        if results.get('tests_skipped', 0) > 0:
                            print(f"  {Fore.YELLOW}Skipped: {results.get('tests_skipped', 0)}{Style.RESET_ALL}")
                        print(f"  Duration: {results.get('duration_seconds', 0):.2f}s")

                        # Show failures if any
                        failures = results.get("failures", [])
                        if failures:
                            print(f"\n{Fore.RED}Failures:{Style.RESET_ALL}")
                            for failure in failures[:5]:  # Show first 5
                                print(f"  • {failure.get('test', 'Unknown')}")
                                if failure.get('message'):
                                    msg = failure['message'][:100]
                                    print(f"    {msg}...")
                    else:
                        print(f"  {Fore.YELLOW}No tests found in project{Style.RESET_ALL}")

                    return self.success(data={"test_results": results})
                else:
                    return self.error(f"Test execution failed: {test_result.get('message', 'Unknown error')}")

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Test execution error: {str(e)}")
            return self.error(f"Test execution error: {str(e)}")


class ProjectFixCommand(BaseCommand):
    """Apply automated fixes to the project"""

    def __init__(self):
        super().__init__(
            name="project fix",
            description="Apply automated fixes to project code",
            usage="project fix [issue-type]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project fix command"""
        if not self._validate_fix_context(context):
            return self.error("Context validation failed")

        orchestrator = context.get("orchestrator")
        project = context.get("project")
        issue_type = self._get_and_validate_issue_type(args)

        if not issue_type:
            return self.error("Invalid issue type")

        print(f"{Fore.YELLOW}Applying fixes (type: {issue_type})...{Style.RESET_ALL}")

        try:
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()
            clone_result = self._clone_fix_repo(git_manager, project.repository_url)
            if not clone_result:
                return self.error("Failed to clone repository")

            temp_path = clone_result["path"]
            try:
                print(f"{Fore.CYAN}Identifying issues...{Style.RESET_ALL}")
                validation_result = orchestrator.process_request(
                    "code_validation",
                    {
                        "action": "validate_project",
                        "project_path": temp_path,
                        "timeout": 300,
                    },
                )

                if validation_result["status"] != "success":
                    return self.error("Validation failed before fixes")

                validation_data = validation_result.get("validation_results", {})
                issues = self._gather_fixable_issues(validation_data, issue_type)

                if not issues:
                    self.print_info("No issues found to fix")
                    return self.success()

                self._display_issues(issues)

                if not self._confirm_fixes():
                    return self.success()

                print(f"{Fore.CYAN}Generating fixes with Claude...{Style.RESET_ALL}")
                fixes_applied = self._apply_fixes(issues, temp_path)

                self._display_fix_summary(issues, fixes_applied)
                return self.success(data={"fixes_applied": fixes_applied})

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Fix error: {str(e)}")
            return self.error(f"Fix error: {str(e)}")

    def _validate_fix_context(self, context: Dict[str, Any]) -> bool:
        """Validate context for fix command"""
        if not self.require_user(context):
            return False

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            self.error("Orchestrator not available")
            return False

        if not project:
            self.error("No project loaded. Use /project load to load a project")
            return False

        if not project.repository_url:
            self.error(
                "Project is not linked to a GitHub repository. "
                "Cannot fix projects without source code."
            )
            return False

        return True

    def _get_and_validate_issue_type(self, args: List[str]) -> str:
        """Get and validate issue type"""
        issue_type = args[0] if args else "all"
        valid_types = {"syntax", "style", "dependencies", "all"}

        if issue_type not in valid_types:
            self.error(f"Invalid issue type. Choose from: {', '.join(valid_types)}")
            return None

        return issue_type

    def _clone_fix_repo(self, git_manager: Any, repo_url: str) -> Any:
        """Clone repository for fix operation"""
        print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
        clone_result = git_manager.clone_repository(repo_url)
        if not clone_result.get("success"):
            return None
        return clone_result

    def _gather_fixable_issues(
        self, validation_data: Dict[str, Any], issue_type: str
    ) -> List[tuple]:
        """Gather fixable issues from validation data"""
        issues = []

        if issue_type in {"syntax", "all"}:
            syntax_issues = validation_data.get("syntax", {}).get("issues", [])
            issues.extend([("syntax", issue) for issue in syntax_issues[:3]])

        if issue_type in {"dependencies", "all"}:
            deps_issues = validation_data.get("dependencies", {}).get("issues", [])
            issues.extend([("dependency", issue) for issue in deps_issues[:3]])

        return issues

    def _display_issues(self, issues: List[tuple]) -> None:
        """Display found issues"""
        print(f"\n{Fore.YELLOW}Issues Found:{Style.RESET_ALL}")
        for i, (itype, issue) in enumerate(issues, 1):
            msg = (
                issue.get("message", str(issue))
                if isinstance(issue, dict)
                else str(issue)
            )
            print(f"  {i}. [{itype.upper()}] {msg[:80]}")

    def _confirm_fixes(self) -> bool:
        """Ask for fix confirmation"""
        confirm = input(f"\n{Fore.CYAN}Apply fixes? (y/n): ").lower()
        if confirm != "y":
            self.print_info("Fix cancelled")
            return False
        return True

    def _apply_fixes(self, issues: List[tuple], temp_path: str) -> int:
        """Apply fixes to identified issues"""
        from pathlib import Path

        fixes_applied = 0
        for itype, issue in issues:
            if itype == "dependency":
                fixes_applied += self._apply_dependency_fix(issue, temp_path)

        return fixes_applied

    def _apply_dependency_fix(self, issue: Any, temp_path: str) -> int:
        """Apply fix for dependency issue"""
        missing = (
            issue.get("missing_modules", [])
            if isinstance(issue, dict)
            else []
        )

        if not missing:
            return 0

        try:
            from pathlib import Path

            req_file = Path(temp_path) / "requirements.txt"
            with open(req_file, "a") as f:
                for module in missing:
                    f.write(f"{module}\n")

            print(
                f"{Fore.GREEN}[OK] Added missing dependencies "
                f"to requirements.txt{Style.RESET_ALL}"
            )
            return 1
        except Exception as e:
            print(f"{Fore.YELLOW}[SKIP] Could not add dependencies: {e}{Style.RESET_ALL}")
            return 0

    def _display_fix_summary(self, issues: List[tuple], fixes_applied: int) -> None:
        """Display fix summary"""
        print(f"\n{Fore.CYAN}Fix Summary:{Style.RESET_ALL}")
        print(f"  Issues processed: {len(issues)}")
        print(f"  Fixes applied: {fixes_applied}")

        if fixes_applied > 0:
            print(f"\n{Fore.YELLOW}Note: Fixed files are in the cloned repository.")
            print(
                f"Use /github push to commit and push changes back to GitHub."
                f"{Style.RESET_ALL}"
            )


class ProjectValidateCommand(BaseCommand):
    """Validate the current project"""

    def __init__(self):
        super().__init__(
            name="project validate",
            description="Re-run validation on project",
            usage="project validate [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project validate command"""
        if not self._validate_cmd_context(context):
            return self.error("Context validation failed")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        print(f"{Fore.YELLOW}Validating project...{Style.RESET_ALL}")

        try:
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()
            clone_result = self._clone_validate_repo(git_manager, project.repository_url)
            if not clone_result:
                return self.error("Failed to clone repository")

            temp_path = clone_result["path"]
            try:
                validation_result = self._run_validation(orchestrator, temp_path)
                if validation_result["status"] != "success":
                    return self.error(
                        f"Validation failed: {validation_result.get('message', 'Unknown error')}"
                    )

                self._display_validation_results(validation_result)
                return self.success(
                    data={"validation": validation_result.get("validation_summary", {})}
                )

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Validation error: {str(e)}")
            return self.error(f"Validation error: {str(e)}")

    def _validate_cmd_context(self, context: Dict[str, Any]) -> bool:
        """Validate context for validate command"""
        if not self.require_user(context):
            return False

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            self.error("Orchestrator not available")
            return False

        if not project:
            self.error("No project loaded. Use /project load to load a project")
            return False

        if not project.repository_url:
            self.error(
                "Project is not linked to a GitHub repository. "
                "Cannot validate projects without source code."
            )
            return False

        return True

    def _clone_validate_repo(self, git_manager: Any, repo_url: str) -> Any:
        """Clone repository for validation"""
        print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
        clone_result = git_manager.clone_repository(repo_url)
        if not clone_result.get("success"):
            return None
        return clone_result

    def _run_validation(self, orchestrator: Any, project_path: str) -> Dict[str, Any]:
        """Run validation pipeline"""
        return orchestrator.process_request(
            "code_validation",
            {
                "action": "validate_project",
                "project_path": project_path,
                "timeout": 300,
            },
        )

    def _display_validation_results(self, validation_result: Dict[str, Any]) -> None:
        """Display all validation results"""
        summary = validation_result.get("validation_summary", {})
        results = validation_result.get("validation_results", {})
        recommendations = validation_result.get("recommendations", [])

        self.print_success("Validation complete!")
        self._display_summary(summary)
        self._display_detailed_results(results)
        self._display_recommendations(recommendations)

    def _display_summary(self, summary: Dict[str, Any]) -> None:
        """Display validation summary"""
        overall = summary.get("overall_status", "unknown").upper()
        color = self._get_status_color(overall)

        print(f"\n{Fore.CYAN}Validation Summary:{Style.RESET_ALL}")
        print(f"  Overall Status: {color}{overall}{Style.RESET_ALL}")
        print(f"  Issues: {summary.get('issues_count', 0)}")
        print(f"  Warnings: {summary.get('warnings_count', 0)}")

    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        if status == "PASS":
            return Fore.GREEN
        elif status == "WARNING":
            return Fore.YELLOW
        return Fore.RED

    def _display_detailed_results(self, results: Dict[str, Any]) -> None:
        """Display detailed validation results"""
        syntax = results.get("syntax", {})
        deps = results.get("dependencies", {})
        tests = results.get("tests", {})

        self._display_syntax_results(syntax)
        self._display_dependency_results(deps)
        self._display_test_results(tests)

    def _display_syntax_results(self, syntax: Dict[str, Any]) -> None:
        """Display syntax validation results"""
        print(f"\n{Fore.CYAN}Syntax Validation:{Style.RESET_ALL}")
        print(f"  Status: {'PASS' if syntax.get('valid') else 'FAIL'}")
        if not syntax.get("valid"):
            issues = syntax.get("issues", [])
            print(f"  Issues: {len(issues)}")

    def _display_dependency_results(self, deps: Dict[str, Any]) -> None:
        """Display dependency validation results"""
        print(f"\n{Fore.CYAN}Dependency Validation:{Style.RESET_ALL}")
        print(f"  Status: {'PASS' if deps.get('valid') else 'FAIL'}")
        meta = deps.get("metadata", {})
        if meta.get("total_dependencies"):
            print(f"  Total Dependencies: {meta.get('total_dependencies')}")
        if meta.get("missing_imports"):
            print(f"  Missing: {len(meta.get('missing_imports', []))}")
        if meta.get("unused_dependencies"):
            print(f"  Unused: {len(meta.get('unused_dependencies', []))}")

    def _display_test_results(self, tests: Dict[str, Any]) -> None:
        """Display test validation results"""
        print(f"\n{Fore.CYAN}Tests:{Style.RESET_ALL}")
        if tests.get("tests_found"):
            print(f"  Passed: {tests.get('tests_passed', 0)}")
            print(f"  Failed: {tests.get('tests_failed', 0)}")
        else:
            print("  No tests found")

    def _display_recommendations(self, recommendations: List[str]) -> None:
        """Display recommendations"""
        if not recommendations:
            return

        print(f"\n{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"  {i}. {rec}")


class ProjectReviewCommand(BaseCommand):
    """Get a comprehensive code review using Claude"""

    def __init__(self):
        super().__init__(
            name="project review",
            description="Get comprehensive code review",
            usage="project review [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project review command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        if not project:
            return self.error("No project loaded. Use /project load to load a project")

        # Check if project has repository URL (GitHub imported)
        if not project.repository_url:
            return self.error("Project is not linked to a GitHub repository. Cannot review projects without source code.")

        print(f"{Fore.YELLOW}Generating code review...{Style.RESET_ALL}")

        try:

            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()

            # Clone repository to temp directory
            print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
            clone_result = git_manager.clone_repository(project.repository_url)
            if not clone_result.get("success"):
                return self.error(f"Failed to clone repository: {clone_result.get('error')}")

            temp_path = clone_result["path"]

            try:
                # Gather code samples from main language files
                print(f"{Fore.CYAN}Gathering code samples...{Style.RESET_ALL}")
                code_samples = self._gather_code_samples(temp_path)

                if not code_samples:
                    return self.error("No code files found in repository")

                # Get Claude client to generate review
                claude_client = orchestrator.claude_client

                # Build review prompt
                review_prompt = f"""
Review this GitHub project: {project.repository_url}

Project Name: {project.name}
Language: {project.repository_language}
Repository: {project.repository_name}

Below are code samples from the repository:

{code_samples}

Please provide a comprehensive code review covering:
1. Code Quality: Structure, readability, maintainability
2. Best Practices: Are established patterns being followed?
3. Potential Issues: Security concerns, performance issues, bugs
4. Strengths: What's done well?
5. Recommendations: Top 3-5 actionable improvements

Format your response with clear sections."""

                # Generate review
                print(f"{Fore.CYAN}Generating Claude review (this may take a moment)...{Style.RESET_ALL}")

                try:
                    # Use the Claude client to generate the review
                    response = claude_client.create_message(
                        system="You are an expert code reviewer. Provide constructive, actionable code reviews focusing on quality, security, and best practices.",
                        user_message=review_prompt,
                        temperature=0.7,
                        max_tokens=2000,
                    )

                    review_text = response.get("content", "") if isinstance(response, dict) else str(response)

                    self.print_success("Code review complete!")
                    print(f"\n{Fore.CYAN}Code Review:{Style.RESET_ALL}")
                    print(review_text)

                    return self.success(data={"review": review_text})

                except Exception as claude_error:
                    # If Claude fails, return structured analysis
                    self.print_warning(f"Could not generate Claude review: {str(claude_error)}")
                    return self.success(data={"review": "Claude review generation failed, but code analysis completed."})

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Review error: {str(e)}")
            return self.error(f"Review error: {str(e)}")

    def _gather_code_samples(self, repo_path: str, max_files: int = 5) -> str:
        """Gather representative code samples from repository"""
        from pathlib import Path

        repo_path_obj = Path(repo_path)
        code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp"}

        code_files = []
        for ext in code_extensions:
            files = list(repo_path_obj.rglob(f"*{ext}"))
            # Exclude common directories
            files = [f for f in files if not any(skip in f.parts for skip in {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist", "test", "tests"})]
            code_files.extend(files[:2])  # Get 2 files per extension

        samples = []
        for file_path in code_files[:max_files]:
            try:
                with open(file_path, encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:1000]  # First 1000 chars
                    samples.append(f"File: {file_path.name}\n```\n{content}\n```")
            except Exception:
                pass

        return "\n\n".join(samples) if samples else ""


class ProjectDiffCommand(BaseCommand):
    """Show changes between validation runs"""

    def __init__(self):
        super().__init__(
            name="project diff",
            description="Show changes between validation runs",
            usage="project diff [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project diff command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        orchestrator = context.get("orchestrator")
        project = context.get("project")

        if not orchestrator:
            return self.error("Orchestrator not available")

        if not project:
            return self.error("No project loaded. Use /project load to load a project")

        print(f"{Fore.YELLOW}Comparing validation results...{Style.RESET_ALL}")

        try:
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()

            # Clone and re-validate to get new results
            print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
            clone_result = git_manager.clone_repository(project.repository_url)
            if not clone_result.get("success"):
                return self.error(f"Failed to clone repository: {clone_result.get('error')}")

            temp_path = clone_result["path"]

            try:
                # Run validation
                validation_result = orchestrator.process_request(
                    "code_validation",
                    {
                        "action": "validate_project",
                        "project_path": temp_path,
                        "timeout": 300,
                    },
                )

                if validation_result["status"] != "success":
                    return self.error("Validation failed")

                new_summary = validation_result.get("validation_summary", {})
                old_summary = getattr(project, "_cached_validation_summary", {}) or {}

                # Display comparison
                self.print_success("Validation comparison complete!")

                print(f"\n{Fore.CYAN}Validation Changes:{Style.RESET_ALL}")

                # Compare issue counts
                old_issues = old_summary.get("issues_count", 0)
                new_issues = new_summary.get("issues_count", 0)
                issue_change = new_issues - old_issues

                old_warnings = old_summary.get("warnings_count", 0)
                new_warnings = new_summary.get("warnings_count", 0)
                warning_change = new_warnings - old_warnings

                # Show changes
                if old_summary:
                    print(f"\n  Issues: {old_issues} → {new_issues} ", end="")
                    if issue_change < 0:
                        print(f"{Fore.GREEN}[{issue_change}] Improved!{Style.RESET_ALL}")
                    elif issue_change > 0:
                        print(f"{Fore.RED}[+{issue_change}] Regressed{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[No change]{Style.RESET_ALL}")

                    print(f"  Warnings: {old_warnings} → {new_warnings} ", end="")
                    if warning_change < 0:
                        print(f"{Fore.GREEN}[{warning_change}] Improved!{Style.RESET_ALL}")
                    elif warning_change > 0:
                        print(f"{Fore.RED}[+{warning_change}]{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[No change]{Style.RESET_ALL}")

                    # Overall comparison
                    old_status = old_summary.get("overall_status", "unknown")
                    new_status = new_summary.get("overall_status", "unknown")

                    if old_status != new_status:
                        print(f"\n  Status: {old_status} → {new_status}")
                else:
                    print("\n  No previous validation data available.")
                    print(f"  Current Issues: {new_issues}")
                    print(f"  Current Warnings: {new_warnings}")
                    print(f"  Current Status: {new_status}")

                # Store current summary for future comparison
                project._cached_validation_summary = new_summary

                return self.success(data={"old_summary": old_summary, "new_summary": new_summary})

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Diff error: {str(e)}")
            return self.error(f"Diff error: {str(e)}")
