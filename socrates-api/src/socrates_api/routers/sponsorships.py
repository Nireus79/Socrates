"""GitHub Sponsors webhook and sponsorship management endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse
from socratic_system.sponsorships.tiers import get_tier_from_sponsorship_amount
from socratic_system.sponsorships.webhook import (
    handle_sponsorship_webhook,
    verify_github_signature,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sponsorships", tags=["sponsorships"])


@router.post(
    "/webhooks/github-sponsors",
    status_code=status.HTTP_200_OK,
    summary="GitHub Sponsors webhook handler",
)
async def github_sponsors_webhook(
    request: Request,
    db=Depends(get_database),
):
    """
    Handle GitHub Sponsors webhook events.

    GitHub sends webhook events when:
    - User starts sponsoring you
    - Sponsorship tier changes
    - Sponsorship is cancelled

    Webhook signature verification using GITHUB_WEBHOOK_SECRET.

    Args:
        request: FastAPI Request with webhook payload
        db: Database connection

    Returns:
        Success response with tier upgrade details
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")

        # Verify webhook signature
        if not verify_github_signature(body, signature):
            logger.warning("Invalid GitHub webhook signature received")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        # Parse JSON payload
        event_data = await request.json()
        logger.info(f"Valid GitHub Sponsors webhook received: {event_data.get('action')}")

        # Process the webhook event
        result = handle_sponsorship_webhook(event_data)

        # If sponsorship qualifies for tier upgrade
        if result["status"] == "success":
            sponsorship_info = result.get("sponsorship", {})
            github_username = sponsorship_info.get("username")
            granted_tier = sponsorship_info.get("tier")
            amount = sponsorship_info.get("amount")

            # Load user by GitHub username (may need to match with Socrates username)
            user = db.load_user(github_username)

            if user:
                # Update subscription tier
                previous_tier = user.subscription_tier
                user.subscription_tier = granted_tier
                user.subscription_status = "active"
                user.subscription_start = datetime.now()
                user.subscription_end = datetime.now() + timedelta(days=365)

                # Save updated user
                db.save_user(user)

                logger.info(
                    f"User {github_username} upgraded from {previous_tier} to {granted_tier} via sponsorship (${amount}/month)"
                )

                # Store sponsorship record for tracking
                try:
                    db.create_sponsorship(
                        {
                            "username": github_username,
                            "github_username": github_username,
                            "sponsorship_amount": amount,
                            "socrates_tier_granted": granted_tier,
                            "sponsorship_status": "active",
                            "sponsored_at": datetime.now(),
                            "tier_expires_at": datetime.now() + timedelta(days=365),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not store sponsorship record: {e}")

                return APIResponse(
                    success=True,
                    status="success",
                    message=f"Sponsorship processed: {github_username} upgraded to {granted_tier}",
                    data={
                        "github_username": github_username,
                        "previous_tier": previous_tier,
                        "new_tier": granted_tier,
                        "sponsorship_amount": f"${amount}/month",
                        "tier_expires": (datetime.now() + timedelta(days=365)).isoformat(),
                    },
                )
            else:
                logger.info(
                    f"Sponsorship received for {github_username} but no Socrates account found"
                )
                return APIResponse(
                    success=True,
                    status="pending",
                    message=f"Sponsorship recorded. User {github_username} needs to create Socrates account to activate tier.",
                    data={"github_username": github_username, "tier": granted_tier},
                )
        else:
            return APIResponse(
                success=True,
                status="skipped",
                message=result.get("message", "Sponsorship processed but no tier upgrade"),
                data=result,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GitHub Sponsors webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )


@router.get(
    "/verify",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify user's active sponsorship",
)
async def verify_sponsorship(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Check if user has an active GitHub sponsorship.

    Returns sponsorship details if user is an active sponsor.

    Args:
        current_user: Authenticated user
        db: Database connection

    Returns:
        Sponsorship details if active, error if not
    """
    try:
        # Load user
        user = db.load_user(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check for active sponsorship
        sponsorship = db.get_active_sponsorship(current_user)

        if not sponsorship:
            return APIResponse(
                success=False,
                status="not_sponsored",
                message="No active sponsorship found",
                data={
                    "username": current_user,
                    "status": "not_sponsored",
                    "tier_granted": user.subscription_tier,
                },
            )

        return APIResponse(
            success=True,
            status="success",
            message="Active sponsorship verified",
            data={
                "username": current_user,
                "github_username": sponsorship.get("github_username"),
                "sponsorship_amount": sponsorship.get("sponsorship_amount"),
                "tier_granted": sponsorship.get("socrates_tier_granted"),
                "sponsored_since": sponsorship.get("sponsored_at"),
                "expires_at": sponsorship.get("tier_expires_at"),
                "days_remaining": (
                    (
                        datetime.fromisoformat(sponsorship.get("tier_expires_at"))
                        - datetime.now()
                    ).days
                    if sponsorship.get("tier_expires_at")
                    else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying sponsorship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify sponsorship: {str(e)}",
        )


@router.get(
    "/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's sponsorship history",
)
async def get_sponsorship_history(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get user's complete sponsorship history.

    Args:
        current_user: Authenticated user
        db: Database connection

    Returns:
        List of all sponsorship records for user
    """
    try:
        sponsorships = db.get_sponsorship_history(current_user)

        return APIResponse(
            success=True,
            status="success",
            message="Sponsorship history retrieved",
            data={
                "username": current_user,
                "sponsorships": sponsorships,
                "total_sponsored": len(sponsorships),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving sponsorship history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sponsorship history: {str(e)}",
        )
