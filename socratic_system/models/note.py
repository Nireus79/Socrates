"""Project note model for Socratic RAG System"""

from dataclasses import dataclass, field
from typing import List, Optional
import datetime
import uuid


@dataclass
class ProjectNote:
    """Represents a note attached to a project"""
    note_id: str
    project_id: str
    note_type: str  # 'design', 'bug', 'idea', 'task', 'general'
    title: str
    content: str
    created_at: datetime.datetime
    created_by: str
    tags: List[str] = field(default_factory=list)

    @classmethod
    def create(cls, project_id: str, note_type: str, title: str, content: str, created_by: str, tags: Optional[List[str]] = None) -> 'ProjectNote':
        """Create a new project note with auto-generated ID"""
        return cls(
            note_id=str(uuid.uuid4()),
            project_id=project_id,
            note_type=note_type,
            title=title,
            content=content,
            created_at=datetime.datetime.now(),
            created_by=created_by,
            tags=tags or []
        )

    def matches_query(self, query: str) -> bool:
        """Check if note matches a search query"""
        query_lower = query.lower()
        return (
            query_lower in self.title.lower() or
            query_lower in self.content.lower() or
            query_lower in self.note_type.lower() or
            any(query_lower in tag.lower() for tag in self.tags)
        )
