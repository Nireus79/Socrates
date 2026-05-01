"""
Password Hashing and Verification using Bcrypt.

Re-exports from socratic_system.auth for backwards compatibility.
The actual implementation is in socratic_system.auth.password since it's
foundational infrastructure used by both CLI and API.
"""

# Re-export from the foundational auth module
from socratic_system.auth import PasswordManager, hash_password, verify_password

__all__ = ["PasswordManager", "hash_password", "verify_password"]
