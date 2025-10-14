#!/usr/bin/env python3
"""Test Conflict Persistence"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import initialize_package
from src.database import get_database
from src.agents.context import ContextAnalyzerAgent
from src.models import Project, ProjectStatus, Conflict, ConflictType
from src.core import DateTimeHelper
import uuid


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def add_pass(self, msg):
        self.passed += 1
        print(f"  [PASS] {msg}")

    def add_fail(self, name, error):
        self.failed += 1
        print(f"  [FAIL] {name}: {error}")

    def print_summary(self):
        print(f"\nTotal: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        if self.failed == 0:
            print("[PASS] ALL TESTS PASSED!")


def test_table_exists(results, db):
    print("\nTEST 1: Conflicts Table Exists")
    try:
        result = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conflicts'"
        )
        if result:
            results.add_pass("Conflicts table exists")
            return True
        else:
            results.add_fail("Table check", "Table not found")
            return False
    except Exception as e:
        results.add_fail("Table check", str(e))
        return False


def test_repository_available(results, db_service):
    print("\nTEST 2: ConflictRepository Available")
    try:
        if not hasattr(db_service, 'conflicts'):
            results.add_fail("Repository", "db_service.conflicts not found")
            return False

        results.add_pass("ConflictRepository registered")

        methods = ['create', 'get_by_id', 'get_by_project_id', 'get_unresolved', 'mark_resolved']
        for method in methods:
            if hasattr(db_service.conflicts, method):
                results.add_pass(f"{method}() exists")
            else:
                results.add_fail("Methods", f"{method}() missing")
                return False

        return True
    except Exception as e:
        results.add_fail("Repository check", str(e))
        return False


def test_conflict_detection(results, agent, project_id, user_id):
    print("\nTEST 3: Conflict Detection and Save")
    try:
        result = agent._detect_conflicts({
            'user_id': user_id,
            'project_id': project_id,
            'session_id': str(uuid.uuid4())
        })

        if not result.get('success'):
            results.add_fail("Detection", result.get('error', 'Unknown'))
            return False

        results.add_pass("Conflict detection completed")

        conflicts_persisted = result.get('data', {}).get('conflicts_persisted', 0)
        results.add_pass(f"Saved {conflicts_persisted} conflicts")

        return True
    except Exception as e:
        results.add_fail("Detection", str(e))
        return False


def test_retrieve_conflicts(results, agent, project_id, user_id):
    print("\nTEST 4: Retrieve Conflicts")
    try:
        result = agent._get_conflicts({
            'user_id': user_id,
            'project_id': project_id,
            'unresolved_only': False
        })

        if not result.get('success'):
            results.add_fail("Retrieval", result.get('error', 'Unknown'))
            return False

        results.add_pass("Conflicts retrieved")

        conflicts = result.get('data', {}).get('conflicts', [])
        results.add_pass(f"Found {len(conflicts)} conflicts")

        if len(conflicts) > 0:
            required = ['id', 'project_id', 'description', 'severity', 'is_resolved']
            for field in required:
                if field not in conflicts[0]:
                    results.add_fail("Structure", f"Missing {field}")
                    return False
            results.add_pass("Conflict structure correct")

        return True
    except Exception as e:
        results.add_fail("Retrieval", str(e))
        return False


def test_unresolved_only(results, agent, project_id, user_id):
    print("\nTEST 5: Unresolved Conflicts Only")
    try:
        result = agent._get_conflicts({
            'user_id': user_id,
            'project_id': project_id,
            'unresolved_only': True
        })

        if not result.get('success'):
            results.add_fail("Unresolved query", result.get('error', 'Unknown'))
            return False

        results.add_pass("Unresolved conflicts retrieved")

        conflicts = result.get('data', {}).get('conflicts', [])
        for c in conflicts:
            if c.get('is_resolved'):
                results.add_fail("Filter", "Found resolved in unresolved list")
                return False

        results.add_pass("All conflicts unresolved")
        return True
    except Exception as e:
        results.add_fail("Unresolved query", str(e))
        return False


def test_resolve_conflict(results, agent, project_id, user_id):
    print("\nTEST 6: Resolve Conflict")
    try:
        result = agent._get_conflicts({
            'user_id': user_id,
            'project_id': project_id,
            'unresolved_only': True
        })

        conflicts = result.get('data', {}).get('conflicts', [])
        if len(conflicts) == 0:
            results.add_pass("No conflicts to resolve (OK)")
            return True

        conflict_id = conflicts[0]['id']

        resolve_result = agent._resolve_conflict({
            'user_id': user_id,
            'conflict_id': conflict_id,
            'resolution_notes': 'Test resolution',
            'resolved_by': 'test_user'
        })

        if not resolve_result.get('success'):
            results.add_fail("Resolution", resolve_result.get('error', 'Unknown'))
            return False

        results.add_pass("Conflict resolved")

        # Verify not in unresolved list
        check = agent._get_conflicts({
            'user_id': user_id,
            'project_id': project_id,
            'unresolved_only': True
        })

        unresolved = check.get('data', {}).get('conflicts', [])
        for c in unresolved:
            if c['id'] == conflict_id:
                results.add_fail("Verification", "Still in unresolved list")
                return False

        results.add_pass("Resolution verified")
        return True
    except Exception as e:
        results.add_fail("Resolution", str(e))
        return False


def test_direct_crud(results, db_service, project_id):
    print("\nTEST 7: Direct Repository CRUD")
    try:
        conflict = Conflict(
            id=str(uuid.uuid4()),
            project_id=project_id,
            session_id="",
            conflict_type=ConflictType.TECHNICAL,
            description="Test conflict",
            severity="high",
            first_requirement="A",
            second_requirement="B",
            conflicting_roles=[],
            is_resolved=False,
            resolution_strategy="",
            resolution_notes="",
            resolved_by=None,
            resolved_at=None,
            affected_modules=[],
            estimated_impact_hours=None,
            created_at=DateTimeHelper.now(),
            updated_at=DateTimeHelper.now()
        )

        # Create
        if not db_service.conflicts.create(conflict):
            results.add_fail("Create", "Failed")
            return False
        results.add_pass("Create successful")

        # Read
        retrieved = db_service.conflicts.get_by_id(conflict.id)
        if not retrieved:
            results.add_fail("Read", "Failed")
            return False
        results.add_pass("Read successful")

        # Update
        conflict.severity = "medium"
        if not db_service.conflicts.update(conflict):
            results.add_fail("Update", "Failed")
            return False
        results.add_pass("Update successful")

        # Verify
        updated = db_service.conflicts.get_by_id(conflict.id)
        if updated.severity != "medium":
            results.add_fail("Verify", "Update not reflected")
            return False
        results.add_pass("Update verified")

        # Delete
        if not db_service.conflicts.delete(conflict.id):
            results.add_fail("Delete", "Failed")
            return False
        results.add_pass("Delete successful")

        return True
    except Exception as e:
        results.add_fail("CRUD", str(e))
        return False


def main():
    print("=" * 70)
    print("CONFLICT PERSISTENCE TESTS")
    print("=" * 70)

    results = TestResults()

    try:
        # Initialize with fresh database
        from src.database import reset_database
        from src.models import User, UserStatus, UserRole

        reset_database()
        services = initialize_package()
        db_service = get_database()
        agent = ContextAnalyzerAgent(services)

        # Create test user for authentication
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username="test_user",
            email="test@example.com",
            password_hash="dummy",
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
        db_service.users.create(user)

        # Create test project
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name="Conflict Test",
            description="Test",
            owner_id=user_id,
            status=ProjectStatus.DRAFT
        )
        db_service.projects.create(project)

        # Run tests
        test_table_exists(results, db_service.db_manager)
        test_repository_available(results, db_service)
        test_conflict_detection(results, agent, project_id, user_id)
        test_retrieve_conflicts(results, agent, project_id, user_id)
        test_unresolved_only(results, agent, project_id, user_id)
        test_resolve_conflict(results, agent, project_id, user_id)
        test_direct_crud(results, db_service, project_id)

        # Cleanup
        db_service.projects.delete(project_id)
        db_service.users.delete(user_id)

    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()

    results.print_summary()


if __name__ == "__main__":
    main()
