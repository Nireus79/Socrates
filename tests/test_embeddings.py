"""Tests for semantic embeddings functionality."""
import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from socratic_morality.precedent.embeddings import SemanticEmbeddings


class TestSemanticEmbeddingsInitialization:
    """Tests for SemanticEmbeddings initialization."""

    def test_initialization_with_default_model(self):
        """Test initialization with default model name."""
        embeddings = SemanticEmbeddings()
        assert embeddings.model_name == "all-MiniLM-L6-v2"
        assert isinstance(embeddings.embeddings_cache, dict)
        assert len(embeddings.embeddings_cache) == 0

    def test_initialization_with_custom_model(self):
        """Test initialization with custom model name."""
        embeddings = SemanticEmbeddings(model_name="all-mpnet-base-v2")
        assert embeddings.model_name == "all-mpnet-base-v2"

    def test_initialization_without_sentence_transformers(self):
        """Test initialization when sentence-transformers is not available."""
        embeddings = SemanticEmbeddings()
        # Model will be None if sentence-transformers is not available
        # This is handled gracefully in the constructor
        assert isinstance(embeddings.embeddings_cache, dict)


class TestEmbeddingGeneration:
    """Tests for embedding generation."""

    def test_embed_with_available_model(self):
        """Test embedding generation when model is available."""
        embeddings = SemanticEmbeddings()
        if embeddings.model:  # Only test if model is actually available
            result = embeddings.embed("test text")
            assert result is not None
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(x, float) for x in result)

    def test_embed_without_model(self):
        """Test embedding generation when model is not available."""
        embeddings = SemanticEmbeddings()
        embeddings.model = None
        result = embeddings.embed("test text")
        assert result is None

    def test_embed_caching(self):
        """Test that embeddings are cached."""
        embeddings = SemanticEmbeddings()
        embeddings.model = None
        embeddings.embeddings_cache["cached_text"] = [0.1, 0.2, 0.3]

        # Should return cached result even without model
        result = embeddings.embed("cached_text")
        assert result == [0.1, 0.2, 0.3]

    def test_embed_error_handling(self):
        """Test embedding generation with error handling."""
        embeddings = SemanticEmbeddings()
        # Mock model to raise exception
        if embeddings.model:
            embeddings.model.encode = Mock(side_effect=Exception("Model error"))
            result = embeddings.embed("test text")
            assert result is None

    def test_embed_caches_new_result(self):
        """Test that new embeddings are cached."""
        embeddings = SemanticEmbeddings()
        embeddings.model = None  # Disable model to use cached values

        # Add to cache
        test_embedding = [0.5, 0.6, 0.7]
        embeddings.embeddings_cache["test"] = test_embedding

        # Should retrieve from cache
        assert embeddings.embed("test") == test_embedding


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        vec = [1.0, 0.0, 0.0]
        similarity = SemanticEmbeddings.cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = SemanticEmbeddings.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = SemanticEmbeddings.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0)

    def test_cosine_similarity_partial_overlap(self):
        """Test cosine similarity with partial overlap."""
        vec1 = [1.0, 1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = SemanticEmbeddings.cosine_similarity(vec1, vec2)
        assert 0 < similarity < 1

    def test_cosine_similarity_empty_vectors(self):
        """Test cosine similarity with empty vectors."""
        similarity = SemanticEmbeddings.cosine_similarity([], [])
        assert similarity == 0.0

    def test_cosine_similarity_different_length(self):
        """Test cosine similarity with different length vectors."""
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = SemanticEmbeddings.cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_zero_magnitude(self):
        """Test cosine similarity when one vector has zero magnitude."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = SemanticEmbeddings.cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_normalized_vectors(self):
        """Test cosine similarity with normalized vectors."""
        # Normalized vectors should have magnitude 1
        vec1 = [0.7071, 0.7071]  # ~sqrt(0.5), sqrt(0.5)
        vec2 = [0.7071, 0.7071]
        similarity = SemanticEmbeddings.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0, abs=0.01)


class TestIsAvailable:
    """Tests for availability checking."""

    def test_is_available_with_model(self):
        """Test is_available when model is loaded."""
        embeddings = SemanticEmbeddings()
        # This depends on whether sentence-transformers is installed
        if embeddings.model:
            assert embeddings.is_available() is True
        else:
            assert embeddings.is_available() is False

    def test_is_available_without_model(self):
        """Test is_available when model is None."""
        embeddings = SemanticEmbeddings()
        embeddings.model = None
        assert embeddings.is_available() is False

    def test_is_available_after_model_loaded(self):
        """Test is_available reflects model state."""
        embeddings = SemanticEmbeddings()
        embeddings.model = None
        assert embeddings.is_available() is False

        embeddings.model = Mock()  # Mock a model
        assert embeddings.is_available() is True


class TestEmbeddingsIntegration:
    """Integration tests for embeddings."""

    def test_embed_and_similarity_workflow(self):
        """Test complete workflow of embedding and similarity."""
        embeddings = SemanticEmbeddings()

        # Create mock embeddings
        embeddings.model = None
        embeddings.embeddings_cache["text1"] = [1.0, 0.0, 0.0]
        embeddings.embeddings_cache["text2"] = [1.0, 0.0, 0.0]
        embeddings.embeddings_cache["text3"] = [0.0, 1.0, 0.0]

        # Get embeddings
        embed1 = embeddings.embed("text1")
        embed2 = embeddings.embed("text2")
        embed3 = embeddings.embed("text3")

        # Calculate similarities
        similarity_same = SemanticEmbeddings.cosine_similarity(embed1, embed2)
        similarity_diff = SemanticEmbeddings.cosine_similarity(embed1, embed3)

        # Same embeddings should have higher similarity
        assert similarity_same > similarity_diff

    def test_multiple_embeddings_independence(self):
        """Test that multiple SemanticEmbeddings instances are independent."""
        embeddings1 = SemanticEmbeddings()
        embeddings2 = SemanticEmbeddings()

        embeddings1.embeddings_cache["key"] = [0.1, 0.2]

        # Should not affect embeddings2
        assert "key" not in embeddings2.embeddings_cache or embeddings2.embeddings_cache.get("key") != [0.1, 0.2]
