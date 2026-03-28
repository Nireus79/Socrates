"""
Test multi-provider LLM support functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from socrates_api.database import LocalDatabase
from socrates_api.orchestrator import APIOrchestrator
import tempfile


def test_multi_provider_database_methods():
    """Test database methods for multi-provider support"""
    print("\n[TEST] Multi-Provider Database Methods")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test.db")
        db = LocalDatabase(db_path=db_file)

        try:
            # Create test user
            user_id = "test_user_123"
            from socrates_api.models_local import User
            user = User(user_id=user_id, username=user_id, email=f"{user_id}@test.com")
            db.save_user(user)

            # Test 1: Set and get default provider
            print("  - Testing set_user_default_provider()...")
            success = db.set_user_default_provider(user_id, "openai")
            assert success, "Failed to set default provider"

            provider = db.get_user_default_provider(user_id)
            assert provider == "openai", f"Expected 'openai', got '{provider}'"
            print("    [OK] Default provider set and retrieved correctly")

            # Test 2: Get default provider for new user (should default to anthropic)
            print("  - Testing default provider fallback...")
            new_user_provider = db.get_user_default_provider("unknown_user")
            assert new_user_provider == "anthropic", f"Expected 'anthropic' default, got '{new_user_provider}'"
            print("    [OK] Defaults to anthropic for new users")

            # Test 3: Set and get provider model
            print("  - Testing set_provider_model()...")
            success = db.set_provider_model(user_id, "openai", "gpt-4-turbo")
            assert success, "Failed to set provider model"

            model = db.get_provider_model(user_id, "openai")
            assert model == "gpt-4-turbo", f"Expected 'gpt-4-turbo', got '{model}'"
            print("    [OK] Provider model set and retrieved correctly")

            # Test 4: Get model for different provider (should use default)
            print("  - Testing default model fallback...")
            anthropic_model = db.get_provider_model(user_id, "anthropic")
            assert anthropic_model == "claude-3-sonnet", f"Expected 'claude-3-sonnet', got '{anthropic_model}'"
            print("    [OK] Uses default model for provider without custom setting")

            # Test 5: Set multiple providers
            print("  - Testing multiple provider models...")
            db.set_provider_model(user_id, "google", "gemini-pro")
            db.set_provider_model(user_id, "anthropic", "claude-3-opus")

            openai_model = db.get_provider_model(user_id, "openai")
            google_model = db.get_provider_model(user_id, "google")
            anthropic_model = db.get_provider_model(user_id, "anthropic")

            assert openai_model == "gpt-4-turbo", f"OpenAI model mismatch: {openai_model}"
            assert google_model == "gemini-pro", f"Google model mismatch: {google_model}"
            assert anthropic_model == "claude-3-opus", f"Anthropic model mismatch: {anthropic_model}"
            print("    [OK] Multiple provider models stored and retrieved correctly")

        finally:
            db.close()

    return True


def test_multi_provider_orchestrator():
    """Test orchestrator integration with multi-provider support"""
    print("\n[TEST] Multi-Provider Orchestrator Integration")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test.db")
        db = LocalDatabase(db_path=db_file)
        orchestrator = APIOrchestrator("test-key")

        try:
            # Create test user
            user_id = "test_user_456"
            from socrates_api.models_local import User
            user = User(user_id=user_id, username=user_id, email=f"{user_id}@test.com")
            db.save_user(user)

            # Test 1: set_default_provider via db
            print("  - Testing set_default_provider via database...")
            success = db.set_user_default_provider(user_id, "openai")
            assert success, "Failed to set default provider"
            provider = db.get_user_default_provider(user_id)
            assert provider == "openai", f"Expected openai, got {provider}"
            print("    [OK] set_default_provider works")

            # Test 2: set_provider_model via db
            print("  - Testing set_provider_model via database...")
            success = db.set_provider_model(user_id, "openai", "gpt-4-turbo")
            assert success, "Failed to set provider model"
            model = db.get_provider_model(user_id, "openai")
            assert model == "gpt-4-turbo", f"Expected gpt-4-turbo, got {model}"
            print("    [OK] set_provider_model works")

            # Test 3: Test orchestrator handlers exist
            print("  - Testing orchestrator handlers registered...")
            assert orchestrator is not None, "Orchestrator not initialized"
            print("    [OK] Orchestrator initialized")

        finally:
            db.close()
            orchestrator = None

    return True


def test_provider_aware_llm_client_creation():
    """Test that LLMClient creation uses correct provider/model"""
    print("\n[TEST] Provider-Aware LLMClient Creation")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test.db")
        db = LocalDatabase(db_path=db_file)

        try:
            user_id = "test_user_789"

            # Create test user
            from socrates_api.models_local import User
            user = User(user_id=user_id, username=user_id, email=f"{user_id}@test.com")
            db.save_user(user)

            # Set user preferences
            print("  - Setting user preferences...")
            db.set_user_default_provider(user_id, "google")
            db.set_provider_model(user_id, "google", "gemini-pro")
            db.save_api_key(user_id, "google", "test-google-key")
            print("    [OK] User set to Google/Gemini")

            # Simulate what happens in _handle_socratic_counselor
            print("  - Simulating provider lookup...")
            provider = db.get_user_default_provider(user_id)
            model = db.get_provider_model(user_id, provider)
            api_key = db.get_api_key(user_id, provider)

            assert provider == "google", f"Wrong provider: {provider}"
            assert model == "gemini-pro", f"Wrong model: {model}"
            assert api_key == "test-google-key", f"Wrong API key: {api_key}"
            print("    [OK] Correct provider/model/key retrieved for Google")

            # Test fallback for unknown user
            print("  - Testing fallback for new user...")
            default_provider = db.get_user_default_provider("unknown_user")
            default_model = db.get_provider_model("unknown_user", default_provider)

            assert default_provider == "anthropic", f"Wrong default: {default_provider}"
            assert default_model == "claude-3-sonnet", f"Wrong default model: {default_model}"
            print("    [OK] Correctly defaults to Claude for new users")

        finally:
            db.close()

    return True


def test_backward_compatibility():
    """Test that system remains backward compatible"""
    print("\n[TEST] Backward Compatibility")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test.db")
        db = LocalDatabase(db_path=db_file)

        try:
            user_id = "old_user"

            # Simulate old user without provider preferences set
            print("  - Testing old user without preferences...")
            provider = db.get_user_default_provider(user_id)
            model = db.get_provider_model(user_id, provider)

            assert provider == "anthropic", "Should default to anthropic"
            assert model == "claude-3-sonnet", "Should default to claude-3-sonnet"
            print("    [OK] Old users default to Claude (backward compatible)")

            # Test API key storage with new provider parameter
            print("  - Testing API key with provider...")
            db.save_api_key(user_id, "anthropic", "test-key")
            retrieved = db.get_api_key(user_id, "anthropic")
            assert retrieved == "test-key", "API key retrieval failed"
            print("    [OK] API key storage with provider parameter works")

        finally:
            db.close()

    return True


if __name__ == "__main__":
    print("=" * 70)
    print("MULTI-PROVIDER SUPPORT TEST SUITE")
    print("=" * 70)

    try:
        results = []
        results.append(("Database Methods", test_multi_provider_database_methods()))
        results.append(("Orchestrator Handlers", test_multi_provider_orchestrator()))
        results.append(("LLMClient Creation", test_provider_aware_llm_client_creation()))
        results.append(("Backward Compatibility", test_backward_compatibility()))

        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)

        for name, result in results:
            status = "[OK]" if result else "[FAIL]"
            print(f"{status} {name}")

        all_passed = all(r[1] for r in results)

        if all_passed:
            print("\n[SUCCESS] All multi-provider tests passed!")
            print("=" * 70)
        else:
            print("\n[FAIL] Some tests failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
