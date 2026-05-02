"""
Runtime patches to unify encryption across the codebase.

Patches the installed socratic_nexus.clients.claude_client to use
the standard Socrates encryption system.
"""

import logging

logger = logging.getLogger(__name__)


def patch_claude_client_decryption():
    """
    Patch claude_client._decrypt_api_key_from_db to use unified encryption.

    This ensures the installed package uses the same encryption/decryption
    as the local Socrates system.
    """
    try:
        from socratic_nexus.clients.claude_client import ClaudeClient
        from socratic_system.encryption import decrypt_data

        # Save original method for reference
        original_decrypt = ClaudeClient._decrypt_api_key_from_db

        def patched_decrypt(self, encrypted_key: str):
            """Use unified encryption system for decryption"""
            try:
                return decrypt_data(encrypted_key)
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt API key with unified encryption: {e}. "
                    f"Attempting legacy decryption methods..."
                )
                # Fall back to original implementation for backward compatibility
                # (though we've deleted all old databases, this is for safety)
                try:
                    return original_decrypt(self, encrypted_key)
                except Exception as legacy_e:
                    logger.error(
                        f"Both unified and legacy decryption failed for API key. "
                        f"Unified error: {e}, Legacy error: {legacy_e}"
                    )
                    return None

        # Replace the method
        ClaudeClient._decrypt_api_key_from_db = patched_decrypt
        logger.info("Patched ClaudeClient to use unified encryption system")

    except Exception as e:
        logger.error(f"Failed to patch claude_client: {e}")
        raise


def apply_all_patches():
    """Apply all runtime patches"""
    patch_claude_client_decryption()
