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
    cost_estimate: float
    timestamp: datetime.datetime
