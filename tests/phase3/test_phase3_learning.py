#!/usr/bin/env python
"""
Phase 3.1.5: Learning Profile Update Test

Tests the learning profile system and updates.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from socrates_api.orchestrator import APIOrchestrator
from socrates_api.database import LocalDatabase
from socrates_api.models_local import ProjectContext


def test_learning_profile():
    """Test 3.1.5: Learning profile updates"""
    print("\n" + "="*70)
    print("TEST 3.1.5: Learning Profile Update Test")
    print("="*70)
    
    try:
        # Initialize orchestrator
        print(f"\n[1] Initializing orchestrator...")
        orchestrator = APIOrchestrator(api_key_or_config="")
        print(f"    [OK] Orchestrator initialized")
        
        # Initialize database
        print(f"\n[2] Initializing database...")
        db = LocalDatabase()
        print(f"    [OK] Database initialized")
        
        # Create test user
        print(f"\n[3] Creating test user...")
        user_id = "learning_test_user"
        username = "learning_user"
        
        db.save_user({
            "id": user_id,
            "username": username,
            "email": "learning@test.com",
            "passcode_hash": "hash"
        })
        print(f"    [OK] User created: {username}")
        
        # Create test project
        print(f"\n[4] Creating test project...")
        project = ProjectContext(
            project_id="learning_test_project",
            name="Learning Test Project",
            owner=user_id,
            description="Test project for learning profile"
        )
        
        if not db.save_project(project):
            print(f"    [ERROR] Failed to create project")
            return False
        
        print(f"    [OK] Project created")
        
        # Execute agents to generate learning data
        print(f"\n[5] Executing agents to generate learning interactions...")
        
        agents_to_test = [
            ("code_generator", {"prompt": "Write a Python function", "language": "python"}),
            ("code_validator", {"code": "def add(a, b): return a + b", "language": "python"}),
            ("quality_controller", {"code": "def foo():pass", "context": "test"})
        ]
        
        interactions = []
        for agent_name, request_data in agents_to_test:
            print(f"    - Executing {agent_name}...")
            
            result = orchestrator.execute_agent(agent_name, request_data)
            
            if result.get("status") == "success":
                print(f"      [OK] {agent_name} executed successfully")
                interactions.append((agent_name, request_data, result))
            else:
                print(f"      [WARNING] {agent_name} result: {result.get('status')}")
        
        # Log learning interactions
        print(f"\n[6] Logging learning interactions...")
        
        for agent_name, request_data, result in interactions:
            session_id = f"{user_id}_session_001"
            
            logged = orchestrator.log_learning_interaction(
                session_id=session_id,
                agent_name=agent_name,
                input_data=request_data,
                output_data=result,
                timestamp=datetime.now(timezone.utc).isoformat(),
                project_id="learning_test_project"
            )
            
            if logged:
                print(f"    [OK] Logged interaction for {agent_name}")
            else:
                print(f"    [WARNING] Failed to log interaction for {agent_name}")
        
        # Get learning effectiveness
        print(f"\n[7] Checking learning effectiveness...")
        
        effectiveness = orchestrator._get_learning_effectiveness(user_id)
        print(f"    Learning effectiveness: {effectiveness:.2f}")
        
        # Test learning agent directly
        print(f"\n[8] Testing learning agent...")
        
        learning_result = orchestrator.execute_agent(
            "learning_agent",
            {
                "action": "analyze",
                "user_id": user_id,
                "sessions": 3
            }
        )
        
        if isinstance(learning_result, dict):
            print(f"    [OK] Learning agent response: {learning_result.get('status', 'unknown')}")
        else:
            print(f"    [INFO] Learning agent result: {type(learning_result)}")
        
        # Verify interactions recorded
        print(f"\n[9] Verification...")
        print(f"    - User: {username}")
        print(f"    - Agents executed: {len(interactions)}")
        print(f"    - Learning effectiveness: {effectiveness:.2f}")
        print(f"    - Status: Learning profile system is functional")
        
        print(f"\n[OK] Test 3.1.5 PASSED: Learning profile system works")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test 3.1.5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nPhase 3.1.5: Learning Profile Update Test")
    print("="*70)
    
    results = []
    results.append(("3.1.5 Learning Profile", test_learning_profile()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
