"""
User model for Socrates AI
"""

import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class User:
    """
    Represents a user of the Socrates AI.

    ## Authorization Model

    The Socrates system uses OWNER-BASED AUTHORIZATION, not global admin roles:
    - There is NO `is_admin` field - no global admin users exist
    - Each user can OWN projects they create
    - Within projects, users can collaborate as: "owner", "editor", or "viewer"
    - Within projects, team members have roles: "lead", "creator", "specialist", "analyst", "coordinator"
    - Project owners control all project management (settings, collaborators, deletion)

    This decentralized model allows collaborative development without central admins.
    """

    username: str
    email: str
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

    # Testing mode - bypasses all monetization restrictions
    # Any authenticated user can enable this for their own account to bypass monetization
    # during development/testing. This is NOT an admin-only feature.
    testing_mode: bool = False

    # Claude authentication method: "api_key" or "subscription"
    claude_auth_method: str = "api_key"  # How to authenticate with Claude API

    # GitHub Integration (NEW)
    github_token: Optional[str] = None  # Encrypted GitHub Personal Access Token
    github_username: Optional[str] = None  # GitHub username (cached from API)
    github_token_expires: Optional[datetime.datetime] = None  # Token expiration date
    has_github_auth: bool = False  # Whether user has authenticated with GitHub

    # Export & Git Preferences (NEW)
    default_export_format: str = "zip"  # Default export format: zip, tar, tar.gz, tar.bz2
    auto_initialize_git: bool = True  # Automatically initialize git repos
    default_repo_visibility: str = "private"  # Default repo visibility: private, public

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
