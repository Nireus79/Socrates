"""
Contradiction Detection for Ethical Reasoning

Identifies logical inconsistencies, principle conflicts, and temporal
consequence contradictions in ethical deliberation results.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from socratic_system.reasoning.ethical_deliberation import DeliberationResult
from socratic_system.reasoning.ethical_framework import (
    EthicalConclusion,
    EthicalFrameworkType,
)


class ContradictionType(Enum):
    """Types of contradictions that can be detected."""

    FRAMEWORK_DISAGREEMENT = "framework_disagreement"
    PRINCIPLE_CONFLICT = "principle_conflict"
    TEMPORAL_CONTRADICTION = "temporal_contradiction"
    CONSEQUENCE_MISMATCH = "consequence_mismatch"
    CONFIDENCE_INCONSISTENCY = "confidence_inconsistency"
    STAKEHOLDER_CONFLICT = "stakeholder_conflict"


@dataclass
class Contradiction:
    """Represents a detected contradiction in reasoning."""

    contradiction_type: ContradictionType
    severity: float  # 0.0-1.0 (how serious is this contradiction)
    description: str
    affected_frameworks: list[str] = field(default_factory=list)
    affected_principles: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __hash__(self):
        """Return hash of this object."""
        return hash((self.contradiction_type.value, self.description))


@dataclass
class ContradictionAnalysis:
    """Complete analysis of contradictions in a deliberation result."""

    action: str
    contradictions: list[Contradiction] = field(default_factory=list)
    has_major_contradictions: bool = False
    total_severity: float = 0.0
    consistency_score: float = 1.0  # 1.0 = fully consistent, 0.0 = highly inconsistent
    coherence_issues: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ContradictionDetector:
    """
    Detects logical inconsistencies and contradictions in ethical reasoning.

    Analyzes:
    - Framework disagreement and conflict severity
    - Principle conflicts (when action violates some principles but follows others)
    - Temporal consequence contradictions (short-term vs long-term)
    - Consequence-conclusion mismatches
    - Confidence inconsistencies
    - Stakeholder impact conflicts
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize contradiction detector.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def analyze(self, result: DeliberationResult) -> ContradictionAnalysis:
        """
        Analyze a deliberation result for contradictions.

        Args:
            result: DeliberationResult from EthicalDeliberation

        Returns:
            ContradictionAnalysis with detected contradictions
        """
        analysis = ContradictionAnalysis(action=result.action)

        # Detect framework disagreement
        disagreements = self._detect_framework_disagreement(result)
        analysis.contradictions.extend(disagreements)

        # Detect principle conflicts
        conflicts = self._detect_principle_conflicts(result)
        analysis.contradictions.extend(conflicts)

        # Detect temporal contradictions
        temporal = self._detect_temporal_contradictions(result)
        analysis.contradictions.extend(temporal)

        # Detect consequence-conclusion mismatches
        mismatches = self._detect_consequence_mismatches(result)
        analysis.contradictions.extend(mismatches)

        # Detect confidence inconsistencies
        inconsistencies = self._detect_confidence_inconsistencies(result)
        analysis.contradictions.extend(inconsistencies)

        # Detect stakeholder conflicts
        stakeholder_conflicts = self._detect_stakeholder_conflicts(result)
        analysis.contradictions.extend(stakeholder_conflicts)

        # Calculate analysis metrics
        analysis.has_major_contradictions = any(c.severity > 0.7 for c in analysis.contradictions)
        analysis.total_severity = sum(c.severity for c in analysis.contradictions)
        analysis.consistency_score = self._calculate_consistency_score(analysis)
        analysis.coherence_issues = self._identify_coherence_issues(result, analysis)

        self.logger.info(
            f"[Contradiction Analysis] Action: {result.action} | "
            f"Contradictions: {len(analysis.contradictions)} | "
            f"Consistency: {analysis.consistency_score:.2f}"
        )

        return analysis

    def _detect_framework_disagreement(self, result: DeliberationResult) -> list[Contradiction]:
        """Detect when ethical frameworks disagree on conclusion."""
        contradictions: list[Contradiction] = []

        if not result.framework_analyses or len(result.framework_analyses) < 2:
            return contradictions

        conclusions = [f.conclusion for f in result.framework_analyses.values()]
        unique_conclusions = set(conclusions)

        if len(unique_conclusions) <= 1:
            return contradictions  # All agree

        # Calculate disagreement severity
        blocked_count = conclusions.count(EthicalConclusion.BLOCKED)
        allowed_count = conclusions.count(EthicalConclusion.ALLOWED)
        escalate_count = conclusions.count(EthicalConclusion.ESCALATE)
        total = len(conclusions)

        # Severity increases with disagreement balance (closer to 50-50 = more severe)
        max_conflict = max(blocked_count, allowed_count, escalate_count)
        disagreement_severity = 1.0 - (max_conflict / total)

        # Identify which frameworks disagree
        frameworks_blocked = [
            f.value
            for f, a in result.framework_analyses.items()
            if a.conclusion == EthicalConclusion.BLOCKED
        ]
        frameworks_allowed = [
            f.value
            for f, a in result.framework_analyses.items()
            if a.conclusion == EthicalConclusion.ALLOWED
        ]

        contradiction = Contradiction(
            contradiction_type=ContradictionType.FRAMEWORK_DISAGREEMENT,
            severity=disagreement_severity,
            description=f"Frameworks disagree: {', '.join(frameworks_blocked or frameworks_allowed)} "
            f"vs {', '.join(frameworks_allowed or frameworks_blocked)}",
            affected_frameworks=list(set(frameworks_blocked + frameworks_allowed)),
            evidence={
                "blocked_frameworks": frameworks_blocked,
                "allowed_frameworks": frameworks_allowed,
                "escalate_frameworks": [
                    f.value
                    for f, a in result.framework_analyses.items()
                    if a.conclusion == EthicalConclusion.ESCALATE
                ],
            },
        )
        contradictions.append(contradiction)

        return contradictions

    def _detect_principle_conflicts(self, result: DeliberationResult) -> list[Contradiction]:
        """Detect when action violates some principles but follows others."""
        contradictions: list[Contradiction] = []

        if not result.framework_analyses:
            return contradictions

        # Extract principles from framework analyses
        blocked_analyses = [
            a
            for a in result.framework_analyses.values()
            if a.conclusion == EthicalConclusion.BLOCKED
        ]
        allowed_analyses = [
            a
            for a in result.framework_analyses.values()
            if a.conclusion == EthicalConclusion.ALLOWED
        ]

        if not blocked_analyses or not allowed_analyses:
            return contradictions

        # Find shared principles between conflicting frameworks
        blocked_principles = set()
        for analysis in blocked_analyses:
            blocked_principles.update(analysis.affected_principles)

        allowed_principles = set()
        for analysis in allowed_analyses:
            allowed_principles.update(analysis.affected_principles)

        shared_principles = blocked_principles & allowed_principles

        if shared_principles:
            severity = len(shared_principles) / max(len(blocked_principles | allowed_principles), 1)

            contradiction = Contradiction(
                contradiction_type=ContradictionType.PRINCIPLE_CONFLICT,
                severity=min(severity, 1.0),
                description=f"Action both violates and respects shared principles: "
                f"{', '.join(sorted(shared_principles))}",
                affected_principles=list(shared_principles),
                evidence={
                    "blocked_principles": list(blocked_principles),
                    "allowed_principles": list(allowed_principles),
                    "shared_principles": list(shared_principles),
                },
            )
            contradictions.append(contradiction)

        return contradictions

    def _detect_temporal_contradictions(self, result: DeliberationResult) -> list[Contradiction]:
        """Detect contradictions between short-term and long-term consequences."""
        contradictions: list[Contradiction] = []

        # This is a simplified check - in practice we'd have consequence data

        # Check stakeholder analysis for temporal impacts
        if not result.stakeholder_analysis or not result.stakeholder_analysis.impacts:
            return contradictions

        impacts = result.stakeholder_analysis.impacts

        short_term_impacts = [i for i in impacts if i.timeframe == "short_term"]
        long_term_impacts = [i for i in impacts if i.timeframe == "long_term"]

        if not short_term_impacts or not long_term_impacts:
            return contradictions

        # Check for sign reversals (benefit -> harm or vice versa)
        short_positive = sum(1 for i in short_term_impacts if i.impact_type == "positive")
        long_positive = sum(1 for i in long_term_impacts if i.impact_type == "positive")

        short_negative = sum(1 for i in short_term_impacts if i.impact_type == "negative")
        long_negative = sum(1 for i in long_term_impacts if i.impact_type == "negative")

        # If direction changes significantly, that's a contradiction
        if (short_positive > 0 and long_negative > 0 and long_positive == 0) or (
            short_negative > 0 and long_positive > 0 and long_negative == 0
        ):
            severity = 0.8
            direction_change = "positive" if short_positive > 0 else "negative"
            reverse_direction = "negative" if short_positive > 0 else "positive"

            contradiction = Contradiction(
                contradiction_type=ContradictionType.TEMPORAL_CONTRADICTION,
                severity=severity,
                description=f"Short-term impact is {direction_change} but long-term becomes {reverse_direction}",
                evidence={
                    "short_term_positive": short_positive,
                    "short_term_negative": short_negative,
                    "long_term_positive": long_positive,
                    "long_term_negative": long_negative,
                },
            )
            contradictions.append(contradiction)

        return contradictions

    def _detect_consequence_mismatches(self, result: DeliberationResult) -> list[Contradiction]:
        """Detect mismatches between claimed consequences and framework conclusions."""
        contradictions: list[Contradiction] = []

        util_analysis = result.framework_analyses.get(EthicalFrameworkType.UTILITARIAN)
        if not util_analysis or not util_analysis.reasoning:
            return contradictions

        # Check if reasoning mentions benefits exceeding harms but conclusion is BLOCKED
        reasoning_lower = util_analysis.reasoning.lower()
        has_positive_reasoning = "benefit" in reasoning_lower and "exceed" in reasoning_lower
        is_blocked = util_analysis.conclusion == EthicalConclusion.BLOCKED

        if has_positive_reasoning and is_blocked:
            contradiction = Contradiction(
                contradiction_type=ContradictionType.CONSEQUENCE_MISMATCH,
                severity=0.6,
                description="Utilitarian analysis claims positive consequences but conclusion is BLOCKED",
                affected_frameworks=["utilitarian"],
                evidence={
                    "reasoning": util_analysis.reasoning,
                    "conclusion": util_analysis.conclusion.value,
                },
            )
            contradictions.append(contradiction)

        return contradictions

    def _detect_confidence_inconsistencies(self, result: DeliberationResult) -> list[Contradiction]:
        """Detect inconsistencies between confidence and conclusion uncertainty."""
        contradictions: list[Contradiction] = []

        if result.final_conclusion == EthicalConclusion.ESCALATE and result.confidence > 0.85:
            # High confidence in escalation is contradictory
            contradiction = Contradiction(
                contradiction_type=ContradictionType.CONFIDENCE_INCONSISTENCY,
                severity=0.5,
                description=f"High confidence ({result.confidence:.2f}) in ESCALATE conclusion "
                f"indicates decision uncertainty is actually resolved",
                evidence={
                    "conclusion": result.final_conclusion.value,
                    "confidence": result.confidence,
                },
            )
            contradictions.append(contradiction)

        return contradictions

    def _detect_stakeholder_conflicts(self, result: DeliberationResult) -> list[Contradiction]:
        """Detect conflicts in how stakeholders are affected."""
        contradictions: list[Contradiction] = []

        if not result.stakeholder_analysis:
            return contradictions

        analysis = result.stakeholder_analysis

        # Check for vulnerable populations being negatively affected
        vulnerable_negatively_affected = [
            i
            for i in analysis.impacts
            if any(s.id == i.affected_party and s.is_vulnerable() for s in analysis.stakeholders)
            and i.impact_type == "negative"
        ]

        if vulnerable_negatively_affected:
            # Check if conclusion is ALLOWED despite harm to vulnerable
            if result.final_conclusion == EthicalConclusion.ALLOWED:
                contradiction = Contradiction(
                    contradiction_type=ContradictionType.STAKEHOLDER_CONFLICT,
                    severity=0.85,
                    description=f"Action is ALLOWED despite {len(vulnerable_negatively_affected)} "
                    f"negative impacts on vulnerable populations",
                    affected_principles=["fairness", "justice", "protection"],
                    evidence={
                        "vulnerable_negative_impacts": len(vulnerable_negatively_affected),
                        "affected_parties": [
                            i.affected_party for i in vulnerable_negatively_affected
                        ],
                    },
                )
                contradictions.append(contradiction)

        return contradictions

    def _calculate_consistency_score(self, analysis: ContradictionAnalysis) -> float:
        """Calculate overall consistency score (1.0 = fully consistent)."""
        if not analysis.contradictions:
            return 1.0

        # Average severity, inverted
        avg_severity = analysis.total_severity / len(analysis.contradictions)
        consistency = 1.0 - avg_severity

        return max(0.0, min(1.0, consistency))

    def _identify_coherence_issues(
        self, result: DeliberationResult, analysis: ContradictionAnalysis
    ) -> list[str]:
        """Identify specific coherence issues in the reasoning."""
        issues = []

        # Major contradictions reduce coherence
        if analysis.has_major_contradictions:
            issues.append("Reasoning contains major contradictions requiring resolution")

        # Escalation with high confidence is problematic
        if result.final_conclusion == EthicalConclusion.ESCALATE and result.confidence > 0.8:
            issues.append("Inconsistent: decision escalated despite high confidence")

        # Framework disagreement without explanation
        if len(result.framework_analyses) > 1:
            conclusions = [f.conclusion for f in result.framework_analyses.values()]
            if len(set(conclusions)) > 1 and not result.escalation_reason:
                issues.append("Framework disagreement detected but not explicitly addressed")

        # Multiple concerns but allowed conclusion
        if len(result.concerns) > 3 and result.final_conclusion == EthicalConclusion.ALLOWED:
            issues.append(f"Multiple concerns ({len(result.concerns)}) but action is ALLOWED")

        return issues
