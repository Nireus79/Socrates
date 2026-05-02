"""
Knowledge Repository - Data access layer for knowledge base persistence.

Encapsulates knowledge-related database operations for both vector and
relational databases, providing a clean interface for services.
"""

from typing import List, Optional

from socratic_system.database import ProjectDatabase, VectorDatabase
from socratic_system.models import KnowledgeEntry
from socratic_system.services.repositories.base import Repository


class KnowledgeRepository(Repository[KnowledgeEntry]):
    """
    Repository for knowledge persistence.

    Manages both vector database (for semantic search) and relational
    database (for metadata and structured storage).
    """

    def __init__(self, project_db: ProjectDatabase, vector_db: VectorDatabase):
        """
        Initialize knowledge repository.

        Args:
            project_db: ProjectDatabase for relational storage
            vector_db: VectorDatabase for semantic search and embeddings
        """
        self.project_db = project_db
        self.vector_db = vector_db

    def save(self, knowledge: KnowledgeEntry) -> KnowledgeEntry:
        """
        Save knowledge entry to both databases.

        Args:
            knowledge: The knowledge entry to save

        Returns:
            The saved knowledge entry
        """
        # Save to relational database
        self.project_db.save_knowledge_document(knowledge)

        # Save embedding to vector database
        if hasattr(knowledge, "content"):
            self.vector_db.add_knowledge(knowledge.content, knowledge.project_id)

        return knowledge

    def find_by_id(self, knowledge_id: str) -> Optional[KnowledgeEntry]:
        """
        Find knowledge entry by ID.

        Args:
            knowledge_id: The ID of the knowledge entry

        Returns:
            The knowledge entry if found, None otherwise
        """
        return self.project_db.get_knowledge_document(knowledge_id)

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[KnowledgeEntry]:
        """
        Find all knowledge entries with optional pagination.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of knowledge entries
        """
        entries = self.project_db.get_all_knowledge_documents()

        if offset > 0:
            entries = entries[offset:]
        if limit is not None:
            entries = entries[:limit]

        return entries

    def delete(self, knowledge_id: str) -> bool:
        """
        Delete knowledge entry.

        Args:
            knowledge_id: The ID of the knowledge entry to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            self.project_db.delete_knowledge_document(knowledge_id)
            return True
        except Exception:
            return False

    def exists(self, knowledge_id: str) -> bool:
        """
        Check if knowledge entry exists.

        Args:
            knowledge_id: The ID to check

        Returns:
            True if exists, False otherwise
        """
        return self.find_by_id(knowledge_id) is not None

    def search(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[tuple[KnowledgeEntry, float]]:
        """
        Search knowledge using vector similarity.

        Args:
            query: Search query
            project_id: Project to search within
            top_k: Maximum number of results

        Returns:
            List of (knowledge_entry, similarity_score) tuples
        """
        return self.vector_db.search_similar(query, top_k, project_id)

    def find_by_project(self, project_id: str) -> List[KnowledgeEntry]:
        """
        Find all knowledge entries for a project.

        Args:
            project_id: The project ID

        Returns:
            List of knowledge entries for the project
        """
        return self.project_db.get_project_knowledge(project_id)
