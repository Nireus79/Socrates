"""Client integrations for Socrates AI"""

import logging

logger = logging.getLogger("socrates.clients")

# Always available - Anthropic SDK required
from .claude_client import ClaudeClient

__all__ = ["ClaudeClient"]

# Optional providers - only import if their SDKs are available
try:
    from .openai_client import OpenAIClient
    __all__.append("OpenAIClient")
except ImportError as e:
    logger.debug(f"OpenAI client not available: {e}")

try:
    from .google_client import GoogleClient
    __all__.append("GoogleClient")
except ImportError as e:
    logger.debug(f"Google client not available: {e}")

try:
    from .ollama_client import OllamaClient
    __all__.append("OllamaClient")
except ImportError as e:
    logger.debug(f"Ollama client not available: {e}")
