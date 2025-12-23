"""
Password Hashing and Verification using Bcrypt.

Provides secure password handling with bcrypt, which is resistant to
brute-force attacks and uses salting by default.
"""

import bcrypt


class PasswordManager:
    """Manages password hashing and verification."""

    # Bcrypt cost factor (higher = more secure but slower)
    # Recommended: 12 for production (takes ~250ms per hash)
    BCRYPT_ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password (includes salt)
        """
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=PasswordManager.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

        # Return decoded string for storage in database
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Plain text password to verify
            password_hash: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Encode password and hash for comparison
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except (ValueError, TypeError):
            # Hash is invalid or corrupted
            return False


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return PasswordManager.hash_password(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash."""
    return PasswordManager.verify_password(password, password_hash)
