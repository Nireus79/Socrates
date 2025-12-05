"""
Project management agent for Socratic RAG System
"""

import datetime
import uuid
from typing import Any, Dict

from socratic_system.models import ProjectContext

from .base import Agent


class ProjectManagerAgent(Agent):
    """Manages project lifecycle including creation, loading, saving, and collaboration"""

    def __init__(self, orchestrator):
        super().__init__("ProjectManager", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process project management requests"""
        action = request.get("action")

        action_handlers = {
            "create_project": self._create_project,
            "load_project": self._load_project,
            "save_project": self._save_project,
            "add_collaborator": self._add_collaborator,
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
        """Create a new project"""
        project_name = request.get("project_name")
        owner = request.get("owner")

        project_id = str(uuid.uuid4())
        project = ProjectContext(
            project_id=project_id,
            name=project_name,
            owner=owner,
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
        )

        self.orchestrator.database.save_project(project)
        self.log(f"Created project '{project_name}' with ID {project_id}")

        return {"status": "success", "project": project}

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
        """Add a collaborator to a project"""
        project = request.get("project")
        username = request.get("username")

        if username not in project.collaborators:
            project.collaborators.append(username)
            self.orchestrator.database.save_project(project)
            self.log(f"Added collaborator '{username}' to project '{project.name}'")
            return {"status": "success"}
        else:
            return {"status": "error", "message": "User already a collaborator"}

    def _list_projects(self, request: Dict) -> Dict:
        """List projects for a user"""
        username = request.get("username")
        projects = self.orchestrator.database.get_user_projects(username)
        return {"status": "success", "projects": projects}

    def _list_collaborators(self, request: Dict) -> Dict:
        """List all collaborators for a project"""
        project = request.get("project")

        collaborators_info = []
        # Add owner info
        collaborators_info.append({"username": project.owner, "role": "owner"})

        # Add collaborators info
        for collaborator in project.collaborators:
            collaborators_info.append({"username": collaborator, "role": "collaborator"})

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
