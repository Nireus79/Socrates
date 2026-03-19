"""Client integrations for Socrates AI

Note: LLM client functionality now provided by socrates-nexus package.
This module is maintained for backward compatibility.
"""

# Legacy import for backward compatibility - use socrates_nexus.LLMClient instead
try:
    from socrates_nexus import LLMClient as ClaudeClient
except ImportError:
    # Fallback if socrates_nexus is not installed
    ClaudeClient = None

__all__ = ["ClaudeClient"]
