"""
Conflict detection models for Socratic RAG System
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ConflictInfo:
    """Represents a conflict detected in project specifications"""
    conflict_id: str
    conflict_type: str  # 'tech_stack', 'requirements', 'goals', 'constraints'
    old_value: str
    new_value: str
    old_author: str
    new_author: str
    old_timestamp: str
    new_timestamp: str
    severity: str  # 'low', 'medium', 'high'
    suggestions: List[str]
