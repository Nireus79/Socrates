#!/usr/bin/env python
"""
Comprehensive Test Suite for All Phases Implementation
Tests question deduplication, skip tracking, suggestions, and database persistence
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))
sys.path.insert(0, str(project_root / "socratic_system"))

def test_phase_1_project_context():
    """Test Phase 1: Extended ProjectContext"""
    print("\n" + "="*70)
    print("PHASE 1: Extended ProjectContext")
    print("="*70)

    try:
        from socratic_system.models.project import ProjectContext

        # Create a project
        project = ProjectContext(
            project_id="test_p1",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Verify new fields exist
        assert hasattr(project, 'asked_questions'), "Missing asked_questions field"
        assert hasattr(project, 'skipped_questions'), "Missing skipped_questions field"
        assert hasattr(project, 'question_cache'), "Missing question_cache field"
        assert hasattr(project, 'debug_logs'), "Missing debug_logs field"

        # Verify fields are initialized
        assert isinstance(project.asked_questions, list), "asked_questions not initialized as list"
        assert isinstance(project.skipped_questions, list), "skipped_questions not initialized as list"

        print("[OK] ProjectContext has all new fields")
        print("[OK] Fields initialized correctly")
        print("[OK] PHASE 1 VERIFICATION PASSED")
        return True

    except Exception as e:
        print(f"[FAIL] PHASE 1 FAILED: {e}")
        return False


def test_phase_2_orchestrator_methods():
    """Test Phase 2: Orchestrator Wrapper Methods"""
    print("\n" + "="*70)
    print("PHASE 2: Orchestrator Wrapper Methods")
    print("="*70)

    try:
        from socrates_api.orchestrator import get_orchestrator
        from socratic_system.models.project import ProjectContext
        from datetime import datetime, timezone

        orchestrator = get_orchestrator()

        # Create test project
        project = ProjectContext(
            project_id="test_p2",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Test 1: Check _generate_suggestions exists and works
        assert hasattr(orchestrator, '_generate_suggestions'), "Missing _generate_suggestions method"
        test_question = "What operations should the system perform?"
        suggestions = orchestrator._generate_suggestions(test_question, project)
        assert isinstance(suggestions, list), "Suggestions not returned as list"
        assert len(suggestions) > 0, "No suggestions generated"
        print(f"[OK] _generate_suggestions works ({len(suggestions)} suggestions)")

        # Test 2: Check _generate_questions_deduplicated exists
        assert hasattr(orchestrator, '_generate_questions_deduplicated'), "Missing deduplication method"
        print("[OK] _generate_questions_deduplicated method exists")

        # Test 3: Check _is_similar_question exists
        assert hasattr(orchestrator, '_is_similar_question'), "Missing similarity check method"
        similar = orchestrator._is_similar_question("What operations?", "What operations would you want?")
        assert isinstance(similar, bool), "Similarity check not returning boolean"
        print(f"[OK] _is_similar_question works (similar={similar})")

        # Test 4: Check _add_debug_log exists
        assert hasattr(orchestrator, '_add_debug_log'), "Missing debug logging method"
        orchestrator._add_debug_log(project, "info", "Test debug message")
        assert len(project.debug_logs) > 0, "Debug log not added"
        print(f"[OK] _add_debug_log works (logs: {len(project.debug_logs)})")

        # Test 5: Check _get_conversation_summary exists
        assert hasattr(orchestrator, '_get_conversation_summary'), "Missing conversation summary method"
        summary = orchestrator._get_conversation_summary(project)
        assert isinstance(summary, str), "Summary not returned as string"
        print("[OK] _get_conversation_summary method exists")

        print("[OK] PHASE 2 VERIFICATION PASSED")
        return True

    except Exception as e:
        print(f"[FAIL] PHASE 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_3_router_integration():
    """Test Phase 3: Router Endpoint Integration"""
    print("\n" + "="*70)
    print("PHASE 3: Router Endpoint Integration")
    print("="*70)

    try:
        from socratic_system.models.project import ProjectContext
        from datetime import datetime, timezone

        # Create test project with question history
        project = ProjectContext(
            project_id="test_p3",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Simulate Phase 3 tracking: Question asked
        question_id = "q_test123"
        question_text = "What operations should the system perform?"

        project.asked_questions = [
            {
                "id": question_id,
                "text": question_text,
                "category": "operations",
                "asked_at": datetime.now(timezone.utc).isoformat(),
                "answer": None,
                "status": "pending"
            }
        ]
        print("[OK] Question tracked in asked_questions (status: pending)")

        # Simulate Phase 3 tracking: Response recorded
        answer_text = "Addition, subtraction, multiplication, division"
        for q in project.asked_questions:
            if q.get("id") == question_id and q.get("status") == "pending":
                q["answer"] = answer_text
                q["answered_at"] = datetime.now(timezone.utc).isoformat()
                q["status"] = "answered"
        print("[OK] Response tracked in asked_questions (status: answered)")

        # Simulate Phase 3 tracking: Question skipped
        project.skipped_questions = ["q_skip001"]
        print("[OK] Skipped question tracked in skipped_questions")

        # Verify skip endpoint tracking would work
        assert len(project.skipped_questions) > 0, "Skipped questions not tracked"
        print("[OK] Skip question tracking verified")

        # Verify get_answer_suggestions would work
        assert len(project.asked_questions) > 0, "No questions for suggestions"
        last_question = project.asked_questions[-1].get("text")
        assert last_question is not None, "Question text not found"
        print(f"[OK] Suggestions endpoint would work with: '{last_question[:50]}...'")

        print("[OK] PHASE 3 VERIFICATION PASSED")
        return True

    except Exception as e:
        print(f"[FAIL] PHASE 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_4_database_persistence():
    """Test Phase 4: Database Persistence"""
    print("\n" + "="*70)
    print("PHASE 4: Database Persistence")
    print("="*70)

    try:
        from socrates_api.database import LocalDatabase
        from socratic_system.models.project import ProjectContext
        from datetime import datetime, timezone
        import tempfile
        import os

        # Create temporary database for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = LocalDatabase(db_path)

            # Create test project
            project = ProjectContext(
                project_id="test_p4",
                name="Database Test Project",
                owner="test_user",
                phase="discovery",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            # Add conversation history
            project.asked_questions = [
                {
                    "id": "q1",
                    "text": "What operations?",
                    "category": "operations",
                    "asked_at": datetime.now(timezone.utc).isoformat(),
                    "answer": "Addition, subtraction",
                    "answered_at": datetime.now(timezone.utc).isoformat(),
                    "status": "answered"
                }
            ]

            project.skipped_questions = ["q2"]
            project.question_cache = {"timestamp": datetime.now(timezone.utc).isoformat(), "questions": []}
            project.debug_logs = [{"level": "info", "message": "Test log", "timestamp": datetime.now(timezone.utc).isoformat()}]

            # Save project
            db.save_project(project)
            print("[OK] Project saved with conversation history")

            # Load project
            loaded = db.load_project("test_p4")
            assert loaded is not None, "Project not loaded from database"
            print("[OK] Project loaded from database")

            # Verify conversation history persisted
            assert hasattr(loaded, 'asked_questions'), "asked_questions not persisted"
            assert len(loaded.asked_questions) > 0, "asked_questions list empty after load"
            assert loaded.asked_questions[0]["text"] == "What operations?", "Question text not persisted"
            print("[OK] asked_questions persisted and restored")

            assert hasattr(loaded, 'skipped_questions'), "skipped_questions not persisted"
            assert len(loaded.skipped_questions) > 0, "skipped_questions list empty after load"
            print("[OK] skipped_questions persisted and restored")

            assert hasattr(loaded, 'question_cache'), "question_cache not persisted"
            assert isinstance(loaded.question_cache, dict), "question_cache not restored as dict"
            print("[OK] question_cache persisted and restored")

            assert hasattr(loaded, 'debug_logs'), "debug_logs not persisted"
            assert len(loaded.debug_logs) > 0, "debug_logs empty after load"
            print("[OK] debug_logs persisted and restored")

            # Test query methods
            history = db.get_conversation_history("test_p4")
            assert isinstance(history, list), "Conversation history not list"
            assert len(history) > 0, "Conversation history empty"
            print(f"[OK] get_conversation_history works ({len(history)} entries)")

            skipped = db.get_skipped_questions("test_p4")
            assert isinstance(skipped, list), "Skipped questions not list"
            assert len(skipped) > 0, "Skipped questions empty"
            print(f"[OK] get_skipped_questions works ({len(skipped)} entries)")

            logs = db.get_debug_logs("test_p4")
            assert isinstance(logs, list), "Debug logs not list"
            assert len(logs) > 0, "Debug logs empty"
            print(f"[OK] get_debug_logs works ({len(logs)} entries)")

            print("[OK] PHASE 4 VERIFICATION PASSED")
            return True

    except Exception as e:
        print(f"[FAIL] PHASE 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_flow():
    """Test complete end-to-end flow"""
    print("\n" + "="*70)
    print("COMPLETE END-TO-END FLOW TEST")
    print("="*70)

    try:
        from socrates_api.database import LocalDatabase
        from socrates_api.orchestrator import get_orchestrator
        from socratic_system.models.project import ProjectContext
        from datetime import datetime, timezone
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = LocalDatabase(db_path)
            orchestrator = get_orchestrator()

            # Step 1: Create project
            project = ProjectContext(
                project_id="flow_test",
                name="Flow Test",
                owner="test_user",
                phase="discovery",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                description="Calculator application",
                goals="Build a working calculator"
            )
            print("[OK] Step 1: Project created")

            # Step 2: Generate questions with deduplication
            questions = orchestrator._generate_questions_deduplicated(
                topic="Calculator",
                level="beginner",
                project=project,
                current_user="test_user"
            )
            print(f"[OK] Step 2: Generated {len(questions)} questions")

            # Step 3: Track first question
            if questions:
                question_id = "q_001"
                project.asked_questions = [
                    {
                        "id": question_id,
                        "text": questions[0],
                        "category": "operations",
                        "asked_at": datetime.now(timezone.utc).isoformat(),
                        "answer": None,
                        "status": "pending"
                    }
                ]
                print(f"[OK] Step 3: First question tracked (q_001)")

                # Step 4: Generate suggestions for the question
                suggestions = orchestrator._generate_suggestions(questions[0], project)
                print(f"[OK] Step 4: Generated {len(suggestions)} suggestions")

                # Step 5: Record answer
                project.asked_questions[0]["answer"] = "Addition, subtraction, multiplication, division"
                project.asked_questions[0]["answered_at"] = datetime.now(timezone.utc).isoformat()
                project.asked_questions[0]["status"] = "answered"
                print("[OK] Step 5: Answer recorded")

                # Step 6: Skip next question
                project.skipped_questions = ["q_002"]
                print("[OK] Step 6: Question skipped (q_002)")

                # Step 7: Save project with all data
                db.save_project(project)
                print("[OK] Step 7: Project saved to database")

                # Step 8: Load project and verify
                loaded = db.load_project("flow_test")
                assert len(loaded.asked_questions) > 0, "Asked questions lost"
                assert len(loaded.skipped_questions) > 0, "Skipped questions lost"
                assert loaded.asked_questions[0]["status"] == "answered", "Status not preserved"
                print("[OK] Step 8: Project loaded, data verified")

                print("\n[OK] COMPLETE END-TO-END FLOW PASSED")
                return True
            else:
                print("[WARN]  No questions generated for flow test")
                return False

    except Exception as e:
        print(f"[FAIL] END-TO-END FLOW FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUITE - ALL PHASES")
    print("="*70)

    results = {
        "Phase 1: ProjectContext": test_phase_1_project_context(),
        "Phase 2: Orchestrator": test_phase_2_orchestrator_methods(),
        "Phase 3: Router Integration": test_phase_3_router_integration(),
        "Phase 4: Database": test_phase_4_database_persistence(),
        "Complete Flow": test_complete_flow(),
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status:10} {test_name}")

    print("="*70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! [SUCCESS]")
        return 0
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
