#!/usr/bin/env python3
"""
Properly recreate the test user with verification.
"""

import sys
import sqlite3
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

from socrates_api.database import get_database, LocalDatabase
from socrates_api.auth.password import hash_password, verify_password
from socrates_api.utils import IDGenerator

def recreate_test_user():
    """Delete old test user and create a new one."""
    db = get_database()
    username = "testuser"
    password = "TestPassword123!"
    email = "test@example.com"

    print("=" * 60)
    print("RECREATE TEST USER")
    print("=" * 60)

    # Delete existing user
    print(f"\n1. Deleting existing user (if any)...")
    try:
        with db._write_lock:
            db.conn.execute("DELETE FROM users WHERE username = ?", (username,))
            db.conn.commit()
        print(f"   [OK] Deleted existing user")
    except Exception as e:
        print(f"   [WARNING] Could not delete user: {e}")

    # Hash the password
    print(f"\n2. Hashing password with bcrypt...")
    try:
        password_hash = hash_password(password)
        print(f"   [OK] Password hashed: {password_hash[:30]}...")
    except Exception as e:
        print(f"   [ERROR] Failed to hash password: {e}")
        return False

    # Verify the hash works
    print(f"\n3. Verifying hash with original password...")
    try:
        is_valid = verify_password(password, password_hash)
        if is_valid:
            print(f"   [OK] Hash verification successful - password is correct")
        else:
            print(f"   [ERROR] Hash verification FAILED - this is a problem!")
            return False
    except Exception as e:
        print(f"   [ERROR] Hash verification error: {e}")
        return False

    # Create the user
    print(f"\n4. Creating user in database...")
    try:
        user_id = IDGenerator.user()
        user = db.create_user(
            user_id=user_id,
            username=username,
            email=email,
            passcode_hash=password_hash,
            metadata={"test": True}
        )
        if user:
            print(f"   [OK] User created successfully")
            print(f"   User ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
        else:
            print(f"   [ERROR] User creation returned None")
            return False
    except Exception as e:
        print(f"   [ERROR] Failed to create user: {e}")
        return False

    # Verify the user can login by reloading and testing password
    print(f"\n5. Verifying user login (reload from DB)...")
    try:
        loaded_user = db.load_user(username)
        is_valid = verify_password(password, loaded_user.passcode_hash)
        if is_valid:
            print(f"   [OK] Login verification successful!")
            print(f"   User can login with password: {password}")
        else:
            print(f"   [ERROR] Password verification failed after reload!")
            print(f"   Stored hash: {loaded_user.passcode_hash[:30]}...")
            print(f"   Test hash: {password_hash[:30]}...")
            return False
    except Exception as e:
        print(f"   [ERROR] Failed to reload user: {e}")
        return False

    print(f"\n" + "=" * 60)
    print("TEST USER READY FOR LOGIN")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    return True

if __name__ == "__main__":
    success = recreate_test_user()
    sys.exit(0 if success else 1)
