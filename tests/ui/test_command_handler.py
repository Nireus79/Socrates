"""
Tests for CommandHandler - Command parsing, routing, and execution
"""

from unittest.mock import MagicMock

import pytest

from socratic_system.ui.command_handler import CommandHandler
from socratic_system.ui.commands.base import BaseCommand


@pytest.mark.unit
class TestCommandHandlerInitialization:
    """Tests for CommandHandler initialization"""

    def test_command_handler_initialization(self):
        """Test CommandHandler initializes correctly"""
        handler = CommandHandler()

        assert handler is not None
        assert handler.commands == {}
        assert handler.aliases == {}

    def test_command_handler_has_registries(self):
        """Test that handler has command and alias registries"""
        handler = CommandHandler()

        assert hasattr(handler, "commands")
        assert hasattr(handler, "aliases")
        assert isinstance(handler.commands, dict)
        assert isinstance(handler.aliases, dict)


@pytest.mark.unit
class TestCommandRegistration:
    """Tests for command registration"""

    def test_register_single_command(self):
        """Test registering a single command"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test", description="Test command")
        handler.register_command(cmd)

        assert "test" in handler.commands
        assert handler.commands["test"] == cmd

    def test_register_multiple_commands(self):
        """Test registering multiple commands at once"""
        handler = CommandHandler()

        class TestCommand1(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        class TestCommand2(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd1 = TestCommand1(name="test1")
        cmd2 = TestCommand2(name="test2")

        handler.register_commands([cmd1, cmd2])

        assert "test1" in handler.commands
        assert "test2" in handler.commands
        assert len(handler.commands) == 2

    def test_register_command_with_aliases(self):
        """Test registering a command with aliases"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test command")
        handler.register_command(cmd, aliases=["t", "tst"])

        assert "test command" in handler.commands
        assert handler.aliases["t"] == "test command"
        assert handler.aliases["tst"] == "test command"

    def test_register_overwrites_existing_command(self):
        """Test that registering duplicate command name overwrites"""
        handler = CommandHandler()

        class TestCommand1(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "version": 1}

        class TestCommand2(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "version": 2}

        cmd1 = TestCommand1(name="test")
        cmd2 = TestCommand2(name="test")

        handler.register_command(cmd1)
        handler.register_command(cmd2)

        # Second registration should overwrite
        assert handler.commands["test"] == cmd2


@pytest.mark.unit
class TestCommandExecution:
    """Tests for command execution"""

    def test_execute_registered_command(self):
        """Test executing a registered command"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "args": args}

        cmd = TestCommand(name="test")
        handler.register_command(cmd)

        context = {"user": MagicMock()}
        result = handler.execute("/test arg1 arg2", context)

        assert result["status"] == "success"
        assert "arg1" in result["args"]
        assert "arg2" in result["args"]

    def test_execute_command_missing_slash(self):
        """Test error when command doesn't start with slash"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")
        handler.register_command(cmd)

        context = {}
        result = handler.execute("test arg1", context)

        assert result["status"] == "error"
        assert "must start with '/'" in result["message"].lower()

    def test_execute_unknown_command(self):
        """Test error when command doesn't exist"""
        handler = CommandHandler()

        context = {}
        result = handler.execute("/nonexistent", context)

        assert result["status"] == "error"
        assert "Unknown command" in result["message"]

    def test_execute_empty_input(self):
        """Test handling empty input"""
        handler = CommandHandler()

        context = {}
        result = handler.execute("", context)

        assert result["status"] == "idle"

    def test_execute_whitespace_only_input(self):
        """Test handling whitespace-only input"""
        handler = CommandHandler()

        context = {}
        result = handler.execute("   ", context)

        assert result["status"] == "idle"

    def test_execute_with_quoted_arguments(self):
        """Test command execution with quoted arguments"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "args": args}

        cmd = TestCommand(name="test")
        handler.register_command(cmd)

        context = {}
        result = handler.execute('/test "arg with spaces" arg2', context)

        assert result["status"] == "success"
        assert "arg with spaces" in result["args"]

    def test_execute_multiword_command(self):
        """Test executing multi-word commands"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "args": args}

        cmd = TestCommand(name="project list")
        handler.register_command(cmd)

        context = {}
        result = handler.execute("/project list all", context)

        assert result["status"] == "success"
        assert "all" in result["args"]


@pytest.mark.unit
class TestCommandAliases:
    """Tests for command alias resolution"""

    def test_execute_with_alias(self):
        """Test executing command via alias"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="help")
        handler.register_command(cmd, aliases=["h", "?"])

        context = {}

        # Execute using alias
        result = handler.execute("/h", context)
        assert result["status"] == "success"

        # Execute using other alias
        result = handler.execute("/?", context)
        assert result["status"] == "success"

    def test_get_command_via_alias(self):
        """Test getting command via alias"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="help")
        handler.register_command(cmd, aliases=["h"])

        # Get via alias
        retrieved = handler.get_command("h")
        assert retrieved == cmd
        assert retrieved.name == "help"


@pytest.mark.unit
class TestCommandMatching:
    """Tests for command matching logic"""

    def test_match_three_word_command(self):
        """Test matching three-word commands"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="project archive restore")
        handler.register_command(cmd)

        context = {}
        result = handler.execute("/project archive restore args", context)

        # Should match three-word command
        assert result["status"] == "success"

    def test_match_two_word_command(self):
        """Test matching two-word commands"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="project list")
        handler.register_command(cmd)

        context = {}
        result = handler.execute("/project list", context)

        assert result["status"] == "success"

    def test_match_one_word_command(self):
        """Test matching one-word commands"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="help")
        handler.register_command(cmd)

        context = {}
        result = handler.execute("/help", context)

        assert result["status"] == "success"

    def test_command_matching_priority(self):
        """Test that longer command names take priority"""
        handler = CommandHandler()

        class TestCommand1(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "matched": "two-word"}

        class TestCommand2(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "matched": "one-word"}

        # Register both
        cmd1 = TestCommand1(name="project list")
        cmd2 = TestCommand2(name="project")
        handler.register_command(cmd2)
        handler.register_command(cmd1)

        context = {}
        result = handler.execute("/project list", context)

        # Two-word should match
        assert result["matched"] == "two-word"


@pytest.mark.unit
class TestCommandQueries:
    """Tests for command query methods"""

    def test_get_command_by_name(self):
        """Test getting command by exact name"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="help")
        handler.register_command(cmd)

        retrieved = handler.get_command("help")
        assert retrieved == cmd

    def test_get_nonexistent_command(self):
        """Test getting non-existent command"""
        handler = CommandHandler()

        retrieved = handler.get_command("nonexistent")
        assert retrieved is None

    def test_get_all_commands(self):
        """Test getting all registered commands"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd1 = TestCommand(name="cmd1")
        cmd2 = TestCommand(name="cmd2")
        cmd3 = TestCommand(name="cmd3")

        handler.register_commands([cmd1, cmd2, cmd3])

        all_cmds = handler.get_all_commands()
        assert len(all_cmds) == 3
        assert "cmd1" in all_cmds
        assert "cmd2" in all_cmds
        assert "cmd3" in all_cmds

    def test_get_all_commands_returns_copy(self):
        """Test that get_all_commands returns a copy, not reference"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        cmd = TestCommand(name="test")
        handler.register_command(cmd)

        cmds1 = handler.get_all_commands()
        cmds2 = handler.get_all_commands()

        # Should be equal but not same object
        assert cmds1 == cmds2
        assert cmds1 is not cmds2

    def test_get_commands_by_prefix(self):
        """Test getting commands by prefix"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        handler.register_commands(
            [
                TestCommand(name="project create"),
                TestCommand(name="project list"),
                TestCommand(name="project delete"),
                TestCommand(name="user login"),
            ]
        )

        project_cmds = handler.get_commands_by_prefix("project")

        assert len(project_cmds) == 3
        assert all(name.startswith("project") for name in project_cmds.keys())

    def test_get_commands_by_prefix_case_insensitive(self):
        """Test that prefix matching is case-insensitive"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        handler.register_command(TestCommand(name="Project Create"))

        cmds = handler.get_commands_by_prefix("PROJECT")

        assert len(cmds) > 0


@pytest.mark.unit
class TestCommandValidation:
    """Tests for command validation"""

    def test_is_valid_command(self):
        """Test validating registered command"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        handler.register_command(TestCommand(name="test"))

        assert handler.is_valid_command("test") is True
        assert handler.is_valid_command("nonexistent") is False

    def test_is_valid_command_with_alias(self):
        """Test validating command via alias"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        handler.register_command(TestCommand(name="test"), aliases=["t"])

        assert handler.is_valid_command("t") is True


@pytest.mark.unit
class TestCommandErrorHandling:
    """Tests for command error handling"""

    def test_handle_parse_error(self):
        """Test handling of parsing errors"""
        handler = CommandHandler()

        class TestCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        handler.register_command(TestCommand(name="test"))

        # Invalid quote will cause parse error
        context = {}
        result = handler.execute('/test "unclosed quote', context)

        assert result["status"] == "error"
        assert "Parse error" in result["message"]

    def test_handle_command_execution_error(self):
        """Test handling of command execution errors"""
        handler = CommandHandler()

        class FaultyCommand(BaseCommand):
            def execute(self, args, context):
                raise ValueError("Command error")

        handler.register_command(FaultyCommand(name="faulty"))

        context = {}
        result = handler.execute("/faulty", context)

        assert result["status"] == "error"
        assert "Command error" in result["message"]


@pytest.mark.integration
class TestCommandHandlerIntegration:
    """Integration tests for CommandHandler"""

    def test_full_command_workflow(self):
        """Test complete workflow: register and execute commands"""
        handler = CommandHandler()

        class HelpCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "message": "Help text"}

        class ProjectCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success", "message": f"Project action: {' '.join(args)}"}

        help_cmd = HelpCommand(name="help")
        proj_cmd = ProjectCommand(name="project")

        handler.register_commands([help_cmd, proj_cmd])
        handler.register_command(help_cmd, aliases=["h", "?"])

        # Execute via main name
        result1 = handler.execute("/help", {})
        assert result1["status"] == "success"

        # Execute via alias
        result2 = handler.execute("/h", {})
        assert result2["status"] == "success"

        # Execute multi-word
        result3 = handler.execute("/project create myproject", {})
        assert result3["status"] == "success"
        assert "myproject" in result3["message"]

    def test_multiple_command_categories(self):
        """Test handler with multiple command categories"""
        handler = CommandHandler()

        class GenericCommand(BaseCommand):
            def execute(self, args, context):
                return {"status": "success"}

        # Register commands from different categories
        handler.register_commands(
            [
                GenericCommand(name="user login"),
                GenericCommand(name="user create"),
                GenericCommand(name="project create"),
                GenericCommand(name="project list"),
                GenericCommand(name="help"),
            ]
        )

        # All should be registered
        assert len(handler.commands) == 5

        # Prefix queries should work
        user_cmds = handler.get_commands_by_prefix("user")
        project_cmds = handler.get_commands_by_prefix("project")

        assert len(user_cmds) == 2
        assert len(project_cmds) == 2
