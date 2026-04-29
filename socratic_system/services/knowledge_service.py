"""
Knowledge Service - Encapsulates knowledge management and retrieval.

Handles:
- Knowledge base operations
- Vector similarity search
- Knowledge caching

No orchestrator dependency - uses dependency injection for all external services.
"""

from typing import List, Optional, Tuple

from socratic_system.config import SocratesConfig
from socratic_system.models import KnowledgeEntry
from socratic_system.services.base import Service
from socratic_system.services.repositories import KnowledgeRepository


class KnowledgeService(Service):
    """
    Service for knowledge management.

    Manages knowledge base operations including storage, retrieval,
    and semantic search using vector databases.
    """

    def __init__(
        self,
        config: SocratesConfig,
        repository: KnowledgeRepository,
    ):
        """
        Initialize knowledge service.

        Args:
            config: SocratesConfig instance
            repository: KnowledgeRepository for knowledge data persistence
        """
        super().__init__(config)
        self.repository = repository

    def add_knowledge(
        self,
        content: str,
        project_id: str,
        metadata: Optional[dict] = None,
    ) -> KnowledgeEntry:
        """
        Add knowledge entry to the knowledge base.

        Args:
            content: The knowledge content
            project_id: Project this knowledge belongs to
            metadata: Optional metadata dictionary

        Returns:
            Created KnowledgeEntry
        """
        if not content or not content.strip():
            raise ValueError("Knowledge content cannot be empty")
        if not project_id:
            raise ValueError("Project ID is required")

        self.log_info(f"Adding knowledge to project {project_id}")

        # Create knowledge entry (using external library interface)
        import uuid

        entry_id = f"know_{str(uuid.uuid4())}"
        knowledge = KnowledgeEntry(
            id=entry_id,
            content=content.strip(),
            category=metadata.get("category", "general") if metadata else "general"
        )

        # Save to repository (includes vector embedding)
        saved_knowledge = self.repository.save(knowledge)

        self.log_info(f"Knowledge added: {saved_knowledge.id}")
        return saved_knowledge

    def search_knowledge(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Search knowledge base using semantic similarity.

        Args:
            query: Search query
            project_id: Project to search within
            top_k: Maximum number of results

        Returns:
            List of (KnowledgeEntry, similarity_score) tuples
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        self.log_debug(f"Searching knowledge in {project_id} for: {query}")

        return self.repository.search(query, project_id, top_k)

    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeEntry]:
        """
        Get knowledge entry by ID.

        Args:
            knowledge_id: The knowledge entry ID

        Returns:
            KnowledgeEntry if found, None otherwise
        """
        return self.repository.find_by_id(knowledge_id)

    def get_project_knowledge(self, project_id: str) -> List[KnowledgeEntry]:
        """
        Get all knowledge entries for a project.

        Args:
            project_id: The project ID

        Returns:
            List of knowledge entries
        """
        return self.repository.find_by_project(project_id)

    def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete knowledge entry.

        Args:
            knowledge_id: The knowledge entry ID

        Returns:
            True if deleted successfully, False otherwise
        """
        knowledge = self.repository.find_by_id(knowledge_id)
        if not knowledge:
            self.log_warning(f"Knowledge not found: {knowledge_id}")
            return False

        success = self.repository.delete(knowledge_id)

        if success:
            self.log_info(f"Knowledge deleted: {knowledge_id}")

        return success

    def knowledge_exists(self, knowledge_id: str) -> bool:
        """
        Check if knowledge entry exists.

        Args:
            knowledge_id: The knowledge entry ID

        Returns:
            True if exists, False otherwise
        """
        return self.repository.exists(knowledge_id)

    def bulk_add_knowledge(
        self,
        entries: List[Tuple[str, str]],
        project_id: str,
    ) -> List[KnowledgeEntry]:
        """
        Add multiple knowledge entries efficiently.

        Args:
            entries: List of (content, title) tuples
            project_id: Project this knowledge belongs to

        Returns:
            List of created KnowledgeEntry objects
        """
        self.log_info(f"Adding {len(entries)} knowledge entries to {project_id}")

        results = []
        for content, title in entries:
            try:
                knowledge = self.add_knowledge(
                    content=content,
                    project_id=project_id,
                    metadata={"title": title} if title else {},
                )
                results.append(knowledge)
            except Exception as e:
                self.log_error(f"Failed to add knowledge '{title}': {e}")

        self.log_info(f"Successfully added {len(results)} knowledge entries")
        return results

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
