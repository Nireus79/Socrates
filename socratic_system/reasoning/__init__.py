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

from socratic_system.reasoning.ethical_framework import (
    EthicalFramework,
    EthicalFrameworkType,
    EthicalConclusion,
    FrameworkAnalysis,
    KantianAnalyzer,
    UtilitarianAnalyzer,
    VirtueAnalyzer,
    RightsAnalyzer,
)

from socratic_system.reasoning.stakeholder_analyzer import (
    StakeholderAnalyzer,
    Stakeholder,
    StakeholderAnalysis,
    StakeholderType,
    Impact,
)

from socratic_system.reasoning.ethical_deliberation import (
    EthicalDeliberation,
    DeliberationResult,
)

from socratic_system.reasoning.contradiction_detector import (
    ContradictionDetector,
    Contradiction,
    ContradictionAnalysis,
    ContradictionType,
)

from socratic_system.reasoning.moral_precedent_engine import (
    MoralPrecedentEngine,
    MoralPrecedent,
    PrecedentType,
    PrecedentQuery,
    PrecedentMatch,
    PrecedentAnalysis,
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
]
