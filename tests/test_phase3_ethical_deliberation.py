"""
Tests for Phase 3 - Ethical Deliberation Agent

Tests multi-framework ethical reasoning, stakeholder analysis,
and ethical deliberation engine.
"""

import pytest
from datetime import datetime

from socratic_system.reasoning import (
    EthicalDeliberation,
    EthicalFrameworkType,
    EthicalConclusion,
    StakeholderAnalyzer,
    KantianAnalyzer,
    UtilitarianAnalyzer,
    VirtueAnalyzer,
    RightsAnalyzer,
)


class TestEthicalFrameworks:
    """Test individual ethical frameworks."""

    def test_kantian_blocks_deception(self):
        """Kantian framework blocks deceptive actions."""
        analyzer = KantianAnalyzer()

        analysis = analyzer.analyze(
            action="hide_operational_logs_from_users",
            context={"scope": "system_wide"},
            stakeholders=[
                {"id": "users", "name": "Users", "vulnerability": 0.5}
            ],
            principles=["transparency", "honesty"],
            consequences={}
        )

        assert analysis.conclusion == EthicalConclusion.BLOCKED
        assert analysis.confidence > 0.8
        assert "deceptive" in analysis.reasoning.lower() or \
               "manipulate" in " ".join(analysis.concerns).lower()

    def test_utilitarian_calculates_balance(self):
        """Utilitarian framework calculates benefit vs harm."""
        analyzer = UtilitarianAnalyzer()

        # Positive consequences
        analysis = analyzer.analyze(
            action="improve_system_performance",
            context={"scope": "system_wide"},
            stakeholders=[{"id": "users", "name": "Users"}],
            principles=["efficiency"],
            consequences={
                "short_term": {"benefit": 0.8, "harm": 0.1},
                "long_term": {"benefit": 0.7, "harm": 0.2}
            }
        )

        assert analysis.conclusion == EthicalConclusion.ALLOWED
        assert analysis.confidence > 0.6

    def test_virtue_identifies_vices(self):
        """Virtue framework identifies vices."""
        analyzer = VirtueAnalyzer()

        analysis = analyzer.analyze(
            action="deceive_users_for_personal_gain",
            context={},
            stakeholders=[],
            principles=["honesty", "integrity"],
            consequences={}
        )

        assert analysis.conclusion == EthicalConclusion.BLOCKED
        assert "deception" in " ".join(analysis.concerns).lower()

    def test_rights_framework_protects_consent(self):
        """Rights framework ensures informed consent."""
        analyzer = RightsAnalyzer()

        analysis = analyzer.analyze(
            action="access_user_data_without_permission",
            context={"consent_obtained": False, "informed": False},
            stakeholders=[
                {"id": "user", "name": "User", "vulnerability": 0.5}
            ],
            principles=["consent", "privacy"],
            consequences={}
        )

        assert analysis.conclusion == EthicalConclusion.BLOCKED
        assert analysis.confidence > 0.8


class TestStakeholderAnalysis:
    """Test stakeholder identification and impact analysis."""

    def setup_method(self):
        """Set up analyzer for each test."""
        self.analyzer = StakeholderAnalyzer()

    def test_identifies_all_stakeholders(self):
        """Analyzer identifies all relevant stakeholders."""
        analysis = self.analyzer.analyze(
            action="hide_operational_logs",
            context={"scope": "system_wide"}
        )

        assert len(analysis.stakeholders) > 0
        stakeholder_types = {s.stakeholder_type for s in analysis.stakeholders}
        assert len(stakeholder_types) > 1  # Multiple types

    def test_identifies_vulnerable_groups(self):
        """Analyzer identifies vulnerable stakeholders."""
        analysis = self.analyzer.analyze(
            action="restrict_access_for_minors",
            context={
                "scope": "targeted",
                "affected_group": "minors"
            }
        )

        assert len(analysis.vulnerable_groups) > 0

    def test_calculates_net_impact(self):
        """Analyzer calculates net impact correctly."""
        analysis = self.analyzer.analyze(
            action="improve_system_performance",
            context={"scope": "system_wide"}
        )

        # Should have some impacts
        assert len(analysis.impacts) > 0

        # Net impact is calculable
        net = analysis.net_impact()
        assert isinstance(net, float)
        assert -2.0 <= net <= 2.0

    def test_detects_powerless_affected(self):
        """Analyzer identifies stakeholders with no power to resist."""
        analysis = self.analyzer.analyze(
            action="enforce_new_policy",
            context={"scope": "all"}
        )

        # Check for powerless affected
        powerless = [s for s in analysis.stakeholders if not s.has_power_to_resist()]
        assert len(powerless) > 0


class TestEthicalDeliberation:
    """Test the ethical deliberation engine."""

    def setup_method(self):
        """Set up deliberation engine."""
        self.engine = EthicalDeliberation(
            frameworks=[
                KantianAnalyzer(),
                UtilitarianAnalyzer(),
                VirtueAnalyzer(),
                RightsAnalyzer(),
            ],
            escalation_threshold=0.6
        )

    def test_deliberation_produces_conclusion(self):
        """Deliberation produces a final conclusion."""
        result = self.engine.deliberate(
            action="log_all_user_actions_transparently",
            context={"scope": "system_wide"}
        )

        assert result.final_conclusion in [
            EthicalConclusion.ALLOWED,
            EthicalConclusion.BLOCKED,
            EthicalConclusion.ESCALATE
        ]
        assert 0.0 <= result.confidence <= 1.0

    def test_deliberation_blocks_unethical_action(self):
        """Deliberation blocks clearly unethical actions."""
        result = self.engine.deliberate(
            action="hide_security_vulnerabilities_from_users",
            context={"scope": "system_wide"},
            constitutional_principles=["transparency", "security"]
        )

        # Multiple frameworks should block this
        blocked_count = sum(
            1 for a in result.framework_analyses.values()
            if a.conclusion == EthicalConclusion.BLOCKED
        )
        assert blocked_count >= 2

        assert result.final_conclusion == EthicalConclusion.BLOCKED

    def test_deliberation_allows_beneficial_action(self):
        """Deliberation allows clearly beneficial actions."""
        result = self.engine.deliberate(
            action="improve_system_reliability_and_security",
            context={"scope": "system_wide"},
            consequences={
                "short_term": {"benefit": 0.9, "harm": 0.0},
                "long_term": {"benefit": 0.9, "harm": 0.1}
            }
        )

        # Most frameworks should allow this
        allowed_count = sum(
            1 for a in result.framework_analyses.values()
            if a.conclusion == EthicalConclusion.ALLOWED
        )
        assert allowed_count >= 2

        assert result.final_conclusion == EthicalConclusion.ALLOWED

    def test_deliberation_escalates_on_disagreement(self):
        """Deliberation escalates when frameworks disagree."""
        result = self.engine.deliberate(
            action="fire_employee_to_save_company",
            context={"scope": "specific"},
            consequences={
                "short_term": {"benefit": 0.7, "harm": 0.8},
                "long_term": {"benefit": 0.9, "harm": 0.5}
            }
        )

        # Frameworks likely disagree on this
        conclusions = [
            a.conclusion for a in result.framework_analyses.values()
        ]

        # Either escalates or very low confidence
        if result.final_conclusion == EthicalConclusion.ESCALATE:
            assert result.escalation_required
        elif result.confidence < 0.7:
            assert result.escalation_required

    def test_deliberation_includes_stakeholder_analysis(self):
        """Deliberation includes stakeholder analysis in result."""
        result = self.engine.deliberate(
            action="restrict_access_for_safety",
            context={"scope": "system_wide"}
        )

        assert result.stakeholder_analysis is not None
        assert len(result.stakeholder_analysis.stakeholders) > 0

    def test_deliberation_generates_reasoning(self):
        """Deliberation generates natural language reasoning."""
        result = self.engine.deliberate(
            action="improve_transparency_through_logging",
            context={"scope": "system_wide"}
        )

        assert result.overall_reasoning is not None
        assert len(result.overall_reasoning) > 0
        assert "transparency" in result.overall_reasoning.lower() or \
               "logging" in result.overall_reasoning.lower()

    def test_deliberation_collects_concerns(self):
        """Deliberation collects concerns from all frameworks."""
        result = self.engine.deliberate(
            action="exploit_user_vulnerabilities",
            context={"scope": "system_wide"}
        )

        assert len(result.concerns) > 0
        # Should have multiple concerns from different frameworks
        assert len(result.concerns) >= 2

    def test_deliberation_produces_consistent_results(self):
        """Repeated deliberation on same action produces same conclusion."""
        action = "log_operational_data_securely"
        context = {"scope": "system_wide"}

        result1 = self.engine.deliberate(action=action, context=context)
        result2 = self.engine.deliberate(action=action, context=context)

        assert result1.final_conclusion == result2.final_conclusion
        assert result1.confidence == result2.confidence

    def test_deliberation_respects_escalation_threshold(self):
        """Deliberation escalates when confidence below threshold."""
        low_confidence_engine = EthicalDeliberation(
            escalation_threshold=0.9
        )

        # Find an ambiguous action
        result = low_confidence_engine.deliberate(
            action="implement_new_feature_with_tradeoffs",
            context={"scope": "system_wide"}
        )

        if result.confidence < 0.9:
            assert result.escalation_required or result.final_conclusion == EthicalConclusion.ESCALATE


class TestEthicalDeliberationIntegration:
    """Integration tests for complete ethical reasoning flow."""

    def test_end_to_end_blocking_scenario(self):
        """Test complete flow for action that should be blocked."""
        engine = EthicalDeliberation()

        result = engine.deliberate(
            action="deceive_users_about_data_usage",
            context={"scope": "system_wide"},
            constitutional_principles=["honesty", "transparency", "privacy"]
        )

        # Verify complete result structure
        assert result.final_conclusion == EthicalConclusion.BLOCKED
        assert result.confidence > 0.8
        assert len(result.framework_analyses) >= 2
        assert result.stakeholder_analysis is not None
        assert len(result.concerns) > 0
        assert result.overall_reasoning

    def test_end_to_end_allowing_scenario(self):
        """Test complete flow for action that should be allowed."""
        engine = EthicalDeliberation()

        result = engine.deliberate(
            action="improve_system_security_with_user_consent",
            context={"scope": "system_wide"},
            constitutional_principles=["security", "honesty", "transparency"],
            consequences={
                "short_term": {"benefit": 0.8, "harm": 0.0},
                "long_term": {"benefit": 0.9, "harm": 0.0}
            }
        )

        # Should be allowed
        assert result.final_conclusion == EthicalConclusion.ALLOWED
        assert result.confidence > 0.7

    def test_end_to_end_escalation_scenario(self):
        """Test complete flow for ambiguous action requiring escalation."""
        engine = EthicalDeliberation(escalation_threshold=0.7)

        result = engine.deliberate(
            action="balance_user_privacy_with_security_needs",
            context={"scope": "system_wide"},
            consequences={
                "short_term": {"benefit": 0.5, "harm": 0.4},
                "long_term": {"benefit": 0.6, "harm": 0.5}
            }
        )

        # May require escalation due to tradeoffs
        assert result.escalation_reason is not None or result.confidence < 0.7

    def test_multiple_frameworks_working_together(self):
        """Test all frameworks analyzing same action."""
        engine = EthicalDeliberation()

        result = engine.deliberate(
            action="restrict_system_features_for_safety",
            context={"scope": "system_wide"}
        )

        # Should have analysis from all frameworks
        assert len(result.framework_analyses) >= 4

        # Each framework provides reasoning
        for framework_type, analysis in result.framework_analyses.items():
            assert analysis.reasoning
            assert analysis.conclusion in [
                EthicalConclusion.ALLOWED,
                EthicalConclusion.BLOCKED,
                EthicalConclusion.ESCALATE
            ]


class TestEthicalDeliberationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_action_description(self):
        """Handle empty action description gracefully."""
        engine = EthicalDeliberation()

        result = engine.deliberate(
            action="",
            context={}
        )

        # Should still produce a result
        assert result.final_conclusion in [
            EthicalConclusion.ALLOWED,
            EthicalConclusion.BLOCKED,
            EthicalConclusion.ESCALATE
        ]

    def test_no_stakeholders_identified(self):
        """Handle case with no stakeholders."""
        engine = EthicalDeliberation()

        result = engine.deliberate(
            action="internal_logging_improvement",
            context={"scope": "internal"}
        )

        # Should still produce analysis
        assert result.final_conclusion is not None
        assert result.stakeholder_analysis is not None

    def test_mixed_positive_negative_consequences(self):
        """Handle action with mixed positive and negative consequences."""
        engine = EthicalDeliberation()

        result = engine.deliberate(
            action="implement_new_feature_with_tradeoffs",
            context={"scope": "system_wide"},
            consequences={
                "short_term": {"benefit": 0.5, "harm": 0.5},
                "long_term": {"benefit": 0.7, "harm": 0.3}
            }
        )

        # Should handle ambiguity
        assert result.final_conclusion is not None
        assert result.overall_reasoning is not None
