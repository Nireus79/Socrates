"""
Tests for Knowledge Analysis Agent and knowledge-aware question regeneration

Tests verify:
1. Knowledge Analysis Agent is properly initialized and listens for events
2. Document import triggers knowledge analysis
3. Knowledge analysis generates proper focus areas
4. Questions are regenerated based on new knowledge
5. Tester role is available in the system
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from socratic_system.agents.knowledge_analysis import KnowledgeAnalysisAgent
from socratic_system.events import EventType, EventEmitter
from socratic_system.models.role import VALID_ROLES, ROLE_FOCUS_AREAS, ROLE_EXAMPLES


class TestKnowledgeAnalysisAgent:
    """Test suite for Knowledge Analysis Agent"""

    def test_agent_initialization(self):
        """Test that Knowledge Analysis Agent initializes properly"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()
        mock_orchestrator.counselor = Mock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        assert agent.name == "KnowledgeAnalysis"
        assert agent.orchestrator == mock_orchestrator
        assert agent.logger is not None

    def test_document_imported_event_listener(self):
        """Test that agent listens for DOCUMENT_IMPORTED events"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()
        mock_orchestrator.counselor = Mock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        # Verify listener was registered
        listener_count = mock_orchestrator.event_emitter.listener_count(EventType.DOCUMENT_IMPORTED)
        assert listener_count == 1, f"Expected 1 listener, got {listener_count}"

    def test_process_analyze_knowledge_action(self):
        """Test the analyze_knowledge action"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()
        mock_orchestrator.counselor = Mock()

        # Mock project
        mock_project = Mock()
        mock_project.name = "TestProject"
        mock_project.phase = "discovery"
        mock_project.goals = ["Build a calculator", "Create documentation"]

        mock_orchestrator.database.load_project.return_value = mock_project
        mock_orchestrator.vector_db.search_similar.return_value = [
            {
                "content": "Calculator implementation in Python",
                "metadata": {"source": "calc.pdf", "chunk": 1},
                "score": 0.85,
            }
        ]

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        result = agent.process({
            "action": "analyze_knowledge",
            "project_id": "test_proj_001",
            "document_name": "calc.pdf",
            "source_type": "pdf",
            "words_extracted": 182,
        })

        assert result["status"] == "success"
        assert "analysis" in result
        assert result["analysis"]["document"] == "calc.pdf"
        assert result["analysis"]["project_phase"] == "discovery"
        assert "suggested_focus_areas" in result["analysis"]

    def test_process_regenerate_questions_action(self):
        """Test the regenerate_questions action"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()
        mock_orchestrator.counselor = Mock()

        mock_project = Mock()
        mock_project.name = "TestProject"
        mock_project.phase = "analysis"

        mock_orchestrator.database.load_project.return_value = mock_project
        mock_orchestrator.counselor.process.return_value = {"insights": ["insight1"]}

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        analysis = {
            "document": "calc.pdf",
            "gaps_filled": ["testing"],
            "suggested_focus_areas": [
                "How will you test the calculator?",
                "What edge cases exist?",
            ],
        }

        result = agent.process({
            "action": "regenerate_questions",
            "project_id": "test_proj_001",
            "knowledge_analysis": analysis,
        })

        assert result["status"] == "success"
        assert "new_focus_areas" in result
        assert len(result["new_focus_areas"]) > 0

    def test_document_imported_triggers_analysis_and_regen(self):
        """Test that DOCUMENT_IMPORTED event triggers analysis and question regeneration"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()
        mock_orchestrator.counselor = Mock()

        mock_project = Mock()
        mock_project.name = "TestProject"
        mock_project.phase = "discovery"
        mock_project.goals = ["Build calculator"]

        mock_orchestrator.database.load_project.return_value = mock_project
        mock_orchestrator.vector_db.search_similar.return_value = [
            {"content": "Calculator content", "metadata": {"source": "calc.pdf"}, "score": 0.8}
        ]
        mock_orchestrator.counselor.process.return_value = {"insights": []}

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        # Emit DOCUMENT_IMPORTED event
        mock_orchestrator.event_emitter.emit(
            EventType.DOCUMENT_IMPORTED,
            {
                "project_id": "test_proj_001",
                "file_name": "calc.pdf",
                "source_type": "pdf",
                "words_extracted": 182,
            },
        )

        # Give event handlers time to execute (they're synchronous in tests)
        # Verify that database was called to load project
        assert mock_orchestrator.database.load_project.called

    def test_get_knowledge_gaps_action(self):
        """Test the get_knowledge_gaps action"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()

        mock_project = Mock()
        mock_project.name = "TestProject"
        mock_project.phase = "implementation"
        mock_project.goals = []

        mock_orchestrator.database.load_project.return_value = mock_project

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        result = agent.process({
            "action": "get_knowledge_gaps",
            "project_id": "test_proj_001",
        })

        assert result["status"] == "success"
        assert "knowledge_gaps" in result
        assert "count" in result
        assert result["project_id"] == "test_proj_001"

    def test_unknown_action_returns_error(self):
        """Test that unknown actions return error status"""
        mock_orchestrator = Mock()
        mock_orchestrator.event_emitter = EventEmitter()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestTesterRole:
    """Test suite for Tester role in the system"""

    def test_tester_role_is_valid(self):
        """Test that 'tester' is a valid role"""
        assert "tester" in VALID_ROLES, "Tester role not in VALID_ROLES"

    def test_tester_role_has_focus_areas(self):
        """Test that tester role has defined focus areas"""
        assert "tester" in ROLE_FOCUS_AREAS, "Tester role not in ROLE_FOCUS_AREAS"

        focus = ROLE_FOCUS_AREAS["tester"]
        assert "quality" in focus.lower(), "Quality not mentioned in tester focus"
        assert "testing" in focus.lower(), "Testing not mentioned in tester focus"
        assert "bug" in focus.lower(), "Bug identification not mentioned in tester focus"

    def test_tester_role_examples_for_all_project_types(self):
        """Test that tester role has examples for all project types"""
        project_types = ["software", "business", "creative", "research", "marketing", "educational"]

        for project_type in project_types:
            assert project_type in ROLE_EXAMPLES, f"Project type {project_type} not in ROLE_EXAMPLES"
            assert "tester" in ROLE_EXAMPLES[project_type], f"Tester role missing for {project_type}"

    def test_tester_role_examples_are_contextual(self):
        """Test that tester role examples are appropriate for their project context"""
        # Software testers should be called QA Engineer
        assert "QA" in ROLE_EXAMPLES["software"]["tester"]

        # Business testers might be Auditors
        assert "Auditor" in ROLE_EXAMPLES["business"]["tester"]

        # Research testers should validate research
        assert "Validator" in ROLE_EXAMPLES["research"]["tester"]


class TestKnowledgeAwareQuestionGeneration:
    """Test suite for knowledge-aware question generation"""

    def test_questions_regenerated_event_exists(self):
        """Test that QUESTIONS_REGENERATED event type exists"""
        assert hasattr(EventType, "QUESTIONS_REGENERATED")

    def test_knowledge_analysis_event_flow(self):
        """Test the complete event flow for knowledge analysis"""
        mock_orchestrator = Mock()
        event_emitter = EventEmitter()
        mock_orchestrator.event_emitter = event_emitter
        mock_orchestrator.database = Mock()
        mock_orchestrator.vector_db = Mock()
        mock_orchestrator.counselor = Mock()

        # Track events emitted
        emitted_events = []

        def track_event(event_type, data):
            emitted_events.append((event_type, data))

        event_emitter.on(EventType.QUESTIONS_REGENERATED, lambda data: track_event(EventType.QUESTIONS_REGENERATED, data))

        mock_project = Mock()
        mock_project.name = "TestProject"
        mock_project.phase = "discovery"
        mock_project.goals = []

        mock_orchestrator.database.load_project.return_value = mock_project
        mock_orchestrator.vector_db.search_similar.return_value = []
        mock_orchestrator.counselor.process.return_value = {"insights": []}

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        # Trigger document import
        event_emitter.emit(
            EventType.DOCUMENT_IMPORTED,
            {
                "project_id": "test_proj_001",
                "file_name": "calc.pdf",
                "source_type": "pdf",
                "words_extracted": 182,
            },
        )

        # Verify QUESTIONS_REGENERATED event was emitted
        regenerated_events = [e for e in emitted_events if e[0] == EventType.QUESTIONS_REGENERATED]
        assert len(regenerated_events) > 0, "QUESTIONS_REGENERATED event was not emitted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
