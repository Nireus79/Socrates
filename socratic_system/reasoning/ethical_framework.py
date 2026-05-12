"""
Ethical Frameworks for Multi-Framework Decision Analysis

Implements Kantian, Utilitarian, Virtue, Rights-Based, and Care Ethics
frameworks for comprehensive ethical reasoning.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EthicalFrameworkType(Enum):
    """Types of ethical frameworks."""

    KANTIAN = "kantian"
    UTILITARIAN = "utilitarian"
    VIRTUE = "virtue"
    RIGHTS_BASED = "rights_based"
    CARE_ETHICS = "care_ethics"


class EthicalConclusion(Enum):
    """Conclusion of ethical analysis."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    ESCALATE = "escalate"


@dataclass
class FrameworkAnalysis:
    """Result of analyzing action through one ethical framework."""

    framework: EthicalFrameworkType
    conclusion: EthicalConclusion
    confidence: float  # 0.0-1.0
    reasoning: str
    concerns: list[str]
    affected_principles: list[str]
    timestamp: datetime | None = None

    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class EthicalFramework(ABC):
    """
    Abstract base class for ethical frameworks.

    Each framework provides analysis of proposed actions through a specific
    ethical lens (deontological, consequentialist, virtue-based, etc).
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize framework.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.name = self.__class__.__name__

    @abstractmethod
    def analyze(
        self,
        action: str,
        context: dict[str, Any],
        stakeholders: list[dict[str, Any]],
        principles: list[str],
        consequences: dict[str, Any],
    ) -> FrameworkAnalysis:
        """
        Analyze action through this framework's lens.

        Args:
            action: Description of proposed action
            context: Context information
            stakeholders: List of affected stakeholders
            principles: Constitutional principles involved
            consequences: Projected consequences (short and long-term)

        Returns:
            FrameworkAnalysis with conclusion and reasoning
        """
        pass

    def _get_framework_type(self) -> EthicalFrameworkType:
        """Get framework type from class name."""
        name = self.name.lower()
        if "kantian" in name:
            return EthicalFrameworkType.KANTIAN
        elif "utilitarian" in name:
            return EthicalFrameworkType.UTILITARIAN
        elif "virtue" in name:
            return EthicalFrameworkType.VIRTUE
        elif "rights" in name:
            return EthicalFrameworkType.RIGHTS_BASED
        elif "care" in name:
            return EthicalFrameworkType.CARE_ETHICS
        return EthicalFrameworkType.KANTIAN


class KantianAnalyzer(EthicalFramework):
    """
    Kantian (Deontological) Framework.

    Focuses on duties, rights, and treating people as ends in themselves,
    not merely as means.

    Key Principles:
    - Categorical imperative (act only as if you'd will it to be universal law)
    - Respect for autonomy and dignity
    - Rights and duties
    - Intentions matter
    """

    def analyze(
        self,
        action: str,
        context: dict[str, Any],
        stakeholders: list[dict[str, Any]],
        principles: list[str],
        consequences: dict[str, Any],
    ) -> FrameworkAnalysis:
        """Analyze through Kantian lens."""
        conclusion = EthicalConclusion.ALLOWED
        confidence = 1.0
        concerns = []
        reasoning_parts = []

        # Check if action treats people as ends in themselves
        if self._treats_as_means_only(action, stakeholders):
            conclusion = EthicalConclusion.BLOCKED
            confidence = 0.95
            concerns.append("Treats people merely as means, not as ends in themselves")
            reasoning_parts.append("Violates respect for autonomy and dignity")

        # Check categorical imperative (universalizability)
        if not self._universalizable(action, context):
            conclusion = EthicalConclusion.BLOCKED
            confidence = min(confidence, 0.85)
            concerns.append("Action fails universalization test (wouldn't want it universal)")
            reasoning_parts.append("Cannot be consistently universalized")

        # Check for duty violations
        duties_violated = self._check_duty_violations(action, stakeholders, context)
        if duties_violated:
            conclusion = EthicalConclusion.BLOCKED
            confidence = min(confidence, 0.9)
            for duty in duties_violated:
                concerns.append(f"Violates duty: {duty}")
            reasoning_parts.append(f"Violates {len(duties_violated)} duties")

        reasoning = (
            " | ".join(reasoning_parts)
            if reasoning_parts
            else "Action respects autonomy, passes universalization test, fulfills duties"
        )

        return FrameworkAnalysis(
            framework=EthicalFrameworkType.KANTIAN,
            conclusion=conclusion,
            confidence=confidence,
            reasoning=reasoning,
            concerns=concerns,
            affected_principles=principles,
        )

    def _treats_as_means_only(self, action: str, stakeholders: list[dict[str, Any]]) -> bool:
        """Check if action treats anyone merely as a means."""
        means_patterns = [
            "exploit",
            "manipulate",
            "deceive",
            "hide",
            "exclude",
            "coerce",
            "force",
            "deny_autonomy",
            "override_consent",
        ]

        action_lower = action.lower()
        if any(pattern in action_lower for pattern in means_patterns):
            # Check if stakeholders have autonomy violated
            if stakeholders:
                # Mark this as deceptive/manipulative in reasoning
                return True

        return False

    def _universalizable(self, action: str, context: dict[str, Any]) -> bool:
        """Check if action passes universalization test."""
        # Actions that couldn't be universal laws
        non_universalizable = [
            "lie",
            "deceive",
            "break promise",
            "harm innocently",
            "refuse help",
            "exploit",
            "hide truth",
        ]

        action_lower = action.lower()
        for pattern in non_universalizable:
            if pattern in action_lower:
                return False

        return True

    def _check_duty_violations(
        self, action: str, stakeholders: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[str]:
        """Check for violations of basic duties."""
        violations = []

        action_lower = action.lower()

        # Duty to tell truth
        if any(w in action_lower for w in ["hide", "deceive", "lie"]):
            violations.append("honesty/truthfulness")

        # Duty to respect autonomy
        if any(w in action_lower for w in ["override", "coerce", "manipulate"]):
            violations.append("respect for autonomy")

        # Duty to keep promises
        if "break promise" in action_lower:
            violations.append("promise-keeping")

        # Duty not to harm innocents
        if any(w in action_lower for w in ["harm", "endanger", "injure"]):
            violations.append("non-maleficence")

        return violations


class UtilitarianAnalyzer(EthicalFramework):
    """
    Utilitarian (Consequentialist) Framework.

    Focuses on maximizing overall happiness/well-being and minimizing suffering.

    Key Principles:
    - Greatest good for greatest number
    - Consequences are what matter
    - Pleasure/pain calculation
    - Impartial consideration of all affected parties
    """

    def analyze(
        self,
        action: str,
        context: dict[str, Any],
        stakeholders: list[dict[str, Any]],
        principles: list[str],
        consequences: dict[str, Any],
    ) -> FrameworkAnalysis:
        """Analyze through utilitarian lens."""
        conclusion = EthicalConclusion.ALLOWED
        confidence = 0.7  # Utilitarian calculations often uncertain
        concerns = []
        reasoning_parts = []

        # Calculate utility balance
        short_term = consequences.get("short_term", {})
        long_term = consequences.get("long_term", {})

        total_benefit = short_term.get("benefit", 0) + long_term.get("benefit", 0)
        total_harm = short_term.get("harm", 0) + long_term.get("harm", 0)

        if total_harm > total_benefit:
            conclusion = EthicalConclusion.BLOCKED
            confidence = 0.8 if long_term.get("harm", 0) > short_term.get("benefit", 0) else 0.6
            concerns.append(f"Net harm: {total_harm - total_benefit}")
            reasoning_parts.append(f"Harms ({total_harm}) outweigh benefits ({total_benefit})")

        # Check for extreme harm to minorities
        if self._extreme_harm_to_minorities(stakeholders, consequences):
            conclusion = EthicalConclusion.ESCALATE
            confidence = min(confidence, 0.7)
            concerns.append("Extreme harm concentrated on small group")
            reasoning_parts.append("Potential injustice to minority requires escalation")

        # Check long-term consequences
        if long_term.get("harm", 0) > long_term.get("benefit", 0):
            confidence = min(confidence, 0.75)
            reasoning_parts.append("Long-term harms concerning")

        reasoning = (
            " | ".join(reasoning_parts)
            if reasoning_parts
            else f"Net positive: benefits ({total_benefit}) exceed harms ({total_harm})"
        )

        return FrameworkAnalysis(
            framework=EthicalFrameworkType.UTILITARIAN,
            conclusion=conclusion,
            confidence=confidence,
            reasoning=reasoning,
            concerns=concerns,
            affected_principles=principles,
        )

    def _extreme_harm_to_minorities(
        self, stakeholders: list[dict[str, Any]], consequences: dict[str, Any]
    ) -> bool:
        """Check if harm is concentrated on small vulnerable groups."""
        if not stakeholders or len(stakeholders) < 2:
            return False

        # Get harm distribution
        harms = []
        for s in stakeholders:
            # Handle both dict and dataclass stakeholders
            stakeholder_id = s.get("id", "") if isinstance(s, dict) else getattr(s, "id", "")
            vulnerability = (
                s.get("vulnerability", 0) if isinstance(s, dict) else getattr(s, "vulnerability", 0)
            )
            harms.append((stakeholder_id, vulnerability))

        # Check for concentrated harm on vulnerable
        vulnerable = [h for h in harms if h[1] > 0.7]
        if vulnerable and consequences.get("short_term", {}).get("harm", 0) > 0.5:
            return True

        return False


class VirtueAnalyzer(EthicalFramework):
    """
    Virtue Ethics Framework.

    Focuses on developing good character traits and what a virtuous
    person would do in a situation.

    Key Principles:
    - Character and virtue development
    - Excellence (arete)
    - Practical wisdom (phronesis)
    - Eudaimonia (flourishing)
    - Avoiding vices
    """

    def analyze(
        self,
        action: str,
        context: dict[str, Any],
        stakeholders: list[dict[str, Any]],
        principles: list[str],
        consequences: dict[str, Any],
    ) -> FrameworkAnalysis:
        """Analyze through virtue ethics lens."""
        conclusion = EthicalConclusion.ALLOWED
        confidence = 0.8
        concerns = []
        reasoning_parts = []

        # Check for virtuous character expression
        vices_demonstrated = self._identify_vices(action)
        if vices_demonstrated:
            conclusion = EthicalConclusion.BLOCKED
            confidence = 0.9
            for vice in vices_demonstrated:
                concerns.append(f"Demonstrates vice: {vice}")
            reasoning_parts.append(f"Action reflects {len(vices_demonstrated)} vices")

        # Check for virtues
        virtues_expressed = self._identify_virtues(action, context)
        if not virtues_expressed:
            conclusion = EthicalConclusion.BLOCKED
            confidence = 0.85
            concerns.append("No virtues expressed; reflects poor character")
            reasoning_parts.append("Does not reflect virtuous character")
        else:
            reasoning_parts.append(f"Expresses virtues: {', '.join(virtues_expressed)}")

        # Check for human flourishing
        if not self._promotes_flourishing(stakeholders, consequences):
            conclusion = EthicalConclusion.ESCALATE
            confidence = min(confidence, 0.75)
            concerns.append("Does not promote human flourishing")
            reasoning_parts.append("May inhibit flourishing of affected parties")

        reasoning = (
            " | ".join(reasoning_parts)
            if reasoning_parts
            else "Action reflects virtuous character and promotes flourishing"
        )

        return FrameworkAnalysis(
            framework=EthicalFrameworkType.VIRTUE,
            conclusion=conclusion,
            confidence=confidence,
            reasoning=reasoning,
            concerns=concerns,
            affected_principles=principles,
        )

    def _identify_vices(self, action: str) -> list[str]:
        """Identify vices the action demonstrates."""
        vices = []
        action_lower = action.lower()

        vice_patterns = {
            "deception": ["lie", "deceive", "hide", "falsify"],
            "cowardice": ["avoid", "shirk", "hide from"],
            "cruelty": ["harm", "hurt", "injure", "torture"],
            "injustice": ["exploit", "steal", "cheat", "defraud"],
            "excess": ["overindulge", "consume excessively"],
            "greed": ["hoard", "accumulate selfishly"],
            "arrogance": ["boast", "show off", "disdain"],
            "apathy": ["ignore suffering", "don't care"],
        }

        for vice, patterns in vice_patterns.items():
            if any(p in action_lower for p in patterns):
                vices.append(vice)

        return vices

    def _identify_virtues(self, action: str, context: dict[str, Any]) -> list[str]:
        """Identify virtues the action demonstrates."""
        virtues = []
        action_lower = action.lower()

        virtue_patterns = {
            "honesty": ["tell truth", "transparent", "honest", "disclose"],
            "courage": ["face challenge", "brave", "stand firm", "overcome"],
            "compassion": ["help", "care", "support", "aid", "protect"],
            "justice": ["fair", "equitable", "righteous", "protect", "secure"],
            "temperance": ["measured", "balanced", "moderate", "careful"],
            "wisdom": ["carefully consider", "thoughtful", "reflective", "improve", "optimize"],
            "generosity": ["give", "share", "donate", "help freely", "enable"],
            "humility": ["acknowledge limits", "humble", "admit error"],
        }

        for virtue, patterns in virtue_patterns.items():
            if any(p in action_lower for p in patterns):
                virtues.append(virtue)

        # If action promotes general good/improvement, consider it virtuous
        if any(
            word in action_lower
            for word in ["improve", "optimize", "secure", "reliable", "safe", "enhance"]
        ):
            if "wisdom" not in virtues:
                virtues.append("wisdom")

        return virtues

    def _promotes_flourishing(
        self, stakeholders: list[dict[str, Any]], consequences: dict[str, Any]
    ) -> bool:
        """Check if action promotes human flourishing."""
        if not stakeholders:
            return True

        # Flourishing includes autonomy, growth, relationships, health
        flourishing_factors = [
            "autonomy",
            "growth",
            "relationships",
            "health",
            "knowledge",
            "development",
            "well-being",
            "improve",
            "secure",
            "reliable",
            "beneficial",
            "good",
        ]

        consequences_text = str(consequences).lower()
        has_flourishing = any(f in consequences_text for f in flourishing_factors)

        # If we have positive consequences with high benefit, assume flourishing
        if consequences.get("short_term", {}).get("benefit", 0) > 0.3:
            has_flourishing = True

        return has_flourishing


class RightsAnalyzer(EthicalFramework):
    """
    Rights-Based Framework.

    Focuses on protecting and respecting fundamental human rights.

    Key Principles:
    - Universal human rights
    - Dignity and worth
    - Consent and autonomy
    - Justice and fairness
    - Protection of vulnerable
    """

    def analyze(
        self,
        action: str,
        context: dict[str, Any],
        stakeholders: list[dict[str, Any]],
        principles: list[str],
        consequences: dict[str, Any],
    ) -> FrameworkAnalysis:
        """Analyze through rights-based lens."""
        conclusion = EthicalConclusion.ALLOWED
        confidence = 0.9
        concerns = []
        reasoning_parts = []

        # Check for rights violations
        rights_violated = self._identify_rights_violations(action, stakeholders, context)
        if rights_violated:
            conclusion = EthicalConclusion.BLOCKED
            confidence = 0.95
            for right in rights_violated:
                concerns.append(f"Violates: {right}")
            reasoning_parts.append(f"Violates {len(rights_violated)} fundamental rights")

        # Check consent
        if not self._consent_obtained(stakeholders, context):
            conclusion = EthicalConclusion.BLOCKED
            confidence = min(confidence, 0.9)
            concerns.append("No informed consent from affected parties")
            reasoning_parts.append("Violates right to informed consent")

        # Check for protecting vulnerable
        if not self._protects_vulnerable(stakeholders):
            conclusion = EthicalConclusion.ESCALATE
            confidence = min(confidence, 0.75)
            concerns.append("Does not adequately protect vulnerable populations")
            reasoning_parts.append("Vulnerable populations at risk")

        reasoning = (
            " | ".join(reasoning_parts)
            if reasoning_parts
            else "Action respects all fundamental rights and obtains consent"
        )

        return FrameworkAnalysis(
            framework=EthicalFrameworkType.RIGHTS_BASED,
            conclusion=conclusion,
            confidence=confidence,
            reasoning=reasoning,
            concerns=concerns,
            affected_principles=principles,
        )

    def _identify_rights_violations(
        self, action: str, stakeholders: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[str]:
        """Identify fundamental rights violations."""
        violations = []
        action_lower = action.lower()

        right_patterns = {
            "right to life": ["kill", "harm", "endanger life"],
            "right to privacy": ["spy", "surveil", "monitor without consent", "expose private"],
            "right to freedom": ["imprison", "coerce", "restrict movement"],
            "right to information": ["hide", "withhold", "misinformation", "censor"],
            "right to dignity": ["humiliate", "degrade", "torture", "disrespect"],
            "right to consent": ["without permission", "non-consensual", "override consent"],
            "right to property": ["steal", "confiscate", "destroy property"],
            "right to justice": ["discriminate", "unjust", "bias"],
        }

        for right, patterns in right_patterns.items():
            if any(p in action_lower for p in patterns):
                violations.append(right)

        return violations

    def _consent_obtained(
        self, stakeholders: list[dict[str, Any]], context: dict[str, Any]
    ) -> bool:
        """Check if informed consent obtained from affected parties."""
        # Check if consent was explicitly denied or not given
        consent_given = context.get("consent_obtained", False)
        informed = context.get("informed", False)

        if not stakeholders:
            return True

        # If explicitly marked as no consent, block
        if consent_given is False:
            return False

        # If not specified, assume consent not required for system-wide improvements
        # (unless action involves personal data or private matters)
        action = context.get("action", "").lower() if isinstance(context.get("action"), str) else ""
        if any(word in action for word in ["data", "privacy", "personal", "medical", "financial"]):
            # Data-related actions require explicit consent
            return bool(consent_given and informed)

        # For general system improvements, assume reasonable consent
        return True

    def _protects_vulnerable(self, stakeholders: list[dict[str, Any]]) -> bool:
        """Check if vulnerable populations are protected."""
        if not stakeholders:
            return True

        # Check for vulnerable people (children, elderly, disabled, disadvantaged)
        vulnerable_indicators = ["minor", "elderly", "disabled", "vulnerable", "disadvantaged"]

        for stakeholder in stakeholders:
            # Handle both dict and dataclass stakeholders
            if isinstance(stakeholder, dict):
                is_vulnerable = stakeholder.get("vulnerability", 0) > 0.5
            else:
                is_vulnerable = getattr(stakeholder, "vulnerability", 0) > 0.5

            if is_vulnerable:
                # Vulnerable person must be protected
                needs_protection = any(
                    ind in str(stakeholder).lower() for ind in vulnerable_indicators
                )
                if needs_protection:
                    return True

        return True
