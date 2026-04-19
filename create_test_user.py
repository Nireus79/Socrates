#!/usr/bin/env python3
"""
Create a test user for Socrates API testing.
This script properly traces through the actual code path.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

from socrates_api.database import get_database
from socrates_api.auth.password import hash_password
from socrates_api.utils import IDGenerator

def create_test_user():
    """Create a test user in the database."""
    # Get database instance
    db = get_database()

    # User details
    username = "testuser"
    password = "TestPassword123!"
    email = "test@example.com"

    # Check if user already exists
    try:
        existing_user = db.load_user(username)
        print(f"User '{username}' already exists in database.")
        print(f"  Username: {existing_user.username}")
        print(f"  Email: {existing_user.email}")
        return existing_user.username, password
    except Exception:
        # User doesn't exist, create new one
        pass

    # Hash the password using the actual hash_password function
    print(f"Hashing password using bcrypt...")
    password_hash = hash_password(password)
    print(f"  Hash created: {password_hash[:20]}...")

    # Generate user ID using the actual IDGenerator
    user_id = IDGenerator.generate_id("user")
    print(f"Generated user ID: {user_id}")

    # Create user using the actual create_user method
    print(f"Creating user in database...")
    user = db.create_user(
        user_id=user_id,
        username=username,
        email=email,
        passcode_hash=password_hash,
        metadata={"created_by": "create_test_user.py"}
    )

    if user:
        print(f"[OK] User created successfully!")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  User ID: {user.user_id}")
        print(f"  Subscription: {user.subscription_tier}")
        print(f"  Created at: {user.created_at}")
        return username, password
    else:
        print(f"[ERROR] Failed to create user")
        return None, None

def test_login(username: str, password: str):
    """Test login with the created user."""
    import requests

    print(f"\n{'='*60}")
    print("Testing Login Endpoint")
    print(f"{'='*60}")

    # Test with the actual login endpoint
    url = "http://localhost:8000/auth/login"
    payload = {
        "username": username,
        "password": password
    }

    print(f"POST {url}")
    print(f"Body: {payload}")

    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print(f"[OK] Login successful!")
            data = response.json()
            if isinstance(data, dict) and "access_token" in data:
                print(f"  Access Token: {data['access_token'][:20]}...")
            return True
        else:
            print(f"[ERROR] Login failed")
            return False
    except Exception as e:
        print(f"[ERROR] Error testing login: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Socrates Test User Creation")
    print("="*60)

    # Create test user
    username, password = create_test_user()

    if username and password:
        print(f"\n{'='*60}")
        print("Test Credentials")
        print(f"{'='*60}")
        print(f"Username: {username}")
        print(f"Password: {password}")

        # Try to test login
        print(f"\nChecking if API is running on port 8000...")
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print(f"[OK] API is running")
                test_login(username, password)
            else:
                print(f"[WARNING] API returned status {response.status_code}")
                print(f"Make sure the API is running: python socrates.py --api")
        except Exception as e:
            print(f"[WARNING] API is not accessible: {e}")
            print(f"Make sure the API is running: python socrates.py --api")
    else:
        print("Failed to create test user")
        sys.exit(1)
