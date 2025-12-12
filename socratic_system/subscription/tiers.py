"""Subscription tier definitions and limits."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TierLimits:
    """Defines limits and features for a subscription tier."""

    name: str
    monthly_cost: float
    max_projects: Optional[int]  # None = unlimited
    max_team_members: Optional[int]  # None = unlimited, 1 = solo only
    max_questions_per_month: Optional[int]  # None = unlimited
    multi_llm_access: bool
    advanced_analytics: bool
    code_generation: bool
    maturity_tracking: bool


# Tier definitions
TIER_LIMITS = {
    "free": TierLimits(
        name="Free",
        monthly_cost=0.0,
        max_projects=1,
        max_team_members=1,  # Solo only
        max_questions_per_month=100,
        multi_llm_access=False,
        advanced_analytics=False,
        code_generation=False,
        maturity_tracking=False,
    ),
    "pro": TierLimits(
        name="Pro",
        monthly_cost=29.0,
        max_projects=10,
        max_team_members=5,
        max_questions_per_month=1000,
        multi_llm_access=True,
        advanced_analytics=True,
        code_generation=True,
        maturity_tracking=True,
    ),
    "enterprise": TierLimits(
        name="Enterprise",
        monthly_cost=99.0,
        max_projects=None,  # Unlimited
        max_team_members=None,  # Unlimited
        max_questions_per_month=None,  # Unlimited
        multi_llm_access=True,
        advanced_analytics=True,
        code_generation=True,
        maturity_tracking=True,
    ),
}


def get_tier_limits(tier: str) -> TierLimits:
    """Get limits for a specific tier."""
    return TIER_LIMITS.get(tier.lower(), TIER_LIMITS["free"])


# Feature-to-tier mapping (minimum tier required)
FEATURE_TIER_REQUIREMENTS = {
    "team_collaboration": "pro",
    "multi_llm": "pro",
    "advanced_analytics": "pro",
    "code_generation": "pro",
    "maturity_tracking": "pro",
}

# Command-to-feature mapping (which feature does each command require)
COMMAND_FEATURE_MAP = {
    # Team collaboration commands (Pro+)
    "collab add": "team_collaboration",
    "collab remove": "team_collaboration",
    "collab list": "team_collaboration",
    "collab role": "team_collaboration",
    "skills set": "team_collaboration",
    "skills list": "team_collaboration",
    # Multi-LLM commands (Pro+)
    "llm": "multi_llm",
    "model": "multi_llm",
    # Advanced analytics commands (Pro+)
    "analytics analyze": "advanced_analytics",
    "analytics recommend": "advanced_analytics",
    "analytics trends": "advanced_analytics",
    "analytics summary": "advanced_analytics",
    "analytics breakdown": "advanced_analytics",
    "analytics status": "advanced_analytics",
    # Code generation commands (Pro+)
    "code generate": "code_generation",
    "code docs": "code_generation",
    "finalize generate": "code_generation",
    "finalize docs": "code_generation",
    # Maturity tracking commands (Pro+)
    "maturity": "maturity_tracking",
    "maturity summary": "maturity_tracking",
    "maturity history": "maturity_tracking",
    "maturity status": "maturity_tracking",
}
