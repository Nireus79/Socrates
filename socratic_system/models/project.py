"""
Project context model for Socratic RAG System
"""

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional


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
    chat_mode: str = "socratic"  # "socratic" or "direct" mode
    is_archived: bool = False
    archived_at: Optional[datetime.datetime] = None
    progress: int = 0  # 0-100 percentage
    status: str = "active"  # active, completed, on-hold
