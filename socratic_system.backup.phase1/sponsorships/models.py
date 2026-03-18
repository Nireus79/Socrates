"""Data models for GitHub Sponsors tracking."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Sponsorship:
    """Represents a GitHub sponsorship and associated Socrates tier."""

    id: Optional[int] = None
    username: str = ""  # Socrates username
    github_username: str = ""  # GitHub username
    github_sponsor_id: Optional[int] = None  # GitHub user ID
    sponsorship_amount: int = 0  # Amount in dollars per month
    socrates_tier_granted: str = ""  # "pro" or "enterprise"
    sponsorship_status: str = "active"  # active, pending, cancelled
    sponsored_at: Optional[datetime] = None
    tier_expires_at: Optional[datetime] = None
    last_payment_at: Optional[datetime] = None
    payment_id: str = ""  # GitHub payment/transaction ID
    webhook_event_id: str = ""  # GitHub webhook delivery ID
    notes: str = ""

    def is_active(self) -> bool:
        """Check if sponsorship is currently active."""
        if self.sponsorship_status != "active":
            return False
        if self.tier_expires_at and datetime.now() > self.tier_expires_at:
            return False
        return True

    def days_remaining(self) -> Optional[int]:
        """Get days until sponsorship expires."""
        if not self.tier_expires_at:
            return None
        days = (self.tier_expires_at - datetime.now()).days
        return max(0, days)
