"""
File Change Tracker - Detects file changes and updates knowledge base

Handles:
- Comparing current files with stored files
- Identifying added, modified, and deleted files
- Computing content hashes for change detection
- Updating vector DB based on changes
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger("socrates.utils.file_change_tracker")


class FileChangeTracker:
    """Detects file changes and updates knowledge base"""

    def __init__(self):
        """Initialize file change tracker"""
        self.logger = logging.getLogger("socrates.utils.file_change_tracker")

    @staticmethod
    def compute_hash(content: str) -> str:
        """
        Compute MD5 hash of content for change detection

        Args:
            content: File content as string

        Returns:
            MD5 hash of content
        """
        return hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()

    def detect_changes(
        self, project_id: str, current_files: list[dict], stored_files: list[dict]
    ) -> dict[str, list[dict]]:
        """
        Detect changes between current files and stored files

        Args:
            project_id: Project ID
            current_files: List of current files with keys: file_path, content, language
            stored_files: List of stored files with keys: file_path, content, language, id

        Returns:
            Dict with keys: added, modified, deleted, unchanged
        """
        # Create lookup tables
        stored_by_path = {f["file_path"]: f for f in stored_files}
        current_paths = {f["file_path"] for f in current_files}

        added = []
        modified = []
        deleted = []
        unchanged = []

        # Check current files
        for current_file in current_files:
            path = current_file["file_path"]

            if path not in stored_by_path:
                # New file
                added.append(current_file)
            else:
                # Existing file - check if content changed
                stored_file = stored_by_path[path]
                current_hash = self.compute_hash(current_file["content"])
                stored_hash = self.compute_hash(stored_file.get("content", ""))

                if current_hash != stored_hash:
                    modified.append(current_file)
                else:
                    unchanged.append(current_file)

        # Check for deleted files
        for path, stored_file in stored_by_path.items():
            if path not in current_paths:
                deleted.append(stored_file)

        self.logger.info(
            f"Change detection: {len(added)} added, "
            f"{len(modified)} modified, {len(deleted)} deleted, "
            f"{len(unchanged)} unchanged"
        )

        return {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged,
        }

    def update_vector_db(
        self,
        changes: dict[str, list[dict]],
        project_id: str,
        orchestrator: Any = None,
    ) -> dict[str, Any]:
        """Update vector DB based on detected changes"""
        results: dict[str, Any] = {
            "status": "success",
            "deleted": 0,
            "modified": 0,
            "added": 0,
            "total": 0,
        }

        if not orchestrator:
            self.logger.warning("No orchestrator provided, skipping vector DB update")
            return results

        try:
            doc_processor = orchestrator.get_agent("document_processor")
            if not doc_processor:
                self.logger.warning("DocumentProcessor agent not available")
                return results

            results["deleted"] = self._process_deleted_files_vector(changes)
            results["modified"] = self._process_modified_files_vector(
                changes, project_id, doc_processor
            )
            results["added"] = self._process_added_files_vector(changes, project_id, doc_processor)

            results["total"] = results["added"] + results["modified"] + results["deleted"]
            self.logger.info(
                f"Vector DB updated: {results['added']} added, "
                f"{results['modified']} modified, {results['deleted']} deleted"
            )

        except Exception as e:
            self.logger.error(f"Error updating vector DB: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)

        return results

    def _process_deleted_files_vector(self, changes: dict) -> int:
        """Process deleted files in vector DB"""
        count = 0
        for deleted_file in changes.get("deleted", []):
            try:
                count += 1
                self.logger.debug(f"Removed from DB: {deleted_file['file_path']}")
            except Exception as e:
                self.logger.error(
                    f"Error deleting file from DB: {deleted_file['file_path']}: {str(e)}"
                )
        return count

    def _process_modified_files_vector(
        self, changes: dict, project_id: str, doc_processor: Any
    ) -> int:
        """Process modified files in vector DB"""
        count = 0
        for modified_file in changes.get("modified", []):
            try:
                result = doc_processor.process(
                    {
                        "action": "process_code_file",
                        "content": modified_file["content"],
                        "filename": modified_file["file_path"],
                        "language": modified_file.get("language", "Unknown"),
                        "project_id": project_id,
                    }
                )

                if result.get("status") == "success":
                    count += 1
                self.logger.debug(f"Updated in DB: {modified_file['file_path']}")
            except Exception as e:
                self.logger.error(
                    f"Error updating file in DB: {modified_file['file_path']}: {str(e)}"
                )
        return count

    def _process_added_files_vector(
        self, changes: dict, project_id: str, doc_processor: Any
    ) -> int:
        """Process added files in vector DB"""
        count = 0
        for added_file in changes.get("added", []):
            try:
                result = doc_processor.process(
                    {
                        "action": "process_code_file",
                        "content": added_file["content"],
                        "filename": added_file["file_path"],
                        "language": added_file.get("language", "Unknown"),
                        "project_id": project_id,
                    }
                )

                if result.get("status") == "success":
                    count += 1
                self.logger.debug(f"Added to DB: {added_file['file_path']}")
            except Exception as e:
                self.logger.error(f"Error adding file to DB: {added_file['file_path']}: {str(e)}")
        return count

    def update_database(
        self, changes: dict[str, list[dict]], project_id: str, database: Any
    ) -> dict[str, Any]:
        """Update project_files table in database based on changes"""
        results: dict[str, Any] = {"status": "success", "deleted": 0, "modified": 0, "added": 0}

        if not database:
            self.logger.warning("No database provided, skipping database update")
            return results

        try:
            from socratic_system.database.project_file_manager import ProjectFileManager

            file_manager = ProjectFileManager(database.db_path)

            results["deleted"] = self._process_deleted_files_db(changes, project_id, file_manager)
            results["modified"] = self._process_modified_files_db(changes, project_id, file_manager)
            results["added"] = self._process_added_files_db(changes, project_id, file_manager)

            results["total"] = results["added"] + results["modified"] + results["deleted"]
            self.logger.info(
                f"Database updated: {results['added']} added, "
                f"{results['modified']} modified, {results['deleted']} deleted"
            )

        except Exception as e:
            self.logger.error(f"Error updating database: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)

        return results

    def _process_deleted_files_db(self, changes: dict, project_id: str, file_manager: Any) -> int:
        """Process deleted files in database"""
        count = 0
        for deleted_file in changes.get("deleted", []):
            try:
                success, _ = file_manager.delete_file(project_id, deleted_file["file_path"])
                if success:
                    count += 1
                    self.logger.debug(f"Deleted from DB: {deleted_file['file_path']}")
            except Exception as e:
                self.logger.error(f"Error deleting file: {deleted_file['file_path']}: {str(e)}")
        return count

    def _process_modified_files_db(self, changes: dict, project_id: str, file_manager: Any) -> int:
        """Process modified files in database"""
        count = 0
        for modified_file in changes.get("modified", []):
            try:
                success, _ = file_manager.update_file(project_id, modified_file)
                if success:
                    count += 1
                    self.logger.debug(f"Updated in DB: {modified_file['file_path']}")
            except Exception as e:
                self.logger.error(f"Error updating file: {modified_file['file_path']}: {str(e)}")
        return count

    def _process_added_files_db(self, changes: dict, project_id: str, file_manager: Any) -> int:
        """Process added files in database"""
        files_to_add = changes.get("added", [])
        if not files_to_add:
            return 0

        try:
            added_count, _ = file_manager.save_files_batch(project_id, files_to_add)
            self.logger.debug(f"Added {added_count} files to DB")
            return added_count
        except Exception as e:
            self.logger.error(f"Error adding files: {str(e)}")
            return 0

    def sync_changes(
        self,
        project_id: str,
        current_files: list[dict],
        stored_files: list[dict],
        orchestrator: Any = None,
        database: Any = None,
    ) -> dict[str, Any]:
        """
        Sync changes to both database and vector DB

        Args:
            project_id: Project ID
            current_files: Current files list
            stored_files: Stored files list
            orchestrator: Orchestrator instance
            database: Database instance

        Returns:
            Dict with overall sync status
        """
        # Detect changes
        changes = self.detect_changes(project_id, current_files, stored_files)

        # Update database
        db_result = self.update_database(changes, project_id, database)

        # Update vector DB
        vector_result = self.update_vector_db(changes, project_id, orchestrator)

        return {
            "status": "success",
            "changes_detected": changes,
            "database_update": db_result,
            "vector_db_update": vector_result,
            "summary": {
                "added": changes.get("added", []),
                "modified": changes.get("modified", []),
                "deleted": changes.get("deleted", []),
                "unchanged": changes.get("unchanged", []),
            },
        }
