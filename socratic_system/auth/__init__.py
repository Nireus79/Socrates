"""Authentication utilities for Socratic System.

Provides foundational authentication infrastructure including password hashing
and verification. Used by both CLI and API layers.
"""

from .password import PasswordManager, hash_password, verify_password

__all__ = ["PasswordManager", "hash_password", "verify_password"]
