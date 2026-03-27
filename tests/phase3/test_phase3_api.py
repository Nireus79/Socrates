#!/usr/bin/env python
"""
Phase 3 API Integration Tests
"""

import json
import sys
from pathlib import Path

# Add backend to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from socrates_api.database import LocalDatabase
from socrates_api.models_local import ProjectContext


def test_project_creation():
    """Test 3.1.2: Project creation via database"""
    print("\n" + "="*70)
    print("TEST 3.1.2: Project Creation Test")
    print("="*70)
    
    try:
        # Initialize database
        db = LocalDatabase()
        
        # Test user data
        test_user_id = "test_user_p3_001"
        test_username = "testuser_p3"
        test_email = "testp3@example.com"
        
        print(f"\n[1] Creating test user...")
        user_result = db.save_user({
            "id": test_user_id,
            "username": test_username,
            "email": test_email,
            "passcode_hash": "dummy_hash",
            "subscription_tier": "free",
            "subscription_status": "active"
        })
        print(f"    User created: {bool(user_result)}")
        
        # Verify user was created
        loaded_user = db.load_user(test_username)
        if not loaded_user:
            print(f"    [ERROR] User not found in database")
            return False
        
        print(f"    [OK] User loaded: {loaded_user.get('username')}")
        
        # Create project using ProjectContext
        print(f"\n[2] Creating test project...")
        project = ProjectContext(
            project_id="test_project_p3_001",
            name="Test Project P3",
            owner=test_user_id,
            description="A test project for Phase 3 testing",
            phase="discovery"
        )
        
        project_result = db.save_project(project)
        if not project_result:
            print(f"    [ERROR] Failed to save project")
            return False
        
        print(f"    Project saved: {project_result}")
        
        # Verify project was created (returns dict)
        loaded_project = db.load_project("test_project_p3_001")
        if not loaded_project:
            print(f"    [ERROR] Project not found in database")
            return False
        
        print(f"    [OK] Project loaded from database")
        if isinstance(loaded_project, dict):
            print(f"       - Project ID: {loaded_project.get('id')}")
            print(f"       - Name: {loaded_project.get('name')}")
            print(f"       - Owner: {loaded_project.get('owner')}")
        else:
            print(f"       - Project ID: {loaded_project.project_id}")
            print(f"       - Name: {loaded_project.name}")
            print(f"       - Owner: {loaded_project.owner}")
        
        # List user projects
        print(f"\n[3] Listing user projects...")
        user_projects = db.get_user_projects(test_user_id)
        print(f"    User has {len(user_projects)} projects")
        for proj in user_projects:
            if isinstance(proj, dict):
                print(f"      - {proj.get('name')} ({proj.get('id')})")
            else:
                print(f"      - {proj.name} ({proj.project_id})")
        
        print(f"\n[OK] Test 3.1.2 PASSED")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test 3.1.2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nPhase 3 API Integration Tests")
    print("="*70)
    
    results = []
    results.append(("3.1.2 Project Creation", test_project_creation()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
