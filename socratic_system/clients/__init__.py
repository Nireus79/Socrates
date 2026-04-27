"""
Client integrations for Socrates AI

This module re-exports clients from socratic-nexus library for backward compatibility.
Direct imports from socratic_nexus.clients are now preferred.
"""

import logging

logger = logging.getLogger("socrates.clients")

# Import from socratic-nexus library (PyPI package)
from socratic_nexus.clients import (
    ClaudeClient,
    GoogleClient,
    OllamaClient,
    OpenAIClient,
)

__all__ = ["ClaudeClient", "OpenAIClient", "GoogleClient", "OllamaClient"]

logger.info("Client imports sourced from socratic-nexus library")
