#!/usr/bin/env python3
"""
Database Migration Verification Script

Verifies that:
1. Projects with legacy collaborators are properly migrated
2. Team members are assigned correct RBAC roles
3. Role hierarchy is properly enforced
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from socratic_system.models.project import ProjectContext
from socratic_system.models.role import TeamMemberRole, VALID_ROLES
from socrates_api.auth.project_access import ROLE_HIERARCHY


def test_migration_with_collaborators():
    """Test that legacy collaborators are migrated to team_members with correct roles"""
    print("\n" + "="*70)
    print("TEST 1: Legacy Collaborator Migration")
    print("="*70)

    # Create a project with legacy collaborators
    project = ProjectContext(
        project_id="test_proj_001",
        name="Test Project",
        owner="alice",
        phase="discovery",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        collaborators=["bob", "charlie"]  # Legacy collaborators
    )

    # Trigger migration via __post_init__ (already called by dataclass)
    print(f"Project: {project.project_id}")
    print(f"Owner: {project.owner}")
    print(f"Legacy collaborators: {project.collaborators}")
    print(f"\nMigrated team_members:")

    if not project.team_members:
        print("  [FAILED] team_members is empty!")
        return False

    all_correct = True
    for member in project.team_members:
        role_valid = member.role in VALID_ROLES
        print(f"  - {member.username}: {member.role} {'[PASS]' if role_valid else '[FAIL] INVALID'}")

        # Check specific role assignments
        if member.username == "alice" and member.role != "owner":
            print(f"    [FAIL] Owner should have 'owner' role, got '{member.role}'")
            all_correct = False
        elif member.username in ["bob", "charlie"] and member.role != "editor":
            print(f"    [FAIL] Collaborators should have 'editor' role, got '{member.role}'")
            all_correct = False

    if all_correct:
        print("\n[PASS] Migration successful: All roles correctly assigned")
    else:
        print("\n[FAIL] Migration failed: Some roles are incorrect")

    return all_correct


def test_role_hierarchy():
    """Test that role hierarchy is properly defined"""
    print("\n" + "="*70)
    print("TEST 2: Role Hierarchy Validation")
    print("="*70)

    print(f"Defined hierarchy:")
    for role, level in sorted(ROLE_HIERARCHY.items(), key=lambda x: x[1], reverse=True):
        print(f"  {role}: level {level}")

    # Verify expected hierarchy
    expected = {
        "owner": 3,
        "editor": 2,
        "viewer": 1
    }

    all_correct = True
    for role, level in expected.items():
        if ROLE_HIERARCHY.get(role) != level:
            print(f"[FAIL] {role} should be level {level}, got {ROLE_HIERARCHY.get(role)}")
            all_correct = False

    if all_correct:
        print("\n[PASS] Hierarchy is correct")
    else:
        print("\n[FAIL] Hierarchy validation failed")

    return all_correct


def test_new_project_without_collaborators():
    """Test that new projects (no legacy collaborators) still get owner in team_members"""
    print("\n" + "="*70)
    print("TEST 3: New Project Owner Assignment")
    print("="*70)

    # Create a new project without collaborators
    project = ProjectContext(
        project_id="test_proj_002",
        name="New Project",
        owner="dave",
        phase="discovery",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print(f"Project: {project.project_id}")
    print(f"Owner: {project.owner}")
    print(f"Team members:")

    if not project.team_members:
        print("  [FAILED] team_members is empty!")
        return False

    # Check that owner is in team_members
    owner_found = False
    owner_correct = False

    for member in project.team_members:
        print(f"  - {member.username}: {member.role}")
        if member.username == "dave":
            owner_found = True
            owner_correct = member.role == "owner"

    if not owner_found:
        print("[FAIL] Owner not found in team_members")
        return False

    if not owner_correct:
        print("[FAIL] Owner has wrong role")
        return False

    print("[PASS] Owner correctly added to team_members")
    return True


def test_role_levels_for_access_control():
    """Test that role levels work correctly for access control"""
    print("\n" + "="*70)
    print("TEST 4: Role-Based Access Control")
    print("="*70)

    test_cases = [
        ("owner", "editor", True, "owner should have access to editor features"),
        ("owner", "owner", True, "owner should have access to owner features"),
        ("editor", "viewer", True, "editor should have access to viewer features"),
        ("editor", "owner", False, "editor should NOT have access to owner features"),
        ("viewer", "editor", False, "viewer should NOT have access to editor features"),
        ("viewer", "viewer", True, "viewer should have access to viewer features"),
    ]

    all_correct = True
    for user_role, min_required, should_pass, description in test_cases:
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(min_required, 0)
        has_access = user_level >= required_level

        status = "[PASS]" if has_access == should_pass else "[FAIL]"
        print(f"{status} {description}")

        if has_access != should_pass:
            print(f"   Expected: {should_pass}, Got: {has_access}")
            print(f"   User level: {user_level} ({user_role}), Required: {required_level} ({min_required})")
            all_correct = False

    if all_correct:
        print("\n[PASS] All access control tests passed")
    else:
        print("\n[FAIL] Some access control tests failed")

    return all_correct


def test_serialization():
    """Test that team members can be serialized and deserialized"""
    print("\n" + "="*70)
    print("TEST 5: Team Member Serialization")
    print("="*70)

    member = TeamMemberRole(
        username="test_user",
        role="editor",
        skills=["python", "testing"],
        joined_at=datetime.now(timezone.utc)
    )

    # Test to_dict
    member_dict = member.to_dict()
    print(f"Serialized: {json.dumps(member_dict, indent=2)}")

    # Test from_dict
    reconstructed = TeamMemberRole.from_dict(member_dict)
    print(f"Deserialized: {reconstructed}")

    if reconstructed.username == member.username and reconstructed.role == member.role:
        print("[PASS] Serialization/deserialization works correctly")
        return True
    else:
        print("[FAIL] Serialization/deserialization failed")
        return False


def main():
    """Run all verification tests"""
    print("\n" + "DATABASE MIGRATION VERIFICATION")
    print("=" * 70)

    results = []

    # Run all tests
    results.append(("Legacy Collaborator Migration", test_migration_with_collaborators()))
    results.append(("Role Hierarchy", test_role_hierarchy()))
    results.append(("New Project Owner", test_new_project_without_collaborators()))
    results.append(("Access Control", test_role_levels_for_access_control()))
    results.append(("Serialization", test_serialization()))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All verification tests passed!")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
