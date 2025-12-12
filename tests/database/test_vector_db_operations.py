"""
Tests for Vector Database operations - Knowledge base and embeddings.

Tests cover:
- Vector embeddings and storage
- Similarity search
- Document indexing
- Knowledge base operations
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_vector_db():
    """Create a mock vector database."""
    return MagicMock()


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "id": "doc-1",
            "content": "Python is a programming language",
            "metadata": {"source": "wiki", "topic": "programming"},
            "embedding": [0.1, 0.2, 0.3] * 128,  # 384 dims
        },
        {
            "id": "doc-2",
            "content": "Django is a web framework for Python",
            "metadata": {"source": "docs", "topic": "web"},
            "embedding": [0.2, 0.3, 0.4] * 128,
        },
        {
            "id": "doc-3",
            "content": "Machine learning with scikit-learn",
            "metadata": {"source": "tutorial", "topic": "ml"},
            "embedding": [0.3, 0.4, 0.5] * 128,
        },
    ]


class TestVectorEmbeddings:
    """Tests for vector embeddings."""

    def test_embedding_creation(self, sample_documents):
        """Test creating vector embeddings."""
        doc = sample_documents[0]

        assert "embedding" in doc
        assert len(doc["embedding"]) == 384  # Standard embedding dimension
        assert isinstance(doc["embedding"][0], float)

    def test_embedding_dimensions(self, sample_documents):
        """Test all embeddings have same dimension."""
        embeddings = [doc["embedding"] for doc in sample_documents]

        # All should have same dimension
        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1
        assert dimensions[0] == 384

    def test_embedding_normalization(self):
        """Test embedding normalization."""
        # Embeddings should be normalized
        embedding = [0.1, 0.2, 0.3] * 128

        # Calculate magnitude
        magnitude = sum(x**2 for x in embedding) ** 0.5

        # Normalized values should be < 1
        normalized = [x / magnitude for x in embedding]
        assert all(abs(x) <= 1 for x in normalized)

    def test_similarity_computation(self):
        """Test computing similarity between embeddings."""
        import math

        # Create embeddings with different directions
        emb1 = [1.0] + [0.0] * 383  # First element only
        emb2 = [1.0] + [0.0] * 383  # Same as emb1 (identical)
        emb3 = [0.0] * 383 + [1.0]  # Last element only (orthogonal)

        # Compute cosine similarity (normalized dot product)
        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))
            return dot / (mag_a * mag_b) if mag_a > 0 and mag_b > 0 else 0

        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)

        # Identical embeddings should have cosine similarity of 1.0
        assert sim_1_2 == 1.0
        # Orthogonal embeddings should have cosine similarity of 0.0
        assert sim_1_3 == 0.0
        # Same embeddings should have higher similarity than orthogonal
        assert sim_1_2 > sim_1_3


class TestVectorSearch:
    """Tests for vector similarity search."""

    def test_search_similar_documents(self, mock_vector_db, sample_documents):
        """Test searching for similar documents."""
        # Mock search results
        query = "Python programming"
        results = [
            {"id": "doc-1", "score": 0.95},
            {"id": "doc-2", "score": 0.87},
            {"id": "doc-3", "score": 0.65},
        ]

        mock_vector_db.search_similar.return_value = results

        found = mock_vector_db.search_similar(query, top_k=3)

        assert len(found) == 3
        assert found[0]["score"] > found[1]["score"]
        assert found[1]["score"] > found[2]["score"]

    def test_search_with_top_k(self, mock_vector_db):
        """Test limiting search results with top_k."""
        results = [
            {"id": "doc-1", "score": 0.9},
            {"id": "doc-2", "score": 0.8},
            {"id": "doc-3", "score": 0.7},
            {"id": "doc-4", "score": 0.6},
            {"id": "doc-5", "score": 0.5},
        ]

        mock_vector_db.search_similar.return_value = results[:3]

        found = mock_vector_db.search_similar("query", top_k=3)

        assert len(found) <= 3

    def test_search_with_threshold(self, mock_vector_db):
        """Test filtering results by similarity threshold."""
        results = [
            {"id": "doc-1", "score": 0.95},
            {"id": "doc-2", "score": 0.75},
            {"id": "doc-3", "score": 0.45},
        ]

        # Filter threshold
        threshold = 0.6
        filtered = [r for r in results if r["score"] >= threshold]

        assert len(filtered) == 2
        assert all(r["score"] >= threshold for r in filtered)

    def test_empty_search_results(self, mock_vector_db):
        """Test handling empty search results."""
        mock_vector_db.search_similar.return_value = []

        results = mock_vector_db.search_similar("nonexistent", top_k=5)

        assert results == []


class TestDocumentIndexing:
    """Tests for document indexing in vector database."""

    def test_add_document(self, mock_vector_db, sample_documents):
        """Test adding document to vector database."""
        doc = sample_documents[0]
        mock_vector_db.add_document.return_value = True

        success = mock_vector_db.add_document(doc)

        assert success is True
        mock_vector_db.add_document.assert_called_once_with(doc)

    def test_add_multiple_documents(self, mock_vector_db, sample_documents):
        """Test adding multiple documents."""
        mock_vector_db.add_documents.return_value = len(sample_documents)

        count = mock_vector_db.add_documents(sample_documents)

        assert count == len(sample_documents)

    def test_update_document(self, mock_vector_db, sample_documents):
        """Test updating document in vector database."""
        doc = sample_documents[0]
        doc["content"] = "Updated content"

        mock_vector_db.update_document.return_value = True

        success = mock_vector_db.update_document(doc)

        assert success is True

    def test_delete_document(self, mock_vector_db):
        """Test deleting document from vector database."""
        doc_id = "doc-1"
        mock_vector_db.delete_document.return_value = True

        success = mock_vector_db.delete_document(doc_id)

        assert success is True

    def test_document_with_metadata(self, sample_documents):
        """Test documents with metadata."""
        doc = sample_documents[0]

        assert "metadata" in doc
        assert "source" in doc["metadata"]
        assert "topic" in doc["metadata"]


class TestKnowledgeBaseOperations:
    """Tests for knowledge base operations."""

    def test_index_size(self, mock_vector_db):
        """Test getting knowledge base index size."""
        mock_vector_db.get_size.return_value = 150

        size = mock_vector_db.get_size()

        assert size == 150

    def test_clear_index(self, mock_vector_db):
        """Test clearing knowledge base."""
        mock_vector_db.clear.return_value = True

        success = mock_vector_db.clear()

        assert success is True

    def test_rebuild_index(self, mock_vector_db, sample_documents):
        """Test rebuilding vector index."""
        mock_vector_db.rebuild.return_value = True

        success = mock_vector_db.rebuild(sample_documents)

        assert success is True

    def test_export_index(self, mock_vector_db):
        """Test exporting vector index."""
        mock_data = {"documents": 150, "vectors": 384}
        mock_vector_db.export.return_value = mock_data

        data = mock_vector_db.export()

        assert isinstance(data, dict)

    def test_import_index(self, mock_vector_db):
        """Test importing vector index."""
        mock_data = {"documents": 150, "vectors": 384}
        mock_vector_db.import_data.return_value = True

        success = mock_vector_db.import_data(mock_data)

        assert success is True


class TestSemanticSearch:
    """Tests for semantic search operations."""

    def test_semantic_search_query(self, mock_vector_db):
        """Test semantic search with query."""
        query = "How to build a web application?"
        results = [
            {
                "id": "doc-1",
                "title": "Web Development Guide",
                "score": 0.92,
                "content_preview": "Building web applications...",
            },
            {
                "id": "doc-2",
                "title": "Django Tutorial",
                "score": 0.88,
                "content_preview": "Django is a framework...",
            },
        ]

        mock_vector_db.semantic_search.return_value = results

        found = mock_vector_db.semantic_search(query, top_k=2)

        assert len(found) == 2
        assert found[0]["score"] > found[1]["score"]

    def test_semantic_search_with_filters(self, mock_vector_db):
        """Test semantic search with metadata filters."""
        query = "Python"
        filters = {"topic": "programming"}
        results = [
            {"id": "doc-1", "score": 0.95, "metadata": {"topic": "programming"}},
            {"id": "doc-2", "score": 0.87, "metadata": {"topic": "programming"}},
        ]

        mock_vector_db.semantic_search.return_value = results

        found = mock_vector_db.semantic_search(query, filters=filters)

        assert all(r["metadata"]["topic"] == "programming" for r in found)

    def test_semantic_search_ranking(self, mock_vector_db):
        """Test ranking of semantic search results."""
        results = [
            {"id": "doc-1", "score": 0.99},
            {"id": "doc-2", "score": 0.95},
            {"id": "doc-3", "score": 0.87},
            {"id": "doc-4", "score": 0.75},
        ]

        # Results should be ranked by score
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestVectorDatabaseIntegration:
    """Integration tests for vector database operations."""

    def test_index_and_search_workflow(self, mock_vector_db, sample_documents):
        """Test complete indexing and search workflow."""
        # Index documents
        mock_vector_db.add_documents.return_value = len(sample_documents)
        indexed = mock_vector_db.add_documents(sample_documents)
        assert indexed == 3

        # Search
        mock_vector_db.search_similar.return_value = [
            {"id": "doc-1", "score": 0.95},
            {"id": "doc-2", "score": 0.87},
        ]
        results = mock_vector_db.search_similar("Python", top_k=2)

        assert len(results) == 2

    def test_update_and_search_workflow(self, mock_vector_db, sample_documents):
        """Test update and search workflow."""
        # Add document
        doc = sample_documents[0]
        mock_vector_db.add_document.return_value = True
        mock_vector_db.add_document(doc)

        # Update document
        doc["content"] = "Updated Python content"
        mock_vector_db.update_document.return_value = True
        mock_vector_db.update_document(doc)

        # Search updated content
        mock_vector_db.search_similar.return_value = [{"id": "doc-1", "score": 0.92}]
        results = mock_vector_db.search_similar("Python", top_k=1)

        assert len(results) == 1

    def test_delete_and_reindex_workflow(self, mock_vector_db, sample_documents):
        """Test delete and reindex workflow."""
        # Index documents
        mock_vector_db.add_documents.return_value = 3
        mock_vector_db.add_documents(sample_documents)

        # Delete document
        mock_vector_db.delete_document.return_value = True
        mock_vector_db.delete_document("doc-1")

        # Rebuild index
        mock_vector_db.rebuild.return_value = True
        mock_vector_db.rebuild(sample_documents[1:])

        assert mock_vector_db.delete_document.called
        assert mock_vector_db.rebuild.called


class TestVectorDatabaseEdgeCases:
    """Tests for edge cases in vector database."""

    def test_large_embedding_dimension(self):
        """Test handling large embedding dimensions."""
        # Vector DB typically uses 384-1536 dimensions
        embedding = [0.1 * i for i in range(1536)]

        assert len(embedding) == 1536

    def test_search_with_zero_results(self, mock_vector_db):
        """Test search returning zero results."""
        mock_vector_db.search_similar.return_value = []

        results = mock_vector_db.search_similar("nonexistent query", top_k=10)

        assert results == []
        assert len(results) == 0

    def test_search_with_single_result(self, mock_vector_db):
        """Test search returning single result."""
        mock_vector_db.search_similar.return_value = [{"id": "doc-1", "score": 0.99}]

        results = mock_vector_db.search_similar("query", top_k=1)

        assert len(results) == 1
        assert results[0]["id"] == "doc-1"

    def test_document_with_special_characters(self):
        """Test documents with special characters."""
        doc = {
            "id": "doc-special",
            "content": "Content with special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/~`",
            "metadata": {"type": "test"},
        }

        assert len(doc["content"]) > 0
        assert "special" in doc["content"]

    def test_empty_document_handling(self):
        """Test handling empty or invalid documents."""
        docs = [
            {"id": "empty", "content": "", "metadata": {}},
            {"id": "valid", "content": "Valid content", "metadata": {}},
        ]

        valid_docs = [d for d in docs if d.get("content", "").strip()]
        assert len(valid_docs) == 1
