"""
Phase 2B: ProjectManagerAgent Migration Tests

Tests for ProjectManagerAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Project CRUD operations
- Team collaboration features
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_system.agents.project_manager import ProjectManagerAgent


class TestProjectManagerMigrationSetup:
    """Test ProjectManagerAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = ProjectManagerAgent(mock_orchestrator)

        assert agent.name == "ProjectManager"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = ProjectManagerAgent(mock_orchestrator)

        # Agent should attempt to register
        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ProjectManagerAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "project_management" in capabilities
        assert "project_creation" in capabilities
        assert "project_import" in capabilities
        assert "team_collaboration" in capabilities
        assert "project_archival" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ProjectManagerAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestProjectManagerSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_load_project_success(self):
        """Test sync load project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "load_project", "project_id": "proj-123"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["project"] == mock_project

    def test_process_load_project_not_found(self):
        """Test sync load project when not found."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.load_project = MagicMock(return_value=None)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "load_project", "project_id": "invalid-id"}

        result = agent.process(request)

        assert result["status"] == "error"
        assert "Project not found" in result["message"]

    def test_process_save_project_success(self):
        """Test sync save project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "save_project", "project": mock_project}

        result = agent.process(request)

        assert result["status"] == "success"
        mock_orchestrator.database.save_project.assert_called_once()

    def test_process_list_projects(self):
        """Test sync list projects action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_projects = [
            MagicMock(project_id="p1", name="Project 1", owner="alice", phase="discovery", status=None, updated_at=None),
            MagicMock(project_id="p2", name="Project 2", owner="alice", phase="active", status=None, updated_at=None),
        ]
        mock_orchestrator.database.get_user_projects = MagicMock(return_value=mock_projects)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "list_projects", "username": "alice"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert len(result["projects"]) == 2

    def test_process_archive_project(self):
        """Test sync archive project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_project.owner = "alice"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.archive_project = MagicMock(return_value=True)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {
            "action": "archive_project",
            "project_id": "proj-123",
            "requester": "alice",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_restore_project(self):
        """Test sync restore project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_project.owner = "alice"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.restore_project = MagicMock(return_value=True)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {
            "action": "restore_project",
            "project_id": "proj-123",
            "requester": "alice",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_delete_project_permanently(self):
        """Test sync delete project permanently action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_project.owner = "alice"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.permanently_delete_project = MagicMock(return_value=True)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {
            "action": "delete_project_permanently",
            "project_id": "proj-123",
            "requester": "alice",
            "confirmation": "DELETE",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_get_archived_projects(self):
        """Test sync get archived projects action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.get_archived_items = MagicMock(
            return_value=["proj-1", "proj-2"]
        )

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "get_archived_projects"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert len(result["archived_projects"]) == 2

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ProjectManagerAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestProjectManagerAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_load_project(self):
        """Test async load project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "load_project", "project_id": "proj-123"}

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert result["project"] == mock_project

    @pytest.mark.asyncio
    async def test_process_async_save_project(self):
        """Test async save project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "save_project", "project": mock_project}

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_list_projects(self):
        """Test async list projects action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_projects = [
            MagicMock(project_id="p1", name="Project 1", owner="alice", phase="discovery", status=None, updated_at=None),
        ]
        mock_orchestrator.database.get_user_projects = MagicMock(return_value=mock_projects)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "list_projects", "username": "alice"}

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert len(result["projects"]) == 1

    @pytest.mark.asyncio
    async def test_process_async_archive_project(self):
        """Test async archive project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_project.owner = "alice"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.archive_project = MagicMock(return_value=True)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {
            "action": "archive_project",
            "project_id": "proj-123",
            "requester": "alice",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_restore_project(self):
        """Test async restore project action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_project.owner = "alice"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.restore_project = MagicMock(return_value=True)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {
            "action": "restore_project",
            "project_id": "proj-123",
            "requester": "alice",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_delete_project(self):
        """Test async delete project permanently action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.name = "Test Project"
        mock_project.owner = "alice"
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.permanently_delete_project = MagicMock(return_value=True)

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {
            "action": "delete_project_permanently",
            "project_id": "proj-123",
            "requester": "alice",
            "confirmation": "DELETE",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_archived_projects(self):
        """Test async get archived projects action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.get_archived_items = MagicMock(
            return_value=["proj-1", "proj-2", "proj-3"]
        )

        agent = ProjectManagerAgent(mock_orchestrator)

        request = {"action": "get_archived_projects"}

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert len(result["archived_projects"]) == 3

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ProjectManagerAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestProjectManagerPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.get_archived_items = MagicMock(return_value=[])

        agent = ProjectManagerAgent(mock_orchestrator)

        bus_request = {
            "action": "get_archived_projects",
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

        agent = ProjectManagerAgent(mock_orchestrator)

        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
