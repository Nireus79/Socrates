"""GitHub Sponsors integration for Socrates monetization system.

This module handles:
- GitHub Sponsors webhook events
- Mapping sponsorship amounts to Socrates tiers
- Automatic tier upgrades for sponsors
- Sponsorship history tracking
"""

from socratic_system.sponsorships.models import Sponsorship
from socratic_system.sponsorships.tiers import (
    get_sponsorship_details,
    get_tier_from_sponsorship_amount,
)
from socratic_system.sponsorships.webhook import (
    handle_sponsorship_webhook,
    verify_github_signature,
)

__all__ = [
    "Sponsorship",
    "get_tier_from_sponsorship_amount",
    "get_sponsorship_details",
    "verify_github_signature",
    "handle_sponsorship_webhook",
]
