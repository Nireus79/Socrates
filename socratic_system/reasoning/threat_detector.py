"""
Advanced Threat Detection for Ethical Reasoning

Detects anomalies, suspicious patterns, and potential threats
in ethical decision-making processes.
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ThreatLevel(Enum):
    """Severity levels for detected threats."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of threats that can be detected."""

    REASONING_INCONSISTENCY = "reasoning_inconsistency"
    FRAMEWORK_MANIPULATION = "framework_manipulation"
    PRINCIPLE_VIOLATION = "principle_violation"
    STAKEHOLDER_HARM = "stakeholder_harm"
    PATTERN_ANOMALY = "pattern_anomaly"
    CONFIDENCE_MANIPULATION = "confidence_manipulation"
    ESCALATION_AVOIDANCE = "escalation_avoidance"
    PRECEDENT_DEVIATION = "precedent_deviation"


@dataclass
class Threat:
    """Represents a detected threat in reasoning."""

    threat_type: ThreatType
    severity: ThreatLevel
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    affected_components: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0.0-1.0
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __hash__(self):
        """Return hash of this object."""
        return hash((self.threat_type.value, self.description))


@dataclass
class ThreatProfile:
    """Profile of anomalous behavior."""

    baseline_mean: float
    baseline_std_dev: float
    observed_value: float
    deviation_score: float  # How many std devs away from mean
    is_anomalous: bool
    context: str = ""


@dataclass
class ThreatAnalysis:
    """Complete threat analysis for a reasoning session."""

    action: str
    threats: List[Threat] = field(default_factory=list)
    overall_threat_level: ThreatLevel = ThreatLevel.NONE
    overall_risk_score: float = 0.0
    is_safe: bool = True
    safety_concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ThreatDetector:
    """
    Detects threats and anomalies in ethical reasoning.

    Analyzes:
    - Reasoning consistency and internal contradictions
    - Framework agreement patterns for signs of manipulation
    - Principle alignment and violations
    - Stakeholder impact patterns
    - Statistical anomalies in confidence scores
    - Deviation from historical precedents
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize threat detector.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.confidence_history: List[float] = []
        self.conclusion_history: List[str] = []
        self.framework_agreement_history: List[float] = []

    def analyze(
        self,
        action: str,
        framework_analyses: Dict[str, Any],
        contradiction_analysis: Optional[Dict[str, Any]] = None,
        precedent_analysis: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
        final_conclusion: str = "unknown",
    ) -> ThreatAnalysis:
        """
        Analyze action for threats and anomalies.

        Args:
            action: Action description
            framework_analyses: Framework analysis results
            contradiction_analysis: Contradiction analysis results
            precedent_analysis: Precedent analysis results
            confidence: Confidence in final conclusion
            final_conclusion: Final conclusion reached

        Returns:
            ThreatAnalysis with detected threats
        """
        analysis = ThreatAnalysis(action=action)

        # Update history
        self.confidence_history.append(confidence)
        self.conclusion_history.append(final_conclusion)

        # Detect various threats
        threats = []

        # Detect reasoning inconsistencies
        inconsistency_threats = self._detect_reasoning_inconsistencies(
            framework_analyses, contradiction_analysis
        )
        threats.extend(inconsistency_threats)

        # Detect framework manipulation patterns
        manipulation_threats = self._detect_framework_manipulation(framework_analyses)
        threats.extend(manipulation_threats)

        # Detect principle violations
        principle_threats = self._detect_principle_violations(framework_analyses)
        threats.extend(principle_threats)

        # Detect stakeholder harm patterns
        harm_threats = self._detect_stakeholder_harm(framework_analyses)
        threats.extend(harm_threats)

        # Detect anomalous patterns
        anomaly_threats = self._detect_pattern_anomalies(confidence, final_conclusion)
        threats.extend(anomaly_threats)

        # Detect confidence manipulation
        confidence_threats = self._detect_confidence_manipulation(confidence, framework_analyses)
        threats.extend(confidence_threats)

        # Detect escalation avoidance
        escalation_threats = self._detect_escalation_avoidance(
            confidence, final_conclusion, contradiction_analysis
        )
        threats.extend(escalation_threats)

        # Detect precedent deviation
        precedent_threats = self._detect_precedent_deviation(
            action, final_conclusion, precedent_analysis
        )
        threats.extend(precedent_threats)

        # Set analysis results
        analysis.threats = threats

        # Calculate overall threat level
        if threats:
            max_severity = max(
                [
                    ThreatLevel.NONE,
                    ThreatLevel.LOW,
                    ThreatLevel.MEDIUM,
                    ThreatLevel.HIGH,
                    ThreatLevel.CRITICAL,
                ],
                key=lambda x: [
                    ThreatLevel.NONE,
                    ThreatLevel.LOW,
                    ThreatLevel.MEDIUM,
                    ThreatLevel.HIGH,
                    ThreatLevel.CRITICAL,
                ].index(x),
            )

            for threat in threats:
                if threat.severity == ThreatLevel.CRITICAL:
                    max_severity = ThreatLevel.CRITICAL
                    break
                elif threat.severity == ThreatLevel.HIGH:
                    max_severity = ThreatLevel.HIGH
                elif threat.severity == ThreatLevel.MEDIUM and max_severity != ThreatLevel.HIGH:
                    max_severity = ThreatLevel.MEDIUM
                elif threat.severity == ThreatLevel.LOW and max_severity == ThreatLevel.NONE:
                    max_severity = ThreatLevel.LOW

            analysis.overall_threat_level = max_severity

            # Calculate overall risk score (average of threat risk scores)
            risk_scores = [t.risk_score for t in threats]
            analysis.overall_risk_score = (
                sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            )
        else:
            analysis.overall_threat_level = ThreatLevel.NONE
            analysis.overall_risk_score = 0.0

        # Determine if action is safe
        analysis.is_safe = analysis.overall_threat_level in [ThreatLevel.NONE, ThreatLevel.LOW]

        # Collect safety concerns and recommendations
        analysis.safety_concerns = [t.description for t in threats]
        for threat in threats:
            analysis.recommendations.extend(threat.recommendations)

        self.logger.info(
            f"[Threat Analysis] {action} -> {analysis.overall_threat_level.value} "
            f"(risk: {analysis.overall_risk_score:.2f})"
        )

        return analysis

    def _detect_reasoning_inconsistencies(
        self,
        framework_analyses: Dict[str, Any],
        contradiction_analysis: Optional[Dict[str, Any]],
    ) -> List[Threat]:
        """Detect internal reasoning inconsistencies."""
        threats = []

        if not contradiction_analysis:
            return threats

        # Check for major contradictions
        num_contradictions = contradiction_analysis.get("num_contradictions", 0)
        if num_contradictions > 3:
            threat = Threat(
                threat_type=ThreatType.REASONING_INCONSISTENCY,
                severity=ThreatLevel.MEDIUM,
                description=f"Multiple reasoning inconsistencies detected ({num_contradictions})",
                risk_score=0.6,
                evidence={"contradiction_count": num_contradictions},
                recommendations=[
                    "Review all framework analyses",
                    "Check for logical errors",
                    "Consider escalation for human review",
                ],
            )
            threats.append(threat)

        return threats

    def _detect_framework_manipulation(self, framework_analyses: Dict[str, Any]) -> List[Threat]:
        """Detect signs of framework manipulation or gaming."""
        threats = []

        if not framework_analyses:
            return threats

        # Check for suspiciously uniform conclusions
        conclusions = [str(f.get("conclusion", "unknown")) for f in framework_analyses.values()]
        unique_conclusions = set(conclusions)

        if len(unique_conclusions) == 1 and len(conclusions) > 1:
            # All frameworks agree - could be sign of manipulation
            threat = Threat(
                threat_type=ThreatType.FRAMEWORK_MANIPULATION,
                severity=ThreatLevel.LOW,
                description="All frameworks reach identical conclusion (unusual pattern)",
                risk_score=0.3,
                evidence={
                    "conclusion": conclusions[0],
                    "num_frameworks": len(conclusions),
                },
                recommendations=[
                    "Verify framework independence",
                    "Check for shared biases",
                ],
            )
            threats.append(threat)

        return threats

    def _detect_principle_violations(self, framework_analyses: Dict[str, Any]) -> List[Threat]:
        """Detect violations of core principles."""
        threats = []

        # Check for blocked conclusions with allowed result
        for framework_name, analysis in framework_analyses.items():
            conclusion = str(analysis.get("conclusion", ""))

            # Detect when analysis cites concerns but conclusion is allowed
            concerns = analysis.get("concerns", [])
            if "allowed" in conclusion.lower() and len(concerns) > 2:
                threat = Threat(
                    threat_type=ThreatType.PRINCIPLE_VIOLATION,
                    severity=ThreatLevel.MEDIUM,
                    description=f"{framework_name}: Multiple concerns but action allowed",
                    risk_score=0.55,
                    evidence={
                        "framework": framework_name,
                        "concern_count": len(concerns),
                    },
                    recommendations=[
                        "Re-examine principle alignment",
                        "Address concerns before allowing",
                    ],
                )
                threats.append(threat)

        return threats

    def _detect_stakeholder_harm(self, framework_analyses: Dict[str, Any]) -> List[Threat]:
        """Detect patterns indicating stakeholder harm."""
        threats = []

        # Check for patterns suggesting stakeholder harm
        for framework_name, analysis in framework_analyses.items():
            reasoning = str(analysis.get("reasoning", "")).lower()
            conclusion = str(analysis.get("conclusion", ""))

            # Look for vulnerable/harm keywords with allowed conclusions
            harmful_keywords = [
                "vulnerable",
                "harm",
                "exploit",
                "endanger",
                "minority",
            ]

            if any(k in reasoning for k in harmful_keywords):
                if "allowed" in conclusion.lower():
                    threat = Threat(
                        threat_type=ThreatType.STAKEHOLDER_HARM,
                        severity=ThreatLevel.HIGH,
                        description="Action may harm stakeholders but is allowed",
                        risk_score=0.8,
                        evidence={"framework": framework_name},
                        recommendations=[
                            "Verify stakeholder protections",
                            "Consider blocking action",
                            "Escalate for human review",
                        ],
                    )
                    threats.append(threat)

        return threats

    def _detect_pattern_anomalies(self, confidence: float, conclusion: str) -> List[Threat]:
        """Detect anomalies in reasoning patterns."""
        threats = []

        if len(self.confidence_history) < 5:
            return threats  # Need enough history for patterns

        # Analyze confidence pattern
        recent_confidences = self.confidence_history[-5:]
        try:
            mean_confidence = statistics.mean(recent_confidences)
            if len(recent_confidences) > 1:
                std_dev = statistics.stdev(recent_confidences)
            else:
                std_dev = 0

            # Check for outlier
            if std_dev > 0:
                z_score = abs((confidence - mean_confidence) / std_dev)
                if z_score > 2.5:  # More than 2.5 std devs away
                    threat = Threat(
                        threat_type=ThreatType.PATTERN_ANOMALY,
                        severity=ThreatLevel.MEDIUM,
                        description=f"Confidence anomaly: {confidence:.2f} (typical: {mean_confidence:.2f})",
                        risk_score=0.5,
                        evidence={
                            "confidence": confidence,
                            "mean": mean_confidence,
                            "z_score": z_score,
                        },
                        recommendations=[
                            "Review confidence calculation",
                            "Verify framework analyses",
                        ],
                    )
                    threats.append(threat)
        except Exception as e:
            self.logger.debug(f"Could not analyze confidence pattern: {e}")

        return threats

    def _detect_confidence_manipulation(
        self, confidence: float, framework_analyses: Dict[str, Any]
    ) -> List[Threat]:
        """Detect signs of confidence score manipulation."""
        threats = []

        if not framework_analyses:
            return threats

        framework_confidences = [
            float(f.get("confidence", 0.5)) for f in framework_analyses.values()
        ]

        if not framework_confidences:
            return threats

        # Check if final confidence is higher than all frameworks
        max_framework_confidence = max(framework_confidences)
        if confidence > max_framework_confidence + 0.1:
            threat = Threat(
                threat_type=ThreatType.CONFIDENCE_MANIPULATION,
                severity=ThreatLevel.MEDIUM,
                description=f"Final confidence ({confidence:.2f}) exceeds all framework confidences",
                risk_score=0.55,
                evidence={
                    "final_confidence": confidence,
                    "max_framework_confidence": max_framework_confidence,
                },
                recommendations=[
                    "Review confidence synthesis algorithm",
                    "Ensure confidence matches evidence",
                ],
            )
            threats.append(threat)

        return threats

    def _detect_escalation_avoidance(
        self,
        confidence: float,
        conclusion: str,
        contradiction_analysis: Optional[Dict[str, Any]],
    ) -> List[Threat]:
        """Detect attempts to avoid escalation inappropriately."""
        threats = []

        # Check for escalation that should have occurred
        if contradiction_analysis:
            has_major_contradictions = contradiction_analysis.get("has_major_contradictions", False)
            if has_major_contradictions and "escalate" not in conclusion.lower():
                threat = Threat(
                    threat_type=ThreatType.ESCALATION_AVOIDANCE,
                    severity=ThreatLevel.HIGH,
                    description="Major contradictions detected but action not escalated",
                    risk_score=0.75,
                    recommendations=[
                        "Escalate for human review",
                        "Address contradictions",
                    ],
                )
                threats.append(threat)

        return threats

    def _detect_precedent_deviation(
        self,
        action: str,
        conclusion: str,
        precedent_analysis: Optional[Dict[str, Any]],
    ) -> List[Threat]:
        """Detect deviations from established precedents."""
        threats = []

        if not precedent_analysis:
            return threats

        precedent_consistency = precedent_analysis.get("consistent", True)
        recommended_conclusion = precedent_analysis.get("recommended")

        if not precedent_consistency and recommended_conclusion:
            if str(conclusion).lower() != str(recommended_conclusion).lower():
                threat = Threat(
                    threat_type=ThreatType.PRECEDENT_DEVIATION,
                    severity=ThreatLevel.MEDIUM,
                    description=f"Conclusion deviates from {recommended_conclusion} precedents",
                    risk_score=0.6,
                    evidence={
                        "recommended": recommended_conclusion,
                        "actual": conclusion,
                    },
                    recommendations=[
                        "Review precedent consistency",
                        "Justify deviation from precedents",
                        "Update precedents if needed",
                    ],
                )
                threats.append(threat)

        return threats

    def get_baseline_stats(self) -> Dict[str, float]:
        """Get baseline statistics from history."""
        if not self.confidence_history:
            return {
                "mean_confidence": 0.0,
                "std_dev_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 1.0,
            }

        try:
            mean = statistics.mean(self.confidence_history)
            std_dev = (
                statistics.stdev(self.confidence_history)
                if len(self.confidence_history) > 1
                else 0.0
            )
            return {
                "mean_confidence": mean,
                "std_dev_confidence": std_dev,
                "min_confidence": min(self.confidence_history),
                "max_confidence": max(self.confidence_history),
                "sample_count": len(self.confidence_history),
            }
        except Exception as e:
            self.logger.warning(f"Could not calculate baseline stats: {e}")
            return {}
