"""
Stakeholder Analysis for Ethical Reasoning

Identifies and analyzes stakeholders affected by proposed actions,
including assessment of impact, vulnerability, and affected rights.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging


class StakeholderType(Enum):
    """Types of stakeholders."""
    USER = "user"
    AGENT = "agent"
    ORGANIZATION = "organization"
    SOCIETY = "society"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


class ImpactSeverity(Enum):
    """Severity of impact on stakeholder."""
    NONE = 0.0
    MINIMAL = 0.2
    LOW = 0.4
    MODERATE = 0.6
    HIGH = 0.8
    CRITICAL = 1.0


@dataclass
class Impact:
    """Impact on a particular stakeholder."""
    affected_party: str
    impact_type: str  # "positive", "negative", "neutral"
    severity: float  # 0.0-1.0
    timeframe: str  # "immediate", "short_term", "long_term"
    reversibility: str  # "reversible", "partially_reversible", "irreversible"
    description: str
    affected_rights: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash((self.affected_party, self.impact_type))


@dataclass
class Stakeholder:
    """Representation of a stakeholder affected by an action."""
    id: str
    name: str
    stakeholder_type: StakeholderType
    vulnerability: float  # 0.0-1.0 (how vulnerable/protected)
    power: float  # 0.0-1.0 (ability to influence/resist)
    interest: float  # 0.0-1.0 (how much affected)
    characteristics: Dict[str, Any] = field(default_factory=dict)
    affected_interests: List[str] = field(default_factory=list)
    affected_rights: List[str] = field(default_factory=list)

    def is_vulnerable(self) -> bool:
        """Check if stakeholder is considered vulnerable."""
        return self.vulnerability > 0.5

    def has_power_to_resist(self) -> bool:
        """Check if stakeholder can resist the action."""
        return self.power > 0.5

    def is_highly_affected(self) -> bool:
        """Check if stakeholder is highly affected."""
        return self.interest > 0.7


@dataclass
class StakeholderAnalysis:
    """Complete analysis of all stakeholders affected by an action."""
    action: str
    stakeholders: List[Stakeholder] = field(default_factory=list)
    impacts: List[Impact] = field(default_factory=list)
    vulnerable_groups: List[Stakeholder] = field(default_factory=list)
    powerless_affected: List[Stakeholder] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def has_vulnerable_affected(self) -> bool:
        """Check if action affects vulnerable stakeholders negatively."""
        return len(self.vulnerable_groups) > 0

    def has_powerless_affected(self) -> bool:
        """Check if powerless people are affected."""
        return len(self.powerless_affected) > 0

    def total_positive_impact(self) -> float:
        """Calculate total positive impact across stakeholders."""
        return sum(
            i.severity for i in self.impacts
            if i.impact_type == "positive"
        )

    def total_negative_impact(self) -> float:
        """Calculate total negative impact across stakeholders."""
        return sum(
            i.severity for i in self.impacts
            if i.impact_type == "negative"
        )

    def net_impact(self) -> float:
        """Net impact (positive minus negative)."""
        return self.total_positive_impact() - self.total_negative_impact()

    def affected_rights_summary(self) -> Dict[str, int]:
        """Summary of affected rights and frequency."""
        rights_count = {}
        for stakeholder in self.stakeholders:
            for right in stakeholder.affected_rights:
                rights_count[right] = rights_count.get(right, 0) + 1
        return rights_count


class StakeholderAnalyzer:
    """
    Analyzes stakeholders and impacts of proposed actions.

    Identifies who is affected, how they're affected, and their
    vulnerability to negative impacts.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize stakeholder analyzer.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def analyze(
        self,
        action: str,
        context: Dict[str, Any],
        additional_stakeholders: Optional[List[Dict[str, Any]]] = None
    ) -> StakeholderAnalysis:
        """
        Analyze stakeholders affected by proposed action.

        Args:
            action: Description of the action
            context: Context information (e.g., who it affects, scope)
            additional_stakeholders: Additional stakeholder definitions

        Returns:
            StakeholderAnalysis with identified stakeholders and impacts
        """
        analysis = StakeholderAnalysis(action=action)

        # Identify stakeholders from context
        stakeholders = self._identify_stakeholders(action, context)

        # Add any additional provided stakeholders
        if additional_stakeholders:
            stakeholders.extend(
                self._parse_stakeholders(additional_stakeholders)
            )

        analysis.stakeholders = stakeholders

        # Analyze impacts on each stakeholder
        impacts = self._analyze_impacts(action, stakeholders, context)
        analysis.impacts = impacts

        # Identify vulnerable groups affected
        analysis.vulnerable_groups = [
            s for s in stakeholders
            if s.is_vulnerable() and any(
                i.affected_party == s.id and i.impact_type == "negative"
                for i in impacts
            )
        ]

        # Identify powerless affected
        analysis.powerless_affected = [
            s for s in stakeholders
            if not s.has_power_to_resist() and any(
                i.affected_party == s.id and i.impact_type == "negative"
                for i in impacts
            )
        ]

        self.logger.info(
            f"[Stakeholder Analysis] Action: {action} | "
            f"Stakeholders: {len(stakeholders)} | "
            f"Vulnerable affected: {len(analysis.vulnerable_groups)} | "
            f"Net impact: {analysis.net_impact():.2f}"
        )

        return analysis

    def _identify_stakeholders(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> List[Stakeholder]:
        """Identify stakeholders from action and context."""
        stakeholders = []

        # Always affected: users/organization
        if context.get("scope", "").lower() in ["system_wide", "all", "global"]:
            stakeholders.append(Stakeholder(
                id="all_users",
                name="All Users",
                stakeholder_type=StakeholderType.USER,
                vulnerability=0.5,  # Users generally moderately vulnerable
                power=0.3,  # Limited power against system
                interest=0.9,  # Highly affected
                affected_interests=["transparency", "security", "control"],
                affected_rights=["privacy", "informed_consent", "information"]
            ))

            stakeholders.append(Stakeholder(
                id="organization",
                name="Organization",
                stakeholder_type=StakeholderType.ORGANIZATION,
                vulnerability=0.0,  # Organization not vulnerable
                power=1.0,  # Has maximum power
                interest=1.0,  # Directly affected
                affected_interests=["reputation", "liability", "operations"],
                affected_rights=["property"]
            ))

            stakeholders.append(Stakeholder(
                id="society",
                name="Society",
                stakeholder_type=StakeholderType.SOCIETY,
                vulnerability=0.6,  # Society moderately vulnerable
                power=0.2,  # Limited direct power
                interest=0.5,  # Somewhat affected
                affected_interests=["public_good", "trust", "accountability"],
                affected_rights=["information", "justice"]
            ))

        elif context.get("scope", "").lower() in ["specific", "targeted", "limited"]:
            # Specific users affected
            num_affected = context.get("num_affected", 1)
            if num_affected == 1:
                stakeholders.append(Stakeholder(
                    id="specific_user",
                    name="Specific User",
                    stakeholder_type=StakeholderType.USER,
                    vulnerability=self._assess_vulnerability(context),
                    power=0.2,
                    interest=1.0,
                    affected_interests=["autonomy", "privacy", "consent"],
                    affected_rights=["privacy", "informed_consent"]
                ))
            else:
                stakeholders.append(Stakeholder(
                    id="group_users",
                    name=f"Group of {num_affected} Users",
                    stakeholder_type=StakeholderType.USER,
                    vulnerability=self._assess_vulnerability(context),
                    power=0.3,
                    interest=1.0,
                    affected_interests=["autonomy", "privacy", "justice"],
                    affected_rights=["privacy", "informed_consent", "justice"]
                ))

        # Check for vulnerable populations
        if self._mentions_vulnerable_group(context):
            stakeholders.append(Stakeholder(
                id="vulnerable_group",
                name="Vulnerable Population",
                stakeholder_type=StakeholderType.USER,
                vulnerability=0.9,  # Very vulnerable
                power=0.1,  # Very little power
                interest=1.0,  # Directly affected
                characteristics={"vulnerable_group": True},
                affected_interests=["protection", "dignity", "justice"],
                affected_rights=["dignity", "protection", "justice"]
            ))

        return stakeholders

    def _parse_stakeholders(
        self,
        stakeholder_dicts: List[Dict[str, Any]]
    ) -> List[Stakeholder]:
        """Parse stakeholder dictionaries into Stakeholder objects."""
        stakeholders = []
        for s_dict in stakeholder_dicts:
            try:
                stakeholder = Stakeholder(
                    id=s_dict.get("id", "unknown"),
                    name=s_dict.get("name", "Unknown Stakeholder"),
                    stakeholder_type=self._parse_type(s_dict.get("type", "unknown")),
                    vulnerability=float(s_dict.get("vulnerability", 0.5)),
                    power=float(s_dict.get("power", 0.5)),
                    interest=float(s_dict.get("interest", 0.5)),
                    characteristics=s_dict.get("characteristics", {}),
                    affected_interests=s_dict.get("affected_interests", []),
                    affected_rights=s_dict.get("affected_rights", [])
                )
                stakeholders.append(stakeholder)
            except Exception as e:
                self.logger.warning(f"Failed to parse stakeholder: {e}")

        return stakeholders

    def _analyze_impacts(
        self,
        action: str,
        stakeholders: List[Stakeholder],
        context: Dict[str, Any]
    ) -> List[Impact]:
        """Analyze impacts of action on stakeholders."""
        impacts = []

        for stakeholder in stakeholders:
            impact = self._assess_impact(action, stakeholder, context)
            if impact:
                impacts.append(impact)

        return impacts

    def _assess_impact(
        self,
        action: str,
        stakeholder: Stakeholder,
        context: Dict[str, Any]
    ) -> Optional[Impact]:
        """Assess impact of action on specific stakeholder."""
        action_lower = action.lower()

        # Determine impact type
        impact_type = "neutral"
        if any(w in action_lower for w in ["help", "protect", "enable", "improve"]):
            impact_type = "positive"
        elif any(w in action_lower for w in ["harm", "restrict", "hide", "deny"]):
            impact_type = "negative"

        if impact_type == "neutral":
            return None

        # Determine severity
        severity = self._calculate_severity(action, stakeholder, context)

        # Determine timeframe
        if any(w in action_lower for w in ["immediately", "now", "instant"]):
            timeframe = "immediate"
        elif any(w in action_lower for w in ["soon", "short term", "next"]):
            timeframe = "short_term"
        else:
            timeframe = "long_term"

        # Determine reversibility
        if any(w in action_lower for w in ["temporary", "reversible", "undo"]):
            reversibility = "reversible"
        elif any(w in action_lower for w in ["partially", "semi"]):
            reversibility = "partially_reversible"
        else:
            reversibility = "irreversible"

        return Impact(
            affected_party=stakeholder.id,
            impact_type=impact_type,
            severity=severity,
            timeframe=timeframe,
            reversibility=reversibility,
            description=f"{impact_type.capitalize()} impact on {stakeholder.name}",
            affected_rights=stakeholder.affected_rights
        )

    def _calculate_severity(
        self,
        action: str,
        stakeholder: Stakeholder,
        context: Dict[str, Any]
    ) -> float:
        """Calculate severity of impact (0.0-1.0)."""
        base_severity = 0.5

        # Increase severity for vulnerable stakeholders
        if stakeholder.is_vulnerable():
            base_severity += 0.2

        # Increase severity for actions affecting basic rights
        action_lower = action.lower()
        if any(w in action_lower for w in ["deny", "harm", "exploit", "manipulate"]):
            base_severity += 0.2

        # Increase severity based on scope
        if context.get("scope", "").lower() in ["system_wide", "all", "global"]:
            base_severity += 0.15

        # Cap at 1.0
        return min(base_severity, 1.0)

    def _assess_vulnerability(self, context: Dict[str, Any]) -> float:
        """Assess vulnerability of user based on context."""
        vulnerability = 0.4  # Base

        # Check for vulnerable indicators
        vulnerable_keywords = [
            "minor", "child", "elderly", "disabled", "vulnerable",
            "disadvantaged", "marginalized", "protected"
        ]

        if any(k in str(context).lower() for k in vulnerable_keywords):
            vulnerability = 0.8

        return min(vulnerability, 1.0)

    def _mentions_vulnerable_group(self, context: Dict[str, Any]) -> bool:
        """Check if context mentions vulnerable populations."""
        vulnerable_keywords = [
            "minor", "child", "children", "elderly", "disabled",
            "vulnerable", "disadvantaged", "marginalized", "protected",
            "at-risk", "underrepresented"
        ]

        context_str = str(context).lower()
        return any(k in context_str for k in vulnerable_keywords)

    def _parse_type(self, type_str: str) -> StakeholderType:
        """Parse stakeholder type string."""
        type_lower = type_str.lower()
        if "user" in type_lower:
            return StakeholderType.USER
        elif "agent" in type_lower:
            return StakeholderType.AGENT
        elif "org" in type_lower:
            return StakeholderType.ORGANIZATION
        elif "society" in type_lower:
            return StakeholderType.SOCIETY
        elif "environment" in type_lower:
            return StakeholderType.ENVIRONMENT
        return StakeholderType.UNKNOWN
