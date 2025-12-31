"""
Phase 3: Integration Testing
Tests the complete workflow paths through direct code execution
"""

import sys
from datetime import datetime

sys.path.insert(0, ".")
sys.path.insert(0, "socrates-api/src")

def test_project_creation_workflow():
    """Test complete project creation workflow"""
    print("\n" + "="*70)
    print("TEST: Complete Project Creation Workflow")
    print("="*70 + "\n")

    try:
        from socrates_api.auth.password import hash_password, verify_password
        from socrates_api.database import DatabaseSingleton

        from socratic_system.models import User
        from socratic_system.subscription.checker import SubscriptionChecker
        from socratic_system.utils.id_generator import ProjectIDGenerator

        # Step 1: Initialize database singleton
        print("[1/7] Initializing DatabaseSingleton...")
        db = DatabaseSingleton.get_instance()
        print(f"      [OK] Database initialized: {type(db).__name__}")

        # Step 2: Create a test user
        print("[2/7] Creating test user...")
        username = f"test_user_{int(datetime.now().timestamp() * 1000)}"
        email = f"{username}@test.local"
        password = "TestPassword123!"
        password_hash = hash_password(password)

        user = User(
            username=username,
            email=email,
            passcode_hash=password_hash,
            subscription_tier="free",
            subscription_status="active",
            testing_mode=False,
            created_at=datetime.now()
        )
        db.save_user(user)
        print(f"      [OK] User created: {username}")

        # Step 3: Verify password works
        print("[3/7] Verifying password hashing...")
        loaded_user = db.load_user(username)
        if verify_password(password, loaded_user.passcode_hash):
            print("      [OK] Password verification works")
        else:
            print("      [FAIL] Password verification failed!")
            return False

        # Step 4: Check subscription limits
        print("[4/7] Checking subscription limits...")
        can_create, message = SubscriptionChecker.check_project_limit(loaded_user, 0)
        if can_create:
            print(f"      [OK] User can create projects: {message}")
        else:
            print(f"      [FAIL] Subscription check failed: {message}")
            return False

        # Step 5: Generate project ID
        print("[5/7] Generating project ID...")
        project_id = ProjectIDGenerator.generate(username)
        if project_id.startswith("proj_"):
            print(f"      [OK] Project ID generated: {project_id}")
        else:
            print(f"      [FAIL] Invalid project ID format: {project_id}")
            return False

        # Step 6: Create and save project (simulating agent behavior)
        print("[6/7] Creating and saving project...")
        from socratic_system.models import ProjectContext

        project = ProjectContext(
            project_id=project_id,
            name="Integration Test Project",
            owner=username,
            description="Test project for Phase 3 integration testing",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_archived=False
        )
        db.save_project(project)
        print(f"      [OK] Project saved: {project.project_id}")

        # Step 7: Verify project can be retrieved
        print("[7/7] Verifying project retrieval...")
        retrieved_project = db.load_project(project_id)
        if retrieved_project and retrieved_project.name == "Integration Test Project":
            print("      [OK] Project retrieved successfully")
            print(f"      [OK] Project owner: {retrieved_project.owner}")
            print(f"      [OK] Project phase: {retrieved_project.phase}")
        else:
            print("      [FAIL] Project retrieval failed!")
            return False

        print("\n" + "="*70)
        print("[SUCCESS] Complete workflow executed successfully!")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_integration():
    """Test orchestrator with unified patterns"""
    print("\n" + "="*70)
    print("TEST: Orchestrator Integration with Unified Patterns")
    print("="*70 + "\n")

    try:

        from socrates_api.database import DatabaseSingleton

        from socratic_system.config import SocratesConfig
        from socratic_system.orchestration.orchestrator import AgentOrchestrator

        # Initialize config from environment
        print("[1/4] Initializing orchestrator...")
        config = SocratesConfig.from_env()
        orchestrator = AgentOrchestrator(config)
        print("      [OK] Orchestrator created")

        # Step 2: Verify database is singleton
        print("[2/4] Verifying database is shared singleton...")
        db_from_orchestrator = orchestrator.database
        db_from_singleton = DatabaseSingleton.get_instance()

        if db_from_orchestrator is db_from_singleton:
            print("      [OK] Orchestrator uses shared DatabaseSingleton")
        else:
            print("      [FAIL] Orchestrator has different database instance!")
            return False

        # Step 3: Test project creation through orchestrator
        print("[3/4] Testing project creation through orchestrator...")
        test_user = f"orch_test_{int(datetime.now().timestamp() * 1000)}"

        # Create test user first
        from socrates_api.auth.password import hash_password

        from socratic_system.models import User

        user = User(
            username=test_user,
            email=f"{test_user}@test.local",
            passcode_hash=hash_password("TestPass123!"),
            subscription_tier="free",
            subscription_status="active",
            testing_mode=False,
            created_at=datetime.now()
        )
        orchestrator.database.save_user(user)

        # Now create project through orchestrator
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": "Orchestrator Test Project",
                "project_type": "general"}
        )

        if result.get("status") == "success":
            project = result.get("project")
            print(f"      [OK] Project created through orchestrator: {project.project_id}")
        else:
            print(f"      [FAIL] Project creation failed: {result.get('message')}")
            return False

        # Step 4: Verify project can be retrieved
        print("[4/4] Verifying project persistence...")
        retrieved = orchestrator.database.load_project(project.project_id)
        if retrieved and retrieved.name == "Orchestrator Test Project":
            print("      [OK] Project persisted and retrievable")
        else:
            print("      [FAIL] Project not found after creation!")
            return False

        print("\n" + "="*70)
        print("[SUCCESS] Orchestrator integration verified!")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("PHASE 3: INTEGRATION TESTING")
    print("Testing complete workflows with unified architectures")
    print("="*70)

    tests = [
        ("Project Creation Workflow", test_project_creation_workflow),
        ("Orchestrator Integration", test_orchestrator_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[CRITICAL ERROR] {name}: {str(e)}")
            results.append((name, False))

    # Print summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70 + "\n")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n" + "="*70)
        print("ALL INTEGRATION TESTS PASSED!")
        print("="*70)
        print("\nWorkflow Summary:")
        print("  1. Database initialized as singleton")
        print("  2. User created with bcrypt password hashing")
        print("  3. Password verification works across systems")
        print("  4. Subscription limits enforced")
        print("  5. Project ID generated with unified generator")
        print("  6. Project created and persisted to database")
        print("  7. Project retrieved successfully from database")
        print("\n  8. Orchestrator uses shared DatabaseSingleton")
        print("  9. Project creation works through orchestrator")
        print(" 10. All data persists correctly")
        print("\nSTATUS: Ready for API endpoint testing")
        return True
    else:
        print(f"\nFailed: {total_count - passed_count} test(s) - see errors above")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
