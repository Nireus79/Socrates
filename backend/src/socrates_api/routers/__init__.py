"""
API route modules for Socrates.

Organizes endpoints by functional area (auth, projects, chat, etc.)
Imports are conditional to allow partial startup if some routers have issues.
"""

import logging

logger = logging.getLogger(__name__)

# Conditional imports - if one fails, continue with others
_routers = {}


def _import_router(name: str, module_name: str, router_var: str = "router"):
    """Safely import a router, logging if it fails"""
    try:
        module = __import__(f"socrates_api.routers.{module_name}", fromlist=[router_var])
        router = getattr(module, router_var)
        _routers[name] = router
        logger.debug(f"Loaded router: {name}")
        return router
    except Exception as e:
        logger.warning(f"Failed to load {name} router: {e}")
        return None


# Load core routers (required for API to function)
auth_router = _import_router("auth_router", "auth")
library_integrations_router = _import_router("library_integrations_router", "library_integrations")

# Load optional routers (non-critical)
analytics_router = _import_router("analytics_router", "analytics")
projects_router = _import_router("projects_router", "projects")
collaboration_router = _import_router("collaboration_router", "collaboration")
code_generation_router = _import_router("code_generation_router", "code_generation")
knowledge_router = _import_router("knowledge_router", "knowledge")
llm_router = _import_router("llm_router", "llm")
projects_chat_router = _import_router("projects_chat_router", "projects_chat")
analysis_router = _import_router("analysis_router", "analysis")
security_router = _import_router("security_router", "security")
github_router = _import_router("github_router", "github")
events_router = _import_router("events_router", "events")
notes_router = _import_router("notes_router", "notes")
finalization_router = _import_router("finalization_router", "finalization")
subscription_router = _import_router("subscription_router", "subscription")
sponsorships_router = _import_router("sponsorships_router", "sponsorships")
query_router = _import_router("query_router", "query")
knowledge_management_router = _import_router("knowledge_management_router", "knowledge_management")
learning_router = _import_router("learning_router", "learning")
commands_router = _import_router("commands_router", "commands")
conflicts_router = _import_router("conflicts_router", "conflicts")
skills_router = _import_router("skills_router", "skills")
progress_router = _import_router("progress_router", "progress")
system_router = _import_router("system_router", "system")
nlu_router = _import_router("nlu_router", "nlu")
free_session_router = _import_router("free_session_router", "free_session")
chat_sessions_router = _import_router("chat_sessions_router", "chat_sessions")

# Collaboration router has different variable name
try:
    from socrates_api.routers.collaboration import collab_router
    _routers["collab_router"] = collab_router
except Exception as e:
    logger.warning(f"Failed to load collab_router: {e}")
    collab_router = None

# Export all loaded routers
__all__ = [name for name in _routers.keys()]
# Also export individual names for backward compatibility
for name, router in _routers.items():
    if router is not None:
        globals()[name] = router
