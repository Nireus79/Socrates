"""
User model for Socratic RAG System
"""

import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class User:
    """Represents a user of the Socratic RAG System"""

    username: str
    passcode_hash: str
    created_at: datetime.datetime
    projects: Optional[List[str]] = None  # User can start with no projects
    is_archived: bool = False
    archived_at: Optional[datetime.datetime] = None

    # NEW: Subscription fields
    subscription_tier: str = "free"  # "free", "pro", "enterprise"
    subscription_status: str = "active"  # "active", "expired", "cancelled"
    subscription_start: Optional[datetime.datetime] = None
    subscription_end: Optional[datetime.datetime] = None

    # NEW: Usage tracking (resets monthly)
    questions_used_this_month: int = 0
    usage_reset_date: Optional[datetime.datetime] = None

    def __post_init__(self):
        """Initialize projects list and subscription fields for new users."""
        if self.projects is None:
            self.projects = []

        # Initialize subscription fields for new users
        if self.subscription_start is None:
            self.subscription_start = datetime.datetime.now()

        # Set initial usage reset date (1st of next month)
        if self.usage_reset_date is None:
            now = datetime.datetime.now()
            if now.month == 12:
                self.usage_reset_date = datetime.datetime(now.year + 1, 1, 1)
            else:
                self.usage_reset_date = datetime.datetime(now.year, now.month + 1, 1)

    def reset_monthly_usage_if_needed(self):
        """Reset monthly usage if we've passed the reset date."""
        if self.usage_reset_date and datetime.datetime.now() >= self.usage_reset_date:
            self.questions_used_this_month = 0

            # Set next reset date
            now = datetime.datetime.now()
            if now.month == 12:
                self.usage_reset_date = datetime.datetime(now.year + 1, 1, 1)
            else:
                self.usage_reset_date = datetime.datetime(now.year, now.month + 1, 1)

    def increment_question_usage(self):
        """Increment question usage counter."""
        self.reset_monthly_usage_if_needed()
        self.questions_used_this_month += 1

    def get_active_projects_count(self) -> int:
        """Get count of active (non-archived) projects."""
        if self.projects is None:
            return 0
        return len([p for p in self.projects if p])
