"""
Local model stubs for API routers

These are minimal placeholder models used by API routers.
Routers should use get_database() and other local modules instead of relying on external model definitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class TeamMemberRole:
    """Team member with role and skills"""
    username: str
    role: str  # 'owner', 'editor', 'viewer'
    skills: List[str] = field(default_factory=list)
    joined_at: Optional[Any] = None
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        joined_str = self.joined_at.isoformat() if hasattr(self.joined_at, 'isoformat') else str(self.joined_at)
        return {
            "username": self.username,
            "role": self.role,
            "skills": self.skills,
            "joined_at": joined_str,
            "status": self.status,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TeamMemberRole':
        """Create from dictionary"""
        return TeamMemberRole(
            username=data.get("username"),
            role=data.get("role"),
            skills=data.get("skills", []),
            joined_at=data.get("joined_at"),
            status=data.get("status", "active"),
        )


class EventType(str, Enum):
    """Event types for system notifications and tracking"""
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_ARCHIVED = "PROJECT_ARCHIVED"
    PROJECT_RESTORED = "PROJECT_RESTORED"
    QUESTION_GENERATED = "QUESTION_GENERATED"
    RESPONSE_ANALYZED = "RESPONSE_ANALYZED"
    CODE_GENERATED = "CODE_GENERATED"
    CODE_ANALYSIS_COMPLETE = "CODE_ANALYSIS_COMPLETE"
    PHASE_MATURITY_UPDATED = "PHASE_MATURITY_UPDATED"
    DOCUMENT_IMPORTED = "DOCUMENT_IMPORTED"
    COLLABORATION_ADDED = "COLLABORATION_ADDED"
    COLLABORATION_REMOVED = "COLLABORATION_REMOVED"
    ACTIVITY_LOGGED = "ACTIVITY_LOGGED"


class User:
    """User model for API routers - supports all auth parameters"""
    def __init__(
        self,
        user_id: str = "",
        username: str = "",
        email: str = "",
        passcode_hash: str = "",
        subscription_tier: str = "free",
        subscription_status: str = "active",
        testing_mode: bool = False,
        created_at: Optional[Any] = None,
        archived: bool = False,
        archived_at: Optional[str] = None,
        **kwargs
    ):
        self.id = user_id
        self.username = username
        self.email = email
        self.passcode_hash = passcode_hash
        self.subscription_tier = subscription_tier
        self.subscription_status = subscription_status
        self.testing_mode = testing_mode
        self.created_at = created_at
        self.archived = archived
        self.archived_at = archived_at
        self.metadata: Dict[str, Any] = {}
        # Store any additional kwargs
        for key, value in kwargs.items():
            if not key.startswith("_"):
                setattr(self, key, value)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "passcode_hash": self.passcode_hash,
            "subscription_tier": self.subscription_tier,
            "subscription_status": self.subscription_status,
            "testing_mode": self.testing_mode,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for compatibility"""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for compatibility"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator support"""
        return hasattr(self, key)


class ProjectContext:
    """Minimal ProjectContext model stub for API routers"""
    def __init__(
        self,
        project_id: str = "",
        name: str = "",
        owner: str = "",
        description: str = "",
        phase: str = "discovery",
        created_at: str = "",
        updated_at: str = "",
        is_archived: bool = False,
        conversation_history: Optional[list] = None,
        overall_maturity: float = 0.0,
        progress: int = 0,
        goals: str = "",
        requirements: Optional[list] = None,
        tech_stack: Optional[list] = None,
        constraints: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        repository_url: Optional[str] = None,
        team_members: Optional[list] = None,
        code_history: Optional[list] = None,
        chat_sessions: Optional[Dict] = None,
        code_generated_count: int = 0,
        **kwargs
    ):
        self.project_id = project_id
        self.name = name
        self.owner = owner
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at
        self.phase = phase
        self.is_archived = is_archived
        self.overall_maturity = overall_maturity
        self.progress = progress
        self.metadata = metadata or {}
        self.conversation_history = conversation_history or []
        self.goals = goals
        self.requirements = requirements or []
        self.tech_stack = tech_stack or []
        self.constraints = constraints or []
        self.repository_url = repository_url
        self.team_members = team_members or []
        self.code_history = code_history or []
        self.chat_sessions = chat_sessions or {}
        self.code_generated_count = code_generated_count

        # Nested data structures - standardized as typed fields
        # Maturity tracking
        self.maturity_score: float = kwargs.get("maturity_score", 0.0)
        self.previous_maturity: float = kwargs.get("previous_maturity", 0.0)
        self.maturity_history: List[Dict[str, Any]] = kwargs.get("maturity_history", [])

        # Phase and category progress
        self.phase_maturity_scores: Dict[str, float] = kwargs.get("phase_maturity_scores", {})
        self.category_scores: Dict[str, float] = kwargs.get("category_scores", {})

        # Chat and question attributes
        self.pending_questions: List[Dict[str, Any]] = kwargs.get("pending_questions", [])
        self.answered_questions: List[Dict[str, Any]] = kwargs.get("answered_questions", [])
        self.skipped_questions: List[Dict[str, Any]] = kwargs.get("skipped_questions", [])

        # Store any additional kwargs
        for key, value in kwargs.items():
            if not key.startswith("_") and key not in (
                "maturity_score", "previous_maturity", "maturity_history",
                "phase_maturity_scores", "category_scores",
                "pending_questions", "answered_questions", "skipped_questions"
            ):
                setattr(self, key, value)

    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "phase": self.phase,
            "is_archived": self.is_archived,
            "overall_maturity": self.overall_maturity,
            "progress": self.progress,
            "metadata": self.metadata
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for compatibility"""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for compatibility"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator support"""
        return hasattr(self, key)


class StorageQuotaManager:
    """Storage quota management - stub for subscription limits"""
    @staticmethod
    def bytes_to_gb(bytes_val: int) -> float:
        """Convert bytes to gigabytes"""
        return bytes_val / (1024 ** 3) if bytes_val > 0 else 0.0

    @staticmethod
    def calculate_user_storage_usage(user_id: str, db: Any) -> int:
        """Calculate user's total storage usage in bytes"""
        return 0  # Stub - returns 0 bytes

    @staticmethod
    def get_storage_usage_report(user_id: str, db: Any) -> Dict[str, Any]:
        """Get detailed storage usage report"""
        return {"total_gb": 0.0, "breakdown": {}}


class LearningIntegration:
    """Minimal LearningIntegration stub - USE socratic_learning FROM PyPI"""
    def __init__(self):
        pass

    def log_interaction(self, user_id: str, action: str, data: Dict) -> bool:
        return True

    def get_recommendations(self, user_id: str) -> Dict:
        return {}
