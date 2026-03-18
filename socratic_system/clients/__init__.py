"""Client integrations for Socrates AI

Note: LLM client functionality now provided by socrates-nexus package.
This module is maintained for backward compatibility.
"""

# Legacy import for backward compatibility - use socrates_nexus.LLMClient instead
from socrates_nexus import LLMClient as ClaudeClient

__all__ = ["ClaudeClient"]
