"""
Project context model for Socratic RAG System
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import datetime


@dataclass
class ProjectContext:
    """Represents a project's complete context and metadata"""
    project_id: str
    name: str
    owner: str
    collaborators: List[str]
    goals: str
    requirements: List[str]
    tech_stack: List[str]
    constraints: List[str]
    team_structure: str
    language_preferences: str
    deployment_target: str
    code_style: str
    phase: str
    conversation_history: List[Dict]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_archived: bool = False
    archived_at: Optional[datetime.datetime] = None
