"""
Local model stubs for API routers

These are minimal placeholder models used by API routers.
Routers should use get_database() and other local modules instead of relying on external model definitions.
"""

from enum import Enum
from typing import Any, Dict, Optional


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


class ProjectContext:
    """Minimal ProjectContext model stub for API routers"""
    def __init__(self, project_id: str = "", name: str = ""):
        self.project_id = project_id
        self.name = name
        self.description = ""
        self.created_at = ""
        self.metadata: Dict[str, Any] = {}
        self.phase_maturity_scores: Dict[str, float] = {}

    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


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


class ProjectDatabase:
    """Minimal ProjectDatabase stub - USE get_database() INSTEAD"""
    def __init__(self, db_path: str = ""):
        self.db_path = db_path

    def get_project(self, project_id: str) -> Optional[Dict]:
        return None

    def save_project(self, project: ProjectContext) -> bool:
        return True

    def list_projects(self, user_id: str = "", limit: int = 100) -> list:
        return []


class LearningIntegration:
    """Minimal LearningIntegration stub - USE socratic_learning FROM PyPI"""
    def __init__(self):
        pass

    def log_interaction(self, user_id: str, action: str, data: Dict) -> bool:
        return True

    def get_recommendations(self, user_id: str) -> Dict:
        return {}
