"""
API route modules for Socrates.

Organizes endpoints by functional area (auth, projects, chat, etc.)
"""

from socrates_api.routers.auth import router as auth_router
from socrates_api.routers.projects import router as projects_router
from socrates_api.routers.websocket import router as websocket_router
from socrates_api.routers.collaboration import router as collaboration_router, collab_router
from socrates_api.routers.code_generation import router as code_generation_router
from socrates_api.routers.knowledge import router as knowledge_router
from socrates_api.routers.llm import router as llm_router
from socrates_api.routers.analysis import router as analysis_router
from socrates_api.routers.security import router as security_router
from socrates_api.routers.analytics import router as analytics_router
from socrates_api.routers.github import router as github_router
from socrates_api.routers.events import router as events_router
from socrates_api.routers.chat import router as chat_router

__all__ = [
    "auth_router",
    "projects_router",
    "websocket_router",
    "collaboration_router",
    "collab_router",
    "code_generation_router",
    "knowledge_router",
    "llm_router",
    "analysis_router",
    "security_router",
    "analytics_router",
    "github_router",
    "events_router",
    "chat_router",
]
