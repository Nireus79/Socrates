"""
Monitoring and token usage models for Socratic RAG System
"""

from dataclasses import dataclass
import datetime


@dataclass
class TokenUsage:
    """Tracks API token usage and costs"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_estimate: float
    timestamp: datetime.datetime
