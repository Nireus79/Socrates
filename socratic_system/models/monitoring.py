"""
Monitoring and token usage models for Socratic RAG System
"""

import datetime
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Tracks API token usage and costs"""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    timestamp: datetime.datetime
    model: str = "claude-opus-4-5-20251101"
    cost_estimate: float = 0.0
