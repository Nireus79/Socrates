"""
Unified encryption/decryption for API keys and sensitive data.

Uses PBKDF2-Fernet with random salts for security.
All encrypted data is stored in format: salt_b64:encrypted_b64
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def encrypt_data(data: str, encryption_key: str | None = None) -> str:
    """
    Encrypt data using Fernet symmetric encryption with PBKDF2 key derivation.

    Args:
        data: Raw data string to encrypt
        encryption_key: Encryption key (defaults to SOCRATES_ENCRYPTION_KEY env var)

    Returns:
        Encrypted data in format: salt_b64:encrypted_b64

    Raises:
        RuntimeError: If encryption fails or key not available
    """
    if encryption_key is None:
        encryption_key = os.getenv("SOCRATES_ENCRYPTION_KEY")

    if not encryption_key:
        raise RuntimeError(
            "SOCRATES_ENCRYPTION_KEY environment variable is required for encryption. "
            'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
        )

    try:
        secret_bytes = encryption_key.encode()

        # Use random salt per encryption for better security
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(secret_bytes))

        # Encrypt with Fernet
        cipher = Fernet(derived_key)
        encrypted = cipher.encrypt(data.encode())

        # Include salt in output for decryption (format: salt:encrypted)
        salt_b64 = base64.urlsafe_b64encode(salt).decode()
        encrypted_b64 = encrypted.decode()
        return f"{salt_b64}:{encrypted_b64}"

    except Exception as e:
        raise RuntimeError(f"Failed to encrypt data: {e}") from e


def decrypt_data(encrypted_data: str, encryption_key: str | None = None) -> str:
    """
    Decrypt data using Fernet symmetric encryption.

    Args:
        encrypted_data: Encrypted data in format: salt_b64:encrypted_b64
        encryption_key: Encryption key (defaults to SOCRATES_ENCRYPTION_KEY env var)

    Returns:
        Decrypted data string

    Raises:
        RuntimeError: If decryption fails
    """
    if encryption_key is None:
        encryption_key = os.getenv("SOCRATES_ENCRYPTION_KEY")

    if not encryption_key:
        raise RuntimeError(
            "SOCRATES_ENCRYPTION_KEY environment variable is required for decryption"
        )

    try:
        secret_bytes = encryption_key.encode()

        # New format: salt_b64:encrypted_b64
        if ":" in encrypted_data:
            try:
                salt_b64, encrypted_b64 = encrypted_data.split(":", 1)
                salt = base64.urlsafe_b64decode(salt_b64)

                # Derive key using same parameters as encryption
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend(),
                )
                derived_key = base64.urlsafe_b64encode(kdf.derive(secret_bytes))

                # Decrypt
                cipher = Fernet(derived_key)
                decrypted = cipher.decrypt(encrypted_b64.encode())
                return decrypted.decode()
            except Exception:
                # If new format fails, try old format
                pass

        # Old format: plain Fernet encrypted data (no salt prefix, no PBKDF2)
        # This handles keys encrypted before the salt-based format was introduced
        try:
            # Use a fixed salt of zeros for old-format keys (they were encrypted without PBKDF2)
            # Actually, old format didn't use salt at all - derive key directly from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"\x00" * 16,  # Fixed salt for backward compatibility
                iterations=100000,
                backend=default_backend(),
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(secret_bytes))

            cipher = Fernet(derived_key)
            decrypted = cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception:
            # If both formats fail, raise error
            raise ValueError("Invalid encrypted data format: could not decrypt with either new or old format")

    except Exception as e:
        raise RuntimeError(f"Failed to decrypt data: {e}") from e
