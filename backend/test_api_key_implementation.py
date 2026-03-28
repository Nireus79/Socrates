#!/usr/bin/env python3
"""
Quick test to verify the API key implementation works correctly.
Run from: backend/ directory
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from socrates_api.database import LocalDatabase
from datetime import datetime, timezone

def test_api_key_storage():
    """Test saving and retrieving API keys"""
    print("=" * 60)
    print("Testing API Key Storage Implementation")
    print("=" * 60)

    # Create a test database
    db = LocalDatabase(":memory:")  # In-memory database for testing

    # Test 1: Save API key
    print("\n[1] Test 1: Save API key")
    try:
        success = db.save_api_key("testuser", "anthropic", "sk-ant-test-12345")
        assert success, "Failed to save API key"
        print("  [PASS] API key saved successfully")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 2: Retrieve API key
    print("\n[OK] Test 2: Retrieve API key")
    try:
        retrieved_key = db.get_api_key("testuser", "anthropic")
        assert retrieved_key == "sk-ant-test-12345", f"Retrieved wrong key: {retrieved_key}"
        print(f"  [PASS] Retrieved API key: {retrieved_key[:10]}...")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 3: Retrieve non-existent key
    print("\n[OK] Test 3: Retrieve non-existent key")
    try:
        retrieved_key = db.get_api_key("testuser", "openai")
        assert retrieved_key is None, f"Should return None for non-existent key, got {retrieved_key}"
        print("  [PASS] Correctly returned None for non-existent key")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 4: Update existing API key
    print("\n[OK] Test 4: Update existing API key")
    try:
        success = db.save_api_key("testuser", "anthropic", "sk-ant-updated-99999")
        assert success, "Failed to update API key"
        retrieved_key = db.get_api_key("testuser", "anthropic")
        assert retrieved_key == "sk-ant-updated-99999", "Key was not updated"
        print(f"  [PASS] API key updated successfully: {retrieved_key[:10]}...")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 5: Delete API key
    print("\n[OK] Test 5: Delete API key")
    try:
        success = db.delete_api_key("testuser", "anthropic")
        assert success, "Failed to delete API key"
        retrieved_key = db.get_api_key("testuser", "anthropic")
        assert retrieved_key is None, "Key should be deleted"
        print("  [PASS] API key deleted successfully")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 6: Multiple providers for same user
    print("\n[OK] Test 6: Multiple providers for same user")
    try:
        db.save_api_key("testuser", "anthropic", "sk-ant-key")
        db.save_api_key("testuser", "openai", "sk-openai-key")

        key1 = db.get_api_key("testuser", "anthropic")
        key2 = db.get_api_key("testuser", "openai")

        assert key1 == "sk-ant-key", "Wrong anthropic key"
        assert key2 == "sk-openai-key", "Wrong openai key"
        print("  [PASS] Multiple providers stored correctly")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("All tests passed! [PASS]")
    print("=" * 60)
    return True

def test_orchestrator_handlers():
    """Test that orchestrator can process the new handlers"""
    print("\n" + "=" * 60)
    print("Testing Orchestrator Handler Integration")
    print("=" * 60)

    try:
        from socrates_api.orchestrator import APIOrchestrator

        # Create orchestrator instance
        print("\n[OK] Creating orchestrator instance...")
        orchestrator = APIOrchestrator("test-key")
        print("  [PASS] Orchestrator created")

        # Test add_api_key handler
        print("\n[OK] Testing add_api_key handler...")
        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "add_api_key",
                "user_id": "testuser",
                "provider": "anthropic",
                "api_key": "sk-ant-test-key"
            }
        )
        assert result.get("status") == "success", f"Handler failed: {result}"
        print("  [PASS] add_api_key handler works")

        # Test remove_api_key handler
        print("\n[OK] Testing remove_api_key handler...")
        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "remove_api_key",
                "user_id": "testuser",
                "provider": "anthropic"
            }
        )
        assert result.get("status") == "success", f"Handler failed: {result}"
        print("  [PASS] remove_api_key handler works")

        # Test set_auth_method handler
        print("\n[OK] Testing set_auth_method handler...")
        result = orchestrator.process_request(
            "multi_llm",
            {
                "action": "set_auth_method",
                "user_id": "testuser",
                "provider": "anthropic",
                "auth_method": "api_key"
            }
        )
        assert result.get("status") == "success", f"Handler failed: {result}"
        print("  [PASS] set_auth_method handler works")

        print("\n" + "=" * 60)
        print("All orchestrator handler tests passed! [PASS]")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[FAIL] Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_api_key_storage()
    success2 = test_orchestrator_handlers()

    if success1 and success2:
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED - IMPLEMENTATION COMPLETE")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed")
        sys.exit(1)
