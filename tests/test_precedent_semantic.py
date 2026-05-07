"""Tests for semantic similarity in precedent engine."""

from unittest.mock import Mock

import pytest
from socratic_morality.precedent.engine import MoralPrecedentEngine


class TestPrecedentSemanticSimilarity:
    """Tests for semantic similarity search in precedent engine."""

    @pytest.fixture
    def precedent_engine(self):
        """Create precedent engine for testing."""
        return MoralPrecedentEngine()

    @pytest.mark.asyncio
    async def test_find_similar_cases_with_embeddings(self, precedent_engine):
        """Test finding similar cases using semantic embeddings."""
        # Store some cases
        decision1 = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor1"
        )
        decision2 = Mock(
            decision_type="deny", allowed=False, context={}, high_impact=False, actor="actor2"
        )

        await precedent_engine.store_case(
            action="user asks for sensitive data access",
            decision=decision1,
            reasoning="User has authorization",
        )
        await precedent_engine.store_case(
            action="unauthorized data request",
            decision=decision2,
            reasoning="No proper authorization",
        )

        # Enable mock embeddings for semantic similarity
        if precedent_engine.embeddings.model:
            # Real embeddings available
            similar_cases = await precedent_engine.find_similar_cases("user requests data", limit=2)
            assert len(similar_cases) > 0
            assert "similarity_score" in similar_cases[0]

    @pytest.mark.asyncio
    async def test_find_similar_cases_fallback_word_overlap(self, precedent_engine):
        """Test finding similar cases using fallback word overlap."""
        # Disable embeddings
        precedent_engine.embeddings.model = None

        # Store cases with overlapping words
        decision1 = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor1"
        )
        decision2 = Mock(
            decision_type="deny", allowed=False, context={}, high_impact=False, actor="actor2"
        )

        await precedent_engine.store_case(
            action="user requests access to sensitive data", decision=decision1, reasoning="Allowed"
        )
        await precedent_engine.store_case(
            action="application sends network request", decision=decision2, reasoning="Denied"
        )

        # Search for similar - should use word overlap
        similar_cases = await precedent_engine.find_similar_cases("user sends request", limit=5)

        # Both cases have overlapping words
        assert len(similar_cases) >= 1
        assert all("similarity_score" in case for case in similar_cases)

    @pytest.mark.asyncio
    async def test_similarity_scoring(self, precedent_engine):
        """Test similarity scoring accuracy."""
        precedent_engine.embeddings.model = None  # Use fallback

        decision = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor"
        )

        # Store case with specific words
        await precedent_engine.store_case(
            action="approve user authentication request",
            decision=decision,
            reasoning="Valid credentials",
        )

        # Search with similar action
        similar = await precedent_engine.find_similar_cases("approve authentication", limit=1)
        assert len(similar) == 1
        assert similar[0]["similarity_score"] > 0

    @pytest.mark.asyncio
    async def test_empty_precedent_similar_search(self, precedent_engine):
        """Test similar search on empty precedent engine."""
        similar_cases = await precedent_engine.find_similar_cases("any action")
        assert similar_cases == []

    @pytest.mark.asyncio
    async def test_similar_cases_limit(self, precedent_engine):
        """Test limit parameter in similar cases search."""
        decision = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor"
        )

        # Store multiple cases
        for i in range(5):
            await precedent_engine.store_case(
                action=f"test action {i}", decision=decision, reasoning="Test"
            )

        # Request only 2 results
        similar = await precedent_engine.find_similar_cases("action", limit=2)
        assert len(similar) <= 2

    @pytest.mark.asyncio
    async def test_similar_cases_sorted_by_similarity(self, precedent_engine):
        """Test that similar cases are sorted by similarity score."""
        precedent_engine.embeddings.model = None  # Use fallback for predictable results

        decision = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor"
        )

        # Store cases with varying word overlap
        await precedent_engine.store_case(
            action="exact test action here", decision=decision, reasoning="Test"
        )
        await precedent_engine.store_case(
            action="different other action", decision=decision, reasoning="Test"
        )

        similar = await precedent_engine.find_similar_cases("test action", limit=5)

        # Results should be sorted by similarity (highest first)
        if len(similar) > 1:
            assert similar[0]["similarity_score"] >= similar[1]["similarity_score"]

    @pytest.mark.asyncio
    async def test_case_metadata_preserved_in_similarity_search(self, precedent_engine):
        """Test that case metadata is preserved in similarity search results."""
        decision = Mock(
            decision_type="allow",
            allowed=True,
            context={"key": "value"},
            high_impact=True,
            actor="actor1",
        )

        case_id = await precedent_engine.store_case(
            action="test action",
            decision=decision,
            reasoning="Test reasoning",
            principles_cited=["principle1", "principle2"],
            stakeholders_affected=["user1", "org1"],
        )

        similar = await precedent_engine.find_similar_cases("action", limit=1)

        assert len(similar) > 0
        case = similar[0]
        assert case["id"] == case_id
        assert case["allowed"]
        assert case["high_impact"]
        assert case["actor"] == "actor1"
        assert "principle1" in case.get("principles_cited", [])
        assert "user1" in case.get("stakeholders_affected", [])


class TestEmbeddingsWithPrecedent:
    """Tests for embeddings integration with precedent engine."""

    @pytest.mark.asyncio
    async def test_embeddings_availability_check(self):
        """Test that embeddings availability is checked."""
        engine = MoralPrecedentEngine()
        embeddings = engine.embeddings

        # Check if embeddings can determine availability
        is_available = embeddings.is_available()
        assert isinstance(is_available, bool)

    @pytest.mark.asyncio
    async def test_precedent_handles_missing_embeddings(self):
        """Test precedent engine handles missing embeddings gracefully."""
        engine = MoralPrecedentEngine()
        engine.embeddings.model = None  # Disable embeddings

        decision = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor"
        )

        await engine.store_case(action="test action", decision=decision, reasoning="Test")

        # Should still work with fallback
        similar = await engine.find_similar_cases("action", limit=1)
        assert len(similar) > 0

    @pytest.mark.asyncio
    async def test_embeddings_caching_with_precedent(self):
        """Test that embeddings are cached across multiple searches."""
        engine = MoralPrecedentEngine()
        engine.embeddings.model = None  # Disable model to use cache

        # Pre-populate cache
        test_embedding = [0.1, 0.2, 0.3]
        engine.embeddings.embeddings_cache["cached action"] = test_embedding

        # Should use cached embedding
        cached = engine.embeddings.embed("cached action")
        assert cached == test_embedding


class TestPrecedentSearchConsistency:
    """Tests for consistency in precedent searches."""

    @pytest.mark.asyncio
    async def test_repeated_search_returns_consistent_order(self):
        """Test that repeated searches return consistent ordering."""
        engine = MoralPrecedentEngine()
        engine.embeddings.model = None  # Use fallback for consistency

        decision = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor"
        )

        # Store cases
        await engine.store_case(action="case one with words", decision=decision, reasoning="A")
        await engine.store_case(action="case two with words", decision=decision, reasoning="B")

        # Search multiple times
        result1 = await engine.find_similar_cases("words", limit=5)
        result2 = await engine.find_similar_cases("words", limit=5)

        # Should have same order and scores
        assert len(result1) == len(result2)
        if len(result1) > 0:
            assert result1[0]["id"] == result2[0]["id"]
            assert result1[0]["similarity_score"] == result2[0]["similarity_score"]

    @pytest.mark.asyncio
    async def test_case_insensitive_fallback_search(self):
        """Test that fallback word overlap search is case-insensitive."""
        engine = MoralPrecedentEngine()
        engine.embeddings.model = None

        decision = Mock(
            decision_type="allow", allowed=True, context={}, high_impact=False, actor="actor"
        )

        await engine.store_case(
            action="User Requests Data Access", decision=decision, reasoning="Test"
        )

        # Search with different case
        similar = await engine.find_similar_cases("user requests", limit=1)
        assert len(similar) > 0
