#!/usr/bin/env python
"""Test if orchestrator creation hangs"""
import sys
import os
import time

# Set up path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

print("[TEST] Testing orchestrator creation...")

try:
    print("[TEST] Importing APIOrchestrator...", flush=True)
    from socrates_api.orchestrator import APIOrchestrator

    print("[TEST] Creating orchestrator...", flush=True)
    start = time.time()
    orchestrator = APIOrchestrator(api_key_or_config="test-key")
    elapsed = time.time() - start
    print(f"[TEST] Orchestrator created in {elapsed:.2f}s")

    print("[TEST] Calling get_system_info()...", flush=True)
    start = time.time()
    system_info = orchestrator.get_system_info()
    elapsed = time.time() - start
    print(f"[TEST] get_system_info() returned in {elapsed:.2f}s")
    print(f"[TEST] System info: {system_info}")

    print("[TEST] Success!")

except Exception as e:
    import traceback
    elapsed = time.time() - start
    print(f"[TEST] Error ({elapsed:.2f}s): {e}")
    traceback.print_exc()
