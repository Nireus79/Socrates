#!/usr/bin/env python
"""Initialize test data for the Socrates API.

This script creates test users and projects with secure randomly-generated passwords.
Credentials are displayed once and should be saved by the user.

Run after the API is started.
"""

import sys
import json
import secrets
import string
from pathlib import Path
from datetime import datetime, timezone

# Add backend src to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

from socrates_api.database import LocalDatabase
from socrates_api.auth import hash_password
from socrates_api.utils import IDGenerator


def generate_secure_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def init_test_data():
    """Initialize test data in the database."""

    # Initialize database (creates fresh DB if cleaned)
    db = LocalDatabase()

    # Generate secure passwords for test users
    password1 = generate_secure_password()
    password2 = generate_secure_password()
    password3 = generate_secure_password()

    # Create test users
    print("Creating test users...")

    # User 1
    user1_id = IDGenerator.user()
    user1 = db.create_user(
        user_id=user1_id,
        username="user1",
        email="user1@example.com",
        passcode_hash=hash_password(password1),
        metadata={"testing_mode": True}
    )
    print(f"[OK] Created user: user1 (ID: {user1_id})")

    # User 2
    user2_id = IDGenerator.user()
    user2 = db.create_user(
        user_id=user2_id,
        username="user2",
        email="user2@example.com",
        passcode_hash=hash_password(password2),
        metadata={"testing_mode": True}
    )
    print(f"[OK] Created user: user2 (ID: {user2_id})")

    # User 3
    user3_id = IDGenerator.user()
    user3 = db.create_user(
        user_id=user3_id,
        username="user3",
        email="user3@example.com",
        passcode_hash=hash_password(password3),
        metadata={"testing_mode": True}
    )
    print(f"[OK] Created user: user3 (ID: {user3_id})")

    print("\nCreating test projects...")

    # Create test project 1
    project1_id = IDGenerator.project()
    project1 = db.create_project(
        project_id=project1_id,
        owner="user1",
        name="Test Project 1",
        description="First test project with collaborators",
        metadata={
            "team_members": [
                {"user_id": user1_id, "role": "owner", "permissions": ["read", "write", "delete"]},
                {"user_id": user2_id, "role": "editor", "permissions": ["read", "write"]},
                {"user_id": user3_id, "role": "viewer", "permissions": ["read"]},
            ],
            "phase": "discovery"
        }
    )
    print(f"[OK] Created project: {project1.name} (ID: {project1_id})")

    # Create test project 2
    project2_id = IDGenerator.project()
    project2 = db.create_project(
        project_id=project2_id,
        owner="user2",
        name="Test Project 2",
        description="Project owned by user2",
        metadata={
            "team_members": [
                {"user_id": user2_id, "role": "owner", "permissions": ["read", "write", "delete"]},
                {"user_id": user1_id, "role": "editor", "permissions": ["read", "write"]},
            ],
            "phase": "analysis"
        }
    )
    print(f"[OK] Created project: {project2.name} (ID: {project2_id})")

    print("\n" + "="*60)
    print("TEST DATA INITIALIZED SUCCESSFULLY")
    print("="*60)
    print("\n⚠️  SAVE THESE CREDENTIALS - THEY WILL NOT BE SHOWN AGAIN:")
    print("-" * 60)
    print("User 1:")
    print(f"  Username: user1")
    print(f"  Password: {password1}")
    print(f"  ID: {user1_id}")
    print()
    print("User 2:")
    print(f"  Username: user2")
    print(f"  Password: {password2}")
    print(f"  ID: {user2_id}")
    print()
    print("User 3:")
    print(f"  Username: user3")
    print(f"  Password: {password3}")
    print(f"  ID: {user3_id}")
    print()
    print("\nTest projects:")
    print("-" * 60)
    print(f"Project 1: {project1.name}")
    print(f"  ID: {project1_id}")
    print(f"  Owner: user1")
    print(f"  Collaborators: user2 (editor), user3 (viewer)")
    print()
    print(f"Project 2: {project2.name}")
    print(f"  ID: {project2_id}")
    print(f"  Owner: user2")
    print(f"  Collaborators: user1 (editor)")
    print()
    print("Ready to test API endpoints:")
    print("  1. Login: POST /auth/login with user1/password")
    print("  2. Get Projects: GET /projects (with auth token)")
    print("  3. Get Collaborators: GET /projects/{id}/collaborators (with auth token)")
    print("-" * 60)


if __name__ == "__main__":
    try:
        init_test_data()
    except Exception as e:
        print(f"Error initializing test data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
