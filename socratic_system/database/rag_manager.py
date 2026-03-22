"""
RAG Manager - Unified interface for Retrieval-Augmented Generation

Coordinates vector database, embedding cache, and search functionality.
Provides high-level API for knowledge retrieval and management.
"""

import logging
from typing import Dict, List, Optional

from socratic_system.database.embedding_cache import EmbeddingCache
from socratic_system.database.rag_config import RAGConfig, get_default_config
from socratic_system.database.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class RAGManager:
    """
    Unified manager for Retrieval-Augmented Generation.

    Coordinates:
    - Vector database for semantic search
    - Embedding cache for performance
    - Configuration management
    - Knowledge retrieval and storage
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG manager.

        Args:
            config: RAG configuration (uses default if not provided)
        """
        self.config = config or get_default_config()

        # Validate configuration
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid RAG configuration: {error_msg}")

        # Initialize components
        self.embedding_cache = None
        self.vector_db = None

        if self.config.embedding_cache_enabled:
            self.embedding_cache = EmbeddingCache(max_size=self.config.embedding_cache_size)
            logger.info(
                f"Embedding cache initialized (size: {self.config.embedding_cache_size})"
            )

        try:
            self.vector_db = VectorDatabase(
                db_path=self.config.vector_store_path,
                embedding_model=self.config.embedding_model.value,
            )
            logger.info("Vector database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            # Continue without vector db if initialization fails (graceful degradation)
            self.vector_db = None

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        project_id: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Search for relevant knowledge entries.

        Args:
            query: Search query
            top_k: Number of results (uses config default if not provided)
            project_id: Optional project filter
            threshold: Similarity threshold (uses config default if not provided)

        Returns:
            List of matching entries with similarity scores
        """
        if not self.vector_db:
            logger.warning("Vector database not available, returning empty results")
            return []

        top_k = top_k or self.config.default_top_k
        threshold = threshold if threshold is not None else self.config.similarity_threshold

        try:
            results = self.vector_db.search_similar(
                query=query,
                top_k=top_k,
                project_id=project_id,
                threshold=threshold,
            )

            # Filter by threshold
            filtered_results = [r for r in results if r.get("similarity", 0) >= threshold]

            logger.debug(f"Search found {len(filtered_results)} results for query: {query}")
            return filtered_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add knowledge entry to the system.

        Args:
            content: Knowledge content
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.vector_db:
            logger.warning("Vector database not available, cannot add knowledge")
            return False

        try:
            if metadata is None:
                metadata = {}

            self.vector_db.add_text(content=content, metadata=metadata)
            logger.debug(f"Added knowledge entry ({len(content)} chars)")
            return True

        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return False

    def get_project_knowledge(self, project_id: str) -> List[Dict]:
        """
        Get all knowledge entries for a project.

        Args:
            project_id: Project ID

        Returns:
            List of knowledge entries
        """
        if not self.vector_db:
            return []

        try:
            entries = self.vector_db.get_project_knowledge(project_id)
            logger.debug(f"Retrieved {len(entries)} entries for project {project_id}")
            return entries

        except Exception as e:
            logger.error(f"Failed to get project knowledge: {e}")
            return []

    def import_knowledge(self, project_id: str, entries: List[Dict]) -> int:
        """
        Import knowledge entries for a project.

        Args:
            project_id: Project ID
            entries: List of knowledge entries to import

        Returns:
            Number of entries imported
        """
        if not self.vector_db:
            logger.warning("Vector database not available, cannot import knowledge")
            return 0

        try:
            count = self.vector_db.import_project_knowledge(project_id, entries)
            logger.info(f"Imported {count} entries for project {project_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to import knowledge: {e}")
            return 0

    def export_knowledge(self, project_id: str) -> List[Dict]:
        """
        Export knowledge entries for a project.

        Args:
            project_id: Project ID

        Returns:
            List of knowledge entries
        """
        if not self.vector_db:
            return []

        try:
            entries = self.vector_db.export_project_knowledge(project_id)
            logger.info(f"Exported {len(entries)} entries for project {project_id}")
            return entries

        except Exception as e:
            logger.error(f"Failed to export knowledge: {e}")
            return []

    def get_cache_stats(self) -> Dict:
        """
        Get embedding cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.embedding_cache:
            return {"enabled": False}

        stats = self.embedding_cache.stats()
        return {
            "enabled": True,
            **stats,
        }

    def get_status(self) -> Dict:
        """
        Get RAG system status.

        Returns:
            Dictionary with system status
        """
        return {
            "vector_db_available": self.vector_db is not None,
            "embedding_cache_available": self.embedding_cache is not None,
            "config": self.config.to_dict(),
            "cache_stats": self.get_cache_stats(),
        }

    def close(self):
        """Close RAG manager and clean up resources"""
        try:
            if self.vector_db:
                self.vector_db.close()
            logger.info("RAG manager closed")
        except Exception as e:
            logger.error(f"Error closing RAG manager: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global RAG manager instance
_rag_manager: Optional[RAGManager] = None


def get_rag_manager(config: Optional[RAGConfig] = None) -> RAGManager:
    """
    Get or create the global RAG manager.

    Args:
        config: Optional configuration (only used if creating new instance)

    Returns:
        RAG manager instance
    """
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager(config)
    return _rag_manager


def initialize_rag(config: RAGConfig) -> RAGManager:
    """
    Initialize RAG system with specified configuration.

    Args:
        config: RAG configuration

    Returns:
        Initialized RAG manager
    """
    global _rag_manager
    _rag_manager = RAGManager(config)
    return _rag_manager
