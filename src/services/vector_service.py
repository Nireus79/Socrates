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
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

# ============================================================================
# CHROMADB IMPORTS - Only import the main module, not types
# ============================================================================

# Define type aliases at module level (always available)
Documents = List[str]
Embeddings = List[List[float]]

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None  # type: ignore[assignment]


# ============================================================================
# FALLBACK TYPE DEFINITIONS - Always defined, used when ChromaDB unavailable
# ============================================================================

class Settings:
    """Settings for ChromaDB configuration"""

    def __init__(self, **kwargs: Any):
        self.anonymized_telemetry = kwargs.get('anonymized_telemetry', False)
        self.is_persistent = kwargs.get('is_persistent', True)
        self.chroma_db_impl = kwargs.get('chroma_db_impl', 'duckdb+parquet')
        self.persist_directory = kwargs.get('persist_directory', '')


# Fallback Collection class
class Collection:
    """Collection interface for vector database operations"""

    def __init__(self, name: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.metadata = metadata or {}

    def add(
            self,
            documents: List[str],
            ids: List[str],
            metadatas: Optional[List[Dict[str, Any]]] = None,
            embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """Add documents to collection"""
        pass

    def query(
            self,
            query_texts: Optional[List[str]] = None,
            query_embeddings: Optional[List[List[float]]] = None,
            n_results: int = 10,
            where: Optional[Dict[str, Any]] = None,
            include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Query collection for similar documents"""
        return {
            'ids': [],
            'distances': [],
            'metadatas': [],
            'documents': [],
            'embeddings': []
        }

    def get(
            self,
            ids: Optional[List[str]] = None,
            where: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get documents from collection"""
        return {
            'ids': [],
            'metadatas': [],
            'documents': [],
            'embeddings': []
        }

    def update(
            self,
            ids: List[str],
            documents: Optional[List[str]] = None,
            metadatas: Optional[List[Dict[str, Any]]] = None,
            embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """Update documents in collection"""
        pass

    def delete(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> None:
        """Delete documents from collection"""
        pass

    def count(self) -> int:
        """Get count of documents in collection"""
        return 0

    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """Peek at documents in collection"""
        return {
            'ids': [],
            'metadatas': [],
            'documents': [],
            'embeddings': []
        }


# Fallback EmbeddingFunction class
class EmbeddingFunction:
    """Base class for embedding functions"""

    def __init__(self) -> None:
        pass

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input documents"""
        # Return empty embeddings of appropriate shape
        return [[0.0] * 384 for _ in input]  # 384 is common embedding dimension


# ============================================================================
# SENTENCE TRANSFORMERS IMPORTS WITH FALLBACK
# ============================================================================

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


    # Fallback SentenceTransformer class
    class SentenceTransformer:
        """Fallback SentenceTransformer when library not available"""

        def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
            self.model_name = model_name
            logging.warning(
                f"SentenceTransformer not available. Install with: pip install sentence-transformers"
            )

        def encode(self, sentences, convert_to_tensor=False, **kwargs):
            """Fallback encode method"""
            # Return dummy embeddings
            import numpy as np
            if isinstance(sentences, str):
                sentences = [sentences]
            # Return array of zeros with shape (n_sentences, 384)
            embeddings = np.zeros((len(sentences), 384))
            if convert_to_tensor:
                try:
                    import torch
                    return torch.from_numpy(embeddings)
                except ImportError:
                    return embeddings
            return embeddings

# ============================================================================
# CORE IMPORTS
# ============================================================================

try:
    from ..core import SocraticException

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


    # Fallback exception class
    class SocraticException(Exception):
        """Fallback base exception"""
        pass

# ============================================================================
# MODULE LOGGER
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

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


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class VectorServiceError(SocraticException):
    """Vector service specific exceptions."""
    pass


# ============================================================================
# CUSTOM EMBEDDING FUNCTION
# ============================================================================

class CustomEmbeddingFunction:
    """Custom embedding function using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning(
                "sentence-transformers package not available. "
                "Install with: pip install sentence-transformers. "
                "Using fallback embeddings."
            )
            self.model = SentenceTransformer(model_name)  # Will use fallback
        else:
            self.model = SentenceTransformer(model_name)

        self.model_name = model_name
        logger.info(f"Initialized embedding model: {model_name}")

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input documents."""
        try:
            embeddings = self.model.encode(input, convert_to_tensor=False)

            # Convert to list format
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            elif isinstance(embeddings, list):
                return embeddings
            else:
                # Assume numpy array
                return embeddings.tolist()

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise VectorServiceError(f"Embedding generation failed: {e}")


# ============================================================================
# VECTOR SERVICE CLASS
# ============================================================================

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
        # Lazy load config to avoid circular imports
        try:
            from src import get_config
            self.config = get_config()
        except (ImportError, AttributeError):
            self.config = None

        self.vector_config = self.config.get('services', {}).get('vector', {}) if self.config else {}

        if not CHROMADB_AVAILABLE:
            logger.warning(
                "ChromaDB package not available. "
                "Install with: pip install chromadb. "
                "Vector service will operate in limited mode."
            )
            # Don't raise error, allow graceful degradation
            self.client = None
            self.embedding_function = None
            return

        # Configuration
        self.data_path = self.vector_config.get('data_path', 'data/vector_db')
        self.embedding_model = self.vector_config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.chunk_size = self.vector_config.get('chunk_size', 1000)
        self.chunk_overlap = self.vector_config.get('chunk_overlap', 200)

        # Ensure data directory exists
        os.makedirs(self.data_path, exist_ok=True)

        # Initialize ChromaDB client
        try:
            # Use chromadb's Settings if available, otherwise use our fallback
            if CHROMADB_AVAILABLE and chromadb is not None:
                # Access Settings from chromadb.config dynamically
                ChromaSettings = chromadb.config.Settings
                self.client = chromadb.PersistentClient(
                    path=self.data_path,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        is_persistent=True
                    )
                )
            else:
                # ChromaDB not available, use fallback
                self.client = None
                logger.warning("ChromaDB not available - using fallback mode")
                return

            # Initialize embedding function
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_function = CustomEmbeddingFunction(self.embedding_model)
            else:
                logger.warning("Using ChromaDB default embedding function (sentence-transformers not available)")
                self.embedding_function = None

            logger.info(f"Vector service initialized with data path: {self.data_path}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            self.client = None
            self.embedding_function = None
            logger.warning("Vector service operating in limited mode")
