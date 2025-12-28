"""
Tests for UI command system - BaseCommand and all command implementations
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.models import User
from socratic_system.ui.commands.base import BaseCommand
from socratic_system.ui.commands.user_commands import UserCreateCommand, UserLoginCommand


@pytest.mark.unit
class TestBaseCommand:
    """Tests for BaseCommand base class"""

    def test_base_command_initialization(self):
        """Test BaseCommand can be initialized with name and description"""

        class SimpleCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = SimpleCommand(name="test", description="Test command", usage="test <arg>")

        assert cmd.name == "test"
        assert cmd.description == "Test command"
        assert cmd.usage == "test <arg>"
        assert cmd.subcommands == {}

    def test_base_command_register_subcommand(self):
        """Test registering subcommands"""

        class ParentCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        class SubCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        parent = ParentCommand(name="parent")
        sub = SubCommand(name="sub", description="Sub command")

        parent.register_subcommand(sub)

        assert "sub" in parent.subcommands
        assert parent.subcommands["sub"] == sub

    def test_base_command_validate_args_valid(self):
        """Test argument validation with valid args"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")

        # Test various valid argument counts
        assert cmd.validate_args([], min_count=0) is True
        assert cmd.validate_args(["arg1"], min_count=1) is True
        assert cmd.validate_args(["arg1", "arg2"], min_count=0, max_count=2) is True
        assert cmd.validate_args(["arg1"], min_count=1, max_count=1) is True

    def test_base_command_validate_args_invalid(self):
        """Test argument validation with invalid args"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")

        # Test insufficient arguments
        assert cmd.validate_args([], min_count=1) is False
        assert cmd.validate_args(["arg1"], min_count=2) is False

        # Test too many arguments
        assert cmd.validate_args(["arg1", "arg2"], max_count=1) is False
        assert cmd.validate_args(["a", "b", "c"], max_count=2) is False

    def test_base_command_error_response(self):
        """Test error response creation"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return self.error("Test error")

        cmd = TestCommand(name="test")
        result = cmd.error("Something went wrong")

        assert result["status"] == "error"
        assert "Something went wrong" in result["message"]

    def test_base_command_success_response(self):
        """Test success response creation"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")

        # Success without message or data
        result = cmd.success()
        assert result["status"] == "success"
        assert "message" not in result or result["message"] == ""

        # Success with message
        result = cmd.success("Command completed")
        assert result["status"] == "success"
        assert "Command completed" in result["message"]

        # Success with data
        result = cmd.success("Done", data={"id": 123})
        assert result["status"] == "success"
        assert result["data"]["id"] == 123

    def test_base_command_info_response(self):
        """Test info response creation"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")
        result = cmd.info("This is informational")

        assert result["status"] == "info"
        assert "This is informational" in result["message"]

    def test_base_command_require_project(self):
        """Test project requirement checking"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")

        # With project
        context_with_project = {"project": MagicMock()}
        assert cmd.require_project(context_with_project) is True

        # Without project
        context_without_project = {"user": MagicMock()}
        assert cmd.require_project(context_without_project) is False

        # With None project
        context_none_project = {"project": None}
        assert cmd.require_project(context_none_project) is False

    def test_base_command_require_user(self):
        """Test user requirement checking"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")

        # With user
        context_with_user = {"user": MagicMock()}
        assert cmd.require_user(context_with_user) is True

        # Without user
        context_without_user = {"project": MagicMock()}
        assert cmd.require_user(context_without_user) is False

        # With None user
        context_none_user = {"user": None}
        assert cmd.require_user(context_none_user) is False

    def test_base_command_get_help(self):
        """Test help text generation"""

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(
            name="test", description="Test command description", usage="test <arg1> <arg2>"
        )

        help_text = cmd.get_help()

        assert "test" in help_text
        assert "Test command description" in help_text
        assert "test <arg1> <arg2>" in help_text

    def test_base_command_get_help_with_subcommands(self):
        """Test help text with subcommands"""

        class ParentCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        class SubCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        parent = ParentCommand(name="parent", description="Parent command")
        sub = SubCommand(name="sub", description="Sub command")
        parent.register_subcommand(sub)

        help_text = parent.get_help()

        assert "parent" in help_text
        assert "Subcommands" in help_text
        assert "sub" in help_text
        assert "Sub command" in help_text


@pytest.mark.unit
class TestUserLoginCommand:
    """Tests for UserLoginCommand"""

    def test_user_login_command_initialization(self):
        """Test UserLoginCommand initializes correctly"""
        cmd = UserLoginCommand()

        assert cmd.name == "user login"
        assert cmd.description == "Login to an existing account"
        assert cmd.usage == "user login"

    @patch("builtins.input")
    def test_user_login_success(self, mock_input, mock_orchestrator, test_config):
        """Test successful user login"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator

            # Create and save a test user
            user = User(
                username="testuser",
                passcode_hash="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # sha256("password")
                created_at=datetime.now(),
                projects=[],
            )
            # Configure mock to return the user when load_user is called
            orchestrator.database.load_user.return_value = user

            # Mock input
            mock_input.side_effect = ["testuser", "password"]

            cmd = UserLoginCommand()
            context = {
                "orchestrator": orchestrator,
                "app": MagicMock(current_user=None, context_display=MagicMock()),
            }

            result = cmd.execute([], context)

            assert result["status"] == "success"
            assert "data" in result
            assert result["data"]["user"].username == "testuser"

    @patch("builtins.input")
    def test_user_login_nonexistent_user(self, mock_input):
        """Test login with nonexistent user"""
        mock_input.side_effect = ["nonexistent", "password"]
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.load_user.return_value = None

        cmd = UserLoginCommand()
        context = {"orchestrator": mock_orchestrator, "app": MagicMock()}

        result = cmd.execute([], context)

        assert result["status"] == "error"
        assert "User not found" in result["message"]

    @patch("builtins.input")
    def test_user_login_invalid_passcode(self, mock_input, mock_orchestrator, test_config):
        """Test login with invalid passcode"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator

            # Create and save a test user
            user = User(
                username="testuser",
                passcode_hash="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # sha256("password")
                created_at=datetime.now(),
                projects=[],
            )
            # Configure mock to return the user when load_user is called
            orchestrator.database.load_user.return_value = user

            # Mock input with wrong password
            mock_input.side_effect = ["testuser", "wrongpassword"]

            cmd = UserLoginCommand()
            context = {
                "orchestrator": orchestrator,
                "app": MagicMock(current_user=None, context_display=MagicMock()),
            }

            result = cmd.execute([], context)

            assert result["status"] == "error"
            assert "Invalid passcode" in result["message"]

    @patch("builtins.input")
    def test_user_login_empty_username(self, mock_input):
        """Test login with empty username"""
        mock_input.side_effect = ["", "password"]
        mock_orchestrator = MagicMock()

        cmd = UserLoginCommand()
        context = {"orchestrator": mock_orchestrator, "app": MagicMock()}

        result = cmd.execute([], context)

        assert result["status"] == "error"
        assert "Username cannot be empty" in result["message"]

    @patch("builtins.input")
    def test_user_login_empty_passcode(self, mock_input):
        """Test login with empty passcode"""
        mock_input.side_effect = ["testuser", ""]
        mock_orchestrator = MagicMock()

        cmd = UserLoginCommand()
        context = {"orchestrator": mock_orchestrator, "app": MagicMock()}

        result = cmd.execute([], context)

        assert result["status"] == "error"
        assert "Passcode cannot be empty" in result["message"]


@pytest.mark.unit
class TestUserCreateCommand:
    """Tests for UserCreateCommand"""

    def test_user_create_command_initialization(self):
        """Test UserCreateCommand initializes correctly"""
        cmd = UserCreateCommand()

        assert cmd.name == "user create"
        assert cmd.description == "Create a new account"
        assert cmd.usage == "user create"

    @patch("builtins.input")
    def test_user_create_success(self, mock_input, mock_orchestrator, test_config):
        """Test successful user creation"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator

            # Mock input for new user
            mock_input.side_effect = ["newuser", "password", "password"]

            # Configure mock to return None initially (no existing user)
            orchestrator.database.load_user.return_value = None

            cmd = UserCreateCommand()
            context = {
                "orchestrator": orchestrator,
                "app": MagicMock(current_user=None, context_display=MagicMock()),
            }

            result = cmd.execute([], context)

            assert result["status"] == "success"
            assert "user" in result["data"]
            assert result["data"]["user"].username == "newuser"

    @patch("builtins.input")
    def test_user_create_duplicate_username(self, mock_input, mock_orchestrator, test_config):
        """Test creating user with existing username"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator

            # Create initial user
            user = User(
                username="existing",
                passcode_hash="hash",
                created_at=datetime.now(),
                projects=[],
            )
            # Configure mock to return the existing user when load_user is called
            orchestrator.database.load_user.return_value = user

            # Try to create duplicate
            mock_input.side_effect = ["existing", "password", "password"]

            cmd = UserCreateCommand()
            context = {"orchestrator": orchestrator, "app": MagicMock()}

            result = cmd.execute([], context)

            assert result["status"] == "error"
            assert "already exists" in result["message"].lower()

    @patch("builtins.input")
    def test_user_create_passcode_mismatch(self, mock_input):
        """Test creating user with mismatched passcodes"""
        mock_input.side_effect = ["newuser", "password1", "password2"]
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.load_user.return_value = None

        cmd = UserCreateCommand()
        context = {"orchestrator": mock_orchestrator, "app": MagicMock()}

        result = cmd.execute([], context)

        assert result["status"] == "error"
        assert "do not match" in result["message"].lower()

    @patch("builtins.input")
    def test_user_create_empty_username(self, mock_input):
        """Test creating user with empty username"""
        mock_input.side_effect = ["", "password", "password"]
        mock_orchestrator = MagicMock()

        cmd = UserCreateCommand()
        context = {"orchestrator": mock_orchestrator, "app": MagicMock()}

        result = cmd.execute([], context)

        assert result["status"] == "error"
        assert "Username cannot be empty" in result["message"]

    @patch("builtins.input")
    def test_user_create_empty_passcode(self, mock_input):
        """Test creating user with empty passcode"""
        mock_input.side_effect = ["newuser", "", ""]
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.load_user.return_value = None

        cmd = UserCreateCommand()
        context = {"orchestrator": mock_orchestrator, "app": MagicMock()}

        result = cmd.execute([], context)

        assert result["status"] == "error"
        assert "Passcode cannot be empty" in result["message"]

    def test_user_create_missing_orchestrator(self):
        """Test creating user when orchestrator is missing"""
        cmd = UserCreateCommand()
        context = {"app": MagicMock()}  # Missing orchestrator

        result = cmd.execute([], context)

        assert result["status"] == "error"

    def test_user_create_missing_app(self):
        """Test creating user when app is missing"""
        cmd = UserCreateCommand()
        context = {"orchestrator": MagicMock()}  # Missing app

        result = cmd.execute([], context)

        assert result["status"] == "error"
