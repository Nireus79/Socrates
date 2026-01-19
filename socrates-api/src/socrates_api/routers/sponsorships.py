"""GitHub Sponsors webhook and sponsorship management endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse
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
                sponsorship_id = None
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
                    # Get sponsorship ID for payment tracking
                    active_sponsorship = db.get_active_sponsorship(github_username)
                    sponsorship_id = active_sponsorship.get("id") if active_sponsorship else None
                except Exception as e:
                    logger.warning(f"Could not store sponsorship record: {e}")

                # Record payment details
                try:
                    if sponsorship_id:
                        payment_id = db.record_payment(
                            {
                                "sponsorship_id": sponsorship_id,
                                "username": github_username,
                                "amount": amount,
                                "currency": "USD",
                                "payment_status": "success",
                                "payment_date": datetime.now().isoformat(),
                                "payment_method_id": None,  # GitHub doesn't provide method details in webhook
                                "reference_id": event_data.get("zen", ""),
                                "notes": "GitHub Sponsors webhook payment for tier upgrade",
                            }
                        )
                        logger.info(f"Recorded payment {payment_id} for user {github_username}")
                except Exception as e:
                    logger.warning(f"Could not record payment details: {e}")

                # Record tier change if tier actually changed
                try:
                    if sponsorship_id and previous_tier != granted_tier:
                        db.record_tier_change(
                            {
                                "sponsorship_id": sponsorship_id,
                                "username": github_username,
                                "change_type": "upgrade" if granted_tier > previous_tier else "downgrade",
                                "old_tier": previous_tier,
                                "new_tier": granted_tier,
                                "old_amount": None,  # Previous sponsorship amount unknown
                                "new_amount": amount,
                                "change_reason": "GitHub Sponsors webhook",
                                "change_date": datetime.now().isoformat(),
                                "effective_date": datetime.now().isoformat(),
                                "notes": f"Tier changed via GitHub Sponsors from {previous_tier} to {granted_tier}",
                            }
                        )
                        logger.info(f"Recorded tier change for user {github_username}: {previous_tier} → {granted_tier}")
                except Exception as e:
                    logger.warning(f"Could not record tier change: {e}")

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

        # Get payment methods for this sponsorship
        sponsorship_id = sponsorship.get("id")
        payment_methods = db.get_payment_methods(sponsorship_id) if sponsorship_id else []

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
                "payment_methods_on_file": len(payment_methods),
                "payment_methods": payment_methods,
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


@router.get(
    "/payments",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's payment history",
)
async def get_payment_history(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    limit: int = 50,
):
    """
    Get user's complete payment history.

    Args:
        current_user: Authenticated user
        db: Database connection
        limit: Maximum number of payments to retrieve

    Returns:
        List of all payment records for user
    """
    try:
        payments = db.get_payment_history(current_user, limit=limit)

        total_successful = sum(
            1 for p in payments if p.get("payment_status") == "success"
        )
        total_failed = sum(1 for p in payments if p.get("payment_status") == "failed")
        total_amount = sum(
            float(p.get("amount", 0))
            for p in payments
            if p.get("payment_status") == "success"
        )

        return APIResponse(
            success=True,
            status="success",
            message="Payment history retrieved",
            data={
                "username": current_user,
                "payments": payments,
                "total_payments": len(payments),
                "successful_payments": total_successful,
                "failed_payments": total_failed,
                "total_amount": f"${total_amount:.2f}",
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving payment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment history: {str(e)}",
        )


@router.get(
    "/refunds",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's refund history",
)
async def get_refund_history(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    limit: int = 50,
):
    """
    Get user's complete refund history.

    Args:
        current_user: Authenticated user
        db: Database connection
        limit: Maximum number of refunds to retrieve

    Returns:
        List of all refund records for user
    """
    try:
        refunds = db.get_refund_history(current_user, limit=limit)

        total_refunded = sum(float(r.get("refund_amount", 0)) for r in refunds)
        by_reason = {}
        for refund in refunds:
            reason = refund.get("refund_reason", "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1

        return APIResponse(
            success=True,
            status="success",
            message="Refund history retrieved",
            data={
                "username": current_user,
                "refunds": refunds,
                "total_refunds": len(refunds),
                "total_refunded_amount": f"${total_refunded:.2f}",
                "refunds_by_reason": by_reason,
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving refund history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve refund history: {str(e)}",
        )


@router.get(
    "/tier-history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's tier change history",
)
async def get_tier_change_history(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
    limit: int = 50,
):
    """
    Get user's complete tier change history (upgrades, downgrades, renewals).

    Args:
        current_user: Authenticated user
        db: Database connection
        limit: Maximum number of tier changes to retrieve

    Returns:
        List of all tier change records for user
    """
    try:
        tier_changes = db.get_tier_change_history(current_user, limit=limit)

        changes_by_type = {}
        for change in tier_changes:
            change_type = change.get("change_type", "unknown")
            changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1

        return APIResponse(
            success=True,
            status="success",
            message="Tier change history retrieved",
            data={
                "username": current_user,
                "tier_changes": tier_changes,
                "total_changes": len(tier_changes),
                "changes_by_type": changes_by_type,
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving tier change history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tier change history: {str(e)}",
        )


@router.get(
    "/analytics",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's sponsorship analytics",
)
async def get_sponsorship_analytics(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get comprehensive sponsorship analytics for user.

    Includes payment stats, refund stats, tier change summary, and net revenue.

    Args:
        current_user: Authenticated user
        db: Database connection

    Returns:
        Comprehensive analytics data
    """
    try:
        analytics = db.get_sponsorship_analytics(current_user)

        return APIResponse(
            success=True,
            status="success",
            message="Sponsorship analytics retrieved",
            data=analytics,
        )

    except Exception as e:
        logger.error(f"Error retrieving sponsorship analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sponsorship analytics: {str(e)}",
        )


@router.get(
    "/payment-methods",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's payment methods",
)
async def get_payment_methods(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get user's stored payment methods.

    Args:
        current_user: Authenticated user
        db: Database connection

    Returns:
        List of payment methods on file
    """
    try:
        sponsorship = db.get_active_sponsorship(current_user)
        if not sponsorship:
            return APIResponse(
                success=False,
                status="not_sponsored",
                message="No active sponsorship found",
                data={
                    "username": current_user,
                    "payment_methods": [],
                },
            )

        sponsorship_id = sponsorship.get("id")
        payment_methods = db.get_payment_methods(sponsorship_id)

        return APIResponse(
            success=True,
            status="success",
            message="Payment methods retrieved",
            data={
                "username": current_user,
                "sponsorship_id": sponsorship_id,
                "payment_methods": payment_methods,
                "total_methods": len(payment_methods),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving payment methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment methods: {str(e)}",
        )


@router.get(
    "/info",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sponsorship information and tiers",
)
async def get_sponsorship_info():
    """
    Get information about sponsorship tiers and how it works.

    Public endpoint - no authentication required.
    Provides information to help users understand sponsorship options.

    Returns:
        Information about sponsorship tiers, benefits, and process
    """
    try:
        sponsorship_info = {
            "message": "Support Socrates development via GitHub Sponsors",
            "github_sponsors_url": "https://github.com/sponsors/Nireus79",
            "sponsorship_guide_url": "https://github.com/Nireus79/Socrates/blob/master/SPONSORSHIP.md",
            "how_it_works": [
                "1. Sponsor on GitHub Sponsors page (https://github.com/sponsors/Nireus79)",
                "2. Use the same username as your GitHub account (or link it in Settings)",
                "3. Your Socrates account is automatically upgraded within seconds",
                "4. Access premium features immediately",
                "5. View payment history and tier details in Settings → Subscription",
            ],
            "tiers": [
                {
                    "name": "Free",
                    "price": "$0/month",
                    "github_sponsors_amount": None,
                    "socrates_tier": "Free",
                    "features": {
                        "projects": 1,
                        "team_members": 1,
                        "storage_gb": 5,
                        "support": "Community",
                    },
                },
                {
                    "name": "Supporter",
                    "price": "$5/month",
                    "github_sponsors_amount": 5,
                    "socrates_tier": "Pro",
                    "features": {
                        "projects": 10,
                        "team_members": 5,
                        "storage_gb": 100,
                        "support": "Community",
                        "sponsor_badge": False,
                    },
                },
                {
                    "name": "Contributor",
                    "price": "$15/month",
                    "github_sponsors_amount": 15,
                    "socrates_tier": "Enterprise",
                    "features": {
                        "projects": "Unlimited",
                        "team_members": "Unlimited",
                        "storage_gb": "Unlimited",
                        "support": "Community",
                        "sponsor_badge": True,
                    },
                },
                {
                    "name": "Custom",
                    "price": "$25+/month",
                    "github_sponsors_amount": 25,
                    "socrates_tier": "Enterprise+",
                    "features": {
                        "projects": "Unlimited",
                        "team_members": "Unlimited",
                        "storage_gb": "Unlimited",
                        "support": "Priority email",
                        "sponsor_badge": True,
                    },
                },
            ],
            "benefits": [
                "Support open-source development",
                "Unlock premium features",
                "Access more projects and storage",
                "Add team members to collaborate",
                "Priority support (higher tiers)",
                "Sponsor badge on GitHub profile",
            ],
            "faq": [
                {
                    "question": "How long does sponsorship activation take?",
                    "answer": "Usually instant (within seconds). If not activated within 5 minutes, try logging out and back in.",
                },
                {
                    "question": "Can I change my sponsorship tier?",
                    "answer": "Yes! You can upgrade or downgrade anytime on GitHub Sponsors. Changes take effect immediately.",
                },
                {
                    "question": "What happens if I cancel my sponsorship?",
                    "answer": "Your tier will downgrade to Free at the next billing cycle. You'll have until then to export your data.",
                },
                {
                    "question": "Can I use a different GitHub account?",
                    "answer": "Yes! Link your GitHub account in Socrates Settings → GitHub Integration.",
                },
                {
                    "question": "Is my payment secure?",
                    "answer": "Yes. All payments are processed by GitHub directly. Socrates never sees payment information.",
                },
            ],
        }

        return APIResponse(
            success=True,
            status="success",
            message="Sponsorship information retrieved",
            data=sponsorship_info,
        )

    except Exception as e:
        logger.error(f"Error retrieving sponsorship info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sponsorship info: {str(e)}",
        )


@router.get(
    "/admin/dashboard",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get admin sponsorship dashboard (repo owner only)",
)
async def get_admin_dashboard(
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
):
    """
    Get comprehensive sponsorship dashboard for repository owner.

    Only accessible to the repository owner (Nireus79).
    Shows all sponsorships, payments, refunds, and tier change data.

    Args:
        current_user: Authenticated user (must be repo owner)
        db: Database connection

    Returns:
        Comprehensive sponsorship dashboard data
    """
    # Check if user is the repo owner
    if current_user != "Nireus79":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only repository owner can access admin dashboard",
        )

    try:
        # Get all sponsorship data from database
        sponsorships = db.get_all_sponsorships() if hasattr(db, 'get_all_sponsorships') else []

        if not sponsorships:
            return APIResponse(
                success=True,
                status="success",
                message="Admin dashboard - no sponsorships found",
                data={
                    "total_sponsors": 0,
                    "active_sponsors": 0,
                    "total_monthly_revenue": "$0.00",
                    "sponsorships_by_tier": {},
                    "recent_sponsorships": [],
                    "total_refunded": "$0.00",
                },
            )

        # Calculate dashboard metrics
        active_sponsors = [s for s in sponsorships if s.get("sponsorship_status") == "active"]
        cancelled_sponsors = [s for s in sponsorships if s.get("sponsorship_status") == "cancelled"]

        total_monthly_revenue = sum(
            float(s.get("sponsorship_amount", 0)) for s in active_sponsors
        )

        # Group by tier
        sponsorships_by_tier = {}
        for sponsorship in sponsorships:
            tier = sponsorship.get("socrates_tier_granted", "unknown")
            if tier not in sponsorships_by_tier:
                sponsorships_by_tier[tier] = {
                    "count": 0,
                    "total_revenue": 0.0,
                    "sponsors": []
                }
            sponsorships_by_tier[tier]["count"] += 1
            sponsorships_by_tier[tier]["total_revenue"] += float(
                sponsorship.get("sponsorship_amount", 0)
            )
            sponsorships_by_tier[tier]["sponsors"].append(
                sponsorship.get("github_username")
            )

        # Format tier data
        tier_summary = {}
        for tier, data in sponsorships_by_tier.items():
            tier_summary[tier] = {
                "count": data["count"],
                "total_revenue": f"${data['total_revenue']:.2f}",
                "sponsors": data["sponsors"],
            }

        # Get recent sponsorships (last 10)
        recent_sponsorships = sorted(
            sponsorships,
            key=lambda x: x.get("sponsored_at", ""),
            reverse=True
        )[:10]

        # Calculate total refunded (sum of all refunds across all users)
        total_refunded = 0.0
        for sponsorship in sponsorships:
            username = sponsorship.get("username")
            if username:
                refunds = db.get_refund_history(username, limit=1000)
                total_refunded += sum(
                    float(r.get("refund_amount", 0)) for r in refunds
                )

        return APIResponse(
            success=True,
            status="success",
            message="Admin dashboard data retrieved",
            data={
                "total_sponsors": len(sponsorships),
                "active_sponsors": len(active_sponsors),
                "cancelled_sponsors": len(cancelled_sponsors),
                "total_monthly_revenue": f"${total_monthly_revenue:.2f}",
                "sponsorships_by_tier": tier_summary,
                "recent_sponsorships": recent_sponsorships,
                "total_refunded": f"${total_refunded:.2f}",
                "net_revenue": f"${total_monthly_revenue - total_refunded:.2f}",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving admin dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin dashboard: {str(e)}",
        )
