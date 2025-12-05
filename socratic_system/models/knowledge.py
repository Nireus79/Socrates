"""
Knowledge entry model for Socratic RAG System
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeEntry:
    """Represents a single entry in the knowledge vector database"""

    id: str
    content: str
    category: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
