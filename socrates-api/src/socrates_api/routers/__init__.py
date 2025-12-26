"""
API route modules for Socrates.

Organizes endpoints by functional area (auth, projects, chat, etc.)
"""

from socrates_api.routers.auth import router as auth_router
from socrates_api.routers.projects import router as projects_router
from socrates_api.routers.collaboration import router as collaboration_router, collab_router
from socrates_api.routers.code_generation import router as code_generation_router
from socrates_api.routers.knowledge import router as knowledge_router
from socrates_api.routers.llm import router as llm_router
from socrates_api.routers.projects_chat import router as projects_chat_router
from socrates_api.routers.analysis import router as analysis_router
from socrates_api.routers.security import router as security_router
from socrates_api.routers.analytics import router as analytics_router
from socrates_api.routers.github import router as github_router
from socrates_api.routers.events import router as events_router
from socrates_api.routers.notes import router as notes_router
from socrates_api.routers.finalization import router as finalization_router
from socrates_api.routers.subscription import router as subscription_router
from socrates_api.routers.query import router as query_router
from socrates_api.routers.knowledge_management import router as knowledge_management_router
from socrates_api.routers.skills import router as skills_router
from socrates_api.routers.progress import router as progress_router
from socrates_api.routers.system import router as system_router
from socrates_api.routers.nlu import router as nlu_router
from socrates_api.routers.presession import router as presession_router

__all__ = [
    "auth_router",
    "projects_router",
    "collaboration_router",
    "collab_router",
    "code_generation_router",
    "knowledge_router",
    "llm_router",
    "projects_chat_router",
    "analysis_router",
    "security_router",
    "analytics_router",
    "github_router",
    "events_router",
    "notes_router",
    "finalization_router",
    "subscription_router",
    "query_router",
    "knowledge_management_router",
    "skills_router",
    "progress_router",
    "system_router",
    "nlu_router",
    "presession_router",
]
