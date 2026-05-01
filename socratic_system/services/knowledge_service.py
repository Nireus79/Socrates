"""Knowledge service - encapsulates knowledge management and vector search."""

from typing import TYPE_CHECKING, List, Dict, Any, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase, VectorDatabase


class KnowledgeService(Service):
    """Service for knowledge management and vector search."""

    def __init__(
        self,
        config,
        project_db: "ProjectDatabase",
        vector_db: "VectorDatabase",
    ):
        """Initialize knowledge service.

        Args:
            config: Socrates configuration
            project_db: Project database
            vector_db: Vector database for embeddings
        """
        super().__init__(config)
        self.project_db = project_db
        self.vector_db = vector_db

    def search_knowledge(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for similar documents.

        Args:
            query: Search query
            project_id: Project identifier
            top_k: Number of results to return

        Returns:
            List of matching documents
        """
        self.logger.debug(f"Searching knowledge for: {query}")
        return self.vector_db.search_similar(query, top_k, project_id)

    def add_knowledge(self, project_id: str, content: str, metadata: Dict) -> str:
        """Add knowledge document to vector database.

        Args:
            project_id: Project identifier
            content: Document content
            metadata: Document metadata

        Returns:
            Document ID
        """
        self.logger.debug(f"Adding knowledge document for project {project_id}")
        doc_id = self.vector_db.add_document(content, metadata, project_id)
        return doc_id

    def get_project_knowledge(self, project_id: str) -> List[Dict]:
        """Get all knowledge documents for project.

        Args:
            project_id: Project identifier

        Returns:
            List of knowledge documents
        """
        project = self.project_db.load_project(project_id)
        if not project:
            return []
        return getattr(project, "knowledge_documents", [])
