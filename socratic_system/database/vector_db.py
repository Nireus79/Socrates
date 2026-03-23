"""
Vector database for knowledge management in Socrates AI

Uses socratic-rag for RAG capabilities and vector search.
"""

import logging
from typing import Dict, List, Optional

try:
    from socratic_rag import RAGClient, RAGConfig
except ImportError:
    RAGClient = None  # type: ignore
    RAGConfig = None  # type: ignore

from socratic_system.models import KnowledgeEntry


class VectorDatabase:
    """Vector database for storing and searching knowledge entries using socratic-rag"""

    def __init__(self, db_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector database.

        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model: Name of the embedding model to use

        Raises:
            ValueError: If db_path is invalid
            RuntimeError: If RAGClient initialization fails
        """
        if not db_path or not isinstance(db_path, str) or db_path.strip() == "":
            raise ValueError(f"Invalid db_path: {db_path!r}. Must be a non-empty string.")

        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.logger = logging.getLogger("socrates.database.vector")

        self.logger.info(f"Initializing vector database: {self.db_path}")

        # Check if RAG dependencies are available
        if RAGClient is None or RAGConfig is None:
            raise ImportError(
                "RAG functionality is not available. Please install 'socratic-rag' package "
                "or use the system without vector database capabilities."
            )

        try:
            # Configure RAG client with ChromaDB backend
            config = RAGConfig(
                vector_store="chromadb",
                embedder="sentence-transformers",
                chunking_strategy="fixed",
                chunk_size=512,
                chunk_overlap=50,
                collection_name="socratic_knowledge",
                embedding_cache=True,
                cache_ttl=3600,
            )

            # Initialize RAG client (it handles the ChromaDB setup internally)
            self.rag_client = RAGClient(config=config)
            self.logger.info("RAGClient initialized successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize RAGClient at {db_path}: {e}") from e

        self.knowledge_loaded = False  # Track if knowledge is already loaded

    def add_knowledge(self, entry: KnowledgeEntry):
        """
        Add a knowledge entry to the vector database.

        Args:
            entry: KnowledgeEntry object to add
        """
        try:
            metadata = {
                "category": getattr(entry, "category", "general"),
                "tags": ",".join(getattr(entry, "tags", [])),
                "created_at": str(getattr(entry, "created_at", "")),
                "source": getattr(entry, "source", "manual"),
            }

            self.rag_client.add_document(
                content=entry.content,
                source=getattr(entry, "source", "knowledge_entry"),
                metadata=metadata,
            )
            self.logger.debug(f"Added knowledge entry: {entry.id}")

        except Exception as e:
            self.logger.error(f"Failed to add knowledge entry: {e}", exc_info=True)
            raise

    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        threshold: float = 0.0,
    ) -> List[Dict]:
        """
        Search for similar knowledge entries.

        Args:
            query: Search query
            top_k: Number of results to return
            project_id: Optional project filter
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of similar entries with metadata
        """
        try:
            filters = None
            if project_id:
                filters = {"project_id": project_id}

            results = self.rag_client.search(query=query, top_k=top_k, filters=filters)

            # Convert SearchResult objects to dictionaries
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result.id if hasattr(result, "id") else str(result),
                        "content": result.content if hasattr(result, "content") else "",
                        "metadata": result.metadata if hasattr(result, "metadata") else {},
                        "similarity": getattr(result, "score", 0.0),
                    }
                )

            return formatted_results

        except Exception as e:
            self.logger.error(f"Search failed: {e}", exc_info=True)
            return []

    def search_similar_adaptive(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        min_quality_score: float = 0.5,
    ) -> List[Dict]:
        """
        Adaptive search that adjusts parameters based on query characteristics.

        Args:
            query: Search query
            top_k: Number of results to return
            project_id: Optional project filter
            min_quality_score: Minimum quality threshold

        Returns:
            List of relevant entries
        """
        # For now, use standard search - can be enhanced with adaptive logic
        return self.search_similar(query, top_k, project_id)

    def add_text(self, content: str, metadata: Dict = None):
        """
        Add plain text content to the vector database.

        Args:
            content: Text content to add
            metadata: Optional metadata dictionary
        """
        try:
            if metadata is None:
                metadata = {}

            self.rag_client.add_document(
                content=content, source=metadata.get("source", "text"), metadata=metadata
            )
            self.logger.debug(f"Added text content: {len(content)} characters")

        except Exception as e:
            self.logger.error(f"Failed to add text: {e}", exc_info=True)
            raise

    def delete_entry(self, entry_id: str):
        """
        Delete an entry from the database.

        Args:
            entry_id: ID of entry to delete
        """
        # Note: RAGClient doesn't have a direct delete method
        # This would need to be implemented in socratic-rag or handled differently
        self.logger.warning(f"Delete not supported in RAGClient: {entry_id}")

    def add_project_knowledge(self, entry: KnowledgeEntry, project_id: str) -> bool:
        """
        Add knowledge specific to a project.

        Args:
            entry: Knowledge entry
            project_id: Project ID

        Returns:
            True if successful
        """
        try:
            metadata = {
                "id": entry.id,
                "project_id": project_id,
                "category": getattr(entry, "category", "general"),
                "tags": ",".join(getattr(entry, "tags", [])),
                "created_at": str(getattr(entry, "created_at", "")),
                "source": getattr(entry, "source", "manual"),
            }

            self.rag_client.add_document(
                content=entry.content,
                source=getattr(entry, "source", "project_knowledge"),
                metadata=metadata,
            )
            self.logger.debug(f"Added project knowledge: {entry.id} for project {project_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add project knowledge: {e}", exc_info=True)
            return False

    def get_project_knowledge(self, project_id: str) -> List[Dict]:
        """
        Get all knowledge entries for a project.

        Args:
            project_id: Project ID

        Returns:
            List of knowledge entries
        """
        try:
            # Search with project_id filter
            results = self.rag_client.search(
                query="", filters={"project_id": project_id}, top_k=100  # Empty query to get all
            )

            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result.id if hasattr(result, "id") else str(result),
                        "content": result.content if hasattr(result, "content") else "",
                        "metadata": result.metadata if hasattr(result, "metadata") else {},
                    }
                )

            return formatted_results

        except Exception as e:
            self.logger.error(f"Failed to get project knowledge: {e}", exc_info=True)
            return []

    def export_project_knowledge(self, project_id: str) -> List[Dict]:
        """
        Export all knowledge entries for a project.

        Args:
            project_id: Project ID

        Returns:
            List of knowledge entries for export
        """
        return self.get_project_knowledge(project_id)

    def import_project_knowledge(self, project_id: str, entries: List[Dict]) -> int:
        """
        Import knowledge entries for a project.

        Args:
            project_id: Project ID
            entries: List of entries to import

        Returns:
            Number of entries imported
        """
        count = 0
        for entry_data in entries:
            try:
                metadata = entry_data.get("metadata", {})
                metadata["project_id"] = project_id

                self.rag_client.add_document(
                    content=entry_data.get("content", ""),
                    source=metadata.get("source", "import"),
                    metadata=metadata,
                )
                count += 1
            except Exception as e:
                self.logger.error(f"Failed to import entry: {e}")
                continue

        self.logger.info(f"Imported {count} entries for project {project_id}")
        return count

    def delete_project_knowledge(self, project_id: str) -> int:
        """
        Delete all knowledge entries for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of entries deleted
        """
        # Note: RAGClient doesn't have delete by filter capability
        self.logger.warning(f"Delete project knowledge not supported in RAGClient: {project_id}")
        return 0

    def count_chunks_by_source(self, source: str, project_id: Optional[str] = None) -> int:
        """
        Count chunks by source.

        Args:
            source: Source identifier
            project_id: Optional project filter

        Returns:
            Number of chunks
        """
        try:
            filters = {"source": source}
            if project_id:
                filters["project_id"] = project_id

            results = self.rag_client.search(query="", filters=filters, top_k=1000)
            return len(results)

        except Exception as e:
            self.logger.error(f"Failed to count chunks: {e}")
            return 0

    def close(self):
        """Close the database connection"""
        try:
            # RAGClient doesn't require explicit cleanup
            self.logger.info("Vector database closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")

    def __del__(self):
        """Cleanup on object deletion"""
        try:
            self.close()
        except Exception:
            pass
