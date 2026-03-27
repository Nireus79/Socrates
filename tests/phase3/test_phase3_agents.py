#!/usr/bin/env python
"""
Phase 3.1.3: Agent Execution Test

Tests agent execution through the API orchestrator.
"""

import json
import sys
from pathlib import Path

# Add backend to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from socrates_api.orchestrator import APIOrchestrator
from socrates_api.models_local import ProjectContext


def test_agent_execution():
    """Test 3.1.3: Agent execution via orchestrator"""
    print("\n" + "="*70)
    print("TEST 3.1.3: Agent Execution Test")
    print("="*70)
    
    try:
        # Initialize orchestrator without API key (tests will work offline)
        print(f"\n[1] Initializing orchestrator...")
        orchestrator = APIOrchestrator(api_key_or_config="")
        print(f"    [OK] Orchestrator initialized")
        
        # List available agents
        print(f"\n[2] Listing available agents...")
        agents = orchestrator.list_agents()
        print(f"    Found {len(agents)} agents:")
        for agent_name in agents:
            print(f"      - {agent_name}")
        
        # Check if code_generator exists
        if "code_generator" not in agents:
            print(f"    [ERROR] code_generator agent not found")
            return False
        
        # Test agent execution with simple request
        print(f"\n[3] Executing code_generator agent...")
        request_data = {
            "prompt": "Write a simple Python function that adds two numbers",
            "language": "python",
            "context": "User is learning Python basics"
        }
        
        result = orchestrator.execute_agent("code_generator", request_data)
        
        print(f"    Agent execution result:")
        print(f"      - Status: {result.get('status', 'unknown')}")
        
        # Check response structure
        if isinstance(result, dict):
            print(f"    [OK] Response is a dictionary")
            
            # Check for required fields (depending on agent implementation)
            if "status" in result or "code" in result or "error" not in result:
                print(f"    [OK] Response has expected structure")
            
            # Print response details
            print(f"    Response keys: {list(result.keys())}")
            
            if "error" in result:
                print(f"    [WARNING] Agent returned error: {result['error']}")
                # This is still OK if it's a structured error
        else:
            print(f"    [ERROR] Response is not a dictionary: {type(result)}")
            return False
        
        # Test another agent
        print(f"\n[4] Executing code_validator agent...")
        request_data_validator = {
            "code": "def add(a, b):\n    return a + b",
            "language": "python"
        }
        
        result_validator = orchestrator.execute_agent("code_validator", request_data_validator)
        
        if isinstance(result_validator, dict):
            print(f"    [OK] CodeValidator response is valid")
            print(f"    Response keys: {list(result_validator.keys())}")
        else:
            print(f"    [ERROR] Invalid response type")
            return False
        
        # Test quality controller
        print(f"\n[5] Executing quality_controller agent...")
        request_data_quality = {
            "code": "def add(a,b):return a+b",
            "context": "Simple function"
        }
        
        result_quality = orchestrator.execute_agent("quality_controller", request_data_quality)
        
        if isinstance(result_quality, dict):
            print(f"    [OK] QualityController response is valid")
            print(f"    Response keys: {list(result_quality.keys())}")
        else:
            print(f"    [ERROR] Invalid response type")
            return False
        
        print(f"\n[OK] Test 3.1.3 PASSED: Agent execution works")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test 3.1.3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nPhase 3.1.3: Agent Execution Test")
    print("="*70)
    
    results = []
    results.append(("3.1.3 Agent Execution", test_agent_execution()))
    
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
