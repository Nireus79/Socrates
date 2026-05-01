"""
Phase 2B: SocraticCounselorAgent Migration Tests

Tests for SocraticCounselorAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Socratic questioning and guided dialogue
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_system.agents.socratic_counselor import SocraticCounselorAgent


class TestSocraticCounselorMigrationSetup:
    """Test SocraticCounselorAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        assert agent.name == "SocraticCounselor"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()
        mock_bus.registry = mock_registry

        agent = SocraticCounselorAgent(mock_orchestrator)

        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "question_generation" in capabilities
        assert "response_processing" in capabilities
        assert "insight_extraction" in capabilities
        assert "phase_advancement" in capabilities
        assert "document_explanation" in capabilities
        assert "hint_generation" in capabilities
        assert "question_answering" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestSocraticCounselorSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_generate_question_success(self):
        """Test sync generate question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "question": "What problem does your project solve?",
        }
        agent._generate_question_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_question",
            "project": MagicMock(phase="discovery"),
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._generate_question_sync.assert_called_once_with(request)

    def test_process_process_response_success(self):
        """Test sync process response action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "insights": {}}
        agent._process_response_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "process_response",
            "project": MagicMock(),
            "response": "User response",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_extract_insights_success(self):
        """Test sync extract insights action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "insights": {}}
        agent._extract_insights_only_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "extract_insights_only",
            "project": MagicMock(),
            "response": "User response",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_advance_phase_success(self):
        """Test sync advance phase action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "new_phase": "analysis"}
        agent._advance_phase_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "advance_phase",
            "project": MagicMock(phase="discovery"),
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_toggle_dynamic_questions(self):
        """Test toggle dynamic questions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)
        initial_mode = agent.use_dynamic_questions

        request = {"action": "toggle_dynamic_questions"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["dynamic_mode"] != initial_mode

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestSocraticCounselorAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_generate_question(self):
        """Test async generate question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "question": "What problem?"}
        agent._generate_question_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_question",
            "project": MagicMock(phase="discovery"),
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_process_response(self):
        """Test async process response action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "insights": {}}
        agent._process_response_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "process_response",
            "project": MagicMock(),
            "response": "Response",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestSocraticCounselorPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "hint": "Keep making progress"}
        agent._generate_hint_sync = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "generate_hint",
            "project": MagicMock(phase="discovery"),
            "message_id": "msg-111",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_is_discoverable(self):
        """Test agent provides discovery information (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()
        mock_bus.registry = mock_registry

        agent = SocraticCounselorAgent(mock_orchestrator)

        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
