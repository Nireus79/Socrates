"""
Vector database for knowledge management in Socratic RAG System
"""

import gc
import logging
import os
from typing import Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from socratic_system.database.embedding_cache import EmbeddingCache
from socratic_system.database.search_cache import SearchResultCache
from socratic_system.models import KnowledgeEntry


class VectorDatabase:
    """Vector database for storing and searching knowledge entries"""

    def __init__(self, db_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector database.

        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model: Name of the embedding model to use

        Raises:
            ValueError: If db_path is invalid
            RuntimeError: If ChromaDB or embedding model initialization fails
        """
        if not db_path or not isinstance(db_path, str) or db_path.strip() == "":
            raise ValueError(f"Invalid db_path: {db_path!r}. Must be a non-empty string.")

        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.logger = logging.getLogger("socrates.database.vector")

        # Create parent directory if needed
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.logger.info(f"Initializing vector database: {self.db_path}")
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.logger.debug("ChromaDB client created")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB client at {db_path}: {e}") from e

        try:
            self.collection = self.client.get_or_create_collection("socratic_knowledge")
            self.logger.debug("Vector collection 'socratic_knowledge' initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to create ChromaDB collection: {e}") from e

        # Lazy-load embedding model on first use (saves 1-3 seconds at startup)
        self._embedding_model_instance = None
        self.logger.info("Vector database initialized successfully (embedding model will load on first use)")

        # Initialize caches for Phase 3 optimization
        self.embedding_cache = EmbeddingCache(max_size=10000)
        self.search_cache = SearchResultCache(ttl_seconds=300)
        self.logger.info("Embedding and search caches initialized (Phase 3)")

        self.knowledge_loaded = False  # Track if knowledge is already loaded

    @property
    def embedding_model(self):
        """Lazy-load embedding model on first access (saves 1-3 seconds at startup)"""
        if self._embedding_model_instance is None:
            self.logger.info(f"Loading embedding model on first use: {self.embedding_model_name}")
            try:
                self._embedding_model_instance = SentenceTransformer(self.embedding_model_name)
                self.logger.info("Embedding model loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load embedding model {self.embedding_model_name}: {e}")
                raise RuntimeError(
                    f"Failed to load embedding model '{self.embedding_model_name}'. "
                    f"This may be due to network issues or missing model. Error: {e}"
                ) from e
        return self._embedding_model_instance

    def _format_metadata_for_chromadb(self, metadata: Optional[Dict]) -> Dict:
        """
        Convert metadata to ChromaDB-compatible format.
        ChromaDB only supports primitive types (str, int, float, bool, None).
        Lists and dicts are converted to strings.
        """
        if not metadata:
            return {}

        formatted = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                formatted[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                formatted[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Convert dicts to JSON string representation
                import json

                formatted[key] = json.dumps(value)
            else:
                # Convert other types to string
                formatted[key] = str(value)

        return formatted

    def add_knowledge(self, entry: KnowledgeEntry):
        """Add knowledge entry to vector database"""
        # Check if entry already exists
        if self._entry_exists(entry.id):
            return

        # Generate or get cached embedding
        self._generate_or_cache_embedding(entry)

        # Add to collection with metadata
        self._add_entry_to_collection(entry)

    def _entry_exists(self, entry_id: str) -> bool:
        """Check if entry already exists"""
        try:
            existing = self.collection.get(ids=[entry_id])
            if existing["ids"]:
                self.logger.debug(f"Knowledge entry '{entry_id}' already exists, skipping...")
                return True
        except (KeyError, ValueError) as e:
            # Entry doesn't exist or invalid query, proceed with adding
            self.logger.debug(f"Entry '{entry_id}' not found or invalid query, will proceed: {e}")
        return False

    def _generate_or_cache_embedding(self, entry: KnowledgeEntry) -> None:
        """Generate embedding or retrieve from cache"""
        if entry.embedding:
            return

        try:
            # Check embedding cache first
            cached_embedding = self.embedding_cache.get(entry.content)
            if cached_embedding:
                entry.embedding = cached_embedding
                self.logger.debug(f"Using cached embedding for knowledge entry: {entry.id}")
            else:
                # Not in cache, encode and cache
                embedding_result = self.embedding_model.encode(entry.content)
                entry.embedding = (
                    embedding_result.tolist()
                    if hasattr(embedding_result, "tolist")
                    else embedding_result
                )
                self.embedding_cache.put(entry.content, entry.embedding)
                self.logger.debug(f"Cached new embedding for knowledge entry: {entry.id}")
        except (ValueError, RuntimeError, OSError) as e:
            self._handle_embedding_error(e, entry)

    def _handle_embedding_error(self, error: Exception, entry: KnowledgeEntry) -> None:
        """Handle embedding generation errors with recovery"""
        if "closed file" not in str(error) and "I/O operation" not in str(error):
            raise

        self.logger.warning(f"Embedding model has stale file handles, attempting recovery: {error}")
        try:
            gc.collect()
            self._embedding_model_instance = None
            self.logger.debug("Reloading embedding model after garbage collection")

            embedding_result = self.embedding_model.encode(entry.content)
            entry.embedding = (
                embedding_result.tolist()
                if hasattr(embedding_result, "tolist")
                else embedding_result
            )
            self.embedding_cache.put(entry.content, entry.embedding)
            self.logger.info("Successfully recovered embedding model and encoded content")
        except Exception as retry_error:
            self.logger.error(f"Failed to recover embedding model: {retry_error}")
            raise

    def _add_entry_to_collection(self, entry: KnowledgeEntry) -> None:
        """Add entry to collection and invalidate caches"""
        try:
            self._prepare_and_add_metadata(entry)
            formatted_metadata = self._format_metadata_for_chromadb(entry.metadata)
            self.collection.add(
                documents=[entry.content],
                metadatas=[formatted_metadata],
                ids=[entry.id],
                embeddings=[entry.embedding],
            )
            self.logger.debug(f"Added knowledge entry: {entry.id}")
            self._invalidate_search_caches_after_add()
        except Exception as e:
            self.logger.warning(f"Could not add knowledge entry {entry.id}: {e}")

    def _prepare_and_add_metadata(self, entry: KnowledgeEntry) -> None:
        """Prepare metadata for entry"""
        if entry.metadata is None:
            entry.metadata = {}
        # If no scope is set and no project_id, mark as global knowledge
        if "scope" not in entry.metadata and "project_id" not in entry.metadata:
            entry.metadata["scope"] = "global"

    def _invalidate_search_caches_after_add(self) -> None:
        """Invalidate search caches after adding knowledge"""
        count = self.search_cache.invalidate_global_searches()
        if count > 0:
            self.logger.debug(
                f"Invalidated {count} global search cache entries after adding knowledge"
            )

    def search_similar(
        self, query: str, top_k: int = 5, project_id: Optional[str] = None
    ) -> List[Dict]:
        """Search for similar knowledge entries

        Args:
            query: Search query string
            top_k: Number of results to return
            project_id: Optional project ID to filter results. If None, searches all knowledge
        """
        if not query.strip():
            return []

        try:
            # Phase 3: Check search result cache first
            cached_results = self.search_cache.get(query, top_k, project_id)
            if cached_results:
                self.logger.debug(f"Using cached search results for query: {query[:30]}...")
                return cached_results

            # Phase 3: Check embedding cache for query
            cached_embedding = self.embedding_cache.get(query)
            if cached_embedding:
                query_embedding = cached_embedding
                self.logger.debug(f"Using cached query embedding for: {query[:30]}...")
            else:
                # Not in cache, encode and cache
                query_embedding = self.embedding_model.encode(query).tolist()
                self.embedding_cache.put(query, query_embedding)
                self.logger.debug(f"Cached query embedding for: {query[:30]}...")

            # Build where filter for project_id if specified
            where_filter = self._build_project_filter(project_id)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count()),
                where=where_filter if where_filter else None,
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            search_results = [
                {"content": doc, "metadata": meta, "score": dist}
                for doc, meta, dist in zip(
                    results["documents"][0], results["metadatas"][0], results["distances"][0]
                )
            ]

            # Phase 3: Cache the search results
            self.search_cache.put(query, top_k, project_id, search_results)
            self.logger.debug(f"Cached search results for query: {query[:30]}...")

            return search_results
        except Exception as e:
            self.logger.warning(f"Search failed: {e}")
            return []

    def search_similar_adaptive(
        self,
        query: str,
        strategy: str = "snippet",
        top_k: int = 5,
        project_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Enhanced search with adaptive content loading.

        Strategies:
        - "full": Return full chunk content (500+ words)
        - "medium": Return 500 chars per chunk
        - "snippet": Return 200 chars per chunk (default, current behavior)

        Args:
            query: Search query string
            strategy: Content loading strategy ("full", "medium", or "snippet")
            top_k: Number of results to return
            project_id: Optional project ID to filter results

        Returns:
            List of dicts with:
            - content: Document text (length based on strategy)
            - full_content: Always include full chunk (for summarization)
            - metadata: Source, chunk info, project_id
            - score: Relevance score (distance metric)
            - summary: Brief summary of full content
        """
        if not query.strip():
            return []

        if strategy not in ("full", "medium", "snippet"):
            self.logger.warning(f"Invalid strategy '{strategy}', defaulting to 'snippet'")
            strategy = "snippet"

        try:
            # Use base search_similar to get results
            base_results = self.search_similar(query, top_k=top_k, project_id=project_id)

            if not base_results:
                return []

            enhanced_results = []
            for result in base_results:
                full_content = result["content"]

                # Apply strategy-based truncation
                if strategy == "full":
                    content = full_content
                elif strategy == "medium":
                    content = full_content[:500] + ("..." if len(full_content) > 500 else "")
                else:  # snippet
                    content = full_content[:200] + ("..." if len(full_content) > 200 else "")

                # Generate summary for the full content
                summary = self._generate_chunk_summary(full_content)

                enhanced_results.append({
                    "content": content,
                    "full_content": full_content,
                    "metadata": result["metadata"],
                    "score": result["score"],
                    "summary": summary
                })

            self.logger.debug(
                f"Adaptive search completed with strategy '{strategy}': "
                f"{len(enhanced_results)} results"
            )
            return enhanced_results

        except Exception as e:
            self.logger.warning(f"Adaptive search failed: {e}")
            return []

    def add_text(self, content: str, metadata: Dict = None):
        """Add text content directly (for document imports)"""
        if metadata is None:
            metadata = {}

        # Generate unique ID based on content hash (non-security use)
        import hashlib

        # Use full MD5 hash (32 chars) instead of truncated (8 chars) to avoid collisions
        try:
            content_id = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
        except TypeError:
            # Python 3.8 doesn't support usedforsecurity parameter
            content_id = hashlib.md5(content.encode()).hexdigest()  # nosec

        # Create knowledge entry
        entry = KnowledgeEntry(
            id=content_id, content=content, category="imported_document", metadata=metadata
        )

        self.add_knowledge(entry)

    def delete_entry(self, entry_id: str):
        """Delete knowledge entry"""
        try:
            self.collection.delete(ids=[entry_id])
        except Exception as e:
            self.logger.warning(f"Could not delete entry {entry_id}: {e}")

    def add_project_knowledge(self, entry: KnowledgeEntry, project_id: str) -> bool:
        """Add knowledge entry specific to a project

        Args:
            entry: KnowledgeEntry to add
            project_id: Project ID to associate with this knowledge

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add project_id and scope to metadata
            if entry.metadata is None:
                entry.metadata = {}
            entry.metadata["project_id"] = project_id
            entry.metadata["scope"] = "project"

            # Use add_knowledge to handle embedding and storage
            self.add_knowledge(entry)

            # Phase 3: Invalidate search cache for this project
            # Since knowledge has changed, cached results are now stale
            count = self.search_cache.invalidate_project(project_id)
            if count > 0:
                self.logger.info(
                    f"Invalidated {count} search cache entries for project '{project_id}'"
                )

            self.logger.debug(f"Added project knowledge '{entry.id}' for project '{project_id}'")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to add project knowledge: {e}")
            return False

    def get_project_knowledge(self, project_id: str) -> List[Dict]:
        """Get all knowledge entries for a specific project

        Args:
            project_id: Project ID to filter by

        Returns:
            List of knowledge entries for the project
        """
        try:
            # Query with project_id filter
            where_filter = {"project_id": {"$eq": project_id}}
            results = self.collection.get(where=where_filter)

            if not results["ids"]:
                return []

            return [
                {"id": entry_id, "content": doc, "metadata": meta}
                for entry_id, doc, meta in zip(
                    results["ids"], results["documents"], results["metadatas"]
                )
            ]
        except Exception as e:
            self.logger.warning(f"Failed to get project knowledge: {e}")
            return []

    def export_project_knowledge(self, project_id: str) -> List[Dict]:
        """Export all knowledge entries for a project as JSON-compatible dicts

        Args:
            project_id: Project ID to export

        Returns:
            List of knowledge entry dicts (id, content, category, metadata)
        """
        try:
            knowledge = self.get_project_knowledge(project_id)
            return [
                {
                    "id": entry["id"],
                    "content": entry["content"],
                    "category": entry["metadata"].get("category", "custom"),
                    "metadata": entry["metadata"],
                }
                for entry in knowledge
            ]
        except Exception as e:
            self.logger.warning(f"Failed to export project knowledge: {e}")
            return []

    def import_project_knowledge(self, project_id: str, entries: List[Dict]) -> int:
        """Import knowledge entries for a project

        Args:
            project_id: Project ID to import into
            entries: List of knowledge entry dicts

        Returns:
            Number of entries successfully imported
        """
        count = 0
        try:
            for entry_data in entries:
                try:
                    # Create KnowledgeEntry from dict
                    entry = KnowledgeEntry(
                        id=entry_data.get("id"),
                        content=entry_data.get("content"),
                        category=entry_data.get("category", "custom"),
                        metadata=entry_data.get("metadata", {}),
                    )
                    if self.add_project_knowledge(entry, project_id):
                        count += 1
                except Exception as e:
                    self.logger.debug(f"Failed to import entry {entry_data.get('id')}: {e}")
                    continue

            self.logger.info(f"Imported {count} knowledge entries for project '{project_id}'")
            return count
        except Exception as e:
            self.logger.warning(f"Failed to import project knowledge: {e}")
            return count

    def _build_project_filter(self, project_id: Optional[str] = None) -> Optional[Dict]:
        """Build ChromaDB where filter for project_id

        Args:
            project_id: Project ID to filter by, or None for global search

        Returns:
            ChromaDB where filter dict. Returns None for truly global search (all knowledge).
            For project-specific search, returns $or filter for global + project knowledge.
        """
        if project_id is None:
            # Global search: Return None (no filter) to search ALL knowledge
            # This is the simplest approach given ChromaDB's operator limitations
            return None
        else:
            # Project-specific search: Get both global AND project-specific knowledge
            # Global knowledge is identified by scope="global" (explicitly marked)
            # Project knowledge is identified by matching project_id
            # Note: ChromaDB only supports: $gt, $gte, $lt, $lte, $ne, $eq, $in, $nin
            # So we can't check for missing fields; we only match what we know is there
            return {
                "$or": [
                    {"scope": {"$eq": "global"}},  # Explicitly marked global knowledge
                    {"project_id": {"$eq": project_id}},  # Project-specific knowledge
                ]
            }

    def delete_project_knowledge(self, project_id: str) -> int:
        """Delete all knowledge entries for a project

        Args:
            project_id: Project ID to delete knowledge for

        Returns:
            Number of entries deleted
        """
        try:
            where_filter = {"project_id": {"$eq": project_id}}
            knowledge = self.collection.get(where=where_filter)

            if not knowledge["ids"]:
                return 0

            self.collection.delete(ids=knowledge["ids"])
            self.logger.info(
                f"Deleted {len(knowledge['ids'])} knowledge entries for project '{project_id}'"
            )
            return len(knowledge["ids"])
        except Exception as e:
            self.logger.warning(f"Failed to delete project knowledge: {e}")
            return 0

    def _generate_chunk_summary(self, chunk: str, max_length: int = 150) -> str:
        """
        Generate a brief summary of a document chunk.

        Summaries are generated using a heuristic approach (first sentences)
        with a fallback to simple truncation if the chunk is very short.

        Args:
            chunk: The document chunk to summarize
            max_length: Maximum length of the summary in characters

        Returns:
            A brief summary of the chunk content
        """
        if not chunk or not chunk.strip():
            return "(empty content)"

        # For very short content, just return it as-is
        if len(chunk) <= max_length:
            return chunk.strip()

        # Try to extract first few sentences for a natural summary
        import re

        # Split by sentence boundaries (., !, ?, followed by space and capital letter)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', chunk)

        summary_parts = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add sentence if it fits within max_length
            potential_length = current_length + len(sentence) + 1  # +1 for space
            if potential_length <= max_length:
                summary_parts.append(sentence)
                current_length = potential_length
            else:
                break

        if summary_parts:
            summary = " ".join(summary_parts)
            # Ensure it ends with punctuation
            if not summary.endswith(('.', '!', '?')):
                summary += "..."
            return summary
        else:
            # Fallback: just truncate and add ellipsis
            return chunk[:max_length].rstrip() + "..."

    def _safe_log(self, level: str, message: str):
        """Safely log messages, suppressing errors during Python shutdown.

        During Python interpreter shutdown, the logging module may be partially
        deinitialized, causing 'sys.meta_path is None' errors. This method
        safely handles those cases.
        """
        try:
            if level == "debug":
                self.logger.debug(message)
            elif level == "info":
                self.logger.info(message)
            elif level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)
        except Exception:
            # Silently ignore logging errors during shutdown
            pass

    def close(self):
        """Close database connections and release file handles.

        This method should be called before deleting temporary directories
        to ensure all ChromaDB file handles are released on Windows.
        """
        self._clear_embedding_model()
        self._close_chromadb_client()
        self._clear_caches()
        self._trigger_garbage_collection()
        self._handle_windows_delay()

    def _clear_embedding_model(self) -> None:
        """Clear the embedding model to release memory and file handles"""
        try:
            if self._embedding_model_instance is not None:
                self._embedding_model_instance = None
                self._safe_log("debug", "Cleared embedding model instance")
        except Exception as e:
            self._safe_log("warning", f"Error clearing embedding model: {e}")

    def _close_chromadb_client(self) -> None:
        """Close ChromaDB client reference for garbage collection"""
        try:
            if hasattr(self, 'client') and self.client is not None:
                self.client = None
                self._safe_log("debug", "Closed ChromaDB client reference")
        except Exception as e:
            self._safe_log("warning", f"Error closing ChromaDB client: {e}")

    def _clear_caches(self) -> None:
        """Clear embedding and search caches"""
        try:
            if hasattr(self, 'embedding_cache'):
                self.embedding_cache.clear()
            if hasattr(self, 'search_cache'):
                self.search_cache.clear()
            self._safe_log("debug", "Cleared embedding and search caches")
        except Exception as e:
            self._safe_log("warning", f"Error clearing caches: {e}")

    def _trigger_garbage_collection(self) -> None:
        """Force garbage collection to release file handles"""
        try:
            gc.collect()
            self._safe_log("debug", "Garbage collection triggered")
        except Exception as e:
            self._safe_log("warning", f"Error during garbage collection: {e}")

    def _handle_windows_delay(self) -> None:
        """Add delay on Windows for SQLite file handle release"""
        import sys
        import time

        if sys.platform == 'win32':
            try:
                time.sleep(0.1)  # 100ms delay for Windows file handle release
            except Exception:
                pass

    def __del__(self):
        """Destructor to ensure cleanup when object is garbage collected."""
        try:
            self.close()
        except Exception:
            # Silently ignore errors in destructor
            pass
