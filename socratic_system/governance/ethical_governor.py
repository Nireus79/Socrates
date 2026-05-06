"""
Ethical Governor Integration with Phase 3 Reasoning Modules

Integrates Ethical Deliberation, Contradiction Detection, Precedent Engine,
Threat Detection, and Mutual TLS into the Governor's decision-making system.

This module bridges the governance layer with advanced ethical reasoning,
providing explainable and auditable decisions for all agent actions.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple
import logging

from socratic_system.reasoning import (
    EthicalDeliberation,
    ContradictionDetector,
    MoralPrecedentEngine,
    ThreatDetector,
    DeliberationResult,
    ContradictionAnalysis,
    PrecedentAnalysis,
    ThreatAnalysis,
    PrecedentType,
)
from socratic_system.security.mutual_tls import (
    MutualTLSManager,
    MutualTLSPolicy,
)


@dataclass
class EthicalDecision:
    """Complete decision with full ethical reasoning trail."""
    action: str
    actor: str
    allowed: bool
    decision_type: str  # ALLOW, DENY, ESCALATE, BLOCK

    # Reasoning components
    deliberation: Optional[DeliberationResult] = None
    contradictions: Optional[ContradictionAnalysis] = None
    precedent: Optional[PrecedentAnalysis] = None
    threat_analysis: Optional[ThreatAnalysis] = None

    # Decision metadata
    confidence: float = 0.5
    violations: List[str] = field(default_factory=list)
    reasoning: str = ""
    decision_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Audit trail
    reasoning_artifacts: Dict[str, Any] = field(default_factory=dict)

    def requires_escalation(self) -> bool:
        """Determine if decision requires human escalation."""
        if self.decision_type == "ESCALATE":
            return True
        if self.threat_analysis and self.threat_analysis.overall_threat_level.value in ["high", "critical"]:
            return True
        if self.confidence < 0.6:
            return True
        return False


class EthicalGovernor:
    """
    Governs agent actions through advanced ethical reasoning.

    Integrates multiple reasoning modules to provide:
    - Multi-framework ethical analysis
    - Contradiction detection
    - Precedent consistency checking
    - Threat and anomaly detection
    - Mutual TLS validation
    - Comprehensive audit trails
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        enable_deliberation: bool = True,
        enable_precedent: bool = True,
        enable_threat_detection: bool = True,
        enable_tls: bool = True,
    ):
        """Initialize Ethical Governor.

        Args:
            logger: Optional logger instance
            enable_deliberation: Enable ethical deliberation engine
            enable_precedent: Enable moral precedent engine
            enable_threat_detection: Enable threat detection
            enable_tls: Enable mutual TLS validation
        """
        self.logger = logger or logging.getLogger(__name__)

        # Core reasoning modules
        self.deliberation = EthicalDeliberation() if enable_deliberation else None
        self.contradiction_detector = ContradictionDetector() if enable_deliberation else None
        self.precedent_engine = MoralPrecedentEngine() if enable_precedent else None
        self.threat_detector = ThreatDetector() if enable_threat_detection else None
        self.tls_manager = MutualTLSManager() if enable_tls else None

        # Decision tracking
        self.decision_count = 0
        self.decisions: Dict[str, EthicalDecision] = {}
        self.escalations: List[EthicalDecision] = []

        self.logger.info("[Ethical Governor] Initialized")

    def evaluate_action(
        self,
        action: str,
        actor: str,
        context: Optional[Dict[str, Any]] = None,
        purpose: str = "",
        high_impact: bool = False,
    ) -> Tuple[bool, str, EthicalDecision]:
        """
        Evaluate an action through ethical reasoning.

        Implements the full Phase 3 reasoning pipeline:
        1. Ethical deliberation across frameworks
        2. Contradiction detection
        3. Precedent consistency checking
        4. Threat/anomaly detection
        5. TLS validation

        Args:
            action: Action description
            actor: Agent performing action
            context: Optional context dict with scope, users, etc.
            purpose: Purpose of the action
            high_impact: Whether this is a high-impact decision

        Returns:
            Tuple of (allowed: bool, reasoning: str, decision: EthicalDecision)
        """
        context = context or {}
        self.decision_count += 1
        decision_id = f"decision_{self.decision_count}_{int(datetime.now(UTC).timestamp())}"

        decision = EthicalDecision(
            action=action,
            actor=actor,
            allowed=True,  # Default to allowed, adjust based on reasoning
            decision_type="ALLOW",
            decision_id=decision_id,
        )

        self.logger.info(f"[Governor] Evaluating: {action} by {actor}")

        # Step 1: Ethical Deliberation
        if self.deliberation:
            try:
                deliberation_result = self.deliberation.deliberate(
                    action=action,
                    context=context,
                    constitutional_principles=None,
                )
                decision.deliberation = deliberation_result
                decision.confidence = deliberation_result.confidence

                # Check deliberation conclusion
                # deliberation_result.final_conclusion is EthicalConclusion enum
                if deliberation_result.final_conclusion.value == "blocked":
                    decision.allowed = False
                    decision.decision_type = "DENY"
                    decision.reasoning = f"Ethical violation: {deliberation_result.overall_reasoning}"
                    decision.violations = deliberation_result.concerns

                if deliberation_result.escalation_required:
                    decision.decision_type = "ESCALATE"
                    decision.reasoning = deliberation_result.escalation_reason or "Escalation required due to framework disagreement"

            except Exception as e:
                self.logger.error(f"[Governor] Deliberation failed: {e}")
                decision.allowed = False
                decision.decision_type = "DENY"
                decision.reasoning = f"Deliberation error: {str(e)}"

        # Step 2: Contradiction Detection
        if self.contradiction_detector and decision.deliberation:
            try:
                contradiction_analysis = self.contradiction_detector.analyze(
                    decision.deliberation
                )
                decision.contradictions = contradiction_analysis

                # High inconsistency may escalate
                if contradiction_analysis.consistency_score < 0.5:
                    decision.decision_type = "ESCALATE"
                    decision.reasoning += "\nHigh contradiction detected - escalating"

            except Exception as e:
                self.logger.error(f"[Governor] Contradiction detection failed: {e}")

        # Step 3: Precedent Consistency
        if self.precedent_engine and decision.allowed:
            try:
                # Extract principles from frameworks if available
                principles = []
                if decision.deliberation:
                    for framework in decision.deliberation.framework_analyses.values():
                        principles.extend(framework.affected_principles)

                precedent_analysis = self.precedent_engine.analyze_precedents(
                    action=action,
                    principles=principles if principles else None,
                )
                decision.precedent = precedent_analysis

                # Significant deviation from precedent may escalate
                if not precedent_analysis.precedent_consistency and high_impact:
                    decision.decision_type = "ESCALATE"
                    decision.reasoning += "\nDeviates from established precedents - escalating"

                # Store the decision as a precedent for future reference
                if decision.allowed:
                    self.precedent_engine.store_precedent(
                        action_description=action,
                        conclusion=PrecedentType.ALLOWED,
                        reasoning=decision.reasoning,
                        principles_involved=principles if principles else [],
                        confidence=decision.confidence,
                        context=context,
                    )

            except Exception as e:
                self.logger.error(f"[Governor] Precedent analysis failed: {e}")

        # Step 4: Threat Detection
        if self.threat_detector:
            try:
                # Convert framework analyses to dict format for threat detector
                framework_analyses_dict = {}
                if decision.deliberation:
                    for framework_type, analysis in decision.deliberation.framework_analyses.items():
                        framework_analyses_dict[framework_type.value] = {
                            "conclusion": analysis.conclusion.value,
                            "confidence": analysis.confidence,
                            "reasoning": analysis.reasoning,
                            "concerns": analysis.concerns,
                        }

                threat_analysis = self.threat_detector.analyze(
                    action=action,
                    framework_analyses=framework_analyses_dict,
                    contradiction_analysis={
                        "num_contradictions": len(decision.contradictions.contradictions) if decision.contradictions else 0,
                        "has_major_contradictions": decision.contradictions.has_major_contradictions if decision.contradictions else False,
                    },
                    precedent_analysis={
                        "consistent": decision.precedent.precedent_consistency if decision.precedent else True,
                        "recommended": decision.precedent.recommended_conclusion.value if decision.precedent and decision.precedent.recommended_conclusion else "allowed",
                    },
                    confidence=decision.confidence,
                    final_conclusion="allowed" if decision.allowed else "denied",
                )
                decision.threat_analysis = threat_analysis

                # Escalate if threats detected
                if not threat_analysis.is_safe:
                    decision.decision_type = "ESCALATE"
                    decision.reasoning += f"\nThreats detected: {threat_analysis.overall_threat_level.value}"
                    decision.allowed = False  # Conservative: deny if threats

            except Exception as e:
                self.logger.error(f"[Governor] Threat detection failed: {e}")

        # Step 5: TLS Validation (for inter-agent communication)
        if self.tls_manager and "target_agent" in context:
            try:
                target_agent = context["target_agent"]
                # Verify TLS configuration exists
                if target_agent not in self.tls_manager.configurations:
                    self.logger.warning(f"[Governor] No TLS config for {target_agent}")
                # TLS check doesn't block, just logs

            except Exception as e:
                self.logger.error(f"[Governor] TLS validation failed: {e}")

        # Build reasoning summary
        if not decision.reasoning:
            if decision.allowed:
                decision.reasoning = f"Action '{action}' approved by ethical framework"
            else:
                decision.reasoning = f"Action '{action}' violates ethical principles"

        # Store decision
        self.decisions[decision_id] = decision
        if decision.requires_escalation():
            self.escalations.append(decision)
            self.logger.warning(f"[Governor] Decision {decision_id} requires escalation")

        allowed = decision.allowed
        reasoning = decision.reasoning

        self.logger.info(
            f"[Governor] Decision: {decision.decision_type} "
            f"(confidence: {decision.confidence:.2f})"
        )

        return allowed, reasoning, decision

    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of all decisions made."""
        return {
            "total_decisions": len(self.decisions),
            "escalations": len(self.escalations),
            "allow_rate": sum(
                1 for d in self.decisions.values() if d.allowed
            ) / max(1, len(self.decisions)),
            "decisions": {
                did: {
                    "action": d.action,
                    "actor": d.actor,
                    "allowed": d.allowed,
                    "type": d.decision_type,
                    "confidence": d.confidence,
                }
                for did, d in self.decisions.items()
            },
        }

    def get_escalations(self) -> List[EthicalDecision]:
        """Get all decisions requiring escalation."""
        return self.escalations

    def export_decision_trail(self, decision_id: str) -> Dict[str, Any]:
        """Export complete reasoning trail for a decision."""
        if decision_id not in self.decisions:
            return {}

        decision = self.decisions[decision_id]

        # Build deliberation artifact
        deliberation_artifact = None
        if decision.deliberation:
            deliberation_artifact = {
                "action": decision.deliberation.action,
                "conclusion": decision.deliberation.final_conclusion.value,
                "confidence": decision.deliberation.confidence,
                "overall_reasoning": decision.deliberation.overall_reasoning,
                "escalation_required": decision.deliberation.escalation_required,
                "concerns": decision.deliberation.concerns,
            }

        return {
            "decision_id": decision_id,
            "action": decision.action,
            "actor": decision.actor,
            "allowed": decision.allowed,
            "decision_type": decision.decision_type,
            "timestamp": decision.timestamp.isoformat(),
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "violations": decision.violations,
            "reasoning_artifacts": {
                "deliberation": deliberation_artifact,
                "contradictions": {
                    "num_contradictions": len(decision.contradictions.contradictions),
                    "consistency_score": decision.contradictions.consistency_score,
                } if decision.contradictions else None,
                "precedent": {
                    "consistent": decision.precedent.precedent_consistency,
                    "historical_pattern": decision.precedent.historical_pattern,
                } if decision.precedent else None,
                "threat_analysis": {
                    "threats": len(decision.threat_analysis.threats),
                    "threat_level": decision.threat_analysis.overall_threat_level.value,
                    "risk_score": decision.threat_analysis.overall_risk_score,
                } if decision.threat_analysis else None,
            },
        }
