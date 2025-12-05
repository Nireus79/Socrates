"""
User model for Socratic RAG System
"""

import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class User:
    """Represents a user of the Socratic RAG System"""

    username: str
    passcode_hash: str
    created_at: datetime.datetime
    projects: List[str]
    is_archived: bool = False
    archived_at: Optional[datetime.datetime] = None
