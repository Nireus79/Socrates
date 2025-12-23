"""
Subscription-based Feature Gating Middleware.

Enforces feature access based on user subscription tier.
Provides decorators for protecting endpoints by tier requirements.
"""

import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Subscription tier feature matrix
TIER_FEATURES = {
    "free": {
        "projects": 1,
        "team_members": 1,
        "questions_per_month": 50,
        "features": {
            "basic_chat": True,
            "socratic_mode": True,
            "direct_mode": False,
            "code_generation": False,
            "collaboration": False,
            "github_import": False,
            "advanced_analytics": False,
            "multi_llm": False,
            "api_access": False,
        },
    },
    "pro": {
        "projects": 10,
        "team_members": 5,
        "questions_per_month": 500,
        "features": {
            "basic_chat": True,
            "socratic_mode": True,
            "direct_mode": True,
            "code_generation": True,
            "collaboration": True,
            "github_import": True,
            "advanced_analytics": True,
            "multi_llm": False,
            "api_access": False,
        },
    },
    "enterprise": {
        "projects": None,  # Unlimited
        "team_members": None,
        "questions_per_month": None,
        "features": {
            "basic_chat": True,
            "socratic_mode": True,
            "direct_mode": True,
            "code_generation": True,
            "collaboration": True,
            "github_import": True,
            "advanced_analytics": True,
            "multi_llm": True,
            "api_access": True,
        },
    },
}


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

            # Check feature access
            has_access = SubscriptionChecker.has_feature(user.subscription_tier, feature)
            if not has_access:
                tier_limits = SubscriptionChecker.get_tier_limits(user.subscription_tier)
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
