"""
Ethical Reasoning Module

Provides multi-framework ethical reasoning for decisions, stakeholder analysis,
and moral deliberation.

Public API:
- EthicalDeliberation: Main reasoning engine
- EthicalFramework: Base class for ethical frameworks
- StakeholderAnalyzer: Identifies and analyzes affected stakeholders
- FrameworkAnalysis: Result of single framework analysis
- DeliberationResult: Final reasoning conclusion
"""

from socratic_system.reasoning.contradiction_detector import (
    Contradiction,
    ContradictionAnalysis,
    ContradictionDetector,
    ContradictionType,
)
from socratic_system.reasoning.ethical_deliberation import (
    DeliberationResult,
    EthicalDeliberation,
)
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
from socratic_system.reasoning.moral_precedent_engine import (
    MoralPrecedent,
    MoralPrecedentEngine,
    PrecedentAnalysis,
    PrecedentMatch,
    PrecedentQuery,
    PrecedentType,
)
from socratic_system.reasoning.stakeholder_analyzer import (
    Impact,
    Stakeholder,
    StakeholderAnalysis,
    StakeholderAnalyzer,
    StakeholderType,
)
from socratic_system.reasoning.threat_detector import (
    Threat,
    ThreatAnalysis,
    ThreatDetector,
    ThreatLevel,
    ThreatProfile,
    ThreatType,
)

__all__ = [
    # Frameworks
    "EthicalFramework",
    "EthicalFrameworkType",
    "EthicalConclusion",
    "FrameworkAnalysis",
    "KantianAnalyzer",
    "UtilitarianAnalyzer",
    "VirtueAnalyzer",
    "RightsAnalyzer",
    # Stakeholder Analysis
    "StakeholderAnalyzer",
    "Stakeholder",
    "StakeholderAnalysis",
    "StakeholderType",
    "Impact",
    # Deliberation
    "EthicalDeliberation",
    "DeliberationResult",
    # Contradiction Detection
    "ContradictionDetector",
    "Contradiction",
    "ContradictionAnalysis",
    "ContradictionType",
    # Moral Precedent Engine
    "MoralPrecedentEngine",
    "MoralPrecedent",
    "PrecedentType",
    "PrecedentQuery",
    "PrecedentMatch",
    "PrecedentAnalysis",
    # Threat Detection
    "ThreatDetector",
    "Threat",
    "ThreatAnalysis",
    "ThreatLevel",
    "ThreatType",
    "ThreatProfile",
]
