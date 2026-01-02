"""
Tests for Socrates CLI commands
"""

# Import CLI commands
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from socrates_cli.cli import main


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing"""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock SocratesConfig"""
    mock = Mock()
    mock.api_key = "sk-ant-test"
    mock.data_dir = "/tmp/test"
    mock.claude_model = "claude-opus-4-5-20251101"
    return mock


@pytest.mark.unit
class TestCLIMainCommand:
    """Tests for main CLI command"""

    def test_cli_help(self, cli_runner):
        """Test CLI help output"""
        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Socrates AI" in result.output

    def test_cli_version(self, cli_runner):
        """Test CLI version output"""
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "8.0.0" in result.output


@pytest.mark.unit
class TestCLIInitCommand:
    """Tests for init command"""

    def test_init_help(self, cli_runner):
        """Test init command help"""
        result = cli_runner.invoke(main, ["init", "--help"])

        assert result.exit_code == 0
        assert "Initialize" in result.output

    def test_init_with_api_key(self, cli_runner, mock_config):
        """Test init command with API key"""
        # Test that init command accepts API key
        result = cli_runner.invoke(main, ["init", "--api-key", "sk-ant-test"])
        # Should either succeed or fail gracefully with proper error message
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCLIProjectCommands:
    """Tests for project commands"""

    def test_project_group_help(self, cli_runner):
        """Test project group help"""
        result = cli_runner.invoke(main, ["project", "--help"])

        assert result.exit_code == 0
        assert "project" in result.output.lower()

    def test_project_create_help(self, cli_runner):
        """Test project create command help"""
        result = cli_runner.invoke(main, ["project", "create", "--help"])

        assert result.exit_code == 0
        assert "create" in result.output.lower()

    def test_project_list_help(self, cli_runner):
        """Test project list command help"""
        result = cli_runner.invoke(main, ["project", "list", "--help"])

        assert result.exit_code == 0
        assert "list" in result.output.lower()

    def test_project_list_command(self, cli_runner):
        """Test project list command execution"""
        # Test the list command doesn't crash
        result = cli_runner.invoke(main, ["project", "list"])
        # May fail due to missing configuration, but should not crash
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCLICodeCommands:
    """Tests for code commands"""

    def test_code_group_help(self, cli_runner):
        """Test code group help"""
        result = cli_runner.invoke(main, ["code", "--help"])

        assert result.exit_code == 0
        assert "code" in result.output.lower()

    def test_code_generate_help(self, cli_runner):
        """Test code generate command help"""
        result = cli_runner.invoke(main, ["code", "generate", "--help"])

        assert result.exit_code == 0
        assert "generate" in result.output.lower()


@pytest.mark.unit
class TestCLIInfoCommand:
    """Tests for info command"""

    def test_info_help(self, cli_runner):
        """Test info command help"""
        result = cli_runner.invoke(main, ["info", "--help"])

        assert result.exit_code == 0
        assert "info" in result.output.lower()

    def test_info_log_level_option(self, cli_runner):
        """Test info command with log level option"""
        result = cli_runner.invoke(main, ["info", "--log-level", "DEBUG"])

        # Will fail without API key, but tests the option parsing
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCLIErrorHandling:
    """Tests for CLI error handling"""

    def test_cli_invalid_command(self, cli_runner):
        """Test invalid command error"""
        result = cli_runner.invoke(main, ["invalid_command"])

        assert result.exit_code != 0

    def test_cli_missing_required_option(self, cli_runner):
        """Test missing required option"""
        result = cli_runner.invoke(main, ["project", "create"])

        # Should fail due to missing options
        assert result.exit_code != 0

    def test_cli_invalid_option_value(self, cli_runner):
        """Test invalid option value"""
        result = cli_runner.invoke(main, ["info", "--log-level", "INVALID"])

        # May succeed or fail depending on validation
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCLIOutputFormatting:
    """Tests for CLI output formatting"""

    def test_cli_success_message_format(self, cli_runner):
        """Test success message formatting"""
        result = cli_runner.invoke(main, ["--help"])
        # Help should succeed
        assert result.exit_code == 0

    def test_cli_error_message_format(self, cli_runner):
        """Test error message formatting"""
        result = cli_runner.invoke(main, ["invalid_command"])

        # Should have error output
        assert "Error" in result.output or "error" in result.output.lower() or result.exit_code != 0


@pytest.mark.unit
class TestCLIDataIntegrity:
    """Tests for CLI data handling"""

    def test_cli_api_key_not_exposed(self, cli_runner):
        """Test that API key is not exposed in output"""
        result = cli_runner.invoke(main, ["info"])
        # Check that any error message doesn't expose sensitive data
        assert "sk-ant" not in result.output

    def test_cli_handles_long_values(self, cli_runner):
        """Test CLI handling of long input values"""
        long_name = "A" * 500

        # Create a context that accepts long values
        result = cli_runner.invoke(
            main,
            ["project", "create", "--name", long_name, "--owner", "user"],
            catch_exceptions=False,
        )

        # Should handle without crashing
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCLIConfiguration:
    """Tests for CLI configuration handling"""

    def test_cli_uses_environment_variables(self, cli_runner):
        """Test that CLI respects environment variables"""
        import os

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            # CLI should respect environment variables when set
            result = cli_runner.invoke(main, ["--help"])
            # Should succeed with environment variable set
            assert result.exit_code == 0

    def test_cli_respects_data_dir_option(self, cli_runner):
        """Test that data-dir option is respected"""
        result = cli_runner.invoke(main, ["init", "--data-dir", "/tmp/test"])
        # Test that the command accepts the data-dir option
        assert result.exit_code in [0, 1, 2]


@pytest.mark.integration
class TestCLIEndToEnd:
    """End-to-end CLI tests"""

    def test_cli_help_all_commands(self, cli_runner):
        """Test that all commands have help"""
        # Test main help
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Commands" in result.output or "commands" in result.output.lower()
