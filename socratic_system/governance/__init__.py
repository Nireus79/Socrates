"""
Governance Module

Provides decision-making and oversight capabilities for the Socratic system.

Core Components:
- EthicalGovernor: Main governance engine integrating ethical reasoning
- EthicalDecision: Complete decision with reasoning trail

Socratic-Morality Integration:
- MoralityGovernanceIntegration: Unified governance API wrapper
- GovernanceAwareOrchestrator: Agent orchestration with governance checks
"""

from socratic_system.governance.ethical_governor import (
    EthicalDecision,
    EthicalGovernor,
)
from socratic_system.governance.morality_integration import (
    MoralityGovernanceIntegration,
    get_morality_governance,
    initialize_morality_governance,
)
from socratic_system.governance.orchestrator_hooks import (
    GovernanceAwareOrchestrator,
    evaluate_action_governance,
    wrap_orchestrator_with_governance,
)

__all__ = [
    # Core governance
    "EthicalGovernor",
    "EthicalDecision",
    # Morality integration
    "MoralityGovernanceIntegration",
    "initialize_morality_governance",
    "get_morality_governance",
    # Orchestrator integration
    "GovernanceAwareOrchestrator",
    "wrap_orchestrator_with_governance",
    "evaluate_action_governance",
]
