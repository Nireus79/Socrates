"""
User management agent for Socrates AI

Phase 2B Migration: Async-first implementation with agent bus support
"""

import asyncio
from typing import Any, Dict

from .base import Agent


class UserManagerAgent(Agent):
    """Manages user accounts, archival, and deletion

    Phase 2B Migration: Async-first CRUD implementation
    - Supports both sync (process) and async (process_async) interfaces
    - Registers with agent bus for discovery
    - All database operations run in thread pool (non-blocking)
    """

    def __init__(self, orchestrator):
        super().__init__("UserManager", orchestrator, auto_register=True)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process user management requests (sync wrapper for backward compatibility)

        Phase 2B: Delegates to sync helper methods
        """
        action = request.get("action")

        if action == "archive_user":
            return self._archive_user_sync(request)
        elif action == "restore_user":
            return self._restore_user_sync(request)
        elif action == "delete_user_permanently":
            return self._delete_user_permanently_sync(request)
        elif action == "get_archived_users":
            return self._get_archived_users_sync(request)

        return {"status": "error", "message": "Unknown action"}

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process user management requests asynchronously (Phase 2B)

        Primary implementation - true async processing with thread pool
        """
        action = request.get("action")

        if action == "archive_user":
            return await self._archive_user_async(request)
        elif action == "restore_user":
            return await self._restore_user_async(request)
        elif action == "delete_user_permanently":
            return await self._delete_user_permanently_async(request)
        elif action == "get_archived_users":
            return await self._get_archived_users_async(request)

        return {"status": "error", "message": "Unknown action"}

    def get_capabilities(self) -> list:
        """Declare agent capabilities for bus discovery (Phase 2B)"""
        return [
            "user_management",
            "account_archival",
            "account_restoration",
            "account_deletion",
            "user_listing",
        ]

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for registration (Phase 2B)"""
        return {
            "version": "2.0",
            "description": "User account management and lifecycle",
            "capabilities_count": 5,
        }

    def _archive_user_sync(self, request: Dict) -> Dict:
        """Archive a user account synchronously (backward compatibility)

        Phase 2B: Legacy sync implementation
        """
        username = request.get("username")
        requester = request.get("requester")
        archive_projects = request.get("archive_projects", True)

        # Users can only archive themselves
        if requester != username:
            return {"status": "error", "message": "Users can only archive their own accounts"}

        success = self.orchestrator.database.archive_user(username, archive_projects)
        if success:
            self.log(f"Archived user '{username}'")
            return {"status": "success", "message": "Account archived successfully"}
        else:
            return {"status": "error", "message": "Failed to archive account"}

    async def _archive_user_async(self, request: Dict) -> Dict:
        """Archive a user account asynchronously (Phase 2B)

        Primary implementation - runs database operation in thread pool
        """
        username = request.get("username")
        requester = request.get("requester")
        archive_projects = request.get("archive_projects", True)

        # Users can only archive themselves
        if requester != username:
            return {"status": "error", "message": "Users can only archive their own accounts"}

        # Run blocking database call in thread pool
        success = await asyncio.to_thread(
            self.orchestrator.database.archive_user,
            username,
            archive_projects
        )

        if success:
            self.log(f"Archived user '{username}'")
            return {"status": "success", "message": "Account archived successfully"}
        else:
            return {"status": "error", "message": "Failed to archive account"}

    def _restore_user_sync(self, request: Dict) -> Dict:
        """Restore an archived user account synchronously (backward compatibility)

        Phase 2B: Legacy sync implementation
        """
        username = request.get("username")

        success = self.orchestrator.database.restore_user(username)
        if success:
            self.log(f"Restored user '{username}'")
            return {"status": "success", "message": "Account restored successfully"}
        else:
            return {
                "status": "error",
                "message": "Failed to restore account or account not archived",
            }

    async def _restore_user_async(self, request: Dict) -> Dict:
        """Restore an archived user account asynchronously (Phase 2B)

        Primary implementation - runs database operation in thread pool
        """
        username = request.get("username")

        # Run blocking database call in thread pool
        success = await asyncio.to_thread(
            self.orchestrator.database.restore_user,
            username
        )

        if success:
            self.log(f"Restored user '{username}'")
            return {"status": "success", "message": "Account restored successfully"}
        else:
            return {
                "status": "error",
                "message": "Failed to restore account or account not archived",
            }

    def _delete_user_permanently_sync(self, request: Dict) -> Dict:
        """Permanently delete a user account synchronously (backward compatibility)

        Phase 2B: Legacy sync implementation
        """
        username = request.get("username")
        requester = request.get("requester")
        confirmation = request.get("confirmation", "")

        # Users can only delete themselves
        if requester != username:
            return {"status": "error", "message": "Users can only delete their own accounts"}

        # Require confirmation
        if confirmation != "DELETE":
            return {
                "status": "error",
                "message": 'Must type "DELETE" to confirm permanent deletion',
            }

        success = self.orchestrator.database.permanently_delete_user(username)
        if success:
            self.log(f"PERMANENTLY DELETED user '{username}'")
            return {"status": "success", "message": "Account permanently deleted"}
        else:
            return {"status": "error", "message": "Failed to delete account"}

    async def _delete_user_permanently_async(self, request: Dict) -> Dict:
        """Permanently delete a user account asynchronously (Phase 2B)

        Primary implementation - runs database operation in thread pool
        """
        username = request.get("username")
        requester = request.get("requester")
        confirmation = request.get("confirmation", "")

        # Users can only delete themselves
        if requester != username:
            return {"status": "error", "message": "Users can only delete their own accounts"}

        # Require confirmation
        if confirmation != "DELETE":
            return {
                "status": "error",
                "message": 'Must type "DELETE" to confirm permanent deletion',
            }

        # Run blocking database call in thread pool
        success = await asyncio.to_thread(
            self.orchestrator.database.permanently_delete_user,
            username
        )

        if success:
            self.log(f"PERMANENTLY DELETED user '{username}'")
            return {"status": "success", "message": "Account permanently deleted"}
        else:
            return {"status": "error", "message": "Failed to delete account"}

    def _get_archived_users_sync(self, request: Dict) -> Dict:
        """Get list of archived users synchronously (backward compatibility)

        Phase 2B: Legacy sync implementation
        """
        archived = self.orchestrator.database.get_archived_items("users")
        return {"status": "success", "archived_users": archived}

    async def _get_archived_users_async(self, request: Dict) -> Dict:
        """Get list of archived users asynchronously (Phase 2B)

        Primary implementation - runs database operation in thread pool
        """
        # Run blocking database call in thread pool
        archived = await asyncio.to_thread(
            self.orchestrator.database.get_archived_items,
            "users"
        )
        return {"status": "success", "archived_users": archived}
