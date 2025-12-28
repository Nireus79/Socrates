#!/usr/bin/env python
"""
Detailed route inspection
"""
import sys
sys.path.insert(0, "C:\\Users\\themi\\PycharmProjects\\Socrates\\socrates-api\\src")

from socrates_api.main import app
import json

print("=" * 70)
print("DETAILED ROUTE INSPECTION")
print("=" * 70)

# Get all routes
all_routes = []
for route in app.routes:
    if hasattr(route, 'path'):
        all_routes.append({
            'path': route.path,
            'methods': getattr(route, 'methods', None),
            'endpoint_name': getattr(route.endpoint, '__name__', None) if hasattr(route, 'endpoint') else None,
        })

# Find collaborator routes
print("\nCOLLABORATOR ROUTES:")
for route in all_routes:
    if 'collaborator' in route['path']:
        print(f"Path: {route['path']}")
        print(f"Methods: {route['methods']}")
        print(f"Endpoint: {route['endpoint_name']}")
        print()

# List all routes
print("\nALL ROUTES:")
for i, route in enumerate(all_routes[:30]):  # First 30
    print(f"{i:3d}. {route['path']:50s} {str(route['methods']):15s} {route['endpoint_name']}")
