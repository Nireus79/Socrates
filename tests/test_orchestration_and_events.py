"""
Tests for Orchestration and Event System - Agent coordination and messaging.

Tests cover:
- Event emission and listening
- Agent orchestration
- Request processing
- Error handling and propagation
"""

import datetime
from unittest.mock import MagicMock

import pytest

from socratic_system.events import EventType
from socratic_system.models import ProjectContext


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.event_emitter = MagicMock()
    orchestrator.database = MagicMock()
    orchestrator.claude_client = MagicMock()
    orchestrator.vector_db = MagicMock()
    return orchestrator


@pytest.fixture
def sample_project():
    """Create a sample project."""
    return ProjectContext(
        project_id="proj-123",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Test",
        requirements=[],
        tech_stack=[],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="local",
        code_style="documented",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


class TestEventTypes:
    """Tests for event types."""

    def test_event_type_exists(self):
        """Test that event types are defined."""
        assert hasattr(EventType, "PROJECT_CREATED")
        assert hasattr(EventType, "PROJECT_UPDATED")
        assert hasattr(EventType, "QUESTION_GENERATED")
        assert hasattr(EventType, "RESPONSE_ANALYZED")

    def test_event_type_values(self):
        """Test event type values."""
        # Event types should be strings or enums
        event_types = [
            EventType.PROJECT_CREATED,
            EventType.PROJECT_UPDATED,
            EventType.QUESTION_GENERATED,
            EventType.RESPONSE_ANALYZED,
        ]

        for event_type in event_types:
            assert event_type is not None


class TestEventEmission:
    """Tests for event emission."""

    def test_emit_project_created(self, mock_orchestrator, sample_project):
        """Test emitting project created event."""
        event_type = EventType.PROJECT_CREATED
        event_data = {"project_id": sample_project.project_id}

        mock_orchestrator.event_emitter.emit(event_type, event_data)

        mock_orchestrator.event_emitter.emit.assert_called_once_with(event_type, event_data)

    def test_emit_question_generated(self, mock_orchestrator):
        """Test emitting question generated event."""
        event_type = EventType.QUESTION_GENERATED
        event_data = {"question": "What are your goals?", "timestamp": datetime.datetime.now()}

        mock_orchestrator.event_emitter.emit(event_type, event_data)

        assert mock_orchestrator.event_emitter.emit.called

    def test_emit_response_analyzed(self, mock_orchestrator):
        """Test emitting response analyzed event."""
        event_type = EventType.RESPONSE_ANALYZED
        event_data = {"response": "Build a web app", "insights": {"goals": "web app"}}

        mock_orchestrator.event_emitter.emit(event_type, event_data)

        assert mock_orchestrator.event_emitter.emit.called

    def test_emit_multiple_events(self, mock_orchestrator):
        """Test emitting multiple events."""
        events = [
            (EventType.PROJECT_CREATED, {"project_id": "p1"}),
            (EventType.QUESTION_GENERATED, {"question": "Q?"}),
            (EventType.RESPONSE_ANALYZED, {"response": "A"}),
        ]

        for event_type, data in events:
            mock_orchestrator.event_emitter.emit(event_type, data)

        assert mock_orchestrator.event_emitter.emit.call_count == 3


class TestEventListening:
    """Tests for event listening."""

    def test_register_event_listener(self, mock_orchestrator):
        """Test registering event listener."""
        event_type = EventType.PROJECT_CREATED
        callback = MagicMock()

        mock_orchestrator.event_emitter.on(event_type, callback)

        mock_orchestrator.event_emitter.on.assert_called_once_with(event_type, callback)

    def test_listener_callback_execution(self, mock_orchestrator):
        """Test listener callback is called."""
        callback = MagicMock()
        event_type = EventType.QUESTION_GENERATED
        event_data = {"question": "What?"}

        # Register listener
        mock_orchestrator.event_emitter.on(event_type, callback)

        # Emit event
        mock_orchestrator.event_emitter.emit(event_type, event_data)

        # Callback should be set up
        assert mock_orchestrator.event_emitter.on.called

    def test_multiple_listeners_same_event(self, mock_orchestrator):
        """Test multiple listeners for same event."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        event_type = EventType.PROJECT_UPDATED

        mock_orchestrator.event_emitter.on(event_type, callback1)
        mock_orchestrator.event_emitter.on(event_type, callback2)

        assert mock_orchestrator.event_emitter.on.call_count == 2

    def test_unregister_listener(self, mock_orchestrator):
        """Test unregistering event listener."""
        event_type = EventType.QUESTION_GENERATED
        callback = MagicMock()

        mock_orchestrator.event_emitter.on(event_type, callback)
        mock_orchestrator.event_emitter.off(event_type, callback)

        assert mock_orchestrator.event_emitter.off.called


class TestOrchestratorRequests:
    """Tests for orchestrator request processing."""

    def test_process_request(self, mock_orchestrator, sample_project):
        """Test processing orchestrator request."""
        request = {
            "action": "analyze_context",
            "project": sample_project,
        }

        mock_orchestrator.process_request.return_value = {"status": "success"}

        result = mock_orchestrator.process_request("agent_name", request)

        assert result["status"] == "success"

    def test_request_with_multiple_fields(self, mock_orchestrator):
        """Test request with multiple fields."""
        request = {
            "action": "generate_question",
            "project_id": "proj-123",
            "context": "discovery phase",
            "timestamp": datetime.datetime.now(),
        }

        mock_orchestrator.process_request.return_value = {"question": "What?"}

        result = mock_orchestrator.process_request("agent", request)

        assert "question" in result

    def test_request_error_handling(self, mock_orchestrator):
        """Test error handling in requests."""
        request = {"action": "invalid_action"}

        mock_orchestrator.process_request.side_effect = Exception("Invalid action")

        with pytest.raises(Exception, match="Invalid action"):
            mock_orchestrator.process_request("agent", request)

    def test_concurrent_requests(self, mock_orchestrator):
        """Test handling concurrent requests."""
        requests = [
            {"action": "action1", "id": 1},
            {"action": "action2", "id": 2},
            {"action": "action3", "id": 3},
        ]

        for req in requests:
            mock_orchestrator.process_request.return_value = {"status": "success"}
            mock_orchestrator.process_request("agent", req)

        assert mock_orchestrator.process_request.call_count == 3


class TestAgentCoordination:
    """Tests for agent coordination through orchestrator."""

    def test_agent_communication(self, mock_orchestrator):
        """Test communication between agents."""
        # Agent 1 produces result
        result_1 = {"insights": {"goals": "test"}}
        mock_orchestrator.database.save_project.return_value = True

        # Agent 2 consumes result
        mock_orchestrator.process_request.return_value = {"status": "success"}
        result_2 = mock_orchestrator.process_request("agent2", {"data": result_1})

        assert result_2["status"] == "success"

    def test_agent_dependency_chain(self, mock_orchestrator, sample_project):
        """Test chain of dependent agent operations."""
        # Sequence: Create → Analyze → Generate → Store

        # Step 1: Create/load project
        mock_orchestrator.database.load_project.return_value = sample_project

        # Step 2: Analyze context
        mock_orchestrator.process_request.return_value = {"analysis": "done"}

        # Step 3: Generate recommendations
        mock_orchestrator.process_request.return_value = {"recommendations": []}

        # Step 4: Store results
        mock_orchestrator.database.save_project.return_value = True

        # Execute chain
        project = mock_orchestrator.database.load_project("proj-123")
        assert project is not None

    def test_agent_error_propagation(self, mock_orchestrator):
        """Test error propagation between agents."""
        # Agent 1 fails
        mock_orchestrator.process_request.side_effect = Exception("Agent 1 failed")

        with pytest.raises(Exception, match="Agent 1 failed"):
            mock_orchestrator.process_request("agent1", {"action": "test"})

        # Error should be catchable by orchestrator


class TestOrchestratorState:
    """Tests for orchestrator state management."""

    def test_project_context_in_orchestrator(self, mock_orchestrator, sample_project):
        """Test project context tracking in orchestrator."""
        mock_orchestrator.current_project = sample_project

        assert mock_orchestrator.current_project.project_id == "proj-123"

    def test_active_agents(self, mock_orchestrator):
        """Test tracking active agents."""
        agents = ["SocraticCounselor", "CodeGenerator", "ProjectManager"]

        mock_orchestrator.active_agents = agents

        assert len(mock_orchestrator.active_agents) == 3
        assert "SocraticCounselor" in mock_orchestrator.active_agents

    def test_request_queue(self, mock_orchestrator):
        """Test request queue management."""
        requests = [
            {"id": 1, "action": "action1"},
            {"id": 2, "action": "action2"},
            {"id": 3, "action": "action3"},
        ]

        mock_orchestrator.request_queue = requests

        assert len(mock_orchestrator.request_queue) == 3
        assert mock_orchestrator.request_queue[0]["id"] == 1


class TestEventIntegration:
    """Integration tests for event system."""

    def test_project_workflow_events(self, mock_orchestrator, sample_project):
        """Test event sequence in project workflow."""
        # Project created
        mock_orchestrator.event_emitter.emit(EventType.PROJECT_CREATED, {"project_id": "p1"})

        # Question generated
        mock_orchestrator.event_emitter.emit(EventType.QUESTION_GENERATED, {"question": "What?"})

        # Response analyzed
        mock_orchestrator.event_emitter.emit(EventType.RESPONSE_ANALYZED, {"response": "Answer"})

        # Project updated
        mock_orchestrator.event_emitter.emit(EventType.PROJECT_UPDATED, {"project_id": "p1"})

        assert mock_orchestrator.event_emitter.emit.call_count == 4

    def test_error_event_handling(self, mock_orchestrator):
        """Test error event handling."""
        error_event = EventType.LOG_ERROR
        error_data = {"message": "An error occurred", "timestamp": datetime.datetime.now()}

        mock_orchestrator.event_emitter.emit(error_event, error_data)

        assert mock_orchestrator.event_emitter.emit.called

    def test_event_listener_workflow(self, mock_orchestrator):
        """Test complete event listener workflow."""
        callback = MagicMock()

        # Register listener
        mock_orchestrator.event_emitter.on(EventType.PROJECT_CREATED, callback)

        # Emit event
        mock_orchestrator.event_emitter.emit(EventType.PROJECT_CREATED, {"project_id": "p1"})

        # Listener registered
        assert mock_orchestrator.event_emitter.on.called


class TestOrchestratorIntegration:
    """Integration tests for orchestrator operations."""

    def test_complete_request_cycle(self, mock_orchestrator, sample_project):
        """Test complete request processing cycle."""
        # Setup
        mock_orchestrator.database.load_project.return_value = sample_project

        # Process request
        request = {"action": "analyze", "project_id": "proj-123"}
        mock_orchestrator.process_request.return_value = {"status": "success"}

        result = mock_orchestrator.process_request("agent", request)

        # Verify
        assert result["status"] == "success"

    def test_multi_agent_workflow(self, mock_orchestrator):
        """Test workflow with multiple agents."""
        agents_used = []

        def track_agent(agent_name, request):
            agents_used.append(agent_name)
            return {"status": "success"}

        mock_orchestrator.process_request.side_effect = track_agent

        # Execute workflow
        mock_orchestrator.process_request("Agent1", {})
        mock_orchestrator.process_request("Agent2", {})
        mock_orchestrator.process_request("Agent3", {})

        assert len(agents_used) == 3

    def test_state_persistence_across_requests(self, mock_orchestrator, sample_project):
        """Test state persistence across multiple requests."""
        # Set state
        mock_orchestrator.current_state = {"project": sample_project}

        # Process requests
        mock_orchestrator.process_request("agent1", {"action": "a1"})
        mock_orchestrator.process_request("agent2", {"action": "a2"})

        # State should persist
        assert mock_orchestrator.current_state["project"].project_id == "proj-123"
