"""
GitHub API client for Socrates.

Handles authentication and API calls to GitHub for:
- Verifying GitHub Personal Access Tokens
- Checking user sponsorships
- Getting user profile information
- Accessing private repository information
"""

import logging
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""

    pass


class GitHubAuthError(GitHubClientError):
    """Raised when authentication fails."""

    pass


class GitHubAPIError(GitHubClientError):
    """Raised when GitHub API returns an error."""

    pass


class GitHubClient:
    """Client for interacting with GitHub API."""

    BASE_URL = "https://api.github.com"
    TIMEOUT = 10  # seconds

    def __init__(self, token: str):
        """
        Initialize GitHub client.

        Args:
            token: GitHub Personal Access Token

        Raises:
            ValueError: If token is empty
        """
        if not token or not isinstance(token, str):
            raise ValueError("GitHub token must be a non-empty string")

        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        if requests is None:
            raise ImportError("requests library is required. Install with: pip install requests")

    def verify_token(self) -> bool:
        """
        Verify that the GitHub token is valid.

        Makes a simple API call to /user to test authentication.

        Returns:
            True if token is valid, False otherwise

        Raises:
            GitHubClientError: If API call fails for unexpected reasons
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user", headers=self.headers, timeout=self.TIMEOUT
            )

            if response.status_code == 401:
                logger.warning("GitHub token verification failed: Invalid or expired token")
                return False

            if response.status_code == 200:
                logger.debug("GitHub token verified successfully")
                return True

            logger.error(f"GitHub token verification failed with status {response.status_code}")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error during token verification: {e}")
            raise GitHubClientError(f"Failed to verify GitHub token: {e}") from e

    def get_user_info(self) -> dict[str, Any]:
        """
        Get authenticated user's GitHub profile information.

        Returns:
            Dictionary with user info including: login, id, name, email, public_repos, etc.

        Raises:
            GitHubAuthError: If token is invalid
            GitHubAPIError: If API call fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user", headers=self.headers, timeout=self.TIMEOUT
            )

            if response.status_code == 401:
                raise GitHubAuthError("GitHub token is invalid or expired")

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get user info: {response.status_code} {response.text}"
                )

            user_info = response.json()
            logger.debug(f"Retrieved GitHub user info for: {user_info.get('login')}")
            return user_info

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error fetching user info: {e}")
            raise GitHubAPIError(f"Failed to fetch user info: {e}") from e

    def get_token_scopes(self) -> list[str]:
        """
        Get OAuth scopes for the current token from response headers.

        Returns:
            List of scopes the token has (e.g., ['user', 'repo', 'gist'])

        Raises:
            GitHubAPIError: If API call fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user", headers=self.headers, timeout=self.TIMEOUT
            )

            if response.status_code != 200:
                raise GitHubAPIError(f"Failed to get token scopes: {response.status_code}")

            # GitHub returns scopes in X-OAuth-Scopes header (comma-separated)
            scopes_header = response.headers.get("X-OAuth-Scopes", "")
            scopes = [scope.strip() for scope in scopes_header.split(",") if scope.strip()]

            logger.debug(f"GitHub token scopes: {scopes}")
            return scopes

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error fetching scopes: {e}")
            raise GitHubAPIError(f"Failed to fetch token scopes: {e}") from e

    def check_active_sponsorships(self) -> list[dict[str, Any]]:
        """
        Get list of all active sponsorships by the authenticated user.

        Returns:
            List of sponsorships with maintainer info, tier, amount, and expiry

        Raises:
            GitHubAuthError: If token is invalid
            GitHubAPIError: If API call fails
        """
        try:
            # Note: /user/sponsorships endpoint may return empty if no sponsorships
            # This is not an error - it just means user isn't sponsoring anyone
            response = requests.get(
                f"{self.BASE_URL}/user/sponsorships",
                headers=self.headers,
                timeout=self.TIMEOUT,
            )

            if response.status_code == 401:
                raise GitHubAuthError("GitHub token is invalid or expired")

            if response.status_code == 404:
                logger.info("GitHub Sponsors API not available or endpoint not found")
                return []

            if response.status_code != 200:
                logger.warning(f"Unexpected status getting sponsorships: {response.status_code}")
                return []

            sponsorships = response.json()

            if not isinstance(sponsorships, list):
                logger.error(f"Expected list of sponsorships, got: {type(sponsorships)}")
                return []

            logger.debug(f"Found {len(sponsorships)} active sponsorships")
            return sponsorships

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error fetching sponsorships: {e}")
            raise GitHubAPIError(f"Failed to fetch sponsorships: {e}") from e

    def get_sponsorship_status(self, maintainer_username: str) -> dict[str, Any] | None:
        """
        Check if authenticated user is sponsoring a specific maintainer.

        Args:
            maintainer_username: GitHub username of the maintainer (e.g., "Nireus79")

        Returns:
            Sponsorship info if user sponsors maintainer, None otherwise

        Raises:
            GitHubAuthError: If token is invalid
            GitHubAPIError: If API call fails
        """
        try:
            sponsorships = self.check_active_sponsorships()

            # Find sponsorship matching maintainer
            for sponsorship in sponsorships:
                maintainer = sponsorship.get("maintainer", {})
                if maintainer.get("login") == maintainer_username:
                    logger.debug(f"Found active sponsorship for {maintainer_username}")
                    return sponsorship

            logger.debug(f"No active sponsorship found for {maintainer_username}")
            return None

        except GitHubAPIError:
            raise
        except GitHubAuthError:
            raise
        except Exception as e:
            logger.error(f"Error checking sponsorship status: {e}")
            raise GitHubAPIError(f"Failed to check sponsorship status: {e}") from e

    def get_user_repos(self, repo_type: str = "all") -> list[dict[str, Any]]:
        """
        Get list of repositories accessible by the authenticated user.

        Args:
            repo_type: Type of repos to return: "all", "owner", "public", "private"

        Returns:
            List of repository info

        Raises:
            GitHubAuthError: If token is invalid
            GitHubAPIError: If API call fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user/repos",
                headers=self.headers,
                params={"type": repo_type, "per_page": 100},
                timeout=self.TIMEOUT,
            )

            if response.status_code == 401:
                raise GitHubAuthError("GitHub token is invalid or expired")

            if response.status_code != 200:
                raise GitHubAPIError(f"Failed to get repos: {response.status_code} {response.text}")

            repos = response.json()
            logger.debug(f"Retrieved {len(repos)} repositories of type '{repo_type}'")
            return repos

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error fetching repos: {e}")
            raise GitHubAPIError(f"Failed to fetch repositories: {e}") from e

    def check_repo_access(self, repo_owner: str, repo_name: str) -> bool:
        """
        Check if authenticated user has read access to a repository.

        Args:
            repo_owner: Repository owner's GitHub username
            repo_name: Repository name

        Returns:
            True if user has access, False otherwise

        Raises:
            GitHubAPIError: If API call fails
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}",
                headers=self.headers,
                timeout=self.TIMEOUT,
            )

            if response.status_code == 200:
                logger.debug(f"User has access to {repo_owner}/{repo_name}")
                return True

            if response.status_code == 404:
                logger.debug(f"User does not have access to {repo_owner}/{repo_name}")
                return False

            logger.error(f"Error checking repo access: {response.status_code} {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error checking repo access: {e}")
            return False
