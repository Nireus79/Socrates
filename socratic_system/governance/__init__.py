"""
Governance Module

Provides decision-making and oversight capabilities for the Socratic system.

Public API:
- EthicalGovernor: Main governance engine integrating ethical reasoning
- EthicalDecision: Complete decision with reasoning trail
"""

from socratic_system.governance.ethical_governor import (
    EthicalDecision,
    EthicalGovernor,
)

__all__ = [
    "EthicalGovernor",
    "EthicalDecision",
]
