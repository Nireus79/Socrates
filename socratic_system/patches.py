"""
Runtime patches for library compatibility.

All previously needed patches have been removed as of socratic-agents 0.3.6:
- list_available_providers() now correctly returns List[ProviderMetadata]
- MultiLLMAgent._list_providers() now uses correct attribute names

This module is kept for backwards compatibility but contains no-op patches.
"""

import logging

logger = logging.getLogger(__name__)


def apply_all_patches():
    """No patches needed - all libraries are properly fixed."""
    logger.info("No runtime patches needed (all libraries properly updated)")
