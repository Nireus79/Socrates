#!/usr/bin/env python3
"""
Direct test of login function to debug the actual error.
This bypasses HTTP and calls the function directly.
"""

import sys
import traceback
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

# Set up logging to see errors
import logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

print("=" * 60)
print("DIRECT LOGIN FUNCTION TEST")
print("=" * 60)

# Import dependencies
from socrates_api.database import get_database
from socrates_api.auth.password import verify_password

def test_login_direct():
    """Test login by directly calling functions."""
    db = get_database()
    username = "testuser"
    password = "TestPassword123!"

    print(f"\n1. Loading user '{username}' from database...")
    try:
        user = db.load_user(username)
        print(f"   [OK] User found: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Passcode hash exists: {bool(user.passcode_hash)}")
    except Exception as e:
        print(f"   [ERROR] Failed to load user: {e}")
        traceback.print_exc()
        return False

    print(f"\n2. Verifying password...")
    try:
        is_valid = verify_password(password, user.passcode_hash)
        print(f"   Password valid: {is_valid}")
        if not is_valid:
            print(f"   [ERROR] Password verification failed")
            return False
    except Exception as e:
        print(f"   [ERROR] Password verification error: {e}")
        traceback.print_exc()
        return False

    print(f"\n3. Checking MFA status...")
    try:
        from socratic_security.auth import get_mfa_manager
        mfa_manager = get_mfa_manager()
        mfa_enabled = mfa_manager.is_mfa_enabled(username)
        print(f"   MFA enabled: {mfa_enabled}")
    except Exception as e:
        print(f"   [ERROR] MFA check failed: {e}")
        traceback.print_exc()
        return False

    print(f"\n4. Creating tokens...")
    try:
        from socrates_api.auth import create_access_token, create_refresh_token
        access_token = create_access_token(username)
        refresh_token = create_refresh_token(username)
        print(f"   [OK] Access token created: {access_token[:20]}...")
        print(f"   [OK] Refresh token created: {refresh_token[:20]}...")
    except Exception as e:
        print(f"   [ERROR] Token creation failed: {e}")
        traceback.print_exc()
        return False

    print(f"\n[OK] All steps completed successfully!")
    return True

if __name__ == "__main__":
    success = test_login_direct()
    sys.exit(0 if success else 1)
