"""
Vector database for knowledge management in Socratic RAG System
"""

import os
from typing import Dict, List

import chromadb
from sentence_transformers import SentenceTransformer

from socratic_system.config import CONFIG
from socratic_system.models import KnowledgeEntry


class VectorDatabase:
    """Vector database for storing and searching knowledge entries"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("socratic_knowledge")
        self.embedding_model = SentenceTransformer(CONFIG['EMBEDDING_MODEL'])
        self.knowledge_loaded = False  # FIX: Track if knowledge is already loaded

    def add_knowledge(self, entry: KnowledgeEntry):
        """Add knowledge entry to vector database"""
        # FIX: Check if entry already exists before adding
        try:
            existing = self.collection.get(ids=[entry.id])
            if existing['ids']:
                print(f"Knowledge entry '{entry.id}' already exists, skipping...")
                return
        except Exception:
            pass  # Entry doesn't exist, proceed with adding

        if not entry.embedding:
            embedding_result = self.embedding_model.encode(entry.content)
            entry.embedding = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else embedding_result

        try:
            self.collection.add(
                documents=[entry.content],
                metadatas=[entry.metadata],
                ids=[entry.id],
                embeddings=[entry.embedding]
            )
            print(f"Added knowledge entry: {entry.id}")
        except Exception as e:
            print(f"Warning: Could not add knowledge entry {entry.id}: {e}")

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar knowledge entries"""
        if not query.strip():
            return []

        try:
            query_embedding = self.embedding_model.encode(query).tolist()

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count())
            )

            if not results['documents'] or not results['documents'][0]:
                return []

            return [{
                'content': doc,
                'metadata': meta,
                'score': dist
            } for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )]
        except Exception as e:
            print(f"Warning: Search failed: {e}")
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
            id=content_id,
            content=content,
            category='imported_document',
            metadata=metadata
        )

        self.add_knowledge(entry)

    def delete_entry(self, entry_id: str):
        """Delete knowledge entry"""
        try:
            self.collection.delete(ids=[entry_id])
        except Exception as e:
            print(f"Warning: Could not delete entry {entry_id}: {e}")
