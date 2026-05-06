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

from socratic_agents.socratic_counselor import SocraticCounselorAgent


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

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, 'process')
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, 'process_async')
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, 'name')
        assert isinstance(agent.name, str)


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
        agent._generate_question = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_question",
            "project": MagicMock(phase="discovery"),
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._generate_question.assert_called_once_with(request)

    def test_process_process_response_success(self):
        """Test sync process response action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.context_analyzer = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        mock_result = {"status": "success", "insights": {}}
        agent._process_response = MagicMock(return_value=mock_result)

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
        agent._extract_insights_only = MagicMock(return_value=mock_result)

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
        agent._advance_phase = MagicMock(return_value=mock_result)

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
        agent._generate_question = MagicMock(return_value=mock_result)

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
        agent._process_response = MagicMock(return_value=mock_result)

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
        agent._generate_hint = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "generate_hint",
            "project": MagicMock(phase="discovery"),
            "message_id": "msg-111",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SocraticCounselorAgent(mock_orchestrator)

        # Agent must have core interface
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'orchestrator')
        assert hasattr(agent, 'process')
        assert hasattr(agent, 'process_async')

        # Verify they're callable/accessible
        assert isinstance(agent.name, str)
        assert agent.orchestrator is mock_orchestrator
        assert callable(agent.process)
        assert callable(agent.process_async)
