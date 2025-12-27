"""
Subscription Management API endpoints for Socrates.

Provides REST endpoints for subscription management including:
- Viewing subscription status
- Upgrading/downgrading plans
- Comparing subscription tiers
- Testing mode management
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import SuccessResponse


class SubscriptionPlan(BaseModel):
    """Subscription plan details"""
    tier: str
    price: float
    projects_limit: int
    team_members_limit: int
    features: list


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["subscription"])


# Define subscription tiers
SUBSCRIPTION_TIERS = {
    "free": {
        "tier": "free",
        "display_name": "Free",
        "price": 0.0,
        "projects_limit": 1,
        "team_members_limit": 1,
        "storage_gb": 1,
        "features": [
            "Basic Socratic questions",
            "Single project",
            "Solo work",
            "Limited conversation history",
        ],
        "description": "Great for getting started with Socrates",
    },
    "pro": {
        "tier": "pro",
        "display_name": "Pro",
        "price": 9.99,
        "projects_limit": 5,
        "team_members_limit": 5,
        "storage_gb": 50,
        "features": [
            "Everything in Free",
            "Up to 5 projects",
            "Team collaboration",
            "Advanced question generation",
            "Code review and analysis",
            "Project documentation",
        ],
        "description": "For individual developers and small teams",
    },
    "team": {
        "tier": "team",
        "display_name": "Team",
        "price": 29.99,
        "projects_limit": 50,
        "team_members_limit": 20,
        "storage_gb": 500,
        "features": [
            "Everything in Pro",
            "Up to 50 projects",
            "Up to 20 team members",
            "Advanced analytics",
            "Priority support",
            "Custom integrations",
        ],
        "description": "For teams and organizations",
    },
    "enterprise": {
        "tier": "enterprise",
        "display_name": "Enterprise",
        "price": "custom",
        "projects_limit": float("inf"),
        "team_members_limit": float("inf"),
        "storage_gb": float("inf"),
        "features": [
            "Everything in Team",
            "Unlimited projects",
            "Unlimited team members",
            "Dedicated support",
            "SLA guarantees",
            "Custom deployment",
        ],
        "description": "For large organizations - custom pricing",
    },
}


@router.get(
    "/status",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user subscription status",
)
async def get_subscription_status(
    current_user: str = Depends(get_current_user),
):
    """
    Get current subscription status for user.

    Returns subscription tier, limits, features, and usage.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with subscription details
    """
    try:
        logger.info(f"Getting subscription status for user: {current_user}")

        db = get_database()

        # Get user's current tier (default to free)
        # In production, would load from user database
        current_tier = "free"  # Default tier

        tier_info = SUBSCRIPTION_TIERS.get(current_tier, SUBSCRIPTION_TIERS["free"])

        # Calculate usage (mock data for now)
        # In production, would calculate from actual database
        projects_count = 0
        team_members_count = 1

        return SuccessResponse(
            success=True,
            message="Subscription status retrieved",
            data={
                "current_tier": current_tier,
                "plan": tier_info,
                "usage": {
                    "projects_used": projects_count,
                    "projects_limit": tier_info["projects_limit"],
                    "team_members_used": team_members_count,
                    "team_members_limit": tier_info["team_members_limit"],
                    "storage_used_gb": 0.1,
                    "storage_limit_gb": tier_info["storage_gb"],
                },
                "billing": {
                    "next_billing_date": "2025-01-26",
                    "auto_renew": True,
                    "payment_method": "card_ending_4242",
                },
                "trial_active": False,
            },
        )

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription status: {str(e)}",
        )


@router.get(
    "/plans",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List all subscription plans",
)
async def list_subscription_plans(
    current_user: str = Depends(get_current_user),
):
    """
    List all available subscription plans for comparison.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with all available plans
    """
    try:
        logger.info(f"Listing subscription plans for user: {current_user}")

        plans = []
        for tier_key, tier_info in SUBSCRIPTION_TIERS.items():
            plans.append({
                "tier": tier_info["tier"],
                "display_name": tier_info["display_name"],
                "price": tier_info["price"],
                "projects_limit": tier_info["projects_limit"],
                "team_members_limit": tier_info["team_members_limit"],
                "storage_gb": tier_info["storage_gb"],
                "features": tier_info["features"],
                "description": tier_info["description"],
            })

        return SuccessResponse(
            success=True,
            message="Plans retrieved",
            data={"plans": plans},
        )

    except Exception as e:
        logger.error(f"Error listing plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plans: {str(e)}",
        )


@router.post(
    "/upgrade",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Upgrade subscription plan",
)
async def upgrade_subscription(
    new_tier: str,
    current_user: str = Depends(get_current_user),
):
    """
    Upgrade to a higher subscription tier.

    Args:
        new_tier: Target subscription tier (pro, team, enterprise)
        current_user: Authenticated user

    Returns:
        SuccessResponse with upgrade confirmation
    """
    try:
        logger.info(f"Upgrading subscription to {new_tier} for user: {current_user}")

        # Validate tier
        if new_tier not in SUBSCRIPTION_TIERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier. Must be one of: {', '.join(SUBSCRIPTION_TIERS.keys())}",
            )

        tier_info = SUBSCRIPTION_TIERS[new_tier]

        return SuccessResponse(
            success=True,
            message=f"Successfully upgraded to {tier_info['display_name']}",
            data={
                "previous_tier": "free",
                "new_tier": new_tier,
                "plan": tier_info,
                "billing": {
                    "amount": tier_info["price"],
                    "currency": "USD",
                    "billing_cycle": "monthly",
                    "next_billing_date": "2025-01-26",
                },
                "effective_immediately": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade subscription: {str(e)}",
        )


@router.post(
    "/downgrade",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Downgrade subscription plan",
)
async def downgrade_subscription(
    new_tier: str,
    current_user: str = Depends(get_current_user),
):
    """
    Downgrade to a lower subscription tier.

    Args:
        new_tier: Target subscription tier (free, pro, team)
        current_user: Authenticated user

    Returns:
        SuccessResponse with downgrade confirmation
    """
    try:
        logger.info(f"Downgrading subscription to {new_tier} for user: {current_user}")

        # Validate tier
        if new_tier not in SUBSCRIPTION_TIERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier. Must be one of: {', '.join(SUBSCRIPTION_TIERS.keys())}",
            )

        tier_info = SUBSCRIPTION_TIERS[new_tier]

        return SuccessResponse(
            success=True,
            message=f"Successfully downgraded to {tier_info['display_name']}",
            data={
                "previous_tier": "pro",
                "new_tier": new_tier,
                "plan": tier_info,
                "billing": {
                    "amount": tier_info["price"],
                    "currency": "USD",
                    "billing_cycle": "monthly",
                    "refund_available": 0.0,
                    "effective_date": "2025-02-26",
                },
                "warning": "Some features may become unavailable with lower tier",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downgrading subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to downgrade subscription: {str(e)}",
        )


@router.put(
    "/testing-mode",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle testing mode (bypasses subscription restrictions)",
)
async def toggle_testing_mode(
    enabled: bool = Query(...),
    current_user: str = Depends(get_current_user),
):
    """
    Enable/disable testing mode (bypasses subscription restrictions).

    ## Authorization Model: Owner-Based, Not Admin-Based

    Socrates uses OWNER-BASED AUTHORIZATION, not global admin roles:
    - There is NO admin role in the system
    - Testing mode is available to ANY authenticated user for their own account
    - This allows all registered users to test the system without monetization limits
    - No admin check is needed - users can manage their own testing mode

    ## NOTE: Primary Implementation

    For persistent storage, use `/auth/me/testing-mode` (PUT) instead.
    This endpoint provides informational response about testing mode capabilities.

    Args:
        enabled: True to enable testing mode, False to disable (query parameter)
        current_user: Authenticated user (from JWT token)

    Returns:
        SuccessResponse with testing mode status and restrictions bypassed
    """
    try:
        logger.info(f"Toggling testing mode to {enabled} for user: {current_user}")

        return SuccessResponse(
            success=True,
            message=f"Testing mode {'enabled' if enabled else 'disabled'}",
            data={
                "testing_mode": enabled,
                "effective_immediately": True,
                "restrictions_bypassed": [
                    "Project limits",
                    "Team member limits",
                    "Feature flags",
                    "Cost tracking",
                ] if enabled else [],
                "warning": "Testing mode enabled - all subscription restrictions bypassed" if enabled else None,
            },
        )

    except Exception as e:
        logger.error(f"Error toggling testing mode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle testing mode: {str(e)}",
        )
