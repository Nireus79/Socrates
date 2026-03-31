#!/usr/bin/env python3
"""
Debug HTTP login by making raw HTTP request and capturing all details.
"""

import sys
import json
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

# Enable ALL logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s - %(message)s'
)

# Import and enable uvicorn logging
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

print("=" * 60)
print("DEBUG: Direct HTTP Layer Test")
print("=" * 60)

# Create a mock FastAPI test client
from fastapi.testclient import TestClient
from socrates_api.main import app

print("\n[INFO] Creating FastAPI TestClient...")
client = TestClient(app)

print("[INFO] Making POST request to /auth/login...")
try:
    response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "TestPassword123!"
        }
    )

    print(f"\n[RESPONSE]")
    print(f"  Status: {response.status_code}")
    print(f"  Body: {json.dumps(response.json(), indent=2)}")

except Exception as e:
    print(f"\n[ERROR] Request failed: {e}")
    import traceback
    traceback.print_exc()
