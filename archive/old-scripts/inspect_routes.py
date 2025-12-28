#!/usr/bin/env python
"""
Inspect FastAPI routes to find what's registered
"""
import sys
sys.path.insert(0, "C:\\Users\\themi\\PycharmProjects\\Socrates\\socrates-api\\src")

from socrates_api.main import app

print("=" * 70)
print("FASTAPI ROUTES")
print("=" * 70)

for route in app.routes:
    if hasattr(route, 'path') and 'collaborator' in route.path:
        print(f"\nRoute: {route.path}")
        if hasattr(route, 'methods'):
            print(f"Methods: {route.methods}")
        if hasattr(route, 'endpoint'):
            print(f"Endpoint: {route.endpoint}")
            if hasattr(route.endpoint, '__name__'):
                print(f"Function: {route.endpoint.__name__}")
            # Try to inspect signature
            try:
                import inspect
                sig = inspect.signature(route.endpoint)
                print(f"Signature: {sig}")
            except:
                pass
