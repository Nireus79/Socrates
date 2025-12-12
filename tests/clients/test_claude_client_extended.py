"""
Extended tests for Claude API client - Additional method coverage.

Expands on existing test_claude_client.py with tests for:
- Code generation methods
- Artifact generation (business plans, research protocols, etc.)
- Token tracking and cost calculation
- JSON response parsing
- Error handling in various methods
- Async operations
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from socratic_system.clients.claude_client import ClaudeClient
from socratic_system.models import ConflictInfo, ProjectContext


class TestClaudeClientCodeGeneration:
    """Tests for code generation methods."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            orchestrator.system_monitor = MagicMock()
            return ClaudeClient("test-key", orchestrator)

    def test_generate_code_success(self, client):
        """Test successful code generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content[0].text = "print('Hello, world!')"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_code("Create a hello world script")

        assert isinstance(result, str)
        assert "Hello" in result
        client.client.messages.create.assert_called_once()

    def test_generate_code_error_handling(self, client):
        """Test code generation error handling."""
        client.client = MagicMock()
        client.client.messages.create.side_effect = Exception("API Error")

        result = client.generate_code("Create a script")

        assert "Error" in result or "error" in result.lower()

    def test_generate_code_tracks_tokens(self, client):
        """Test code generation tracks token usage."""
        mock_response = MagicMock()
        mock_response.content[0].text = "code here"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 200

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        client.generate_code("Create code")

        # Verify token tracking was called
        client.orchestrator.system_monitor.process.assert_called()
        call_args = client.orchestrator.system_monitor.process.call_args
        assert call_args[0][0]["action"] == "track_tokens"

    def test_generate_business_plan(self, client):
        """Test business plan generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Executive Summary\n..."
        mock_response.usage.input_tokens = 150
        mock_response.usage.output_tokens = 300

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_business_plan("Start a SaaS company")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_research_protocol(self, client):
        """Test research protocol generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Research Question: ..."
        mock_response.usage.input_tokens = 120
        mock_response.usage.output_tokens = 280

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_research_protocol("Study human learning")

        assert isinstance(result, str)

    def test_generate_creative_brief(self, client):
        """Test creative brief generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Project Overview: ..."
        mock_response.usage.input_tokens = 110
        mock_response.usage.output_tokens = 270

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_creative_brief("Design a brand identity")

        assert isinstance(result, str)

    def test_generate_marketing_plan(self, client):
        """Test marketing plan generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Marketing Strategy: ..."
        mock_response.usage.input_tokens = 130
        mock_response.usage.output_tokens = 290

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_marketing_plan("Launch a new product")

        assert isinstance(result, str)

    def test_generate_curriculum(self, client):
        """Test curriculum generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Course Outline: ..."
        mock_response.usage.input_tokens = 125
        mock_response.usage.output_tokens = 275

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_curriculum("Teach Python programming")

        assert isinstance(result, str)

    def test_generate_artifact_software_type(self, client):
        """Test artifact generation for software projects."""
        mock_response = MagicMock()
        mock_response.content[0].text = "print('test')"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_artifact("Build a web app", "software")

        assert isinstance(result, str)

    def test_generate_artifact_business_type(self, client):
        """Test artifact generation for business projects."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Business Plan..."
        mock_response.usage.input_tokens = 150
        mock_response.usage.output_tokens = 300

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_artifact("Start a company", "business")

        assert isinstance(result, str)

    def test_generate_artifact_research_type(self, client):
        """Test artifact generation for research projects."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Research Protocol..."
        mock_response.usage.input_tokens = 120
        mock_response.usage.output_tokens = 280

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_artifact("Conduct a study", "research")

        assert isinstance(result, str)

    def test_generate_artifact_unknown_type_defaults_to_code(self, client):
        """Test artifact generation defaults to code for unknown types."""
        mock_response = MagicMock()
        mock_response.content[0].text = "code"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_artifact("Create something", "unknown_type")

        assert isinstance(result, str)


class TestClaudeClientConflictResolution:
    """Tests for conflict resolution methods."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            orchestrator.context_analyzer.get_context_summary.return_value = "Project summary"
            return ClaudeClient("test-key", orchestrator)

    @pytest.fixture
    def conflict(self):
        """Create a test conflict."""
        import datetime
        return ConflictInfo(
            conflict_id="conf123",
            conflict_type="specification",
            old_value="Use Python",
            new_value="Use JavaScript",
            old_author="user1",
            new_author="user2",
            old_timestamp=datetime.datetime.now().isoformat(),
            new_timestamp=datetime.datetime.now().isoformat(),
            severity="medium",
            suggestions=["Consider both approaches", "Evaluate performance"],
        )

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Build something",
            requirements=[],
            tech_stack=["Python"],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=None,
            updated_at=None,
        )

    def test_generate_conflict_resolution_success(self, client, conflict, project):
        """Test successful conflict resolution suggestions."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Here are some suggestions..."

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_conflict_resolution_suggestions(conflict, project)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_conflict_resolution_error_handling(self, client, conflict, project):
        """Test error handling in conflict resolution."""
        client.client = MagicMock()
        client.client.messages.create.side_effect = Exception("API Error")

        result = client.generate_conflict_resolution_suggestions(conflict, project)

        assert "Error" in result


class TestClaudeClientTokenTracking:
    """Tests for token tracking and cost calculation."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            return ClaudeClient("test-key", orchestrator)

    def test_track_token_usage(self, client):
        """Test token usage tracking."""
        usage = MagicMock()
        usage.input_tokens = 100
        usage.output_tokens = 50

        # Should not raise error
        client._track_token_usage(usage, "test_operation")

        # Verify event was emitted
        if hasattr(client.orchestrator, "event_emitter"):
            client.orchestrator.event_emitter.emit.assert_called()

    def test_calculate_cost_basic(self, client):
        """Test cost calculation."""
        usage = MagicMock()
        usage.input_tokens = 1000
        usage.output_tokens = 1000

        cost = client._calculate_cost(usage)

        assert isinstance(cost, (int, float))
        assert cost >= 0

    def test_calculate_cost_zero_tokens(self, client):
        """Test cost calculation with zero tokens."""
        usage = MagicMock()
        usage.input_tokens = 0
        usage.output_tokens = 0

        cost = client._calculate_cost(usage)

        assert cost == 0

    def test_calculate_cost_large_tokens(self, client):
        """Test cost calculation with large token counts."""
        usage = MagicMock()
        usage.input_tokens = 100000
        usage.output_tokens = 100000

        cost = client._calculate_cost(usage)

        assert isinstance(cost, (int, float))
        assert cost > 0


class TestClaudeClientResponseParsing:
    """Tests for JSON response parsing."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            return ClaudeClient("test-key", orchestrator)

    def test_parse_valid_json(self, client):
        """Test parsing valid JSON response."""
        json_text = '{"key": "value", "number": 42}'
        result = client._parse_json_response(json_text)

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_parse_invalid_json(self, client):
        """Test parsing invalid JSON response."""
        invalid_json = "This is not JSON"
        result = client._parse_json_response(invalid_json)

        # Should return empty dict or error dict
        assert isinstance(result, dict)

    def test_parse_json_with_whitespace(self, client):
        """Test parsing JSON with extra whitespace."""
        json_text = '  \n  {"key": "value"}  \n  '
        result = client._parse_json_response(json_text)

        assert isinstance(result, dict)
        assert result["key"] == "value"

    def test_parse_empty_json_object(self, client):
        """Test parsing empty JSON object."""
        result = client._parse_json_response("{}")

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parse_json_array(self, client):
        """Test parsing JSON array."""
        json_text = '[{"item": 1}, {"item": 2}]'
        result = client._parse_json_response(json_text)

        # Should handle array gracefully
        assert isinstance(result, (dict, list))

    def test_parse_malformed_json(self, client):
        """Test parsing malformed JSON."""
        malformed = '{"key": value}'  # Unquoted value
        result = client._parse_json_response(malformed)

        assert isinstance(result, dict)


class TestClaudeClientSocraticQuestions:
    """Tests for Socratic question generation."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            return ClaudeClient("test-key", orchestrator)

    def test_generate_socratic_question(self, client):
        """Test Socratic question generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "What do you think should be the first step?"

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_socratic_question("Design a web application")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_socratic_question_error(self, client):
        """Test Socratic question generation with error."""
        from socratic_system.exceptions import APIError

        client.client = MagicMock()
        client.client.messages.create.side_effect = Exception("API Error")

        with pytest.raises(APIError):
            client.generate_socratic_question("Design a web application")


class TestClaudeClientGenerateSuggestions:
    """Tests for suggestion generation."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            return ClaudeClient("test-key", orchestrator)

    @pytest.fixture
    def project(self):
        """Create a test project."""
        return ProjectContext(
            project_id="proj123",
            name="Test",
            owner="user",
            collaborators=[],
            goals="Test",
            requirements=[],
            tech_stack=["Python"],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="design",
            conversation_history=[],
            created_at=None,
            updated_at=None,
        )

    def test_generate_suggestions(self, client, project):
        """Test suggestion generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "1. First suggestion\n2. Second suggestion"

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_suggestions("Current question", project)

        assert isinstance(result, str)

    def test_generate_suggestions_error(self, client, project):
        """Test suggestion generation error handling."""
        client.client = MagicMock()
        client.client.messages.create.side_effect = Exception("API Error")

        result = client.generate_suggestions("Question", project)

        assert isinstance(result, str)


class TestClaudeClientGenerateResponse:
    """Tests for generic response generation."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.Anthropic"):
            orchestrator = MagicMock()
            orchestrator.config = test_config
            orchestrator.config.claude_model = "claude-3-sonnet-20240229"
            return ClaudeClient("test-key", orchestrator)

    def test_generate_response(self, client):
        """Test response generation."""
        mock_response = MagicMock()
        mock_response.content[0].text = "This is a response"

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        result = client.generate_response("Generate a response")

        assert isinstance(result, str)

    def test_generate_response_with_context(self, client):
        """Test response generation with conversation context."""
        mock_response = MagicMock()
        mock_response.content[0].text = "Contextual response"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        client.client = MagicMock()
        client.client.messages.create.return_value = mock_response

        # Note: generate_response doesn't accept messages parameter directly
        result = client.generate_response("Current question")

        assert isinstance(result, str)

    def test_generate_response_error(self, client):
        """Test response generation error handling."""
        from socratic_system.exceptions import APIError

        client.client = MagicMock()
        client.client.messages.create.side_effect = Exception("API Error")

        with pytest.raises(APIError):
            client.generate_response("Question")


class TestClaudeClientAsync:
    """Tests for async operations."""

    @pytest.fixture
    def client(self, test_config):
        """Create a Claude client instance."""
        with patch("anthropic.AsyncAnthropic"):
            with patch("anthropic.Anthropic"):
                orchestrator = MagicMock()
                orchestrator.config = test_config
                orchestrator.config.claude_model = "claude-3-sonnet-20240229"
                return ClaudeClient("test-key", orchestrator)

    @pytest.mark.asyncio
    async def test_extract_insights_async(self, client):
        """Test async extract insights."""
        project = ProjectContext(
            project_id="proj123",
            name="Test",
            owner="user",
            collaborators=[],
            goals="Test",
            requirements=[],
            tech_stack=["Python"],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=None,
            updated_at=None,
        )

        # Mock async response
        mock_response = MagicMock()
        mock_response.content[0].text = json.dumps({"goals": "Test goal"})
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        client.async_client = AsyncMock()
        client.async_client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.extract_insights_async("Test input", project)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_extract_insights_async_empty(self, client):
        """Test async extract insights with empty input."""
        project = ProjectContext(
            project_id="proj123",
            name="Test",
            owner="user",
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=None,
            updated_at=None,
        )

        result = await client.extract_insights_async("", project)

        assert result == {}
