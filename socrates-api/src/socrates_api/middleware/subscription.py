"""
Subscription-based Feature Gating Middleware.

Enforces feature access based on user subscription tier.
Provides decorators for protecting endpoints by tier requirements.

Centralized tier definitions now imported from socratic_system.subscription.tiers
to maintain a single source of truth across CLI, API, and storage systems.
"""

import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status
from socratic_system.subscription.tiers import TIER_LIMITS

logger = logging.getLogger(__name__)

# Build API-compatible feature matrix from central TIER_LIMITS
# This maintains backward compatibility while using the centralized definitions
def _build_tier_features():
    """Build TIER_FEATURES from central TIER_LIMITS for backward compatibility."""
    tier_features = {}
    for tier_name, tier_limits in TIER_LIMITS.items():
        tier_features[tier_name] = {
            "projects": tier_limits.max_projects,
            "team_members": tier_limits.max_team_members,
            "storage_gb": tier_limits.storage_gb,
            "questions_per_month": tier_limits.max_questions_per_month,
            "features": {
                # All features available to all tiers - limited only by quotas
                "basic_chat": True,
                "socratic_mode": True,
                "direct_mode": True,
                "code_generation": tier_limits.code_generation,
                "collaboration": tier_limits.max_team_members != 1,  # True for pro+, False for solo
                "github_import": True,
                "github_export": True,
                "advanced_analytics": tier_limits.advanced_analytics,
                "multi_llm": tier_limits.multi_llm_access,
                "api_access": True,
                "project_creation": True,
                "knowledge_management": True,
                "nlu_features": True,
            },
        }
    return tier_features

# Dynamically built from central TIER_LIMITS
# FREEMIUM MODEL: All tiers have FULL FEATURE ACCESS, limited only by quotas (projects, team members, storage).
# Free tier users can use all features (code generation, analytics, GitHub, etc.) on their single project.
# Pro tier users can collaborate with teams, have more projects, and more storage.
TIER_FEATURES = _build_tier_features()


class SubscriptionChecker:
    """Checks subscription tier and feature access."""

    @staticmethod
    def get_tier_limits(tier: str) -> dict:
        """Get limits for a subscription tier."""
        return TIER_FEATURES.get(tier, TIER_FEATURES["free"])

    @staticmethod
    def has_feature(tier: str, feature: str) -> bool:
        """Check if a tier has access to a feature."""
        tier_data = TIER_FEATURES.get(tier, TIER_FEATURES["free"])
        return tier_data.get("features", {}).get(feature, False)

    @staticmethod
    def can_create_projects(tier: str, current_count: int) -> tuple:
        """
        Check if user can create projects.

        Returns:
            (can_create: bool, reason: str or None)
        """
        limits = TIER_FEATURES.get(tier, TIER_FEATURES["free"])
        max_projects = limits.get("projects")

        if max_projects is None:
            return True, None

        if current_count >= max_projects:
            return False, f"Project limit ({max_projects}) reached for {tier} tier"

        return True, None

    @staticmethod
    def can_add_team_member(tier: str, current_count: int) -> tuple:
        """
        Check if user can add team members.

        Returns:
            (can_add: bool, reason: str or None)
        """
        limits = TIER_FEATURES.get(tier, TIER_FEATURES["free"])
        max_members = limits.get("team_members")

        if max_members is None:
            return True, None

        if current_count >= max_members:
            return False, f"Team member limit ({max_members}) reached for {tier} tier"

        return True, None

    @staticmethod
    def can_ask_questions(tier: str, questions_asked_this_month: int) -> tuple:
        """
        Check if user can ask more questions.

        Returns:
            (can_ask: bool, reason: str or None)
        """
        limits = TIER_FEATURES.get(tier, TIER_FEATURES["free"])
        max_questions = limits.get("questions_per_month")

        if max_questions is None:
            return True, None

        if questions_asked_this_month >= max_questions:
            return (
                False,
                f"Question limit ({max_questions}/month) reached for {tier} tier",
            )

        remaining = max_questions - questions_asked_this_month
        return True, f"{remaining} questions remaining this month"


def require_subscription_feature(feature: str) -> Callable:
    """
    Decorator to require a specific feature for an endpoint.

    Args:
        feature: Feature name from TIER_FEATURES

    Returns:
        Decorator function

    Usage:
        @router.post("/collaborate")
        @require_subscription_feature("collaboration")
        async def add_collaborator(current_user: str = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )

            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database not available",
                )

            # Load user and check tier
            user = db.load_user(current_user)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # If testing mode is enabled, bypass subscription checks
            if getattr(user, "testing_mode", False):
                logger.debug(f"Testing mode enabled for {current_user}, bypassing subscription check for feature: {feature}")
                return await func(*args, **kwargs)

            # Check feature access
            has_access = SubscriptionChecker.has_feature(user.subscription_tier, feature)
            if not has_access:
                SubscriptionChecker.get_tier_limits(user.subscription_tier)
                logger.warning(
                    f"User {current_user} ({user.subscription_tier}) attempted to access "
                    f"restricted feature: {feature}"
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "feature_not_available",
                        "message": f"Feature '{feature}' is not available in {user.subscription_tier} tier",
                        "required_tier": _get_required_tier_for_feature(feature),
                        "current_tier": user.subscription_tier,
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_subscription_tier(required_tier: str) -> Callable:
    """
    Decorator to require a minimum subscription tier.

    Args:
        required_tier: Minimum tier (free, pro, enterprise)

    Returns:
        Decorator function

    Usage:
        @router.get("/analytics")
        @require_subscription_tier("pro")
        async def get_analytics(current_user: str = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )

            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database not available",
                )

            user = db.load_user(current_user)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # If testing mode is enabled, bypass subscription tier checks
            if getattr(user, "testing_mode", False):
                logger.debug(f"Testing mode enabled for {current_user}, bypassing subscription tier check for required tier: {required_tier}")
                return await func(*args, **kwargs)

            # Check tier
            tier_order = ["free", "pro", "enterprise"]
            current_tier_level = tier_order.index(
                user.subscription_tier if user.subscription_tier in tier_order else "free"
            )
            required_tier_level = tier_order.index(
                required_tier if required_tier in tier_order else "free"
            )

            if current_tier_level < required_tier_level:
                logger.warning(
                    f"User {current_user} ({user.subscription_tier}) attempted to access "
                    f"endpoint requiring {required_tier} tier"
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "insufficient_tier",
                        "message": f"This endpoint requires {required_tier} subscription tier",
                        "current_tier": user.subscription_tier,
                        "required_tier": required_tier,
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def _get_required_tier_for_feature(feature: str) -> str:
    """Get the minimum tier required for a feature."""
    tier_order = ["free", "pro", "enterprise"]

    for tier in tier_order:
        if TIER_FEATURES[tier]["features"].get(feature, False):
            return tier

    return "enterprise"  # Default to highest tier if not found
