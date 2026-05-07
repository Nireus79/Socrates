"""
Ethical Deliberation Engine

Orchestrates multi-framework ethical reasoning to arrive at decisions
about proposed actions with detailed reasoning and confidence levels.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from socratic_system.reasoning.ethical_framework import (
    EthicalConclusion,
    EthicalFramework,
    EthicalFrameworkType,
    FrameworkAnalysis,
    KantianAnalyzer,
    RightsAnalyzer,
    UtilitarianAnalyzer,
    VirtueAnalyzer,
)
from socratic_system.reasoning.stakeholder_analyzer import (
    StakeholderAnalysis,
    StakeholderAnalyzer,
)


@dataclass
class DeliberationResult:
    """Result of ethical deliberation on an action."""
    action: str
    final_conclusion: EthicalConclusion
    confidence: float  # 0.0-1.0
    overall_reasoning: str
    framework_analyses: Dict[EthicalFrameworkType, FrameworkAnalysis] = field(default_factory=dict)
    stakeholder_analysis: Optional[StakeholderAnalysis] = None
    concerns: List[str] = field(default_factory=list)
    reasoning_summary: str = ""
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __hash__(self):
        return hash((self.action, self.final_conclusion.value))


class EthicalDeliberation:
    """
    Multi-framework ethical reasoning engine.

    Analyzes proposed actions through multiple ethical frameworks,
    identifies stakeholders, and arrives at reasoned conclusions
    about whether actions should be allowed, blocked, or escalated.
    """

    def __init__(
        self,
        frameworks: Optional[List[EthicalFramework]] = None,
        escalation_threshold: float = 0.6,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize deliberation engine.

        Args:
            frameworks: List of ethical frameworks to use (defaults to all)
            escalation_threshold: Confidence threshold below which to escalate (0.0-1.0)
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.escalation_threshold = escalation_threshold

        # Default to all frameworks if not specified
        self.frameworks = frameworks or [
            KantianAnalyzer(logger),
            UtilitarianAnalyzer(logger),
            VirtueAnalyzer(logger),
            RightsAnalyzer(logger),
        ]

        self.stakeholder_analyzer = StakeholderAnalyzer(logger)

    def deliberate(
        self,
        action: str,
        context: Dict[str, Any],
        constitutional_principles: Optional[List[str]] = None,
        consequences: Optional[Dict[str, Any]] = None,
        additional_stakeholders: Optional[List[Dict[str, Any]]] = None
    ) -> DeliberationResult:
        """
        Deliberate on whether action should be taken.

        Args:
            action: Description of proposed action
            context: Context information
            constitutional_principles: Relevant constitutional principles
            consequences: Known/projected consequences (short/long-term)
            additional_stakeholders: Additional stakeholder definitions

        Returns:
            DeliberationResult with conclusion and detailed reasoning
        """
        self.logger.info(f"[Deliberation] Starting analysis of action: {action}")

        # Analyze stakeholders
        stakeholder_analysis = self.stakeholder_analyzer.analyze(
            action=action,
            context=context,
            additional_stakeholders=additional_stakeholders
        )

        # If no consequences provided, use stakeholder analysis to infer
        if not consequences:
            consequences = self._infer_consequences(action, stakeholder_analysis)

        principles = constitutional_principles or [
            "transparency", "accountability", "fairness",
            "security", "privacy", "autonomy"
        ]

        # Run through all frameworks
        framework_analyses = {}
        conclusions = []
        confidences = []

        for framework in self.frameworks:
            try:
                analysis = framework.analyze(
                    action=action,
                    context=context,
                    stakeholders=stakeholder_analysis.stakeholders,
                    principles=principles,
                    consequences=consequences
                )

                framework_analyses[analysis.framework] = analysis
                conclusions.append(analysis.conclusion)
                confidences.append(analysis.confidence)

                self.logger.debug(
                    f"[{analysis.framework.value}] {analysis.conclusion.value} "
                    f"(confidence: {analysis.confidence:.2f})"
                )

            except Exception as e:
                self.logger.error(f"Error running {framework.name}: {e}")

        # Determine final conclusion
        final_conclusion, confidence = self._synthesize_conclusions(
            conclusions=conclusions,
            confidences=confidences,
            stakeholder_analysis=stakeholder_analysis
        )

        # Generate reasoning
        overall_reasoning = self._generate_reasoning(
            framework_analyses=framework_analyses,
            stakeholder_analysis=stakeholder_analysis,
            final_conclusion=final_conclusion
        )

        # Collect concerns from all frameworks
        all_concerns = []
        for analysis in framework_analyses.values():
            all_concerns.extend(analysis.concerns)

        # Check if escalation needed
        escalation_required = (
            confidence < self.escalation_threshold or
            final_conclusion == EthicalConclusion.ESCALATE
        )
        escalation_reason = None
        if escalation_required and framework_analyses:
            conflicting = [
                c for c in conclusions
                if c != final_conclusion
            ]
            if conflicting:
                escalation_reason = (
                    f"Framework disagreement: "
                    f"{', '.join(c.value for c in set(conflicting))} "
                    f"vs {final_conclusion.value}"
                )
            elif confidence < 0.5:
                escalation_reason = "Low confidence in conclusion across frameworks"
            elif final_conclusion == EthicalConclusion.ESCALATE:
                escalation_reason = "Conclusion marked for escalation due to complexity or uncertainty"

        result = DeliberationResult(
            action=action,
            final_conclusion=final_conclusion,
            confidence=confidence,
            overall_reasoning=overall_reasoning,
            framework_analyses=framework_analyses,
            stakeholder_analysis=stakeholder_analysis,
            concerns=all_concerns,
            escalation_required=escalation_required,
            escalation_reason=escalation_reason
        )

        self.logger.info(
            f"[Deliberation] Conclusion: {final_conclusion.value} "
            f"(confidence: {confidence:.2f}) | "
            f"Escalation: {escalation_required}"
        )

        return result

    def _synthesize_conclusions(
        self,
        conclusions: List[EthicalConclusion],
        confidences: List[float],
        stakeholder_analysis: StakeholderAnalysis
    ) -> tuple:
        """
        Synthesize conclusions from multiple frameworks into final decision.

        Args:
            conclusions: Conclusions from each framework
            confidences: Confidence scores for each conclusion
            stakeholder_analysis: Stakeholder impact analysis

        Returns:
            Tuple of (final_conclusion, overall_confidence)
        """
        if not conclusions:
            return EthicalConclusion.ESCALATE, 0.0

        # Count conclusion types
        allow_count = conclusions.count(EthicalConclusion.ALLOWED)
        block_count = conclusions.count(EthicalConclusion.BLOCKED)
        escalate_count = conclusions.count(EthicalConclusion.ESCALATE)

        total = len(conclusions)
        allow_pct = allow_count / total if total > 0 else 0

        # Decision logic
        if block_count > total * 0.5:  # Majority says block
            # Increase confidence if affects vulnerable
            confidence = sum(
                conf for conc, conf in zip(conclusions, confidences)
                if conc == EthicalConclusion.BLOCKED
            ) / max(block_count, 1)

            if stakeholder_analysis.has_vulnerable_affected():
                confidence = min(confidence * 1.1, 1.0)

            return EthicalConclusion.BLOCKED, confidence

        elif allow_count == total:  # Unanimous allow
            confidence = sum(confidences) / total
            return EthicalConclusion.ALLOWED, confidence

        elif escalate_count > 0 or allow_pct < 0.8:
            # If any framework says escalate, or there's disagreement
            confidence = sum(confidences) / total if total > 0 else 0.5
            return EthicalConclusion.ESCALATE, confidence

        else:  # Majority allow
            confidence = sum(
                conf for conc, conf in zip(conclusions, confidences)
                if conc == EthicalConclusion.ALLOWED
            ) / max(allow_count, 1)
            return EthicalConclusion.ALLOWED, confidence

    def _generate_reasoning(
        self,
        framework_analyses: Dict[EthicalFrameworkType, FrameworkAnalysis],
        stakeholder_analysis: StakeholderAnalysis,
        final_conclusion: EthicalConclusion
    ) -> str:
        """Generate natural language reasoning for the conclusion."""
        parts = []

        # Stakeholder summary
        if stakeholder_analysis.stakeholders:
            parts.append(
                f"Affects {len(stakeholder_analysis.stakeholders)} stakeholders "
                f"(vulnerable: {len(stakeholder_analysis.vulnerable_groups)})"
            )

        # Net impact
        net = stakeholder_analysis.net_impact()
        if net > 0:
            parts.append(f"Net positive impact (+{net:.2f})")
        elif net < 0:
            parts.append(f"Net negative impact ({net:.2f})")
        else:
            parts.append("Neutral net impact")

        # Framework consensus
        if framework_analyses:
            allow_frameworks = [
                f.framework.value
                for f in framework_analyses.values()
                if f.conclusion == EthicalConclusion.ALLOWED
            ]
            block_frameworks = [
                f.framework.value
                for f in framework_analyses.values()
                if f.conclusion == EthicalConclusion.BLOCKED
            ]

            if allow_frameworks:
                parts.append(f"Allowed by: {', '.join(allow_frameworks)}")
            if block_frameworks:
                parts.append(f"Blocked by: {', '.join(block_frameworks)}")

        # Final conclusion
        if final_conclusion == EthicalConclusion.BLOCKED:
            parts.append("-> BLOCKED: Action violates ethical principles")
        elif final_conclusion == EthicalConclusion.ALLOWED:
            parts.append("-> ALLOWED: Action aligned with ethical frameworks")
        else:
            parts.append("-> ESCALATE: Requires human review due to complexity")

        return " | ".join(parts)

    def _infer_consequences(
        self,
        action: str,
        stakeholder_analysis: StakeholderAnalysis
    ) -> Dict[str, Any]:
        """Infer consequences from action description and stakeholder analysis."""
        consequences = {
            "short_term": {
                "benefit": 0.0,
                "harm": 0.0,
            },
            "long_term": {
                "benefit": 0.0,
                "harm": 0.0,
            }
        }

        # Infer from negative impacts
        negative_impacts = [
            i for i in stakeholder_analysis.impacts
            if i.impact_type == "negative"
        ]

        if negative_impacts:
            avg_severity = sum(i.severity for i in negative_impacts) / len(negative_impacts)
            for impact in negative_impacts:
                if impact.timeframe == "short_term":
                    consequences["short_term"]["harm"] = max(
                        consequences["short_term"]["harm"],
                        avg_severity
                    )
                else:
                    consequences["long_term"]["harm"] = max(
                        consequences["long_term"]["harm"],
                        avg_severity
                    )

        # Infer from positive impacts
        positive_impacts = [
            i for i in stakeholder_analysis.impacts
            if i.impact_type == "positive"
        ]

        if positive_impacts:
            avg_severity = sum(i.severity for i in positive_impacts) / len(positive_impacts)
            for impact in positive_impacts:
                if impact.timeframe == "short_term":
                    consequences["short_term"]["benefit"] = max(
                        consequences["short_term"]["benefit"],
                        avg_severity
                    )
                else:
                    consequences["long_term"]["benefit"] = max(
                        consequences["long_term"]["benefit"],
                        avg_severity
                    )

        return consequences
