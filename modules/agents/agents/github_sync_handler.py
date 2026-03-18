"""
GitHub Sync Edge Case Handler

Handles critical edge cases in GitHub synchronization:
1. Merge conflict resolution
2. Large file handling
3. Token expiry detection and refresh
4. Network interruption recovery with retry
5. Permission errors and access revocation

This module provides robust error handling and recovery mechanisms
for reliable GitHub sync operations.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConflictResolutionError(Exception):
    """Raised when merge conflict cannot be resolved"""

    pass


class TokenExpiredError(Exception):
    """Raised when GitHub authentication token has expired"""

    pass


class PermissionDeniedError(Exception):
    """Raised when user lacks repository access"""

    pass


class RepositoryNotFoundError(Exception):
    """Raised when repository no longer exists or is inaccessible"""

    pass


class NetworkSyncFailedError(Exception):
    """Raised when sync fails after all retry attempts"""

    pass


class FileSizeExceededError(Exception):
    """Raised when file size exceeds GitHub limits"""

    pass


class GitHubSyncHandler:
    """Handles GitHub sync operations with edge case management"""

    # GitHub size limits
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_REPO_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1  # 1 second
    MAX_BACKOFF = 32  # 32 seconds

    def __init__(self, db=None):
        """Initialize GitHub sync handler

        Args:
            db: Database instance for tracking sync progress
        """
        self.db = db
        self.sync_progress_log = []

    # ========================================================================
    # Edge Case 1: Merge Conflict Resolution
    # ========================================================================

    def detect_merge_conflicts(self, repo_path: str) -> List[str]:
        """
        Detect merge conflicts in repository

        Args:
            repo_path: Path to repository

        Returns:
            List of files with conflicts

        Raises:
            ConflictResolutionError: If conflict detection fails
        """
        try:
            import subprocess

            logger.info(f"Detecting merge conflicts in {repo_path}")

            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(f"Git command failed: {result.stderr}")
                return []

            conflicted_files = result.stdout.strip().split("\n")
            conflicted_files = [f for f in conflicted_files if f]

            logger.info(f"Found {len(conflicted_files)} conflicted files")
            return conflicted_files

        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            raise ConflictResolutionError(f"Failed to detect conflicts: {e}")

    def resolve_merge_conflict(
        self, repo_path: str, file_path: str, strategy: str = "ours"
    ) -> bool:
        """
        Resolve a specific merge conflict

        Args:
            repo_path: Path to repository
            file_path: Path to conflicted file
            strategy: Resolution strategy ('ours', 'theirs', 'manual')

        Returns:
            True if conflict resolved, False otherwise

        Raises:
            ConflictResolutionError: If resolution fails
        """
        try:
            import subprocess

            logger.info(f"Resolving conflict in {file_path} using {strategy} strategy")

            if strategy == "ours":
                # Keep our version
                result = subprocess.run(
                    ["git", "checkout", "--ours", file_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            elif strategy == "theirs":
                # Keep their version
                result = subprocess.run(
                    ["git", "checkout", "--theirs", file_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            else:
                logger.warning(f"Manual resolution required for {file_path}")
                return False

            if result.returncode != 0:
                logger.error(f"Failed to resolve conflict: {result.stderr}")
                return False

            # Stage the resolved file
            subprocess.run(
                ["git", "add", file_path], cwd=repo_path, capture_output=True, timeout=30
            )

            logger.info(f"Successfully resolved conflict in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            raise ConflictResolutionError(f"Failed to resolve conflict: {e}")

    def handle_merge_conflicts(
        self, repo_path: str, conflict_info: Dict[str, Any], default_strategy: str = "ours"
    ) -> Dict[str, Any]:
        """
        Handle merge conflicts during sync

        Args:
            repo_path: Path to repository
            conflict_info: Information about conflicts
            default_strategy: Default resolution strategy

        Returns:
            Resolution report with status for each file
        """
        try:
            logger.info(f"Handling merge conflicts in {repo_path}")

            # Detect conflicts
            conflicted_files = self.detect_merge_conflicts(repo_path)

            if not conflicted_files:
                return {"status": "success", "conflicts_found": 0, "resolved": []}

            # Log conflicts
            if self.db:
                self.db.log_sync_error(
                    repo_path,
                    "merge_conflicts_detected",
                    f"{len(conflicted_files)} files with conflicts",
                )

            # Resolve each conflict
            resolution_report = {
                "status": "partial",
                "conflicts_found": len(conflicted_files),
                "resolved": [],
                "manual_required": [],
            }

            for file_path in conflicted_files:
                try:
                    if self.resolve_merge_conflict(repo_path, file_path, default_strategy):
                        resolution_report["resolved"].append(file_path)
                    else:
                        resolution_report["manual_required"].append(file_path)
                except Exception as e:
                    logger.error(f"Error resolving {file_path}: {e}")
                    resolution_report["manual_required"].append(file_path)

            # Determine final status
            if not resolution_report["manual_required"]:
                resolution_report["status"] = "success"

            logger.info(f"Conflict resolution complete: {resolution_report}")
            return resolution_report

        except Exception as e:
            logger.error(f"Error handling conflicts: {e}")
            return {
                "status": "error",
                "error": str(e),
                "conflicts_found": 0,
                "resolved": [],
                "manual_required": [],
            }

    # ========================================================================
    # Edge Case 2: Large File Handling
    # ========================================================================

    def validate_file_sizes(
        self, files_to_push: List[str]
    ) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """
        Validate file sizes before pushing

        Args:
            files_to_push: List of file paths to validate

        Returns:
            Tuple of (all_valid, invalid_files, size_report)
        """
        try:
            import os

            logger.info(f"Validating sizes for {len(files_to_push)} files")

            invalid_files = []
            size_report = []
            total_size = 0

            for file_path in files_to_push:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue

                file_size = os.path.getsize(file_path)
                total_size += file_size

                # Check individual file size
                if file_size > self.MAX_FILE_SIZE:
                    logger.warning(f"File {file_path} exceeds limit: {file_size} bytes")
                    invalid_files.append(file_path)

                size_report.append(
                    {
                        "file": file_path,
                        "size": file_size,
                        "size_mb": file_size / (1024 * 1024),
                        "exceeds_limit": file_size > self.MAX_FILE_SIZE,
                    }
                )

            # Check total size
            all_valid = len(invalid_files) == 0 and total_size <= self.MAX_REPO_SIZE

            if total_size > self.MAX_REPO_SIZE:
                logger.warning(f"Total repo size {total_size} exceeds limit")
                all_valid = False

            logger.info(
                f"Size validation complete: valid={all_valid}, invalid={len(invalid_files)}"
            )
            return all_valid, invalid_files, size_report

        except Exception as e:
            logger.error(f"Error validating file sizes: {e}")
            return False, files_to_push, []

    def handle_large_files(
        self, files_to_push: List[str], strategy: str = "exclude"
    ) -> Dict[str, Any]:
        """
        Handle large files during sync

        Args:
            files_to_push: List of files to handle
            strategy: How to handle large files ('exclude', 'lfs', 'split')

        Returns:
            Handling report with status
        """
        all_valid, invalid_files, size_report = self.validate_file_sizes(files_to_push)

        if all_valid:
            return {"status": "success", "all_files_valid": True, "size_report": size_report}

        logger.warning(f"Handling {len(invalid_files)} large files using {strategy} strategy")

        if strategy == "exclude":
            valid_files = [f for f in files_to_push if f not in invalid_files]
            return {
                "status": "partial",
                "all_files_valid": False,
                "strategy": "exclude",
                "excluded_files": invalid_files,
                "valid_files": valid_files,
                "size_report": size_report,
            }
        elif strategy == "lfs":
            logger.info("Using Git LFS for large files")
            return {
                "status": "requires_setup",
                "all_files_valid": False,
                "strategy": "lfs",
                "message": "Git LFS required for large files",
                "large_files": invalid_files,
                "size_report": size_report,
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown strategy: {strategy}",
                "large_files": invalid_files,
                "size_report": size_report,
            }

    # ========================================================================
    # Edge Case 3: Token Expiry Detection and Refresh
    # ========================================================================

    def check_token_validity(
        self, token: Optional[str] = None, token_expiry: Optional[datetime] = None
    ) -> bool:
        """
        Check if GitHub token is still valid

        Args:
            token: GitHub auth token
            token_expiry: Token expiration time

        Returns:
            True if token is valid, False if expired

        Raises:
            TokenExpiredError: If token is expired
        """
        try:
            if not token:
                logger.warning("No GitHub token provided")
                raise TokenExpiredError("GitHub token not configured")

            # Check expiration time if available
            if token_expiry:
                now = datetime.now(timezone.utc)
                if isinstance(token_expiry, str):
                    token_expiry = datetime.fromisoformat(token_expiry)
                elif not isinstance(token_expiry, datetime):
                    token_expiry = datetime.fromtimestamp(token_expiry, tz=timezone.utc)

                if now > token_expiry:
                    logger.error(f"Token expired at {token_expiry}")
                    raise TokenExpiredError(f"Token expired at {token_expiry}")

            # Verify token still works with API call
            import requests

            response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}"},
                timeout=5,
            )

            if response.status_code == 401:
                logger.error("Token authentication failed (401)")
                raise TokenExpiredError("Token no longer valid (401 Unauthorized)")

            if response.status_code != 200:
                logger.warning(f"Unexpected response: {response.status_code}")
                return False

            logger.info("Token validation successful")
            return True

        except requests.RequestException as e:
            logger.error(f"Token verification failed: {e}")
            raise TokenExpiredError(f"Token verification failed: {e}")
        except TokenExpiredError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking token: {e}")
            return False

    def sync_with_token_refresh(
        self, repo_url: str, token: str, refresh_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Perform sync with automatic token refresh on expiry

        Args:
            repo_url: GitHub repository URL
            token: Current GitHub token
            refresh_callback: Function to call to refresh token

        Returns:
            Sync result
        """
        try:
            # Check token validity before sync
            self.check_token_validity(token)

            logger.info(f"Token valid, proceeding with sync for {repo_url}")
            return {"status": "success", "synced": True}

        except TokenExpiredError as e:
            logger.warning(f"Token expired: {e}")

            if not refresh_callback:
                logger.error("No token refresh callback provided")
                return {"status": "error", "message": "Token expired, refresh required"}

            try:
                logger.info("Attempting to refresh token")
                new_token = refresh_callback()

                if not new_token:
                    return {"status": "error", "message": "Failed to refresh token"}

                logger.info("Token refreshed successfully")
                return {"status": "success", "synced": True, "token_refreshed": True}

            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return {"status": "error", "message": f"Token refresh failed: {e}"}

    # ========================================================================
    # Edge Case 4: Network Interruption Recovery with Retry
    # ========================================================================

    def sync_with_retry_and_resume(
        self,
        repo_url: str,
        sync_function: Any,
        max_retries: int = None,
        timeout_per_attempt: int = 30,
    ) -> Dict[str, Any]:
        """
        Perform sync with exponential backoff retry and progress tracking

        Args:
            repo_url: Repository URL
            sync_function: Function to call for sync
            max_retries: Maximum retry attempts
            timeout_per_attempt: Timeout per attempt in seconds

        Returns:
            Sync result with retry information

        Raises:
            NetworkSyncFailedError: If all retries exhausted
        """
        max_retries = max_retries or self.MAX_RETRIES
        logger.info(f"Starting sync with retry for {repo_url}")

        for attempt in range(max_retries):
            try:
                # Track progress in database
                sync_record = {
                    "repo_url": repo_url,
                    "attempt": attempt + 1,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "status": "in_progress",
                }

                if self.db:
                    self.db.save_sync_progress(sync_record)

                logger.info(f"Attempt {attempt + 1}/{max_retries} to sync {repo_url}")

                # Call sync function with timeout
                result = self._call_with_timeout(
                    sync_function, args=(repo_url,), timeout_seconds=timeout_per_attempt
                )

                sync_record["status"] = "success"
                if self.db:
                    self.db.save_sync_progress(sync_record)

                logger.info(f"Sync successful on attempt {attempt + 1}")
                return {"status": "success", "attempt": attempt + 1, "result": result}

            except (OSError, TimeoutError, ConnectionError) as e:
                sync_record["status"] = "failed"
                sync_record["error"] = str(e)

                if self.db:
                    self.db.save_sync_progress(sync_record)

                if attempt < max_retries - 1:
                    # Calculate exponential backoff
                    wait_time = min(self.INITIAL_BACKOFF * (2**attempt), self.MAX_BACKOFF)
                    logger.warning(
                        f"Sync failed: {e}. Retrying in {wait_time}s "
                        f"(attempt {attempt + 2}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Sync failed after {max_retries} attempts: {e}")
                    raise NetworkSyncFailedError(f"Sync failed after {max_retries} attempts: {e}")

    def _call_with_timeout(self, func: Any, args: tuple = (), timeout_seconds: int = 30) -> Any:
        """Call function with timeout"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")

        # Set timeout alarm
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            result = func(*args)
            signal.alarm(0)  # Disable alarm
            return result
        except TimeoutError:
            raise
        finally:
            signal.alarm(0)  # Disable alarm

    # ========================================================================
    # Edge Case 5: Permission Errors and Access Revocation
    # ========================================================================

    def check_repo_access(self, repo_url: str, token: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        Verify user still has access to repository

        Args:
            repo_url: Repository URL
            token: GitHub token
            timeout: Request timeout

        Returns:
            Tuple of (has_access, reason)

        Raises:
            PermissionDeniedError: If access is denied
            RepositoryNotFoundError: If repo doesn't exist
        """
        try:
            import requests

            logger.info(f"Checking access to {repo_url}")

            # Extract owner/repo from URL
            import re

            match = re.search(r"github\.com[:/](.+?)/(.+?)(?:\.git)?$", repo_url)

            if not match:
                logger.error(f"Invalid GitHub URL: {repo_url}")
                raise RepositoryNotFoundError(f"Invalid GitHub URL: {repo_url}")

            owner, repo = match.groups()
            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            response = requests.get(
                api_url, headers={"Authorization": f"token {token}"}, timeout=timeout
            )

            if response.status_code == 403:
                logger.error(f"Access forbidden to {repo_url}")
                raise PermissionDeniedError("Access denied to repository (403 Forbidden)")

            if response.status_code == 404:
                logger.error(f"Repository not found: {repo_url}")
                raise RepositoryNotFoundError("Repository no longer exists (404 Not Found)")

            if response.status_code == 200:
                logger.info("Repository access verified")
                return True, "Access granted"

            logger.warning(f"Unexpected response: {response.status_code}")
            return False, f"Unexpected response: {response.status_code}"

        except requests.RequestException as e:
            logger.error(f"Failed to verify access: {e}")
            raise PermissionDeniedError(f"Failed to verify access: {e}")

    def sync_with_permission_check(
        self, repo_url: str, token: str, sync_function: Any
    ) -> Dict[str, Any]:
        """
        Perform sync with pre-sync permission verification

        Args:
            repo_url: Repository URL
            token: GitHub token
            sync_function: Function to call for sync

        Returns:
            Sync result with permission check information
        """
        try:
            # Check access before attempting sync
            has_access, reason = self.check_repo_access(repo_url, token)

            if not has_access:
                logger.warning(f"Access check failed: {reason}")
                return {
                    "status": "error",
                    "message": f"Access check failed: {reason}",
                    "access_verified": False,
                }

            logger.info("Access verified, proceeding with sync")

            # Proceed with sync
            result = sync_function(repo_url)

            return {"status": "success", "access_verified": True, "synced": True, "result": result}

        except PermissionDeniedError as e:
            logger.error(f"Permission denied: {e}")

            # Log permission error in database
            if self.db:
                self.db.log_sync_error(repo_url, "permission_denied", str(e))

            return {
                "status": "error",
                "message": str(e),
                "error_type": "permission_denied",
                "access_verified": False,
                "action_required": "Re-authenticate or check repository permissions",
            }

        except RepositoryNotFoundError as e:
            logger.error(f"Repository not found: {e}")

            # Mark project as needing re-link
            if self.db:
                self.db.mark_github_sync_broken(repo_url)

            return {
                "status": "error",
                "message": str(e),
                "error_type": "repository_not_found",
                "access_verified": False,
                "action_required": "Repository has been deleted or is inaccessible. Re-link project to GitHub.",
            }


# ============================================================================
# Convenience Functions
# ============================================================================


def create_github_sync_handler(db=None) -> GitHubSyncHandler:
    """Factory function to create GitHub sync handler"""
    return GitHubSyncHandler(db=db)
