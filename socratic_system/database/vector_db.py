"""
Vector database for knowledge management in Socratic RAG System
"""

import logging
from typing import Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from socratic_system.models import KnowledgeEntry


class VectorDatabase:
    """Vector database for storing and searching knowledge entries"""

    def __init__(self, db_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.logger = logging.getLogger("socrates.database.vector")

        self.logger.info(f"Initializing vector database: {self.db_path}")
        self.client = chromadb.PersistentClient(path=db_path)
        self.logger.debug("ChromaDB client created")

        self.collection = self.client.get_or_create_collection("socratic_knowledge")
        self.logger.debug("Vector collection 'socratic_knowledge' initialized")

        self.logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.logger.info("Vector database initialized successfully")

        self.knowledge_loaded = False  # Track if knowledge is already loaded

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
        # FIX: Check if entry already exists before adding
        try:
            existing = self.collection.get(ids=[entry.id])
            if existing["ids"]:
                self.logger.debug(f"Knowledge entry '{entry.id}' already exists, skipping...")
                return
        except (KeyError, ValueError) as e:
            # Entry doesn't exist or invalid query, proceed with adding
            self.logger.debug(f"Entry '{entry.id}' not found or invalid query, will proceed: {e}")

        if not entry.embedding:
            embedding_result = self.embedding_model.encode(entry.content)
            entry.embedding = (
                embedding_result.tolist()
                if hasattr(embedding_result, "tolist")
                else embedding_result
            )

        try:
            formatted_metadata = self._format_metadata_for_chromadb(entry.metadata)
            self.collection.add(
                documents=[entry.content],
                metadatas=[formatted_metadata],
                ids=[entry.id],
                embeddings=[entry.embedding],
            )
            self.logger.debug(f"Added knowledge entry: {entry.id}")
        except Exception as e:
            self.logger.warning(f"Could not add knowledge entry {entry.id}: {e}")

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
            query_embedding = self.embedding_model.encode(query).tolist()

            # Build where filter for project_id if specified
            where_filter = self._build_project_filter(project_id)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count()),
                where=where_filter if where_filter else None,
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            return [
                {"content": doc, "metadata": meta, "score": dist}
                for doc, meta, dist in zip(
                    results["documents"][0], results["metadatas"][0], results["distances"][0]
                )
            ]
        except Exception as e:
            self.logger.warning(f"Search failed: {e}")
            return []

    def add_text(self, content: str, metadata: Dict = None):
        """Add text content directly (for document imports)"""
        if metadata is None:
            metadata = {}

        # Generate unique ID based on content hash
        import hashlib

        content_id = hashlib.md5(content.encode()).hexdigest()[:8]

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
            project_id: Project ID to filter by, or None for no filtering

        Returns:
            ChromaDB where filter dict, or None if no filtering needed
        """
        if project_id is None:
            # No filtering - search all knowledge
            return None
        else:
            # Search only project-specific knowledge
            return {"project_id": {"$eq": project_id}}

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
