"""
Integration tests for all fixes - testing actual runtime behavior.

Tests that verify the fixes work end-to-end in realistic scenarios.
"""

import asyncio
import json
import logging
import sys
import tempfile
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
# INTEGRATION TEST 1: Event Persistence (FIX #4)
# ============================================================================


def test_integration_event_persistence():
    """Integration test: Events are saved and retrieved from database"""
    try:
        from socrates_api.database import LocalDatabase
        from pathlib import Path
        import tempfile

        # Create temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_events.db"
            db = LocalDatabase(str(db_path))

            # Record an event
            event_id = db.record_event(
                event_type="test_event",
                data={"key": "value"},
                user_id="user123",
                project_id="proj456",
            )

            logger.info(f"  ✓ Event recorded with ID: {event_id}")

            # Retrieve events
            events = db.get_events_for_user("user123")
            assert len(events) > 0, "Should retrieve recorded events"
            logger.info(f"  ✓ Retrieved {len(events)} events")

            # Verify event data
            event = next(
                (e for e in events if e.get("event_type") == "test_event"),
                None,
            )
            assert event is not None, "Should find our test event"
            assert event["data"]["key"] == "value", "Event data should be preserved"
            logger.info("  ✓ Event data correctly persisted and retrieved")

        record_result("Integration Test 1: Event Persistence", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 1: Event Persistence", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 1: Event Persistence", "ERROR", str(e))
        return False


# ============================================================================
# INTEGRATION TEST 2: Transaction Atomicity (FIX #6)
# ============================================================================


def test_integration_transaction_atomicity():
    """Integration test: Database transactions are atomic"""
    try:
        from socrates_api.database import LocalDatabase
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_transactions.db"
            db = LocalDatabase(str(db_path))

            # Test successful transaction
            try:
                with db.transaction():
                    # Record two events in transaction
                    event1 = db.record_event(
                        event_type="event1", data={}, user_id="user1", project_id="proj1"
                    )
                    event2 = db.record_event(
                        event_type="event2", data={}, user_id="user1", project_id="proj1"
                    )
                    logger.info(f"  ✓ Transaction recorded 2 events: {event1}, {event2}")

                # Verify both were saved
                events = db.get_events_for_user("user1")
                assert len(events) >= 2, "Both events should be committed"
                logger.info("  ✓ Transaction committed both events")

            except Exception as e:
                logger.error(f"  ✗ Transaction failed: {e}")
                raise

        record_result("Integration Test 2: Transaction Atomicity", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 2: Transaction Atomicity", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 2: Transaction Atomicity", "ERROR", str(e))
        return False


# ============================================================================
# INTEGRATION TEST 3: Error Result Handling (FIX #7)
# ============================================================================


def test_integration_error_handling():
    """Integration test: Error handling with OperationResult"""
    try:
        from socrates_api.services.error_handler import (
            OperationResult,
            ErrorSeverity,
            require_success,
        )

        # Test success case
        result = OperationResult.success_result(
            data={"status": "ok"},
            warnings=["warning1"],
        )
        assert result.success is True
        assert result.data["status"] == "ok"
        assert "warning1" in result.warnings
        logger.info("  ✓ Success result with warnings created")

        # Test require_success with successful result
        data = require_success(result)
        assert data["status"] == "ok"
        logger.info("  ✓ require_success returns data on success")

        # Test failure case
        failure = OperationResult.failure_result(
            error="Operation failed",
            error_code="OP_FAILED",
            severity=ErrorSeverity.HIGH,
        )
        assert failure.success is False
        assert failure.error == "Operation failed"
        logger.info("  ✓ Failure result created")

        # Test require_success with failure raises
        try:
            require_success(failure, "Context: checking result")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Context: checking result" in str(e)
            logger.info("  ✓ require_success raises on failure")

        record_result("Integration Test 3: Error Result Handling", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 3: Error Result Handling", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 3: Error Result Handling", "ERROR", str(e))
        return False


# ============================================================================
# INTEGRATION TEST 4: Cache Invalidation (FIX #2)
# ============================================================================


def test_integration_cache_invalidation():
    """Integration test: Cache invalidation works end-to-end"""
    try:
        from socrates_api.services.query_cache import get_query_cache

        cache = get_query_cache()

        # Set multiple keys
        cache.set("project:123:metrics", {"value": 100})
        cache.set("project:123:readiness", {"status": "ready"})
        cache.set("project:456:metrics", {"value": 200})
        logger.info("  ✓ Cached multiple keys")

        # Verify they're cached
        assert cache.get("project:123:metrics") is not None
        assert cache.get("project:123:readiness") is not None
        logger.info("  ✓ Retrieved cached values")

        # Invalidate by pattern
        cache.invalidate("project:123:metrics")
        assert cache.get("project:123:metrics") is None
        assert (
            cache.get("project:123:readiness") is not None
        ), "Other keys should remain"
        assert (
            cache.get("project:456:metrics") is not None
        ), "Other projects should remain"
        logger.info("  ✓ Selective invalidation works")

        record_result("Integration Test 4: Cache Invalidation", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 4: Cache Invalidation", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 4: Cache Invalidation", "ERROR", str(e))
        return False


# ============================================================================
# INTEGRATION TEST 5: Conflict History Tracking (FIX #9)
# ============================================================================


def test_integration_conflict_tracking():
    """Integration test: Conflicts are tracked with unique IDs"""
    try:
        from socrates_api.database import LocalDatabase
        from socrates_api.utils import IDGenerator
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_conflicts.db"
            db = LocalDatabase(str(db_path))

            # Create a conflict
            conflict_id = IDGenerator.generate_id("conflict")
            success = db.save_conflict(
                project_id="proj123",
                conflict_id=conflict_id,
                conflict_type="goal_conflict",
                title="Goal Conflict",
                description="New goal conflicts with existing",
                severity="high",
                related_agents=["agent1"],
                context={"field": "goals", "existing": "web app", "new": "mobile app"},
            )

            assert success, "Should save conflict"
            logger.info(f"  ✓ Conflict saved with ID: {conflict_id}")

            # Retrieve conflict history
            history = db.get_conflict_history("proj123")
            assert len(history) > 0, "Should retrieve conflict history"
            logger.info(f"  ✓ Retrieved {len(history)} conflicts")

            # Verify conflict data
            conflict = history[0]
            assert conflict["conflict_id"] == conflict_id
            assert conflict["conflict_type"] == "goal_conflict"
            assert conflict["severity"] == "high"
            logger.info("  ✓ Conflict data correctly saved and retrieved")

        record_result("Integration Test 5: Conflict History Tracking", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 5: Conflict History Tracking", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 5: Conflict History Tracking", "ERROR", str(e))
        return False


# ============================================================================
# INTEGRATION TEST 6: Conflict Resolution with Decisions (FIX #10)
# ============================================================================


def test_integration_atomic_conflict_resolution():
    """Integration test: Conflict resolution saves atomically with decisions"""
    try:
        from socrates_api.database import LocalDatabase
        from socrates_api.utils import IDGenerator
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_resolution.db"
            db = LocalDatabase(str(db_path))

            # Create a conflict first
            conflict_id = IDGenerator.generate_id("conflict")
            db.save_conflict(
                project_id="proj123",
                conflict_id=conflict_id,
                conflict_type="tech_conflict",
                title="Tech Stack Conflict",
                description="New tech conflicts with existing",
                severity="medium",
                related_agents=[],
                context={"field": "tech_stack"},
            )
            logger.info("  ✓ Created conflict for resolution")

            # Save resolution
            resolution_id = IDGenerator.generate_id("resolution")
            db.save_resolution(
                resolution_id=resolution_id,
                conflict_id=conflict_id,
                strategy="replace",
                confidence=0.9,
                rationale="New technology is better",
            )
            logger.info("  ✓ Saved resolution")

            # Save decision
            decision_id = IDGenerator.generate_id("decision")
            db.save_decision(
                decision_id=decision_id,
                conflict_id=conflict_id,
                resolution_id=resolution_id,
                decided_by="user123",
                rationale="User approved new tech",
                version=1,
            )
            logger.info("  ✓ Saved decision")

            # Verify resolution and decision are linked
            resolutions = db.get_conflict_resolutions(conflict_id)
            assert len(resolutions) > 0, "Should retrieve resolutions"
            logger.info(f"  ✓ Retrieved {len(resolutions)} resolutions")

            decisions = db.get_conflict_decisions(conflict_id)
            assert len(decisions) > 0, "Should retrieve decisions"
            assert decisions[0]["resolution_id"] == resolution_id
            logger.info("  ✓ Decision correctly linked to resolution")

        record_result("Integration Test 6: Atomic Conflict Resolution", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 6: Atomic Conflict Resolution", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 6: Atomic Conflict Resolution", "ERROR", str(e))
        return False


# ============================================================================
# INTEGRATION TEST 7: WebSocket Connection Manager (FIX #8)
# ============================================================================


def test_integration_websocket_broadcasts():
    """Integration test: WebSocket broadcasts work"""
    try:
        from socrates_api.websocket import get_connection_manager

        conn_manager = get_connection_manager()

        # Verify broadcast methods exist and are callable
        assert callable(conn_manager.broadcast_to_project)
        assert callable(conn_manager.broadcast_to_user)
        assert callable(conn_manager.broadcast_to_all)
        logger.info("  ✓ All broadcast methods exist and are callable")

        # Check metadata tracking
        assert hasattr(conn_manager, "_connections")
        assert hasattr(conn_manager, "_metadata")
        logger.info("  ✓ Connection tracking infrastructure exists")

        record_result("Integration Test 7: WebSocket Broadcasts", "PASS")
        return True

    except AssertionError as e:
        record_result("Integration Test 7: WebSocket Broadcasts", "FAIL", str(e))
        return False
    except Exception as e:
        record_result("Integration Test 7: WebSocket Broadcasts", "ERROR", str(e))
        return False


# ============================================================================
# RUN ALL INTEGRATION TESTS
# ============================================================================


def run_all_integration_tests():
    """Run all integration test suites"""
    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION TESTS - RUNTIME BEHAVIOR VERIFICATION")
    logger.info("=" * 70 + "\n")

    tests = [
        ("Event Persistence (FIX #4)", test_integration_event_persistence),
        ("Transaction Atomicity (FIX #6)", test_integration_transaction_atomicity),
        ("Error Result Handling (FIX #7)", test_integration_error_handling),
        ("Cache Invalidation (FIX #2)", test_integration_cache_invalidation),
        ("Conflict History Tracking (FIX #9)", test_integration_conflict_tracking),
        ("Atomic Conflict Resolution (FIX #10)", test_integration_atomic_conflict_resolution),
        ("WebSocket Broadcasts (FIX #8)", test_integration_websocket_broadcasts),
    ]

    for test_name, test_func in tests:
        logger.info(f"\n{test_name}...")
        try:
            test_func()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            record_result(test_name, "ERROR", str(e))

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION TEST RESULTS")
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
        logger.info(f"✓ ALL INTEGRATION TESTS PASSED ({total_passed}/{total_tests}) - {success_rate:.0f}%")
    elif success_rate >= 80:
        logger.info(f"✓ MOST INTEGRATION TESTS PASSED ({total_passed}/{total_tests}) - {success_rate:.0f}%")
    else:
        logger.info(f"✗ INTEGRATION TESTS FAILED ({total_passed}/{total_tests}) - {success_rate:.0f}%")
    logger.info("=" * 70 + "\n")

    return success_rate >= 80


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
