"""
Comprehensive test suite for GitHub Sync Edge Case Handler

Tests cover:
1. Merge conflict detection and resolution
2. Large file handling and validation
3. Token expiry detection and refresh
4. Network interruption recovery with retry
5. Permission errors and access revocation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
import os
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from github_sync_handler import (
    GitHubSyncHandler,
    create_github_sync_handler,
    ConflictResolutionError,
    TokenExpiredError,
    PermissionDeniedError,
    RepositoryNotFoundError,
    NetworkSyncFailedError,
    FileSizeExceededError,
)


class TestConflictDetectionAndResolution(unittest.TestCase):
    """Test suite for merge conflict detection and resolution"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = GitHubSyncHandler()
        self.temp_repo = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test artifacts"""
        if os.path.exists(self.temp_repo):
            shutil.rmtree(self.temp_repo)

    @patch("subprocess.run")
    def test_detect_merge_conflicts_success(self, mock_run):
        """Test successful conflict detection"""
        # Mock git diff output with conflicted files
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.py\nfile2.py\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        conflicts = self.handler.detect_merge_conflicts(self.temp_repo)

        self.assertEqual(conflicts, ["file1.py", "file2.py"])
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertIn("git", args[0])
        self.assertIn("diff", args[0])

    @patch("subprocess.run")
    def test_detect_merge_conflicts_no_conflicts(self, mock_run):
        """Test when there are no conflicts"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        conflicts = self.handler.detect_merge_conflicts(self.temp_repo)

        self.assertEqual(conflicts, [])

    @patch("subprocess.run")
    def test_detect_merge_conflicts_git_failure(self, mock_run):
        """Test handling of git command failure"""
        mock_result = Mock()
        mock_result.returncode = 128
        mock_result.stderr = "fatal: not a git repository"
        mock_run.return_value = mock_result

        conflicts = self.handler.detect_merge_conflicts(self.temp_repo)

        self.assertEqual(conflicts, [])

    @patch("subprocess.run")
    def test_resolve_merge_conflict_ours_strategy(self, mock_run):
        """Test resolving conflict with 'ours' strategy"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.handler.resolve_merge_conflict(
            self.temp_repo, "conflict.py", strategy="ours"
        )

        self.assertTrue(result)
        # Should call git checkout --ours and git add
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_resolve_merge_conflict_theirs_strategy(self, mock_run):
        """Test resolving conflict with 'theirs' strategy"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.handler.resolve_merge_conflict(
            self.temp_repo, "conflict.py", strategy="theirs"
        )

        self.assertTrue(result)
        # Verify git checkout --theirs was called
        calls = [c[0][0] for c in mock_run.call_args_list]
        self.assertTrue(any("--theirs" in str(c) for c in calls))

    @patch("subprocess.run")
    def test_resolve_merge_conflict_manual_strategy(self, mock_run):
        """Test that manual strategy returns False"""
        result = self.handler.resolve_merge_conflict(
            self.temp_repo, "conflict.py", strategy="manual"
        )

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_resolve_merge_conflict_failure(self, mock_run):
        """Test conflict resolution failure"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "error: path conflict.py not found"
        mock_run.return_value = mock_result

        result = self.handler.resolve_merge_conflict(
            self.temp_repo, "conflict.py", strategy="ours"
        )

        self.assertFalse(result)

    @patch.object(GitHubSyncHandler, "detect_merge_conflicts")
    @patch.object(GitHubSyncHandler, "resolve_merge_conflict")
    def test_handle_merge_conflicts_full_workflow(
        self, mock_resolve, mock_detect
    ):
        """Test full conflict handling workflow"""
        mock_detect.return_value = ["file1.py", "file2.py"]
        mock_resolve.return_value = True

        result = self.handler.handle_merge_conflicts(
            self.temp_repo, {}, default_strategy="ours"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["conflicts_found"], 2)
        self.assertEqual(len(result["resolved"]), 2)
        self.assertEqual(len(result["manual_required"]), 0)

    @patch.object(GitHubSyncHandler, "detect_merge_conflicts")
    @patch.object(GitHubSyncHandler, "resolve_merge_conflict")
    def test_handle_merge_conflicts_partial_resolution(
        self, mock_resolve, mock_detect
    ):
        """Test when only some conflicts are resolved"""
        mock_detect.return_value = ["file1.py", "file2.py"]
        mock_resolve.side_effect = [True, False]

        result = self.handler.handle_merge_conflicts(
            self.temp_repo, {}, default_strategy="ours"
        )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["resolved"]), 1)
        self.assertEqual(len(result["manual_required"]), 1)

    @patch.object(GitHubSyncHandler, "detect_merge_conflicts")
    def test_handle_merge_conflicts_no_conflicts(self, mock_detect):
        """Test when there are no conflicts"""
        mock_detect.return_value = []

        result = self.handler.handle_merge_conflicts(self.temp_repo, {})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["conflicts_found"], 0)


class TestLargeFileHandling(unittest.TestCase):
    """Test suite for large file handling and validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = GitHubSyncHandler()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test artifacts"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_validate_file_sizes_all_valid(self):
        """Test validation when all files are under limit"""
        # Create test files under limit
        test_files = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write("x" * (10 * 1024 * 1024))  # 10MB
            test_files.append(file_path)

        all_valid, invalid_files, size_report = self.handler.validate_file_sizes(
            test_files
        )

        self.assertTrue(all_valid)
        self.assertEqual(len(invalid_files), 0)
        self.assertEqual(len(size_report), 3)
        for report in size_report:
            self.assertFalse(report["exceeds_limit"])

    def test_validate_file_sizes_file_exceeds_limit(self):
        """Test validation when a file exceeds 100MB limit"""
        # Create a file larger than 100MB
        large_file = os.path.join(self.temp_dir, "large_file.bin")
        with open(large_file, "wb") as f:
            f.write(b"x" * (150 * 1024 * 1024))  # 150MB

        all_valid, invalid_files, size_report = self.handler.validate_file_sizes(
            [large_file]
        )

        self.assertFalse(all_valid)
        self.assertIn(large_file, invalid_files)
        self.assertTrue(size_report[0]["exceeds_limit"])

    def test_validate_file_sizes_nonexistent_file(self):
        """Test validation with nonexistent file"""
        all_valid, invalid_files, size_report = self.handler.validate_file_sizes(
            ["/nonexistent/file.txt"]
        )

        # Should handle gracefully
        self.assertEqual(len(size_report), 0)

    def test_handle_large_files_exclude_strategy(self):
        """Test large file handling with exclude strategy"""
        # Create files - some large, some small
        small_file = os.path.join(self.temp_dir, "small.txt")
        with open(small_file, "wb") as f:
            f.write(b"x" * (10 * 1024 * 1024))  # 10MB

        large_file = os.path.join(self.temp_dir, "large.bin")
        with open(large_file, "wb") as f:
            f.write(b"x" * (150 * 1024 * 1024))  # 150MB

        result = self.handler.handle_large_files(
            [small_file, large_file], strategy="exclude"
        )

        self.assertEqual(result["status"], "partial")
        self.assertIn(large_file, result["excluded_files"])
        self.assertIn(small_file, result["valid_files"])

    def test_handle_large_files_lfs_strategy(self):
        """Test large file handling with LFS strategy"""
        large_file = os.path.join(self.temp_dir, "large.bin")
        with open(large_file, "wb") as f:
            f.write(b"x" * (150 * 1024 * 1024))  # 150MB

        result = self.handler.handle_large_files([large_file], strategy="lfs")

        self.assertEqual(result["status"], "requires_setup")
        self.assertEqual(result["strategy"], "lfs")
        self.assertIn(large_file, result["large_files"])

    def test_handle_large_files_unknown_strategy(self):
        """Test large file handling with unknown strategy"""
        large_file = os.path.join(self.temp_dir, "large.bin")
        with open(large_file, "wb") as f:
            f.write(b"x" * (150 * 1024 * 1024))  # 150MB

        result = self.handler.handle_large_files(
            [large_file], strategy="unknown"
        )

        self.assertEqual(result["status"], "error")

    def test_handle_large_files_all_valid(self):
        """Test when all files are valid"""
        small_file = os.path.join(self.temp_dir, "small.txt")
        with open(small_file, "wb") as f:
            f.write(b"x" * (10 * 1024 * 1024))  # 10MB

        result = self.handler.handle_large_files([small_file])

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["all_files_valid"])


class TestTokenExpiryHandling(unittest.TestCase):
    """Test suite for token expiry detection and refresh"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = GitHubSyncHandler()
        self.valid_token = "ghp_validtoken123"

    @patch("requests.get")
    def test_check_token_validity_success(self, mock_get):
        """Test successful token validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        is_valid = self.handler.check_token_validity(self.valid_token)

        self.assertTrue(is_valid)
        mock_get.assert_called_once()

    def test_check_token_validity_no_token(self):
        """Test validation with no token provided"""
        with self.assertRaises(TokenExpiredError):
            self.handler.check_token_validity(None)

    @patch("requests.get")
    def test_check_token_validity_401_unauthorized(self, mock_get):
        """Test token validation with 401 response"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(TokenExpiredError):
            self.handler.check_token_validity(self.valid_token)

    def test_check_token_validity_expiration_time(self):
        """Test token validation with expiration time check"""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)

        with self.assertRaises(TokenExpiredError):
            self.handler.check_token_validity(
                self.valid_token, token_expiry=expired_time
            )

    def test_check_token_validity_future_expiration(self):
        """Test token validation with future expiration time"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            is_valid = self.handler.check_token_validity(
                self.valid_token, token_expiry=future_time
            )

            self.assertTrue(is_valid)

    @patch("requests.get")
    def test_check_token_validity_network_error(self, mock_get):
        """Test token validation with network error"""
        mock_get.side_effect = Exception("Network error")

        with self.assertRaises(TokenExpiredError):
            self.handler.check_token_validity(self.valid_token)

    @patch.object(GitHubSyncHandler, "check_token_validity")
    def test_sync_with_token_refresh_valid_token(self, mock_check):
        """Test sync when token is valid"""
        mock_check.return_value = True

        result = self.handler.sync_with_token_refresh(
            "https://github.com/user/repo",
            self.valid_token,
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["synced"])

    @patch.object(GitHubSyncHandler, "check_token_validity")
    def test_sync_with_token_refresh_expired_token_no_callback(self, mock_check):
        """Test sync with expired token and no refresh callback"""
        mock_check.side_effect = TokenExpiredError("Token expired")

        result = self.handler.sync_with_token_refresh(
            "https://github.com/user/repo",
            self.valid_token,
            refresh_callback=None,
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("Token expired", result["message"])

    @patch.object(GitHubSyncHandler, "check_token_validity")
    def test_sync_with_token_refresh_with_callback(self, mock_check):
        """Test sync with token refresh callback"""
        mock_check.side_effect = TokenExpiredError("Token expired")
        refresh_callback = Mock(return_value="ghp_newtoken456")

        result = self.handler.sync_with_token_refresh(
            "https://github.com/user/repo",
            self.valid_token,
            refresh_callback=refresh_callback,
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["token_refreshed"])
        refresh_callback.assert_called_once()

    @patch.object(GitHubSyncHandler, "check_token_validity")
    def test_sync_with_token_refresh_callback_failure(self, mock_check):
        """Test sync with failed token refresh"""
        mock_check.side_effect = TokenExpiredError("Token expired")
        refresh_callback = Mock(return_value=None)

        result = self.handler.sync_with_token_refresh(
            "https://github.com/user/repo",
            self.valid_token,
            refresh_callback=refresh_callback,
        )

        self.assertEqual(result["status"], "error")


class TestNetworkRetryAndResume(unittest.TestCase):
    """Test suite for network interruption recovery with retry"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = GitHubSyncHandler()
        self.repo_url = "https://github.com/user/repo"

    def test_sync_with_retry_success_first_attempt(self):
        """Test successful sync on first attempt"""
        sync_func = Mock(return_value={"status": "synced"})

        result = self.handler.sync_with_retry_and_resume(
            self.repo_url, sync_func, max_retries=3
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempt"], 1)
        sync_func.assert_called_once()

    @patch("time.sleep")
    def test_sync_with_retry_success_after_failures(self, mock_sleep):
        """Test successful sync after some failures"""
        sync_func = Mock()
        sync_func.side_effect = [
            ConnectionError("Connection lost"),
            ConnectionError("Connection lost"),
            {"status": "synced"},
        ]

        result = self.handler.sync_with_retry_and_resume(
            self.repo_url, sync_func, max_retries=3
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempt"], 3)
        self.assertEqual(sync_func.call_count, 3)
        # Verify exponential backoff was used
        self.assertEqual(mock_sleep.call_count, 2)

    def test_sync_with_retry_all_attempts_fail(self):
        """Test when all retry attempts fail"""
        sync_func = Mock(side_effect=ConnectionError("Connection lost"))

        with self.assertRaises(NetworkSyncFailedError):
            self.handler.sync_with_retry_and_resume(
                self.repo_url, sync_func, max_retries=3
            )

        self.assertEqual(sync_func.call_count, 3)

    @patch("time.sleep")
    def test_sync_with_retry_exponential_backoff(self, mock_sleep):
        """Test exponential backoff timing"""
        sync_func = Mock()
        sync_func.side_effect = [
            TimeoutError("Timeout"),
            TimeoutError("Timeout"),
            TimeoutError("Timeout"),
        ]

        with self.assertRaises(NetworkSyncFailedError):
            self.handler.sync_with_retry_and_resume(
                self.repo_url, sync_func, max_retries=3
            )

        # Check sleep was called with exponential backoff values
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        self.assertEqual(len(sleep_calls), 2)  # 2 sleeps for 3 attempts
        self.assertEqual(sleep_calls[0], 1)  # First backoff: 1s
        self.assertEqual(sleep_calls[1], 2)  # Second backoff: 2s

    @patch("time.sleep")
    def test_sync_with_retry_max_backoff_cap(self, mock_sleep):
        """Test that backoff is capped at MAX_BACKOFF"""
        sync_func = Mock(side_effect=IOError("IO Error"))

        with self.assertRaises(NetworkSyncFailedError):
            self.handler.sync_with_retry_and_resume(
                self.repo_url, sync_func, max_retries=6
            )

        # Check sleep calls don't exceed MAX_BACKOFF (32s)
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        self.assertTrue(all(s <= 32 for s in sleep_calls))

    def test_call_with_timeout_success(self):
        """Test _call_with_timeout with successful function"""
        func = Mock(return_value="success")

        result = self.handler._call_with_timeout(func, args=("arg1",), timeout_seconds=5)

        self.assertEqual(result, "success")
        func.assert_called_once_with("arg1")


class TestPermissionErrorHandling(unittest.TestCase):
    """Test suite for permission errors and access revocation"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = GitHubSyncHandler()
        self.repo_url = "https://github.com/user/repo"
        self.token = "ghp_token123"

    @patch("requests.get")
    def test_check_repo_access_granted(self, mock_get):
        """Test successful repository access verification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        has_access, reason = self.handler.check_repo_access(
            self.repo_url, self.token
        )

        self.assertTrue(has_access)
        self.assertEqual(reason, "Access granted")

    @patch("requests.get")
    def test_check_repo_access_forbidden(self, mock_get):
        """Test access denied (403 Forbidden)"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with self.assertRaises(PermissionDeniedError):
            self.handler.check_repo_access(self.repo_url, self.token)

    @patch("requests.get")
    def test_check_repo_access_not_found(self, mock_get):
        """Test repository not found (404)"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(RepositoryNotFoundError):
            self.handler.check_repo_access(self.repo_url, self.token)

    def test_check_repo_access_invalid_url(self):
        """Test with invalid GitHub URL"""
        invalid_url = "https://example.com/invalid"

        with self.assertRaises(RepositoryNotFoundError):
            self.handler.check_repo_access(invalid_url, self.token)

    @patch("requests.get")
    def test_check_repo_access_network_error(self, mock_get):
        """Test network error during access check"""
        mock_get.side_effect = Exception("Network error")

        with self.assertRaises(PermissionDeniedError):
            self.handler.check_repo_access(self.repo_url, self.token)

    @patch.object(GitHubSyncHandler, "check_repo_access")
    def test_sync_with_permission_check_success(self, mock_check):
        """Test sync with successful permission check"""
        mock_check.return_value = (True, "Access granted")
        sync_func = Mock(return_value={"status": "synced"})

        result = self.handler.sync_with_permission_check(
            self.repo_url, self.token, sync_func
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["access_verified"])
        sync_func.assert_called_once()

    @patch.object(GitHubSyncHandler, "check_repo_access")
    def test_sync_with_permission_check_denied(self, mock_check):
        """Test sync with permission denied"""
        mock_check.side_effect = PermissionDeniedError("Access denied")

        result = self.handler.sync_with_permission_check(
            self.repo_url, self.token, Mock()
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "permission_denied")
        self.assertFalse(result["access_verified"])

    @patch.object(GitHubSyncHandler, "check_repo_access")
    def test_sync_with_permission_check_repo_not_found(self, mock_check):
        """Test sync with repository not found"""
        mock_check.side_effect = RepositoryNotFoundError("Repo not found")

        result = self.handler.sync_with_permission_check(
            self.repo_url, self.token, Mock()
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "repository_not_found")
        self.assertFalse(result["access_verified"])

    @patch.object(GitHubSyncHandler, "check_repo_access")
    def test_sync_with_permission_check_partial_access(self, mock_check):
        """Test sync when access check returns False but no exception"""
        mock_check.return_value = (False, "Unexpected response: 500")

        result = self.handler.sync_with_permission_check(
            self.repo_url, self.token, Mock()
        )

        self.assertEqual(result["status"], "error")
        self.assertFalse(result["access_verified"])


class TestFactoryFunction(unittest.TestCase):
    """Test suite for factory function"""

    def test_create_github_sync_handler_no_db(self):
        """Test creating handler without database"""
        handler = create_github_sync_handler()

        self.assertIsInstance(handler, GitHubSyncHandler)
        self.assertIsNone(handler.db)

    def test_create_github_sync_handler_with_db(self):
        """Test creating handler with database"""
        mock_db = Mock()
        handler = create_github_sync_handler(db=mock_db)

        self.assertIsInstance(handler, GitHubSyncHandler)
        self.assertEqual(handler.db, mock_db)


class TestExceptionClasses(unittest.TestCase):
    """Test suite for custom exception classes"""

    def test_conflict_resolution_error(self):
        """Test ConflictResolutionError exception"""
        with self.assertRaises(ConflictResolutionError):
            raise ConflictResolutionError("Test error")

    def test_token_expired_error(self):
        """Test TokenExpiredError exception"""
        with self.assertRaises(TokenExpiredError):
            raise TokenExpiredError("Test error")

    def test_permission_denied_error(self):
        """Test PermissionDeniedError exception"""
        with self.assertRaises(PermissionDeniedError):
            raise PermissionDeniedError("Test error")

    def test_repository_not_found_error(self):
        """Test RepositoryNotFoundError exception"""
        with self.assertRaises(RepositoryNotFoundError):
            raise RepositoryNotFoundError("Test error")

    def test_network_sync_failed_error(self):
        """Test NetworkSyncFailedError exception"""
        with self.assertRaises(NetworkSyncFailedError):
            raise NetworkSyncFailedError("Test error")

    def test_file_size_exceeded_error(self):
        """Test FileSizeExceededError exception"""
        with self.assertRaises(FileSizeExceededError):
            raise FileSizeExceededError("Test error")


if __name__ == "__main__":
    unittest.main()
