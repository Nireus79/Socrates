"""Phase 2B: CodeValidationAgent Migration Tests"""

import asyncio
from unittest.mock import MagicMock

import pytest
from socratic_agents.code_validation_agent import CodeValidationAgent


class TestCodeValidationMigrationSetup:
    """Test CodeValidationAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.agent_bus.registry = mock_orchestrator.agent_registry

        agent = CodeValidationAgent(mock_orchestrator)

        assert agent.name == "CodeValidation"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, "process_async")
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, "name")
        assert isinstance(agent.name, str)


class TestCodeValidationSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_validate_project_success(self):
        """Test sync validate project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "overall_status": "passed",
            "issues": [],
        }
        agent._validate_project = MagicMock(return_value=mock_result)

        request = {
            "action": "validate_project",
            "project_path": "/path/to/project",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._validate_project.assert_called_once_with(request)

    def test_process_validate_file_success(self):
        """Test sync validate file action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "file_valid": True,
        }
        agent._validate_file = MagicMock(return_value=mock_result)

        request = {
            "action": "validate_file",
            "file_path": "/path/to/file.py",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._validate_file.assert_called_once_with(request)

    def test_process_run_tests_success(self):
        """Test sync run tests action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "tests_passed": 10,
            "tests_failed": 0,
        }
        agent._run_tests = MagicMock(return_value=mock_result)

        request = {
            "action": "run_tests",
            "project_path": "/path/to/project",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._run_tests.assert_called_once_with(request)

    def test_process_check_syntax_success(self):
        """Test sync check syntax action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "syntax_valid": True,
        }
        agent._check_syntax = MagicMock(return_value=mock_result)

        request = {
            "action": "check_syntax",
            "target": "/path/to/target",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._check_syntax.assert_called_once_with(request)

    def test_process_check_dependencies_success(self):
        """Test sync check dependencies action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "dependencies_valid": True,
        }
        agent._check_dependencies = MagicMock(return_value=mock_result)

        request = {
            "action": "check_dependencies",
            "project_path": "/path/to/project",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._check_dependencies.assert_called_once_with(request)

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestCodeValidationAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_validate_project(self):
        """Test async validate project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "overall_status": "passed",
        }
        agent._validate_project = MagicMock(return_value=mock_result)

        request = {
            "action": "validate_project",
            "project_path": "/path/to/project",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_validate_file(self):
        """Test async validate file action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "file_valid": True,
        }
        agent._validate_file = MagicMock(return_value=mock_result)

        request = {
            "action": "validate_file",
            "file_path": "/path/to/file.py",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_run_tests(self):
        """Test async run tests action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "tests_passed": 10,
        }
        agent._run_tests = MagicMock(return_value=mock_result)

        request = {
            "action": "run_tests",
            "project_path": "/path/to/project",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_check_syntax(self):
        """Test async check syntax action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "syntax_valid": True,
        }
        agent._check_syntax = MagicMock(return_value=mock_result)

        request = {
            "action": "check_syntax",
            "target": "/path/to/target",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_check_dependencies(self):
        """Test async check dependencies action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "dependencies_valid": True,
        }
        agent._check_dependencies = MagicMock(return_value=mock_result)

        request = {
            "action": "check_dependencies",
            "project_path": "/path/to/project",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestCodeValidationPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "syntax_valid": True,
        }
        agent._check_syntax = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "check_syntax",
            "target": "/path/to/target",
            "message_id": "msg-333",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = CodeValidationAgent(mock_orchestrator)

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
