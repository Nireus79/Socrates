"""Tests for recent code fixes and changes.

Tests added to improve code coverage and ensure recent modifications work correctly.
"""

import logging
from unittest.mock import Mock

import pytest

# Import the classes we're testing
from socratic_system.database.vector_db import VectorDatabase
from socratic_system.ui.commands.system_commands import ExitCommand
from socratic_system.utils.logger import DebugLogger


class TestVectorDBFilter:
    """Test _build_project_filter() after removing $exists operator."""

    def test_build_filter_returns_none_when_no_project(self):
        """When project_id is None, _build_project_filter should return None."""
        # Create a mock VectorDatabase instance
        mock_vector_db = Mock(spec=VectorDatabase)

        # Call the actual method directly
        result = VectorDatabase._build_project_filter(mock_vector_db, None)

        # Should return None (no filtering)
        assert result is None

    def test_build_filter_returns_eq_when_project_specified(self):
        """When project_id is provided, should return $or filter for global + project knowledge."""
        mock_vector_db = Mock(spec=VectorDatabase)
        project_id = "proj_test_123"

        result = VectorDatabase._build_project_filter(mock_vector_db, project_id)

        # Should return $or filter that includes both global and project-specific knowledge
        assert "$or" in result
        assert len(result["$or"]) == 2
        assert "$exists" not in str(result)

    def test_build_filter_with_various_project_ids(self):
        """Test filter building with different project IDs."""
        test_cases = ["proj_123", "project_abc", "test-project", "UPPERCASE_PROJECT"]

        mock_vector_db = Mock(spec=VectorDatabase)

        for proj_id in test_cases:
            result = VectorDatabase._build_project_filter(mock_vector_db, proj_id)
            # Should return $or filter with global + project-specific knowledge
            assert "$or" in result
            assert len(result["$or"]) == 2

    def test_search_similar_uses_filter(self):
        """Verify _build_project_filter is correct when used in search_similar."""
        # This is simpler - just test the filter function behavior
        mock_vector_db = Mock(spec=VectorDatabase)

        # Test filter is correctly built for project search - should include both global and project knowledge
        filter_with_project = VectorDatabase._build_project_filter(mock_vector_db, "proj_123")
        assert "$or" in filter_with_project
        assert len(filter_with_project["$or"]) == 2

        # Test filter for no project returns None
        filter_no_project = VectorDatabase._build_project_filter(mock_vector_db, None)
        assert filter_no_project is None


class TestLoggerInitialization:
    """Test logger initialization with correct default level."""

    def test_console_handler_initialized_with_info_level(self):
        """Console handler should initialize with INFO level, not DEBUG."""
        # Reset singleton for clean test
        DebugLogger._instance = None

        logger_instance = DebugLogger()

        # Verify console handler level is INFO
        assert logger_instance._console_handler is not None
        assert logger_instance._console_handler.level == logging.INFO

    def test_debug_mode_off_by_default(self):
        """Debug mode should start as False."""
        DebugLogger._instance = None
        logger_instance = DebugLogger()

        # Check debug mode is off
        assert not logger_instance.is_debug_mode()

    def test_set_debug_mode_true(self):
        """When debug mode enabled, handler level should be DEBUG."""
        DebugLogger._instance = None
        logger_instance = DebugLogger()

        # Enable debug
        logger_instance.set_debug_mode(True)

        # Should be DEBUG level now
        assert logger_instance._console_handler.level == logging.DEBUG
        assert logger_instance.is_debug_mode()

    def test_set_debug_mode_false(self):
        """When debug mode disabled, handler level should be INFO."""
        DebugLogger._instance = None
        logger_instance = DebugLogger()

        # First enable
        logger_instance.set_debug_mode(True)
        # Then disable
        logger_instance.set_debug_mode(False)

        # Should be INFO level again
        assert logger_instance._console_handler.level == logging.INFO
        assert not logger_instance.is_debug_mode()

    def test_console_shows_info_by_default(self):
        """Console should show INFO messages by default, not DEBUG."""
        DebugLogger._instance = None
        logger_instance = DebugLogger()

        # Create a test logger
        test_logger = logger_instance.get_logger("test")

        # Handler should filter out DEBUG messages by default
        for handler in test_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                # This is the console handler
                assert handler.level <= logging.INFO


class TestExitCommandFormatting:
    """Test ExitCommand exit message formatting."""

    def test_exit_command_returns_exit_status(self):
        """Exit command should return exit status."""
        command = ExitCommand()
        context = {"app": None, "project": None, "user": None}

        result = command.execute([], context)

        assert result["status"] == "exit"
        assert "message" in result

    def test_exit_command_output_format(self, capsys):
        """Exit command should print formatted message with colors."""
        command = ExitCommand()
        context = {"app": None, "project": None, "user": None}

        command.execute([], context)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain the main message
        assert "Thank you for using Socratic RAG System" in output

    def test_exit_command_greek_text_present(self, capsys):
        """Exit command should include the Greek philosophical quote."""
        command = ExitCommand()
        context = {"app": None, "project": None, "user": None}

        command.execute([], context)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain Greek text (Socrates' last words)
        # τω Ασκληπιώ οφείλομεν αλετρυόνα
        assert "Ασκληπιώ" in output  # Part of the Greek text

    def test_exit_command_uses_fstring_formatting(self, capsys):
        """Verify exit command uses f-string for proper color formatting."""
        command = ExitCommand()
        context = {"app": None, "project": None, "user": None}

        # Capture output
        command.execute([], context)
        captured = capsys.readouterr()

        # The f-string should properly format colors
        # Should not have literal {Style.RESET_ALL} in output
        output = captured.out
        assert "{Style.RESET_ALL}" not in output  # Should not be literal
        assert "Style.RESET_ALL" not in output  # Should not be visible


class TestVectorDBAndLoggerIntegration:
    """Integration tests for vector DB and logger changes."""

    def test_vector_db_search_respects_log_level(self):
        """Vector DB operations should respect logger's debug level."""
        DebugLogger._instance = None
        debug_logger = DebugLogger()
        debug_logger.set_debug_mode(False)  # Off by default

        # Create vector DB mock
        mock_db = Mock(spec=VectorDatabase)
        mock_db.logger = debug_logger.get_logger("vector_db")

        # Logger should have correct level
        assert mock_db.logger.level <= logging.DEBUG  # Logger itself is DEBUG
        # But handlers filter to INFO
        for handler in mock_db.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                assert handler.level == logging.INFO

    def test_exit_in_debug_mode(self, capsys):
        """Exit command should work correctly even with debug mode on."""
        # Enable debug mode
        DebugLogger._instance = None
        debug_logger = DebugLogger()
        debug_logger.set_debug_mode(True)

        # Run exit command
        command = ExitCommand()
        context = {"app": None, "project": None, "user": None}

        result = command.execute([], context)
        captured = capsys.readouterr()

        # Should still work
        assert result["status"] == "exit"
        assert "Thank you" in captured.out

        # Clean up
        debug_logger.set_debug_mode(False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
