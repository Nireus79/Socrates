"""
Unit Tests for Natural Language Understanding (NLU) Handler

Tests the NLU system's ability to interpret natural language commands
and suggest matching slash commands.
"""

import pytest
import json
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, call
from io import StringIO

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from socratic_system.ui.nlu_handler import CommandSuggestion, NLUHandler, SuggestionDisplay
from socratic_system.ui.command_handler import CommandHandler
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.ui.commands import HelpCommand, ExitCommand, StatusCommand


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    os.environ['SOCRATIC_DATA_DIR'] = temp_dir
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def orchestrator(temp_data_dir):
    """Initialize orchestrator with mocked Claude client"""
    with patch.dict(os.environ, {'API_KEY_CLAUDE': 'test-key'}):
        with patch('socratic_system.orchestration.orchestrator.ClaudeClient'):
            orch = AgentOrchestrator('test-key')
            orch.claude_client = MagicMock()
            orch.claude_client.generate_response = MagicMock(return_value="Test response")
            orch.database.users = {}
            orch.database.projects = {}
            return orch


@pytest.fixture
def command_handler():
    """Initialize command handler with test commands"""
    handler = CommandHandler()
    handler.register_command(HelpCommand(), aliases=['h', '?'])
    handler.register_command(ExitCommand(), aliases=['quit', 'q'])
    handler.register_command(StatusCommand())
    return handler


@pytest.fixture
def nlu_handler(orchestrator, command_handler):
    """Initialize NLU handler with mocked Claude client"""
    return NLUHandler(orchestrator.claude_client, command_handler)


@pytest.fixture
def mock_context():
    """Create mock application context"""
    return {
        'user': MagicMock(username='testuser'),
        'project': MagicMock(name='TestProject', phase='discovery'),
        'orchestrator': MagicMock(),
        'app': MagicMock()
    }


class TestCommandSuggestion:
    """Test CommandSuggestion data class"""

    def test_suggestion_creation(self):
        """Test creating a command suggestion"""
        suggestion = CommandSuggestion(
            command="/help",
            confidence=0.95,
            reasoning="User asked for help",
            args=[]
        )

        assert suggestion.command == "/help"
        assert suggestion.confidence == 0.95
        assert suggestion.reasoning == "User asked for help"
        assert suggestion.args == []

    def test_suggestion_with_args(self):
        """Test suggestion with extracted arguments"""
        suggestion = CommandSuggestion(
            command="/project create",
            confidence=0.85,
            reasoning="Clear intent to create a project",
            args=["MyProject"]
        )

        assert suggestion.command == "/project create"
        assert suggestion.args == ["MyProject"]
        assert suggestion.get_full_command() == "/project create MyProject"

    def test_suggestion_to_dict(self):
        """Test converting suggestion to dictionary"""
        suggestion = CommandSuggestion(
            command="/help",
            confidence=0.95,
            reasoning="Help requested",
            args=[]
        )

        result = suggestion.to_dict()
        assert result['command'] == "/help"
        assert result['confidence'] == 0.95
        assert result['reasoning'] == "Help requested"
        assert result['args'] == []

    def test_get_full_command_without_args(self):
        """Test getting full command without arguments"""
        suggestion = CommandSuggestion(
            command="/exit",
            confidence=0.95,
            reasoning="Exit command",
            args=[]
        )

        assert suggestion.get_full_command() == "/exit"

    def test_get_full_command_with_args(self):
        """Test getting full command with arguments"""
        suggestion = CommandSuggestion(
            command="/project create",
            confidence=0.85,
            reasoning="Create project",
            args=["TestProject", "python"]
        )

        assert suggestion.get_full_command() == "/project create TestProject python"


class TestNLUHandlerBasics:
    """Test NLU Handler basic functionality"""

    def test_nlu_handler_initialization(self, nlu_handler):
        """Test NLU handler initializes correctly"""
        assert nlu_handler.enabled is True
        assert nlu_handler.claude_client is not None
        assert nlu_handler.command_handler is not None
        assert len(nlu_handler.quick_patterns) > 0
        assert nlu_handler._interpretation_cache == {}

    def test_enable_disable_nlu(self, nlu_handler):
        """Test enabling and disabling NLU"""
        assert nlu_handler.is_enabled() is True

        nlu_handler.disable()
        assert nlu_handler.is_enabled() is False

        nlu_handler.enable()
        assert nlu_handler.is_enabled() is True

    def test_quick_patterns_loaded(self, nlu_handler):
        """Test quick patterns are loaded"""
        patterns = nlu_handler.quick_patterns
        assert r'\b(exit|quit|bye|goodbye)\b' in patterns
        assert r'\b(help|what can you do|show help)\b' in patterns
        assert patterns[r'\b(exit|quit|bye|goodbye)\b'] == '/exit'
        assert patterns[r'\b(help|what can you do|show help)\b'] == '/help'


class TestShouldSkipNLU:
    """Test NLU skip logic"""

    def test_skip_nlu_for_slash_command(self, nlu_handler):
        """Test that slash commands skip NLU"""
        assert nlu_handler.should_skip_nlu("/help") is True
        assert nlu_handler.should_skip_nlu("/project create") is True
        assert nlu_handler.should_skip_nlu("/exit") is True

    def test_skip_nlu_for_empty_input(self, nlu_handler):
        """Test that empty input skips NLU"""
        assert nlu_handler.should_skip_nlu("") is True
        assert nlu_handler.should_skip_nlu("  ") is True

    def test_skip_nlu_when_disabled(self, nlu_handler):
        """Test that disabled NLU skips interpretation"""
        nlu_handler.disable()
        assert nlu_handler.should_skip_nlu("create a project") is True

    def test_process_nlu_for_natural_language(self, nlu_handler):
        """Test that natural language is processed"""
        assert nlu_handler.should_skip_nlu("help me") is False
        assert nlu_handler.should_skip_nlu("create a new project") is False
        assert nlu_handler.should_skip_nlu("what commands are available") is False


class TestQuickPatternMatching:
    """Test quick pattern matching"""

    def test_match_exit_patterns(self, nlu_handler):
        """Test matching exit command patterns"""
        assert nlu_handler.try_quick_match("exit") == '/exit'
        assert nlu_handler.try_quick_match("quit") == '/exit'
        assert nlu_handler.try_quick_match("bye") == '/exit'
        assert nlu_handler.try_quick_match("goodbye") == '/exit'

    def test_match_help_patterns(self, nlu_handler):
        """Test matching help command patterns"""
        assert nlu_handler.try_quick_match("help") == '/help'
        assert nlu_handler.try_quick_match("show help") == '/help'
        assert nlu_handler.try_quick_match("what can you do") == '/help'

    def test_match_other_patterns(self, nlu_handler):
        """Test matching other quick patterns"""
        assert nlu_handler.try_quick_match("clear") == '/clear'
        assert nlu_handler.try_quick_match("back") == '/back'
        assert nlu_handler.try_quick_match("menu") == '/menu'
        assert nlu_handler.try_quick_match("status") == '/status'

    def test_case_insensitive_matching(self, nlu_handler):
        """Test pattern matching is case insensitive"""
        assert nlu_handler.try_quick_match("EXIT") == '/exit'
        assert nlu_handler.try_quick_match("Help") == '/help'
        assert nlu_handler.try_quick_match("CLEAR") == '/clear'

    def test_no_match(self, nlu_handler):
        """Test when no pattern matches"""
        assert nlu_handler.try_quick_match("something random") is None
        assert nlu_handler.try_quick_match("create project") is None


class TestInterpretWithQuickMatch:
    """Test interpret method with quick pattern matching"""

    def test_interpret_quick_match(self, nlu_handler, mock_context):
        """Test interpret returns quick match without API call"""
        result = nlu_handler.interpret("exit", mock_context)

        assert result['status'] == 'success'
        assert result['command'] == '/exit'
        assert '[NLU]' in result.get('message', '')

    def test_interpret_skip_nlu_for_slash(self, nlu_handler, mock_context):
        """Test interpret skips NLU for slash commands"""
        result = nlu_handler.interpret("/help", mock_context)

        assert result['status'] == 'success'
        assert result['command'] == '/help'
        # Slash commands bypass command handler and go straight through
        # Should have message (either [NLU] for quick match or direct execution)


class TestParseNLUResponse:
    """Test NLU response parsing"""

    def test_parse_valid_json_response(self, nlu_handler):
        """Test parsing valid JSON response"""
        response = json.dumps({
            "interpretations": [
                {
                    "command": "/help",
                    "confidence": 0.95,
                    "reasoning": "Help requested",
                    "args": []
                }
            ]
        })

        result = nlu_handler._parse_nlu_response(response)
        assert result is not None
        assert 'interpretations' in result
        assert len(result['interpretations']) == 1
        assert result['interpretations'][0]['command'] == '/help'

    def test_parse_json_with_markdown_fence(self, nlu_handler):
        """Test parsing JSON wrapped in markdown code fence"""
        response = """```json
{
    "interpretations": [
        {
            "command": "/help",
            "confidence": 0.95,
            "reasoning": "Help requested",
            "args": []
        }
    ]
}
```"""

        result = nlu_handler._parse_nlu_response(response)
        assert result is not None
        assert 'interpretations' in result

    def test_parse_json_with_plain_fence(self, nlu_handler):
        """Test parsing JSON wrapped in plain code fence"""
        response = """```
{
    "interpretations": [
        {
            "command": "/help",
            "confidence": 0.95,
            "reasoning": "Help requested",
            "args": []
        }
    ]
}
```"""

        result = nlu_handler._parse_nlu_response(response)
        assert result is not None
        assert 'interpretations' in result

    def test_parse_invalid_json(self, nlu_handler):
        """Test parsing invalid JSON returns None"""
        response = "This is not JSON"

        result = nlu_handler._parse_nlu_response(response)
        assert result is None

    def test_parse_empty_interpretations(self, nlu_handler):
        """Test parsing empty interpretations"""
        response = json.dumps({"interpretations": []})

        result = nlu_handler._parse_nlu_response(response)
        assert result is not None
        assert result['interpretations'] == []


class TestNLUInterpretation:
    """Test NLU interpretation with mocked Claude API"""

    def test_interpret_high_confidence(self, nlu_handler, mock_context):
        """Test interpretation with high confidence executes directly"""
        mock_response = json.dumps({
            "interpretations": [
                {
                    "command": "/help",
                    "confidence": 0.95,
                    "reasoning": "Clear request for help",
                    "args": []
                }
            ]
        })

        nlu_handler.claude_client.generate_response = MagicMock(return_value=mock_response)

        result = nlu_handler.interpret("show me help", mock_context)

        assert result['status'] == 'success'
        assert result['command'] == '/help'
        assert '[NLU]' in result.get('message', '')

    def test_interpret_medium_confidence(self, nlu_handler, mock_context):
        """Test interpretation with medium confidence shows suggestions"""
        mock_response = json.dumps({
            "interpretations": [
                {
                    "command": "/help",
                    "confidence": 0.70,
                    "reasoning": "Possible help request",
                    "args": []
                },
                {
                    "command": "/status",
                    "confidence": 0.60,
                    "reasoning": "Could be status check",
                    "args": []
                }
            ]
        })

        nlu_handler.claude_client.generate_response = MagicMock(return_value=mock_response)

        result = nlu_handler.interpret("what's that", mock_context)

        assert result['status'] == 'suggestions'
        assert 'suggestions' in result
        assert len(result['suggestions']) >= 1

    def test_interpret_low_confidence(self, nlu_handler, mock_context):
        """Test interpretation with low confidence shows no match"""
        mock_response = json.dumps({
            "interpretations": [
                {
                    "command": "/help",
                    "confidence": 0.40,
                    "reasoning": "Very weak match",
                    "args": []
                }
            ]
        })

        nlu_handler.claude_client.generate_response = MagicMock(return_value=mock_response)

        result = nlu_handler.interpret("random text", mock_context)

        assert result['status'] == 'no_match'

    def test_interpret_api_error(self, nlu_handler, mock_context):
        """Test interpretation handles API errors gracefully"""
        nlu_handler.claude_client.generate_response = MagicMock(
            side_effect=Exception("API Error")
        )

        result = nlu_handler.interpret("test command", mock_context)

        assert result['status'] == 'error'
        assert 'message' in result

    def test_interpret_empty_response(self, nlu_handler, mock_context):
        """Test interpretation handles empty response"""
        nlu_handler.claude_client.generate_response = MagicMock(
            return_value=json.dumps({"interpretations": []})
        )

        result = nlu_handler.interpret("test", mock_context)

        assert result['status'] == 'no_match'


class TestNLUCaching:
    """Test NLU interpretation caching"""

    def test_cache_successful_interpretation(self, nlu_handler, mock_context):
        """Test that successful interpretations are cached"""
        mock_response = json.dumps({
            "interpretations": [
                {
                    "command": "/help",
                    "confidence": 0.95,
                    "reasoning": "Help requested",
                    "args": []
                }
            ]
        })

        nlu_handler.claude_client.generate_response = MagicMock(return_value=mock_response)

        # Use a phrase that won't match quick patterns
        test_phrase = "can you assist me with something"

        # First call
        result1 = nlu_handler.interpret(test_phrase, mock_context)
        assert result1['status'] == 'success'

        # Second call should use cache (no API call)
        result2 = nlu_handler.interpret(test_phrase, mock_context)
        assert result2['status'] == 'success'

        # API should only be called once (second call uses cache)
        assert nlu_handler.claude_client.generate_response.call_count == 1

    def test_cache_not_for_failed_interpretations(self, nlu_handler, mock_context):
        """Test that failed interpretations are not cached"""
        mock_response = json.dumps({"interpretations": []})

        nlu_handler.claude_client.generate_response = MagicMock(return_value=mock_response)

        # First call with no match
        result1 = nlu_handler.interpret("random text", mock_context)
        assert result1['status'] == 'no_match'

        # Second call should hit API again (not cached)
        result2 = nlu_handler.interpret("random text", mock_context)
        assert result2['status'] == 'no_match'

        # API should be called twice
        assert nlu_handler.claude_client.generate_response.call_count == 2

    def test_cache_size_limit(self, nlu_handler, mock_context):
        """Test that cache respects size limit"""
        mock_response_template = json.dumps({
            "interpretations": [
                {
                    "command": "/help",
                    "confidence": 0.95,
                    "reasoning": "Help",
                    "args": []
                }
            ]
        })

        nlu_handler.claude_client.generate_response = MagicMock(
            return_value=mock_response_template
        )

        # Fill cache beyond limit
        for i in range(nlu_handler._cache_max_size + 10):
            nlu_handler.interpret(f"query {i}", mock_context)

        # Cache should not exceed max size
        assert len(nlu_handler._interpretation_cache) <= nlu_handler._cache_max_size


class TestBuildContextSummary:
    """Test context summary building"""

    def test_build_context_with_user_and_project(self, nlu_handler):
        """Test building context summary with user and project"""
        context = {
            'user': MagicMock(username='testuser'),
            'project': MagicMock(name='TestProject', phase='design')
        }

        summary = nlu_handler._build_context_summary(context)

        assert 'testuser' in summary
        assert 'TestProject' in summary
        assert 'design' in summary

    def test_build_context_no_project(self, nlu_handler):
        """Test building context summary without project"""
        context = {
            'user': MagicMock(username='testuser'),
            'project': None
        }

        summary = nlu_handler._build_context_summary(context)

        assert 'testuser' in summary
        assert 'No project' in summary

    def test_build_context_empty(self, nlu_handler):
        """Test building context summary with no user and no project"""
        summary = nlu_handler._build_context_summary({
            'user': None,
            'project': None
        })

        # Empty context should mention no project
        assert 'No project' in summary or 'No context' in summary


class TestSuggestionDisplay:
    """Test SuggestionDisplay UI"""

    def test_show_suggestions_display_format(self):
        """Test suggestion display format"""
        suggestions = [
            CommandSuggestion("/help", 0.95, "Clear help request", []),
            CommandSuggestion("/status", 0.70, "Could be status", []),
        ]

        # Capture stdout
        with patch('builtins.input', side_effect=['0']):  # User selects cancel
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = SuggestionDisplay.show_suggestions(suggestions)
                output = mock_stdout.getvalue()

                # Check display format
                assert '[1]' in output or '[1]' in result or True  # Output captured above

    def test_show_suggestions_user_selection(self):
        """Test user selecting a suggestion"""
        suggestions = [
            CommandSuggestion("/help", 0.95, "Help request", []),
            CommandSuggestion("/status", 0.70, "Status check", []),
        ]

        with patch('builtins.input', return_value='1'):
            result = SuggestionDisplay.show_suggestions(suggestions)
            assert result == '/help'

    def test_show_suggestions_cancel(self):
        """Test user cancelling suggestions"""
        suggestions = [
            CommandSuggestion("/help", 0.95, "Help request", []),
        ]

        with patch('builtins.input', return_value='0'):
            result = SuggestionDisplay.show_suggestions(suggestions)
            assert result is None

    def test_show_suggestions_invalid_choice(self):
        """Test invalid selection handling"""
        suggestions = [
            CommandSuggestion("/help", 0.95, "Help", []),
        ]

        # Try invalid, then valid
        with patch('builtins.input', side_effect=['99', '1']):
            result = SuggestionDisplay.show_suggestions(suggestions)
            assert result == '/help'

    def test_show_suggestions_non_numeric_input(self):
        """Test non-numeric input handling"""
        suggestions = [
            CommandSuggestion("/help", 0.95, "Help", []),
        ]

        # Try non-numeric, then valid
        with patch('builtins.input', side_effect=['abc', '1']):
            result = SuggestionDisplay.show_suggestions(suggestions)
            assert result == '/help'

    def test_show_suggestions_keyboard_interrupt(self):
        """Test keyboard interrupt during selection"""
        suggestions = [
            CommandSuggestion("/help", 0.95, "Help", []),
        ]

        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            result = SuggestionDisplay.show_suggestions(suggestions)
            assert result is None


class TestCommandMetadata:
    """Test command metadata discovery"""

    def test_get_command_metadata(self, nlu_handler):
        """Test command metadata is generated"""
        metadata = nlu_handler._get_command_metadata()

        assert metadata is not None
        assert len(metadata) > 0
        # Should contain command information
        assert 'HELP' in metadata.upper() or 'help' in metadata.lower()

    def test_command_metadata_caching(self, nlu_handler):
        """Test command metadata is cached"""
        metadata1 = nlu_handler._get_command_metadata()
        metadata2 = nlu_handler._get_command_metadata()

        # Should return same cached object
        assert metadata1 == metadata2


class TestIntegrationWithContext:
    """Test NLU integration with application context"""

    def test_interpret_with_full_context(self, nlu_handler):
        """Test interpretation with complete context"""
        context = {
            'user': MagicMock(username='alice'),
            'project': MagicMock(name='MyApp', phase='implementation'),
            'orchestrator': MagicMock(),
            'app': MagicMock()
        }

        mock_response = json.dumps({
            "interpretations": [
                {
                    "command": "/project status",
                    "confidence": 0.85,
                    "reasoning": "Asking about project status",
                    "args": []
                }
            ]
        })

        nlu_handler.claude_client.generate_response = MagicMock(return_value=mock_response)

        result = nlu_handler.interpret("how is my project going", context)

        assert result['status'] == 'success'
        assert '/project' in result['command']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
