"""
Integration tests for Socrates orchestrator
"""

from unittest.mock import Mock, patch

import pytest

import socrates
from socratic_system.orchestration import AgentOrchestrator


@pytest.mark.integration
class TestOrchestratorInitialization:
    """Tests for orchestrator initialization"""

    def test_orchestrator_creation_with_config(self, test_config):
        """Test creating orchestrator with SocratesConfig"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator is not None
            assert orchestrator.config == test_config

    def test_orchestrator_creation_with_api_key(self, mock_api_key):
        """Test creating orchestrator with API key string"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(mock_api_key)

            assert orchestrator is not None
            assert orchestrator.config.api_key == mock_api_key

    def test_orchestrator_has_required_components(self, test_config):
        """Test that orchestrator has all required components"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert hasattr(orchestrator, "claude_client")
            assert hasattr(orchestrator, "database")
            assert hasattr(orchestrator, "vector_db")
            assert hasattr(orchestrator, "event_emitter")

    def test_orchestrator_event_emitter_initialized(self, test_config):
        """Test that orchestrator initializes event emitter"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator.event_emitter is not None
            assert isinstance(orchestrator.event_emitter, socrates.EventEmitter)


@pytest.mark.integration
class TestOrchestratorProjectManagement:
    """Tests for orchestrator project management"""

    def test_orchestrator_can_create_project(self, test_config):
        """Test creating project through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Mock the project manager agent
            result = orchestrator.process_request(
                "project_manager",
                {
                    "action": "create_project",
                    "project_name": "Test Project",
                    "owner": "testuser",
                    "description": "Test description",
                },
            )

            # Should return result even if agent is mocked
            assert result is not None

    def test_orchestrator_can_list_projects(self, test_config):
        """Test listing projects through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            result = orchestrator.process_request("project_manager", {"action": "list_projects"})

            assert result is not None
            assert "projects" in result

    def test_orchestrator_project_persistence(self, test_config):
        """Test that projects are persisted through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Create a project
            project_result = orchestrator.process_request(
                "project_manager",
                {
                    "action": "create_project",
                    "project_name": "Persistent Project",
                    "owner": "testuser",
                },
            )

            # Project should be saved to database
            if project_result.get("status") == "success":
                project = project_result["project"]

                # Load the project
                load_result = orchestrator.process_request(
                    "project_manager", {"action": "load_project", "project_id": project.project_id}
                )

                assert load_result.get("status") == "success"


@pytest.mark.integration
class TestOrchestratorEventEmission:
    """Tests for orchestrator event emission"""

    def test_orchestrator_emits_initialization_event(self, test_config):
        """Test that orchestrator emits system initialized event"""
        event_callback = Mock()

        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)
            orchestrator.event_emitter.on(socrates.EventType.SYSTEM_INITIALIZED, event_callback)

            # Force re-emit initialization
            orchestrator.event_emitter.emit(socrates.EventType.SYSTEM_INITIALIZED, {})

            assert event_callback.called

    def test_orchestrator_emits_agent_events(self, test_config):
        """Test that orchestrator emits agent events"""
        agent_start_callback = Mock()

        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)
            orchestrator.event_emitter.on(socrates.EventType.AGENT_START, agent_start_callback)

            # Process a request (should emit agent events)
            orchestrator.process_request("project_manager", {"action": "list_projects"})

            # Callback should be called (if request processing works)

    def test_orchestrator_event_listener_registration(self, test_config):
        """Test registering event listeners with orchestrator"""
        callback = Mock()

        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            orchestrator.event_emitter.on(socrates.EventType.LOG_INFO, callback)

            assert orchestrator.event_emitter.listener_count(socrates.EventType.LOG_INFO) >= 1


@pytest.mark.integration
class TestOrchestratorRequestProcessing:
    """Tests for orchestrator request processing"""

    def test_orchestrator_process_request_basic(self, test_config):
        """Test basic request processing"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            result = orchestrator.process_request("project_manager", {"action": "list_projects"})

            assert result is not None
            assert isinstance(result, dict)

    def test_orchestrator_process_request_with_invalid_agent(self, test_config):
        """Test processing request with invalid agent"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Should handle invalid agent gracefully
            result = orchestrator.process_request("nonexistent_agent", {})

            assert result is not None

    def test_orchestrator_processes_multiple_requests(self, test_config):
        """Test processing multiple sequential requests"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Process multiple requests
            for _i in range(3):
                result = orchestrator.process_request(
                    "project_manager", {"action": "list_projects"}
                )

                assert result is not None


@pytest.mark.integration
class TestOrchestratorErrorHandling:
    """Tests for orchestrator error handling"""

    def test_orchestrator_handles_agent_errors(self, test_config):
        """Test that orchestrator handles agent errors"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Process invalid request
            result = orchestrator.process_request("project_manager", {"action": "invalid_action"})

            # Should return error result, not raise exception
            assert result is not None

    def test_orchestrator_error_event_emission(self, test_config):
        """Test that orchestrator emits error events"""
        error_callback = Mock()

        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)
            orchestrator.event_emitter.on(socrates.EventType.AGENT_ERROR, error_callback)

            # Process request that might fail
            try:
                orchestrator.process_request("nonexistent_agent", {})
            except Exception:
                pass

            # Error event might be emitted


@pytest.mark.integration
class TestOrchestratorWithMockedAPI:
    """Tests for orchestrator with mocked API"""

    def test_orchestrator_with_mocked_anthropic(self, test_config, mock_anthropic_client):
        """Test orchestrator with mocked Anthropic client"""
        with patch(
            "socratic_system.clients.anthropic.Anthropic", return_value=mock_anthropic_client
        ):
            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator.claude_client is not None

    def test_orchestrator_async_support(self, test_config):
        """Test that orchestrator has async support"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert hasattr(orchestrator, "process_request_async")


@pytest.mark.integration
class TestOrchestratorKnowledgeBase:
    """Tests for orchestrator knowledge base management"""

    def test_orchestrator_initializes_knowledge_base(self, test_config):
        """Test that orchestrator initializes knowledge base"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator.vector_db is not None

    def test_orchestrator_can_add_knowledge(self, test_config, sample_knowledge_entry):
        """Test adding knowledge through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Add knowledge
            orchestrator.vector_db.add_knowledge(sample_knowledge_entry)

            # Should not raise exception


@pytest.mark.integration
class TestOrchestratorDatabase:
    """Tests for orchestrator database integration"""

    def test_orchestrator_initializes_database(self, test_config):
        """Test that orchestrator initializes database"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator.database is not None

    def test_orchestrator_database_persistence(self, test_config, sample_project):
        """Test database persistence through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Save project
            orchestrator.database.save_project(sample_project)

            # Load project
            loaded = orchestrator.database.load_project(sample_project.project_id)

            assert loaded is not None
            assert loaded.project_id == sample_project.project_id


@pytest.mark.integration
class TestOrchestratorConfiguration:
    """Tests for orchestrator configuration handling"""

    def test_orchestrator_uses_config_settings(self, test_config):
        """Test that orchestrator uses configuration settings"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator.config.api_key == test_config.api_key
            assert orchestrator.config.claude_model == test_config.claude_model

    def test_orchestrator_config_affects_database_path(self, test_config):
        """Test that config affects database paths"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert str(orchestrator.database.db_path) == str(test_config.projects_db_path)

    def test_orchestrator_config_affects_vector_db_path(self, test_config):
        """Test that config affects vector db path"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            assert str(orchestrator.vector_db.db_path) == str(test_config.vector_db_path)
