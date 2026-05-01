"""
DocumentRepository - Data access for project documents.

Abstracts all document metadata database operations.
Used by DocumentService instead of direct database calls.

This is the single point of change for document schema updates.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base_repository import BaseRepository

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase


class DocumentRepository(BaseRepository):
    """
    Repository for document data access.

    Encapsulates all document import and metadata database operations.
    Services use this instead of calling database directly.
    """

    def __init__(self, database: "ProjectDatabase"):
        """
        Initialize document repository.

        Args:
            database: ProjectDatabase instance
        """
        super().__init__(database)

    def get_project_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a project.

        Args:
            project_id: Project ID

        Returns:
            List of document metadata dicts
        """
        self._log_operation("get_project_documents", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if project and hasattr(project, "documents"):
                return project.documents if project.documents else []
            return []
        except Exception as e:
            self.logger.error(f"Failed to get documents for {project_id}: {e}")
            return []

    def add_document(
        self,
        project_id: str,
        file_name: str,
        file_path: str,
        content_type: str,
        word_count: int,
        chunk_count: int,
        entries_stored: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a document record to project.

        Args:
            project_id: Project ID
            file_name: Original file name
            file_path: Path to file
            content_type: Type of content (file, text, url, etc.)
            word_count: Number of words extracted
            chunk_count: Number of chunks created
            entries_stored: Number of entries stored in vector DB
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "add_document",
            {"project_id": project_id, "file_name": file_name},
        )
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            # Initialize documents list if not exists
            if not hasattr(project, "documents"):
                project.documents = []

            document = {
                "file_name": file_name,
                "file_path": file_path,
                "content_type": content_type,
                "word_count": word_count,
                "chunk_count": chunk_count,
                "entries_stored": entries_stored,
                "imported": True,
                "metadata": metadata or {},
                "imported_at": __import__("datetime").datetime.now().isoformat(),
            }

            project.documents.append(document)
            self.database.save_project(project)
            self.logger.debug(f"Added document {file_name} to project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add document for {project_id}: {e}")
            return False

    def get_document_by_name(
        self, project_id: str, file_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document by file name.

        Args:
            project_id: Project ID
            file_name: File name to search for

        Returns:
            Document dict if found, None otherwise
        """
        self._log_operation(
            "get_document_by_name",
            {"project_id": project_id, "file_name": file_name},
        )
        try:
            documents = self.get_project_documents(project_id)
            for doc in documents:
                if doc.get("file_name") == file_name:
                    return doc
            return None
        except Exception as e:
            self.logger.error(
                f"Failed to get document {file_name} for {project_id}: {e}"
            )
            return None

    def get_documents_by_type(
        self, project_id: str, content_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get all documents of a specific type.

        Args:
            project_id: Project ID
            content_type: Type of content to filter by (file, text, url, etc.)

        Returns:
            List of documents matching the type
        """
        self._log_operation(
            "get_documents_by_type",
            {"project_id": project_id, "content_type": content_type},
        )
        try:
            documents = self.get_project_documents(project_id)
            filtered = [d for d in documents if d.get("content_type") == content_type]
            self.logger.debug(
                f"Found {len(filtered)} {content_type} documents for {project_id}"
            )
            return filtered
        except Exception as e:
            self.logger.error(
                f"Failed to get {content_type} documents for {project_id}: {e}"
            )
            return []

    def get_document_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Get statistics about all documents for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with document statistics
        """
        self._log_operation(
            "get_document_statistics", {"project_id": project_id}
        )
        try:
            documents = self.get_project_documents(project_id)

            stats = {
                "total_documents": len(documents),
                "total_words": 0,
                "total_chunks": 0,
                "total_entries": 0,
                "by_type": {},
            }

            for doc in documents:
                stats["total_words"] += doc.get("word_count", 0)
                stats["total_chunks"] += doc.get("chunk_count", 0)
                stats["total_entries"] += doc.get("entries_stored", 0)

                content_type = doc.get("content_type", "unknown")
                if content_type not in stats["by_type"]:
                    stats["by_type"][content_type] = {
                        "count": 0,
                        "words": 0,
                        "chunks": 0,
                    }
                stats["by_type"][content_type]["count"] += 1
                stats["by_type"][content_type]["words"] += doc.get("word_count", 0)
                stats["by_type"][content_type]["chunks"] += doc.get("chunk_count", 0)

            self.logger.debug(
                f"Retrieved statistics for {len(documents)} documents in {project_id}"
            )
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get document statistics for {project_id}: {e}")
            return {"total_documents": 0, "total_words": 0}

    def delete_document(
        self, project_id: str, file_name: str
    ) -> bool:
        """
        Delete a document record from project.

        Args:
            project_id: Project ID
            file_name: File name to delete

        Returns:
            True if successful, False otherwise
        """
        self._log_operation(
            "delete_document",
            {"project_id": project_id, "file_name": file_name},
        )
        try:
            project = self.database.load_project(project_id)
            if not project or not hasattr(project, "documents"):
                self.logger.error(f"Project {project_id} or documents not found")
                return False

            # Find and remove document
            original_count = len(project.documents)
            project.documents = [d for d in project.documents if d.get("file_name") != file_name]

            if len(project.documents) < original_count:
                self.database.save_project(project)
                self.logger.debug(f"Deleted document {file_name} from {project_id}")
                return True
            else:
                self.logger.warning(
                    f"Document {file_name} not found in project {project_id}"
                )
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete document for {project_id}: {e}")
            return False

    def clear_documents(self, project_id: str) -> bool:
        """
        Clear all document records for a project.

        Args:
            project_id: Project ID

        Returns:
            True if successful, False otherwise
        """
        self._log_operation("clear_documents", {"project_id": project_id})
        try:
            project = self.database.load_project(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False

            project.documents = []
            self.database.save_project(project)
            self.logger.debug(f"Cleared all documents for project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear documents for {project_id}: {e}")
            return False
