"""GitHub Sponsors tier mapping for Socrates monetization."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SponsorshipTier:
    """Defines sponsorship amount and corresponding Socrates tier."""

    amount: int  # Sponsorship amount in dollars per month
    socrates_tier: str  # pro, enterprise
    duration_days: int  # How long the tier lasts
    description: str


# Map GitHub sponsorship amounts to Socrates tiers
# Free tier users can fork the public repo - no sponsorship needed
SPONSORSHIP_TIER_MAP = {
    5: SponsorshipTier(
        amount=5,
        socrates_tier="pro",  # $5/month → Pro tier
        duration_days=365,  # 1 year
        description="Pro tier - 10 projects, 5 team members, 100GB storage",
    ),
    15: SponsorshipTier(
        amount=15,
        socrates_tier="enterprise",  # $15/month → Enterprise tier
        duration_days=365,
        description="Enterprise tier - Unlimited projects, team members, storage",
    ),
}


def get_tier_from_sponsorship_amount(amount: int) -> Optional[str]:
    """
    Get Socrates tier based on GitHub sponsorship amount.

    Args:
        amount: Monthly sponsorship amount in dollars

    Returns:
        Socrates tier: "pro" or "enterprise", or None if not eligible
    """
    # Exact match for standard tiers
    if amount in SPONSORSHIP_TIER_MAP:
        return SPONSORSHIP_TIER_MAP[amount].socrates_tier

    # Custom amounts: $5-$14 → pro, $15+ → enterprise
    if 5 <= amount < 15:
        return "pro"
    elif amount >= 15:
        return "enterprise"

    # Amounts less than $5 don't grant tier upgrade
    return None


def get_sponsorship_details(amount: int) -> Optional[SponsorshipTier]:
    """
    Get detailed sponsorship tier information.

    Args:
        amount: Monthly sponsorship amount in dollars

    Returns:
        SponsorshipTier object or None if not found
    """
    return SPONSORSHIP_TIER_MAP.get(amount)
