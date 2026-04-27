"""
Client integrations for Socrates AI

This module re-exports clients from socratic-nexus library for backward compatibility.
Direct imports from socratic_nexus.clients are now preferred.
"""

import logging

# Import from socratic-nexus library (PyPI package)
from socratic_nexus.clients import (
    ClaudeClient,
    GoogleClient,
    OllamaClient,
)

# OpenAIClient may not be available in all versions
try:
    from socratic_nexus.clients import OpenAIClient

    __all__ = ["ClaudeClient", "OpenAIClient", "GoogleClient", "OllamaClient"]
except ImportError:
    __all__ = ["ClaudeClient", "GoogleClient", "OllamaClient"]

logger = logging.getLogger("socrates.clients")
logger.info("Client imports sourced from socratic-nexus library")
