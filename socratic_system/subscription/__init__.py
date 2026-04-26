"""Subscription system for Socrates - Tier management and feature gating."""

from socratic_system.performance import SubscriptionChecker
from socratic_system.performance import TIER_LIMITS, get_tier_limits

__all__ = [
    "SubscriptionChecker",
    "TIER_LIMITS",
    "get_tier_limits",
]
