"""
Project management agent for Socratic RAG System
"""

import datetime
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from socratic_system.models import VALID_ROLES, ProjectContext, TeamMemberRole

from .base import Agent

if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator


class ProjectManagerAgent(Agent):
    """Manages project lifecycle including creation, loading, saving, and collaboration"""

    def __init__(self, orchestrator: "AgentOrchestrator") -> None:
        super().__init__("ProjectManager", orchestrator)

    @staticmethod
    def _generate_auto_user_email(username: str) -> str:
        """Generate unique email for auto-created users (no hardcoded domain)"""
        domain_parts = ["socrates", "local"]
        domain = ".".join(domain_parts)
        uuid_suffix = str(uuid.uuid4())[:8]
        return f"{username}+{uuid_suffix}@{domain}"

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process project management requests"""
        action = request.get("action")

        action_handlers = {
            "create_project": self._create_project,
            "create_from_github": self._create_from_github,
            "load_project": self._load_project,
            "save_project": self._save_project,
            "add_collaborator": self._add_collaborator,
            "update_member_role": self._update_member_role,
            "list_projects": self._list_projects,
            "list_collaborators": self._list_collaborators,
            "remove_collaborator": self._remove_collaborator,
            "archive_project": self._archive_project,
            "restore_project": self._restore_project,
            "delete_project_permanently": self._delete_project_permanently,
            "get_archived_projects": self._get_archived_projects,
        }

        handler = action_handlers.get(action)
        if handler:
            return handler(request)

        return {"status": "error", "message": "Unknown action"}

    def _create_project(self, request: Dict) -> Dict:
        """Create a new project with quota checking"""
        project_name = request.get("project_name")
        owner = request.get("owner")
        project_type = request.get("project_type", "software")  # Default to software
        description = request.get("description", "")  # Optional description

        # Validate required fields
        if not project_name:
            return {
                "status": "error",
                "message": "project_name is required to create a project",
            }
        if not owner:
            return {
                "status": "error",
                "message": "owner is required to create a project",
            }

        # NEW: Check project limit
        from socratic_system.subscription.checker import SubscriptionChecker

        user = self.orchestrator.database.load_user(owner)

        # Create user if they don't exist (for automation/testing)
        if user is None:
            from socratic_system.models.user import User

            # Generate unique email for auto-created user
            unique_email = self._generate_auto_user_email(owner)

            user = User(
                username=owner,
                email=unique_email,  # UUID-based email for system-created users
                passcode_hash="",  # Empty hash - will need password reset to use UI
                created_at=datetime.datetime.now(),
                projects=[],
                subscription_tier="pro",  # Default to pro tier for auto-created users
            )
            self.orchestrator.database.save_user(user)

        active_projects = self.orchestrator.database.get_user_projects(owner)
        active_count = len([p for p in active_projects if p.status != "archived"])

        can_create, error_message = SubscriptionChecker.check_project_limit(user, active_count)
        if not can_create:
            return {
                "status": "error",
                "message": error_message,
            }

        project_id = str(uuid.uuid4())
        project = ProjectContext(
            project_id=project_id,
            name=project_name,
            owner=owner,
            description=description,
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            project_type=project_type,
        )

        self.orchestrator.database.save_project(project)
        self.log(f"Created project '{project_name}' (type: {project_type}) with ID {project_id}")

        return {"status": "success", "project": project}

    def _create_from_github(self, request: Dict) -> Dict:
        """Create a new project from a GitHub repository"""
        github_url = request.get("github_url")
        project_name = request.get("project_name")
        owner = request.get("owner")

        # Validate required fields
        if not github_url:
            return {
                "status": "error",
                "message": "github_url is required",
            }
        if not owner:
            return {
                "status": "error",
                "message": "owner is required",
            }

        try:
            # Import GitRepositoryManager
            from socratic_system.utils.git_repository_manager import GitRepositoryManager

            # Validate GitHub URL
            git_manager = GitRepositoryManager()
            is_valid, error_msg = git_manager.validate_github_url(github_url)
            if not is_valid:
                return {
                    "status": "error",
                    "message": f"Invalid GitHub URL: {error_msg}",
                }

            self.log(f"Starting GitHub import for {github_url}")

            # Clone repository to temp directory
            clone_result = git_manager.clone_repository(github_url)
            if not clone_result.get("success"):
                return {
                    "status": "error",
                    "message": f"Failed to clone repository: {clone_result.get('error', 'Unknown error')}",
                }

            temp_path = clone_result["path"]

            try:
                # Extract metadata
                self.log("Extracting repository metadata...")
                metadata = git_manager.extract_repository_metadata(temp_path)

                # Extract owner/repo from URL
                url_parts = git_manager.validate_github_url(github_url)
                repo_owner, repo_name = github_url.strip("/").split("/")[-2:]

                # Use provided project name or repo name
                final_project_name = project_name or repo_name

                # Check project limit
                from socratic_system.subscription.checker import SubscriptionChecker

                user = self.orchestrator.database.load_user(owner)

                # Create user if they don't exist
                if user is None:
                    from socratic_system.models.user import User

                    user = User(
                        username=owner,
                        email=self._generate_auto_user_email(owner),  # Auto-generated email for system-created users
                        passcode_hash="",
                        created_at=datetime.datetime.now(),
                        projects=[],
                        subscription_tier="pro",
                    )
                    self.orchestrator.database.save_user(user)

                active_projects = self.orchestrator.database.get_user_projects(owner)
                active_count = len([p for p in active_projects if p.status != "archived"])

                can_create, error_message = SubscriptionChecker.check_project_limit(user, active_count)
                if not can_create:
                    return {
                        "status": "error",
                        "message": error_message,
                    }

                # Run code validation
                self.log("Running code validation...")
                validation_result = self.orchestrator.process_request(
                    "code_validation",
                    {
                        "action": "validate_project",
                        "project_path": temp_path,
                        "timeout": 300,
                    },
                )

                # Create project with repository metadata
                project_id = str(uuid.uuid4())
                project = ProjectContext(
                    project_id=project_id,
                    name=final_project_name,
                    owner=owner,
                    collaborators=[],
                    goals=metadata.get("description", ""),
                    requirements=[],
                    tech_stack=metadata.get("languages", []),
                    constraints=[],
                    team_structure="individual",
                    language_preferences="python",
                    deployment_target="local",
                    code_style="documented",
                    phase="imported",
                    conversation_history=[],
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                    project_type="github_import",
                    # Repository fields
                    repository_url=github_url,
                    repository_owner=repo_owner,
                    repository_name=repo_name,
                    repository_description=metadata.get("description", ""),
                    repository_language=metadata.get("language", "unknown"),
                    repository_imported_at=datetime.datetime.now(),
                    repository_file_count=metadata.get("file_count", 0),
                    repository_has_tests=metadata.get("has_tests", False),
                )

                # Save project to database
                self.orchestrator.database.save_project(project)

                self.log(f"Created project '{final_project_name}' from GitHub repository")

                # NEW: Save project files to database before cleanup
                self.log("Saving project files to database...")
                try:
                    from socratic_system.database.project_file_manager import ProjectFileManager

                    file_manager = ProjectFileManager(self.orchestrator.database.db_path)

                    # Collect files to save
                    files_to_save = []
                    for file_path in Path(temp_path).rglob("*"):
                        if file_path.is_file() and self._should_save_file(file_path, temp_path):
                            try:
                                content = file_path.read_text(encoding="utf-8", errors="ignore")
                                language = self._detect_language(str(file_path))

                                rel_path = file_path.relative_to(temp_path).as_posix()
                                files_to_save.append(
                                    {
                                        "path": rel_path,
                                        "content": content,
                                        "language": language,
                                        "size": len(content.encode("utf-8")),
                                    }
                                )
                            except Exception as e:
                                self.log(
                                    f"Warning: Could not read file {file_path}: {str(e)}",
                                    level="WARNING",
                                )
                                continue

                    # Save files in batch
                    if files_to_save:
                        files_saved, save_msg = file_manager.save_files_batch(
                            project_id, files_to_save
                        )
                        self.log(save_msg)
                    else:
                        self.log("No files to save (all filtered out)")

                except Exception as e:
                    self.log(
                        f"Warning: Failed to save project files: {str(e)}", level="WARNING"
                    )
                    # Don't fail the import if file saving fails

                return {
                    "status": "success",
                    "project": project,
                    "validation_results": validation_result.get("validation_summary", {}),
                    "metadata": metadata,
                    "files_saved": len(files_to_save) if "files_to_save" in locals() else 0,
                }

            finally:
                # Clean up temp directory
                git_manager.cleanup(temp_path)

        except Exception as e:
            self.log(f"ERROR: Failed to import GitHub repository: {str(e)}", level="ERROR")
            return {
                "status": "error",
                "message": f"Failed to import GitHub repository: {str(e)}",
            }

    def _load_project(self, request: Dict) -> Dict:
        """Load a project by ID"""
        project_id = request.get("project_id")
        project = self.orchestrator.database.load_project(project_id)

        if project:
            self.log(f"Loaded project '{project.name}'")
            return {"status": "success", "project": project}
        else:
            return {"status": "error", "message": "Project not found"}

    def _save_project(self, request: Dict) -> Dict:
        """Save a project"""
        project = request.get("project")
        project.updated_at = datetime.datetime.now()
        self.orchestrator.database.save_project(project)
        self.log(f"Saved project '{project.name}'")
        return {"status": "success"}

    def _add_collaborator(self, request: Dict) -> Dict:
        """Add a collaborator to a project with team size checking"""
        project = request.get("project")
        username = request.get("username")
        role = request.get("role", "creator")  # Default to creator role

        # Validate role
        if role not in VALID_ROLES:
            return {
                "status": "error",
                "message": f"Invalid role: {role}. Valid roles: {', '.join(VALID_ROLES)}",
            }

        # NEW: Check team member limit
        from socratic_system.subscription.checker import SubscriptionChecker

        user = self.orchestrator.database.load_user(project.owner)
        current_team_size = len(project.team_members or [])

        can_add, error_message = SubscriptionChecker.check_team_member_limit(
            user, current_team_size
        )
        if not can_add:
            return {
                "status": "error",
                "message": error_message,
            }

        # Check if user already in team_members
        for member in project.team_members or []:
            if member.username == username:
                return {"status": "error", "message": "User already a team member"}

        # Create new team member
        new_member = TeamMemberRole(
            username=username, role=role, skills=[], joined_at=datetime.datetime.now()
        )

        # Add to team_members
        if project.team_members is None:
            project.team_members = []
        project.team_members.append(new_member)

        # Update deprecated collaborators list for backward compatibility
        if project.collaborators is None:
            project.collaborators = []
        if username not in project.collaborators:
            project.collaborators.append(username)

        self.orchestrator.database.save_project(project)
        self.log(f"Added '{username}' as {role} to project '{project.name}'")

        return {
            "status": "success",
            "message": f"Added {username} as {role}",
            "member": new_member.to_dict(),
        }

    def _update_member_role(self, request: Dict) -> Dict:
        """Update a team member's role"""
        project = request.get("project")
        username = request.get("username")
        new_role = request.get("role")

        # Validate role
        if new_role not in VALID_ROLES:
            return {
                "status": "error",
                "message": f"Invalid role: {new_role}. Valid roles: {', '.join(VALID_ROLES)}",
            }

        # Find and update member
        member_found = False
        old_role = None
        for member in project.team_members or []:
            if member.username == username:
                old_role = member.role
                member.role = new_role
                member_found = True
                break

        if not member_found:
            return {"status": "error", "message": f"User {username} not in project"}

        self.orchestrator.database.save_project(project)
        self.log(
            f"Updated {username} role from {old_role} to {new_role} in project '{project.name}'"
        )

        return {
            "status": "success",
            "message": f"Updated {username} role from {old_role} to {new_role}",
        }

    def _list_projects(self, request: Dict) -> Dict:
        """List projects for a user"""
        username = request.get("username")
        projects = self.orchestrator.database.get_user_projects(username)

        # Convert ProjectContext objects to dictionaries for JSON serialization
        projects_dict = []
        for project in projects:
            projects_dict.append({
                "project_id": project.project_id,
                "name": project.name,
                "owner": project.owner,
                "phase": project.phase,
                "status": project.status,
                "updated_at": project.updated_at.isoformat() if hasattr(project.updated_at, 'isoformat') else str(project.updated_at),
            })

        return {"status": "success", "projects": projects_dict}

    def _list_collaborators(self, request: Dict) -> Dict:
        """List all team members for a project with their roles"""
        project = request.get("project")

        collaborators_info = []

        # Use team_members if available
        if project.team_members:
            for member in project.team_members:
                collaborators_info.append(
                    {
                        "username": member.username,
                        "role": member.role,
                        "joined_at": member.joined_at.isoformat(),
                        "is_owner": member.username == project.owner,
                        "skills": member.skills,
                    }
                )
        else:
            # Fallback to old collaborators list for backward compatibility
            collaborators_info.append({"username": project.owner, "role": "lead", "is_owner": True})
            for collaborator in project.collaborators or []:
                collaborators_info.append(
                    {"username": collaborator, "role": "creator", "is_owner": False}
                )

        return {
            "status": "success",
            "collaborators": collaborators_info,
            "total_count": len(collaborators_info),
        }

    def _remove_collaborator(self, request: Dict) -> Dict:
        """Remove a collaborator from project"""
        project = request.get("project")
        username = request.get("username")
        requester = request.get("requester")

        # Only owner can remove collaborators
        if requester != project.owner:
            return {"status": "error", "message": "Only project owner can remove collaborators"}

        # Cannot remove owner
        if username == project.owner:
            return {"status": "error", "message": "Cannot remove project owner"}

        if username in project.collaborators:
            project.collaborators.remove(username)
            self.orchestrator.database.save_project(project)
            self.log(f"Removed collaborator '{username}' from project '{project.name}'")
            return {"status": "success"}
        else:
            return {"status": "error", "message": "User is not a collaborator"}

    def _archive_project(self, request: Dict) -> Dict:
        """Archive a project"""
        project_id = request.get("project_id")
        requester = request.get("requester")

        # Load project to check ownership
        project = self.orchestrator.database.load_project(project_id)
        if not project:
            return {"status": "error", "message": "Project not found"}

        # Only owner can archive
        if requester != project.owner:
            return {"status": "error", "message": "Only project owner can archive project"}

        success = self.orchestrator.database.archive_project(project_id)
        if success:
            self.log(f"Archived project '{project.name}' (ID: {project_id})")
            return {"status": "success", "message": "Project archived successfully"}
        else:
            return {"status": "error", "message": "Failed to archive project"}

    def _restore_project(self, request: Dict) -> Dict:
        """Restore an archived project"""
        project_id = request.get("project_id")
        requester = request.get("requester")

        # Load project to check ownership
        project = self.orchestrator.database.load_project(project_id)
        if not project:
            return {"status": "error", "message": "Project not found"}

        # Only owner can restore
        if requester != project.owner:
            return {"status": "error", "message": "Only project owner can restore project"}

        success = self.orchestrator.database.restore_project(project_id)
        if success:
            self.log(f"Restored project '{project.name}' (ID: {project_id})")
            return {"status": "success", "message": "Project restored successfully"}
        else:
            return {"status": "error", "message": "Failed to restore project"}

    def _delete_project_permanently(self, request: Dict) -> Dict:
        """Permanently delete a project"""
        project_id = request.get("project_id")
        requester = request.get("requester")
        confirmation = request.get("confirmation", "")

        # Load project to check ownership
        project = self.orchestrator.database.load_project(project_id)
        if not project:
            return {"status": "error", "message": "Project not found"}

        # Only owner can delete
        if requester != project.owner:
            return {"status": "error", "message": "Only project owner can delete project"}

        # Require confirmation
        if confirmation != "DELETE":
            return {
                "status": "error",
                "message": 'Must type "DELETE" to confirm permanent deletion',
            }

        success = self.orchestrator.database.permanently_delete_project(project_id)
        if success:
            self.log(f"PERMANENTLY DELETED project '{project.name}' (ID: {project_id})")
            return {"status": "success", "message": "Project permanently deleted"}
        else:
            return {"status": "error", "message": "Failed to delete project"}

    def _get_archived_projects(self, request: Dict) -> Dict:
        """Get archived projects"""
        archived = self.orchestrator.database.get_archived_items("projects")
        return {"status": "success", "archived_projects": archived}

    def _should_save_file(self, file_path: Path, repo_root: str) -> bool:
        """
        Filter out binaries, large files, and generated code that shouldn't be stored.

        Args:
            file_path: Path object to the file
            repo_root: Root directory of repository

        Returns:
            True if file should be saved, False if it should be skipped
        """
        # Skip certain extensions (binaries, media, archives)
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

        # Skip certain directories
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

        # Check if file is in a skipped directory
        for part in file_path.parts:
            if part in SKIP_DIRS:
                return False

        # Check file extension
        if file_path.suffix.lower() in SKIP_EXTENSIONS:
            return False

        # Check file size (skip files > 5MB)
        try:
            size = file_path.stat().st_size
            if size > 5 * 1024 * 1024:  # 5MB limit
                return False
        except Exception:
            return False

        return True

    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the file as string

        Returns:
            Language name or 'Unknown' if not recognized
        """
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
