"""Subscription system for Socrates - Tier management and feature gating."""

try:
    from socratic_system.performance import SubscriptionChecker
except ImportError:
    SubscriptionChecker = None

from .tiers import TIER_LIMITS, get_tier_limits

__all__ = [
    "TIER_LIMITS",
    "get_tier_limits",
]

# Add SubscriptionChecker if successfully imported
if SubscriptionChecker is not None:
    __all__.append("SubscriptionChecker")
