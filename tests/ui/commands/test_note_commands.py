"""
Tests for project note management commands.

Tests cover:
- NoteAddCommand: Create new notes with type, title, tags, and content
- NoteListCommand: List notes with optional type filter
- NoteSearchCommand: Search notes by query
- NoteDeleteCommand: Delete notes with confirmation
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User
from socratic_system.ui.commands.note_commands import (
    NoteAddCommand,
    NoteDeleteCommand,
    NoteListCommand,
    NoteSearchCommand,
)


class TestNoteAddCommand:
    """Tests for NoteAddCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return NoteAddCommand()

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User(
            username="testuser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=["proj123"],
        )

    def test_add_note_no_project(self, command):
        """Test add note without project returns error."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "No project loaded" in result["message"]

    def test_add_note_missing_context(self, command, project):
        """Test add note with missing required context."""
        context = {"project": project, "orchestrator": None}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "Required context not available" in result["message"]

    def test_add_note_with_args(self, command, project, user):
        """Test adding note with command-line arguments."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "note": {
                "note_id": "note123",
                "title": "Test Note",
                "type": "bug",
                "content": "test content",
                "created_by": "testuser",
            },
        }

        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(
                ["bug", "Test", "Note"],
                context,
            )

        assert result["status"] == "success"
        mock_orchestrator.process_request.assert_called_once()
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][0] == "note_manager"
        assert call_args[0][1]["action"] == "add_note"
        assert call_args[0][1]["note_type"] == "bug"
        assert call_args[0][1]["title"] == "Test Note"

    def test_add_note_interactive_input(self, command, project, user):
        """Test adding note with interactive input."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "note": {"note_id": "note456"},
        }

        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        # Mock interactive inputs
        inputs = ["design", "Database Schema", "schema,db", "Create table structure", ""]
        with patch("builtins.input", side_effect=inputs), patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"

    def test_add_note_invalid_type(self, command, project, user):
        """Test adding note with invalid type."""
        mock_orchestrator = MagicMock()
        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        result = command.execute(["invalid", "Title"], context)

        assert result["status"] == "error"
        assert "Invalid note type" in result["message"]

    def test_add_note_valid_types(self, command, project, user):
        """Test all valid note types are accepted."""
        valid_types = ["design", "bug", "idea", "task", "general"]

        for note_type in valid_types:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_request.return_value = {
                "status": "success",
                "note": {"note_id": f"note_{note_type}"},
            }

            context = {
                "project": project,
                "orchestrator": mock_orchestrator,
                "user": user,
            }

            with patch("builtins.input"), patch("builtins.print"):
                result = command.execute([note_type, "Test"], context)

            assert result["status"] == "success"

    def test_add_note_empty_title(self, command, project, user):
        """Test adding note with empty title returns error."""
        mock_orchestrator = MagicMock()
        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        result = command.execute(["bug", ""], context)

        assert result["status"] == "error"

    def test_add_note_with_tags(self, command, project, user):
        """Test adding note with tags."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "note": {"note_id": "note789"},
        }

        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        inputs = ["idea", "New Feature", "feature,discussion", "Some content", ""]
        with patch("builtins.input", side_effect=inputs), patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        request_data = call_args[0][1]
        assert "tags" in request_data

    def test_add_note_orchestrator_failure(self, command, project, user):
        """Test add note when orchestrator fails."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Database error",
        }

        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["bug", "Test"], context)

        assert result["status"] == "error"
        assert "Database error" in result["message"]


class TestNoteListCommand:
    """Tests for NoteListCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return NoteListCommand()

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    def test_list_notes_no_project(self, command):
        """Test list notes without project returns error."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "No project loaded" in result["message"]

    def test_list_notes_no_notes(self, command, project):
        """Test listing when no notes exist."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "notes": [],
            "count": 0,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"

    def test_list_all_notes(self, command, project):
        """Test listing all notes."""
        notes = [
            {
                "note_id": "n1",
                "title": "Bug Fix",
                "type": "bug",
                "created_by": "user1",
                "created_at": "2024-01-01",
                "tags": ["critical"],
                "preview": "This is a bug...",
            },
            {
                "note_id": "n2",
                "title": "New Feature",
                "type": "idea",
                "created_by": "user1",
                "created_at": "2024-01-02",
                "tags": ["feature"],
                "preview": "Add new feature...",
            },
        ]

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "notes": notes,
            "count": 2,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["count"] == 2
        assert len(result["data"]["notes"]) == 2

    def test_list_notes_by_type(self, command, project):
        """Test listing notes filtered by type."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "notes": [
                {
                    "note_id": "n1",
                    "title": "Bug 1",
                    "type": "bug",
                    "created_by": "user1",
                    "created_at": "2024-01-01",
                    "tags": [],
                    "preview": "Bug preview",
                }
            ],
            "count": 1,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["bug"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["note_type"] == "bug"

    def test_list_notes_invalid_type(self, command, project):
        """Test list with invalid type filter."""
        mock_orchestrator = MagicMock()
        context = {"project": project, "orchestrator": mock_orchestrator}

        result = command.execute(["invalid_type"], context)

        assert result["status"] == "error"
        assert "Invalid note type" in result["message"]

    def test_list_notes_orchestrator_failure(self, command, project):
        """Test list when orchestrator fails."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Failed to retrieve notes",
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "error"


class TestNoteSearchCommand:
    """Tests for NoteSearchCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return NoteSearchCommand()

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    def test_search_notes_no_project(self, command):
        """Test search without project returns error."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "No project loaded" in result["message"]

    def test_search_notes_no_query(self, command, project):
        """Test search with empty query."""
        mock_orchestrator = MagicMock()
        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"
        assert "cannot be empty" in result["message"]

    def test_search_notes_with_args(self, command, project):
        """Test search with command-line query."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "results": [
                {
                    "note_id": "n1",
                    "title": "Database Schema",
                    "type": "design",
                    "created_by": "user1",
                    "tags": ["schema"],
                    "preview": "Create tables...",
                }
            ],
            "count": 1,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["database", "schema"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["query"] == "database schema"

    def test_search_notes_no_results(self, command, project):
        """Test search with no results."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "results": [],
            "count": 0,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["nonexistent"], context)

        assert result["status"] == "success"
        assert result["data"]["count"] == 0

    def test_search_notes_multiple_results(self, command, project):
        """Test search with multiple results."""
        results = [
            {
                "note_id": "n1",
                "title": "Test 1",
                "type": "bug",
                "created_by": "user1",
                "tags": [],
                "preview": "Preview 1",
            },
            {
                "note_id": "n2",
                "title": "Test 2",
                "type": "idea",
                "created_by": "user2",
                "tags": ["feature"],
                "preview": "Preview 2",
            },
        ]

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "results": results,
            "count": 2,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["test"], context)

        assert result["status"] == "success"
        assert result["data"]["count"] == 2

    def test_search_notes_orchestrator_failure(self, command, project):
        """Test search when orchestrator fails."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Search failed",
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["test"], context)

        assert result["status"] == "error"


class TestNoteDeleteCommand:
    """Tests for NoteDeleteCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return NoteDeleteCommand()

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    def test_delete_note_no_project(self, command):
        """Test delete without project returns error."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "No project loaded" in result["message"]

    def test_delete_note_no_id(self, command, project):
        """Test delete without note ID."""
        mock_orchestrator = MagicMock()
        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"
        assert "cannot be empty" in result["message"]

    def test_delete_note_with_confirmation(self, command, project):
        """Test deleting note with confirmation."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value="yes"), patch("builtins.print"):
            result = command.execute(["note123"], context)

        assert result["status"] == "success"
        mock_orchestrator.process_request.assert_called_once()
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["note_id"] == "note123"

    def test_delete_note_cancelled(self, command, project):
        """Test deletion cancelled by user."""
        mock_orchestrator = MagicMock()
        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value="no"), patch("builtins.print"):
            result = command.execute(["note123"], context)

        assert result["status"] == "success"
        mock_orchestrator.process_request.assert_not_called()

    def test_delete_note_wrong_confirmation(self, command, project):
        """Test deletion cancelled on wrong confirmation."""
        mock_orchestrator = MagicMock()
        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value="maybe"), patch("builtins.print"):
            result = command.execute(["note123"], context)

        assert result["status"] == "success"
        mock_orchestrator.process_request.assert_not_called()

    def test_delete_note_orchestrator_failure(self, command, project):
        """Test deletion when orchestrator fails."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Note not found",
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value="yes"), patch("builtins.print"):
            result = command.execute(["invalid"], context)

        assert result["status"] == "error"


class TestNoteCommandsIntegration:
    """Integration tests for note commands working together."""

    def test_add_list_search_workflow(self):
        """Test workflow: add note -> list notes -> search notes."""
        project = ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        user = User(
            username="testuser",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=["proj123"],
        )

        mock_orchestrator = MagicMock()

        # 1. Add a note
        add_cmd = NoteAddCommand()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "note": {"note_id": "note1"},
        }

        context = {
            "project": project,
            "orchestrator": mock_orchestrator,
            "user": user,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = add_cmd.execute(["bug", "Test"], context)

        assert result["status"] == "success"

        # 2. List notes
        list_cmd = NoteListCommand()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "notes": [
                {
                    "note_id": "note1",
                    "title": "Test",
                    "type": "bug",
                    "created_by": "testuser",
                    "created_at": "2024-01-01",
                    "tags": [],
                    "preview": "Preview",
                }
            ],
            "count": 1,
        }

        with patch("builtins.print"):
            result = list_cmd.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["count"] == 1

        # 3. Search for note
        search_cmd = NoteSearchCommand()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "results": [
                {
                    "note_id": "note1",
                    "title": "Test",
                    "type": "bug",
                    "created_by": "testuser",
                    "tags": [],
                    "preview": "Preview",
                }
            ],
            "count": 1,
        }

        with patch("builtins.print"):
            result = search_cmd.execute(["test"], context)

        assert result["status"] == "success"

    def test_delete_after_list(self):
        """Test deleting a note after listing."""
        project = ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        mock_orchestrator = MagicMock()

        # List notes first
        list_cmd = NoteListCommand()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "notes": [
                {
                    "note_id": "note1",
                    "title": "Note to Delete",
                    "type": "idea",
                    "created_by": "testuser",
                    "created_at": "2024-01-01",
                    "tags": [],
                    "preview": "Will be deleted",
                }
            ],
            "count": 1,
        }

        context = {"project": project, "orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            list_result = list_cmd.execute([], context)

        assert list_result["status"] == "success"

        # Delete the note
        delete_cmd = NoteDeleteCommand()
        mock_orchestrator.process_request.return_value = {"status": "success"}

        with patch("builtins.input", return_value="yes"), patch("builtins.print"):
            delete_result = delete_cmd.execute(["note1"], context)

        assert delete_result["status"] == "success"
