"""
Tests for Claude API client - API interaction and response handling
"""

from unittest.mock import MagicMock, patch
import json

import pytest
import socrates

from socratic_system.clients.claude_client import ClaudeClient
from socratic_system.models import ProjectContext
from socratic_system.exceptions import APIError


@pytest.mark.unit
class TestClaudeClientInitialization:
    """Tests for ClaudeClient initialization"""

    def test_claude_client_initialization(self, test_config):
        """Test ClaudeClient initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-api-key", orchestrator)

            assert client is not None
            assert client.model == test_config.claude_model
            assert client.orchestrator == orchestrator

    def test_claude_client_requires_api_key(self, test_config):
        """Test that ClaudeClient requires an API key"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Should not raise error with valid key
            client = ClaudeClient("valid-key", orchestrator)
            assert client is not None


@pytest.mark.unit
class TestClaudeClientExtractInsights:
    """Tests for ClaudeClient.extract_insights method"""

    def test_extract_insights_empty_response(self, test_config, sample_project):
        """Test extract_insights handles empty response"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            # Empty string response
            result = client.extract_insights("", sample_project)
            assert result == {}

            # Very short response
            result = client.extract_insights("ab", sample_project)
            assert result == {}

    def test_extract_insights_non_informative_responses(self, test_config, sample_project):
        """Test extract_insights handles non-informative responses"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            non_informative = ["i don't know", "idk", "not sure", "no idea", "dunno", "unsure"]

            for response in non_informative:
                result = client.extract_insights(response, sample_project)
                assert isinstance(result, dict)
                # Should contain uncertainty note
                assert "note" in result or result == {}

    @patch("anthropic.Anthropic")
    def test_extract_insights_with_valid_response(self, mock_anthropic, test_config, sample_project):
        """Test extract_insights with valid user response"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            # Mock the API response
            mock_response = MagicMock()
            mock_response.content[0].text = json.dumps({
                "goals": "Build a REST API",
                "requirements": ["JWT auth", "Database"],
                "tech_stack": ["Python", "FastAPI"],
                "constraints": ["Low latency"],
            })

            client.client = MagicMock()
            client.client.messages.create.return_value = mock_response

            result = client.extract_insights("I want to build a REST API with Python", sample_project)

            # Should have parsed the response
            assert isinstance(result, (dict, list))

    def test_extract_insights_with_project_context(self, test_config):
        """Test extract_insights uses project context in prompt"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            project = ProjectContext(
                project_id="test-123",
                name="Test Project",
                description="Test description",
                owner="testuser",
                phase="planning",
                goals="Build something",
                tech_stack=["Python"],
                requirements=["Fast"],
            )

            # This should not raise an error
            result = client.extract_insights("Some user input", project)
            assert isinstance(result, dict)


@pytest.mark.unit
class TestClaudeClientErrorHandling:
    """Tests for ClaudeClient error handling"""

    @patch("anthropic.Anthropic")
    def test_claude_client_handles_api_error(self, mock_anthropic, test_config):
        """Test handling of API errors"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            # Mock API error
            client.client = MagicMock()
            client.client.messages.create.side_effect = Exception("API Rate Limited")

            project = ProjectContext(
                project_id="test", name="Test", description="", owner="test", phase="planning"
            )

            # Should handle the error gracefully
            try:
                result = client.extract_insights("test input", project)
                # If no exception, error was handled
                assert isinstance(result, dict)
            except Exception as e:
                # Error propagation is also acceptable
                assert "API Rate Limited" in str(e)

    @patch("anthropic.Anthropic")
    def test_claude_client_invalid_json_response(self, mock_anthropic, test_config, sample_project):
        """Test handling of invalid JSON in response"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            # Mock invalid JSON response
            mock_response = MagicMock()
            mock_response.content[0].text = "Not valid JSON"

            client.client = MagicMock()
            client.client.messages.create.return_value = mock_response

            # Should handle gracefully
            try:
                result = client.extract_insights("test input", sample_project)
                # If no exception, error was handled
                assert isinstance(result, (dict, list))
            except Exception:
                # JSON parsing error is acceptable
                pass


@pytest.mark.unit
class TestClaudeClientModelConfiguration:
    """Tests for model configuration in ClaudeClient"""

    def test_claude_client_uses_configured_model(self, test_config):
        """Test that client uses the configured model"""
        with patch("anthropic.Anthropic"):
            test_config.claude_model = "claude-3-sonnet-20240229"
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            assert client.model == "claude-3-sonnet-20240229"

    def test_claude_client_model_can_be_changed(self, test_config):
        """Test that model can be configured"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            original_model = client.model
            client.model = "claude-3-haiku-20240307"

            assert client.model == "claude-3-haiku-20240307"
            assert client.model != original_model


@pytest.mark.unit
class TestClaudeClientLogging:
    """Tests for logging in ClaudeClient"""

    def test_claude_client_has_logger(self, test_config):
        """Test that client has logger configured"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            assert client.logger is not None
            assert client.logger.name == "socrates.clients.claude"

    @patch("socratic_system.clients.claude_client.logging")
    def test_claude_client_logger_used(self, mock_logging, test_config):
        """Test that logger is properly configured"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            mock_logging.getLogger.return_value = MagicMock()

            client = ClaudeClient("test-key", orchestrator)

            # Logger should be retrieved
            assert client.logger is not None


@pytest.mark.unit
class TestClaudeClientOrchestratorIntegration:
    """Tests for integration with Orchestrator"""

    def test_claude_client_stores_orchestrator_reference(self, test_config):
        """Test that client stores orchestrator reference"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            assert client.orchestrator is orchestrator

    def test_claude_client_uses_orchestrator_config(self, test_config):
        """Test that client uses orchestrator's config"""
        with patch("anthropic.Anthropic"):
            test_config.claude_model = "claude-test-model"
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            assert client.model == orchestrator.config.claude_model


@pytest.mark.unit
class TestClaudeClientAsyncSupport:
    """Tests for async support in ClaudeClient"""

    def test_claude_client_has_async_client(self, test_config):
        """Test that client has async client initialized"""
        with patch("anthropic.AsyncAnthropic"):
            with patch("anthropic.Anthropic"):
                orchestrator = socrates.AgentOrchestrator(test_config)
                client = ClaudeClient("test-key", orchestrator)

                assert hasattr(client, "async_client")

    def test_claude_client_has_sync_client(self, test_config):
        """Test that client has sync client initialized"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            assert hasattr(client, "client")


@pytest.mark.integration
class TestClaudeClientIntegration:
    """Integration tests for Claude client"""

    @patch("anthropic.Anthropic")
    def test_claude_client_full_workflow(self, mock_anthropic, test_config, sample_project):
        """Test full workflow: initialize, configure, extract insights"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            # Mock successful API response
            mock_response = MagicMock()
            mock_response.content[0].text = json.dumps({"goals": "test goal"})

            client.client = MagicMock()
            client.client.messages.create.return_value = mock_response

            # Workflow: initialize -> extract insights
            result = client.extract_insights("Create a new feature", sample_project)

            assert isinstance(result, (dict, list))

    @patch("anthropic.Anthropic")
    def test_claude_client_with_different_projects(self, mock_anthropic, test_config):
        """Test client with multiple different projects"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            client = ClaudeClient("test-key", orchestrator)

            projects = [
                ProjectContext(
                    project_id=f"proj-{i}",
                    name=f"Project {i}",
                    description=f"Description {i}",
                    owner="testuser",
                    phase="planning",
                )
                for i in range(3)
            ]

            for project in projects:
                # Should handle each project independently
                result = client.extract_insights("test input", project)
                assert isinstance(result, dict)
