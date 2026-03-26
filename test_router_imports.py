#!/usr/bin/env python
"""Test which router import causes hang"""
import sys
import os
import time

# Set up path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

routers_to_test = [
    'auth_router',
    'commands_router',
    'conflicts_router',
    'projects_router',
    'code_generation_router',
    'knowledge_router',
    'learning_router',
    'llm_router',
    'projects_chat_router',
    'analysis_router',
]

from socrates_api import routers

print("[TEST] Testing router imports...")
for router_name in routers_to_test:
    print(f"[TEST] Importing {router_name}...", end="", flush=True)
    start = time.time()

    try:
        router = getattr(routers, router_name)
        elapsed = time.time() - start
        print(f" OK ({elapsed:.2f}s)")
    except AttributeError as e:
        elapsed = time.time() - start
        print(f" MISSING ({e})")
    except Exception as e:
        elapsed = time.time() - start
        print(f" ERROR: {type(e).__name__}: {e}")
