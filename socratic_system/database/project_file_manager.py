"""
Project File Manager - CRUD operations for project_files table

Handles:
- Saving files to project_files table
- Retrieving files from database
- File hashing for change detection
- Batch operations for performance
"""

import hashlib
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("socrates.database.project_files")


class ProjectFileManager:
    """Manages CRUD operations for project files in database"""

    def __init__(self, db_path: str):
        """
        Initialize project file manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger("socrates.database.project_files")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allow accessing columns by name
        return conn

    def save_files_batch(
        self, project_id: str, files: List[Dict[str, str]]
    ) -> Tuple[int, str]:
        """
        Save multiple files in batch (optimized for performance)

        Args:
            project_id: Project ID
            files: List of file dicts with keys:
                - path: Relative file path
                - content: File content
                - language: Programming language (optional)
                - size: File size in bytes (optional)

        Returns:
            Tuple of (files_saved_count: int, message: str)
        """
        if not files:
            return 0, "No files to save"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Prepare data for batch insert
            batch_data = []
            for file_info in files:
                file_path = file_info.get("path") or file_info.get("file_path", "")
                content = file_info.get("content", "")
                language = file_info.get("language")
                file_size = file_info.get("size", len(content.encode("utf-8")))

                batch_data.append(
                    (
                        project_id,
                        file_path,
                        content,
                        language,
                        file_size,
                    )
                )

            # Batch insert with REPLACE (update if exists)
            cursor.executemany(
                """
                INSERT OR REPLACE INTO project_files
                (project_id, file_path, content, language, file_size)
                VALUES (?, ?, ?, ?, ?)
                """,
                batch_data,
            )

            conn.commit()
            files_saved = cursor.rowcount
            conn.close()

            msg = f"Saved {files_saved} files for project {project_id}"
            self.logger.info(msg)
            return files_saved, msg

        except sqlite3.DatabaseError as e:
            msg = f"Database error saving files: {str(e)}"
            self.logger.error(msg)
            return 0, msg

        except Exception as e:
            msg = f"Error saving files batch: {str(e)}"
            self.logger.error(msg)
            return 0, msg

    def get_project_files(
        self, project_id: str, offset: int = 0, limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve paginated list of files for a project

        Args:
            project_id: Project ID
            offset: Number of files to skip
            limit: Maximum number of files to return

        Returns:
            List of file dicts with columns from database
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, project_id, file_path, content, language, file_size,
                       created_at, updated_at
                FROM project_files
                WHERE project_id = ?
                ORDER BY file_path
                LIMIT ? OFFSET ?
                """,
                (project_id, limit, offset),
            )

            files = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return files

        except Exception as e:
            self.logger.error(f"Error retrieving project files: {str(e)}")
            return []

    def get_file_count(self, project_id: str) -> int:
        """
        Get total number of files for a project

        Args:
            project_id: Project ID

        Returns:
            Number of files
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM project_files
                WHERE project_id = ?
                """,
                (project_id,),
            )

            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception as e:
            self.logger.error(f"Error getting file count: {str(e)}")
            return 0

    def get_file_by_path(self, project_id: str, file_path: str) -> Optional[Dict]:
        """
        Retrieve a single file by project and path

        Args:
            project_id: Project ID
            file_path: Relative file path

        Returns:
            File dict or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, project_id, file_path, content, language, file_size,
                       created_at, updated_at
                FROM project_files
                WHERE project_id = ? AND file_path = ?
                """,
                (project_id, file_path),
            )

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Error retrieving file by path: {str(e)}")
            return None

    def update_file(
        self, project_id: str, file_info: Dict[str, str]
    ) -> Tuple[bool, str]:
        """
        Update an existing file

        Args:
            project_id: Project ID
            file_info: File dict with keys:
                - path/file_path: File path
                - content: New file content
                - language: Programming language (optional)

        Returns:
            Tuple of (success: bool, message: str)
        """
        file_path = file_info.get("path") or file_info.get("file_path", "")
        content = file_info.get("content", "")
        language = file_info.get("language")
        file_size = len(content.encode("utf-8"))

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE project_files
                SET content = ?, language = ?, file_size = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ? AND file_path = ?
                """,
                (content, language, file_size, project_id, file_path),
            )

            conn.commit()
            success = cursor.rowcount > 0
            conn.close()

            if success:
                msg = f"Updated file {file_path} in project {project_id}"
                self.logger.info(msg)
                return True, msg
            else:
                msg = f"File not found: {file_path}"
                self.logger.warning(msg)
                return False, msg

        except Exception as e:
            msg = f"Error updating file: {str(e)}"
            self.logger.error(msg)
            return False, msg

    def delete_file(self, project_id: str, file_path: str) -> Tuple[bool, str]:
        """
        Delete a file

        Args:
            project_id: Project ID
            file_path: Relative file path

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM project_files
                WHERE project_id = ? AND file_path = ?
                """,
                (project_id, file_path),
            )

            conn.commit()
            success = cursor.rowcount > 0
            conn.close()

            if success:
                msg = f"Deleted file {file_path} from project {project_id}"
                self.logger.info(msg)
                return True, msg
            else:
                msg = f"File not found: {file_path}"
                self.logger.warning(msg)
                return False, msg

        except Exception as e:
            msg = f"Error deleting file: {str(e)}"
            self.logger.error(msg)
            return False, msg

    def delete_project_files(self, project_id: str) -> Tuple[int, str]:
        """
        Delete all files for a project

        Args:
            project_id: Project ID

        Returns:
            Tuple of (files_deleted_count: int, message: str)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM project_files
                WHERE project_id = ?
                """,
                (project_id,),
            )

            conn.commit()
            files_deleted = cursor.rowcount
            conn.close()

            msg = f"Deleted {files_deleted} files from project {project_id}"
            self.logger.info(msg)
            return files_deleted, msg

        except Exception as e:
            msg = f"Error deleting project files: {str(e)}"
            self.logger.error(msg)
            return 0, msg

    @staticmethod
    def compute_file_hash(content: str) -> str:
        """
        Compute MD5 hash of file content for change detection

        Args:
            content: File content as string

        Returns:
            MD5 hash of content
        """
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def get_project_files_generator(self, project_id: str, batch_size: int = 50):
        """
        Generator that yields files in batches (memory efficient)

        Args:
            project_id: Project ID
            batch_size: Number of files per batch

        Yields:
            Batches of file dicts
        """
        offset = 0

        while True:
            batch = self.get_project_files(project_id, offset=offset, limit=batch_size)
            if not batch:
                break

            yield batch
            offset += batch_size

    def get_languages_in_project(self, project_id: str) -> List[str]:
        """
        Get list of programming languages found in project

        Args:
            project_id: Project ID

        Returns:
            List of unique language names
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT language
                FROM project_files
                WHERE project_id = ? AND language IS NOT NULL
                ORDER BY language
                """,
                (project_id,),
            )

            languages = [row[0] for row in cursor.fetchall()]
            conn.close()

            return languages

        except Exception as e:
            self.logger.error(f"Error getting languages: {str(e)}")
            return []

    def get_total_size(self, project_id: str) -> int:
        """
        Get total size of all files in project

        Args:
            project_id: Project ID

        Returns:
            Total size in bytes
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT SUM(file_size) FROM project_files
                WHERE project_id = ?
                """,
                (project_id,),
            )

            result = cursor.fetchone()[0]
            conn.close()

            return result or 0

        except Exception as e:
            self.logger.error(f"Error getting total size: {str(e)}")
            return 0

    def get_project_stats(self, project_id: str) -> Dict:
        """
        Get comprehensive statistics about project files

        Args:
            project_id: Project ID

        Returns:
            Dict with file statistics
        """
        try:
            file_count = self.get_file_count(project_id)
            total_size = self.get_total_size(project_id)
            languages = self.get_languages_in_project(project_id)

            return {
                "project_id": project_id,
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "languages": languages,
                "language_count": len(languages),
            }

        except Exception as e:
            self.logger.error(f"Error getting project stats: {str(e)}")
            return {}
