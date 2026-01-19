"""
Testing Mode Utility

Handles testing mode detection and application for subscription testing.
When testing mode is enabled via the /subscription testing-mode on command,
subscription limits are bypassed for development and testing purposes.
"""

import logging

logger = logging.getLogger(__name__)


class TestingModeChecker:
    """Check and apply testing mode rules"""

    TESTING_MODE_HEADER = "x-testing-mode"

    @staticmethod
    def is_testing_mode_enabled(headers: dict) -> bool:
        """
        Check if testing mode is enabled via request headers.

        Args:
            headers: Request headers dict

        Returns:
            True if testing mode is enabled, False otherwise
        """
        if not headers:
            return False

        testing_mode = headers.get(TestingModeChecker.TESTING_MODE_HEADER, "").lower()
        return testing_mode == "enabled"

    @staticmethod
    def bypass_subscription_check(headers: dict) -> bool:
        """
        Check if subscription check should be bypassed due to testing mode.

        Args:
            headers: Request headers dict

        Returns:
            True if subscription check should be skipped, False otherwise
        """
        return TestingModeChecker.is_testing_mode_enabled(headers)

    @staticmethod
    def get_testing_tier(headers: dict) -> str:
        """
        Get subscription tier for testing mode.

        Args:
            headers: Request headers dict

        Returns:
            "pro" if testing mode enabled, otherwise normal tier determination
        """
        if TestingModeChecker.is_testing_mode_enabled(headers):
            logger.info("Testing mode detected - using pro subscription tier")
            return "pro"
        return "free"


def get_testing_mode_from_request(request) -> bool:
    """
    Extract testing mode status from FastAPI request.

    Args:
        request: FastAPI Request object

    Returns:
        True if testing mode is enabled, False otherwise
    """
    return TestingModeChecker.is_testing_mode_enabled(request.headers)
