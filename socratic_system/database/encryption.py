"""
Database Encryption Module - Field-level encryption for sensitive data.

Provides transparent encryption/decryption for sensitive database fields using
the cryptography library's Fernet symmetric encryption.

Features:
- Field-level encryption for user emails, passwords, API keys
- Automatic encryption on save, decryption on load
- Key derivation from environment variable or master key
- Graceful fallback for non-encrypted data
- Performance optimized with lazy loading
"""

import base64
import hashlib
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Global encryption configuration
encryption_config = {
    "enabled": False,  # Off by default in v1.6.0, required in v2.0.0
    "key": None,
    "fields": ["email", "passcode_hash", "encrypted_key"],
}


def initialize_encryption(enabled: bool = False, key: Optional[str] = None) -> bool:
    """
    Initialize database encryption.

    Args:
        enabled: Enable database encryption
        key: Master encryption key (Fernet format or base string to derive from)

    Returns:
        True if encryption initialized successfully, False otherwise
    """
    encryption_config["enabled"] = enabled

    if not enabled:
        logger.info("Database encryption disabled")
        return True

    # Get key from parameter or environment
    encryption_key = key or os.getenv("DATABASE_ENCRYPTION_KEY")

    if not encryption_key:
        logger.warning(
            "DATABASE_ENCRYPTION_KEY not set. Database encryption disabled. "
            "Set DATABASE_ENCRYPTION_KEY environment variable to enable."
        )
        encryption_config["enabled"] = False
        return False

    try:
        # If key looks like a Fernet key (starts with 'gAAAAAB'), use it directly
        if encryption_key.startswith("gAAAAAB"):
            encryption_config["key"] = encryption_key.encode()
        else:
            # Otherwise, derive a key from the provided string
            # Use SHA256 for key derivation, then pad to Fernet key size
            derived = hashlib.sha256(encryption_key.encode()).digest()
            encryption_config["key"] = base64.urlsafe_b64encode(derived)

        # Test that key works
        cipher = Fernet(encryption_config["key"])
        test_data = b"test"
        encrypted = cipher.encrypt(test_data)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == test_data

        logger.info("Database encryption initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database encryption: {e}")
        encryption_config["enabled"] = False
        return False


def encrypt_field(value: Optional[str], field_name: str = "generic") -> Optional[str]:
    """
    Encrypt a single field value.

    Args:
        value: Value to encrypt
        field_name: Name of field (for logging)

    Returns:
        Encrypted value (as string) or original value if encryption disabled
    """
    if not value or not encryption_config["enabled"] or not encryption_config["key"]:
        return value

    try:
        cipher = Fernet(encryption_config["key"])
        encrypted = cipher.encrypt(value.encode())
        # Return as string prefixed with "enc:" to indicate it's encrypted
        return f"enc:{encrypted.decode()}"
    except Exception as e:
        logger.error(f"Failed to encrypt {field_name}: {e}")
        return value


def decrypt_field(value: Optional[str], field_name: str = "generic") -> Optional[str]:
    """
    Decrypt a single field value.

    Args:
        value: Encrypted value (or original if not encrypted)
        field_name: Name of field (for logging)

    Returns:
        Decrypted value or original if not encrypted or encryption disabled
    """
    if not value:
        return value

    # Check if value is encrypted (starts with "enc:")
    if not isinstance(value, str) or not value.startswith("enc:"):
        return value  # Not encrypted, return as-is

    if not encryption_config["enabled"] or not encryption_config["key"]:
        # Encrypted data but encryption is disabled - can't decrypt
        logger.warning(f"Found encrypted {field_name} but encryption is disabled")
        return value

    try:
        cipher = Fernet(encryption_config["key"])
        encrypted_part = value[4:]  # Remove "enc:" prefix
        decrypted = cipher.decrypt(encrypted_part.encode())
        return decrypted.decode()
    except (InvalidToken, Exception) as e:
        logger.error(f"Failed to decrypt {field_name}: {e}")
        return value  # Return encrypted value if decryption fails


def should_encrypt_field(field_name: str) -> bool:
    """
    Determine if a field should be encrypted.

    Args:
        field_name: Name of field

    Returns:
        True if field should be encrypted
    """
    return encryption_config["enabled"] and field_name in encryption_config["fields"]


class DatabaseEncryptionWrapper:
    """
    Wrapper for transparent field-level encryption in database operations.

    Usage:
        ```python
        wrapper = DatabaseEncryptionWrapper(["email", "passcode_hash"])
        encrypted_user = wrapper.encrypt_row(user_dict)
        decrypted_user = wrapper.decrypt_row(encrypted_user)
        ```
    """

    def __init__(self, sensitive_fields: list[str] = None):
        """
        Initialize encryption wrapper.

        Args:
            sensitive_fields: List of field names to encrypt
        """
        self.sensitive_fields = sensitive_fields or ["email", "passcode_hash", "encrypted_key"]

    def encrypt_row(self, row: dict) -> dict:
        """
        Encrypt sensitive fields in a row.

        Args:
            row: Dictionary with field data

        Returns:
            Dictionary with sensitive fields encrypted
        """
        if not encryption_config["enabled"]:
            return row

        encrypted = row.copy()
        for field in self.sensitive_fields:
            if field in encrypted and encrypted[field]:
                encrypted[field] = encrypt_field(encrypted[field], field)
        return encrypted

    def decrypt_row(self, row: dict) -> dict:
        """
        Decrypt sensitive fields in a row.

        Args:
            row: Dictionary with encrypted field data

        Returns:
            Dictionary with sensitive fields decrypted
        """
        if not encryption_config["enabled"]:
            return row

        decrypted = row.copy()
        for field in self.sensitive_fields:
            if field in decrypted and decrypted[field]:
                decrypted[field] = decrypt_field(decrypted[field], field)
        return decrypted
