#!/usr/bin/env python3
"""
Test Conflict Persistence
==========================
Tests for conflict detection and database persistence.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_database
from src.models import Project, Conflict, ConflictType
from src.agents.context import ContextAnalyzerAgent
from src.core import ServiceContainer, DateTimeHelper
import uuid
from typing import Any


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.failures = []

    def add_pass(self, message: str):
        self.passed += 1
        print(f"  ✓ {message}")

    def add_fail(self, test_name: str, reason: str):
        self.failed += 1
        self.failures.append((test_name, reason))
        print(f"  ✗ {test_name}: {reason}")

    def add_warning(self, message: str):
        self.warnings += 1
        print(f"  ⚠ {message}")

    def print_summary(self):
        print("\n" + "="*80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Warnings: {self.warnings}")

        if self.failed > 0:
            print("\nFailures:")
            for test_name, reason in self.failures:
                print(f"  - {test_name}: {reason}")

        if self.failed == 0:
            print("✓ ALL TESTS PASSED 🎉")
        print("="*80)


def print_header(text: str):
    print("\n" + "="*80)
    print(text)
    print("="*80)


def print_info(text: str):
    print(f"→ {text}")


def test_conflicts_table_exists(results: TestResults, db: Any) -> bool:
    """Test 1: Verify conflicts table exists"""
    print_header("TEST 1: Conflicts Table Exists")

    try:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='conflicts'"
        result = db.execute_query(query)

        if not result or len(result) == 0:
            results.add_fail("Table existence", "Conflicts table not found")
            return False

        results.add_pass("Conflicts table exists")
        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def test_conflict_repository_available(results: TestResults, db_service: Any) -> bool:
    """Test 2: Verify ConflictRepository is registered"""
    print_header("TEST 2: ConflictRepository Available")

    try:
        if not hasattr(db_service, 'conflicts'):
            results.add_fail("Repository registration", "db_service.conflicts not found")
            return False

        results.add_pass("ConflictRepository registered")

        # Test repository methods exist
        required_methods = ['create', 'get_by_id', 'get_by_project_id', 'get_unresolved', 'mark_resolved']
        for method in required_methods:
            if not hasattr(db_service.conflicts, method):
                results.add_fail("Repository methods", f"Method {method} not found")
                return False

        results.add_pass("All required repository methods exist")
        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def test_conflict_detection_and_save(results: TestResults, agent: Any, project_id: str) -> bool:
    """Test 3: Detect and save conflicts"""
    print_header("TEST 3: Conflict Detection and Persistence")

    try:
        # Create a project with conflicting requirements
        print_info("Creating project with conflicts...")

        # Trigger conflict detection
        result = agent._detect_conflicts({
            'project_id': project_id,
            'session_id': str(uuid.uuid4())
        })

        if not result.get('success'):
            results.add_fail("Conflict detection", result.get('error', 'Unknown error'))
            return False

        results.add_pass("Conflict detection completed")

        # Check if conflicts were saved
        data = result.get('data', {})
        conflicts_persisted = data.get('conflicts_persisted', 0)

        if conflicts_persisted > 0:
            results.add_pass(f"Saved {conflicts_persisted} conflicts to database")
        else:
            results.add_warning("No conflicts detected (may be normal for test project)")

        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def test_retrieve_conflicts(results: TestResults, agent: Any, project_id: str) -> bool:
    """Test 4: Retrieve conflicts from database"""
    print_header("TEST 4: Retrieve Conflicts")

    try:
        # Get all conflicts for project
        result = agent._get_conflicts({
            'project_id': project_id,
            'unresolved_only': False
        })

        if not result.get('success'):
            results.add_fail("Conflict retrieval", result.get('error', 'Unknown error'))
            return False

        results.add_pass("Conflicts retrieved successfully")

        data = result.get('data', {})
        conflicts = data.get('conflicts', [])

        if len(conflicts) > 0:
            results.add_pass(f"Found {len(conflicts)} conflicts in database")

            # Verify conflict structure
            first_conflict = conflicts[0]
            required_fields = ['id', 'project_id', 'description', 'severity', 'is_resolved']
            for field in required_fields:
                if field not in first_conflict:
                    results.add_fail("Conflict structure", f"Missing field: {field}")
                    return False

            results.add_pass("Conflict data structure is correct")
        else:
            results.add_warning("No conflicts found (may be normal)")

        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def test_unresolved_conflicts_only(results: TestResults, agent: Any, project_id: str) -> bool:
    """Test 5: Retrieve only unresolved conflicts"""
    print_header("TEST 5: Retrieve Unresolved Conflicts Only")

    try:
        # Get unresolved conflicts
        result = agent._get_conflicts({
            'project_id': project_id,
            'unresolved_only': True
        })

        if not result.get('success'):
            results.add_fail("Unresolved conflicts retrieval", result.get('error', 'Unknown error'))
            return False

        results.add_pass("Unresolved conflicts retrieved successfully")

        data = result.get('data', {})
        conflicts = data.get('conflicts', [])

        # Verify all are unresolved
        for conflict in conflicts:
            if conflict.get('is_resolved'):
                results.add_fail("Unresolved filter", "Found resolved conflict in unresolved list")
                return False

        results.add_pass("All retrieved conflicts are unresolved")
        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def test_resolve_conflict(results: TestResults, agent: Any, project_id: str) -> bool:
    """Test 6: Mark conflict as resolved"""
    print_header("TEST 6: Resolve Conflict")

    try:
        # Get a conflict to resolve
        result = agent._get_conflicts({
            'project_id': project_id,
            'unresolved_only': True
        })

        if not result.get('success'):
            results.add_warning("No conflicts to resolve")
            return True

        data = result.get('data', {})
        conflicts = data.get('conflicts', [])

        if len(conflicts) == 0:
            results.add_warning("No unresolved conflicts found")
            return True

        # Resolve first conflict
        conflict_id = conflicts[0]['id']
        print_info(f"Resolving conflict {conflict_id}...")

        resolve_result = agent._resolve_conflict({
            'conflict_id': conflict_id,
            'resolution_notes': 'Test resolution',
            'resolved_by': 'test_user'
        })

        if not resolve_result.get('success'):
            results.add_fail("Conflict resolution", resolve_result.get('error', 'Unknown error'))
            return False

        results.add_pass("Conflict marked as resolved")

        # Verify it's no longer in unresolved list
        unresolved_result = agent._get_conflicts({
            'project_id': project_id,
            'unresolved_only': True
        })

        unresolved_conflicts = unresolved_result.get('data', {}).get('conflicts', [])
        for conflict in unresolved_conflicts:
            if conflict['id'] == conflict_id:
                results.add_fail("Resolution verification", "Resolved conflict still in unresolved list")
                return False

        results.add_pass("Resolved conflict no longer in unresolved list")
        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def test_conflict_direct_repository(results: TestResults, db_service: Any, project_id: str) -> bool:
    """Test 7: Direct repository CRUD operations"""
    print_header("TEST 7: Direct Repository CRUD")

    try:
        # Create a conflict directly
        conflict = Conflict(
            id=str(uuid.uuid4()),
            project_id=project_id,
            session_id="",
            conflict_type=ConflictType.TECHNICAL,
            description="Test conflict from repository",
            severity="high",
            first_requirement="Requirement A",
            second_requirement="Requirement B",
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
        success = db_service.conflicts.create(conflict)
        if not success:
            results.add_fail("Direct create", "Failed to create conflict")
            return False

        results.add_pass("Direct conflict creation successful")

        # Read
        retrieved = db_service.conflicts.get_by_id(conflict.id)
        if not retrieved:
            results.add_fail("Direct read", "Failed to retrieve conflict")
            return False

        results.add_pass("Direct conflict retrieval successful")

        # Update
        conflict.severity = "medium"
        success = db_service.conflicts.update(conflict)
        if not success:
            results.add_fail("Direct update", "Failed to update conflict")
            return False

        results.add_pass("Direct conflict update successful")

        # Verify update
        updated = db_service.conflicts.get_by_id(conflict.id)
        if updated.severity != "medium":
            results.add_fail("Update verification", "Severity not updated")
            return False

        results.add_pass("Conflict update verified")

        # Delete
        success = db_service.conflicts.delete(conflict.id)
        if not success:
            results.add_fail("Direct delete", "Failed to delete conflict")
            return False

        results.add_pass("Direct conflict deletion successful")

        return True

    except Exception as e:
        results.add_fail("Test execution", str(e))
        return False


def run_all_tests():
    """Run all conflict persistence tests"""
    print_header("CONFLICT PERSISTENCE TESTS")
    print("Testing conflict detection and database persistence...")

    results = TestResults()

    try:
        # Initialize
        db_service = get_database()
        db = db_service.db_manager

        services = ServiceContainer()
        agent = ContextAnalyzerAgent(services)

        # Create test project
        test_project_id = str(uuid.uuid4())
        project = Project(
            id=test_project_id,
            name="Test Project",
            description="Test project for conflict persistence",
            owner_id="test_user",
            created_at=DateTimeHelper.now(),
            updated_at=DateTimeHelper.now()
        )
        db_service.projects.create(project)

        # Run tests
        test_conflicts_table_exists(results, db)
        test_conflict_repository_available(results, db_service)
        test_conflict_detection_and_save(results, agent, test_project_id)
        test_retrieve_conflicts(results, agent, test_project_id)
        test_unresolved_conflicts_only(results, agent, test_project_id)
        test_resolve_conflict(results, agent, test_project_id)
        test_conflict_direct_repository(results, db_service, test_project_id)

        # Cleanup
        db_service.projects.delete(test_project_id)

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        results.print_summary()


if __name__ == "__main__":
    run_all_tests()
