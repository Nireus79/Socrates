"""
Unit tests for git_initializer.py

Tests the GitInitializer for git and GitHub operations.
Uses mocking for external dependencies (git commands, GitHub API).
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
from socratic_system.utils.git_initializer import (
    GitInitializer,
    GitInitializationError,
    GitOperationError,
    GitHubError,
)


class TestGitInitializer:
    """Test suite for GitInitializer"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()
            (project_dir / "README.md").write_text("# Test")
            (project_dir / "main.py").write_text("print('test')")
            yield project_dir

    # ===== Git Installation Tests =====

    @patch("subprocess.run")
    def test_is_git_installed_success(self, mock_run):
        """Test successful git installation check"""
        mock_run.return_value.returncode = 0

        result = GitInitializer.is_git_installed()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_is_git_installed_not_found(self, mock_run):
        """Test git not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = GitInitializer.is_git_installed()

        assert result is False

    @patch("subprocess.run")
    def test_is_git_installed_error(self, mock_run):
        """Test git command error"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = GitInitializer.is_git_installed()

        assert result is False

    # ===== Repository Initialization Tests =====

    @patch("subprocess.run")
    @patch.object(GitInitializer, "is_git_installed", return_value=True)
    def test_initialize_repository_success(self, mock_is_installed, mock_run, temp_project_dir):
        """Test successful git repository initialization"""
        mock_run.return_value.returncode = 0

        success, message = GitInitializer.initialize_repository(temp_project_dir)

        assert success is True
        assert "successfully" in message.lower()
        # Should call git init, config user.name, config user.email, add, commit
        assert mock_run.call_count == 5

    @patch("subprocess.run")
    @patch.object(GitInitializer, "is_git_installed", return_value=True)
    def test_initialize_repository_custom_author(self, mock_is_installed, mock_run, temp_project_dir):
        """Test repo initialization with custom author"""
        mock_run.return_value.returncode = 0

        success, message = GitInitializer.initialize_repository(
            temp_project_dir,
            author_name="Test Author",
            author_email="test@example.com"
        )

        assert success is True
        # Verify author was configured
        calls = [call_obj for call_obj in mock_run.call_args_list]
        config_calls = [c for c in calls if "config" in str(c)]
        assert len(config_calls) > 0

    @patch("subprocess.run")
    @patch.object(GitInitializer, "is_git_installed", return_value=True)
    def test_initialize_repository_custom_message(self, mock_is_installed, mock_run, temp_project_dir):
        """Test repo initialization with custom commit message"""
        mock_run.return_value.returncode = 0

        custom_msg = "Custom initial commit"
        success, message = GitInitializer.initialize_repository(
            temp_project_dir,
            initial_commit_message=custom_msg
        )

        assert success is True
        # Verify custom message was used
        calls = [call_obj for call_obj in mock_run.call_args_list]
        commit_calls = [c for c in calls if "commit" in str(c)]
        assert any(custom_msg in str(c) for c in commit_calls)

    @patch("subprocess.run")
    @patch.object(GitInitializer, "is_git_installed", return_value=True)
    def test_initialize_repository_already_exists(self, mock_is_installed, mock_run, temp_project_dir):
        """Test initializing repo when .git already exists"""
        # Create .git directory
        (temp_project_dir / ".git").mkdir()

        success, message = GitInitializer.initialize_repository(temp_project_dir)

        assert success is True
        assert "already initialized" in message.lower()

    @patch.object(GitInitializer, "is_git_installed", return_value=False)
    def test_initialize_repository_git_not_installed(self, mock_is_installed, temp_project_dir):
        """Test repo initialization when git not installed"""
        success, message = GitInitializer.initialize_repository(temp_project_dir)

        assert success is False
        assert "not installed" in message.lower()

    def test_initialize_repository_invalid_path(self):
        """Test repo initialization with invalid path"""
        invalid_path = Path("/nonexistent/path")

        success, message = GitInitializer.initialize_repository(invalid_path)

        assert success is False
        assert "does not exist" in message

    # ===== GitHub Repository Creation Tests =====

    @patch("requests.post")
    def test_create_github_repository_success(self, mock_post):
        """Test successful GitHub repository creation"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "html_url": "https://github.com/user/repo",
            "clone_url": "https://github.com/user/repo.git",
        }
        mock_post.return_value = mock_response

        success, data = GitInitializer.create_github_repository(
            repo_name="test-repo",
            description="Test repo",
            private=True,
            github_token="ghp_test123"
        )

        assert success is True
        assert data["html_url"] == "https://github.com/user/repo"

    @patch("requests.post")
    def test_create_github_repository_invalid_token(self, mock_post):
        """Test GitHub repo creation with invalid token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        success, data = GitInitializer.create_github_repository(
            repo_name="test-repo",
            description="Test repo",
            private=True,
            github_token="ghp_invalid"
        )

        assert success is False
        assert "authentication" in data.get("error", "").lower()

    @patch("requests.post")
    def test_create_github_repository_already_exists(self, mock_post):
        """Test creating repo that already exists"""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_post.return_value = mock_response

        success, data = GitInitializer.create_github_repository(
            repo_name="existing-repo",
            description="Test",
            private=True,
            github_token="ghp_test123"
        )

        assert success is False
        assert "already exists" in data.get("error", "").lower() or "invalid" in data.get("error", "").lower()

    @patch("requests.post")
    def test_create_github_repository_api_error(self, mock_post):
        """Test GitHub API error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response

        success, data = GitInitializer.create_github_repository(
            repo_name="test-repo",
            description="Test",
            private=True,
            github_token="ghp_test123"
        )

        assert success is False
        assert "error" in data

    @patch("requests.post")
    def test_create_github_repository_network_error(self, mock_post):
        """Test network error during repo creation"""
        mock_post.side_effect = Exception("Network error")

        success, data = GitInitializer.create_github_repository(
            repo_name="test-repo",
            description="Test",
            private=True,
            github_token="ghp_test123"
        )

        assert success is False
        assert "error" in data

    # ===== Push to GitHub Tests =====

    @patch("subprocess.run")
    def test_push_to_github_success(self, mock_run, temp_project_dir):
        """Test successful push to GitHub"""
        # Create .git directory
        (temp_project_dir / ".git").mkdir()

        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        success, message = GitInitializer.push_to_github(
            temp_project_dir,
            "https://github.com/user/repo.git"
        )

        assert success is True
        assert "successfully pushed" in message.lower()

    @patch("subprocess.run")
    def test_push_to_github_authentication_error(self, mock_run, temp_project_dir):
        """Test push with authentication error"""
        (temp_project_dir / ".git").mkdir()

        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "fatal: Authentication failed"

        success, message = GitInitializer.push_to_github(
            temp_project_dir,
            "https://github.com/user/repo.git"
        )

        assert success is False
        assert "authentication" in message.lower()

    def test_push_to_github_not_git_repo(self, temp_project_dir):
        """Test push when not a git repository"""
        success, message = GitInitializer.push_to_github(
            temp_project_dir,
            "https://github.com/user/repo.git"
        )

        assert success is False
        assert "not a git repository" in message.lower()

    # ===== Repository Status Tests =====

    @patch("subprocess.run")
    def test_get_repository_status_valid_repo(self, mock_run, temp_project_dir):
        """Test getting status of valid git repository"""
        (temp_project_dir / ".git").mkdir()

        # Mock subprocess responses
        mock_run.side_effect = [
            # For branch check
            MagicMock(stdout="main\n", returncode=0),
            # For remotes check
            MagicMock(stdout="origin  https://github.com/user/repo.git\n", returncode=0),
            # For status check
            MagicMock(stdout="", returncode=0),
        ]

        status = GitInitializer.get_repository_status(temp_project_dir)

        assert status["is_git_repo"] is True
        assert status["branch"] == "main"

    def test_get_repository_status_not_git_repo(self, temp_project_dir):
        """Test status of non-git directory"""
        status = GitInitializer.get_repository_status(temp_project_dir)

        assert status["is_git_repo"] is False
        assert status["branch"] is None

    # ===== GitHub User Info Tests =====

    @patch("requests.get")
    def test_get_github_user_info_success(self, mock_get):
        """Test successful GitHub user info retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "testuser",
            "id": 123,
            "name": "Test User"
        }
        mock_get.return_value = mock_response

        success, data = GitInitializer.get_github_user_info("ghp_test123")

        assert success is True
        assert data["login"] == "testuser"

    @patch("requests.get")
    def test_get_github_user_info_invalid_token(self, mock_get):
        """Test GitHub user info with invalid token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        success, data = GitInitializer.get_github_user_info("ghp_invalid")

        assert success is False
        assert "authentication" in data.get("error", "").lower()

    @patch("requests.get")
    def test_get_github_user_info_network_error(self, mock_get):
        """Test network error during user info retrieval"""
        mock_get.side_effect = Exception("Network error")

        success, data = GitInitializer.get_github_user_info("ghp_test123")

        assert success is False
        assert "error" in data

    # ===== Integration Tests =====

    @patch("subprocess.run")
    @patch.object(GitInitializer, "is_git_installed", return_value=True)
    def test_full_git_workflow(self, mock_is_installed, mock_run, temp_project_dir):
        """Test complete git initialization and commit workflow"""
        mock_run.return_value.returncode = 0

        success, message = GitInitializer.initialize_repository(temp_project_dir)

        assert success is True
        # Verify multiple git commands were executed
        assert mock_run.call_count >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
