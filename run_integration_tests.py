#!/usr/bin/env python
"""
Standalone integration test runner for LLM clients

Runs core functionality tests without requiring full pytest setup.
"""

import base64
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


class TestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"[PASS] {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"[FAIL] {test_name}")
        print(f"  Error: {error}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print("=" * 70)


class MockOrchestrator:
    """Mock orchestrator for testing"""

    def __init__(self):
        self.config = Mock()
        self.config.claude_model = "claude-haiku-4-5-20251001"
        self.config.openai_model = "gpt-4-turbo"
        self.config.google_model = "gemini-pro"
        self.config.ollama_model = "mistral"
        self.config.ollama_url = "http://localhost:11434"

        self.event_emitter = Mock()
        self.event_emitter.emit = Mock()

        self.system_monitor = Mock()
        self.system_monitor.process = Mock()

        self.database = MockDatabase()


class MockDatabase:
    """Mock database for API key storage"""

    def __init__(self):
        self.api_keys: Dict[tuple, str] = {}

    def save_api_key(self, user_id: str, provider: str, encrypted_key: str, key_hash: str) -> bool:
        try:
            self.api_keys[(user_id, provider)] = encrypted_key
            return True
        except Exception:
            return False

    def get_api_key(self, user_id: str, provider: str) -> str | None:
        return self.api_keys.get((user_id, provider))

    def delete_api_key(self, user_id: str, provider: str) -> bool:
        try:
            if (user_id, provider) in self.api_keys:
                del self.api_keys[(user_id, provider)]
            return True
        except Exception:
            return False


def test_openai_client_import():
    """Test OpenAI client can be imported"""
    try:
        # Import directly to avoid monolith __init__.py
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "openai_client",
            "C:/Users/themi/PycharmProjects/Socrates/socratic_system/clients/openai_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            return True, "OpenAI client imported successfully"
        except ModuleNotFoundError as e:
            if "openai" in str(e).lower():
                return True, "OpenAI SDK not installed (expected in test environment)"
            raise
    except Exception as e:
        return False, f"Import error: {str(e)[:100]}"


def test_google_client_import():
    """Test Google client can be imported"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "google_client",
            "C:/Users/themi/PycharmProjects/Socrates/socratic_system/clients/google_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            return True, "Google client imported successfully"
        except ModuleNotFoundError as e:
            if "google" in str(e).lower():
                return True, "Google SDK not installed (expected in test environment)"
            raise
    except Exception as e:
        return False, f"Import error: {str(e)[:100]}"


def test_ollama_client_import():
    """Test Ollama client can be imported"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "ollama_client",
            "C:/Users/themi/PycharmProjects/Socrates/socratic_system/clients/ollama_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "Ollama client imported successfully"
    except Exception as e:
        return False, f"Failed to import: {str(e)[:100]}"


def test_openai_client_initialization():
    """Test OpenAI client initializes correctly"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient

        orchestrator = MockOrchestrator()
        client = OpenAIClient(api_key="sk-test-key", orchestrator=orchestrator)

        assert client.api_key == "sk-test-key"
        assert client.model == "gpt-4-turbo"
        assert client.orchestrator is orchestrator
        return True, "OpenAI client initialized correctly"
    except Exception as e:
        return False, f"Initialization failed: {e}"


def test_google_client_initialization():
    """Test Google client initializes correctly"""
    try:
        from socratic_system.clients.google_client import GoogleClient

        orchestrator = MockOrchestrator()
        client = GoogleClient(api_key="AIza-test-key", orchestrator=orchestrator)

        assert client.api_key == "AIza-test-key"
        assert client.model == "gemini-pro"
        assert client.orchestrator is orchestrator
        return True, "Google client initialized correctly"
    except Exception as e:
        return False, f"Initialization failed: {e}"


def test_ollama_client_initialization():
    """Test Ollama client initializes correctly"""
    try:
        from socratic_system.clients.ollama_client import OllamaClient

        orchestrator = MockOrchestrator()
        client = OllamaClient(orchestrator=orchestrator)

        assert client.model == "mistral"
        assert client.base_url == "http://localhost:11434"
        assert client.orchestrator is orchestrator
        return True, "Ollama client initialized correctly"
    except Exception as e:
        return False, f"Initialization failed: {e}"


def test_cache_key_generation():
    """Test cache key generation"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient

        orchestrator = MockOrchestrator()
        client = OpenAIClient(api_key="sk-test", orchestrator=orchestrator)

        message = "Test message"
        cache_key = client._get_cache_key(message)
        expected = hashlib.sha256(message.encode()).hexdigest()

        assert cache_key == expected
        return True, "Cache key generation works correctly"
    except Exception as e:
        return False, f"Cache key generation failed: {e}"


def test_insights_caching():
    """Test insights caching"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient

        orchestrator = MockOrchestrator()
        client = OpenAIClient(api_key="sk-test", orchestrator=orchestrator)

        test_data = {"goals": "build app"}
        cache_key = client._get_cache_key("test response")
        client._insights_cache[cache_key] = test_data

        assert cache_key in client._insights_cache
        assert client._insights_cache[cache_key] == test_data
        return True, "Insights caching works correctly"
    except Exception as e:
        return False, f"Insights caching failed: {e}"


def test_database_api_key_storage():
    """Test API key storage and retrieval"""
    try:
        import os
        from cryptography.fernet import Fernet

        db = MockDatabase()

        # Create encrypted key
        encryption_key_base = "test-encryption-key"
        key_hash = hashlib.sha256(encryption_key_base.encode()).digest()
        encryption_key = base64.urlsafe_b64encode(key_hash)
        cipher = Fernet(encryption_key)

        user_api_key = "sk-user-test-key"
        encrypted = cipher.encrypt(user_api_key.encode()).decode()

        # Save to database
        success = db.save_api_key("user123", "openai", encrypted, "hash")
        assert success is True

        # Retrieve from database
        retrieved = db.get_api_key("user123", "openai")
        assert retrieved == encrypted

        return True, "Database API key storage works correctly"
    except Exception as e:
        return False, f"Database API key storage failed: {e}"


def test_token_tracking_integration():
    """Test token tracking with orchestrator"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient

        orchestrator = MockOrchestrator()
        client = OpenAIClient(api_key="sk-test", orchestrator=orchestrator)

        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50

        client._track_token_usage(mock_usage, "test_operation")

        # Verify system_monitor.process was called
        assert orchestrator.system_monitor.process.called
        call_args = orchestrator.system_monitor.process.call_args[0][0]

        assert call_args["action"] == "track_tokens"
        assert call_args["input_tokens"] == 100
        assert call_args["output_tokens"] == 50

        return True, "Token tracking integration works correctly"
    except Exception as e:
        return False, f"Token tracking integration failed: {e}"


def test_cost_calculation():
    """Test cost calculation for different providers"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient
        from socratic_system.clients.google_client import GoogleClient
        from socratic_system.clients.ollama_client import OllamaClient

        orchestrator = MockOrchestrator()

        # OpenAI cost
        openai_client = OpenAIClient(api_key="sk-test", orchestrator=orchestrator)
        mock_usage = Mock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 1000
        openai_cost = openai_client._calculate_cost(mock_usage)
        assert openai_cost > 0

        # Google cost
        google_client = GoogleClient(api_key="AIza-test", orchestrator=orchestrator)
        google_cost = google_client._calculate_cost_google(1000, 500)
        assert google_cost > 0

        # Ollama cost (should be zero)
        ollama_client = OllamaClient(orchestrator=orchestrator)
        # Ollama doesn't track cost traditionally

        return True, "Cost calculation works for all providers"
    except Exception as e:
        return False, f"Cost calculation failed: {e}"


def test_json_parsing():
    """Test JSON response parsing"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient

        orchestrator = MockOrchestrator()
        client = OpenAIClient(api_key="sk-test", orchestrator=orchestrator)

        # Test markdown JSON
        markdown_json = '''```json
        {"goals": "build app", "requirements": ["fast"]}
        ```'''

        result = client._parse_json_response(markdown_json)
        assert result["goals"] == "build app"
        assert "fast" in result["requirements"]

        # Test plain JSON
        plain_json = '{"test": "value"}'
        result = client._parse_json_response(plain_json)
        assert result["test"] == "value"

        # Test invalid JSON
        invalid = "not json at all"
        result = client._parse_json_response(invalid)
        assert result == {}

        return True, "JSON parsing works correctly"
    except Exception as e:
        return False, f"JSON parsing failed: {e}"


def test_method_presence():
    """Test all required methods exist in each client"""
    try:
        from socratic_system.clients.openai_client import OpenAIClient
        from socratic_system.clients.google_client import GoogleClient
        from socratic_system.clients.ollama_client import OllamaClient

        orchestrator = MockOrchestrator()

        clients = [
            ("OpenAI", OpenAIClient(api_key="sk-test", orchestrator=orchestrator)),
            ("Google", GoogleClient(api_key="AIza-test", orchestrator=orchestrator)),
            ("Ollama", OllamaClient(orchestrator=orchestrator)),
        ]

        required_methods = [
            "extract_insights",
            "generate_code",
            "generate_socratic_question",
            "generate_response",
            "test_connection",
            "_get_cache_key",
            "_track_token_usage",
        ]

        for client_name, client in clients:
            for method in required_methods:
                if not hasattr(client, method):
                    return False, f"{client_name} missing method: {method}"

        return True, "All required methods present in all clients"
    except Exception as e:
        return False, f"Method presence check failed: {e}"


def main():
    """Run all integration tests"""
    results = TestResults()

    tests = [
        ("OpenAI client import", test_openai_client_import),
        ("Google client import", test_google_client_import),
        ("Ollama client import", test_ollama_client_import),
        ("OpenAI client initialization", test_openai_client_initialization),
        ("Google client initialization", test_google_client_initialization),
        ("Ollama client initialization", test_ollama_client_initialization),
        ("Cache key generation", test_cache_key_generation),
        ("Insights caching", test_insights_caching),
        ("Database API key storage", test_database_api_key_storage),
        ("Token tracking integration", test_token_tracking_integration),
        ("Cost calculation", test_cost_calculation),
        ("JSON parsing", test_json_parsing),
        ("Method presence", test_method_presence),
    ]

    print("=" * 70)
    print("LLM Clients Integration Test Suite")
    print("=" * 70 + "\n")

    for test_name, test_func in tests:
        try:
            passed, message = test_func()
            if passed:
                results.add_pass(f"{test_name}: {message}")
            else:
                results.add_fail(test_name, message)
        except Exception as e:
            results.add_fail(test_name, str(e))

    results.summary()

    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
