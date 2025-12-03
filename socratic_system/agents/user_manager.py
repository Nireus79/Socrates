"""
User management agent for Socratic RAG System
"""

from typing import Dict, Any

from .base import Agent


class UserManagerAgent(Agent):
    """Manages user accounts, archival, and deletion"""

    def __init__(self, orchestrator):
        super().__init__("UserManager", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process user management requests"""
        action = request.get('action')

        if action == 'archive_user':
            return self._archive_user(request)
        elif action == 'restore_user':
            return self._restore_user(request)
        elif action == 'delete_user_permanently':
            return self._delete_user_permanently(request)
        elif action == 'get_archived_users':
            return self._get_archived_users(request)

        return {'status': 'error', 'message': 'Unknown action'}

    def _archive_user(self, request: Dict) -> Dict:
        """Archive a user account"""
        username = request.get('username')
        requester = request.get('requester')
        archive_projects = request.get('archive_projects', True)

        # Users can only archive themselves
        if requester != username:
            return {'status': 'error', 'message': 'Users can only archive their own accounts'}

        success = self.orchestrator.database.archive_user(username, archive_projects)
        if success:
            self.log(f"Archived user '{username}'")
            return {'status': 'success', 'message': 'Account archived successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to archive account'}

    def _restore_user(self, request: Dict) -> Dict:
        """Restore an archived user account"""
        username = request.get('username')

        success = self.orchestrator.database.restore_user(username)
        if success:
            self.log(f"Restored user '{username}'")
            return {'status': 'success', 'message': 'Account restored successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to restore account or account not archived'}

    def _delete_user_permanently(self, request: Dict) -> Dict:
        """Permanently delete a user account"""
        username = request.get('username')
        requester = request.get('requester')
        confirmation = request.get('confirmation', '')

        # Users can only delete themselves
        if requester != username:
            return {'status': 'error', 'message': 'Users can only delete their own accounts'}

        # Require confirmation
        if confirmation != 'DELETE':
            return {'status': 'error', 'message': 'Must type "DELETE" to confirm permanent deletion'}

        success = self.orchestrator.database.permanently_delete_user(username)
        if success:
            self.log(f"PERMANENTLY DELETED user '{username}'")
            return {'status': 'success', 'message': 'Account permanently deleted'}
        else:
            return {'status': 'error', 'message': 'Failed to delete account'}

    def _get_archived_users(self, request: Dict) -> Dict:
        """Get list of archived users"""
        archived = self.orchestrator.database.get_archived_items('users')
        return {'status': 'success', 'archived_users': archived}
