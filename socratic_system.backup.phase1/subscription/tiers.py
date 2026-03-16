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
    storage_gb: Optional[int]  # None = unlimited
    multi_llm_access: bool
    advanced_analytics: bool
    code_generation: bool
    maturity_tracking: bool


# Tier definitions - All tiers have full feature access, limited only by quotas
TIER_LIMITS = {
    "free": TierLimits(
        name="Free",
        monthly_cost=0.0,
        max_projects=1,
        max_team_members=1,  # Solo only
        max_questions_per_month=None,  # Unlimited
        storage_gb=5,
        multi_llm_access=True,  # All features available in free tier
        advanced_analytics=True,
        code_generation=True,
        maturity_tracking=True,
    ),
    "pro": TierLimits(
        name="Pro",
        monthly_cost=4.99,  # Reduced from $29
        max_projects=10,
        max_team_members=5,
        max_questions_per_month=None,  # Unlimited
        storage_gb=100,
        multi_llm_access=True,
        advanced_analytics=True,
        code_generation=True,
        maturity_tracking=True,
    ),
    "enterprise": TierLimits(
        name="Enterprise",
        monthly_cost=9.99,  # Reduced from $99
        max_projects=None,  # Unlimited
        max_team_members=None,  # Unlimited
        max_questions_per_month=None,  # Unlimited
        storage_gb=None,  # Unlimited
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
# FREEMIUM MODEL: All features available in all tiers. Only team collaboration is restricted to Pro+
# due to team member quota limits in free tier (solo only). Features like code generation,
# analytics, etc. are available to free tier users on their single project.
FEATURE_TIER_REQUIREMENTS = {
    "team_collaboration": "pro",  # Only feature restricted: requires team member capability
}

# Command-to-feature mapping (which feature does each command require)
# FREEMIUM MODEL: Most commands available in all tiers. Only team collaboration commands restricted.
COMMAND_FEATURE_MAP = {
    # Team collaboration commands (Pro+ only - requires team member capability)
    "collab add": "team_collaboration",
    "collab remove": "team_collaboration",
    "collab list": "team_collaboration",
    "collab role": "team_collaboration",
    "skills set": "team_collaboration",
    "skills list": "team_collaboration",
    # All other commands available to free tier:
    # - llm, model (multi-LLM)
    # - analytics * (advanced analytics)
    # - code generate, code docs (code generation)
    # - maturity * (maturity tracking)
    # - chat, knowledge, finalize, etc.
}
