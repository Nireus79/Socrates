"""
Knowledge management system integrating socratic-knowledge with RAG capabilities.

Provides versioning, access control, audit logs, and retrieval-augmented generation.
"""

import logging
from typing import Any, Dict, List, Optional

from socratic_knowledge import KnowledgeManager as SKnowledgeManager
from socratic_rag import LLMPoweredRAG, RAGClient, RAGConfig

from socratic_system.models import KnowledgeEntry


class KnowledgeManager:
    """
    Integrated knowledge management system combining:
    - socratic-knowledge for versioning, access control, audit logs
    - socratic-rag for retrieval-augmented generation
    """

    def __init__(self, db_path: str, llm_client: Optional[Any] = None):
        """
        Initialize knowledge manager.

        Args:
            db_path: Path to knowledge database
            llm_client: Optional LLM client for RAG capabilities
        """
        self.db_path = db_path
        self.llm_client = llm_client
        self.logger = logging.getLogger("socrates.knowledge")

        try:
            # Initialize socratic-knowledge for versioning and access control
            self.km = SKnowledgeManager(
                storage="sqlite",
                db_path=db_path,
                enable_rag=True,
            )
            self.logger.info("KnowledgeManager initialized (socratic-knowledge)")

            # Initialize RAG system for retrieval
            rag_config = RAGConfig(
                vector_store="chromadb",
                embedder="sentence-transformers",
                chunking_strategy="fixed",
                chunk_size=512,
                chunk_overlap=50,
                collection_name="socratic_knowledge",
            )
            self.rag_client = RAGClient(config=rag_config)

            # Initialize LLM-powered RAG if LLM client provided
            if llm_client:
                self.llm_rag = LLMPoweredRAG(
                    rag_client=self.rag_client,
                    llm_client=llm_client
                )
                self.logger.info("LLM-powered RAG initialized")
            else:
                self.llm_rag = None

        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge manager: {e}")
            raise

    def create_item(self, content: str, title: str, metadata: Optional[Dict] = None,
                   user_id: str = "system") -> str:
        """
        Create a knowledge item with versioning.

        Args:
            content: Knowledge content
            title: Item title
            metadata: Optional metadata
            user_id: User creating the item

        Returns:
            Item ID
        """
        try:
            # Create in socratic-knowledge (with versioning)
            item = self.km.create_item(
                title=title,
                content=content,
                metadata=metadata or {},
            )

            # Also add to RAG for vector search
            self.rag_client.add_document(
                content=content,
                source=title,
                metadata={
                    "item_id": item.id if hasattr(item, 'id') else str(item),
                    "title": title,
                    **(metadata or {})
                }
            )

            self.logger.debug(f"Created knowledge item: {title}")
            return item.id if hasattr(item, 'id') else str(item)

        except Exception as e:
            self.logger.error(f"Failed to create item: {e}")
            raise

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching items
        """
        try:
            results = self.rag_client.search(query=query, top_k=top_k)

            formatted = []
            for result in results:
                formatted.append({
                    "content": result.content if hasattr(result, 'content') else "",
                    "metadata": result.metadata if hasattr(result, 'metadata') else {},
                    "score": getattr(result, 'score', 0.0),
                })

            return formatted

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def generate_answer(self, query: str, top_k: int = 5,
                       context_prefix: str = "Context:\n") -> str:
        """
        Generate answer using LLM with retrieved context.

        Args:
            query: User question
            top_k: Number of context documents
            context_prefix: Prefix for context section

        Returns:
            Generated answer with context
        """
        if not self.llm_rag:
            self.logger.warning("LLM RAG not initialized, returning search results instead")
            results = self.search(query, top_k)
            return "\n".join([r.get("content", "") for r in results])

        try:
            answer = self.llm_rag.generate_answer(
                query=query,
                top_k=top_k,
                context_prefix=context_prefix
            )
            return answer

        except Exception as e:
            self.logger.error(f"Answer generation failed: {e}")
            # Fallback to search results
            results = self.search(query, top_k)
            return "\n".join([r.get("content", "") for r in results])

    def get_history(self, item_id: str) -> List[Dict]:
        """
        Get version history for an item.

        Args:
            item_id: Item ID

        Returns:
            List of versions
        """
        try:
            history = self.km.get_resource_history(item_id)
            return history if history else []
        except Exception as e:
            self.logger.error(f"Failed to get history: {e}")
            return []

    def get_audit_log(self, resource_id: str) -> List[Dict]:
        """
        Get audit log for a resource.

        Args:
            resource_id: Resource ID

        Returns:
            List of audit entries
        """
        try:
            log = self.km.get_audit_log(resource_id)
            return log if log else []
        except Exception as e:
            self.logger.error(f"Failed to get audit log: {e}")
            return []

    def add_knowledge_entry(self, entry: KnowledgeEntry) -> bool:
        """
        Add a knowledge entry (from Socrates format).

        Args:
            entry: KnowledgeEntry object

        Returns:
            True if successful
        """
        try:
            self.create_item(
                content=entry.content,
                title=entry.category,
                metadata={
                    "id": entry.id,
                    "category": entry.category,
                    **(entry.metadata or {})
                }
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to add entry: {e}")
            return False

    def close(self):
        """Close connections"""
        try:
            self.logger.info("Knowledge manager closed")
        except Exception as e:
            self.logger.error(f"Error closing: {e}")

    def __del__(self):
        """Cleanup"""
        try:
            self.close()
        except Exception:
            pass
