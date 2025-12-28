#!/usr/bin/env python
"""Simple check of router definitions without full app initialization"""

import sys
sys.path.insert(0, r'C:\Users\themi\PycharmProjects\Socrates')
sys.path.insert(0, r'C:\Users\themi\PycharmProjects\Socrates\socrates-api\src')

# Import routers directly
from socrates_api.routers.chat_sessions import router as chat_sessions_router
from socrates_api.routers.projects_chat import router as projects_chat_router

print("=" * 80)
print("CHAT SESSIONS ROUTER")
print("=" * 80)
print(f"Prefix: {chat_sessions_router.prefix}")
print(f"Tags: {chat_sessions_router.tags}")
print(f"Routes: {len(chat_sessions_router.routes)}")

for route in chat_sessions_router.routes:
    if hasattr(route, 'path'):
        print(f"  {str(route.methods or []).ljust(20)} {route.path}")

print("\n" + "=" * 80)
print("PROJECTS CHAT ROUTER")
print("=" * 80)
print(f"Prefix: {projects_chat_router.prefix}")
print(f"Tags: {projects_chat_router.tags}")
print(f"Routes: {len(projects_chat_router.routes)}")

for route in projects_chat_router.routes[:10]:
    if hasattr(route, 'path'):
        print(f"  {str(route.methods or []).ljust(20)} {route.path}")

if len(projects_chat_router.routes) > 10:
    print(f"  ... and {len(projects_chat_router.routes) - 10} more")

print("\n" + "=" * 80)
print("CHECKING IF ROUTES LOOK CORRECT")
print("=" * 80)

# Check expected chat sessions routes
expected_paths = [
    "/projects/{project_id}/sessions",
    "/projects/{project_id}/sessions/{session_id}",
]

for expected in expected_paths:
    found = any(
        hasattr(r, 'path') and r.path == expected
        for r in chat_sessions_router.routes
    )
    status = "✅" if found else "❌"
    print(f"{status} {expected}")
