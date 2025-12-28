#!/usr/bin/env python
"""Diagnostic script to inspect FastAPI registered routes"""

import sys
sys.path.insert(0, r'C:\Users\themi\PycharmProjects\Socrates')
sys.path.insert(0, r'C:\Users\themi\PycharmProjects\Socrates\socrates-api\src')

from socrates_api.main import app

print("=" * 80)
print("FASTAPI REGISTERED ROUTES")
print("=" * 80)

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        # Skip internal routes
        if any(x in route.path for x in ['openapi', 'swagger', 'redoc', 'health']):
            continue
        print(f"{str(route.methods or []).ljust(20)} {route.path}")

print("\n" + "=" * 80)
print("CHECKING CHAT SESSIONS ROUTES")
print("=" * 80)

chat_routes = [r for r in app.routes
               if hasattr(r, 'path') and 'chat' in r.path.lower() and 'sessions' in r.path.lower()]

if chat_routes:
    print(f"Found {len(chat_routes)} chat/sessions routes:")
    for route in chat_routes:
        print(f"  {str(route.methods or []).ljust(20)} {route.path}")
else:
    print("❌ NO CHAT/SESSIONS ROUTES FOUND")

print("\n" + "=" * 80)
print("CHECKING CHAT ROUTES (ALL)")
print("=" * 80)

chat_all_routes = [r for r in app.routes
                    if hasattr(r, 'path') and 'chat' in r.path.lower()]

if chat_all_routes:
    print(f"Found {len(chat_all_routes)} chat routes:")
    for route in chat_all_routes:
        print(f"  {str(route.methods or []).ljust(20)} {route.path}")
else:
    print("❌ NO CHAT ROUTES FOUND AT ALL")

print("\n" + "=" * 80)
print("CHECKING PROJECTS ROUTES")
print("=" * 80)

proj_routes = [r for r in app.routes
               if hasattr(r, 'path') and 'projects' in r.path.lower()]

print(f"Total projects routes: {len(proj_routes)}")
for route in proj_routes[:10]:  # Show first 10
    print(f"  {str(route.methods or []).ljust(20)} {route.path}")
if len(proj_routes) > 10:
    print(f"  ... and {len(proj_routes) - 10} more")

print("\n" + "=" * 80)
print("ROUTERS REGISTERED")
print("=" * 80)

print(f"Total routes: {len(app.routes)}")

# Check each router
from socrates_api import routers

routers_to_check = [
    ('chat_sessions_router', routers.chat_sessions_router),
    ('projects_chat_router', routers.projects_chat_router),
    ('collaboration_router', routers.collaboration_router),
]

for name, router in routers_to_check:
    print(f"\n{name}:")
    print(f"  Router object: {router}")
    print(f"  Routes in router: {len(router.routes)}")
    for route in router.routes[:5]:
        if hasattr(route, 'path'):
            print(f"    {str(route.methods or []).ljust(20)} {route.path}")
    if len(router.routes) > 5:
        print(f"    ... and {len(router.routes) - 5} more")
