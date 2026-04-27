"""
Integration tests for LLM clients with AgentOrchestrator

Tests verify:
- Client initialization with orchestrator
- API key retrieval from database
- Token tracking and event emission
- Encryption/decryption of API keys
- Async operations
- Error handling
- Cache functionality
"""

import base64
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest

# Setup logging for test debugging
logging.basicConfig(level=logging.DEBUG)


class MockOrchestrator:
    """Mock orchestrator for testing without full system initialization"""

    def __init__(self, db_path: str = None):
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

        # Setup mock database
        self.database = MockDatabase(db_path)

    def reset_mocks(self):
        """Reset all mock calls"""
        self.event_emitter.emit.reset_mock()
        self.system_monitor.process.reset_mock()


class MockDatabase:
    """Mock database for testing API key storage"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or ":memory:"
        self.api_keys: Dict[tuple, str] = {}  # (user_id, provider) -> encrypted_key
        self._setup()

    def _setup(self):
        """Setup in-memory database"""
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def save_api_key(self, user_id: str, provider: str, encrypted_key: str, key_hash: str) -> bool:
        """Save encrypted API key"""
        try:
            self.api_keys[(user_id, provider)] = encrypted_key
            return True
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False

    def get_api_key(self, user_id: str, provider: str) -> str | None:
        """Retrieve encrypted API key"""
        return self.api_keys.get((user_id, provider))

    def delete_api_key(self, user_id: str, provider: str) -> bool:
        """Delete API key"""
        try:
            if (user_id, provider) in self.api_keys:
                del self.api_keys[(user_id, provider)]
            return True
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False


class TestOpenAIClientIntegration:
    """Integration tests for OpenAI client"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI SDK"""
        with patch("socratic_system.clients.openai_client.openai") as mock:
            yield mock

    def test_client_initialization(self, mock_orchestrator):
        """Test OpenAI client initializes with orchestrator"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        assert client.api_key == "sk-test-key"
        assert client.orchestrator is mock_orchestrator
        assert client.model == "gpt-4-turbo"
        assert client._insights_cache == {}

    def test_client_initialization_with_placeholder_key(self, mock_orchestrator):
        """Test client initializes with placeholder key"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="placeholder_key", orchestrator=mock_orchestrator)

        # Should not create clients with placeholder key
        assert client.api_key == "placeholder_key"
        assert client.client is None

    def test_get_user_api_key_from_database(self, mock_orchestrator):
        """Test retrieving user API key from database"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="default-key", orchestrator=mock_orchestrator)

        # Setup user API key in database
        encryption_key_base = os.getenv("SOCRATES_ENCRYPTION_KEY", "default-socrates-key")
        key_hash = hashlib.sha256(encryption_key_base.encode()).digest()
        encryption_key = base64.urlsafe_b64encode(key_hash)

        from cryptography.fernet import Fernet

        cipher = Fernet(encryption_key)
        user_key = "sk-user-specific-key"
        encrypted = cipher.encrypt(user_key.encode()).decode()

        mock_orchestrator.database.save_api_key(
            "user123", "openai", encrypted, hashlib.sha256(user_key.encode()).hexdigest()
        )

        # Retrieve user-specific key
        api_key, is_user_specific = client._get_user_api_key("user123")
        assert api_key == user_key
        assert is_user_specific is True

    def test_fallback_to_default_key(self, mock_orchestrator):
        """Test fallback to default key when user key not found"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="default-key", orchestrator=mock_orchestrator)

        # No user key in database
        api_key, is_user_specific = client._get_user_api_key("nonexistent_user")
        assert api_key == "default-key"
        assert is_user_specific is False

    def test_cache_key_generation(self, mock_orchestrator):
        """Test SHA256 cache key generation"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        message = "Test message"
        cache_key = client._get_cache_key(message)

        expected = hashlib.sha256(message.encode()).hexdigest()
        assert cache_key == expected

    def test_insights_caching(self, mock_orchestrator):
        """Test insights extraction caching"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        # Manually add to cache
        test_response = {"goals": "build app", "requirements": ["fast", "scalable"]}
        cache_key = client._get_cache_key("Test response")
        client._insights_cache[cache_key] = test_response

        # Verify cache hit
        assert cache_key in client._insights_cache
        assert client._insights_cache[cache_key] == test_response

    def test_error_on_no_api_key(self, mock_orchestrator, mock_openai):
        """Test APIError raised when no valid API key"""
        from socratic_nexus.clients import OpenAIClient

        from socratic_system.exceptions import APIError

        client = OpenAIClient(api_key=None, orchestrator=mock_orchestrator)

        with pytest.raises(APIError) as exc_info:
            client._get_client(user_id="nonexistent_user")

        assert exc_info.value.error_type == "MISSING_API_KEY"
        assert "OpenAI" in exc_info.value.message

    def test_token_tracking(self, mock_orchestrator, mock_openai):
        """Test token usage tracking"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        # Mock usage object
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50

        client._track_token_usage(mock_usage, "test_operation")

        # Verify system_monitor.process was called
        mock_orchestrator.system_monitor.process.assert_called_once()
        call_args = mock_orchestrator.system_monitor.process.call_args[0][0]

        assert call_args["action"] == "track_tokens"
        assert call_args["operation"] == "test_operation"
        assert call_args["input_tokens"] == 100
        assert call_args["output_tokens"] == 50
        assert call_args["total_tokens"] == 150

    def test_cost_calculation(self, mock_orchestrator):
        """Test cost calculation for OpenAI"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        mock_usage = Mock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 1000

        cost = client._calculate_cost(mock_usage)

        # $0.01 per 1K input + $0.03 per 1K output = $0.04
        expected = 0.01 + 0.03
        assert abs(cost - expected) < 0.0001


class TestGoogleClientIntegration:
    """Integration tests for Google client"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    @pytest.fixture
    def mock_google(self):
        """Mock Google SDK"""
        with patch("socratic_system.clients.google_client.genai") as mock:
            yield mock

    def test_client_initialization(self, mock_orchestrator, mock_google):
        """Test Google client initializes with orchestrator"""
        from socratic_nexus.clients import GoogleClient

        client = GoogleClient(api_key="AIza-test-key", orchestrator=mock_orchestrator)

        assert client.api_key == "AIza-test-key"
        assert client.orchestrator is mock_orchestrator
        assert client.model == "gemini-pro"

    def test_token_estimation_google(self, mock_orchestrator, mock_google):
        """Test token estimation for Google (text-length based)"""
        from socratic_nexus.clients import GoogleClient

        client = GoogleClient(api_key="AIza-test-key", orchestrator=mock_orchestrator)

        input_len = 400  # 400 chars ≈ 100 tokens (4 chars per token)
        output_len = 200  # 200 chars ≈ 50 tokens

        client._track_token_usage_google(input_len, output_len, "test_operation")

        # Verify tracking
        mock_orchestrator.system_monitor.process.assert_called_once()
        call_args = mock_orchestrator.system_monitor.process.call_args[0][0]

        assert call_args["input_tokens"] == 100
        assert call_args["output_tokens"] == 50

    def test_cost_calculation_google(self, mock_orchestrator, mock_google):
        """Test cost calculation for Google (text-length based)"""
        from socratic_nexus.clients import GoogleClient

        client = GoogleClient(api_key="AIza-test-key", orchestrator=mock_orchestrator)

        # 1000 chars input, 500 chars output
        cost = client._calculate_cost_google(1000, 500)

        # $0.00025 per 1K chars input + $0.0005 per 1K chars output
        # (1000/1000) * 0.00025 + (500/1000) * 0.0005 = 0.00025 + 0.00025 = 0.0005
        expected = 0.00025 + 0.00025
        assert abs(cost - expected) < 0.00001


class TestOllamaClientIntegration:
    """Integration tests for Ollama client"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    @pytest.fixture
    def mock_requests(self):
        """Mock requests library"""
        with patch("socratic_system.clients.ollama_client.requests") as mock:
            yield mock

    def test_client_initialization(self, mock_orchestrator, mock_requests):
        """Test Ollama client initializes with orchestrator"""
        from socratic_nexus.clients import OllamaClient

        client = OllamaClient(orchestrator=mock_orchestrator)

        assert client.orchestrator is mock_orchestrator
        assert client.model == "mistral"
        assert client.base_url == "http://localhost:11434"

    def test_ollama_url_from_config(self, mock_orchestrator, mock_requests):
        """Test Ollama URL can be configured"""
        from socratic_nexus.clients import OllamaClient

        mock_orchestrator.config.ollama_url = "http://custom-server:11434"

        client = OllamaClient(orchestrator=mock_orchestrator)

        assert client.base_url == "http://custom-server:11434"

    def test_ollama_model_from_config(self, mock_orchestrator, mock_requests):
        """Test Ollama model can be configured"""
        from socratic_nexus.clients import OllamaClient

        mock_orchestrator.config.ollama_model = "llama2"

        client = OllamaClient(orchestrator=mock_orchestrator)

        assert client.model == "llama2"

    def test_ollama_token_tracking(self, mock_orchestrator, mock_requests):
        """Test token tracking for Ollama"""
        from socratic_nexus.clients import OllamaClient

        client = OllamaClient(orchestrator=mock_orchestrator)

        client._track_token_usage_ollama(400, 200, "test_operation")

        # Verify system_monitor.process was called
        mock_orchestrator.system_monitor.process.assert_called_once()
        call_args = mock_orchestrator.system_monitor.process.call_args[0][0]

        assert call_args["input_tokens"] == 100  # 400/4
        assert call_args["output_tokens"] == 50  # 200/4
        assert call_args["cost_estimate"] == 0.0  # Ollama is free

    def test_ollama_cost_is_zero(self, mock_orchestrator, mock_requests):
        """Test Ollama always returns zero cost"""
        from socratic_nexus.clients import OllamaClient

        client = OllamaClient(orchestrator=mock_orchestrator)

        cost = client._estimate_cost(10000, 5000)
        assert cost == 0.0


class TestClientInterchangeability:
    """Test that all clients have compatible interfaces"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    def test_all_clients_have_same_methods(self, mock_orchestrator):
        """Test all clients implement same methods"""
        from socratic_nexus.clients import GoogleClient, OllamaClient, OpenAIClient

        clients = [
            OpenAIClient(api_key="test", orchestrator=mock_orchestrator),
            GoogleClient(api_key="test", orchestrator=mock_orchestrator),
            OllamaClient(orchestrator=mock_orchestrator),
        ]

        # Methods that should exist in all clients
        required_methods = [
            "extract_insights",
            "extract_insights_async",
            "generate_code",
            "generate_socratic_question",
            "generate_socratic_question_async",
            "generate_response",
            "generate_response_async",
            "test_connection",
            "_get_cache_key",
            "_track_token_usage",
            "_track_token_usage_async",
            "_get_user_api_key",
            "_decrypt_api_key_from_db",
        ]

        for client in clients:
            for method in required_methods:
                assert hasattr(client, method), f"{client.__class__.__name__} missing {method}"
                assert callable(getattr(client, method)), f"{method} is not callable"

    def test_client_substitutability(self, mock_orchestrator):
        """Test that any client can substitute for another"""
        from socratic_nexus.clients import GoogleClient, OllamaClient, OpenAIClient

        def use_client(client, prompt: str):
            """Generic function that uses any client"""
            # This should work with any client
            cache_key = client._get_cache_key(prompt)
            return cache_key

        clients = [
            OpenAIClient(api_key="test", orchestrator=mock_orchestrator),
            GoogleClient(api_key="test", orchestrator=mock_orchestrator),
            OllamaClient(orchestrator=mock_orchestrator),
        ]

        for client in clients:
            result = use_client(client, "Test prompt")
            assert result == hashlib.sha256("Test prompt".encode()).hexdigest()


class TestEventEmission:
    """Test event emission from clients"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    def test_token_usage_event_emission(self, mock_orchestrator):
        """Test TOKEN_USAGE event emitted"""
        from socratic_nexus.clients import OpenAIClient

        from socratic_system.events import EventType

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50

        client._track_token_usage(mock_usage, "test_operation")

        # Verify event_emitter.emit was called
        mock_orchestrator.event_emitter.emit.assert_called_once()
        call_args = mock_orchestrator.event_emitter.emit.call_args

        assert call_args[0][0] == EventType.TOKEN_USAGE
        assert call_args[0][1]["operation"] == "test_operation"
        assert call_args[0][1]["input_tokens"] == 100
        assert call_args[0][1]["output_tokens"] == 50


class TestEncryption:
    """Test API key encryption/decryption"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    def test_encryption_key_from_env(self, mock_orchestrator, monkeypatch):
        """Test using custom encryption key from environment"""
        import base64
        import hashlib

        from cryptography.fernet import Fernet
        from socratic_nexus.clients import OpenAIClient

        custom_key = "my-custom-encryption-key"
        monkeypatch.setenv("SOCRATES_ENCRYPTION_KEY", custom_key)

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        # Encrypt with custom key
        key_hash = hashlib.sha256(custom_key.encode()).digest()
        encryption_key = base64.urlsafe_b64encode(key_hash)
        cipher = Fernet(encryption_key)
        original_key = "sk-user-key"
        encrypted = cipher.encrypt(original_key.encode()).decode()

        # Decrypt with client
        decrypted = client._decrypt_api_key_from_db(encrypted)
        assert decrypted == original_key

    def test_encryption_fallback_methods(self, mock_orchestrator, monkeypatch):
        """Test encryption method fallbacks"""
        import base64

        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        # Test Base64 fallback (Method 3)
        original_key = "sk-test-key"
        encrypted = base64.b64encode(original_key.encode()).decode()

        decrypted = client._decrypt_api_key_from_db(encrypted)
        # Base64 should work as fallback (though SHA256 will try first)
        assert decrypted is not None  # Either Base64 or SHA256 succeeds


class TestAsyncOperations:
    """Test async operation support"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    @pytest.mark.asyncio
    async def test_async_token_tracking(self, mock_orchestrator):
        """Test async token tracking"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50

        await client._track_token_usage_async(mock_usage, "async_operation")

        # Verify tracking was called
        mock_orchestrator.system_monitor.process.assert_called_once()


class TestErrorHandling:
    """Test error handling in clients"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return MockOrchestrator()

    def test_api_error_on_missing_key(self, mock_orchestrator):
        """Test APIError raised with clear message"""
        from socratic_nexus.clients import OpenAIClient

        from socratic_system.exceptions import APIError

        client = OpenAIClient(api_key=None, orchestrator=mock_orchestrator)

        with pytest.raises(APIError) as exc_info:
            client._get_client()

        error = exc_info.value
        assert error.error_type == "MISSING_API_KEY"
        assert "Settings" in error.message

    def test_json_parsing_handles_markdown(self, mock_orchestrator):
        """Test JSON parsing removes markdown code blocks"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        response_with_markdown = """```json
        {
            "goals": "build app",
            "requirements": ["fast"]
        }
        ```"""

        result = client._parse_json_response(response_with_markdown)
        assert result["goals"] == "build app"
        assert "fast" in result["requirements"]

    def test_json_parsing_handles_invalid_json(self, mock_orchestrator):
        """Test JSON parsing returns empty dict on invalid JSON"""
        from socratic_nexus.clients import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key", orchestrator=mock_orchestrator)

        invalid_json = "This is not JSON {invalid"
        result = client._parse_json_response(invalid_json)

        assert result == {}


class TestDatabaseIntegration:
    """Test database integration for API key storage"""

    def test_save_and_retrieve_api_key(self):
        """Test saving and retrieving API keys from database"""
        db = MockDatabase()

        # Save API key
        success = db.save_api_key("user123", "openai", "encrypted_key_value", "key_hash")
        assert success is True

        # Retrieve API key
        retrieved = db.get_api_key("user123", "openai")
        assert retrieved == "encrypted_key_value"

    def test_save_and_retrieve_multiple_providers(self):
        """Test storing keys for multiple providers per user"""
        db = MockDatabase()

        # Save keys for multiple providers
        db.save_api_key("user123", "openai", "openai_key", "hash1")
        db.save_api_key("user123", "google", "google_key", "hash2")
        db.save_api_key("user123", "ollama", "ollama_key", "hash3")

        # Verify retrieval
        assert db.get_api_key("user123", "openai") == "openai_key"
        assert db.get_api_key("user123", "google") == "google_key"
        assert db.get_api_key("user123", "ollama") == "ollama_key"

    def test_delete_api_key(self):
        """Test deleting API keys"""
        db = MockDatabase()

        db.save_api_key("user123", "openai", "key_value", "hash")
        assert db.get_api_key("user123", "openai") is not None

        success = db.delete_api_key("user123", "openai")
        assert success is True
        assert db.get_api_key("user123", "openai") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
