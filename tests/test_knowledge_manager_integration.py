"""
Integration tests for KnowledgeManagerAgent with orchestrator
"""

import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import gc
import os
import shutil
import tempfile

from socratic_system.config import SocratesConfig
from socratic_system.events import EventType
from socratic_system.orchestration.orchestrator import AgentOrchestrator


def test_knowledge_manager_initialization():
    """Test that KnowledgeManagerAgent initializes correctly"""
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

        # Verify knowledge_manager exists
        assert orchestrator.knowledge_manager is not None
        assert orchestrator.knowledge_manager.name == "knowledge_manager"
        assert hasattr(orchestrator.knowledge_manager, "suggestions")

        # Clean up resources
        del orchestrator
        gc.collect()

        print("[PASS] KnowledgeManagerAgent initialized successfully")
    finally:
        # Force cleanup of temp directory
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_knowledge_suggestion_collection():
    """Test that knowledge suggestions are collected from agents"""
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
        project_id = "test_project"

        # Emit a knowledge suggestion through event system
        orchestrator.event_emitter.emit(
            EventType.KNOWLEDGE_SUGGESTION,
            {
                "content": "Test knowledge content",
                "category": "test_category",
                "topic": "test_topic",
                "difficulty": "beginner",
                "reason": "insufficient_context",
                "agent": "test_agent",
                "project_id": project_id,
            },
        )

        # Small delay to ensure event is processed
        import time

        time.sleep(0.1)

        # Query suggestions
        result = orchestrator.process_request(
            "knowledge_manager",
            {"action": "get_suggestions", "project_id": project_id, "status": "pending"},
        )

        assert result["status"] == "success"
        assert result["count"] > 0
        assert len(result["suggestions"]) > 0

        suggestion = result["suggestions"][0]
        assert suggestion["content"] == "Test knowledge content"
        assert suggestion["category"] == "test_category"
        assert suggestion["status"] == "pending"

        del orchestrator
        gc.collect()

        print("[PASS] Knowledge suggestions collected correctly")
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_knowledge_suggestion_approval():
    """Test that suggestions can be approved and added to project knowledge"""
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
        project_id = "test_project"

        # Create a suggestion
        orchestrator.event_emitter.emit(
            EventType.KNOWLEDGE_SUGGESTION,
            {
                "content": "Python decorators modify function behavior",
                "category": "python_advanced",
                "topic": "decorators",
                "difficulty": "intermediate",
                "reason": "insufficient_context",
                "agent": "code_generator",
                "project_id": project_id,
            },
        )

        import time

        time.sleep(0.1)

        # Get the suggestion
        result = orchestrator.process_request(
            "knowledge_manager",
            {"action": "get_suggestions", "project_id": project_id, "status": "pending"},
        )

        assert result["count"] == 1
        suggestion_id = result["suggestions"][0]["id"]

        # Approve the suggestion
        approve_result = orchestrator.process_request(
            "knowledge_manager",
            {
                "action": "approve_suggestion",
                "project_id": project_id,
                "suggestion_id": suggestion_id,
            },
        )

        assert approve_result["status"] == "success"
        assert "Knowledge added" in approve_result["message"]

        # Verify suggestion is now approved
        queue_result = orchestrator.process_request(
            "knowledge_manager", {"action": "get_queue_status", "project_id": project_id}
        )

        assert queue_result["approved"] == 1
        assert queue_result["pending"] == 0

        del orchestrator
        gc.collect()

        print("[PASS] Knowledge suggestions approved successfully")
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_knowledge_queue_status():
    """Test queue status tracking"""
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
        project_id = "test_project"

        # Add 3 suggestions
        for i in range(3):
            orchestrator.event_emitter.emit(
                EventType.KNOWLEDGE_SUGGESTION,
                {
                    "content": f"Test content {i}",
                    "category": "test_category",
                    "topic": "test_topic",
                    "difficulty": "beginner",
                    "reason": "insufficient_context",
                    "agent": "test_agent",
                    "project_id": project_id,
                },
            )

        import time

        time.sleep(0.2)

        # Check status
        result = orchestrator.process_request(
            "knowledge_manager", {"action": "get_queue_status", "project_id": project_id}
        )

        assert result["status"] == "success"
        assert result["pending"] == 3
        assert result["total"] == 3

        del orchestrator
        gc.collect()

        print("[PASS] Queue status tracking works correctly")
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_knowledge_suggestion_rejection():
    """Test that suggestions can be rejected"""
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
        project_id = "test_project"

        # Create a suggestion
        orchestrator.event_emitter.emit(
            EventType.KNOWLEDGE_SUGGESTION,
            {
                "content": "Test content",
                "category": "test_category",
                "topic": "test_topic",
                "difficulty": "beginner",
                "reason": "insufficient_context",
                "agent": "test_agent",
                "project_id": project_id,
            },
        )

        import time

        time.sleep(0.1)

        # Get the suggestion ID
        result = orchestrator.process_request(
            "knowledge_manager",
            {"action": "get_suggestions", "project_id": project_id, "status": "pending"},
        )

        suggestion_id = result["suggestions"][0]["id"]

        # Reject the suggestion
        reject_result = orchestrator.process_request(
            "knowledge_manager",
            {
                "action": "reject_suggestion",
                "project_id": project_id,
                "suggestion_id": suggestion_id,
            },
        )

        assert reject_result["status"] == "success"

        # Verify it's now rejected
        queue_result = orchestrator.process_request(
            "knowledge_manager", {"action": "get_queue_status", "project_id": project_id}
        )

        assert queue_result["rejected"] == 1

        del orchestrator
        gc.collect()

        print("[PASS] Knowledge suggestions rejected successfully")
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    print("\n[TEST] Knowledge Manager Integration Tests\n")

    try:
        test_knowledge_manager_initialization()
        test_knowledge_suggestion_collection()
        test_knowledge_suggestion_approval()
        test_knowledge_queue_status()
        test_knowledge_suggestion_rejection()

        print("\n[OK] All integration tests passed!")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
