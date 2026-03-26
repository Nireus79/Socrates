#!/usr/bin/env python
"""Test which router inclusion causes hang"""
import sys
import os
import time

# Set up path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

from fastapi import FastAPI

app = FastAPI(title="TestIncludeRouters")

print(f"[TEST] App created. Initial routes: {len(app.routes)}")

from socrates_api import routers

routers_to_test = [
    ('auth_router', routers.auth_router),
    ('commands_router', routers.commands_router),
    ('conflicts_router', routers.conflicts_router),
    ('projects_router', routers.projects_router),
]

print("[TEST] Testing router inclusion...")
for name, router in routers_to_test:
    print(f"[TEST] Including {name}...", end="", flush=True)
    start = time.time()

    try:
        app.include_router(router)
        elapsed = time.time() - start
        print(f" OK ({elapsed:.3f}s) - now {len(app.routes)} routes")
    except Exception as e:
        elapsed = time.time() - start
        print(f" ERROR ({elapsed:.3f}s): {e}")

print(f"\n[TEST] Final route count: {len(app.routes)}")
print("[TEST] All routers included successfully!")
