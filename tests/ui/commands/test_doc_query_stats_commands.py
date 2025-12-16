"""
Tests for document, query, and stats commands.

Tests cover:
- DocImportCommand: Import single document files
- DocImportDirCommand: Import directory of documents
- DocListCommand: List imported documents
- ExplainCommand: Get explanation of topics
- SearchCommand: Search knowledge base
- ProjectStatsCommand: View project statistics
- ProjectProgressCommand: Update project progress
- ProjectStatusCommand: Set project status
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.models.project import ProjectContext
from socratic_system.ui.commands.doc_commands import (
    DocImportCommand,
    DocImportDirCommand,
    DocImportUrlCommand,
    DocListCommand,
    DocPasteCommand,
)
from socratic_system.ui.commands.query_commands import (
    ExplainCommand,
    SearchCommand,
)
from socratic_system.ui.commands.stats_commands import (
    ProjectProgressCommand,
    ProjectStatsCommand,
    ProjectStatusCommand,
)


class TestDocImportCommand:
    """Tests for DocImportCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DocImportCommand()

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

    def test_import_no_orchestrator(self, command):
        """Test import without orchestrator returns error."""
        context = {"orchestrator": None}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "Orchestrator not available" in result["message"]

    def test_import_with_args(self, command):
        """Test importing file with command-line path."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "test.pdf",
            "words_extracted": 1000,
            "chunks_created": 50,
            "entries_added": 50,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["path/to/file.pdf"], context)

        assert result["status"] == "success"
        assert result["data"]["file_name"] == "test.pdf"

    def test_import_no_path(self, command):
        """Test import with empty path."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"

    def test_import_with_project_link(self, command, project):
        """Test importing file and linking to project."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "file.pdf",
            "words_extracted": 500,
            "chunks_created": 25,
            "entries_added": 25,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": project,
        }

        with patch("builtins.input", return_value="y"), patch("builtins.print"):
            result = command.execute(["file.pdf"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["project_id"] == "proj123"

    def test_import_without_project_link(self, command, project):
        """Test importing file without linking to project."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "file.pdf",
            "words_extracted": 500,
            "chunks_created": 25,
            "entries_added": 25,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": project,
        }

        with patch("builtins.input", return_value="n"), patch("builtins.print"):
            result = command.execute(["file.pdf"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["project_id"] is None

    def test_import_failure(self, command):
        """Test import failure handling."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "File not found",
        }

        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["nonexistent.pdf"], context)

        assert result["status"] == "error"
        assert "File not found" in result["message"]


class TestDocImportDirCommand:
    """Tests for DocImportDirCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DocImportDirCommand()

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

    def test_import_dir_no_orchestrator(self, command):
        """Test import-dir without orchestrator returns error."""
        context = {"orchestrator": None}
        result = command.execute([], context)

        assert result["status"] == "error"

    def test_import_dir_with_path(self, command):
        """Test importing directory with path."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "files_processed": 5,
            "files_failed": 0,
            "total_words_extracted": 5000,
            "total_chunks_created": 250,
            "total_entries_stored": 250,
        }

        context = {"orchestrator": mock_orchestrator, "project": None}

        # Mock inputs for recursive and project link questions
        with patch("builtins.input", side_effect=["n", "n"]), patch("builtins.print"):
            result = command.execute(["path/to/dir"], context)

        assert result["status"] == "success"
        assert result["data"]["files_processed"] == 5

    def test_import_dir_recursive(self, command):
        """Test importing directory recursively."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "files_processed": 10,
            "files_failed": 1,
            "total_words_extracted": 10000,
            "total_chunks_created": 500,
            "total_entries_stored": 500,
        }

        context = {"orchestrator": mock_orchestrator, "project": None}

        with patch("builtins.input", side_effect=["y", "n"]), patch("builtins.print"):
            result = command.execute(["path/to/dir"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["recursive"] is True

    def test_import_dir_with_failures(self, command):
        """Test import-dir with some failed files."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "files_processed": 8,
            "files_failed": 2,
            "total_words_extracted": 8000,
            "total_chunks_created": 400,
            "total_entries_stored": 400,
        }

        context = {"orchestrator": mock_orchestrator, "project": None}

        with patch("builtins.input", side_effect=["n", "n"]), patch("builtins.print"):
            result = command.execute(["path/to/dir"], context)

        assert result["status"] == "success"
        assert result["data"]["files_failed"] == 2


class TestDocListCommand:
    """Tests for DocListCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DocListCommand()

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

    def test_list_docs_no_orchestrator(self, command, project):
        """Test list without orchestrator."""
        context = {"orchestrator": None, "project": project}
        result = command.execute([], context)

        assert result["status"] == "error"

    def test_list_docs_no_project(self, command):
        """Test list without project and no args."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator, "project": None}

        result = command.execute([], context)

        assert result["status"] == "error"

    def test_list_docs_current_project(self, command, project):
        """Test listing documents for current project."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "documents": [
                {
                    "file_name": "guide.pdf",
                    "entries_count": 50,
                    "imported_at": "2024-01-01",
                },
                {
                    "file_name": "spec.md",
                    "entries_count": 30,
                    "imported_at": "2024-01-02",
                },
            ],
        }

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert len(result["data"]["documents"]) == 2

    def test_list_docs_by_project_id(self, command):
        """Test listing documents for specific project ID."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "documents": [
                {
                    "file_name": "doc.pdf",
                    "entries_count": 40,
                    "imported_at": "2024-01-01",
                }
            ],
        }

        context = {"orchestrator": mock_orchestrator, "project": None}

        with patch("builtins.print"):
            result = command.execute(["proj456"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["project_id"] == "proj456"

    def test_list_docs_empty(self, command, project):
        """Test listing with no documents."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "documents": [],
        }

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"


class TestDocPasteCommand:
    """Tests for DocPasteCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DocPasteCommand()

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

    def test_paste_no_orchestrator(self, command):
        """Test paste without orchestrator returns error."""
        context = {"orchestrator": None}

        # Input sequence: title, content line, EOF marker, (no project link needed)
        with patch("builtins.input", side_effect=["test", "Some content", "EOF"]):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "error"
        assert "Orchestrator not available" in result["message"]

    def test_paste_with_title(self, command):
        """Test pasting text with explicit title."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "title": "my_content",
            "words_extracted": 100,
            "chunks_created": 2,
            "entries_added": 2,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        # Mock multi-line input with title
        with patch("builtins.input", side_effect=["Line 1", "Line 2", "EOF", "n"]):
            with patch("builtins.print"):
                result = command.execute(["my_content"], context)

        assert result["status"] == "success"
        assert result["data"]["title"] == "my_content"
        assert result["data"]["words_extracted"] == 100

    def test_paste_no_content(self, command):
        """Test paste with empty content."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator}

        # Input sequence: empty title (uses default), immediately EOF with no content
        with patch("builtins.input", side_effect=["", "EOF"]):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "error"
        assert "No content provided" in result["message"]

    def test_paste_multiline_content(self, command):
        """Test pasting multiline text."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "title": "pasted_text",
            "words_extracted": 250,
            "chunks_created": 3,
            "entries_added": 3,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        # Multi-line content with title input
        with patch("builtins.input", side_effect=[
            "test_title",  # Title input
            "First line of content",
            "Second line of content",
            "Third line of content",
            "EOF",
            "n"  # Don't link to project
        ]):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["entries_added"] == 3

    def test_paste_with_project_link(self, command, project):
        """Test pasting text and linking to project."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "title": "pasted_text",
            "words_extracted": 150,
            "chunks_created": 2,
            "entries_added": 2,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": project,
        }

        with patch("builtins.input", side_effect=[
            "",  # Use default title
            "Some content here",
            "EOF",
            "y"  # Link to project
        ]):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["project_id"] == "proj123"

    def test_paste_failure(self, command):
        """Test paste failure handling."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Failed to process text",
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        with patch("builtins.input", side_effect=["default_title", "Content", "EOF", "n"]):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "error"
        assert "Failed to process text" in result["message"]


class TestDocImportUrlCommand:
    """Tests for DocImportUrlCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DocImportUrlCommand()

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

    def test_import_url_no_orchestrator(self, command):
        """Test import-url without orchestrator returns error."""
        context = {"orchestrator": None}

        with patch("builtins.input", return_value="https://example.com"):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "error"
        assert "Orchestrator not available" in result["message"]

    def test_import_url_with_args(self, command):
        """Test importing URL with command-line URL."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "example_com",
            "url": "https://example.com",
            "words_extracted": 2000,
            "chunks_created": 100,
            "entries_added": 100,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["https://example.com"], context)

        assert result["status"] == "success"
        assert result["data"]["file_name"] == "example_com"
        assert result["data"]["url"] == "https://example.com"

    def test_import_url_no_url(self, command):
        """Test import with empty URL."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"
        assert "URL cannot be empty" in result["message"]

    def test_import_url_invalid_format(self, command):
        """Test import with invalid URL format."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["example.com"], context)

        assert result["status"] == "error"
        assert "http://" in result["message"] or "https://" in result["message"]

    def test_import_url_https(self, command):
        """Test importing HTTPS URL."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "github_com",
            "url": "https://github.com/example/repo",
            "words_extracted": 3000,
            "chunks_created": 150,
            "entries_added": 150,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["https://github.com/example/repo"], context)

        assert result["status"] == "success"
        assert "github_com" in result["data"]["file_name"]

    def test_import_url_with_project_link(self, command, project):
        """Test importing URL and linking to project."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "doc_example",
            "url": "https://docs.example.com",
            "words_extracted": 1500,
            "chunks_created": 75,
            "entries_added": 75,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": project,
        }

        with patch("builtins.input", return_value="y"), patch("builtins.print"):
            result = command.execute(["https://docs.example.com"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["project_id"] == "proj123"

    def test_import_url_without_project_link(self, command, project):
        """Test importing URL without linking to project."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "doc_example",
            "url": "https://docs.example.com",
            "words_extracted": 1500,
            "chunks_created": 75,
            "entries_added": 75,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": project,
        }

        with patch("builtins.input", return_value="n"), patch("builtins.print"):
            result = command.execute(["https://docs.example.com"], context)

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert call_args[0][1]["project_id"] is None

    def test_import_url_with_spaces(self, command):
        """Test importing URL with spaces handled correctly."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "example_com",
            "url": "https://example.com/page",
            "words_extracted": 1000,
            "chunks_created": 50,
            "entries_added": 50,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        # URL split across multiple args gets joined
        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["https://example.com/page"], context)

        assert result["status"] == "success"

    def test_import_url_failure(self, command):
        """Test import URL failure handling."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Failed to fetch URL: Connection timeout",
        }

        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["https://nonexistent-domain-12345.com"], context)

        assert result["status"] == "error"
        assert "Failed to fetch" in result["message"] or "Connection" in result["message"]

    def test_import_url_http(self, command):
        """Test importing HTTP (non-HTTPS) URL."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "file_name": "oldsite_com",
            "url": "http://oldsite.com",
            "words_extracted": 800,
            "chunks_created": 40,
            "entries_added": 40,
        }

        context = {
            "orchestrator": mock_orchestrator,
            "project": None,
        }

        with patch("builtins.input"), patch("builtins.print"):
            result = command.execute(["http://oldsite.com"], context)

        assert result["status"] == "success"


class TestExplainCommand:
    """Tests for ExplainCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ExplainCommand()

    def test_explain_no_orchestrator(self, command):
        """Test explain without orchestrator."""
        context = {"orchestrator": None}
        result = command.execute(["concept"], context)

        assert result["status"] == "error"

    def test_explain_no_topic(self, command):
        """Test explain with no topic."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"

    def test_explain_with_topic(self, command):
        """Test explaining a topic."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client.generate_response.return_value = "Detailed explanation..."
        mock_orchestrator.vector_db = None

        context = {"orchestrator": mock_orchestrator, "project": None}

        with patch("builtins.print"):
            result = command.execute(["database", "design"], context)

        assert result["status"] == "success"
        assert result["data"]["topic"] == "database design"

    def test_explain_with_context(self, command):
        """Test explaining with vector database context."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client.generate_response.return_value = (
            "Explanation with context..."
        )
        mock_orchestrator.vector_db.search_similar.return_value = [
            {
                "content": "Relevant knowledge...",
                "metadata": {"source": "doc1"},
            }
        ]

        context = {"orchestrator": mock_orchestrator, "project": None}

        with patch("builtins.print"):
            result = command.execute(["REST API"], context)

        assert result["status"] == "success"
        assert result["data"]["has_context"] is True

    def test_explain_exception_handling(self, command):
        """Test explain handles exceptions gracefully."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client.generate_response.side_effect = Exception("API error")

        context = {"orchestrator": mock_orchestrator, "project": None}

        with patch("builtins.print"):
            result = command.execute(["topic"], context)

        assert result["status"] == "error"


class TestSearchCommand:
    """Tests for SearchCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return SearchCommand()

    def test_search_no_vector_db(self, command):
        """Test search without vector database."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.vector_db = None

        context = {"orchestrator": mock_orchestrator}

        result = command.execute(["query"], context)

        assert result["status"] == "error"

    def test_search_no_query(self, command):
        """Test search with no query."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.vector_db = MagicMock()

        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.input", return_value=""):
            result = command.execute([], context)

        assert result["status"] == "error"

    def test_search_with_results(self, command):
        """Test search with results."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.vector_db.search_similar.return_value = [
            {
                "content": "Result 1 content",
                "metadata": {"source": "file1.pdf"},
            },
            {
                "content": "Result 2 content",
                "metadata": {"source": "file2.pdf"},
            },
        ]

        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["python"], context)

        assert result["status"] == "success"
        assert result["data"]["results"] == 2

    def test_search_no_results(self, command):
        """Test search with no results."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.vector_db.search_similar.return_value = []

        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["nonexistent"], context)

        assert result["status"] == "success"
        assert result["data"]["results"] == 0

    def test_search_exception_handling(self, command):
        """Test search handles exceptions."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.vector_db.search_similar.side_effect = Exception("Search failed")

        context = {"orchestrator": mock_orchestrator}

        with patch("builtins.print"):
            result = command.execute(["query"], context)

        assert result["status"] == "error"


class TestProjectStatsCommand:
    """Tests for ProjectStatsCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectStatsCommand()

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test goals",
            requirements=["req1", "req2"],
            tech_stack=["python", "django"],
            constraints=["time"],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    def test_stats_no_project(self, command):
        """Test stats without project."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"

    def test_stats_success(self, command, project):
        """Test getting project stats."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "statistics": {
                "project_name": "Test Project",
                "owner": "testuser",
                "current_phase": "discovery",
                "status": "active",
                "progress": 50,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-15",
                "days_active": 14,
                "collaborators": 0,
                "requirements": 2,
                "tech_stack": 2,
                "constraints": 1,
                "total_conversations": 25,
                "questions_asked": 15,
                "responses_given": 25,
                "notes": 5,
            },
        }

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["statistics"]["project_name"] == "Test Project"

    def test_stats_failure(self, command, project):
        """Test stats when orchestrator fails."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Failed to get statistics",
        }

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "error"


class TestProjectProgressCommand:
    """Tests for ProjectProgressCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectProgressCommand()

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
            progress=0,
        )

    def test_progress_no_project(self, command):
        """Test progress without project."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"

    def test_progress_with_args(self, command, project):
        """Test updating progress with arguments."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {"status": "success"}

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute(["75"], context)

        assert result["status"] == "success"
        assert result["data"]["progress"] == 75
        assert project.progress == 75

    def test_progress_invalid_number(self, command, project):
        """Test progress with non-numeric input."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator, "project": project}

        result = command.execute(["invalid"], context)

        assert result["status"] == "error"
        assert "must be a number" in result["message"]

    def test_progress_out_of_range(self, command, project):
        """Test progress with out-of-range values."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator, "project": project}

        # Test < 0
        result = command.execute(["-5"], context)
        assert result["status"] == "error"

        # Test > 100
        result = command.execute(["150"], context)
        assert result["status"] == "error"

    def test_progress_boundary_values(self, command, project):
        """Test progress with boundary values."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {"status": "success"}

        context = {"orchestrator": mock_orchestrator, "project": project}

        # Test 0
        with patch("builtins.print"):
            result = command.execute(["0"], context)
        assert result["status"] == "success"

        # Reset and test 100
        project.progress = 0
        with patch("builtins.print"):
            result = command.execute(["100"], context)
        assert result["status"] == "success"


class TestProjectStatusCommand:
    """Tests for ProjectStatusCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectStatusCommand()

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
            status="active",
        )

    def test_status_no_project(self, command):
        """Test status without project."""
        context = {"project": None, "orchestrator": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"

    def test_status_with_args(self, command, project):
        """Test setting status with arguments."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {"status": "success"}

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute(["completed"], context)

        assert result["status"] == "success"
        assert result["data"]["status"] == "completed"
        assert project.status == "completed"

    def test_status_invalid(self, command, project):
        """Test setting invalid status."""
        mock_orchestrator = MagicMock()
        context = {"orchestrator": mock_orchestrator, "project": project}

        result = command.execute(["invalid"], context)

        assert result["status"] == "error"
        assert "Invalid status" in result["message"]

    def test_status_valid_options(self, command, project):
        """Test all valid status options."""
        valid_statuses = ["active", "completed", "on-hold"]

        for status_val in valid_statuses:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_request.return_value = {"status": "success"}

            context = {"orchestrator": mock_orchestrator, "project": project}

            with patch("builtins.print"):
                result = command.execute([status_val], context)

            assert result["status"] == "success"
            assert result["data"]["status"] == status_val

    def test_status_case_insensitive(self, command, project):
        """Test status is case insensitive."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {"status": "success"}

        context = {"orchestrator": mock_orchestrator, "project": project}

        with patch("builtins.print"):
            result = command.execute(["COMPLETED"], context)

        assert result["status"] == "success"
        assert project.status == "completed"
