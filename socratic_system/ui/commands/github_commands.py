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

        github_url = self._get_github_url(args)
        if not github_url:
            return self.error("GitHub URL cannot be empty")

        project_name = self._get_project_name(args)

        if not self._validate_import_context(context):
            return self.error("Required context not available")

        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")

        print(f"{Fore.YELLOW}Importing from GitHub...{Style.RESET_ALL}")

        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_from_github",
                "github_url": github_url,
                "project_name": project_name,
                "owner": user.username,
            },
        )

        if result["status"] != "success":
            return self.error(result.get("message", "Failed to import repository"))

        project = result["project"]
        app.current_project = project
        app.context_display.set_context(project=project)

        self.print_success(f"Repository imported as project '{project.name}'!")
        self._show_import_metadata(result)
        self._show_import_validation(result)
        self._print_import_next_steps()

        return self.success(data={"project": project})

    def _get_github_url(self, args: List[str]) -> str:
        """Get GitHub URL from args or user input"""
        if self.validate_args(args, min_count=1):
            return args[0]
        return input(f"{Fore.WHITE}GitHub repository URL: ").strip()

    def _get_project_name(self, args: List[str]) -> str:
        """Get project name from args or user input"""
        if len(args) > 1:
            return " ".join(args[1:])

        custom_name = input(
            f"{Fore.CYAN}Project name (optional, press Enter to use repo name): "
        ).strip()
        return custom_name if custom_name else None

    def _validate_import_context(self, context: Dict[str, Any]) -> bool:
        """Validate required context for import"""
        orchestrator = context.get("orchestrator")
        app = context.get("app")
        user = context.get("user")
        return bool(orchestrator and app and user)

    def _show_import_metadata(self, result: Dict[str, Any]) -> None:
        """Display repository metadata"""
        metadata = result.get("metadata", {})
        if not metadata:
            return

        print(f"\n{Fore.CYAN}Repository Information:{Style.RESET_ALL}")
        if metadata.get("language"):
            print(f"  Language: {metadata.get('language')}")
        if metadata.get("file_count"):
            print(f"  Files: {metadata.get('file_count')}")
        if metadata.get("has_tests"):
            print("  Tests: Yes")
        if metadata.get("description"):
            print(f"  Description: {metadata.get('description')[:80]}...")

    def _show_import_validation(self, result: Dict[str, Any]) -> None:
        """Display validation results"""
        validation = result.get("validation_results", {})
        if not validation:
            return

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

    def _print_import_next_steps(self) -> None:
        """Print next steps after import"""
        print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print("  • Use /project analyze to examine the code")
        print("  • Use /project test to run tests")
        print("  • Use /project fix to apply automated fixes")
        print("  • Use /github pull to fetch latest changes")


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
        if not self._validate_pull_context(context):
            return self._context_error()

        project = context.get("project")
        orchestrator = context.get("orchestrator")

        print(f"{Fore.YELLOW}Pulling latest changes from GitHub...{Style.RESET_ALL}")

        try:
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()
            clone_result = self._clone_repository(git_manager, project.repository_url)
            if not clone_result:
                return self.error(f"Failed to clone repository")

            temp_path = clone_result["path"]
            try:
                return self._handle_pull_workflow(git_manager, temp_path, project, orchestrator)
            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Pull error: {str(e)}")
            return self.error(f"Pull error: {str(e)}")

    def _validate_pull_context(self, context: Dict[str, Any]) -> bool:
        """Validate context for pull operation"""
        if not self.require_user(context):
            return False

        app = context.get("app")
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not app or not project:
            self.error("No project loaded. Use /project load to load a project")
            return False

        if not project.repository_url:
            self.error("Current project is not linked to a GitHub repository")
            return False

        if not orchestrator:
            self.error("Orchestrator not available")
            return False

        return True

    def _context_error(self) -> Dict[str, Any]:
        """Return context validation error"""
        return self.error("Context validation failed")

    def _clone_repository(self, git_manager: Any, repo_url: str) -> Any:
        """Clone repository to temp directory"""
        print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
        clone_result = git_manager.clone_repository(repo_url)
        if not clone_result.get("success"):
            return None
        return clone_result

    def _handle_pull_workflow(
        self, git_manager: Any, temp_path: str, project: Any, orchestrator: Any
    ) -> Dict[str, Any]:
        """Handle complete pull workflow"""
        print(f"{Fore.CYAN}Pulling updates...{Style.RESET_ALL}")
        pull_result = git_manager.pull_repository(temp_path)

        if pull_result["status"] != "success":
            return self.error(f"Pull failed: {pull_result.get('message', 'Unknown error')}")

        self.print_success("Successfully pulled latest changes!")
        self._show_pull_output(pull_result)
        self._sync_file_changes(temp_path, project, orchestrator)
        self._show_git_diff(git_manager, temp_path)

        print(f"\n{Fore.GREEN}[OK] Pull completed successfully{Style.RESET_ALL}")
        return self.success(data={"pull_result": pull_result})

    def _show_pull_output(self, pull_result: Dict[str, Any]) -> None:
        """Show pull command output"""
        if pull_result.get("message"):
            print(f"\n{Fore.CYAN}Pull Output:{Style.RESET_ALL}")
            print(pull_result["message"][:500])

    def _sync_file_changes(self, temp_path: str, project: Any, orchestrator: Any) -> None:
        """Detect and sync file changes"""
        print(f"\n{Fore.CYAN}Detecting file changes...{Style.RESET_ALL}")
        try:
            from pathlib import Path

            from socratic_system.database.project_file_manager import ProjectFileManager
            from socratic_system.utils.file_change_tracker import FileChangeTracker

            current_files = self._read_cloned_files(temp_path)
            file_manager = ProjectFileManager(orchestrator.database.db_path)
            stored_files = file_manager.get_project_files(
                project.project_id, limit=1000
            )

            tracker = FileChangeTracker()
            sync_result = tracker.sync_changes(
                project.project_id,
                current_files,
                stored_files,
                orchestrator=orchestrator,
                database=orchestrator.database,
            )

            self._show_change_summary(sync_result)

        except Exception as e:
            self.logger.warning(f"Error syncing file changes: {str(e)}")
            print(f"{Fore.YELLOW}Warning: Could not sync file changes: {str(e)}{Style.RESET_ALL}")

    def _read_cloned_files(self, temp_path: str) -> List[Dict[str, Any]]:
        """Read all files from cloned repository"""
        from pathlib import Path

        current_files = []
        for file_path in Path(temp_path).rglob("*"):
            if file_path.is_file() and self._should_save_file(file_path, temp_path):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    language = self._detect_language(str(file_path))
                    rel_path = file_path.relative_to(temp_path).as_posix()

                    current_files.append(
                        {
                            "file_path": rel_path,
                            "content": content,
                            "language": language,
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Could not read file {file_path}: {str(e)}")

        return current_files

    def _show_change_summary(self, sync_result: Dict[str, Any]) -> None:
        """Show summary of file changes"""
        if sync_result["status"] != "success":
            return

        summary = sync_result["summary"]
        added_count = len(summary.get("added", []))
        modified_count = len(summary.get("modified", []))
        deleted_count = len(summary.get("deleted", []))

        if added_count + modified_count + deleted_count > 0:
            print(f"\n{Fore.CYAN}Files Updated:{Style.RESET_ALL}")
            if added_count > 0:
                print(f"  {Fore.GREEN}+{added_count} added{Style.RESET_ALL}")
            if modified_count > 0:
                print(f"  {Fore.YELLOW}~{modified_count} modified{Style.RESET_ALL}")
            if deleted_count > 0:
                print(f"  {Fore.RED}-{deleted_count} deleted{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}No file changes detected{Style.RESET_ALL}")

    def _show_git_diff(self, git_manager: Any, temp_path: str) -> None:
        """Show git diff summary"""
        print(f"\n{Fore.CYAN}Git Diff Summary:{Style.RESET_ALL}")
        diff = git_manager.get_git_diff(temp_path)
        if diff and diff != "No differences":
            lines = diff.split("\n")[:20]
            for line in lines:
                print(line[:100])
            if len(diff.split("\n")) > 20:
                print(f"{Fore.YELLOW}... (use 'git diff' for full details){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No git diff changes{Style.RESET_ALL}")

    def _should_save_file(self, file_path, repo_root: str) -> bool:
        """Filter out binaries, large files, and generated code"""

        SKIP_EXTENSIONS = {
            ".pyc",
            ".pyo",
            ".so",
            ".exe",
            ".dll",
            ".bin",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".ico",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".zip",
            ".tar",
            ".gz",
            ".7z",
            ".rar",
        }

        SKIP_DIRS = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            ".env",
            "dist",
            "build",
            ".egg-info",
            ".pytest_cache",
            ".tox",
            ".coverage",
            "htmlcov",
        }

        for part in file_path.parts:
            if part in SKIP_DIRS:
                return False

        if file_path.suffix.lower() in SKIP_EXTENSIONS:
            return False

        try:
            size = file_path.stat().st_size
            if size > 5 * 1024 * 1024:  # 5MB limit
                return False
        except Exception:
            return False

        return True

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        from pathlib import Path

        ext_to_lang = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JSX",
            ".tsx": "TSX",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".sh": "Shell",
            ".bash": "Bash",
            ".sql": "SQL",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".less": "Less",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".xml": "XML",
            ".md": "Markdown",
            ".rst": "ReStructuredText",
            ".txt": "Text",
            ".toml": "TOML",
            ".ini": "INI",
            ".cfg": "Config",
        }

        file_ext = Path(file_path).suffix.lower()
        return ext_to_lang.get(file_ext, "Unknown")


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
        if not self._validate_push_context(context):
            return self.error("Context validation failed")

        project = context.get("project")
        commit_message = self._get_commit_message(args, project)

        print(f"{Fore.YELLOW}Pushing changes to GitHub...{Style.RESET_ALL}")

        try:
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            git_manager = GitRepositoryManager()
            clone_result = self._clone_push_repo(git_manager, project.repository_url)
            if not clone_result:
                return self.error("Failed to clone repository")

            temp_path = clone_result["path"]
            try:
                return self._handle_push_workflow(git_manager, temp_path, commit_message)
            finally:
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.print_error(f"Push error: {str(e)}")
            return self.error(f"Push error: {str(e)}")

    def _validate_push_context(self, context: Dict[str, Any]) -> bool:
        """Validate context for push operation"""
        if not self.require_user(context):
            return False

        app = context.get("app")
        project = context.get("project")
        orchestrator = context.get("orchestrator")

        if not app or not project:
            self.error("No project loaded. Use /project load to load a project")
            return False

        if not project.repository_url:
            self.error("Current project is not linked to a GitHub repository")
            return False

        if not orchestrator:
            self.error("Orchestrator not available")
            return False

        return True

    def _get_commit_message(self, args: List[str], project: Any) -> str:
        """Get commit message from args or user input"""
        if len(args) > 0:
            return " ".join(args)

        commit_message = input(
            f"{Fore.WHITE}Commit message (or press Enter for default): "
        ).strip()
        return commit_message if commit_message else f"Updates from Socratic RAG - {project.name}"

    def _clone_push_repo(self, git_manager: Any, repo_url: str) -> Any:
        """Clone repository for push operation"""
        print(f"{Fore.CYAN}Cloning repository...{Style.RESET_ALL}")
        clone_result = git_manager.clone_repository(repo_url)
        if not clone_result.get("success"):
            return None
        return clone_result

    def _handle_push_workflow(
        self, git_manager: Any, temp_path: str, commit_message: str
    ) -> Dict[str, Any]:
        """Handle complete push workflow"""
        if not self._show_push_diff(git_manager, temp_path):
            return self.success(data={"message": "No changes to push"})

        if not self._confirm_push(commit_message):
            return self.success(data={"message": "Push cancelled by user"})

        print(f"{Fore.CYAN}Pushing to GitHub...{Style.RESET_ALL}")
        push_result = git_manager.push_repository(temp_path, commit_message)

        return self._handle_push_result(push_result)

    def _show_push_diff(self, git_manager: Any, temp_path: str) -> bool:
        """Show diff and return whether there are changes"""
        print(f"\n{Fore.CYAN}Changes to push:{Style.RESET_ALL}")
        diff = git_manager.get_git_diff(temp_path)
        if not diff or diff == "No differences":
            print(f"{Fore.YELLOW}No changes to push{Style.RESET_ALL}")
            return False

        lines = diff.split("\n")[:30]
        for line in lines:
            if line.startswith("+"):
                print(f"{Fore.GREEN}{line[:100]}{Style.RESET_ALL}")
            elif line.startswith("-"):
                print(f"{Fore.RED}{line[:100]}{Style.RESET_ALL}")
            else:
                print(line[:100])

        if len(diff.split("\n")) > 30:
            more_lines = len(diff.split(chr(10))) - 30
            print(f"{Fore.YELLOW}... ({more_lines} more lines){Style.RESET_ALL}")

        return True

    def _confirm_push(self, commit_message: str) -> bool:
        """Get push confirmation from user"""
        print(f"\n{Fore.WHITE}Commit message: {Fore.CYAN}{commit_message}{Style.RESET_ALL}")
        confirm = input(f"{Fore.WHITE}Proceed with push? (yes/no): ").strip().lower()
        if confirm != "yes":
            print(f"{Fore.YELLOW}Push cancelled{Style.RESET_ALL}")
            return False
        return True

    def _handle_push_result(self, push_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push result and return appropriate response"""
        if push_result.get("status") == "success":
            self.print_success("Successfully pushed changes to GitHub!")
            if push_result.get("message"):
                print(f"\n{Fore.CYAN}Push Output:{Style.RESET_ALL}")
                print(push_result["message"][:500])

            print(f"\n{Fore.GREEN}[OK] Push completed successfully{Style.RESET_ALL}")
            return self.success(data={"push_result": push_result})

        error_msg = push_result.get("message", "Unknown error")
        if "auth" in error_msg.lower() or "permission" in error_msg.lower():
            return self.error(
                f"Authentication failed: {error_msg}\n"
                "Make sure GITHUB_TOKEN environment variable is set with proper permissions"
            )
        return self.error(f"Push failed: {error_msg}")


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
            print("  • Pulled latest changes from GitHub")
            print("  • Pushed local changes to GitHub")
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
