#!/usr/bin/env python3
"""
Test LoginRequest model validation directly.
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

from socrates_api.models import LoginRequest

print("=" * 60)
print("LOGIN REQUEST MODEL VALIDATION TEST")
print("=" * 60)

test_data = {
    "username": "testuser",
    "password": "TestPassword123!"
}

print(f"\n1. Test data:")
print(json.dumps(test_data, indent=2))

print(f"\n2. Validating with LoginRequest model...")
try:
    login_request = LoginRequest(**test_data)
    print(f"   [OK] Model validation successful")
    print(f"   Username: {login_request.username}")
    print(f"   Password: {login_request.password}")
except Exception as e:
    print(f"   [ERROR] Model validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n[OK] LoginRequest model works correctly!")
