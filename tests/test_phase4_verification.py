"""
Phase 4 Implementation Verification Test
Verifies that automatic knowledge enrichment system is fully integrated
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import gc
import os
import shutil
import tempfile
import time

from socratic_system.config import SocratesConfig
from socratic_system.events import EventType
from socratic_system.orchestration.orchestrator import AgentOrchestrator


def test_phase4_complete_workflow():
    """Test complete Phase 4 workflow: Agent suggests knowledge -> Orchestrator routes to knowledge_manager -> Manager approves"""
    tmpdir = tempfile.mkdtemp()
    try:
        config = SocratesConfig(
            api_key="test-key",
            data_dir=tmpdir,
            projects_db_path=os.path.join(tmpdir, "projects.db"),
            vector_db_path=os.path.join(tmpdir, "vector_db"),
            knowledge_base_path=None,
        )

        orchestrator = AgentOrchestrator(config)
        project_id = "default"  # Knowledge manager defaults to 'default' project if not specified

        # Simulate: CodeGeneratorAgent detects missing knowledge and suggests enrichment
        print("\n[STEP 1] Simulating agent knowledge suggestion...")

        # Emit knowledge suggestion directly with project_id
        orchestrator.code_generator.emit_event(
            EventType.KNOWLEDGE_SUGGESTION,
            {
                "content": "Transformer architectures use attention mechanisms to process sequences in parallel",
                "category": "machine_learning",
                "topic": "transformers",
                "difficulty": "advanced",
                "reason": "insufficient_context",
                "project_id": project_id,
            },
        )

        # Allow event to propagate
        time.sleep(0.2)

        # Verify suggestion was collected
        print("[STEP 2] Verifying knowledge manager collected suggestion...")
        result = orchestrator.process_request(
            "knowledge_manager",
            {"action": "get_suggestions", "project_id": project_id, "status": "pending"},
        )

        assert result["status"] == "success", "Knowledge manager should return success"
        pending_count = result["count"]
        print(f"   Found {pending_count} pending suggestion(s)")

        # Also verify direct queue status
        print("[STEP 3] Checking queue status...")
        status_result = orchestrator.process_request(
            "knowledge_manager", {"action": "get_queue_status", "project_id": project_id}
        )
        assert status_result["status"] == "success"
        assert status_result["pending"] > 0, "Should have pending suggestions"
        print(
            f"   Queue: {status_result['pending']} pending, {status_result['approved']} approved, {status_result['rejected']} rejected"
        )

        # Approve a suggestion
        if result["count"] > 0:
            print("[STEP 4] Approving suggestion...")
            suggestion = result["suggestions"][0]
            suggestion_id = suggestion["id"]

            approve_result = orchestrator.process_request(
                "knowledge_manager",
                {
                    "action": "approve_suggestion",
                    "project_id": project_id,
                    "suggestion_id": suggestion_id,
                },
            )
            assert approve_result["status"] == "success"
            print(f"   Approved: {approve_result['message']}")

        # Verify project knowledge was added
        print("[STEP 5] Verifying project knowledge was added to vector DB...")
        project_knowledge = orchestrator.vector_db.get_project_knowledge(project_id)
        print(f"   Project now has {len(project_knowledge)} knowledge entries")
        assert len(project_knowledge) > 0, "Project should have knowledge after approval"

        # Test rejection workflow
        print("[STEP 6] Testing rejection workflow...")
        orchestrator.socratic_counselor.emit_event(
            EventType.KNOWLEDGE_SUGGESTION,
            {
                "content": "Socratic method uses questioning to develop understanding",
                "category": "pedagogy",
                "topic": "socratic_method",
                "difficulty": "intermediate",
                "reason": "pattern_detected",
                "project_id": project_id,
            },
        )

        time.sleep(0.2)

        # Get pending suggestions
        result = orchestrator.process_request(
            "knowledge_manager",
            {"action": "get_suggestions", "project_id": project_id, "status": "pending"},
        )

        if result["count"] > 0:
            suggestion_id = result["suggestions"][0]["id"]
            reject_result = orchestrator.process_request(
                "knowledge_manager",
                {
                    "action": "reject_suggestion",
                    "project_id": project_id,
                    "suggestion_id": suggestion_id,
                },
            )
            assert reject_result["status"] == "success"
            print(f"   Rejected suggestion: {suggestion_id}")

        # Final queue status
        print("[STEP 7] Final queue status...")
        final_status = orchestrator.process_request(
            "knowledge_manager", {"action": "get_queue_status", "project_id": project_id}
        )
        print(
            f"   Final: {final_status['pending']} pending, {final_status['approved']} approved, {final_status['rejected']} rejected"
        )

        print("\n[OK] Phase 4 complete workflow test PASSED!")
        print("     - Agents can suggest knowledge")
        print("     - KnowledgeManagerAgent collects suggestions via events")
        print("     - Suggestions can be approved/rejected")
        print("     - Project knowledge is properly stored")

        del orchestrator
        gc.collect()

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except:
            pass


def test_agent_has_suggest_method():
    """Verify all agents have suggest_knowledge_addition method"""
    tmpdir = tempfile.mkdtemp()
    try:
        config = SocratesConfig(
            api_key="test-key",
            data_dir=tmpdir,
            projects_db_path=os.path.join(tmpdir, "projects.db"),
            vector_db_path=os.path.join(tmpdir, "vector_db"),
            knowledge_base_path=None,
        )

        orchestrator = AgentOrchestrator(config)

        print("\n[VERIFY] Checking that all agents have knowledge suggestion capability...")
        agents_to_check = [
            orchestrator.code_generator,
            orchestrator.socratic_counselor,
            orchestrator.context_analyzer,
            orchestrator.project_manager,
        ]

        for agent in agents_to_check:
            assert hasattr(
                agent, "suggest_knowledge_addition"
            ), f"{agent.name} missing suggest_knowledge_addition method"
            print(f"   [OK] {agent.name} has suggest_knowledge_addition")

        del orchestrator
        gc.collect()

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except:
            pass


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PHASE 4: AUTOMATIC KNOWLEDGE ENRICHMENT VERIFICATION")
    print("=" * 70)

    try:
        test_agent_has_suggest_method()
        test_phase4_complete_workflow()

        print("\n" + "=" * 70)
        print("ALL PHASE 4 VERIFICATION TESTS PASSED")
        print("=" * 70 + "\n")

    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
