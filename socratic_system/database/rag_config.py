"""
RAG Configuration Module - Unified configuration for Retrieval-Augmented Generation

Supports multiple vector store backends (ChromaDB, FAISS, Qdrant, Pinecone)
and configurable embedding models.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class VectorStoreBackend(Enum):
    """Supported vector store backends"""

    CHROMADB = "chromadb"  # Default, local persistent storage
    FAISS = "faiss"  # Facebook AI Similarity Search (in-memory)
    QDRANT = "qdrant"  # Open-source vector DB
    PINECONE = "pinecone"  # Managed vector DB (cloud)


class EmbeddingModel(Enum):
    """Supported embedding models"""

    ALL_MINILM_L6_V2 = "all-MiniLM-L6-v2"  # Default: fast, 384 dims
    ALL_MPNET_BASE_V2 = "all-mpnet-base-v2"  # Better quality, 768 dims
    BERT_BASE_UNCASED = "bert-base-uncased"  # Traditional BERT
    SENTENCE_TRANSFORMERS = "sentence-transformers/multi-qa-mpnet-base-dot-v1"  # QA specific
    OPENAI = "openai"  # OpenAI embeddings API
    COHERE = "cohere"  # Cohere embeddings API
    HUGGINGFACE = "huggingface"  # Custom HuggingFace models


@dataclass
class RAGConfig:
    """Configuration for RAG system"""

    # Vector store configuration
    vector_store: VectorStoreBackend = VectorStoreBackend.CHROMADB
    vector_store_path: str = field(default_factory=lambda: os.getenv("RAG_DATA_DIR", "./rag_data"))
    collection_name: str = "socratic_knowledge"

    # Embedding configuration
    embedding_model: EmbeddingModel = EmbeddingModel.ALL_MINILM_L6_V2
    embedding_cache_enabled: bool = True
    embedding_cache_size: int = 10000
    embedding_cache_ttl: int = 3600  # seconds

    # Chunking configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunking_strategy: str = "fixed"  # or "semantic"

    # Search configuration
    default_top_k: int = 5
    similarity_threshold: float = 0.0
    search_timeout: int = 30  # seconds

    # External service credentials
    pinecone_api_key: Optional[str] = field(default_factory=lambda: os.getenv("PINECONE_API_KEY"))
    pinecone_environment: Optional[str] = field(default_factory=lambda: os.getenv("PINECONE_ENVIRONMENT"))
    qdrant_url: Optional[str] = field(default_factory=lambda: os.getenv("QDRANT_URL"))
    qdrant_api_key: Optional[str] = field(default_factory=lambda: os.getenv("QDRANT_API_KEY"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    cohere_api_key: Optional[str] = field(default_factory=lambda: os.getenv("COHERE_API_KEY"))

    # Feature flags
    enable_reranking: bool = True
    enable_metadata_filtering: bool = True
    enable_hybrid_search: bool = False  # Combine semantic + keyword search

    def validate(self) -> tuple[bool, str]:
        """
        Validate RAG configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate vector store configuration
        if self.vector_store == VectorStoreBackend.PINECONE:
            if not self.pinecone_api_key or not self.pinecone_environment:
                return False, "Pinecone requires PINECONE_API_KEY and PINECONE_ENVIRONMENT"

        elif self.vector_store == VectorStoreBackend.QDRANT:
            if not self.qdrant_url:
                return False, "Qdrant requires QDRANT_URL"

        # Validate embedding model configuration
        if self.embedding_model == EmbeddingModel.OPENAI:
            if not self.openai_api_key:
                return False, "OpenAI embeddings require OPENAI_API_KEY"

        elif self.embedding_model == EmbeddingModel.COHERE:
            if not self.cohere_api_key:
                return False, "Cohere embeddings require COHERE_API_KEY"

        # Validate chunk sizes
        if self.chunk_size < 100:
            return False, "chunk_size must be at least 100"

        if self.chunk_overlap >= self.chunk_size:
            return False, "chunk_overlap must be less than chunk_size"

        if self.default_top_k < 1:
            return False, "default_top_k must be at least 1"

        if not 0.0 <= self.similarity_threshold <= 1.0:
            return False, "similarity_threshold must be between 0.0 and 1.0"

        return True, ""

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "vector_store": self.vector_store.value,
            "vector_store_path": self.vector_store_path,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model.value,
            "embedding_cache_enabled": self.embedding_cache_enabled,
            "embedding_cache_size": self.embedding_cache_size,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "default_top_k": self.default_top_k,
            "similarity_threshold": self.similarity_threshold,
            "enable_reranking": self.enable_reranking,
            "enable_metadata_filtering": self.enable_metadata_filtering,
            "enable_hybrid_search": self.enable_hybrid_search,
        }


class RAGConfigBuilder:
    """Builder for RAG configuration"""

    def __init__(self):
        """Initialize config builder with defaults"""
        self.config = RAGConfig()

    def with_vector_store(self, backend: VectorStoreBackend, path: Optional[str] = None) -> "RAGConfigBuilder":
        """Set vector store backend"""
        self.config.vector_store = backend
        if path:
            self.config.vector_store_path = path
        return self

    def with_embedding_model(self, model: EmbeddingModel) -> "RAGConfigBuilder":
        """Set embedding model"""
        self.config.embedding_model = model
        return self

    def with_chunk_size(self, size: int, overlap: int = 50) -> "RAGConfigBuilder":
        """Set chunk configuration"""
        self.config.chunk_size = size
        self.config.chunk_overlap = overlap
        return self

    def with_search_config(self, top_k: int, threshold: float = 0.0) -> "RAGConfigBuilder":
        """Set search configuration"""
        self.config.default_top_k = top_k
        self.config.similarity_threshold = threshold
        return self

    def with_cache(self, enabled: bool, size: int = 10000, ttl: int = 3600) -> "RAGConfigBuilder":
        """Configure embedding cache"""
        self.config.embedding_cache_enabled = enabled
        self.config.embedding_cache_size = size
        self.config.embedding_cache_ttl = ttl
        return self

    def enable_reranking(self, enabled: bool = True) -> "RAGConfigBuilder":
        """Enable/disable result reranking"""
        self.config.enable_reranking = enabled
        return self

    def enable_hybrid_search(self, enabled: bool = True) -> "RAGConfigBuilder":
        """Enable/disable hybrid search"""
        self.config.enable_hybrid_search = enabled
        return self

    def build(self) -> RAGConfig:
        """Build and validate configuration"""
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid RAG configuration: {error_msg}")

        logger.info(f"RAG configuration built: {self.config.vector_store.value} backend")
        return self.config


# Default configurations for common use cases
def get_default_config() -> RAGConfig:
    """Get default RAG configuration (ChromaDB + all-MiniLM-L6-v2)"""
    return RAGConfig()


def get_production_config() -> RAGConfig:
    """Get production RAG configuration (Qdrant + mpnet)"""
    return (
        RAGConfigBuilder()
        .with_vector_store(VectorStoreBackend.QDRANT)
        .with_embedding_model(EmbeddingModel.ALL_MPNET_BASE_V2)
        .with_cache(True, size=50000, ttl=7200)
        .enable_reranking(True)
        .build()
    )


def get_local_config() -> RAGConfig:
    """Get local development configuration (FAISS)"""
    return (
        RAGConfigBuilder()
        .with_vector_store(VectorStoreBackend.FAISS)
        .with_embedding_model(EmbeddingModel.ALL_MINILM_L6_V2)
        .with_cache(True)
        .build()
    )


def get_cloud_config() -> RAGConfig:
    """Get cloud configuration (Pinecone + OpenAI embeddings)"""
    return (
        RAGConfigBuilder()
        .with_vector_store(VectorStoreBackend.PINECONE)
        .with_embedding_model(EmbeddingModel.OPENAI)
        .with_cache(True, size=5000)
        .enable_reranking(True)
        .build()
    )
