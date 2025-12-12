"""
Comprehensive test suite for the Monetization System.

Tests verify:
1. Subscription tier configuration and limits
2. Command-level feature gating
3. Quota enforcement at operation level
4. User experience with upgrade messages
5. Monthly usage reset functionality
"""

import datetime

import pytest

from socratic_system.models.user import User
from socratic_system.subscription.checker import SubscriptionChecker
from socratic_system.subscription.tiers import (
    COMMAND_FEATURE_MAP,
    FEATURE_TIER_REQUIREMENTS,
    get_tier_limits,
)


class TestTierConfiguration:
    """Test subscription tier definitions and limits."""

    def test_free_tier_limits(self):
        """Verify Free tier has correct limits."""
        free = get_tier_limits("free")
        assert free.name == "Free"
        assert free.monthly_cost == 0.0
        assert free.max_projects == 1
        assert free.max_team_members == 1
        assert free.max_questions_per_month == 100
        assert free.multi_llm_access is False
        assert free.advanced_analytics is False
        assert free.code_generation is False
        assert free.maturity_tracking is False

    def test_pro_tier_limits(self):
        """Verify Pro tier has correct limits."""
        pro = get_tier_limits("pro")
        assert pro.name == "Pro"
        assert pro.monthly_cost == 29.0
        assert pro.max_projects == 10
        assert pro.max_team_members == 5
        assert pro.max_questions_per_month == 1000
        assert pro.multi_llm_access is True
        assert pro.advanced_analytics is True
        assert pro.code_generation is True
        assert pro.maturity_tracking is True

    def test_enterprise_tier_limits(self):
        """Verify Enterprise tier has correct limits."""
        enterprise = get_tier_limits("enterprise")
        assert enterprise.name == "Enterprise"
        assert enterprise.monthly_cost == 99.0
        assert enterprise.max_projects is None  # Unlimited
        assert enterprise.max_team_members is None  # Unlimited
        assert enterprise.max_questions_per_month is None  # Unlimited
        assert enterprise.multi_llm_access is True
        assert enterprise.advanced_analytics is True
        assert enterprise.code_generation is True
        assert enterprise.maturity_tracking is True

    def test_tier_limits_case_insensitive(self):
        """Verify tier lookup is case-insensitive."""
        assert get_tier_limits("FREE").name == "Free"
        assert get_tier_limits("PRO").name == "Pro"
        assert get_tier_limits("ENTERPRISE").name == "Enterprise"

    def test_invalid_tier_defaults_to_free(self):
        """Verify invalid tier defaults to Free tier."""
        invalid = get_tier_limits("invalid_tier")
        assert invalid.name == "Free"


class TestFeatureMapping:
    """Test feature-to-tier and command-to-feature mappings."""

    def test_team_collaboration_requires_pro(self):
        """Verify team collaboration requires Pro tier."""
        assert FEATURE_TIER_REQUIREMENTS["team_collaboration"] == "pro"

    def test_multi_llm_requires_pro(self):
        """Verify multi-LLM access requires Pro tier."""
        assert FEATURE_TIER_REQUIREMENTS["multi_llm"] == "pro"

    def test_advanced_analytics_requires_pro(self):
        """Verify advanced analytics requires Pro tier."""
        assert FEATURE_TIER_REQUIREMENTS["advanced_analytics"] == "pro"

    def test_code_generation_requires_pro(self):
        """Verify code generation requires Pro tier."""
        assert FEATURE_TIER_REQUIREMENTS["code_generation"] == "pro"

    def test_maturity_tracking_requires_pro(self):
        """Verify maturity tracking requires Pro tier."""
        assert FEATURE_TIER_REQUIREMENTS["maturity_tracking"] == "pro"

    def test_collab_commands_gated(self):
        """Verify collaboration commands are gated."""
        assert COMMAND_FEATURE_MAP.get("collab add") == "team_collaboration"
        assert COMMAND_FEATURE_MAP.get("collab remove") == "team_collaboration"
        assert COMMAND_FEATURE_MAP.get("collab list") == "team_collaboration"
        assert COMMAND_FEATURE_MAP.get("collab role") == "team_collaboration"

    def test_analytics_commands_gated(self):
        """Verify analytics commands are gated."""
        assert COMMAND_FEATURE_MAP.get("analytics analyze") == "advanced_analytics"
        assert COMMAND_FEATURE_MAP.get("analytics recommend") == "advanced_analytics"
        assert COMMAND_FEATURE_MAP.get("analytics trends") == "advanced_analytics"

    def test_code_generation_commands_gated(self):
        """Verify code generation commands are gated."""
        assert COMMAND_FEATURE_MAP.get("code generate") == "code_generation"
        assert COMMAND_FEATURE_MAP.get("code docs") == "code_generation"

    def test_ungated_commands_not_in_map(self):
        """Verify core commands are not gated."""
        # Core commands should not appear in COMMAND_FEATURE_MAP
        assert "help" not in COMMAND_FEATURE_MAP
        assert "chat" not in COMMAND_FEATURE_MAP
        assert "exit" not in COMMAND_FEATURE_MAP


class TestUserSubscriptionFields:
    """Test User model subscription fields and methods."""

    def test_user_defaults_to_free_tier(self):
        """Verify new users default to Free tier."""
        user = User(
            username="test_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
        )
        assert user.subscription_tier == "free"
        assert user.subscription_status == "active"

    def test_user_tracks_questions_used(self):
        """Verify user tracks questions used this month."""
        user = User(
            username="test_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
        )
        assert user.questions_used_this_month == 0
        user.increment_question_usage()
        assert user.questions_used_this_month == 1

    def test_monthly_usage_reset(self):
        """Verify monthly usage resets on reset date."""
        user = User(
            username="test_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
        )
        # Set current date to past reset date
        now = datetime.datetime.now()
        if now.month == 12:
            past_reset = datetime.datetime(now.year, 1, 1)
        else:
            past_reset = datetime.datetime(now.year, now.month + 1, 1)

        user.usage_reset_date = past_reset
        user.questions_used_this_month = 50

        # Call reset - should reset counter
        user.reset_monthly_usage_if_needed()
        assert user.questions_used_this_month == 0

    def test_subscription_start_initialized(self):
        """Verify subscription_start is initialized."""
        user = User(
            username="test_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
        )
        assert user.subscription_start is not None
        assert isinstance(user.subscription_start, datetime.datetime)

    def test_usage_reset_date_initialized(self):
        """Verify usage_reset_date is set to 1st of next month."""
        user = User(
            username="test_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
        )
        assert user.usage_reset_date is not None
        # Should be 1st of next month
        now = datetime.datetime.now()
        if now.month == 12:
            expected_month = 1
            expected_year = now.year + 1
        else:
            expected_month = now.month + 1
            expected_year = now.year
        assert user.usage_reset_date.month == expected_month
        assert user.usage_reset_date.year == expected_year
        assert user.usage_reset_date.day == 1


class TestSubscriptionChecker:
    """Test subscription checking and enforcement logic."""

    def test_free_user_blocked_from_collab_add(self):
        """Verify Free tier user cannot use collab add command."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "collab add")
        assert has_access is False
        assert error_msg is not None
        assert "Pro" in error_msg or "pro" in error_msg

    def test_pro_user_allowed_collab_add(self):
        """Verify Pro tier user can use collab add command."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "collab add")
        assert has_access is True
        assert error_msg is None

    def test_enterprise_user_allowed_collab_add(self):
        """Verify Enterprise tier user can use collab add command."""
        user = User(
            username="enterprise_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="enterprise",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "collab add")
        assert has_access is True
        assert error_msg is None

    def test_free_user_blocked_from_analytics(self):
        """Verify Free tier user cannot use analytics commands."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "analytics analyze")
        assert has_access is False
        assert error_msg is not None

    def test_free_user_blocked_from_code_generate(self):
        """Verify Free tier user cannot use code generation."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "code generate")
        assert has_access is False
        assert error_msg is not None

    def test_free_user_blocked_from_llm(self):
        """Verify Free tier user cannot access multi-LLM."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "llm")
        assert has_access is False
        assert error_msg is not None

    def test_ungated_command_always_allowed(self):
        """Verify ungated commands are always allowed."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        # Help is not gated
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "help")
        assert has_access is True
        assert error_msg is None


class TestProjectLimitEnforcement:
    """Test project limit quota enforcement."""

    def test_free_user_project_limit(self):
        """Verify Free tier limited to 1 project."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        # User has 1 active project already
        can_create, error_msg = SubscriptionChecker.check_project_limit(
            user, current_project_count=1
        )
        assert can_create is False
        assert error_msg is not None
        assert "project" in error_msg.lower()

    def test_free_user_can_create_first_project(self):
        """Verify Free tier can create their first project."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        can_create, error_msg = SubscriptionChecker.check_project_limit(
            user, current_project_count=0
        )
        assert can_create is True
        assert error_msg is None

    def test_pro_user_project_limit(self):
        """Verify Pro tier limited to 10 projects."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
        )
        # User has 10 projects already
        can_create, error_msg = SubscriptionChecker.check_project_limit(
            user, current_project_count=10
        )
        assert can_create is False
        assert error_msg is not None

    def test_pro_user_can_create_under_limit(self):
        """Verify Pro user can create projects under limit."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
        )
        can_create, error_msg = SubscriptionChecker.check_project_limit(
            user, current_project_count=5
        )
        assert can_create is True
        assert error_msg is None

    def test_enterprise_user_unlimited_projects(self):
        """Verify Enterprise tier has unlimited projects."""
        user = User(
            username="enterprise_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="enterprise",
        )
        # Even with 1000 projects
        can_create, error_msg = SubscriptionChecker.check_project_limit(
            user, current_project_count=1000
        )
        assert can_create is True
        assert error_msg is None


class TestTeamMemberLimitEnforcement:
    """Test team member limit quota enforcement."""

    def test_free_user_no_team_collaboration(self):
        """Verify Free tier cannot add team members (solo only)."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        can_add, error_msg = SubscriptionChecker.check_team_member_limit(user, current_team_size=0)
        assert can_add is False
        assert error_msg is not None
        assert "Free" in error_msg or "solo" in error_msg.lower()

    def test_pro_user_team_member_limit(self):
        """Verify Pro tier limited to 5 team members."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
        )
        # User has 5 team members already
        can_add, error_msg = SubscriptionChecker.check_team_member_limit(user, current_team_size=5)
        assert can_add is False
        assert error_msg is not None

    def test_pro_user_can_add_under_limit(self):
        """Verify Pro user can add team members under limit."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
        )
        can_add, error_msg = SubscriptionChecker.check_team_member_limit(user, current_team_size=2)
        assert can_add is True
        assert error_msg is None

    def test_enterprise_user_unlimited_team(self):
        """Verify Enterprise tier has unlimited team members."""
        user = User(
            username="enterprise_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="enterprise",
        )
        can_add, error_msg = SubscriptionChecker.check_team_member_limit(
            user, current_team_size=100
        )
        assert can_add is True
        assert error_msg is None


class TestQuestionLimitEnforcement:
    """Test question limit quota enforcement."""

    def test_free_user_question_limit(self):
        """Verify Free tier limited to 100 questions/month."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            questions_used_this_month=100,
        )
        can_ask, error_msg = SubscriptionChecker.check_question_limit(user)
        assert can_ask is False
        assert error_msg is not None
        assert "question" in error_msg.lower()

    def test_free_user_under_question_limit(self):
        """Verify Free tier user can ask questions under limit."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            questions_used_this_month=50,
        )
        can_ask, error_msg = SubscriptionChecker.check_question_limit(user)
        assert can_ask is True
        assert error_msg is None

    def test_pro_user_question_limit(self):
        """Verify Pro tier limited to 1000 questions/month."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
            questions_used_this_month=1000,
        )
        can_ask, error_msg = SubscriptionChecker.check_question_limit(user)
        assert can_ask is False
        assert error_msg is not None

    def test_enterprise_user_unlimited_questions(self):
        """Verify Enterprise tier has unlimited questions."""
        user = User(
            username="enterprise_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="enterprise",
            questions_used_this_month=10000,
        )
        can_ask, error_msg = SubscriptionChecker.check_question_limit(user)
        assert can_ask is True
        assert error_msg is None


class TestUpgradeMessages:
    """Test that upgrade messages are friendly and actionable."""

    def test_upgrade_message_includes_feature_name(self):
        """Verify upgrade message includes the feature name."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "collab add")
        assert has_access is False
        assert "Team Collaboration" in error_msg

    def test_upgrade_message_includes_current_tier(self):
        """Verify upgrade message shows current tier."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "llm")
        assert has_access is False
        assert "FREE" in error_msg.upper() or "free" in error_msg.lower()

    def test_upgrade_message_includes_upgrade_command(self):
        """Verify upgrade message suggests upgrade command."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        has_access, error_msg = SubscriptionChecker.check_command_access(user, "analytics analyze")
        assert has_access is False
        assert "/subscription upgrade" in error_msg or "upgrade" in error_msg.lower()

    def test_project_limit_message_shows_count(self):
        """Verify project limit message shows current/max count."""
        user = User(
            username="free_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )
        can_create, error_msg = SubscriptionChecker.check_project_limit(
            user, current_project_count=1
        )
        assert can_create is False
        assert "1" in error_msg  # Should show count

    def test_team_member_limit_message_actionable(self):
        """Verify team member limit message is actionable."""
        user = User(
            username="pro_user",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
        )
        can_add, error_msg = SubscriptionChecker.check_team_member_limit(user, current_team_size=5)
        assert can_add is False
        assert "enterprise" in error_msg.lower() or "upgrade" in error_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
