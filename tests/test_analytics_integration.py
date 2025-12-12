"""
Integration tests for analytics flow - End-to-end testing of maturity and analytics systems.

Tests the interaction between:
- InsightCategorizer (categorization)
- MaturityCalculator (maturity computation)
- QualityControllerAgent (orchestration)
- AnalyticsCalculator (analytics computation)
- Analytics CLI commands (user interface)

Validates the complete workflow: Response → Categorization → Maturity Update → Analytics Update
"""

from dataclasses import asdict
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from socratic_system.agents.quality_controller import QualityControllerAgent
from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.events import EventType
from socratic_system.models import CategoryScore
from socratic_system.ui.commands.analytics_commands import (
    AnalyticsAnalyzeCommand,
    AnalyticsRecommendCommand,
    AnalyticsSummaryCommand,
    AnalyticsTrendsCommand,
)


@pytest.mark.integration
class TestAnalyticsEndToEndFlow:
    """Test complete analytics flow from response to metrics update"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with event emitter"""
        orchestrator = MagicMock()
        orchestrator.events = []

        def emit_event(event_type, data):
            orchestrator.events.append({"type": event_type, "data": data})

        orchestrator.emit_event = emit_event
        orchestrator.claude_client = None
        return orchestrator

    @pytest.fixture
    def quality_controller(self, mock_orchestrator):
        """Create a quality controller agent"""
        agent = QualityControllerAgent(mock_orchestrator)
        agent.emit_event = mock_orchestrator.emit_event
        return agent

    def test_response_processing_updates_maturity_and_analytics(
        self, quality_controller, mock_orchestrator, sample_project
    ):
        """Test that processing a response updates maturity and analytics metrics"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Simulate Q&A response with insights
        insights = {
            "goals": ["Build a web application", "Enable user collaboration"],
            "scope": ["User authentication", "Real-time notifications"],
            "problem_definition": ["Users need a better way to collaborate"],
        }

        # Process response through quality controller
        result = quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights}
        )

        # Verify maturity was updated
        assert result["status"] == "success"
        assert sample_project.phase_maturity_scores["discovery"] > 0

        # Verify analytics metrics were updated
        assert sample_project.analytics_metrics["total_qa_sessions"] > 0
        assert "velocity" in sample_project.analytics_metrics
        assert "weak_categories" in sample_project.analytics_metrics
        assert "strong_categories" in sample_project.analytics_metrics
        assert sample_project.analytics_metrics["last_updated"] is not None

    def test_multiple_qa_sessions_update_velocity(
        self, quality_controller, mock_orchestrator, sample_project
    ):
        """Test that velocity is calculated correctly with multiple Q&A sessions"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # First Q&A session
        insights_1 = {"goals": ["Goal 1", "Goal 2"], "scope": ["Scope 1"]}
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights_1}
        )

        velocity_after_1 = sample_project.analytics_metrics.get("velocity", 0.0)
        sessions_after_1 = sample_project.analytics_metrics.get("total_qa_sessions", 0)

        # Second Q&A session
        insights_2 = {
            "problem_definition": ["Define problem"],
            "scope": ["More scope"],
        }
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights_2}
        )

        velocity_after_2 = sample_project.analytics_metrics.get("velocity", 0.0)
        sessions_after_2 = sample_project.analytics_metrics.get("total_qa_sessions", 0)

        # Verify sessions increased
        assert sessions_after_2 == sessions_after_1 + 1

        # Verify velocity is calculated
        assert velocity_after_2 >= 0.0

    def test_events_emitted_during_maturity_calculation(
        self, quality_controller, mock_orchestrator, sample_project
    ):
        """Test that appropriate events are emitted during maturity updates"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"
        insights = {
            "goals": ["Goal 1"],
            "scope": ["Scope 1"],
            "problem_definition": ["Problem 1"],
        }

        # Clear previous events
        mock_orchestrator.events = []

        # Process response
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights}
        )

        # Verify events were emitted
        event_types = [e["type"] for e in mock_orchestrator.events]
        assert EventType.PHASE_MATURITY_UPDATED in event_types

    def test_weak_categories_identified_in_real_time_metrics(
        self, quality_controller, sample_project
    ):
        """Test that weak categories are identified and stored in real-time metrics"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Add only minimal specs to create weak categories
        sample_project.categorized_specs["discovery"] = [
            {
                "category": "goals",
                "content": "Build a web app",
                "confidence": 0.9,
                "value": 1.0,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        # Manually trigger maturity calculation and analytics update
        quality_controller._calculate_phase_maturity(
            {"project": sample_project, "phase": "discovery"}
        )
        quality_controller._update_analytics_metrics(sample_project)

        # Verify weak categories identified
        weak = sample_project.analytics_metrics.get("weak_categories", [])
        assert isinstance(weak, list)
        # Should have weak categories due to minimal specs

    def test_analytics_metrics_persist_across_phases(self, quality_controller, sample_project):
        """Test that analytics metrics are tracked across phase transitions"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Add specs to discovery
        insights = {"goals": ["Goal 1", "Goal 2"], "scope": ["Scope 1"]}
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights}
        )

        discovery_sessions = sample_project.analytics_metrics["total_qa_sessions"]
        discovery_velocity = sample_project.analytics_metrics["velocity"]

        # Move to next phase
        sample_project.phase = "analysis"

        # Add specs to analysis
        insights_2 = {"requirements": ["Req 1"], "constraints": ["Constraint 1"]}
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights_2}
        )

        # Verify metrics updated for new phase
        analysis_sessions = sample_project.analytics_metrics["total_qa_sessions"]
        assert analysis_sessions > discovery_sessions


@pytest.mark.integration
class TestQualityControllerIntegration:
    """Test QualityControllerAgent integration with other components"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = MagicMock()
        orchestrator.events = []
        orchestrator.emit_event = lambda et, d: orchestrator.events.append({"type": et, "data": d})
        orchestrator.claude_client = None
        return orchestrator

    @pytest.fixture
    def quality_controller(self, mock_orchestrator):
        """Create quality controller"""
        agent = QualityControllerAgent(mock_orchestrator)
        agent.emit_event = mock_orchestrator.emit_event
        return agent

    def test_calculate_phase_maturity_returns_valid_structure(
        self, quality_controller, sample_project
    ):
        """Test that maturity calculation returns proper structure"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"
        sample_project.categorized_specs["discovery"] = [
            {
                "category": "goals",
                "content": "Goal 1",
                "confidence": 0.9,
                "value": 1.0,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        result = quality_controller._calculate_phase_maturity(
            {"project": sample_project, "phase": "discovery"}
        )

        assert result["status"] == "success"
        assert "maturity" in result
        maturity = result["maturity"]
        assert "overall_score" in maturity
        assert "category_scores" in maturity
        assert "is_ready_to_advance" in maturity

    def test_verify_advancement_returns_readiness_assessment(
        self, quality_controller, sample_project
    ):
        """Test that advancement verification provides readiness assessment"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Add sufficient specs
        for i in range(10):
            sample_project.categorized_specs.setdefault("discovery", []).append(
                {
                    "category": "goals",
                    "content": f"Goal {i}",
                    "confidence": 0.9,
                    "value": 1.0,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        result = quality_controller._verify_advancement(
            {"project": sample_project, "from_phase": "discovery"}
        )

        assert result["status"] == "success"
        assert "verification" in result
        verification = result["verification"]
        assert "maturity_score" in verification
        assert "warnings" in verification
        assert "ready" in verification
        assert "complete" in verification

    def test_maturity_history_recorded_on_response(self, quality_controller, sample_project):
        """Test that maturity events are recorded in history"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"
        initial_history_length = len(sample_project.maturity_history)

        insights = {"goals": ["Goal 1"]}
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights}
        )

        # Verify history grew
        assert len(sample_project.maturity_history) > initial_history_length

        # Verify last event has proper structure
        last_event = sample_project.maturity_history[-1]
        assert "timestamp" in last_event
        assert "phase" in last_event
        assert "score_before" in last_event
        assert "score_after" in last_event
        assert "delta" in last_event
        assert "event_type" in last_event


@pytest.mark.integration
class TestAnalyticsCommandsIntegration:
    """Test analytics CLI commands with real project data"""

    @pytest.fixture
    def mock_orchestrator(self, sample_project):
        """Create mock orchestrator with project"""
        orchestrator = MagicMock()
        orchestrator.get_current_project = MagicMock(return_value=sample_project)
        orchestrator.events = []
        orchestrator.emit_event = lambda et, d: orchestrator.events.append({"type": et, "data": d})
        orchestrator.claude_client = None
        return orchestrator

    @pytest.fixture
    def project_with_data(self, sample_project):
        """Create project with real analytics data"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Add category scores
        sample_project.category_scores["discovery"] = {
            "goals": asdict(
                CategoryScore(
                    category="goals",
                    current_score=14.0,
                    target_score=15.0,
                    confidence=0.95,
                    spec_count=5,
                )
            ),
            "scope": asdict(
                CategoryScore(
                    category="scope",
                    current_score=8.0,
                    target_score=12.0,
                    confidence=0.80,
                    spec_count=3,
                )
            ),
            "problem_definition": asdict(
                CategoryScore(
                    category="problem_definition",
                    current_score=2.0,
                    target_score=10.0,
                    confidence=0.60,
                    spec_count=1,
                )
            ),
        }

        # Add maturity history
        sample_project.maturity_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 0.0,
                "score_after": 10.0,
                "delta": 10.0,
                "event_type": "response_processed",
                "details": {"specs_added": 3},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 10.0,
                "score_after": 18.0,
                "delta": 8.0,
                "event_type": "response_processed",
                "details": {"specs_added": 2},
            },
        ]

        # Update analytics metrics
        sample_project.analytics_metrics = {
            "velocity": 9.0,
            "total_qa_sessions": 2,
            "avg_confidence": 0.78,
            "weak_categories": ["problem_definition"],
            "strong_categories": ["goals"],
            "last_updated": datetime.now().isoformat(),
        }

        return sample_project

    def test_analytics_analyze_command_executes(self, mock_orchestrator, project_with_data):
        """Test that analyze command executes without error"""
        mock_orchestrator.get_current_project = MagicMock(return_value=project_with_data)

        command = AnalyticsAnalyzeCommand(mock_orchestrator)
        result = command.execute([])

        assert result["status"] == "success"
        assert "analysis" in result
        analysis = result["analysis"]
        assert "phase" in analysis
        assert "weak_categories" in analysis
        assert "strong_categories" in analysis

    def test_analytics_recommend_command_executes(self, mock_orchestrator, project_with_data):
        """Test that recommend command executes without error"""
        mock_orchestrator.get_current_project = MagicMock(return_value=project_with_data)

        command = AnalyticsRecommendCommand(mock_orchestrator)
        result = command.execute([])

        assert result["status"] == "success"
        assert "recommendations" in result
        assert "suggestions" in result
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["suggestions"], list)

    def test_analytics_trends_command_executes(self, mock_orchestrator, project_with_data):
        """Test that trends command executes without error"""
        mock_orchestrator.get_current_project = MagicMock(return_value=project_with_data)

        command = AnalyticsTrendsCommand(mock_orchestrator)
        result = command.execute([])

        assert result["status"] == "success"
        assert "trends" in result
        trends = result["trends"]
        assert "velocity" in trends
        assert "total_sessions" in trends
        assert "current_phase" in trends

    def test_analytics_summary_command_executes(self, mock_orchestrator, project_with_data):
        """Test that summary command executes without error"""
        mock_orchestrator.get_current_project = MagicMock(return_value=project_with_data)

        command = AnalyticsSummaryCommand(mock_orchestrator)
        result = command.execute([])

        assert result["status"] == "success"
        assert "metrics" in result


@pytest.mark.integration
class TestAnalyticsComputationFlow:
    """Test analytics computation using real data flow"""

    def test_analytics_calculator_with_real_maturity_history(self, sample_project):
        """Test analytics calculator with real maturity history"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Add realistic maturity history
        sample_project.maturity_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 0.0,
                "score_after": 5.0,
                "delta": 5.0,
                "event_type": "response_processed",
                "details": {"specs_added": 2},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 5.0,
                "score_after": 12.0,
                "delta": 7.0,
                "event_type": "response_processed",
                "details": {"specs_added": 3},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 12.0,
                "score_after": 18.0,
                "delta": 6.0,
                "event_type": "response_processed",
                "details": {"specs_added": 2},
            },
        ]

        # Add category scores
        sample_project.category_scores["discovery"] = {
            "goals": asdict(
                CategoryScore(
                    category="goals",
                    current_score=15.0,
                    target_score=15.0,
                    confidence=0.95,
                    spec_count=5,
                )
            ),
            "scope": asdict(
                CategoryScore(
                    category="scope",
                    current_score=3.0,
                    target_score=12.0,
                    confidence=0.60,
                    spec_count=1,
                )
            ),
        }

        # Calculate analytics
        calculator = AnalyticsCalculator("software")
        trends = calculator.analyze_progression_trends(sample_project)

        # Verify velocity calculated correctly
        assert trends["velocity"] == pytest.approx(6.0, rel=0.01)
        assert trends["total_sessions"] == 3

        # Get recommendations
        recommendations = calculator.generate_recommendations(sample_project)
        assert isinstance(recommendations, list)
        # Should recommend working on scope (weak category)
        categories = [r["category"] for r in recommendations]
        assert "scope" in categories

    def test_insights_categorization_through_quality_controller(self, sample_project):
        """Test that insights are properly categorized through quality controller"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Create mock orchestrator with no Claude client (will use fallback)
        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client = None
        mock_orchestrator.emit_event = MagicMock()

        quality_controller = QualityControllerAgent(mock_orchestrator)

        insights = {
            "goals": ["Build a web app", "Enable real-time collaboration"],
            "scope": ["User management", "Chat feature"],
            "problem_definition": ["Users need better communication tools"],
        }

        # Process through quality controller
        result = quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights}
        )

        # Verify specs were categorized
        assert result["status"] == "success"
        specs = sample_project.categorized_specs.get("discovery", [])
        assert len(specs) > 0

        # Verify specs have proper structure
        for spec in specs:
            assert "category" in spec
            assert "content" in spec
            assert "confidence" in spec
            assert "value" in spec

    def test_weak_category_identification_with_progression(self, sample_project):
        """Test identification of weak categories that improve over time"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        calculator = AnalyticsCalculator("software")

        # Initial state: weak categories
        sample_project.category_scores["discovery"] = {
            "goals": asdict(
                CategoryScore(
                    category="goals",
                    current_score=2.0,
                    target_score=15.0,
                    confidence=0.5,
                    spec_count=1,
                )
            ),
            "scope": asdict(
                CategoryScore(
                    category="scope",
                    current_score=1.0,
                    target_score=12.0,
                    confidence=0.4,
                    spec_count=1,
                )
            ),
        }

        weak_1 = calculator.identify_weak_categories(sample_project)
        assert len(weak_1) == 2

        # Improve goals
        sample_project.category_scores["discovery"]["goals"] = asdict(
            CategoryScore(
                category="goals",
                current_score=12.0,
                target_score=15.0,
                confidence=0.9,
                spec_count=4,
            )
        )

        weak_2 = calculator.identify_weak_categories(sample_project)
        assert len(weak_2) == 1
        assert "scope" in weak_2

    def test_recommendation_priority_based_on_gap(self, sample_project):
        """Test that recommendations are prioritized by gap size"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        sample_project.category_scores["discovery"] = {
            "goals": asdict(
                CategoryScore(
                    category="goals",
                    current_score=1.0,
                    target_score=15.0,
                    confidence=0.5,
                    spec_count=1,
                )
            ),  # 6.7% - 70% gap
            "scope": asdict(
                CategoryScore(
                    category="scope",
                    current_score=2.0,
                    target_score=12.0,
                    confidence=0.5,
                    spec_count=1,
                )
            ),  # 16.7% - 53.3% gap
        }

        calculator = AnalyticsCalculator("software")
        recommendations = calculator.generate_recommendations(sample_project)

        # Recommendations should be sorted by gap
        if len(recommendations) > 1:
            first_gap = recommendations[0]["gap"]
            second_gap = recommendations[1]["gap"]
            assert first_gap >= second_gap


@pytest.mark.integration
class TestAnalyticsDataConsistency:
    """Test consistency of analytics data across components"""

    def test_phase_maturity_scores_consistency(self, sample_project):
        """Test that phase maturity scores are consistent across operations"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client = None
        mock_orchestrator.emit_event = MagicMock()

        quality_controller = QualityControllerAgent(mock_orchestrator)

        # Add specs
        insights = {"goals": ["Goal 1", "Goal 2"], "scope": ["Scope 1"]}
        quality_controller._update_maturity_after_response(
            {"project": sample_project, "insights": insights}
        )

        discovery_score = sample_project.phase_maturity_scores.get("discovery", 0.0)

        # Recalculate maturity
        result = quality_controller._calculate_phase_maturity(
            {"project": sample_project, "phase": "discovery"}
        )

        recalculated_score = sample_project.phase_maturity_scores.get("discovery", 0.0)

        # Should be same (same specs, same calculation)
        assert discovery_score == pytest.approx(recalculated_score, rel=0.01)

    def test_category_scores_reflect_specs(self, sample_project):
        """Test that category scores accurately reflect specs"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        sample_project.categorized_specs["discovery"] = [
            {
                "category": "goals",
                "content": "Goal 1",
                "confidence": 1.0,
                "value": 1.0,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "category": "goals",
                "content": "Goal 2",
                "confidence": 1.0,
                "value": 1.0,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "category": "scope",
                "content": "Scope 1",
                "confidence": 0.8,
                "value": 1.0,
                "timestamp": datetime.now().isoformat(),
            },
        ]

        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client = None
        mock_orchestrator.emit_event = MagicMock()

        quality_controller = QualityControllerAgent(mock_orchestrator)
        quality_controller._calculate_phase_maturity(
            {"project": sample_project, "phase": "discovery"}
        )

        # Check that category scores reflect specs
        goals_score = sample_project.category_scores["discovery"]["goals"]
        assert goals_score["spec_count"] == 2
        assert goals_score["confidence"] == pytest.approx(1.0, rel=0.01)

        scope_score = sample_project.category_scores["discovery"]["scope"]
        assert scope_score["spec_count"] == 1

    def test_velocity_matches_maturity_deltas(self, sample_project):
        """Test that calculated velocity matches maturity history deltas"""
        sample_project.project_type = "software"
        sample_project.phase = "discovery"

        # Create specific maturity history
        sample_project.maturity_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 0.0,
                "score_after": 5.0,
                "delta": 5.0,
                "event_type": "response_processed",
                "details": {},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 5.0,
                "score_after": 8.0,
                "delta": 3.0,
                "event_type": "response_processed",
                "details": {},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 8.0,
                "score_after": 14.0,
                "delta": 6.0,
                "event_type": "response_processed",
                "details": {},
            },
        ]

        calculator = AnalyticsCalculator("software")
        velocity = calculator.calculate_velocity(sample_project)

        # Expected velocity: (5 + 3 + 6) / 3 = 4.67
        expected = (5.0 + 3.0 + 6.0) / 3
        assert velocity == pytest.approx(expected, rel=0.01)
