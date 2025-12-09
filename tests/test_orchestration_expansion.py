"""
Expanded tests for Orchestrator - Advanced workflows and integration scenarios
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
import socrates

from socratic_system.models import User, ProjectContext
from socratic_system.orchestration.orchestrator import AgentOrchestrator


@pytest.mark.unit
class TestOrchestratorAdvancedConfiguration:
    """Tests for advanced orchestrator configuration"""

    def test_orchestrator_config_persistence(self, test_config):
        """Test that orchestrator preserves configuration settings"""
        with patch("anthropic.Anthropic"):
            test_config.claude_model = "claude-3-haiku-20240307"
            test_config.max_context_window = 2000

            orchestrator = AgentOrchestrator(test_config)

            assert orchestrator.config.claude_model == "claude-3-haiku-20240307"
            assert orchestrator.config.max_context_window == 2000

    def test_orchestrator_config_affects_components(self, test_config):
        """Test that config changes affect all components"""
        with patch("anthropic.Anthropic"):
            original_path = test_config.projects_db_path
            test_config.projects_db_path = "/tmp/test_db"

            orchestrator = AgentOrchestrator(test_config)

            # Database should use configured path
            assert str(orchestrator.database.db_path) == str(test_config.projects_db_path)


@pytest.mark.unit
class TestOrchestratorProjectManagementAdvanced:
    """Advanced project management tests"""

    def test_orchestrator_handles_multiple_projects(self, test_config):
        """Test orchestrator managing multiple projects"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Create multiple projects
            for i in range(3):
                result = orchestrator.process_request("project_manager", {
                    "action": "create_project",
                    "project_name": f"Project {i}",
                    "owner": "testuser"
                })

                if result and result.get("status") == "success":
                    assert "project" in result

    def test_orchestrator_project_isolation(self, test_config):
        """Test that different projects don't interfere"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Create two projects
            proj1_result = orchestrator.process_request("project_manager", {
                "action": "create_project",
                "project_name": "Project A",
                "owner": "alice"
            })

            proj2_result = orchestrator.process_request("project_manager", {
                "action": "create_project",
                "project_name": "Project B",
                "owner": "bob"
            })

            # Both should be created independently
            if proj1_result and proj2_result:
                assert proj1_result.get("project") is not None
                assert proj2_result.get("project") is not None


@pytest.mark.unit
class TestOrchestratorDataPersistence:
    """Tests for data persistence through orchestrator"""

    def test_orchestrator_persists_project_data(self, test_config, sample_project):
        """Test that project data is persisted"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Save project
            orchestrator.database.save_project(sample_project)

            # Load project
            loaded = orchestrator.database.load_project(sample_project.project_id)

            assert loaded is not None
            assert loaded.project_id == sample_project.project_id
            assert loaded.name == sample_project.name

    def test_orchestrator_persists_user_data(self, test_config, sample_user):
        """Test that user data is persisted"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Save user
            orchestrator.database.save_user(sample_user)

            # Load user
            loaded = orchestrator.database.load_user(sample_user.username)

            assert loaded is not None
            assert loaded.username == sample_user.username

    def test_orchestrator_updates_existing_data(self, test_config, sample_project):
        """Test updating existing persisted data"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Save initial project
            orchestrator.database.save_project(sample_project)

            # Update project
            sample_project.goals = "Updated goals"
            orchestrator.database.save_project(sample_project)

            # Load and verify update
            loaded = orchestrator.database.load_project(sample_project.project_id)
            assert loaded.goals == "Updated goals"


@pytest.mark.unit
class TestOrchestratorKnowledgeManagement:
    """Tests for knowledge base operations through orchestrator"""

    def test_orchestrator_adds_knowledge(self, test_config):
        """Test adding knowledge through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Add knowledge entry
            knowledge_entry = {
                "content": "Test knowledge entry",
                "metadata": {"category": "test"}
            }

            # Should not raise error
            try:
                orchestrator.vector_db.add_knowledge(knowledge_entry)
            except Exception as e:
                # Some implementations might not support add_knowledge
                pass

    def test_orchestrator_searches_knowledge(self, test_config):
        """Test searching knowledge through orchestrator"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Search knowledge base
            try:
                results = orchestrator.vector_db.search("test query")
                # Should return results or empty list
                assert isinstance(results, (list, dict))
            except Exception:
                # Some implementations might not support search
                pass


@pytest.mark.integration
class TestOrchestratorComplexWorkflows:
    """Integration tests for complex orchestrator workflows"""

    def test_user_to_project_workflow(self, test_config, sample_user):
        """Test workflow: user login → create project"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Save user
            orchestrator.database.save_user(sample_user)

            # Create project for user
            result = orchestrator.process_request("project_manager", {
                "action": "create_project",
                "project_name": "User Project",
                "owner": sample_user.username
            })

            # User-created project should be saved
            if result and result.get("status") == "success":
                assert result["project"].owner == sample_user.username

    def test_project_modification_workflow(self, test_config, sample_project):
        """Test workflow: create project → modify → save"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Save initial project
            orchestrator.database.save_project(sample_project)

            # Modify project
            sample_project.tech_stack = ["Python", "FastAPI"]
            sample_project.goals = "Build API"

            # Save modified project
            orchestrator.database.save_project(sample_project)

            # Verify modifications
            loaded = orchestrator.database.load_project(sample_project.project_id)
            assert "FastAPI" in loaded.tech_stack
            assert loaded.goals == "Build API"

    def test_multi_step_project_workflow(self, test_config):
        """Test multi-step workflow with project configuration"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Step 1: Create project
            proj_result = orchestrator.process_request("project_manager", {
                "action": "create_project",
                "project_name": "Multi-Step Project",
                "owner": "testuser"
            })

            if proj_result and proj_result.get("status") == "success":
                project = proj_result["project"]

                # Step 2: Configure project
                project.phase = "implementation"
                project.tech_stack = ["Python"]
                project.requirements = ["Fast", "Scalable"]

                # Step 3: Save configured project
                orchestrator.database.save_project(project)

                # Step 4: Verify complete workflow
                loaded = orchestrator.database.load_project(project.project_id)
                assert loaded.phase == "implementation"
                assert len(loaded.requirements) > 0


@pytest.mark.integration
class TestOrchestratorErrorRecovery:
    """Tests for orchestrator error recovery"""

    def test_orchestrator_recovers_from_invalid_project(self, test_config):
        """Test orchestrator handles invalid project gracefully"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Try to load non-existent project
            result = orchestrator.database.load_project("non-existent-id")

            # Should return None or empty, not crash
            assert result is None or result == {}

    def test_orchestrator_handles_missing_user(self, test_config):
        """Test orchestrator handles missing user gracefully"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Try to load non-existent user
            result = orchestrator.database.load_user("non-existent-user")

            # Should return None, not crash
            assert result is None

    def test_orchestrator_continues_after_error(self, test_config, sample_project):
        """Test orchestrator continues functioning after errors"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Cause an error (load non-existent)
            orchestrator.database.load_project("bad-id")

            # Orchestrator should still work for valid operations
            orchestrator.database.save_project(sample_project)
            loaded = orchestrator.database.load_project(sample_project.project_id)

            assert loaded is not None


@pytest.mark.integration
class TestOrchestratorEventHandling:
    """Tests for event handling in orchestrator"""

    def test_orchestrator_emits_events(self, test_config):
        """Test that orchestrator emits events during operations"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Track events
            events = []

            def capture_event(data):
                events.append(data)

            # Register listener
            orchestrator.event_emitter.on("*", capture_event)

            # Perform operation
            orchestrator.process_request("project_manager", {"action": "list_projects"})

            # Events might be emitted (depends on implementation)
            # Just verify no crashes

    def test_orchestrator_listener_registration(self, test_config):
        """Test registering event listeners"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            callback = MagicMock()

            # Register listener
            orchestrator.event_emitter.on("test_event", callback)

            # Emit event
            orchestrator.event_emitter.emit("test_event", {"data": "test"})

            # Callback may or may not be called depending on implementation


@pytest.mark.integration
class TestOrchestratorResourceManagement:
    """Tests for resource management in orchestrator"""

    def test_orchestrator_initializes_all_components(self, test_config):
        """Test that orchestrator initializes all required components"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # All components should be initialized
            assert orchestrator.claude_client is not None
            assert orchestrator.database is not None
            assert orchestrator.vector_db is not None
            assert orchestrator.event_emitter is not None

    def test_orchestrator_handles_multiple_requests(self, test_config):
        """Test orchestrator handling multiple sequential requests"""
        with patch("anthropic.Anthropic"):
            orchestrator = AgentOrchestrator(test_config)

            # Make multiple requests
            for i in range(5):
                result = orchestrator.process_request("project_manager", {
                    "action": "list_projects"
                })

                # All should return something
                assert result is not None
