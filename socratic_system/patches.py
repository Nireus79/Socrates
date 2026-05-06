"""
Patches for library compatibility (deprecated as of socratic-nexus 0.4.1).

All fixes have been integrated directly into the libraries:
- socratic-nexus 0.4.1: Uses unified PBKDF2-Fernet encryption with random salts
- socratic-agents: Returns ProviderMetadata objects from list_available_providers()
- socratic-agents MultiLLMAgent: Uses correct attribute names on ProviderMetadata

These patches are kept for backward compatibility but are no longer necessary.
"""

import logging

logger = logging.getLogger(__name__)


def apply_all_patches():
    """No patches needed with socratic-nexus 0.4.1+"""
    logger.info("No runtime patches needed with current library versions")
