"""
Unified ID generation for Socrates system

Ensures both CLI and API generate consistent identifiers.
Used by project_manager agent, API endpoints, and any other components.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional


class ProjectIDGenerator:
    """Unified project ID generation for CLI + API consistency"""

    FORMAT = "uuid"  # Can be changed to "timestamp" if needed
    # Available formats:
    # - "uuid": Pure UUID format (recommended for simplicity)
    # - "timestamp": Owner-prefixed timestamp format for sortability

    @classmethod
    def generate(cls, owner: Optional[str] = None) -> str:
        """
        Generate a project ID consistently across all systems.

        Args:
            owner: Optional project owner username (used in timestamp format only)

        Returns:
            str: Generated project ID in consistent format

        Examples:
            >>> project_id = ProjectIDGenerator.generate("alice")
            >>> project_id.startswith("proj_")
            True
        """
        if cls.FORMAT == "uuid":
            return cls._generate_uuid()
        elif cls.FORMAT == "timestamp":
            return cls._generate_timestamp(owner)
        else:
            raise ValueError(f"Unknown format: {cls.FORMAT}")

    @staticmethod
    def _generate_uuid() -> str:
        """Generate UUID-based project ID"""
        return f"proj_{str(uuid.uuid4())}"

    @staticmethod
    def _generate_timestamp(owner: Optional[str] = None) -> str:
        """Generate timestamp-based project ID"""
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        if owner:
            return f"proj_{owner}_{timestamp}"
        return f"proj_{timestamp}"


class UserIDGenerator:
    """Unified user ID generation"""

    @staticmethod
    def generate(username: Optional[str] = None) -> str:
        """
        Generate a user ID consistently.

        Args:
            username: Optional username (used if provided)

        Returns:
            str: User ID
        """
        if username:
            return username
        return f"user_{str(uuid.uuid4())}"
