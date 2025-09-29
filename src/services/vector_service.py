"""
Vector Service - ChromaDB Vector Database Integration
===================================================

Provides vector database operations for the Socratic RAG Enhanced system using ChromaDB.
Handles document embeddings, vector storage, similarity search, and knowledge retrieval.

Features:
- Document embedding and storage
- Similarity search and retrieval
- Collection management
- Metadata filtering and querying
- Knowledge extraction and chunking
- Vector database operations
"""

import logging
import os
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.types import Collection, EmbeddingFunction
    from typing import List

    # Handle different ChromaDB versions for Documents and Embeddings
    try:
        from chromadb.api.types import Documents, Embeddings
    except ImportError:
        # Fallback type definitions for older ChromaDB versions
        Documents = List[str]
        Embeddings = List[List[float]]

    CHROMADB_AVAILABLE = True

except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Documents = List[str]
    Embeddings = List[List[float]]

    # Complete type stubs for when ChromaDB is not available
    class Collection:
        """Type stub for Collection when ChromaDB not available"""
        name: str = ""
        metadata: Optional[Dict[str, Any]] = None

        def add(self, documents: List[str], ids: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
            pass

        def query(self, query_texts: List[str], n_results: int = 10,
                  where: Optional[Dict[str, Any]] = None, include: Optional[List[str]] = None) -> Dict[str, Any]:
            return {}

        def get(self, ids: List[str], include: Optional[List[str]] = None) -> Dict[str, Any]:
            return {}

        def update(self, ids: List[str], documents: Optional[List[str]] = None,
                   metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
            pass

        def delete(self, ids: List[str]) -> None:
            pass

        def count(self) -> int:
            return 0


    class EmbeddingFunction:
        """Type stub for EmbeddingFunction when ChromaDB not available"""
        pass

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from .. import get_config
from ..core import SocraticException

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Represents a document stored in the vector database."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """Represents a search result from the vector database."""
    document: VectorDocument
    score: float
    rank: int


@dataclass
class CollectionStats:
    """Statistics for a vector collection."""
    name: str
    count: int
    dimension: Optional[int] = None
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class VectorServiceError(SocraticException):
    """Vector service specific exceptions."""
    pass


class CustomEmbeddingFunction:
    """Custom embedding function using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise VectorServiceError(
                "sentence-transformers package not available. Install with: pip install sentence-transformers")

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info(f"Initialized embedding model: {model_name}")

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input documents."""
        try:
            embeddings = self.model.encode(input, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise VectorServiceError(f"Embedding generation failed: {e}")


class VectorService:
    """
    ChromaDB vector database integration service.

    Provides methods for:
    - Document embedding and storage
    - Similarity search and retrieval
    - Collection management
    - Metadata filtering and querying
    - Knowledge base operations
    """

    def __init__(self):
        self.config = get_config()
        self.vector_config = self.config.get('services', {}).get('vector', {})

        if not CHROMADB_AVAILABLE:
            raise VectorServiceError("ChromaDB package not available. Install with: pip install chromadb")

        # Configuration
        self.data_path = self.vector_config.get('data_path', 'data/vector_db')
        self.embedding_model = self.vector_config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.chunk_size = self.vector_config.get('chunk_size', 1000)
        self.chunk_overlap = self.vector_config.get('chunk_overlap', 200)

        # Ensure data directory exists
        os.makedirs(self.data_path, exist_ok=True)

        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=self.data_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    is_persistent=True
                )
            )

            # Initialize embedding function
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_function = CustomEmbeddingFunction(self.embedding_model)
            else:
                logger.warning("Using ChromaDB default embedding function (sentence-transformers not available)")
                self.embedding_function = None

            logger.info(f"Vector service initialized with data path: {self.data_path}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise VectorServiceError(f"ChromaDB initialization failed: {e}")

    def _generate_document_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID based on content and metadata."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        metadata_hash = hashlib.md5(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        return f"doc_{content_hash[:8]}_{metadata_hash[:8]}"

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If we're not at the end, try to find a good break point
            if end < len(text):
                # Look for sentence boundary
                for i in range(end, max(start + self.chunk_size - 200, start + 1), -1):
                    if text[i - 1] in '.!?':
                        end = i
                        break
                else:
                    # Look for word boundary
                    for i in range(end, max(start + self.chunk_size - 100, start + 1), -1):
                        if text[i].isspace():
                            end = i
                            break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap
            if start <= 0:
                start = end

        return chunks

    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """
        Create a new vector collection.

        Args:
            name: Collection name
            metadata: Optional collection metadata

        Returns:
            ChromaDB Collection object
        """
        try:
            # Delete collection if it exists
            try:
                self.client.delete_collection(name)
                logger.info(f"Deleted existing collection: {name}")
            except Exception:
                pass  # Collection doesn't exist

            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=self.embedding_function
            )

            logger.info(f"Created collection: {name}")
            return collection

        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            raise VectorServiceError(f"Collection creation failed: {e}")

    def get_collection(self, name: str) -> Collection:
        """
        Get an existing collection.

        Args:
            name: Collection name

        Returns:
            ChromaDB Collection object
        """
        try:
            collection = self.client.get_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            return collection

        except Exception as e:
            logger.error(f"Failed to get collection {name}: {e}")
            raise VectorServiceError(f"Collection retrieval failed: {e}")

    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """
        Get existing collection or create if it doesn't exist.

        Args:
            name: Collection name
            metadata: Optional collection metadata

        Returns:
            ChromaDB Collection object
        """
        try:
            return self.get_collection(name)
        except VectorServiceError:
            return self.create_collection(name, metadata)

    def add_document(
            self,
            collection_name: str,
            content: str,
            metadata: Optional[Dict[str, Any]] = None,
            document_id: Optional[str] = None,
            chunk_content: bool = True
    ) -> List[str]:
        """
        Add a document to the vector database.

        Args:
            collection_name: Name of the collection
            content: Document content
            metadata: Document metadata
            document_id: Optional custom document ID
            chunk_content: Whether to chunk large content

        Returns:
            List of added document IDs
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            metadata = metadata or {}

            # Add timestamp to metadata
            metadata['created_at'] = datetime.now().isoformat()
            metadata['content_length'] = len(content)

            # Chunk content if needed
            if chunk_content and len(content) > self.chunk_size:
                chunks = self._chunk_text(content)
                logger.info(f"Chunked document into {len(chunks)} pieces")
            else:
                chunks = [content]

            document_ids = []

            for i, chunk in enumerate(chunks):
                # Generate document ID
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)

                if document_id:
                    chunk_id = f"{document_id}_chunk_{i}" if len(chunks) > 1 else document_id
                else:
                    chunk_id = self._generate_document_id(chunk, chunk_metadata)

                # Add to collection
                collection.add(
                    documents=[chunk],
                    ids=[chunk_id],
                    metadatas=[chunk_metadata]
                )

                document_ids.append(chunk_id)

            logger.info(f"Added document to collection {collection_name}: {len(document_ids)} chunks")
            return document_ids

        except Exception as e:
            logger.error(f"Failed to add document to {collection_name}: {e}")
            raise VectorServiceError(f"Document addition failed: {e}")

    def add_documents_batch(
            self,
            collection_name: str,
            documents: List[Dict[str, Any]],
            chunk_content: bool = True
    ) -> List[str]:
        """
        Add multiple documents to the vector database in batch.

        Args:
            collection_name: Name of the collection
            documents: List of documents with 'content' and optional 'metadata', 'id'
            chunk_content: Whether to chunk large content

        Returns:
            List of all added document IDs
        """
        all_document_ids = []

        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            doc_id = doc.get('id')

            if content:
                ids = self.add_document(
                    collection_name=collection_name,
                    content=content,
                    metadata=metadata,
                    document_id=doc_id,
                    chunk_content=chunk_content
                )
                all_document_ids.extend(ids)

        logger.info(f"Batch added {len(all_document_ids)} document chunks to {collection_name}")
        return all_document_ids

    def search(
            self,
            collection_name: str,
            query: str,
            n_results: int = 10,
            where: Optional[Dict[str, Any]] = None,
            include_metadata: bool = True,
            include_distances: bool = True
    ) -> List[SearchResult]:
        """
        Search for similar documents in the vector database.

        Args:
            collection_name: Name of the collection to search
            query: Search query text
            n_results: Number of results to return
            where: Metadata filter conditions
            include_metadata: Whether to include metadata in results
            include_distances: Whether to include similarity scores

        Returns:
            List of SearchResult objects
        """
        try:
            collection = self.get_collection(collection_name)

            # Perform search
            include = ["documents"]
            if include_metadata:
                include.append("metadatas")
            if include_distances:
                include.append("distances")

            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=include
            )

            # Format results
            search_results = []
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0] if include_metadata else [{}] * len(documents)
            distances = results.get('distances', [[]])[0] if include_distances else [0.0] * len(documents)
            ids = results.get('ids', [[]])[0]

            for i, (doc_id, content, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                vector_doc = VectorDocument(
                    id=doc_id,
                    content=content,
                    metadata=metadata or {},
                    created_at=datetime.fromisoformat(metadata.get('created_at')) if metadata and metadata.get(
                        'created_at') else None
                )

                # Convert distance to similarity score (1 - distance for cosine similarity)
                score = max(0.0, 1.0 - distance) if include_distances else 1.0

                search_results.append(SearchResult(
                    document=vector_doc,
                    score=score,
                    rank=i + 1
                ))

            logger.info(f"Search in {collection_name} returned {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            raise VectorServiceError(f"Search operation failed: {e}")

    def get_document(self, collection_name: str, document_id: str) -> Optional[VectorDocument]:
        """
        Retrieve a specific document by ID.

        Args:
            collection_name: Name of the collection
            document_id: Document ID to retrieve

        Returns:
            VectorDocument if found, None otherwise
        """
        try:
            collection = self.get_collection(collection_name)

            results = collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )

            if not results['ids'] or not results['ids'][0]:
                return None

            doc_id = results['ids'][0]
            content = results['documents'][0]
            metadata = results['metadatas'][0] or {}

            return VectorDocument(
                id=doc_id,
                content=content,
                metadata=metadata,
                created_at=datetime.fromisoformat(metadata.get('created_at')) if metadata.get('created_at') else None
            )

        except Exception as e:
            logger.error(f"Failed to get document {document_id} from {collection_name}: {e}")
            raise VectorServiceError(f"Document retrieval failed: {e}")

    def update_document(
            self,
            collection_name: str,
            document_id: str,
            content: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document in the vector database.

        Args:
            collection_name: Name of the collection
            document_id: Document ID to update
            content: New content (optional)
            metadata: New metadata (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_collection(collection_name)

            # Get current document
            current_doc = self.get_document(collection_name, document_id)
            if not current_doc:
                logger.warning(f"Document {document_id} not found in {collection_name}")
                return False

            # Prepare update data
            update_data = {}

            if content is not None:
                update_data['documents'] = [content]

            if metadata is not None:
                # Merge with existing metadata
                updated_metadata = current_doc.metadata.copy()
                updated_metadata.update(metadata)
                updated_metadata['updated_at'] = datetime.now().isoformat()
                update_data['metadatas'] = [updated_metadata]

            # Update document
            collection.update(
                ids=[document_id],
                **update_data
            )

            logger.info(f"Updated document {document_id} in {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update document {document_id} in {collection_name}: {e}")
            raise VectorServiceError(f"Document update failed: {e}")

    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Delete a document from the vector database.

        Args:
            collection_name: Name of the collection
            document_id: Document ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_collection(collection_name)
            collection.delete(ids=[document_id])

            logger.info(f"Deleted document {document_id} from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from {collection_name}: {e}")
            return False

    def list_collections(self) -> List[CollectionStats]:
        """
        List all collections and their statistics.

        Returns:
            List of CollectionStats objects
        """
        try:
            collections = self.client.list_collections()
            stats = []

            for collection in collections:
                try:
                    count = collection.count()
                    metadata = collection.metadata or {}

                    stats.append(CollectionStats(
                        name=collection.name,
                        count=count,
                        created_at=datetime.fromisoformat(metadata.get('created_at')) if metadata.get(
                            'created_at') else None
                    ))
                except Exception as e:
                    logger.warning(f"Could not get stats for collection {collection.name}: {e}")
                    stats.append(CollectionStats(
                        name=collection.name,
                        count=0
                    ))

            return stats

        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise VectorServiceError(f"Collection listing failed: {e}")

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: Collection name to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            return False

    def get_collection_stats(self, name: str) -> Optional[CollectionStats]:
        """
        Get statistics for a specific collection.

        Args:
            name: Collection name

        Returns:
            CollectionStats if successful, None otherwise
        """
        try:
            collection = self.get_collection(name)
            count = collection.count()
            metadata = collection.metadata or {}

            return CollectionStats(
                name=name,
                count=count,
                created_at=datetime.fromisoformat(metadata.get('created_at')) if metadata.get('created_at') else None,
                last_updated=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to get stats for collection {name}: {e}")
            return None

    def health_check(self) -> Dict[str, Any]:
        """Check vector service health and connectivity."""
        try:
            # Test basic operations
            collections = self.client.list_collections()

            return {
                "status": "healthy",
                "data_path": self.data_path,
                "embedding_model": self.embedding_model,
                "collections_count": len(collections),
                "chromadb_available": CHROMADB_AVAILABLE,
                "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Vector service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "data_path": self.data_path,
                "chromadb_available": CHROMADB_AVAILABLE,
                "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
                "last_check": datetime.now().isoformat()
            }
