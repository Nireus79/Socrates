"""GitHub Sponsors webhook handler and signature verification."""

import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from socratic_system.sponsorships.models import Sponsorship
from socratic_system.sponsorships.tiers import get_tier_from_sponsorship_amount

logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature.

    GitHub sends X-Hub-Signature-256 header with format: sha256=<hash>
    We verify using our GITHUB_WEBHOOK_SECRET.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid, False otherwise
    """
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()

    if not secret:
        logger.warning("GITHUB_WEBHOOK_SECRET not configured - cannot verify signatures")
        return False

    # Calculate expected signature
    expected_hash = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).hexdigest()
    expected_signature = f"sha256={expected_hash}"

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)


def process_sponsorship_event(event_data: Dict) -> Optional[Sponsorship]:
    """
    Process GitHub Sponsors webhook event.

    Args:
        event_data: Parsed JSON from GitHub webhook

    Returns:
        Sponsorship object if successfully processed, None otherwise
    """
    action = event_data.get("action")
    sponsorship_data = event_data.get("sponsorship", {})

    if not sponsorship_data:
        logger.warning("No sponsorship data in webhook event")
        return None

    # Extract sponsor information
    sponsor = sponsorship_data.get("sponsor", {})
    github_username = sponsor.get("login", "")
    github_user_id = sponsor.get("id")

    # Extract sponsorship tier information
    tier_data = sponsorship_data.get("tier", {})
    monthly_price_cents = tier_data.get("monthly_price_in_cents", 0)
    monthly_price_dollars = monthly_price_cents // 100

    # Determine Socrates tier
    socrates_tier = get_tier_from_sponsorship_amount(monthly_price_dollars)

    if not socrates_tier:
        logger.info(
            f"Sponsorship amount ${monthly_price_dollars} does not qualify for tier upgrade"
        )
        return None

    logger.info(
        f"Processing GitHub sponsorship: {github_username} → ${monthly_price_dollars}/month → {socrates_tier} tier"
    )

    # Create sponsorship record
    sponsorship = Sponsorship(
        username=github_username,  # Will be matched to Socrates user later
        github_username=github_username,
        github_sponsor_id=github_user_id,
        sponsorship_amount=monthly_price_dollars,
        socrates_tier_granted=socrates_tier,
        sponsorship_status="active" if action != "cancelled" else "cancelled",
        sponsored_at=datetime.now(),
        tier_expires_at=datetime.now() + timedelta(days=365),
        webhook_event_id=event_data.get("zen", ""),
    )

    return sponsorship


def handle_sponsorship_webhook(event_data: Dict) -> Dict:
    """
    Main webhook handler for GitHub Sponsors events.

    Args:
        event_data: Parsed JSON from GitHub webhook

    Returns:
        Response dict with status and message
    """
    action = event_data.get("action")
    logger.info(f"Received GitHub sponsorship webhook: action={action}")

    try:
        sponsorship = process_sponsorship_event(event_data)

        if not sponsorship:
            return {
                "status": "skipped",
                "message": "Sponsorship amount does not qualify for tier upgrade",
            }

        # Note: Database operations will be handled by the API endpoint
        # This function just processes the event data

        return {
            "status": "success",
            "message": f"Sponsorship processed: {sponsorship.github_username} → {sponsorship.socrates_tier_granted}",
            "sponsorship": {
                "username": sponsorship.github_username,
                "tier": sponsorship.socrates_tier_granted,
                "amount": sponsorship.sponsorship_amount,
            },
        }

    except Exception as e:
        logger.error(f"Error processing sponsorship webhook: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to process webhook: {str(e)}",
        }
