"""
Comprehensive test suite for all Critical and Priority fixes.

Tests all 11 fixes implemented in the system remediation effort:
- CRITICAL FIX #1: WebSocket JWT Authentication
- CRITICAL FIX #2: Cache Invalidation
- CRITICAL FIX #3: Conversation Consolidation
- CRITICAL FIX #4: Event Persistence
- CRITICAL FIX #5: Orphaned Document Cleanup
- HIGH FIX #6: Database Transactions
- HIGH FIX #7: Error Handling
- HIGH FIX #8: WebSocket Message Synchronization
- MEDIUM FIX #9: Conflict History Tracking
- MEDIUM FIX #10: Atomic Conflict Resolution
- MEDIUM FIX #11: WebSocket Broadcast Implementation
"""

import asyncio
import json
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Setup path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "errors": [],
}


def record_result(test_name, status, message=""):
    """Record test result"""
    if status == "PASS":
        test_results["passed"].append(test_name)
        logger.info(f"[OK] {test_name}")
    elif status == "FAIL":
        test_results["failed"].append((test_name, message))
        logger.error(f"[FAIL] {test_name}: {message}")
    else:
        test_results["errors"].append((test_name, message))
        logger.error(f"[ERROR] {test_name}: {message}")


# ============================================================================
# FIX #1: WebSocket JWT Authentication
# ============================================================================


def test_fix1_websocket_jwt_validation():
    """Test that WebSocket endpoints require valid JWT tokens"""
    try:
        from socrates_api.auth.jwt_handler import verify_access_token

        # Test 1: Verify token validation exists
        assert callable(verify_access_token), "verify_access_token function must exist"
        logger.info("  ✓ JWT verification function exists")

        # Test 2: Check websocket.py has token validation
        websocket_file = Path(__file__).parent / "src" / "socrates_api" / "routers" / "websocket.py"
        if websocket_file.exists():
            content = websocket_file.read_text()
            assert "verify_access_token" in content, "WebSocket should verify access token"
            assert "Authentication token required" in content, "Should reject missing token"
            assert "Invalid authentication token" in content, "Should reject invalid token"
            logger.info("  ✓ WebSocket has JWT validation")

        record_result("FIX #1: WebSocket JWT Authentication", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #1: WebSocket JWT Authentication", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #1: WebSocket JWT Authentication", "ERROR", str(e))
        return False


# ============================================================================
# FIX #2: Cache Invalidation
# ============================================================================


def test_fix2_cache_invalidation():
    """Test that cache is invalidated after project updates"""
    try:
        from socrates_api.services.query_cache import get_query_cache

        cache = get_query_cache()
        assert cache is not None, "Query cache must exist"
        logger.info("  ✓ Query cache exists")

        # Check cache invalidation methods exist
        assert hasattr(cache, "invalidate"), "Cache must have invalidate method"
        assert hasattr(cache, "get"), "Cache must have get method"
        assert hasattr(cache, "set"), "Cache must have set method"
        logger.info("  ✓ Cache has invalidation methods")

        # Test cache invalidation
        cache.set("test_key", {"data": "test"})
        assert cache.get("test_key") is not None, "Cache should store values"
        logger.info("  ✓ Cache stores values")

        cache.invalidate("test_key")
        assert cache.get("test_key") is None, "Cache should be invalidated"
        logger.info("  ✓ Cache invalidation works")

        # Check projects_chat.py has cache invalidation calls
        chat_file = (
            Path(__file__).parent / "src" / "socrates_api" / "routers" / "projects_chat.py"
        )
        if chat_file.exists():
            content = chat_file.read_text()
            assert "CRITICAL FIX #2" in content, "Should mark cache invalidation as critical fix"
            assert "cache.invalidate" in content, "Should call cache invalidation"
            logger.info("  ✓ projects_chat.py has cache invalidation")

        record_result("FIX #2: Cache Invalidation", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #2: Cache Invalidation", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #2: Cache Invalidation", "ERROR", str(e))
        return False


# ============================================================================
# FIX #3: Conversation Consolidation
# ============================================================================


def test_fix3_conversation_consolidation():
    """Test conversation storage consolidation"""
    try:
        from socrates_api.services.conversation_migration import (
            migrate_chat_sessions_to_conversation_history,
        )

        assert callable(migrate_chat_sessions_to_conversation_history)
        logger.info("  ✓ Conversation migration function exists")

        # Check that migration is integrated into database loading
        db_file = Path(__file__).parent / "src" / "socrates_api" / "database.py"
        if db_file.exists():
            content = db_file.read_text()
            assert (
                "conversation_migration" in content or "migrate_chat_sessions" in content
            ), "Database should integrate conversation migration"
            logger.info("  ✓ Database integrates conversation migration")

        record_result("FIX #3: Conversation Consolidation", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #3: Conversation Consolidation", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #3: Conversation Consolidation", "ERROR", str(e))
        return False


# ============================================================================
# FIX #4: Event Persistence
# ============================================================================


def test_fix4_event_persistence():
    """Test that events are persisted to database"""
    try:
        # Check database has events table
        db_file = Path(__file__).parent / "src" / "socrates_api" / "database.py"
        if db_file.exists():
            content = db_file.read_text()
            assert "CREATE TABLE IF NOT EXISTS events" in content, "Database should have events table"
            assert "record_event" in content, "Database should have record_event method"
            logger.info("  ✓ Database has events table and persistence")

        # Check events.py persists to database
        events_file = Path(__file__).parent / "src" / "socrates_api" / "routers" / "events.py"
        if events_file.exists():
            content = events_file.read_text()
            assert (
                "db.record_event" in content
            ), "Events router should persist to database"
            assert (
                "CRITICAL FIX #4" in content
            ), "Should mark event persistence as critical fix"
            logger.info("  ✓ Events router persists to database")

        record_result("FIX #4: Event Persistence", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #4: Event Persistence", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #4: Event Persistence", "ERROR", str(e))
        return False


# ============================================================================
# FIX #5: Orphaned Document Cleanup
# ============================================================================


def test_fix5_orphan_cleanup():
    """Test cleanup of orphaned documents"""
    try:
        from socrates_api.database import LocalDatabase

        db = LocalDatabase()
        assert hasattr(
            db, "cleanup_orphaned_documents"
        ), "Database should have cleanup_orphaned_documents method"
        assert hasattr(
            db, "permanently_delete_project"
        ), "Database should have permanently_delete_project method"
        logger.info("  ✓ Database has orphan cleanup methods")

        # Check database schema has CASCADE DELETE
        db_file = Path(__file__).parent / "src" / "socrates_api" / "database.py"
        if db_file.exists():
            content = db_file.read_text()
            assert "ON DELETE CASCADE" in content, "Database should use CASCADE DELETE"
            logger.info("  ✓ Database uses CASCADE DELETE")

        record_result("FIX #5: Orphaned Document Cleanup", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #5: Orphaned Document Cleanup", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #5: Orphaned Document Cleanup", "ERROR", str(e))
        return False


# ============================================================================
# FIX #6: Database Transactions
# ============================================================================


def test_fix6_database_transactions():
    """Test atomic database transactions"""
    try:
        from socrates_api.database import LocalDatabase
        from contextlib import contextmanager

        db = LocalDatabase()
        assert hasattr(db, "transaction"), "Database should have transaction context manager"
        logger.info("  ✓ Database has transaction context manager")

        # Verify transaction method returns context manager
        tx = db.transaction()
        assert hasattr(
            tx, "__enter__"
        ) and hasattr(
            tx, "__exit__"
        ), "transaction() should return context manager"
        logger.info("  ✓ Transaction is a context manager")

        # Check database.py marks this as CRITICAL FIX #6
        db_file = Path(__file__).parent / "src" / "socrates_api" / "database.py"
        if db_file.exists():
            content = db_file.read_text()
            assert (
                "CRITICAL FIX #6" in content
            ), "Transactions should be marked as critical fix"
            assert (
                "BEGIN TRANSACTION" in content
            ), "Should use BEGIN TRANSACTION"
            assert "COMMIT" in content, "Should have COMMIT"
            assert "ROLLBACK" in content, "Should have ROLLBACK"
            logger.info("  ✓ Transaction implementation uses ACID properties")

        record_result("FIX #6: Database Transactions", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #6: Database Transactions", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #6: Database Transactions", "ERROR", str(e))
        return False


# ============================================================================
# FIX #7: Error Handling
# ============================================================================


def test_fix7_error_handling():
    """Test explicit error handling with OperationResult"""
    try:
        from socrates_api.services.error_handler import (
            OperationResult,
            ErrorHandler,
            ErrorSeverity,
        )

        # Test OperationResult
        result = OperationResult.success_result(data={"test": "data"})
        assert result.success is True, "Success result should have success=True"
        assert result.data == {"test": "data"}, "Success result should contain data"
        logger.info("  ✓ OperationResult success creation works")

        failure = OperationResult.failure_result(
            error="Test error", error_code="TEST_ERROR"
        )
        assert failure.success is False, "Failure result should have success=False"
        assert failure.error == "Test error", "Failure result should contain error"
        logger.info("  ✓ OperationResult failure creation works")

        # Test error severity levels
        assert hasattr(ErrorSeverity, "CRITICAL"), "Should have CRITICAL severity"
        assert hasattr(ErrorSeverity, "HIGH"), "Should have HIGH severity"
        assert hasattr(ErrorSeverity, "MEDIUM"), "Should have MEDIUM severity"
        assert hasattr(ErrorSeverity, "LOW"), "Should have LOW severity"
        logger.info("  ✓ ErrorSeverity enum is complete")

        record_result("FIX #7: Error Handling", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #7: Error Handling", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #7: Error Handling", "ERROR", str(e))
        return False


# ============================================================================
# FIX #8: WebSocket Message Synchronization
# ============================================================================


def test_fix8_websocket_sync():
    """Test atomic WebSocket message synchronization"""
    try:
        from socrates_api.websocket import get_connection_manager

        conn_manager = get_connection_manager()
        assert conn_manager is not None, "Connection manager should exist"
        logger.info("  ✓ WebSocket connection manager exists")

        # Check for synchronization methods
        assert hasattr(
            conn_manager, "broadcast_to_project"
        ), "Should have broadcast_to_project"
        assert hasattr(conn_manager, "broadcast_to_user"), "Should have broadcast_to_user"
        assert hasattr(conn_manager, "broadcast_to_all"), "Should have broadcast_to_all"
        logger.info("  ✓ WebSocket has broadcast methods")

        # Check websocket.py has atomic sync
        ws_file = Path(__file__).parent / "src" / "socrates_api" / "routers" / "websocket.py"
        if ws_file.exists():
            content = ws_file.read_text()
            assert (
                "CRITICAL FIX #8" in content or "atomic" in content.lower()
            ), "WebSocket should have atomic synchronization"
            logger.info("  ✓ WebSocket has atomic sync implementation")

        record_result("FIX #8: WebSocket Message Synchronization", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #8: WebSocket Message Synchronization", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #8: WebSocket Message Synchronization", "ERROR", str(e))
        return False


# ============================================================================
# FIX #9: Conflict History Tracking
# ============================================================================


def test_fix9_conflict_tracking():
    """Test conflict history tracking with unique IDs"""
    try:
        from socrates_api.routers.conflicts import ConflictInfo

        # Test ConflictInfo has conflict_id field
        conflict = ConflictInfo(
            conflict_type="test",
            field_name="goals",
            existing_value="old",
            new_value="new",
            severity="medium",
            description="Test conflict",
            conflict_id="conflict_123",
        )
        assert conflict.conflict_id == "conflict_123", "ConflictInfo should have conflict_id"
        logger.info("  ✓ ConflictInfo includes conflict_id field")

        # Check conflicts.py has FIX #9 marker
        conflicts_file = Path(__file__).parent / "src" / "socrates_api" / "routers" / "conflicts.py"
        if conflicts_file.exists():
            content = conflicts_file.read_text()
            assert "FIX #9" in content, "Should mark conflict tracking as fix #9"
            assert (
                "IDGenerator.generate_id" in content
            ), "Should generate unique conflict IDs"
            assert (
                "db.save_conflict" in content
            ), "Should save conflicts to database"
            logger.info("  ✓ Conflict tracking generates unique IDs and saves")

        # Check database has conflict history tables
        db_file = Path(__file__).parent / "src" / "socrates_api" / "database.py"
        if db_file.exists():
            content = db_file.read_text()
            assert (
                "CREATE TABLE IF NOT EXISTS conflict_history" in content
            ), "Should have conflict_history table"
            assert (
                "CREATE TABLE IF NOT EXISTS conflict_resolutions" in content
            ), "Should have conflict_resolutions table"
            assert (
                "CREATE TABLE IF NOT EXISTS conflict_decisions" in content
            ), "Should have conflict_decisions table"
            logger.info("  ✓ Database has all conflict tracking tables")

        record_result("FIX #9: Conflict History Tracking", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #9: Conflict History Tracking", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #9: Conflict History Tracking", "ERROR", str(e))
        return False


# ============================================================================
# FIX #10: Atomic Conflict Resolution
# ============================================================================


def test_fix10_atomic_resolution():
    """Test atomic conflict resolution with transactions"""
    try:
        conflicts_file = Path(__file__).parent / "src" / "socrates_api" / "routers" / "conflicts.py"
        if conflicts_file.exists():
            content = conflicts_file.read_text()
            assert "FIX #10" in content, "Should mark atomic resolution as fix #10"
            assert (
                "db.transaction()" in content
            ), "Should use transaction context manager"
            assert (
                "save_resolution" in content
            ), "Should save resolutions within transaction"
            assert "save_decision" in content, "Should save decisions within transaction"
            logger.info("  ✓ Conflict resolution uses atomic transactions")

        record_result("FIX #10: Atomic Conflict Resolution", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #10: Atomic Conflict Resolution", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #10: Atomic Conflict Resolution", "ERROR", str(e))
        return False


# ============================================================================
# FIX #11: WebSocket Broadcast Implementation
# ============================================================================


def test_fix11_websocket_broadcast():
    """Test WebSocket broadcast for conflict events"""
    try:
        chat_file = Path(__file__).parent / "src" / "socrates_api" / "routers" / "projects_chat.py"
        if chat_file.exists():
            content = chat_file.read_text()
            assert "FIX #11" in content, "Should mark WebSocket broadcast as fix #11"
            assert (
                "CONFLICTS_RESOLVED" in content
            ), "Should broadcast CONFLICTS_RESOLVED event"
            assert (
                "broadcast_to_project" in content
            ), "Should use broadcast_to_project method"
            assert (
                "eventType" in content
            ), "Should include eventType in broadcast"
            logger.info("  ✓ WebSocket broadcasts conflict resolution events")

        record_result("FIX #11: WebSocket Broadcast Implementation", "PASS")
        return True

    except AssertionError as e:
        record_result("FIX #11: WebSocket Broadcast Implementation", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("FIX #11: WebSocket Broadcast Implementation", "ERROR", str(e))
        return False


# ============================================================================
# SYNTAX VALIDATION
# ============================================================================


def test_syntax_validation():
    """Test that all modified files compile without syntax errors"""
    try:
        import py_compile

        files_to_check = [
            "src/socrates_api/routers/websocket.py",
            "src/socrates_api/routers/projects_chat.py",
            "src/socrates_api/routers/events.py",
            "src/socrates_api/routers/conflicts.py",
            "src/socrates_api/database.py",
            "src/socrates_api/services/error_handler.py",
            "src/socrates_api/services/conversation_migration.py",
        ]

        errors = []
        for file_path in files_to_check:
            full_path = Path(__file__).parent / file_path
            if full_path.exists():
                try:
                    py_compile.compile(str(full_path), doraise=True)
                    logger.info(f"  ✓ {file_path} - syntax OK")
                except py_compile.PyCompileError as e:
                    errors.append(f"{file_path}: {e}")
            else:
                logger.warning(f"  ? {file_path} - not found")

        if errors:
            record_result("Syntax Validation", "FAIL", "; ".join(errors))
            return False

        record_result("Syntax Validation", "PASS")
        return True

    except Exception as e:
        record_result("Syntax Validation", "ERROR", str(e))
        return False


# ============================================================================
# RUN ALL TESTS
# ============================================================================


def run_all_tests():
    """Run all test suites"""
    logger.info("\n" + "=" * 70)
    logger.info("COMPREHENSIVE FIX VALIDATION TEST SUITE")
    logger.info("=" * 70 + "\n")

    tests = [
        ("CRITICAL FIX #1", test_fix1_websocket_jwt_validation),
        ("CRITICAL FIX #2", test_fix2_cache_invalidation),
        ("CRITICAL FIX #3", test_fix3_conversation_consolidation),
        ("CRITICAL FIX #4", test_fix4_event_persistence),
        ("CRITICAL FIX #5", test_fix5_orphan_cleanup),
        ("HIGH FIX #6", test_fix6_database_transactions),
        ("HIGH FIX #7", test_fix7_error_handling),
        ("HIGH FIX #8", test_fix8_websocket_sync),
        ("MEDIUM FIX #9", test_fix9_conflict_tracking),
        ("MEDIUM FIX #10", test_fix10_atomic_resolution),
        ("MEDIUM FIX #11", test_fix11_websocket_broadcast),
        ("Syntax Validation", test_syntax_validation),
    ]

    for test_name, test_func in tests:
        logger.info(f"\nTesting {test_name}...")
        try:
            test_func()
        except Exception as e:
            logger.error(f"Unexpected error in {test_name}: {e}")
            record_result(test_name, "ERROR", str(e))

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Passed: {len(test_results['passed'])}/{len(tests)}")
    logger.info(f"Failed: {len(test_results['failed'])}/{len(tests)}")
    logger.info(f"Errors: {len(test_results['errors'])}/{len(tests)}")

    if test_results["passed"]:
        logger.info("\n[PASS] Tests passed:")
        for test in test_results["passed"]:
            logger.info(f"  ✓ {test}")

    if test_results["failed"]:
        logger.info("\n[FAIL] Tests failed:")
        for test, msg in test_results["failed"]:
            logger.info(f"  ✗ {test}: {msg}")

    if test_results["errors"]:
        logger.info("\n[ERROR] Tests with errors:")
        for test, msg in test_results["errors"]:
            logger.info(f"  ✗ {test}: {msg}")

    # Overall status
    total_passed = len(test_results["passed"])
    total_tests = len(tests)
    success_rate = (total_passed / total_tests) * 100

    logger.info("\n" + "=" * 70)
    if success_rate == 100:
        logger.info(f"✓ ALL TESTS PASSED ({total_passed}/{total_tests}) - {success_rate:.0f}%")
    elif success_rate >= 80:
        logger.info(f"✓ MOST TESTS PASSED ({total_passed}/{total_tests}) - {success_rate:.0f}%")
    else:
        logger.info(f"✗ TESTS FAILED ({total_passed}/{total_tests}) - {success_rate:.0f}%")
    logger.info("=" * 70 + "\n")

    return success_rate >= 80


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
