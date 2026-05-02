"""
Phase 2B: CodeGeneratorAgent Migration Tests

Tests for CodeGeneratorAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Code and documentation generation
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_system.agents.code_generator import CodeGeneratorAgent


class TestCodeGeneratorMigrationSetup:
    """Test CodeGeneratorAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        assert agent.name == "CodeGenerator"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = CodeGeneratorAgent(mock_orchestrator)

        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "code_generation" in capabilities
        assert "artifact_generation" in capabilities
        assert "documentation_generation" in capabilities
        assert "code_analysis" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestCodeGeneratorSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_generate_artifact_success(self):
        """Test sync generate artifact action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "artifact": "def hello(): pass",
            "artifact_type": "code",
        }
        agent._generate_artifact_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_artifact",
            "project": MagicMock(),
            "current_user": "alice",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._generate_artifact_sync.assert_called_once_with(request)

    def test_process_generate_documentation_success(self):
        """Test sync generate documentation action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "documentation": "# Project Documentation",
        }
        agent._generate_documentation_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_documentation",
            "project": MagicMock(),
            "artifact": "def hello(): pass",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_generate_script_legacy_support(self):
        """Test sync generate script action (legacy support)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "artifact": "def hello(): pass",
        }
        agent._generate_artifact_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_script",
            "project": MagicMock(),
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._generate_artifact_sync.assert_called_once()

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestCodeGeneratorAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_generate_artifact(self):
        """Test async generate artifact action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "artifact": "def hello(): pass",
            "artifact_type": "code",
        }
        agent._generate_artifact_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_artifact",
            "project": MagicMock(),
            "current_user": "alice",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_generate_documentation(self):
        """Test async generate documentation action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "documentation": "# Project Documentation",
        }
        agent._generate_documentation_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_documentation",
            "project": MagicMock(),
            "artifact": "def hello(): pass",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_generate_script_legacy(self):
        """Test async generate script action (legacy support)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {"status": "success", "artifact": "def hello(): pass"}
        agent._generate_artifact_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "generate_script",
            "project": MagicMock(),
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestCodeGeneratorPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeGeneratorAgent(mock_orchestrator)

        mock_result = {"status": "success", "documentation": "# Docs"}
        agent._generate_documentation_sync = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "generate_documentation",
            "project": MagicMock(),
            "artifact": "code",
            "message_id": "msg-789",
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
        mock_bus.registry = mock_registry

        agent = CodeGeneratorAgent(mock_orchestrator)

        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
