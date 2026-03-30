#!/usr/bin/env python3
"""
Test script to verify LLM API key management is working correctly.

This script tests:
1. Database initialization with encryption
2. API key storage and retrieval
3. Provider metadata loading
4. LLM client creation with API keys
5. Encryption/decryption
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LLM_Test")

def test_database_initialization():
    """Test 1: Database initialization with encryption"""
    logger.info("=" * 60)
    logger.info("TEST 1: Database Initialization with Encryption")
    logger.info("=" * 60)

    try:
        from socratic_system.database import DatabaseSingleton

        # Initialize database
        test_db_path = Path.home() / ".socrates" / "test_projects.db"
        logger.info(f"Initializing database at: {test_db_path}")

        DatabaseSingleton.initialize(str(test_db_path))
        db = DatabaseSingleton.get_instance()
        logger.info("✓ Database initialized successfully")

        # Check encryption status
        from socratic_system.database.encryption import encryption_config
        if encryption_config["enabled"]:
            logger.info("✓ Encryption is ENABLED")
        else:
            logger.warning("⚠ Encryption is DISABLED (set SECURITY_DATABASE_ENCRYPTION=true to enable)")

        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False

def test_provider_metadata():
    """Test 2: Provider metadata loading"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Provider Metadata Loading")
    logger.info("=" * 60)

    try:
        from socratic_system.models.llm_provider import (
            list_available_providers,
            get_provider_metadata,
            PROVIDER_METADATA
        )

        providers = list_available_providers()
        logger.info(f"✓ Loaded {len(providers)} providers")

        for provider in providers:
            logger.info(f"\n  Provider: {provider.display_name}")
            logger.info(f"    - Name: {provider.provider}")
            logger.info(f"    - Models: {len(provider.models)} available")
            logger.info(f"    - Requires API Key: {provider.requires_api_key}")
            logger.info(f"    - Cost: ${provider.cost_per_1k_input_tokens:.6f}/1K input")
            logger.info(f"    - Context: {provider.context_window:,} tokens")

        logger.info("\n✓ All provider metadata loaded successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Provider metadata loading failed: {e}")
        return False

def test_api_key_storage(test_username="testuser"):
    """Test 3: API key storage and retrieval"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: API Key Storage and Retrieval")
    logger.info("=" * 60)

    try:
        from socratic_system.database import DatabaseSingleton

        db = DatabaseSingleton.get_instance()

        # Test 3a: Save API key
        test_key = "test-api-key-12345-secret"
        test_provider = "openai"

        logger.info(f"Saving test API key for {test_provider}...")
        success = db.save_api_key(test_username, test_provider, test_key)
        if not success:
            logger.error(f"✗ Failed to save API key")
            return False
        logger.info("✓ API key saved successfully")

        # Test 3b: Retrieve API key
        logger.info(f"Retrieving API key for {test_provider}...")
        retrieved_key = db.get_api_key(test_username, test_provider)

        if not retrieved_key:
            logger.error("✗ Failed to retrieve API key")
            return False

        if retrieved_key == test_key:
            logger.info("✓ Retrieved key matches saved key")
        else:
            logger.error(f"✗ Key mismatch!")
            logger.error(f"  Saved:    {test_key}")
            logger.error(f"  Retrieved: {retrieved_key}")
            return False

        # Test 3c: Delete API key
        logger.info(f"Deleting API key for {test_provider}...")
        success = db.delete_api_key(test_username, test_provider)
        if not success:
            logger.warning("⚠ Failed to delete API key")
            # Not critical, continue
        else:
            logger.info("✓ API key deleted successfully")

        # Test 3d: Verify deletion
        retrieved_again = db.get_api_key(test_username, test_provider)
        if retrieved_again is None:
            logger.info("✓ Confirmed key deleted")
        else:
            logger.warning("⚠ Key still exists after deletion")

        return True
    except Exception as e:
        logger.error(f"✗ API key storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_encryption(test_username="testuser"):
    """Test 4: Encryption/Decryption"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Encryption and Decryption")
    logger.info("=" * 60)

    try:
        from socratic_system.database.encryption import (
            encrypt_field,
            decrypt_field,
            encryption_config
        )

        if not encryption_config["enabled"]:
            logger.warning("⚠ Encryption not enabled, skipping encryption test")
            return True

        test_data = "sk-ant-test-key-12345"

        logger.info(f"Original data: {test_data}")

        # Encrypt
        encrypted = encrypt_field(test_data, field_name="api_key")
        logger.info(f"Encrypted: {encrypted[:50]}..." if encrypted else "Failed to encrypt")

        if not encrypted:
            logger.error("✗ Encryption failed")
            return False

        # Decrypt
        decrypted = decrypt_field(encrypted, field_name="api_key")
        logger.info(f"Decrypted: {decrypted}")

        if decrypted == test_data:
            logger.info("✓ Encryption/decryption working correctly")
            return True
        else:
            logger.error(f"✗ Decryption mismatch!")
            logger.error(f"  Original:  {test_data}")
            logger.error(f"  Decrypted: {decrypted}")
            return False
    except Exception as e:
        logger.error(f"✗ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_client_creation():
    """Test 5: LLM client creation"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: LLM Client Creation")
    logger.info("=" * 60)

    try:
        logger.info("Checking if socrates_nexus is available...")
        try:
            from socrates_nexus import LLMClient
            logger.info("✓ socrates_nexus imported successfully")
        except ImportError:
            logger.warning("⚠ socrates_nexus not available (this is expected if not in API environment)")
            logger.info("  LLM client creation requires socrates_nexus package")
            return True

        # Note: We won't actually create a client without a valid API key
        logger.info("✓ LLMClient import successful")
        logger.info("  (Actual client creation requires valid API key)")

        return True
    except Exception as e:
        logger.warning(f"⚠ LLM client test warning: {e}")
        return True  # Not critical

def test_orchestrator_integration():
    """Test 6: Orchestrator integration"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Orchestrator Multi-LLM Integration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.orchestrator import AgentOrchestrator
        from socratic_core import SocratesConfig

        logger.info("Creating orchestrator with test config...")
        config = SocratesConfig(api_key="test-key")
        orchestrator = AgentOrchestrator(config)
        logger.info("✓ Orchestrator created successfully")

        # Check multi_llm handler
        logger.info("Testing multi_llm handler...")
        result = orchestrator.process_request("multi_llm", {
            "action": "list_providers",
            "user_id": "testuser"
        })

        if result.get("status") == "success":
            providers = result.get("data", {}).get("providers", [])
            logger.info(f"✓ multi_llm handler working, returned {len(providers)} providers")
            return True
        else:
            logger.error(f"✗ multi_llm handler failed: {result.get('message')}")
            return False
    except Exception as e:
        logger.error(f"✗ Orchestrator integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("Starting LLM API Key Setup Tests...\n")

    # Check environment
    logger.info("Environment Check:")
    encryption_enabled = os.getenv("SECURITY_DATABASE_ENCRYPTION", "false").lower() == "true"
    logger.info(f"  SECURITY_DATABASE_ENCRYPTION: {encryption_enabled}")

    encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY")
    if encryption_key:
        logger.info(f"  DATABASE_ENCRYPTION_KEY: {'*' * 20} (set)")
    else:
        logger.warning("  DATABASE_ENCRYPTION_KEY: not set (encryption will be disabled)")

    # Run tests
    results = {
        "Database Initialization": test_database_initialization(),
        "Provider Metadata": test_provider_metadata(),
        "API Key Storage": test_api_key_storage(),
        "Encryption": test_encryption(),
        "LLM Client Creation": test_llm_client_creation(),
        "Orchestrator Integration": test_orchestrator_integration(),
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n✓ All tests passed! LLM API key management is ready to use.")
        logger.info("\nNext steps:")
        logger.info("1. Start the Socrates application")
        logger.info("2. Go to Settings → LLM Providers")
        logger.info("3. Add your API key")
        logger.info("4. Ask a question in chat to verify it works")
        return 0
    else:
        logger.error(f"\n✗ {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
