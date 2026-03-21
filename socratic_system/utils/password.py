"""
Password utility functions for hashing and verification.

Uses bcrypt for secure password handling. This module is used by both the CLI
and API to ensure consistent password hashing across the system.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string (includes salt)
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    if not password:
        raise ValueError("Password cannot be empty")

    # bcrypt returns bytes, decode to string for storage
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Args:
        password: Plain text password to verify
        hashed: Bcrypt hash to check against

    Returns:
        True if password matches hash, False otherwise
    """
    if not isinstance(password, str) or not isinstance(hashed, str):
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        # Invalid hash format or other bcrypt error
        return False
