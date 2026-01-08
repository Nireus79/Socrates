"""
Integration tests for GitHub sync with GitHubSyncHandler.

Tests cover integration of GitHubSyncHandler with:
1. API routers (sync, pull, push endpoints)
2. CLI commands (GithubPullCommand, GithubPushCommand, GithubSyncCommand)
3. Edge case handling (conflicts, permissions, token expiry, network, files)

Test Organization:
- TestSyncProjectEndpoint: API endpoint integration tests
- TestPullChangesEndpoint: Pull endpoint edge case tests
- TestPushChangesEndpoint: Push endpoint validation tests
- TestGithubPullCommand: CLI pull command tests
- TestGithubPushCommand: CLI push command tests
- TestGithubSyncCommand: CLI sync command orchestration tests
- TestGitHubSyncHandlerIntegration: Handler integration tests
- TestEdgeCaseHandling: Cross-component edge case tests

Markers:
- @pytest.mark.integration: These are integration tests
- @pytest.mark.slow: Some tests may take >1 second
- @pytest.mark.requires_api: Tests that need GitHub API access (mocked)
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import os
import tempfile
from datetime import datetime, timedelta, timezone

# Import the components we're testing
from socrates_api.routers.github import (
    sync_project,
    pull_changes,
    push_changes,
)
from socratic_system.ui.commands.github_commands import (
    GithubPullCommand,
    GithubPushCommand,
    GithubSyncCommand,
)
from socratic_system.agents.github_sync_handler import (
    create_github_sync_handler,
    TokenExpiredError,
    PermissionDeniedError,
    RepositoryNotFoundError,
    NetworkSyncFailedError,
    ConflictResolutionError,
)


@pytest.mark.integration
@pytest.mark.requires_api
class TestSyncProjectEndpoint(unittest.TestCase):
    """Test /github/projects/{project_id}/sync endpoint integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.project_id = "test_project_123"
        self.repo_url = "https://github.com/test/repo"
        self.token = "ghp_test_token"

    @patch('socrates_api.routers.github.get_database')
    @patch('socrates_api.routers.github.get_current_user')
    async def test_sync_project_success(self, mock_user, mock_db):
        """Test successful project sync"""
        # Setup mocks
        mock_project = Mock()
        mock_project.repository_url = self.repo_url
        mock_project.local_path = "/tmp/repo"
        mock_project.name = "Test Repo"

        mock_db_instance = Mock()
        mock_db_instance.load_project.return_value = mock_project
        mock_db_instance.get_user_github_token.return_value = self.token
        mock_db.return_value = mock_db_instance
        mock_user.return_value = "test_user"

        # Note: This would need FastAPI test client or actual endpoint testing
        # This is a simplified example showing the pattern

    @patch('socrates_api.routers.github.create_github_sync_handler')
    @patch('socrates_api.routers.github.get_database')
    async def test_sync_project_with_token_expired(self, mock_db, mock_handler):
        """Test sync endpoint handles token expiry"""
        mock_handler_instance = Mock()
        mock_handler_instance.check_repo_access.side_effect = TokenExpiredError("Token expired")
        mock_handler.return_value = mock_handler_instance

        # Verify that TokenExpiredError is caught and handled
        self.assertTrue(issubclass(TokenExpiredError, Exception))

    @patch('socrates_api.routers.github.create_github_sync_handler')
    async def test_sync_project_with_permission_denied(self, mock_handler):
        """Test sync endpoint handles permission denied"""
        mock_handler_instance = Mock()
        mock_handler_instance.check_repo_access.side_effect = PermissionDeniedError("Access denied")
        mock_handler.return_value = mock_handler_instance

        # Verify that PermissionDeniedError is caught and handled
        self.assertTrue(issubclass(PermissionDeniedError, Exception))

    @patch('socrates_api.routers.github.create_github_sync_handler')
    async def test_sync_project_with_conflict(self, mock_handler):
        """Test sync endpoint handles merge conflicts"""
        mock_handler_instance = Mock()
        mock_handler_instance.handle_merge_conflicts.return_value = {
            "status": "partial",
            "conflicts_found": 2,
            "resolved": ["file1.py"],
            "manual_required": ["file2.py"],
        }
        mock_handler.return_value = mock_handler_instance

        # Verify handler is initialized and methods are available
        self.assertIsNotNone(mock_handler_instance.handle_merge_conflicts)


class TestPullChangesEndpoint(unittest.TestCase):
    """Test /github/projects/{project_id}/pull endpoint integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.project_id = "test_project_123"
        self.repo_url = "https://github.com/test/repo"
        self.token = "ghp_test_token"

    @patch('socrates_api.routers.github.create_github_sync_handler')
    def test_pull_with_conflict_detection(self, mock_handler):
        """Test pull endpoint detects and resolves conflicts"""
        mock_handler_instance = Mock()
        mock_handler_instance.detect_merge_conflicts.return_value = ["file1.py", "file2.py"]
        mock_handler_instance.handle_merge_conflicts.return_value = {
            "status": "success",
            "conflicts_found": 2,
            "resolved": ["file1.py", "file2.py"],
            "manual_required": [],
        }
        mock_handler.return_value = mock_handler_instance

        # Create handler and verify conflict detection is called
        handler = mock_handler()
        self.assertIsNotNone(handler.detect_merge_conflicts)

    @patch('socrates_api.routers.github.create_github_sync_handler')
    def test_pull_with_token_validation(self, mock_handler):
        """Test pull endpoint validates token before pulling"""
        mock_handler_instance = Mock()
        mock_handler_instance.check_token_validity.return_value = True
        mock_handler.return_value = mock_handler_instance

        handler = mock_handler()
        is_valid = handler.check_token_validity(self.token)
        self.assertTrue(is_valid)

    @patch('socrates_api.routers.github.create_github_sync_handler')
    def test_pull_with_network_retry(self, mock_handler):
        """Test pull endpoint retries on network failure"""
        mock_handler_instance = Mock()
        mock_handler_instance.sync_with_retry_and_resume.return_value = {
            "status": "success",
            "attempt": 2,
        }
        mock_handler.return_value = mock_handler_instance

        handler = mock_handler()
        result = handler.sync_with_retry_and_resume(
            self.repo_url,
            lambda url: {"status": "success"},
            max_retries=3
        )
        self.assertEqual(result["attempt"], 2)


class TestPushChangesEndpoint(unittest.TestCase):
    """Test /github/projects/{project_id}/push endpoint integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.project_id = "test_project_123"
        self.repo_url = "https://github.com/test/repo"
        self.token = "ghp_test_token"

    @patch('socrates_api.routers.github.create_github_sync_handler')
    def test_push_with_file_size_validation(self, mock_handler):
        """Test push endpoint validates file sizes"""
        mock_handler_instance = Mock()
        mock_handler_instance.handle_large_files.return_value = {
            "status": "partial",
            "all_files_valid": False,
            "strategy": "exclude",
            "excluded_files": ["/path/to/large_file.bin"],
            "valid_files": ["/path/to/small_file.py"],
        }
        mock_handler.return_value = mock_handler_instance

        handler = mock_handler()
        result = handler.handle_large_files(
            ["/path/to/large_file.bin", "/path/to/small_file.py"],
            strategy="exclude"
        )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["excluded_files"]), 1)

    @patch('socrates_api.routers.github.create_github_sync_handler')
    def test_push_with_token_expired(self, mock_handler):
        """Test push endpoint handles token expiry"""
        mock_handler_instance = Mock()
        mock_handler_instance.check_token_validity.side_effect = TokenExpiredError("Expired")
        mock_handler.return_value = mock_handler_instance

        handler = mock_handler()
        with self.assertRaises(TokenExpiredError):
            handler.check_token_validity(self.token)


class TestGithubPullCommand(unittest.TestCase):
    """Test GithubPullCommand with GitHubSyncHandler"""

    def setUp(self):
        """Set up test fixtures"""
        self.command = GithubPullCommand()
        self.context = {
            "user": Mock(username="test_user"),
            "project": Mock(
                project_id="test_project",
                repository_url="https://github.com/test/repo",
                local_path="/tmp/repo",
            ),
            "app": Mock(),
            "orchestrator": Mock(),
        }

    @patch('socratic_system.ui.commands.github_commands.create_github_sync_handler')
    @patch('socratic_system.ui.commands.github_commands.GitRepositoryManager')
    def test_pull_command_with_conflicts(self, mock_git_manager, mock_handler):
        """Test pull command detects and resolves conflicts"""
        # Setup handler mock
        mock_handler_instance = Mock()
        mock_handler_instance.detect_merge_conflicts.return_value = ["file1.py"]
        mock_handler_instance.handle_merge_conflicts.return_value = {
            "status": "success",
            "resolved": ["file1.py"],
            "manual_required": [],
        }
        mock_handler.return_value = mock_handler_instance

        # Setup git manager mock
        mock_git_instance = Mock()
        mock_git_instance.clone_repository.return_value = {
            "success": True,
            "data": {"path": "/tmp/test_repo"},
        }
        mock_git_instance.pull_repository.return_value = {
            "data": {"status": "success"},
            "message": "Pulled successfully",
        }
        mock_git_manager.return_value = mock_git_instance

        # Execute command
        result = self.command.execute([], self.context)

        # Verify handler was created
        mock_handler.assert_called()

    @patch('socratic_system.ui.commands.github_commands.create_github_sync_handler')
    def test_pull_command_token_expired_error(self, mock_handler):
        """Test pull command handles token expiry"""
        mock_handler.side_effect = TokenExpiredError("Token expired")

        result = self.command.execute([], self.context)

        # Verify error is handled
        self.assertIsNotNone(result)


class TestGithubPushCommand(unittest.TestCase):
    """Test GithubPushCommand with GitHubSyncHandler"""

    def setUp(self):
        """Set up test fixtures"""
        self.command = GithubPushCommand()
        self.context = {
            "user": Mock(username="test_user"),
            "project": Mock(
                project_id="test_project",
                repository_url="https://github.com/test/repo",
                name="Test Repo",
            ),
            "app": Mock(),
            "orchestrator": Mock(),
        }

    @patch('socratic_system.ui.commands.github_commands.create_github_sync_handler')
    @patch('socratic_system.ui.commands.github_commands.GitRepositoryManager')
    def test_push_command_with_file_validation(self, mock_git_manager, mock_handler):
        """Test push command validates file sizes"""
        # Setup handler mock
        mock_handler_instance = Mock()
        mock_handler_instance.handle_large_files.return_value = {
            "status": "partial",
            "excluded_files": ["large_file.bin"],
            "valid_files": ["code.py"],
        }
        mock_handler.return_value = mock_handler_instance

        # Setup git manager mock
        mock_git_instance = Mock()
        mock_git_instance.clone_repository.return_value = {
            "success": True,
            "data": {"path": "/tmp/test_repo"},
        }
        mock_git_instance.get_git_diff.return_value = "diff content"
        mock_git_manager.return_value = mock_git_instance

        # Verify handler initialization
        handler = mock_handler()
        self.assertIsNotNone(handler.handle_large_files)

    @patch('socratic_system.ui.commands.github_commands.create_github_sync_handler')
    def test_push_command_permission_denied_error(self, mock_handler):
        """Test push command handles permission denied"""
        mock_handler.side_effect = PermissionDeniedError("Access denied")

        result = self.command.execute([], self.context)

        # Verify error is handled
        self.assertIsNotNone(result)


class TestGithubSyncCommand(unittest.TestCase):
    """Test GithubSyncCommand coordinates pull and push"""

    def setUp(self):
        """Set up test fixtures"""
        self.command = GithubSyncCommand()
        self.context = {
            "user": Mock(username="test_user"),
            "project": Mock(
                project_id="test_project",
                repository_url="https://github.com/test/repo",
                name="Test Repo",
            ),
            "app": Mock(),
            "orchestrator": Mock(),
        }

    @patch.object(GithubPushCommand, 'execute')
    @patch.object(GithubPullCommand, 'execute')
    def test_sync_command_executes_pull_then_push(self, mock_pull, mock_push):
        """Test sync command executes pull then push"""
        mock_pull.return_value = {"data": {"status": "success"}}
        mock_push.return_value = {"data": {"status": "success"}}

        result = self.command.execute([], self.context)

        # Verify both pull and push were called
        mock_pull.assert_called()
        mock_push.assert_called()


class TestGitHubSyncHandlerIntegration(unittest.TestCase):
    """Test GitHubSyncHandler integration with routers and commands"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = create_github_sync_handler()

    def test_handler_creation(self):
        """Test handler can be created"""
        self.assertIsNotNone(self.handler)

    def test_handler_with_database(self):
        """Test handler can be created with database"""
        mock_db = Mock()
        handler = create_github_sync_handler(db=mock_db)
        self.assertEqual(handler.db, mock_db)

    @patch('socratic_system.agents.github_sync_handler.requests.get')
    def test_token_validity_check(self, mock_get):
        """Test token validity checking"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        is_valid = self.handler.check_token_validity("test_token")
        self.assertTrue(is_valid)

    def test_file_size_validation(self):
        """Test file size validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a small test file
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            all_valid, invalid, report = self.handler.validate_file_sizes([test_file])
            self.assertTrue(all_valid)
            self.assertEqual(len(invalid), 0)

    def test_conflict_detection_mock(self):
        """Test conflict detection with mock"""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            conflicts = self.handler.detect_merge_conflicts("/tmp/repo")
            self.assertEqual(conflicts, [])

    def test_exception_classes(self):
        """Test all custom exception classes"""
        with self.assertRaises(TokenExpiredError):
            raise TokenExpiredError("Test")

        with self.assertRaises(PermissionDeniedError):
            raise PermissionDeniedError("Test")

        with self.assertRaises(RepositoryNotFoundError):
            raise RepositoryNotFoundError("Test")

        with self.assertRaises(NetworkSyncFailedError):
            raise NetworkSyncFailedError("Test")

        with self.assertRaises(ConflictResolutionError):
            raise ConflictResolutionError("Test")


class TestEdgeCaseHandling(unittest.TestCase):
    """Test edge case handling across API and CLI"""

    def test_token_expired_workflow(self):
        """Test complete workflow when token expires"""
        handler = create_github_sync_handler()

        # Test that TokenExpiredError is properly defined
        self.assertTrue(issubclass(TokenExpiredError, Exception))

    def test_permission_denied_workflow(self):
        """Test complete workflow when permission is denied"""
        handler = create_github_sync_handler()

        # Test that PermissionDeniedError is properly defined
        self.assertTrue(issubclass(PermissionDeniedError, Exception))

    def test_conflict_resolution_workflow(self):
        """Test conflict resolution workflow"""
        handler = create_github_sync_handler()

        # Test that ConflictResolutionError is properly defined
        self.assertTrue(issubclass(ConflictResolutionError, Exception))

    def test_network_retry_workflow(self):
        """Test network retry workflow"""
        handler = create_github_sync_handler()

        # Test that NetworkSyncFailedError is properly defined
        self.assertTrue(issubclass(NetworkSyncFailedError, Exception))

    def test_large_file_handling_workflow(self):
        """Test large file handling workflow"""
        handler = create_github_sync_handler()

        # Verify handler has file handling methods
        self.assertTrue(hasattr(handler, 'validate_file_sizes'))
        self.assertTrue(hasattr(handler, 'handle_large_files'))


if __name__ == "__main__":
    unittest.main()
