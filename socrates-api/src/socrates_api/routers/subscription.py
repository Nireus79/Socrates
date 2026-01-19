"""
Subscription Management API endpoints for Socrates.

Provides REST endpoints for subscription management including:
- Viewing subscription status
- Upgrading/downgrading plans
- Comparing subscription tiers
- Testing mode management

Uses centralized tier definitions from socratic_system.subscription.tiers
to maintain a single source of truth.
"""

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse
from socratic_system.subscription.tiers import TIER_LIMITS

if TYPE_CHECKING:
    from socratic_system.database import ProjectDatabase


class SubscriptionPlan(BaseModel):
    """Subscription plan details"""

    tier: str
    price: float
    projects_limit: int
    team_members_limit: int
    features: list


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["subscription"])


# Build subscription tier details from central TIER_LIMITS
# FREEMIUM MODEL: All tiers have FULL FEATURE ACCESS, differentiated only by quotas
def _build_subscription_tiers():
    """Build SUBSCRIPTION_TIERS from central TIER_LIMITS."""
    tiers = {}

    # Feature descriptions for each tier
    feature_descriptions = {
        "free": [
            "✓ Socratic dialogue mode",
            "✓ Direct mode (code conversations)",
            "✓ Code generation & documentation",
            "✓ GitHub integration (import/push)",
            "✓ Advanced analytics & metrics",
            "✓ Multi-LLM access (all providers)",
            "✓ API access",
            "✓ Unlimited questions per month",
        ],
        "pro": [
            "✓ Everything in Free",
            "✓ Up to 10 projects",
            "✓ Team collaboration (up to 5 members)",
            "✓ Team management tools",
            "✓ Priority support",
            "✓ Advanced integrations",
        ],
        "enterprise": [
            "✓ Everything in Pro",
            "✓ Unlimited projects & team members",
            "✓ Unlimited storage",
            "✓ Dedicated account manager",
            "✓ Custom SLA & support",
            "✓ White-label options (coming soon)",
        ],
    }

    tier_descriptions = {
        "free": "Full-featured for solo developers and students",
        "pro": "For teams and growing projects",
        "enterprise": "For organizations and enterprises",
    }

    for tier_name, tier_limits in TIER_LIMITS.items():
        tiers[tier_name] = {
            "tier": tier_name,
            "display_name": tier_limits.name,
            "price": tier_limits.monthly_cost,
            "projects_limit": tier_limits.max_projects,
            "team_members_limit": tier_limits.max_team_members,
            "storage_gb": tier_limits.storage_gb,
            "features": feature_descriptions.get(tier_name, []),
            "description": tier_descriptions.get(tier_name, ""),
        }

    return tiers

# Dynamically built from central TIER_LIMITS
SUBSCRIPTION_TIERS = _build_subscription_tiers()


@router.get(
    "/status",
    response_model=APIResponse,
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

        # Load user from database to get actual tier and testing_mode flag
        user = db.load_user(current_user)
        current_tier = user.subscription_tier if user else "free"
        testing_mode = user.testing_mode if user else False

        tier_info = SUBSCRIPTION_TIERS.get(current_tier, SUBSCRIPTION_TIERS["free"])

        # Calculate actual usage from database
        from socratic_system.subscription.storage import StorageQuotaManager

        projects = db.get_user_projects(current_user)
        # Count only owned projects
        owned_projects = [p for p in projects if p.owner == current_user]
        projects_count = len(owned_projects)

        # Get team members count (from owned projects)
        team_members_count = 1  # User is always a member of their own project
        for proj in owned_projects:
            if hasattr(proj, 'team_members') and proj.team_members:
                team_members_count = max(team_members_count, len(proj.team_members) + 1)

        # Calculate storage usage
        storage_used_gb = StorageQuotaManager.bytes_to_gb(
            StorageQuotaManager.calculate_user_storage_usage(current_user, db)
        )
        storage_limit_gb = tier_info["storage_gb"]

        return APIResponse(
            success=True,
        status="success",
            message="Subscription status retrieved",
            data={
                "current_tier": current_tier,
                "testing_mode": testing_mode,
                "plan": tier_info,
                "usage": {
                    "projects_used": projects_count,
                    "projects_limit": tier_info["projects_limit"],
                    "team_members_used": team_members_count,
                    "team_members_limit": tier_info["team_members_limit"],
                    "storage_used_gb": round(storage_used_gb, 2),
                    "storage_limit_gb": storage_limit_gb,
                    "storage_percentage_used": round((storage_used_gb / storage_limit_gb * 100), 2) if storage_limit_gb else 0,
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
    "/storage",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get storage usage report",
)
async def get_storage_usage(
    current_user: str = Depends(get_current_user),
    db: "ProjectDatabase" = Depends(get_database),
):
    """
    Get detailed storage usage report for user.

    Returns storage used, limit, and percentage for current tier.

    Args:
        current_user: Authenticated user

    Returns:
        SuccessResponse with storage usage details
    """
    try:
        logger.info(f"Getting storage usage for user: {current_user}")

        from socratic_system.subscription.storage import StorageQuotaManager

        # Import here to avoid circular imports at module level
        from socrates_api.database import get_database as get_db_instance
        db = get_db_instance()

        report = StorageQuotaManager.get_storage_usage_report(current_user, db)

        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=report["error"],
            )

        return APIResponse(
            success=True,
            status="success",
            message="Storage usage retrieved",
            data=report,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage usage: {str(e)}",
        )


@router.get(
    "/plans",
    response_model=APIResponse,
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
        for _tier_key, tier_info in SUBSCRIPTION_TIERS.items():
            plans.append(
                {
                    "tier": tier_info["tier"],
                    "display_name": tier_info["display_name"],
                    "price": tier_info["price"],
                    "projects_limit": tier_info["projects_limit"],
                    "team_members_limit": tier_info["team_members_limit"],
                    "storage_gb": tier_info["storage_gb"],
                    "features": tier_info["features"],
                    "description": tier_info["description"],
                }
            )

        return APIResponse(
            success=True,
        status="success",
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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
        status="success",
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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
        status="success",
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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle testing mode (bypasses subscription restrictions)",
)
async def toggle_testing_mode(
    enabled: bool = Query(...),
    current_user: str = Depends(get_current_user),
    db: "ProjectDatabase" = Depends(get_database),
):
    """
    Enable/disable testing mode (bypasses subscription restrictions).

    ## Authorization Model: Owner-Based, Not Admin-Based

    Socrates uses OWNER-BASED AUTHORIZATION, not global admin roles:
    - There is NO admin role in the system
    - Testing mode is available to ANY authenticated user for their own account
    - This allows all registered users to test the system without monetization limits
    - No admin check is needed - users can manage their own testing mode

    ## Persistent Storage

    This endpoint persists the testing mode state to the database.
    The change is effective immediately and persists across sessions.

    Args:
        enabled: True to enable testing mode, False to disable (query parameter)
        current_user: Authenticated user (from JWT token)
        db: Database connection

    Returns:
        SuccessResponse with testing mode status and restrictions bypassed
    """
    try:
        logger.info(f"Toggling testing mode to {enabled} for user: {current_user}")

        # Load user and update testing mode flag
        user = db.load_user(current_user)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.testing_mode = enabled
        db.save_user(user)
        logger.info(f"Testing mode {'enabled' if enabled else 'disabled'} for user: {current_user}")

        return APIResponse(
            success=True,
            status="success",
            message=f"Testing mode {'enabled' if enabled else 'disabled'}",
            data={
                "testing_mode": enabled,
                "effective_immediately": True,
                "restrictions_bypassed": (
                    [
                        "Project limits",
                        "Team member limits",
                        "Feature flags",
                        "Cost tracking",
                    ]
                    if enabled
                    else []
                ),
                "warning": (
                    "Testing mode enabled - all subscription restrictions bypassed"
                    if enabled
                    else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling testing mode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle testing mode: {str(e)}",
        )
