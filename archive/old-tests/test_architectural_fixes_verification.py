"""
Test Suite to Verify Phase 1 & 2 Architectural Fixes

Tests that the architectural fixes have been properly implemented:
- Fix #7: Removed owner field from CreateProjectRequest
- Fix #5: Removed password hashing fallback
- Fix #4: ProjectIDGenerator for consistent IDs
- Fix #3: DatabaseSingleton for shared database
- Fix #2: get_current_user_object() dependencies
- Fix #1: create_project uses orchestrator pattern
"""

import sys
import os

# Add paths
sys.path.insert(0, ".")
sys.path.insert(0, "socrates-api/src")

def test_fix_7_removed_owner_field():
    """Test: CreateProjectRequest no longer has owner field"""
    print("\n" + "="*70)
    print("FIX #7: CreateProjectRequest model updated")
    print("="*70)

    try:
        from socrates_api.models import CreateProjectRequest
        from pydantic import ValidationError

        # Try to create request with owner field (should fail)
        try:
            request = CreateProjectRequest(
                name="Test Project",
                owner="alice",  # This field should not be accepted
                description="Test"
            )
            print("[FAIL] CreateProjectRequest still accepts 'owner' field!")
            return False
        except ValidationError as e:
            if "owner" in str(e):
                print("[PASS] CreateProjectRequest correctly rejects 'owner' field")
                print(f"       Error: {str(e)[:80]}...")
                return True
            raise

        # Try without owner field (should succeed)
        request = CreateProjectRequest(
            name="Test Project",
            description="Test"
        )
        print("[PASS] CreateProjectRequest works without 'owner' field")
        return True

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def test_fix_5_no_password_fallback():
    """Test: CLI imports password functions directly from API"""
    print("\n" + "="*70)
    print("FIX #5: Password hashing unified (no fallback)")
    print("="*70)

    try:
        from socratic_system.ui.commands.user_commands import hash_password, verify_password
        from socrates_api.auth.password import hash_password as api_hash, verify_password as api_verify

        # Verify they're the same functions
        if hash_password is api_hash and verify_password is api_verify:
            print("[PASS] CLI imports password functions directly from API")
            print("       hash_password and verify_password are identical")
            return True
        else:
            print("[FAIL] Password functions don't match!")
            return False

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def test_fix_4_project_id_generator():
    """Test: ProjectIDGenerator exists and works"""
    print("\n" + "="*70)
    print("FIX #4: ProjectIDGenerator for consistent IDs")
    print("="*70)

    try:
        from socratic_system.utils.id_generator import ProjectIDGenerator

        # Generate IDs
        id1 = ProjectIDGenerator.generate("alice")
        id2 = ProjectIDGenerator.generate("bob")

        # Check format
        if id1.startswith("proj_") and id2.startswith("proj_"):
            print(f"[PASS] ProjectIDGenerator creates consistent format")
            print(f"       Example: {id1}")

            # Verify they're different
            if id1 != id2:
                print("[PASS] Different users get different IDs")
                return True
            else:
                print("[FAIL] IDs are identical!")
                return False
        else:
            print(f"[FAIL] Invalid ID format: {id1}, {id2}")
            return False

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def test_fix_3_database_singleton():
    """Test: DatabaseSingleton exists and works"""
    print("\n" + "="*70)
    print("FIX #3: DatabaseSingleton for shared database")
    print("="*70)

    try:
        from socrates_api.database import DatabaseSingleton, get_database

        # Get instance twice
        db1 = DatabaseSingleton.get_instance()
        db2 = DatabaseSingleton.get_instance()

        # Verify they're the same instance
        if db1 is db2:
            print("[PASS] DatabaseSingleton returns same instance")
            print(f"       Instance type: {type(db1).__name__}")

            # Verify get_database() also returns same instance
            db3 = get_database()
            if db3 is db1:
                print("[PASS] get_database() returns DatabaseSingleton instance")
                return True
            else:
                print("[FAIL] get_database() returns different instance!")
                return False
        else:
            print("[FAIL] DatabaseSingleton returns different instances!")
            return False

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def test_fix_2_user_object_dependency():
    """Test: get_current_user_object() exists"""
    print("\n" + "="*70)
    print("FIX #2: get_current_user_object() dependency")
    print("="*70)

    try:
        from socrates_api.auth import get_current_user_object, get_current_user_object_optional
        import inspect

        # Check function signatures
        sig1 = inspect.signature(get_current_user_object)
        sig2 = inspect.signature(get_current_user_object_optional)

        print("[PASS] get_current_user_object() exists")
        print(f"       Params: {list(sig1.parameters.keys())}")

        print("[PASS] get_current_user_object_optional() exists")
        print(f"       Params: {list(sig2.parameters.keys())}")

        # Check return type annotations
        if "User" in str(sig1.return_annotation):
            print("[PASS] get_current_user_object returns User object")
            return True
        else:
            print("[FAIL] get_current_user_object return type unclear")
            return False

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def test_fix_1_create_project_uses_orchestrator():
    """Test: create_project endpoint uses orchestrator pattern"""
    print("\n" + "="*70)
    print("FIX #1: create_project endpoint uses orchestrator pattern")
    print("="*70)

    try:
        import inspect
        from socrates_api.routers.projects import create_project

        # Get source code
        source = inspect.getsource(create_project)

        # Check for orchestrator.process_request call
        if "orchestrator.process_request" in source:
            print("[PASS] create_project uses orchestrator.process_request()")

            # Check for agent name
            if '"project_manager"' in source or "'project_manager'" in source:
                print("[PASS] Uses 'project_manager' agent")

                # Check for action
                if '"create_project"' in source or "'create_project'" in source:
                    print("[PASS] Uses correct action name")
                    return True
        else:
            print("[FAIL] create_project doesn't use orchestrator pattern!")
            return False

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def test_orchestrator_uses_singleton():
    """Test: Orchestrator uses DatabaseSingleton"""
    print("\n" + "="*70)
    print("BONUS: Orchestrator integration with DatabaseSingleton")
    print("="*70)

    try:
        import inspect
        from socratic_system.orchestration.orchestrator import AgentOrchestrator

        # Get source of __init__
        source = inspect.getsource(AgentOrchestrator.__init__)

        # Check for DatabaseSingleton usage
        if "DatabaseSingleton" in source:
            print("[PASS] Orchestrator uses DatabaseSingleton")
            if "initialize" in source:
                print("[PASS] Orchestrator calls DatabaseSingleton.initialize()")
            if "get_instance" in source:
                print("[PASS] Orchestrator calls DatabaseSingleton.get_instance()")
            return True
        else:
            print("[FAIL] Orchestrator doesn't use DatabaseSingleton!")
            return False

    except Exception as e:
        print(f"[FAIL] {str(e)}")
        return False


def main():
    """Run all fix verification tests"""
    print("\n" + "="*70)
    print("ARCHITECTURAL FIXES VERIFICATION TEST SUITE")
    print("="*70)

    tests = [
        ("Fix #7: CreateProjectRequest.owner removed", test_fix_7_removed_owner_field),
        ("Fix #5: Password hashing unified", test_fix_5_no_password_fallback),
        ("Fix #4: ProjectIDGenerator implemented", test_fix_4_project_id_generator),
        ("Fix #3: DatabaseSingleton implemented", test_fix_3_database_singleton),
        ("Fix #2: get_current_user_object created", test_fix_2_user_object_dependency),
        ("Fix #1: create_project uses orchestrator", test_fix_1_create_project_uses_orchestrator),
        ("Bonus: Orchestrator uses DatabaseSingleton", test_orchestrator_uses_singleton),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[ERROR] {name}: {str(e)}")
            results.append((name, False))

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70 + "\n")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n[SUCCESS] ALL ARCHITECTURAL FIXES VERIFIED!")
        print("\nThe following have been successfully implemented:")
        print("  [OK] Fix #7: Removed owner field from CreateProjectRequest")
        print("  [OK] Fix #5: Unified password hashing (no fallback)")
        print("  [OK] Fix #4: ProjectIDGenerator for consistency")
        print("  [OK] Fix #3: DatabaseSingleton for shared database")
        print("  [OK] Fix #2: get_current_user_object() dependency")
        print("  [OK] Fix #1: create_project uses orchestrator pattern")
        print("  [OK] Orchestrator integration with DatabaseSingleton")
        return True
    else:
        print(f"\n[FAIL] {total_count - passed_count} test(s) failed - review above for details")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
