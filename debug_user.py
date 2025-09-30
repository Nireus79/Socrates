#!/usr/bin/env python3
"""Debug user authentication"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import DatabaseManager
from werkzeug.security import check_password_hash

# Connect to database
db = DatabaseManager('data/projects.db')

# Check schema
print("=" * 60)
print("CHECKING DATABASE SCHEMA")
print("=" * 60)

try:
    schema = db.execute_query("PRAGMA table_info(users)")
    print("\nUsers table columns:")
    for col in schema:
        print(f"  - {col['name']} ({col['type']})")

    # Check if password_hash column exists
    has_password_hash = any(col['name'] == 'password_hash' for col in schema)
    print(f"\n✓ password_hash column exists: {has_password_hash}")

except Exception as e:
    print(f"✗ Error checking schema: {e}")

# List all users
print("\n" + "=" * 60)
print("CHECKING USERS IN DATABASE")
print("=" * 60)

try:
    users = db.execute_query("SELECT id, username, email, password_hash, role FROM users")

    if not users:
        print("\n⚠ No users found in database!")
        print("  Please register a user first")
    else:
        print(f"\nFound {len(users)} user(s):")
        for user in users:
            print(f"\n  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Role: {user['role']}")
            print(f"  Password hash exists: {bool(user.get('password_hash'))}")
            if user.get('password_hash'):
                print(f"  Password hash (first 20 chars): {user['password_hash'][:20]}...")
            else:
                print(f"  ⚠ PASSWORD HASH IS NULL OR EMPTY!")

except Exception as e:
    print(f"✗ Error querying users: {e}")

# Test password verification
print("\n" + "=" * 60)
print("TEST PASSWORD VERIFICATION")
print("=" * 60)

try:
    users = db.execute_query("SELECT username, password_hash FROM users LIMIT 1")
    if users and users[0].get('password_hash'):
        test_username = users[0]['username']
        stored_hash = users[0]['password_hash']

        print(f"\nTesting with user: {test_username}")
        test_password = input("Enter the password you used during registration: ")

        is_valid = check_password_hash(stored_hash, test_password)
        print(f"\n{'✓' if is_valid else '✗'} Password verification: {is_valid}")

        if not is_valid:
            print("\n⚠ Password does not match!")
            print("  This means either:")
            print("  1. You entered the wrong password")
            print("  2. The password wasn't stored correctly during registration")
    else:
        print("\n⚠ No users with password hash to test")

except Exception as e:
    print(f"✗ Error testing password: {e}")

print("\n" + "=" * 60)
