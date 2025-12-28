#!/usr/bin/env python
"""Check if projects_chat imports cleanly"""
import sys
import traceback

sys.path.insert(0, r'C:\Users\themi\PycharmProjects\Socrates\socrates-api\src')

try:
    print("Attempting to import projects_chat...")
    from socrates_api.routers.projects_chat import router

    print("Import successful!")
    print(f"Router has {len(router.routes)} routes")

    # Check for routes that should exist
    routes_to_check = [
        "/projects/{project_id}/chat/sessions",
        "/projects/{project_id}/chat/test-endpoint",
        "/projects/{project_id}/chat/message",
        "/projects/{project_id}/chat/question",
    ]

    router_paths = [r.path for r in router.routes if hasattr(r, 'path')]

    print("\nChecking for expected routes:")
    for expected in routes_to_check:
        found = expected in router_paths
        print(f"  {expected}: {'FOUND' if found else 'NOT FOUND'}")

    print("\nAll routes in router:")
    for route in sorted(set(router_paths)):
        print(f"  {route}")

except Exception as e:
    print(f"Import failed with error:")
    print(f"  {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
