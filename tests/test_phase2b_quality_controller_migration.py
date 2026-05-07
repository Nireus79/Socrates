"""
Phase 2B: QualityControllerAgent Migration Tests

Tests for QualityControllerAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Quality control and maturity tracking
"""

import asyncio
from unittest.mock import MagicMock

import pytest
from socratic_agents.quality_controller import QualityControllerAgent


class TestQualityControllerMigrationSetup:
    """Test QualityControllerAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        assert agent.name == "QualityController"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, "process_async")
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, "name")
        assert isinstance(agent.name, str)


class TestQualityControllerSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_handles_calculate_maturity_action(self):
        """Test agent recognizes and handles calculate_maturity action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        request = {
            "action": "calculate_maturity",
            "project": MagicMock(
                name="Test",
                phase="discovery",
                project_type="software",
                phase_maturity_scores={"discovery": 75.0},
                categorized_specs={"discovery": []},
                category_scores={},
            ),
        }

        result = agent.process(request)
        assert isinstance(result, dict)
        assert "status" in result

    def test_process_handles_get_readiness_action(self):
        """Test agent recognizes and handles get_readiness action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        request = {
            "action": "get_readiness",
            "project": MagicMock(
                name="Test",
                phase="discovery",
                project_type="software",
                phase_maturity_scores={"discovery": 85.0},
                categorized_specs={"discovery": []},
                category_scores={},
            ),
        }

        result = agent.process(request)
        assert isinstance(result, dict)
        assert "status" in result

    def test_process_update_after_response_success(self):
        """Test sync update maturity after response action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        mock_result = {"status": "success", "new_score": 80.0}
        agent._update_maturity_after_response = MagicMock(return_value=mock_result)

        request = {
            "action": "update_after_response",
            "project": MagicMock(),
            "insights": {},
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_handles_get_maturity_summary_action(self):
        """Test agent recognizes and handles get_maturity_summary action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        request = {
            "action": "get_maturity_summary",
            "project": MagicMock(
                name="Test",
                project_type="software",
                phase_maturity_scores={"discovery": 75.0},
                categorized_specs={"discovery": []},
                category_scores={},
            ),
        }

        result = agent.process(request)
        assert isinstance(result, dict)
        assert "status" in result

    def test_process_handles_verify_advancement_action(self):
        """Test agent recognizes and handles verify_advancement action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        request = {
            "action": "verify_advancement",
            "project": MagicMock(
                name="Test",
                phase="discovery",
                project_type="software",
                phase_maturity_scores={"discovery": 85.0},
                categorized_specs={"discovery": []},
                category_scores={},
            ),
        }

        result = agent.process(request)
        assert isinstance(result, dict)
        assert "status" in result

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestQualityControllerAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_calculate_maturity(self):
        """Test async calculate maturity action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        request = {
            "action": "calculate_maturity",
            "project": MagicMock(
                name="Test",
                phase="discovery",
                project_type="software",
                phase_maturity_scores={"discovery": 75.0},
                categorized_specs={"discovery": []},
                category_scores={},
            ),
        }

        result = await agent.process_async(request)

        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_process_async_get_readiness(self):
        """Test async get readiness action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        request = {
            "action": "get_readiness",
            "project": MagicMock(
                name="Test",
                phase="discovery",
                project_type="software",
                phase_maturity_scores={"discovery": 85.0},
                categorized_specs={"discovery": []},
                category_scores={},
            ),
        }

        result = await agent.process_async(request)

        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestQualityControllerPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        bus_request = {
            "action": "get_maturity_summary",
            "project": MagicMock(
                name="Test",
                project_type="software",
                phase_maturity_scores={"discovery": 75.0, "analysis": 80.0},
                categorized_specs={"discovery": [], "analysis": []},
                category_scores={},
            ),
            "message_id": "msg-555",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert isinstance(result, dict)
        assert "status" in result

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = QualityControllerAgent(mock_orchestrator)

        # Agent must have core interface
        assert hasattr(agent, "name")
        assert hasattr(agent, "orchestrator")
        assert hasattr(agent, "process")
        assert hasattr(agent, "process_async")

        # Verify they're callable/accessible
        assert isinstance(agent.name, str)
        assert agent.orchestrator is mock_orchestrator
        assert callable(agent.process)
        assert callable(agent.process_async)
