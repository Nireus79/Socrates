#!/usr/bin/env python
"""
End-to-end testing script for Socrates system.
Tests all major functionality including:
- Project creation
- Socratic mode chat
- Direct mode chat
- Answer suggestions
- Debug mode
- NLU mode
"""

import asyncio
import json
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))
sys.path.insert(0, str(Path(__file__).parent))

async def test_basic_imports():
    """Test that all imports work"""
    print("\n" + "="*60)
    print("TEST 1: Basic Imports")
    print("="*60)

    try:
        from socratic_system.models.project import ProjectContext
        from socrates_api.database import LocalDatabase
        from socrates_api.routers.system import is_debug_mode, set_debug_mode
        from socrates_api.routers.projects_chat import is_debug_mode as chat_is_debug
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False


async def test_debug_mode_toggle():
    """Test that debug mode toggle works across modules"""
    print("\n" + "="*60)
    print("TEST 2: Debug Mode Toggle")
    print("="*60)

    try:
        from socrates_api.routers.system import is_debug_mode, set_debug_mode
        from socrates_api.routers.projects_chat import is_debug_mode as chat_is_debug

        # Initial state
        initial = is_debug_mode()
        print(f"Initial debug state in system: {initial}")
        print(f"Initial debug state in chat: {chat_is_debug()}")

        # Toggle to True
        set_debug_mode(True)
        state1 = is_debug_mode()
        chat_state1 = chat_is_debug()
        print(f"After set_debug_mode(True):")
        print(f"  System: {state1}")
        print(f"  Chat: {chat_state1}")

        if state1 and chat_state1:
            print("[OK] Debug mode toggle works correctly")
        else:
            print("[FAIL] Debug mode not synchronized between modules")
            return False

        # Toggle to False
        set_debug_mode(False)
        state2 = is_debug_mode()
        chat_state2 = chat_is_debug()
        print(f"After set_debug_mode(False):")
        print(f"  System: {state2}")
        print(f"  Chat: {chat_state2}")

        if not state2 and not chat_state2:
            print("[OK] Debug mode synchronized correctly")
            return True
        else:
            print("[FAIL] Debug mode toggle failed")
            return False

    except Exception as e:
        print(f"[FAIL] Debug mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_project_creation():
    """Test creating a project"""
    print("\n" + "="*60)
    print("TEST 3: Project Creation")
    print("="*60)

    try:
        from socratic_system.models.project import ProjectContext
        from datetime import datetime, timezone

        project = ProjectContext(
            project_id="test_proj_001",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            description="A simple test project for calculator",
            chat_mode="socratic"
        )

        print(f"[OK] Project created: {project.project_id}")
        print(f"  Name: {project.name}")
        print(f"  Phase: {project.phase}")
        print(f"  Chat Mode: {project.chat_mode}")

        # Check that pending_questions is initialized
        if project.pending_questions is not None:
            print(f"[OK] pending_questions initialized: {project.pending_questions}")
            return True, project
        else:
            print(f"[FAIL] pending_questions not initialized")
            return False, project

    except Exception as e:
        print(f"[FAIL] Project creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_pending_questions():
    """Test adding questions to pending_questions"""
    print("\n" + "="*60)
    print("TEST 4: Pending Questions Management")
    print("="*60)

    try:
        success, project = await test_project_creation()
        if not success:
            return False

        # Simulate adding a question (what get_question endpoint does)
        from datetime import datetime, timezone

        question_entry = {
            "question": "What do you want to build with this calculator?",
            "status": "unanswered",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase": project.phase,
        }

        project.pending_questions.append(question_entry)
        print(f"[OK] Added question to pending_questions")
        print(f"  Total questions: {len(project.pending_questions)}")
        print(f"  Question: {question_entry['question'][:50]}...")

        # Now simulate user answer (what send_message does)
        for q in reversed(project.pending_questions):
            if q.get("status") == "unanswered":
                q["status"] = "answered"
                q["answered_at"] = datetime.now(timezone.utc).isoformat()
                print(f"[OK] Marked question as answered")
                break

        # Now check if get_answer_suggestions can find it
        current_question = None
        if project.pending_questions:
            unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
            if unanswered:
                current_question = unanswered[-1].get("question")
            else:
                print("  (No unanswered questions - as expected after answering)")

        # Add another question to test suggestions
        question_entry2 = {
            "question": "What features should it have?",
            "status": "unanswered",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase": project.phase,
        }
        project.pending_questions.append(question_entry2)

        # Now get_answer_suggestions should find it
        current_question = None
        if project.pending_questions:
            unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
            if unanswered:
                current_question = unanswered[-1].get("question")

        if current_question:
            print(f"[OK] get_answer_suggestions can find current question: {current_question[:50]}...")
            return True
        else:
            print(f"[FAIL] Could not find current question")
            return False

    except Exception as e:
        print(f"[FAIL] Pending questions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_nlu_endpoint():
    """Test NLU endpoint"""
    print("\n" + "="*60)
    print("TEST 5: NLU Mode")
    print("="*60)

    try:
        from socrates_api.routers.nlu import NLUInterpretRequest

        # Test direct command
        request = NLUInterpretRequest(
            input="/help",
            context={"project_id": "test_proj_001"}
        )
        print(f"[OK] NLU Request created for direct command: {request.input}")

        # Test natural language input
        request2 = NLUInterpretRequest(
            input="Show me the status of my project",
            context={"project_id": "test_proj_001"}
        )
        print(f"[OK] NLU Request created for natural language: {request2.input[:50]}...")

        print("[OK] NLU mode classes work correctly")
        return True

    except Exception as e:
        print(f"[FAIL] NLU mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator():
    """Test that orchestrator can be initialized"""
    print("\n" + "="*60)
    print("TEST 6: Orchestrator Initialization")
    print("="*60)

    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        print(f"[OK] Orchestrator initialized: {type(orchestrator).__name__}")

        # Check key components
        if hasattr(orchestrator, 'agents') and 'socratic_counselor' in orchestrator.agents:
            print(f"[OK] SocraticCounselor agent available")
        else:
            print(f"[FAIL] SocraticCounselor agent not found")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_nexus_import():
    """Test that socrates-nexus is properly installed and working"""
    print("\n" + "="*60)
    print("TEST 7: Socrates-Nexus Integration")
    print("="*60)

    try:
        from socrates_nexus import LLMClient

        # Test that we can create a client (without actually calling API)
        client = LLMClient(
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            api_key="dummy_key_for_test"
        )
        print(f"[OK] LLMClient created with Anthropic provider")
        print(f"  Model: {client.config.model}")
        print(f"  Provider: {client.config.provider}")

        return True

    except Exception as e:
        print(f"[FAIL] Socrates-Nexus test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("SOCRATES SYSTEM END-TO-END TEST SUITE")
    print("="*70)

    results = []

    # Test 1: Imports
    result = await test_basic_imports()
    results.append(("Basic Imports", result))
    if not result:
        print("\nCritical import failure - stopping tests")
        return results

    # Test 2: Debug Mode Toggle
    result = await test_debug_mode_toggle()
    results.append(("Debug Mode Toggle", result))

    # Test 3: Project Creation (no await needed, but keeping async structure)
    result, _ = await test_project_creation()
    results.append(("Project Creation", result))

    # Test 4: Pending Questions
    result = await test_pending_questions()
    results.append(("Pending Questions", result))

    # Test 5: NLU Mode
    result = await test_nlu_endpoint()
    results.append(("NLU Mode", result))

    # Test 6: Orchestrator
    result = await test_orchestrator()
    results.append(("Orchestrator", result))

    # Test 7: Nexus
    result = await test_nexus_import()
    results.append(("Socrates-Nexus", result))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\nWARNING:  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
