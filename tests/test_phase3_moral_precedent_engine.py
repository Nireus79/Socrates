"""
Tests for Phase 3.3 - Moral Precedent Engine

Tests precedent storage, retrieval, consistency checking, and
pattern analysis for maintaining ethical consistency.
"""

import os
import tempfile

from socratic_system.reasoning import (
    MoralPrecedentEngine,
    PrecedentQuery,
    PrecedentType,
)


class TestPrecedentStorage:
    """Test storing and retrieving moral precedents."""

    def setup_method(self):
        """Set up precedent engine for tests."""
        self.engine = MoralPrecedentEngine()

    def test_engine_initializes(self):
        """Engine initializes successfully."""
        assert self.engine is not None
        assert len(self.engine.precedents) == 0

    def test_store_single_precedent(self):
        """Can store a single precedent."""
        prec_id = self.engine.store_precedent(
            action_description="improve_system_security",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.95,
            reasoning="Security improvements benefit all stakeholders",
            principles_involved=["security", "protection"],
        )

        assert prec_id is not None
        assert prec_id in self.engine.precedents
        assert self.engine.precedents[prec_id].action_description == ("improve_system_security")

    def test_store_multiple_precedents(self):
        """Can store multiple precedents."""
        ids = []
        for i in range(5):
            prec_id = self.engine.store_precedent(
                action_description=f"action_{i}",
                conclusion=PrecedentType.ALLOWED,
                confidence=0.8,
                reasoning=f"Reasoning for action {i}",
            )
            ids.append(prec_id)

        assert len(self.engine.precedents) == 5
        assert all(prec_id in self.engine.precedents for prec_id in ids)

    def test_precedent_has_metadata(self):
        """Stored precedent contains all metadata."""
        prec_id = self.engine.store_precedent(
            action_description="test_action",
            conclusion=PrecedentType.BLOCKED,
            confidence=0.85,
            reasoning="Test reasoning",
            principles_involved=["honesty", "transparency"],
            context={"scope": "system_wide"},
            stakeholders_affected=["users", "organization"],
        )

        precedent = self.engine.precedents[prec_id]
        assert precedent.action_description == "test_action"
        assert precedent.conclusion == PrecedentType.BLOCKED
        assert precedent.confidence == 0.85
        assert precedent.reasoning == "Test reasoning"
        assert set(precedent.principles_involved) == {"honesty", "transparency"}
        assert precedent.context["scope"] == "system_wide"
        assert set(precedent.stakeholders_affected) == {"users", "organization"}


class TestPrecedentQuerying:
    """Test querying and finding similar precedents."""

    def setup_method(self):
        """Set up engine with sample precedents."""
        self.engine = MoralPrecedentEngine()

        # Store various precedents
        self.engine.store_precedent(
            action_description="improve system security",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.95,
            reasoning="Security improvements are beneficial",
            principles_involved=["security", "protection"],
        )

        self.engine.store_precedent(
            action_description="improve system performance",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.90,
            reasoning="Performance improvements help users",
            principles_involved=["efficiency"],
        )

        self.engine.store_precedent(
            action_description="exploit user data",
            conclusion=PrecedentType.BLOCKED,
            confidence=0.98,
            reasoning="Data exploitation violates privacy",
            principles_involved=["privacy", "consent"],
        )

    def test_query_finds_similar_precedent(self):
        """Query finds precedents similar to action."""
        query = PrecedentQuery(
            action="improve security",
            similarity_threshold=0.3,
        )

        matches = self.engine.query_precedents(query)

        assert len(matches) > 0
        assert any("security" in m.precedent.action_description.lower() for m in matches)

    def test_query_respects_similarity_threshold(self):
        """Query respects similarity threshold."""
        query = PrecedentQuery(
            action="improve security",
            similarity_threshold=0.8,
        )

        matches = self.engine.query_precedents(query)

        # Threshold 0.8 is very high, might not match anything
        for match in matches:
            assert match.similarity_score >= 0.8

    def test_query_filters_by_conclusion(self):
        """Query can filter by conclusion type."""
        query = PrecedentQuery(
            action="action",
            conclusion_filter=[PrecedentType.ALLOWED],
        )

        matches = self.engine.query_precedents(query)

        for match in matches:
            assert match.precedent.conclusion == PrecedentType.ALLOWED

    def test_query_filters_by_principles(self):
        """Query can filter by principles involved."""
        query = PrecedentQuery(
            action="action",
            principle_filter=["security"],
        )

        matches = self.engine.query_precedents(query)

        for match in matches:
            assert "security" in match.precedent.principles_involved

    def test_query_limits_results(self):
        """Query respects max_results limit."""
        query = PrecedentQuery(
            action="improve",
            similarity_threshold=0.0,
            max_results=1,
        )

        matches = self.engine.query_precedents(query)

        assert len(matches) <= 1


class TestPrecedentAnalysis:
    """Test analyzing collections of precedents."""

    def setup_method(self):
        """Set up engine with precedents."""
        self.engine = MoralPrecedentEngine()

        # Store consistent precedents
        for _i in range(3):
            self.engine.store_precedent(
                action_description="improve system functionality",
                conclusion=PrecedentType.ALLOWED,
                confidence=0.9,
                reasoning="Improvements benefit users",
                principles_involved=["efficiency", "user_benefit"],
            )

    def test_analyze_finds_matching_precedents(self):
        """Analysis finds matching precedents."""
        analysis = self.engine.analyze_precedents(action="improve system")

        assert analysis is not None
        assert len(analysis.matching_precedents) > 0

    def test_analysis_checks_consistency(self):
        """Analysis checks consistency among precedents."""
        analysis = self.engine.analyze_precedents(action="improve system")

        assert isinstance(analysis.precedent_consistency, bool)
        assert analysis.consistency_explanation is not None

    def test_analysis_identifies_historical_pattern(self):
        """Analysis identifies patterns in precedents."""
        analysis = self.engine.analyze_precedents(action="improve system")

        assert analysis.historical_pattern is not None
        assert "usually" in analysis.historical_pattern or "Mixed" in analysis.historical_pattern

    def test_analysis_recommends_conclusion(self):
        """Analysis can recommend conclusion from precedents."""
        analysis = self.engine.analyze_precedents(action="improve system")

        # With consistent precedents, should recommend
        if analysis.precedent_consistency:
            assert analysis.recommended_conclusion is not None


class TestConsistencyChecking:
    """Test checking consistency with precedents."""

    def setup_method(self):
        """Set up engine with precedents."""
        self.engine = MoralPrecedentEngine()

        self.prec1 = self.engine.store_precedent(
            action_description="harm users",
            conclusion=PrecedentType.BLOCKED,
            confidence=0.99,
            reasoning="User harm is unethical",
        )

        self.prec2 = self.engine.store_precedent(
            action_description="steal user data",
            conclusion=PrecedentType.BLOCKED,
            confidence=0.98,
            reasoning="Theft violates rights",
        )

    def test_consistent_conclusion_is_valid(self):
        """Consistent conclusions pass check."""
        precedents = list(self.engine.precedents.values())
        is_consistent, explanation = self.engine.check_consistency(
            PrecedentType.BLOCKED, precedents
        )

        assert is_consistent
        assert explanation is not None

    def test_inconsistent_conclusion_flags_error(self):
        """Inconsistent conclusions fail check."""
        precedents = list(self.engine.precedents.values())
        is_consistent, explanation = self.engine.check_consistency(
            PrecedentType.ALLOWED, precedents
        )

        assert not is_consistent
        assert "Contradicts" in explanation

    def test_no_precedents_allows_any_conclusion(self):
        """No precedents allows any conclusion."""
        is_consistent, explanation = self.engine.check_consistency(PrecedentType.ESCALATED, [])

        assert is_consistent


class TestPrecedentStatistics:
    """Test generating statistics from precedents."""

    def setup_method(self):
        """Set up engine with various precedents."""
        self.engine = MoralPrecedentEngine()

        # Store different conclusion types
        self.engine.store_precedent(
            action_description="improve",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.95,
            reasoning="Improvement",
        )

        self.engine.store_precedent(
            action_description="harm",
            conclusion=PrecedentType.BLOCKED,
            confidence=0.98,
            reasoning="Harm",
        )

        self.engine.store_precedent(
            action_description="ambiguous",
            conclusion=PrecedentType.ESCALATED,
            confidence=0.70,
            reasoning="Needs review",
        )

    def test_get_statistics(self):
        """Can retrieve statistics about precedents."""
        stats = self.engine.get_statistics()

        assert stats["total_precedents"] == 3
        assert stats["allowed_count"] == 1
        assert stats["blocked_count"] == 1
        assert stats["escalated_count"] == 1
        assert 0.0 <= stats["average_confidence"] <= 1.0

    def test_statistics_with_empty_engine(self):
        """Statistics work with empty engine."""
        empty_engine = MoralPrecedentEngine()
        stats = empty_engine.get_statistics()

        assert stats["total_precedents"] == 0
        assert stats["average_confidence"] == 0.0


class TestPrecedentImportExport:
    """Test exporting and importing precedents."""

    def setup_method(self):
        """Set up engine with precedents."""
        self.engine = MoralPrecedentEngine()

        self.engine.store_precedent(
            action_description="test action",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.85,
            reasoning="Test reasoning",
            principles_involved=["test", "principle"],
        )

    def test_export_precedents(self):
        """Can export precedents to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "precedents.json")
            self.engine.export_precedents(filepath)

            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0

    def test_import_precedents(self):
        """Can import precedents from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "precedents.json")

            # Export
            self.engine.export_precedents(filepath)
            original_count = len(self.engine.precedents)

            # Import into new engine
            new_engine = MoralPrecedentEngine()
            new_engine.import_precedents(filepath)

            assert len(new_engine.precedents) == original_count

    def test_round_trip_preserves_data(self):
        """Export-import round trip preserves data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "precedents.json")

            # Get original data
            original = list(self.engine.precedents.values())[0]

            # Round trip
            self.engine.export_precedents(filepath)
            new_engine = MoralPrecedentEngine()
            new_engine.import_precedents(filepath)

            # Verify
            imported = list(new_engine.precedents.values())[0]
            assert imported.action_description == original.action_description
            assert imported.conclusion == original.conclusion
            assert imported.confidence == original.confidence


class TestSimilarityCalculation:
    """Test similarity calculation for precedents."""

    def setup_method(self):
        """Set up precedents for similarity testing."""
        self.engine = MoralPrecedentEngine()
        self.prec = self.engine.store_precedent(
            action_description="improve system security",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.95,
            reasoning="Security is important",
        )

    def test_identical_similarity_is_high(self):
        """Identical actions have high similarity."""
        precedent = self.engine.precedents[self.prec]
        similarity = precedent.similarity_to("improve system security")

        assert similarity > 0.9

    def test_completely_different_similarity_is_low(self):
        """Completely different actions have low similarity."""
        precedent = self.engine.precedents[self.prec]
        similarity = precedent.similarity_to("xyz abc def")

        assert similarity < 0.1

    def test_similar_similarity_is_moderate(self):
        """Similar but different actions have moderate similarity."""
        precedent = self.engine.precedents[self.prec]
        similarity = precedent.similarity_to("improve system performance")

        assert 0.2 < similarity < 0.9


class TestIntegrationWithDeliberation:
    """Test integration between precedent engine and deliberation."""

    def setup_method(self):
        """Set up for integration tests."""
        self.engine = MoralPrecedentEngine()

    def test_store_deliberation_result_as_precedent(self):
        """Can store deliberation results as precedents."""
        prec_id = self.engine.store_precedent(
            action_description="balance_competing_interests",
            conclusion=PrecedentType.ESCALATED,
            confidence=0.65,
            reasoning="Multiple frameworks disagreed",
            principles_involved=["fairness", "security"],
        )

        assert prec_id in self.engine.precedents
        stored = self.engine.precedents[prec_id]
        assert stored.conclusion == PrecedentType.ESCALATED

    def test_query_for_similar_deliberation(self):
        """Can query for precedents similar to deliberation action."""
        # Store precedent
        self.engine.store_precedent(
            action_description="improve transparency",
            conclusion=PrecedentType.ALLOWED,
            confidence=0.90,
            reasoning="Transparency benefits all",
            principles_involved=["transparency"],
        )

        # Query for similar
        query = PrecedentQuery(
            action="improve transparency and accountability",
            similarity_threshold=0.3,
        )

        matches = self.engine.query_precedents(query)

        assert len(matches) > 0
        assert any("transparency" in m.precedent.action_description for m in matches)
