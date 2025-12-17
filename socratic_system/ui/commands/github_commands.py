"""GitHub integration commands for importing and syncing repositories"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class GithubImportCommand(BaseCommand):
    """Import a GitHub repository as a new project"""

    def __init__(self):
        super().__init__(
            name="github import",
            description="Import a GitHub repository as a new project",
            usage="github import <url> [project-name]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute github import command"""
        if not self.require_user(context):
            return self.error("Must be logged in to import from GitHub")

        if not self.validate_args(args, min_count=1):
            github_url = input(f"{Fore.WHITE}GitHub repository URL: ").strip()
        else:
            github_url = args[0]

        if not github_url:
            return self.error("GitHub URL cannot be empty")

        # Optional: get custom project name
        project_name = None
        if len(args) > 1:
            project_name = " ".join(args[1:])
        else:
            custom_name = input(
                f"{Fore.CYAN}Project name (optional, press Enter to use repo name): "
            ).strip()
            if custom_name:
                project_name = custom_name

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        if not orchestrator or not app or not user:
            return self.error("Required context not available")

        print(f"{Fore.YELLOW}Importing from GitHub...{Style.RESET_ALL}")

        # Call ProjectManager to create from GitHub
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_from_github",
                "github_url": github_url,
                "project_name": project_name,
                "owner": user.username,
            },
        )

        if result["status"] == "success":
            project = result["project"]
            app.current_project = project
            app.context_display.set_context(project=project)

            self.print_success(f"Repository imported as project '{project.name}'!")

            # Display repository information
            metadata = result.get("metadata", {})
            if metadata:
                print(f"\n{Fore.CYAN}Repository Information:{Style.RESET_ALL}")
                if metadata.get("language"):
                    print(f"  Language: {metadata.get('language')}")
                if metadata.get("file_count"):
                    print(f"  Files: {metadata.get('file_count')}")
                if metadata.get("has_tests"):
                    print(f"  Tests: Yes")
                if metadata.get("description"):
                    print(f"  Description: {metadata.get('description')[:80]}...")

            # Display validation results
            validation = result.get("validation_results", {})
            if validation:
                print(f"\n{Fore.CYAN}Code Validation:{Style.RESET_ALL}")
                status = validation.get("overall_status", "unknown").upper()
                if status == "PASS":
                    print(f"  Overall Status: {Fore.GREEN}{status}{Style.RESET_ALL}")
                elif status == "WARNING":
                    print(f"  Overall Status: {Fore.YELLOW}{status}{Style.RESET_ALL}")
                else:
                    print(f"  Overall Status: {Fore.RED}{status}{Style.RESET_ALL}")

                if validation.get("issues_count"):
                    print(f"  Issues: {validation.get('issues_count')}")
                if validation.get("warnings_count"):
                    print(f"  Warnings: {validation.get('warnings_count')}")

            print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
            print("  • Use /project analyze to examine the code")
            print("  • Use /project test to run tests")
            print("  • Use /project fix to apply automated fixes")
            print("  • Use /github pull to fetch latest changes")

            return self.success(data={"project": project})
        else:
            return self.error(result.get("message", "Failed to import repository"))


class GithubPullCommand(BaseCommand):
    """Pull latest changes from GitHub repository"""

    def __init__(self):
        super().__init__(
            name="github pull",
            description="Pull latest changes from GitHub repository",
            usage="github pull [project-id]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute github pull command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        app = context.get("app")
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not app or not project:
            return self.error("No project loaded. Use /project load to load a project")

        if not project.repository_url:
            return self.error("Current project is not linked to a GitHub repository")

        if not orchestrator:
            return self.error("Orchestrator not available")

        print(f"{Fore.YELLOW}Pulling latest changes from GitHub...{Style.RESET_ALL}")

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
                # Pull latest changes
                print(f"{Fore.CYAN}Pulling updates...{Style.RESET_ALL}")
                pull_result = git_manager.pull_repository(temp_path)

                if pull_result["status"] == "success":
                    self.print_success("Successfully pulled latest changes!")

                    # Show pull output
                    if pull_result.get("message"):
                        print(f"\n{Fore.CYAN}Pull Output:{Style.RESET_ALL}")
                        print(pull_result["message"][:500])  # Show first 500 chars

                    # Get diff to show what changed
                    print(f"\n{Fore.CYAN}Changes Summary:{Style.RESET_ALL}")
                    diff = git_manager.get_git_diff(temp_path)
                    if diff and diff != "No differences":
                        lines = diff.split("\n")[:20]  # Show first 20 lines
                        for line in lines:
                            print(line[:100])  # Limit line length
                        if len(diff.split("\n")) > 20:
                            print(f"{Fore.YELLOW}... (use 'git diff' for full details){Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}No changes in working directory{Style.RESET_ALL}")

                    print(f"\n{Fore.GREEN}[OK] Pull completed successfully{Style.RESET_ALL}")
                    return self.success(data={"pull_result": pull_result})
                else:
                    return self.error(f"Pull failed: {pull_result.get('message', 'Unknown error')}")

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Pull error: {str(e)}")
            return self.error(f"Pull error: {str(e)}")


class GithubPushCommand(BaseCommand):
    """Push local changes back to GitHub repository"""

    def __init__(self):
        super().__init__(
            name="github push",
            description="Push local changes back to GitHub repository",
            usage="github push [project-id] [message]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute github push command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        app = context.get("app")
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not app or not project:
            return self.error("No project loaded. Use /project load to load a project")

        if not project.repository_url:
            return self.error("Current project is not linked to a GitHub repository")

        if not orchestrator:
            return self.error("Orchestrator not available")

        # Get commit message
        if len(args) > 0:
            commit_message = " ".join(args)
        else:
            commit_message = input(
                f"{Fore.WHITE}Commit message (or press Enter for default): "
            ).strip()
            if not commit_message:
                commit_message = f"Updates from Socratic RAG - {project.name}"

        print(f"{Fore.YELLOW}Pushing changes to GitHub...{Style.RESET_ALL}")

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
                # Get git diff to show user what will be pushed
                print(f"\n{Fore.CYAN}Changes to push:{Style.RESET_ALL}")
                diff = git_manager.get_git_diff(temp_path)
                if diff and diff != "No differences":
                    lines = diff.split("\n")[:30]  # Show first 30 lines
                    for line in lines:
                        if line.startswith("+"):
                            print(f"{Fore.GREEN}{line[:100]}{Style.RESET_ALL}")
                        elif line.startswith("-"):
                            print(f"{Fore.RED}{line[:100]}{Style.RESET_ALL}")
                        else:
                            print(line[:100])
                    if len(diff.split("\n")) > 30:
                        print(f"{Fore.YELLOW}... ({len(diff.split(chr(10))) - 30} more lines){Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No changes to push{Style.RESET_ALL}")
                    return self.success(data={"message": "No changes to push"})

                # Ask for confirmation
                print(f"\n{Fore.WHITE}Commit message: {Fore.CYAN}{commit_message}{Style.RESET_ALL}")
                confirm = input(
                    f"{Fore.WHITE}Proceed with push? (yes/no): "
                ).strip().lower()

                if confirm != "yes":
                    print(f"{Fore.YELLOW}Push cancelled{Style.RESET_ALL}")
                    return self.success(data={"message": "Push cancelled by user"})

                # Push changes
                print(f"{Fore.CYAN}Pushing to GitHub...{Style.RESET_ALL}")
                push_result = git_manager.push_repository(temp_path, commit_message)

                if push_result.get("status") == "success":
                    self.print_success("Successfully pushed changes to GitHub!")

                    if push_result.get("message"):
                        print(f"\n{Fore.CYAN}Push Output:{Style.RESET_ALL}")
                        print(push_result["message"][:500])

                    print(f"\n{Fore.GREEN}[OK] Push completed successfully{Style.RESET_ALL}")
                    return self.success(data={"push_result": push_result})
                else:
                    error_msg = push_result.get("message", "Unknown error")
                    # Check for authentication errors
                    if "auth" in error_msg.lower() or "permission" in error_msg.lower():
                        return self.error(
                            f"Authentication failed: {error_msg}\n"
                            "Make sure GITHUB_TOKEN environment variable is set with proper permissions"
                        )
                    return self.error(f"Push failed: {error_msg}")

            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Push error: {str(e)}")
            return self.error(f"Push error: {str(e)}")


class GithubSyncCommand(BaseCommand):
    """Sync project with GitHub (pull then push)"""

    def __init__(self):
        super().__init__(
            name="github sync",
            description="Sync project with GitHub (pull updates then push changes)",
            usage="github sync [project-id] [commit-message]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute github sync command"""
        if not self.require_user(context):
            return self.error("Must be logged in")

        app = context.get("app")
        project = context.get("project")

        if not app or not project:
            return self.error("No project loaded. Use /project load to load a project")

        if not project.repository_url:
            return self.error("Current project is not linked to a GitHub repository")

        print(f"{Fore.YELLOW}Syncing with GitHub (pull + push)...{Style.RESET_ALL}")

        # Step 1: Pull latest changes
        print(f"\n{Fore.CYAN}Step 1: Pulling latest changes from GitHub{Style.RESET_ALL}")
        pull_command = GithubPullCommand()
        pull_result = pull_command.execute([], context)

        if pull_result["status"] != "success":
            print(f"{Fore.YELLOW}Pull operation had issues, but continuing...{Style.RESET_ALL}")

        # Step 2: Push changes
        print(f"\n{Fore.CYAN}Step 2: Pushing local changes to GitHub{Style.RESET_ALL}")

        # Pass commit message args to push if provided
        push_args = args if len(args) > 0 else []
        push_command = GithubPushCommand()
        push_result = push_command.execute(push_args, context)

        if push_result["status"] == "success":
            self.print_success("Sync completed successfully!")
            print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
            print(f"  • Pulled latest changes from GitHub")
            print(f"  • Pushed local changes to GitHub")
            return self.success(
                data={
                    "pull_result": pull_result.get("data", {}),
                    "push_result": push_result.get("data", {}),
                }
            )
        else:
            # Pull succeeded, but push failed
            self.print_error("Sync partially failed")
            print(f"{Fore.YELLOW}Pull succeeded, but push encountered an issue:{Style.RESET_ALL}")
            print(f"  {push_result.get('message', 'Unknown error')}")
            return push_result
