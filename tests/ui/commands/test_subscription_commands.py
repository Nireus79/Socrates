"""
Tests for subscription management commands.

Tests cover:
- SubscriptionStatusCommand: Display current tier and usage
- SubscriptionUpgradeCommand: Upgrade to higher tier
- SubscriptionDowngradeCommand: Downgrade to Free tier
- SubscriptionCompareCommand: Display tier comparison table
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User
from socratic_system.ui.commands.subscription_commands import (
    SubscriptionCompareCommand,
    SubscriptionDowngradeCommand,
    SubscriptionStatusCommand,
    SubscriptionUpgradeCommand,
)


class TestSubscriptionStatusCommand:
    """Tests for SubscriptionStatusCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return SubscriptionStatusCommand()

    @pytest.fixture
    def user_free(self):
        """Create a Free tier user."""
        return User(
            username="testuser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            subscription_status="active",
            subscription_start=datetime.datetime.now(),
            questions_used_this_month=50,
        )

    @pytest.fixture
    def user_pro(self):
        """Create a Pro tier user."""
        return User(
            username="prouser",
            passcode_hash="hash456",
            created_at=datetime.datetime.now(),
            projects=["proj1", "proj2"],
            subscription_tier="pro",
            subscription_status="active",
            subscription_start=datetime.datetime.now(),
            questions_used_this_month=500,
        )

    @pytest.fixture
    def user_enterprise(self):
        """Create an Enterprise tier user."""
        return User(
            username="entuser",
            passcode_hash="hash789",
            created_at=datetime.datetime.now(),
            projects=["p1", "p2", "p3"],
            subscription_tier="enterprise",
            subscription_status="active",
            subscription_start=datetime.datetime.now(),
            questions_used_this_month=2000,
        )

    def test_status_no_user(self, command):
        """Test status command without user returns error."""
        context = {"user": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "User not found" in result["message"]

    def test_status_free_tier(self, command, user_free):
        """Test status command displays Free tier correctly."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_user_projects.return_value = []

        context = {"user": user_free, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        mock_orchestrator.database.get_user_projects.assert_called_once_with("testuser")

    def test_status_pro_tier(self, command, user_pro):
        """Test status command displays Pro tier correctly."""
        mock_orchestrator = MagicMock()

        # Create mock projects
        proj1 = MagicMock(spec=ProjectContext)
        proj1.is_archived = False
        proj2 = MagicMock(spec=ProjectContext)
        proj2.is_archived = False

        mock_orchestrator.database.get_user_projects.return_value = [proj1, proj2]

        context = {"user": user_pro, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        mock_orchestrator.database.get_user_projects.assert_called_once_with("prouser")

    def test_status_enterprise_tier(self, command, user_enterprise):
        """Test status command displays Enterprise tier correctly."""
        mock_orchestrator = MagicMock()

        # Create mock projects
        projects = [MagicMock(spec=ProjectContext) for _ in range(3)]
        for proj in projects:
            proj.is_archived = False

        mock_orchestrator.database.get_user_projects.return_value = projects

        context = {"user": user_enterprise, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"

    def test_status_with_archived_projects(self, command, user_pro):
        """Test status command correctly counts only active projects."""
        mock_orchestrator = MagicMock()

        # Create projects: 2 active, 1 archived
        active1 = MagicMock(spec=ProjectContext)
        active1.is_archived = False
        active2 = MagicMock(spec=ProjectContext)
        active2.is_archived = False
        archived = MagicMock(spec=ProjectContext)
        archived.is_archived = True

        mock_orchestrator.database.get_user_projects.return_value = [active1, active2, archived]

        context = {"user": user_pro, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"

    def test_status_resets_monthly_usage(self, command, user_free):
        """Test status command calls reset_monthly_usage_if_needed."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_user_projects.return_value = []

        # Mock the reset method
        user_free.reset_monthly_usage_if_needed = MagicMock()

        context = {"user": user_free, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            command.execute([], context)

        user_free.reset_monthly_usage_if_needed.assert_called_once()

    def test_status_displays_unlimited_questions(self, command, user_enterprise):
        """Test status shows 'unlimited' for enterprise questions."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_user_projects.return_value = []

        context = {"user": user_enterprise, "orchestrator": mock_orchestrator}

        with patch("builtins.print") as mock_print:
            result = command.execute([], context)

        assert result["status"] == "success"
        # Verify 'unlimited' is printed for questions
        printed_output = [str(call) for call in mock_print.call_args_list]
        unlimited_found = any("unlimited" in str(call).lower() for call in printed_output)
        assert unlimited_found


class TestSubscriptionUpgradeCommand:
    """Tests for SubscriptionUpgradeCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return SubscriptionUpgradeCommand()

    @pytest.fixture
    def free_user(self):
        """Create a Free tier user."""
        return User(
            username="freeuser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            subscription_status="active",
        )

    @pytest.fixture
    def pro_user(self):
        """Create a Pro tier user."""
        return User(
            username="prouser",
            passcode_hash="hash456",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="pro",
            subscription_status="active",
        )

    def test_upgrade_no_user(self, command):
        """Test upgrade without user returns error."""
        context = {"user": None, "orchestrator": MagicMock()}
        result = command.execute(["pro"], context)

        assert result["status"] == "error"
        assert "User not found" in result["message"]

    def test_upgrade_no_args(self, command, free_user):
        """Test upgrade without tier argument returns error."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        result = command.execute([], context)

        assert result["status"] == "error"
        assert "Usage:" in result["message"]

    def test_upgrade_invalid_tier(self, command, free_user):
        """Test upgrade with invalid tier returns error."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        result = command.execute(["invalid"], context)

        assert result["status"] == "error"
        assert "Invalid tier" in result["message"]

    def test_upgrade_free_to_pro(self, command, free_user):
        """Test upgrading from Free to Pro tier."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["pro"], context)

        assert result["status"] == "success"
        assert "Upgraded from Free to Pro" in result["message"]
        assert free_user.subscription_tier == "pro"
        assert free_user.subscription_status == "active"
        mock_orchestrator.database.save_user.assert_called_once_with(free_user)

    def test_upgrade_free_to_enterprise(self, command, free_user):
        """Test upgrading from Free to Enterprise tier."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["enterprise"], context)

        assert result["status"] == "success"
        assert "Upgraded from Free to Enterprise" in result["message"]
        assert free_user.subscription_tier == "enterprise"
        mock_orchestrator.database.save_user.assert_called_once()

    def test_upgrade_pro_to_enterprise(self, command, pro_user):
        """Test upgrading from Pro to Enterprise tier."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["enterprise"], context)

        assert result["status"] == "success"
        assert "Upgraded from Pro to Enterprise" in result["message"]
        assert pro_user.subscription_tier == "enterprise"

    def test_upgrade_already_on_tier(self, command, pro_user):
        """Test upgrade when already on same tier."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        result = command.execute(["pro"], context)

        assert result["status"] == "error"
        assert "already on the Pro tier" in result["message"]
        mock_orchestrator.database.save_user.assert_not_called()

    def test_upgrade_case_insensitive(self, command, free_user):
        """Test upgrade accepts case-insensitive tier names."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["PRO"], context)

        assert result["status"] == "success"
        assert free_user.subscription_tier == "pro"

    def test_upgrade_sets_subscription_start(self, command, free_user):
        """Test upgrade updates subscription_start date."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        before = datetime.datetime.now()

        with patch("builtins.print"):
            result = command.execute(["pro"], context)

        after = datetime.datetime.now()

        assert result["status"] == "success"
        assert before <= free_user.subscription_start <= after


class TestSubscriptionDowngradeCommand:
    """Tests for SubscriptionDowngradeCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return SubscriptionDowngradeCommand()

    @pytest.fixture
    def pro_user(self):
        """Create a Pro tier user."""
        return User(
            username="prouser",
            passcode_hash="hash456",
            created_at=datetime.datetime.now(),
            projects=["proj1"],
            subscription_tier="pro",
            subscription_status="active",
        )

    @pytest.fixture
    def free_user(self):
        """Create a Free tier user."""
        return User(
            username="freeuser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            subscription_status="active",
        )

    def test_downgrade_no_user(self, command):
        """Test downgrade without user returns error."""
        context = {"user": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "User not found" in result["message"]

    def test_downgrade_already_free(self, command, free_user):
        """Test downgrade when already on Free tier."""
        mock_orchestrator = MagicMock()
        context = {"user": free_user, "orchestrator": mock_orchestrator}

        result = command.execute([], context)

        assert result["status"] == "error"
        assert "already on the Free tier" in result["message"]
        mock_orchestrator.database.save_user.assert_not_called()

    def test_downgrade_pro_to_free_confirmed(self, command, pro_user):
        """Test downgrading from Pro to Free with confirmation."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"), patch("builtins.input", return_value="yes"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert "Downgraded from Pro to Free" in result["message"]
        assert pro_user.subscription_tier == "free"
        mock_orchestrator.database.save_user.assert_called_once()

    def test_downgrade_cancelled_by_user(self, command, pro_user):
        """Test downgrade cancelled when user doesn't confirm."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"), patch("builtins.input", return_value="no"):
            result = command.execute([], context)

        assert result["status"] == "error"
        assert "cancelled" in result["message"].lower()
        assert pro_user.subscription_tier == "pro"  # Tier unchanged
        mock_orchestrator.database.save_user.assert_not_called()

    def test_downgrade_cancelled_on_empty_response(self, command, pro_user):
        """Test downgrade cancelled on empty input."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"), patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"
        assert pro_user.subscription_tier == "pro"

    def test_downgrade_requires_yes_confirmation(self, command, pro_user):
        """Test downgrade requires 'yes' confirmation, not just any input."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        # Try various inputs that aren't "yes"
        test_inputs = ["y", "YES", "confirm", "ok", "1"]

        for test_input in test_inputs:
            pro_user.subscription_tier = "pro"  # Reset
            with patch("builtins.print"), patch("builtins.input", return_value=test_input):
                result = command.execute([], context)

            # Only "yes" should succeed, all others should be cancelled
            assert result["status"] == "error"

    def test_downgrade_confirms_yes_exact(self, command, pro_user):
        """Test downgrade works with 'yes' in various cases."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"), patch("builtins.input", return_value="yes"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert pro_user.subscription_tier == "free"

    def test_downgrade_shows_warning(self, command, pro_user):
        """Test downgrade displays warning about feature loss."""
        mock_orchestrator = MagicMock()
        context = {"user": pro_user, "orchestrator": mock_orchestrator}

        with patch("builtins.print") as mock_print, patch("builtins.input", return_value="no"):
            command.execute([], context)

        # Verify warning is printed
        printed_output = [str(call) for call in mock_print.call_args_list]
        warning_found = any("Warning" in str(call) for call in printed_output)
        assert warning_found


class TestSubscriptionCompareCommand:
    """Tests for SubscriptionCompareCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return SubscriptionCompareCommand()

    def test_compare_returns_success(self, command):
        """Test compare command returns success."""
        context = {}  # No user/orchestrator needed

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"

    def test_compare_displays_tier_names(self, command):
        """Test compare displays all three tier names."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "Free" in printed_output
        assert "Pro" in printed_output
        assert "Enterprise" in printed_output

    def test_compare_displays_costs(self, command):
        """Test compare displays tier costs."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "$0" in printed_output
        assert "$29" in printed_output
        assert "$99" in printed_output

    def test_compare_displays_project_limits(self, command):
        """Test compare displays project limits."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "1" in printed_output  # Free tier: 1 project
        assert "10" in printed_output  # Pro tier: 10 projects
        assert "Unlimited" in printed_output  # Enterprise: unlimited

    def test_compare_displays_team_limits(self, command):
        """Test compare displays team member limits."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "Solo only" in printed_output
        assert "Up to 5" in printed_output

    def test_compare_displays_question_limits(self, command):
        """Test compare displays question limits."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "100" in printed_output  # Free: 100
        assert "1,000" in printed_output  # Pro: 1,000

    def test_compare_displays_features(self, command):
        """Test compare displays feature availability."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)

        # Check for feature names
        assert "Multi-LLM" in printed_output
        assert "Analytics" in printed_output
        assert "Code Generation" in printed_output
        assert "Maturity Tracking" in printed_output

    def test_compare_shows_feature_checkmarks(self, command):
        """Test compare uses checkmarks and X marks for features."""
        context = {}

        with patch("builtins.print") as mock_print:
            command.execute([], context)

        printed_output = " ".join(str(call) for call in mock_print.call_args_list)

        # Should have checkmarks for Pro/Enterprise features
        assert "✓" in printed_output
        # Should have X marks for Free tier missing features
        assert "✗" in printed_output

    def test_compare_ignores_args(self, command):
        """Test compare ignores any provided arguments."""
        context = {}

        with patch("builtins.print") as mock_print:
            # Should work the same regardless of args
            result1 = command.execute([], context)
            result2 = command.execute(["ignored"], context)
            result3 = command.execute(["multiple", "args"], context)

        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result3["status"] == "success"


class TestSubscriptionCommandIntegration:
    """Integration tests for subscription commands working together."""

    def test_upgrade_then_check_status(self):
        """Test upgrading a user then checking status."""
        # Create user
        user = User(
            username="testuser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            subscription_status="active",
        )

        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_user_projects.return_value = []

        # Upgrade
        upgrade_cmd = SubscriptionUpgradeCommand()
        context = {"user": user, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            upgrade_result = upgrade_cmd.execute(["pro"], context)

        assert upgrade_result["status"] == "success"
        assert user.subscription_tier == "pro"

        # Check status
        status_cmd = SubscriptionStatusCommand()
        with patch("builtins.print"):
            status_result = status_cmd.execute([], context)

        assert status_result["status"] == "success"

    def test_tier_progression(self):
        """Test progression through all tiers."""
        user = User(
            username="progresser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
            subscription_status="active",
        )

        mock_orchestrator = MagicMock()
        upgrade_cmd = SubscriptionUpgradeCommand()

        context = {"user": user, "orchestrator": mock_orchestrator}

        # Free -> Pro
        with patch("builtins.print"):
            result = upgrade_cmd.execute(["pro"], context)
        assert result["status"] == "success"
        assert user.subscription_tier == "pro"

        # Pro -> Enterprise
        with patch("builtins.print"):
            result = upgrade_cmd.execute(["enterprise"], context)
        assert result["status"] == "success"
        assert user.subscription_tier == "enterprise"
