#!/usr/bin/env python
"""Initialize test data for the Socrates API.

This script creates:
- Test users (testuser, admin)
- Test projects with collaborators
- Sample data for testing

Run after the API is started.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add backend src to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

from socrates_api.database import LocalDatabase
from socrates_api.auth import hash_password
from socrates_api.utils import IDGenerator

def init_test_data():
    """Initialize test data in the database."""

    # Initialize database (creates fresh DB if cleaned)
    db = LocalDatabase()

    # Create test users
    print("Creating test users...")

    # User 1: testuser
    user1_id = IDGenerator.user()
    user1 = db.create_user(
        user_id=user1_id,
        username="testuser",
        email="test@example.com",
        passcode_hash=hash_password("testpass"),
        metadata={"testing_mode": True}
    )
    print(f"[OK] Created user: testuser (ID: {user1_id})")

    # User 2: admin
    user2_id = IDGenerator.user()
    user2 = db.create_user(
        user_id=user2_id,
        username="admin",
        email="admin@example.com",
        passcode_hash=hash_password("adminpass"),
        metadata={"testing_mode": True}
    )
    print(f"[OK] Created user: admin (ID: {user2_id})")

    # User 3: collaborator
    user3_id = IDGenerator.user()
    user3 = db.create_user(
        user_id=user3_id,
        username="collaborator",
        email="collab@example.com",
        passcode_hash=hash_password("collabpass"),
        metadata={"testing_mode": True}
    )
    print(f"[OK] Created user: collaborator (ID: {user3_id})")

    print("\nCreating test projects...")

    # Create test project 1
    project1_id = IDGenerator.project()
    project1 = db.create_project(
        project_id=project1_id,
        owner="testuser",
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
        owner="admin",
        name="Admin Test Project",
        description="Project owned by admin user",
        metadata={
            "team_members": [
                {"user_id": user2_id, "role": "owner", "permissions": ["read", "write", "delete"]},
                {"user_id": user1_id, "role": "editor", "permissions": ["read", "write"]},
            ],
            "phase": "analysis"
        }
    )
    print(f"[OK] Created project: {project2.name} (ID: {project2_id})")

    print("\n" + "="*50)
    print("TEST DATA INITIALIZED SUCCESSFULLY")
    print("="*50)
    print("\nTest credentials:")
    print("-" * 50)
    print("User 1:")
    print(f"  Username: testuser")
    print(f"  Password: testpass")
    print(f"  ID: {user1_id}")
    print()
    print("User 2 (admin):")
    print(f"  Username: admin")
    print(f"  Password: adminpass")
    print(f"  ID: {user2_id}")
    print()
    print("User 3 (collaborator):")
    print(f"  Username: collaborator")
    print(f"  Password: collabpass")
    print(f"  ID: {user3_id}")
    print()
    print("\nTest projects:")
    print("-" * 50)
    print(f"Project 1: {project1.name}")
    print(f"  ID: {project1_id}")
    print(f"  Owner: testuser")
    print(f"  Collaborators: admin (editor), collaborator (viewer)")
    print()
    print(f"Project 2: {project2.name}")
    print(f"  ID: {project2_id}")
    print(f"  Owner: admin")
    print(f"  Collaborators: testuser (editor)")
    print()
    print("Ready to test API endpoints:")
    print("  1. Login: POST /auth/login with testuser/testpass")
    print("  2. Get Projects: GET /projects (with auth token)")
    print("  3. Get Collaborators: GET /projects/{id}/collaborators (with auth token)")
    print("-" * 50)

if __name__ == "__main__":
    try:
        init_test_data()
    except Exception as e:
        print(f"Error initializing test data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
