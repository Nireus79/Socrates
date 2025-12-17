"""
Tests for GitHub integration and project analysis commands.

Tests cover:
- GithubImportCommand: Import GitHub repository
- GithubPullCommand: Pull latest changes from GitHub
- GithubPushCommand: Push changes to GitHub
- GithubSyncCommand: Sync with GitHub (pull + push)
- ProjectAnalyzeCommand: Analyze project code
- ProjectTestCommand: Run project tests
- ProjectValidateCommand: Validate project
- ProjectFixCommand: Fix project issues
- ProjectReviewCommand: Review project code
- ProjectDiffCommand: Compare validation results
"""

import datetime
from unittest.mock import MagicMock, patch, call

import pytest

from socratic_system.models.project import ProjectContext
from socratic_system.ui.commands.github_commands import (
    GithubImportCommand,
    GithubPullCommand,
    GithubPushCommand,
    GithubSyncCommand,
)
from socratic_system.ui.commands.project_commands import (
    ProjectAnalyzeCommand,
    ProjectTestCommand,
    ProjectValidateCommand,
    ProjectFixCommand,
    ProjectReviewCommand,
    ProjectDiffCommand,
)


@pytest.fixture
def project_with_repo():
    """Create a test project linked to a GitHub repository."""
    return ProjectContext(
        project_id="proj123",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Test goals",
        requirements=[],
        tech_stack=["python"],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="local",
        code_style="documented",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        repository_url="https://github.com/testuser/test-repo",
        repository_name="test-repo",
        repository_owner="testuser",
    )


@pytest.fixture
def project_no_repo():
    """Create a test project without a GitHub repository."""
    return ProjectContext(
        project_id="proj456",
        name="Local Project",
        owner="testuser",
        collaborators=[],
        goals="Test goals",
        requirements=[],
        tech_stack=["python"],
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


# ============================================================================
# GitHub Import Command Tests
# ============================================================================


class TestGithubImportCommand:
    """Tests for GithubImportCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return GithubImportCommand()

    def test_import_not_logged_in(self, command):
        """Test import without authentication."""
        context = {"orchestrator": MagicMock(), "app": MagicMock()}
        result = command.execute(["https://github.com/user/repo"], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_import_no_orchestrator(self, command):
        """Test import without orchestrator."""
        mock_user = MagicMock()
        context = {
            "orchestrator": None,
            "app": MagicMock(),
            "user": mock_user,
        }
        result = command.execute(["https://github.com/user/repo"], context)

        assert result["status"] == "error"
        assert "context not available" in result["message"].lower()

    def test_import_success(self, command):
        """Test successful repository import."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "project": ProjectContext(
                project_id="imported123",
                name="test-repo",
                owner="testuser",
                phase="discovery",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                repository_url="https://github.com/testuser/test-repo",
                repository_name="test-repo",
                repository_owner="testuser",
                repository_language="python",
                repository_file_count=42,
                repository_has_tests=True,
            ),
            "metadata": {
                "language": "python",
                "file_count": 42,
                "has_tests": True,
                "description": "Test repository",
            },
            "validation_results": {
                "overall_status": "pass",
                "issues_count": 0,
                "warnings_count": 2,
            },
        }

        mock_user = MagicMock()
        mock_user.username = "testuser"

        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute(["https://github.com/testuser/test-repo"], context)

        assert result["status"] == "success"
        assert result["data"]["project"].project_id == "imported123"
        mock_orchestrator.process_request.assert_called_once()

    def test_import_with_custom_name(self, command):
        """Test import with custom project name."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "project": ProjectContext(
                project_id="custom123",
                name="My Custom Project",
                owner="testuser",
                phase="discovery",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                repository_url="https://github.com/testuser/test-repo",
            ),
            "metadata": {},
            "validation_results": {},
        }

        mock_user = MagicMock()
        mock_user.username = "testuser"

        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute(
                ["https://github.com/testuser/test-repo", "My", "Custom", "Project"],
                context,
            )

        assert result["status"] == "success"
        call_args = mock_orchestrator.process_request.call_args
        assert "My Custom Project" in call_args[0][1]["project_name"]

    def test_import_failure(self, command):
        """Test import failure handling."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "error",
            "message": "Repository not found",
        }

        mock_user = MagicMock()
        mock_user.username = "testuser"

        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute(["https://github.com/nonexistent/repo"], context)

        assert result["status"] == "error"
        assert "Repository not found" in result["message"]


# ============================================================================
# GitHub Pull Command Tests
# ============================================================================


class TestGithubPullCommand:
    """Tests for GithubPullCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return GithubPullCommand()

    def test_pull_not_logged_in(self, command):
        """Test pull without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_pull_no_project(self, command):
        """Test pull without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_pull_no_repo_url(self, command, project_no_repo):
        """Test pull on project without repository URL."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_no_repo,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "not linked to a GitHub repository" in result["message"]

    def test_pull_success(self, command, project_with_repo):
        """Test successful pull from GitHub."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": True,
            "path": "/tmp/repo",
        }
        mock_git_manager.pull_repository.return_value = {
            "status": "success",
            "message": "Successfully pulled latest changes",
        }
        mock_git_manager.get_git_diff.return_value = "+added line\n-removed line"

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "success"
        mock_git_manager.cleanup.assert_called_once_with("/tmp/repo")

    def test_pull_clone_failure(self, command, project_with_repo):
        """Test pull when clone fails."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": False,
            "error": "Clone failed",
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "error"
        assert "Failed to clone" in result["message"]

    def test_pull_exception_handling(self, command, project_with_repo):
        """Test pull exception handling."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            side_effect=Exception("Git error"),
        ):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "error"
        assert "Git error" in result["message"]


# ============================================================================
# GitHub Push Command Tests
# ============================================================================


class TestGithubPushCommand:
    """Tests for GithubPushCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return GithubPushCommand()

    def test_push_not_logged_in(self, command):
        """Test push without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_push_no_project(self, command):
        """Test push without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_push_no_repo_url(self, command, project_no_repo):
        """Test push on project without repository URL."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_no_repo,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "not linked to a GitHub repository" in result["message"]

    def test_push_success(self, command, project_with_repo):
        """Test successful push to GitHub."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": True,
            "path": "/tmp/repo",
        }
        mock_git_manager.get_git_diff.return_value = "+added\n-removed"
        mock_git_manager.push_repository.return_value = {
            "status": "success",
            "message": "Pushed successfully",
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.input", return_value="yes"):
                with patch("builtins.print"):
                    result = command.execute(["Test commit"], context)

        assert result["status"] == "success"
        mock_git_manager.push_repository.assert_called_once()

    def test_push_no_changes(self, command, project_with_repo):
        """Test push when there are no changes."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": True,
            "path": "/tmp/repo",
        }
        mock_git_manager.get_git_diff.return_value = "No differences"

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.print"):
                result = command.execute([], context)

        assert result["status"] == "success"
        assert "No changes" in result["data"]["message"]

    def test_push_user_cancel(self, command, project_with_repo):
        """Test push cancelled by user."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": True,
            "path": "/tmp/repo",
        }
        mock_git_manager.get_git_diff.return_value = "+added"

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.input", return_value="no"):
                with patch("builtins.print"):
                    result = command.execute([], context)

        assert result["status"] == "success"
        assert "cancelled" in result["data"]["message"].lower()
        mock_git_manager.push_repository.assert_not_called()

    def test_push_auth_error(self, command, project_with_repo):
        """Test push with authentication error."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": True,
            "path": "/tmp/repo",
        }
        mock_git_manager.get_git_diff.return_value = "+added"
        mock_git_manager.push_repository.return_value = {
            "status": "error",
            "message": "Authentication failed: invalid credentials",
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.input", return_value="yes"):
                with patch("builtins.print"):
                    result = command.execute([], context)

        assert result["status"] == "error"
        assert "Authentication" in result["message"]
        assert "GITHUB_TOKEN" in result["message"]


# ============================================================================
# GitHub Sync Command Tests
# ============================================================================


class TestGithubSyncCommand:
    """Tests for GithubSyncCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return GithubSyncCommand()

    def test_sync_not_logged_in(self, command):
        """Test sync without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_sync_no_project(self, command):
        """Test sync without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_sync_success(self, command, project_with_repo):
        """Test successful sync (pull + push)."""
        mock_pull_command = MagicMock()
        mock_pull_command.execute.return_value = {
            "status": "success",
            "data": {"pull_result": {}},
        }

        mock_push_command = MagicMock()
        mock_push_command.execute.return_value = {
            "status": "success",
            "data": {"push_result": {}},
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch(
            "socratic_system.ui.commands.github_commands.GithubPullCommand",
            return_value=mock_pull_command,
        ):
            with patch(
                "socratic_system.ui.commands.github_commands.GithubPushCommand",
                return_value=mock_push_command,
            ):
                with patch("builtins.print"):
                    result = command.execute([], context)

        assert result["status"] == "success"


# ============================================================================
# Project Analysis Command Tests
# ============================================================================


class TestProjectAnalyzeCommand:
    """Tests for ProjectAnalyzeCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectAnalyzeCommand()

    def test_analyze_not_logged_in(self, command):
        """Test analyze without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_analyze_no_project(self, command):
        """Test analyze without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_analyze_success(self, command, project_with_repo):
        """Test successful project analysis."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "analysis": {
                "overall_quality": 75,
                "structure_rating": "good",
                "files_analyzed": 42,
                "lines_of_code": 5000,
                "complexity": "medium",
            },
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["analysis"]["overall_quality"] == 75


# ============================================================================
# Project Test Command Tests
# ============================================================================


class TestProjectTestCommand:
    """Tests for ProjectTestCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectTestCommand()

    def test_test_not_logged_in(self, command):
        """Test without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_test_no_project(self, command):
        """Test without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_test_success(self, command, project_with_repo):
        """Test successful test execution."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "tests_passed": 15,
            "tests_failed": 0,
            "tests_skipped": 2,
            "test_framework": "pytest",
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["tests_passed"] == 15


# ============================================================================
# Project Validate Command Tests
# ============================================================================


class TestProjectValidateCommand:
    """Tests for ProjectValidateCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectValidateCommand()

    def test_validate_not_logged_in(self, command):
        """Test validate without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_validate_no_project(self, command):
        """Test validate without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_validate_success(self, command, project_with_repo):
        """Test successful validation."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "validation": {
                "overall_status": "pass",
                "syntax_valid": True,
                "dependencies_valid": True,
                "tests_passed": True,
                "issues": 0,
                "warnings": 2,
            },
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["validation"]["overall_status"] == "pass"


# ============================================================================
# Project Fix Command Tests
# ============================================================================


class TestProjectFixCommand:
    """Tests for ProjectFixCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectFixCommand()

    def test_fix_not_logged_in(self, command):
        """Test fix without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_fix_no_project(self, command):
        """Test fix without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_fix_success(self, command, project_with_repo):
        """Test successful fix application."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "fixes_applied": 3,
            "fixes_available": 5,
            "issues_resolved": ["syntax_error_1", "style_violation_2"],
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch("builtins.input", return_value="yes"):
            with patch("builtins.print"):
                result = command.execute(["syntax"], context)

        assert result["status"] == "success"
        assert result["data"]["fixes_applied"] >= 0


# ============================================================================
# Project Review Command Tests
# ============================================================================


class TestProjectReviewCommand:
    """Tests for ProjectReviewCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectReviewCommand()

    def test_review_not_logged_in(self, command):
        """Test review without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_review_no_project(self, command):
        """Test review without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute([], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_review_success(self, command, project_with_repo):
        """Test successful code review."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "review": {
                "overall_rating": 7,
                "strengths": ["Good structure", "Well documented"],
                "improvements": ["Add type hints", "Reduce complexity"],
                "patterns_found": ["MVC pattern"],
            },
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute([], context)

        assert result["status"] == "success"
        assert result["data"]["review"]["overall_rating"] >= 0


# ============================================================================
# Project Diff Command Tests
# ============================================================================


class TestProjectDiffCommand:
    """Tests for ProjectDiffCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ProjectDiffCommand()

    def test_diff_not_logged_in(self, command):
        """Test diff without authentication."""
        context = {"orchestrator": MagicMock(), "project": MagicMock()}
        result = command.execute(["val1", "val2"], context)

        assert result["status"] == "error"
        assert "logged in" in result["message"].lower()

    def test_diff_no_project(self, command):
        """Test diff without project loaded."""
        mock_user = MagicMock()
        context = {
            "orchestrator": MagicMock(),
            "app": MagicMock(),
            "project": None,
            "user": mock_user,
        }
        result = command.execute(["val1", "val2"], context)

        assert result["status"] == "error"
        assert "project loaded" in result["message"].lower()

    def test_diff_success(self, command, project_with_repo):
        """Test successful diff comparison."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "diff": {
                "issues_resolved": 3,
                "new_issues": 0,
                "quality_improvement": 15,
                "changes": {
                    "files_modified": 5,
                    "lines_added": 125,
                    "lines_removed": 45,
                },
            },
        }

        mock_user = MagicMock()
        context = {
            "orchestrator": mock_orchestrator,
            "app": MagicMock(),
            "project": project_with_repo,
            "user": mock_user,
        }

        with patch("builtins.print"):
            result = command.execute(["validation1", "validation2"], context)

        assert result["status"] == "success"
        assert result["data"]["diff"]["issues_resolved"] >= 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestGitHubAndProjectIntegration:
    """Integration tests for GitHub and project commands."""

    def test_import_then_analyze_workflow(self, project_with_repo):
        """Test workflow: import repository then analyze."""
        # Simulate import
        import_command = GithubImportCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "project": project_with_repo,
            "metadata": {},
            "validation_results": {},
        }

        mock_user = MagicMock()
        mock_user.username = "testuser"
        app = MagicMock()

        import_context = {
            "orchestrator": mock_orchestrator,
            "app": app,
            "user": mock_user,
        }

        with patch("builtins.print"):
            import_result = import_command.execute(
                ["https://github.com/testuser/test-repo"], import_context
            )

        assert import_result["status"] == "success"

        # Simulate analyze on imported project
        analyze_command = ProjectAnalyzeCommand()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "analysis": {"overall_quality": 75},
        }

        analyze_context = {
            "orchestrator": mock_orchestrator,
            "app": app,
            "project": import_result["data"]["project"],
            "user": mock_user,
        }

        with patch("builtins.print"):
            analyze_result = analyze_command.execute([], analyze_context)

        assert analyze_result["status"] == "success"

    def test_pull_test_push_workflow(self, project_with_repo):
        """Test workflow: pull updates, run tests, push changes."""
        mock_git_manager = MagicMock()
        mock_git_manager.clone_repository.return_value = {
            "success": True,
            "path": "/tmp/repo",
        }
        mock_git_manager.pull_repository.return_value = {
            "status": "success",
            "message": "Pulled successfully",
        }
        mock_git_manager.push_repository.return_value = {
            "status": "success",
            "message": "Pushed successfully",
        }
        mock_git_manager.get_git_diff.return_value = "+line"

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = {
            "status": "success",
            "tests_passed": 10,
        }

        mock_user = MagicMock()
        app = MagicMock()

        context = {
            "orchestrator": mock_orchestrator,
            "app": app,
            "project": project_with_repo,
            "user": mock_user,
        }

        # Pull
        pull_command = GithubPullCommand()
        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.print"):
                pull_result = pull_command.execute([], context)

        assert pull_result["status"] == "success"

        # Test
        test_command = ProjectTestCommand()
        with patch("builtins.print"):
            test_result = test_command.execute([], context)

        assert test_result["status"] == "success"

        # Push
        push_command = GithubPushCommand()
        with patch(
            "socratic_system.ui.commands.github_commands.GitRepositoryManager",
            return_value=mock_git_manager,
        ):
            with patch("builtins.input", return_value="yes"):
                with patch("builtins.print"):
                    push_result = push_command.execute([], context)

        assert push_result["status"] == "success"
