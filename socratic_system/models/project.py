"""
Project context model for Socratic RAG System
"""

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional

from socratic_system.models.role import TeamMemberRole


@dataclass
class ProjectContext:
    """Represents a project's complete context and metadata"""

    project_id: str
    name: str
    owner: str
    phase: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    collaborators: List[
        str
    ] = None  # DEPRECATED: Kept for backward compatibility. Use team_members instead.
    goals: str = ""
    requirements: List[str] = None
    tech_stack: List[str] = None
    constraints: List[str] = None
    team_structure: str = "individual"
    language_preferences: str = "python"
    deployment_target: str = "local"
    code_style: str = "standard"
    conversation_history: List[Dict] = None
    chat_mode: str = "socratic"  # "socratic" or "direct" mode
    is_archived: bool = False
    archived_at: Optional[datetime.datetime] = None
    progress: int = 0  # 0-100 percentage
    status: str = "active"  # active, completed, on-hold
    project_type: str = (
        "software"  # Type of project (software, business, creative, research, marketing, educational)
    )

    # Team management (NEW)
    team_members: Optional[List[TeamMemberRole]] = (
        None  # Team members with roles (supersedes collaborators)
    )
    pending_questions: Optional[List[Dict]] = None  # Question queue for team projects

    # Notes tracking
    notes: Optional[List[Dict]] = None  # Project notes list

    # Maturity tracking fields
    phase_maturity_scores: Dict[str, float] = None  # Per-phase maturity (0-100)
    category_scores: Dict[str, Dict[str, float]] = None  # Category scores by phase
    categorized_specs: Dict[str, List[Dict[str, any]]] = (
        None  # Specs organized by phase and category
    )
    maturity_history: List[Dict[str, any]] = None  # Historical maturity events

    # Analytics tracking fields (real-time metrics updated after each Q&A)
    analytics_metrics: Dict[str, any] = None  # Real-time analytics metrics

    def __post_init__(self):
        """Initialize default values and migrate legacy collaborators to team_members"""
        # Initialize list fields with defaults
        if self.collaborators is None:
            self.collaborators = []
        if self.requirements is None:
            self.requirements = []
        if self.tech_stack is None:
            self.tech_stack = []
        if self.constraints is None:
            self.constraints = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.notes is None:
            self.notes = []

        # Migrate old collaborators to team_members if needed (backward compatibility)
        if self.team_members is None and self.collaborators:
            self.team_members = []

            # Add owner as team member with "lead" role (default for owner/lead)
            if self.owner:
                owner_member = TeamMemberRole(
                    username=self.owner, role="lead", skills=[], joined_at=self.created_at
                )
                self.team_members.append(owner_member)

            # Migrate collaborators to team members with default "creator" role
            for collab_username in self.collaborators:
                member = TeamMemberRole(
                    username=collab_username,
                    role="creator",  # Default role for migrated users
                    skills=[],
                    joined_at=datetime.datetime.now(),
                )
                self.team_members.append(member)

        # Initialize team_members for new projects (no collaborators)
        elif self.team_members is None:
            self.team_members = []
            if self.owner:
                owner_member = TeamMemberRole(
                    username=self.owner, role="lead", skills=[], joined_at=self.created_at
                )
                self.team_members.append(owner_member)

        # Initialize pending_questions queue for question assignment
        if self.pending_questions is None:
            self.pending_questions = []

        if self.phase_maturity_scores is None:
            self.phase_maturity_scores = {
                "discovery": 0.0,
                "analysis": 0.0,
                "design": 0.0,
                "implementation": 0.0,
            }
        if self.category_scores is None:
            self.category_scores = {}
        if self.categorized_specs is None:
            self.categorized_specs = {}
        if self.maturity_history is None:
            self.maturity_history = []
        if self.analytics_metrics is None:
            self.analytics_metrics = {
                "velocity": 0.0,
                "total_qa_sessions": 0,
                "avg_confidence": 0.0,
                "weak_categories": [],
                "strong_categories": [],
                "last_updated": None,
            }

    def get_member_role(self, username: str) -> Optional[str]:
        """Get role for a specific team member."""
        for member in self.team_members or []:
            if member.username == username:
                return member.role
        return None

    def is_solo_project(self) -> bool:
        """Check if this is a solo project (only owner, no other team members)."""
        return len(self.team_members or []) <= 1
