"""
Centralized ID generation for all entity types.

This module restores the pattern from the monolithic system that was removed
during the monorepo migration. It's essential for:
- Consistency across entity types
- Auditability and debugging
- Testability (can mock the generator)
- Future flexibility (easily switch to ULID, nanoid, etc.)

ID Format Convention:
    {prefix}_{random_hex}
    Examples: proj_abc123def456, user_xyz789, sess_ab12

This follows Stripe/Anthropic conventions for readability in logs and APIs.
"""

import uuid
from typing import Final


class IDGenerator:
    """Generate consistent, prefixed IDs for all entity types."""

    # ID prefixes for different entity types
    PROJECT_PREFIX: Final[str] = "proj"
    USER_PREFIX: Final[str] = "user"
    SESSION_PREFIX: Final[str] = "sess"
    MESSAGE_PREFIX: Final[str] = "msg"
    SKILL_PREFIX: Final[str] = "skill"
    NOTE_PREFIX: Final[str] = "note"
    INTERACTION_PREFIX: Final[str] = "int"
    DOCUMENT_PREFIX: Final[str] = "doc"
    TOKEN_PREFIX: Final[str] = "tok"
    ACTIVITY_PREFIX: Final[str] = "act"
    INVITATION_PREFIX: Final[str] = "inv"

    @staticmethod
    def generate_id(prefix: str, length: int = 12) -> str:
        """
        Generate a prefixed, randomly-unique ID.

        Args:
            prefix: Entity type prefix (e.g., 'proj', 'user')
            length: Length of hex suffix (default: 12 chars = 48 bits of entropy)

        Returns:
            Formatted ID string (e.g., 'proj_abc123def456')

        Raises:
            ValueError: If prefix is empty

        Examples:
            >>> id = IDGenerator.generate_id('proj')
            >>> id.startswith('proj_')
            True
            >>> len(id)
            17  # 5 chars prefix + 1 underscore + 12 hex chars
        """
        if not prefix:
            raise ValueError("Prefix cannot be empty")

        if not isinstance(prefix, str):
            raise TypeError(f"Prefix must be string, got {type(prefix)}")

        # Use hex for readability (compact vs full UUID with hyphens)
        # UUID4 provides 122 bits of randomness, we use first 48 bits (12 hex chars)
        suffix = uuid.uuid4().hex[:length]
        return f"{prefix}_{suffix}"

    @staticmethod
    def project() -> str:
        """
        Generate a unique project ID.

        Returns:
            Project ID (format: proj_XXXXXXXXXXXX)

        Example:
            >>> project_id = IDGenerator.project()
            >>> project_id.startswith('proj_')
            True
        """
        return IDGenerator.generate_id(IDGenerator.PROJECT_PREFIX)

    @staticmethod
    def user() -> str:
        """
        Generate a unique user ID.

        Returns:
            User ID (format: user_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.USER_PREFIX)

    @staticmethod
    def session() -> str:
        """
        Generate a unique session ID.

        Uses shorter suffix (8 chars) for readability in session management.

        Returns:
            Session ID (format: sess_XXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.SESSION_PREFIX, length=8)

    @staticmethod
    def message() -> str:
        """
        Generate a unique message ID.

        Returns:
            Message ID (format: msg_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.MESSAGE_PREFIX)

    @staticmethod
    def skill() -> str:
        """
        Generate a unique skill ID.

        Returns:
            Skill ID (format: skill_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.SKILL_PREFIX)

    @staticmethod
    def note() -> str:
        """
        Generate a unique note ID.

        Returns:
            Note ID (format: note_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.NOTE_PREFIX)

    @staticmethod
    def interaction() -> str:
        """
        Generate a unique interaction ID.

        Used for tracking user interactions with the system.

        Returns:
            Interaction ID (format: int_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.INTERACTION_PREFIX)

    @staticmethod
    def document() -> str:
        """
        Generate a unique document ID.

        Returns:
            Document ID (format: doc_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.DOCUMENT_PREFIX)

    @staticmethod
    def token() -> str:
        """
        Generate a unique token ID.

        Returns:
            Token ID (format: tok_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.TOKEN_PREFIX)

    @staticmethod
    def activity() -> str:
        """
        Generate a unique activity ID.

        Used for tracking project activities.

        Returns:
            Activity ID (format: act_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.ACTIVITY_PREFIX)

    @staticmethod
    def invitation() -> str:
        """
        Generate a unique invitation ID.

        Used for project collaboration invitations.

        Returns:
            Invitation ID (format: inv_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.INVITATION_PREFIX)

    @staticmethod
    def question() -> str:
        """
        Generate a unique question ID.

        Used for tracking generated questions in the Socratic method.

        Returns:
            Question ID (format: msg_XXXXXXXXXXXX)
        """
        return IDGenerator.generate_id(IDGenerator.MESSAGE_PREFIX)

    # Backward compatibility wrapper for monolithic system imports
    class ProjectIDGenerator:
        """
        Compatibility wrapper for monolithic system code.

        The monolithic system used socratic_core.utils.ProjectIDGenerator.
        This wrapper allows old code patterns to work with the new system.

        Example:
            >>> # Old monolithic pattern
            >>> id = IDGenerator.ProjectIDGenerator.generate()
            >>> id.startswith('proj_')
            True
        """

        @staticmethod
        def generate() -> str:
            """
            Generate a project ID (backward compatible).

            This method provides compatibility with code that was written
            for the monolithic system's ProjectIDGenerator pattern.

            Returns:
                Project ID (format: proj_XXXXXXXXXXXX)
            """
            return IDGenerator.project()
