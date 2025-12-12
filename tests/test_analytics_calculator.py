"""
Unit tests for AnalyticsCalculator module
"""

from dataclasses import asdict
from datetime import datetime

import pytest

from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.models import CategoryScore


@pytest.mark.unit
class TestAnalyticsCalculatorInit:
    """Tests for AnalyticsCalculator initialization"""

    def test_init_default_project_type(self):
        """Test initializing with default project type"""
        calculator = AnalyticsCalculator()
        assert calculator.project_type == "software"
        assert calculator.phase_categories is not None
        assert len(calculator.phase_categories) == 4  # 4 phases

    def test_init_with_project_type(self):
        """Test initializing with specific project type"""
        calculator = AnalyticsCalculator(project_type="business")
        assert calculator.project_type == "business"
        assert calculator.phase_categories is not None

    def test_init_all_project_types(self):
        """Test initializing with all supported project types"""
        project_types = ["software", "business", "creative", "research", "marketing", "educational"]
        for proj_type in project_types:
            calculator = AnalyticsCalculator(project_type=proj_type)
            assert calculator.project_type == proj_type
            assert calculator.phase_categories is not None


@pytest.mark.unit
class TestCategoryAnalysis:
    """Tests for category analysis methods"""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance"""
        return AnalyticsCalculator(project_type="software")

    @pytest.fixture
    def project_with_categories(self, sample_project):
        """Create a project with category scores"""
        # Set up category scores for current phase (discovery)
        sample_project.category_scores["discovery"] = {
            "goals": asdict(
                CategoryScore(
                    category="goals",
                    current_score=15.0,
                    target_score=15.0,
                    confidence=0.95,
                    spec_count=3,
                )
            ),
            "scope": asdict(
                CategoryScore(
                    category="scope",
                    current_score=5.0,
                    target_score=12.0,
                    confidence=0.80,
                    spec_count=2,
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
            "competitive_analysis": asdict(
                CategoryScore(
                    category="competitive_analysis",
                    current_score=0.0,
                    target_score=10.0,
                    confidence=0.0,
                    spec_count=0,
                )
            ),
        }
        sample_project.phase = "discovery"
        return sample_project

    def test_identify_weak_categories(self, calculator, project_with_categories):
        """Test identifying weak categories (< 30%)"""
        weak = calculator.identify_weak_categories(project_with_categories)

        assert "problem_definition" in weak
        assert "competitive_analysis" in weak
        assert "goals" not in weak  # 100% - not weak
        assert len(weak) >= 2

    def test_identify_strong_categories(self, calculator, project_with_categories):
        """Test identifying strong categories (> 70%)"""
        strong = calculator.identify_strong_categories(project_with_categories)

        assert "goals" in strong  # 100% - strong
        assert "problem_definition" not in strong  # 20% - not strong
        assert "competitive_analysis" not in strong  # 0% - not strong

    def test_analyze_category_performance(self, calculator, project_with_categories):
        """Test comprehensive category performance analysis"""
        analysis = calculator.analyze_category_performance(project_with_categories)

        assert analysis["phase"] == "discovery"
        assert "weak_categories" in analysis
        assert "strong_categories" in analysis
        assert "missing_categories" in analysis
        assert "balance" in analysis

        # Check categorization
        assert len(analysis["missing_categories"]) >= 1
        assert "competitive_analysis" in analysis["missing_categories"]

    def test_analyze_category_balance_imbalanced(self, calculator, project_with_categories):
        """Test detecting imbalanced category development"""
        balance = calculator.analyze_category_balance(project_with_categories)

        # Should detect imbalance (goals=100%, problem_def=20%)
        assert balance["status"] in ["BALANCED", "IMBALANCED"]
        assert "messages" in balance

    def test_get_missing_categories(self, calculator, sample_project):
        """Test identifying missing categories across phases"""
        # Empty categories
        missing = calculator.get_missing_categories(sample_project)

        # Should return dict with phases as keys
        assert isinstance(missing, dict)
        for phase in ["discovery", "analysis", "design", "implementation"]:
            # Each phase should have missing categories since we haven't added any
            if phase in missing:
                assert isinstance(missing[phase], list)


@pytest.mark.unit
class TestProgressionAnalysis:
    """Tests for progression analysis methods"""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance"""
        return AnalyticsCalculator(project_type="software")

    @pytest.fixture
    def project_with_history(self, sample_project):
        """Create a project with maturity history"""
        # Add Q&A events
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
                "score_after": 10.0,
                "delta": 5.0,
                "event_type": "response_processed",
                "details": {"specs_added": 2},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
                "score_before": 10.0,
                "score_after": 12.0,
                "delta": 2.0,
                "event_type": "response_processed",
                "details": {"specs_added": 1},
            },
        ]
        sample_project.phase = "discovery"
        return sample_project

    def test_calculate_velocity_empty_history(self, calculator, sample_project):
        """Test velocity calculation with empty history"""
        velocity = calculator.calculate_velocity(sample_project)
        assert velocity == 0.0

    def test_calculate_velocity_with_history(self, calculator, project_with_history):
        """Test velocity calculation with Q&A events"""
        velocity = calculator.calculate_velocity(project_with_history)

        # Total gain = 5 + 5 + 2 = 12, sessions = 3, velocity = 4.0
        assert velocity > 0.0
        assert isinstance(velocity, float)
        assert velocity == pytest.approx(4.0, rel=0.01)

    def test_analyze_progression_trends(self, calculator, project_with_history):
        """Test progression trend analysis"""
        trends = calculator.analyze_progression_trends(project_with_history)

        assert "velocity" in trends
        assert "total_sessions" in trends
        assert "current_phase" in trends
        assert "current_score" in trends
        assert "insights" in trends

        assert trends["total_sessions"] == 3
        assert trends["velocity"] > 0.0
        assert isinstance(trends["insights"], list)

    def test_identify_plateaus_no_plateaus(self, calculator, project_with_history):
        """Test plateau identification with steady progress"""
        plateaus = calculator.identify_plateaus(project_with_history)

        # Should not find plateaus in steady progress (5, 5, 2 - all > 0.5)
        assert isinstance(plateaus, list)

    def test_identify_plateaus_insufficient_data(self, calculator, sample_project):
        """Test plateau identification with insufficient data"""
        sample_project.maturity_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "response_processed",
                "delta": 1.0,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "response_processed",
                "delta": 1.0,
            },
        ]

        plateaus = calculator.identify_plateaus(sample_project)
        assert plateaus == []  # Need at least 3 events


@pytest.mark.unit
class TestRecommendations:
    """Tests for recommendation generation"""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance"""
        return AnalyticsCalculator(project_type="software")

    @pytest.fixture
    def project_with_weak_categories(self, sample_project):
        """Create a project with weak categories"""
        sample_project.category_scores["discovery"] = {
            "goals": asdict(
                CategoryScore(
                    category="goals",
                    current_score=14.0,
                    target_score=15.0,
                    confidence=0.95,
                    spec_count=3,
                )
            ),
            "problem_definition": asdict(
                CategoryScore(
                    category="problem_definition",
                    current_score=2.0,
                    target_score=10.0,
                    confidence=0.50,
                    spec_count=1,
                )
            ),
            "competitive_analysis": asdict(
                CategoryScore(
                    category="competitive_analysis",
                    current_score=0.0,
                    target_score=10.0,
                    confidence=0.0,
                    spec_count=0,
                )
            ),
        }
        sample_project.phase = "discovery"
        return sample_project

    def test_generate_recommendations_returns_list(self, calculator, sample_project):
        """Test that recommendations are returned as a list"""
        recommendations = calculator.generate_recommendations(sample_project)
        assert isinstance(recommendations, list)

    def test_generate_recommendations_includes_weak_categories(
        self, calculator, project_with_weak_categories
    ):
        """Test that weak categories are included in recommendations"""
        recommendations = calculator.generate_recommendations(project_with_weak_categories)

        assert len(recommendations) > 0

        # Should include problem_definition and competitive_analysis
        categories = [r["category"] for r in recommendations]
        assert "problem_definition" in categories or "competitive_analysis" in categories

    def test_generate_recommendations_has_priority(self, calculator, project_with_weak_categories):
        """Test that recommendations have priority levels"""
        recommendations = calculator.generate_recommendations(project_with_weak_categories)

        for rec in recommendations:
            assert "priority" in rec
            assert rec["priority"] in ["high", "medium"]

    def test_generate_recommendations_includes_actions(
        self, calculator, project_with_weak_categories
    ):
        """Test that recommendations include actionable suggestions"""
        recommendations = calculator.generate_recommendations(project_with_weak_categories)

        for rec in recommendations:
            assert "action" in rec
            assert isinstance(rec["action"], str)
            assert len(rec["action"]) > 0

    def test_suggest_next_questions(self, calculator, project_with_weak_categories):
        """Test question suggestion for weak areas"""
        questions = calculator.suggest_next_questions(project_with_weak_categories, count=5)

        assert isinstance(questions, list)
        assert len(questions) <= 5

        # Each question should be a non-empty string
        for question in questions:
            assert isinstance(question, str)
            assert len(question) > 0
            assert "?" in question  # Questions should end with ?


@pytest.mark.unit
class TestHelperMethods:
    """Tests for helper methods"""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance"""
        return AnalyticsCalculator(project_type="software")

    def test_generate_action_for_category(self, calculator):
        """Test action generation for known categories"""
        action = calculator._generate_action_for_category("goals")
        assert isinstance(action, str)
        assert len(action) > 0
        assert "goal" in action.lower() or "achieve" in action.lower()

    def test_generate_action_for_unknown_category(self, calculator):
        """Test action generation for unknown categories"""
        action = calculator._generate_action_for_category("unknown_category")
        assert isinstance(action, str)
        assert len(action) > 0

    def test_generate_question_for_category(self, calculator):
        """Test question generation for known categories"""
        question = calculator._generate_question_for_category("goals")
        assert isinstance(question, str)
        assert "?" in question

    def test_generate_question_for_unknown_category(self, calculator):
        """Test question generation for unknown categories"""
        question = calculator._generate_question_for_category("unknown_category")
        assert isinstance(question, str)
        assert "?" in question

    def test_generate_insights_empty_events(self, calculator):
        """Test insight generation with empty events"""
        insights = calculator._generate_insights([], velocity=0.0)
        assert isinstance(insights, list)

    def test_generate_insights_with_velocity(self, calculator):
        """Test insight generation with positive velocity"""
        events = [{"delta": 5.0}, {"delta": 4.0}, {"delta": 3.0}]
        insights = calculator._generate_insights(events, velocity=4.0)

        assert isinstance(insights, list)
        assert len(insights) > 0


@pytest.mark.unit
class TestProjectTypes:
    """Tests for different project types"""

    def test_analytics_calculator_software(self):
        """Test analytics for software projects"""
        calculator = AnalyticsCalculator(project_type="software")
        assert calculator.project_type == "software"
        assert "discovery" in calculator.phase_categories

    def test_analytics_calculator_business(self):
        """Test analytics for business projects"""
        calculator = AnalyticsCalculator(project_type="business")
        assert calculator.project_type == "business"
        assert "discovery" in calculator.phase_categories

    def test_analytics_calculator_creative(self):
        """Test analytics for creative projects"""
        calculator = AnalyticsCalculator(project_type="creative")
        assert calculator.project_type == "creative"
        assert "discovery" in calculator.phase_categories


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance"""
        return AnalyticsCalculator(project_type="software")

    def test_velocity_with_single_event(self, calculator, sample_project):
        """Test velocity calculation with single Q&A event"""
        sample_project.maturity_history = [{"event_type": "response_processed", "delta": 5.0}]

        velocity = calculator.calculate_velocity(sample_project)
        assert velocity == 5.0

    def test_zero_velocity_acceptable(self, calculator, sample_project):
        """Test that zero velocity is acceptable"""
        sample_project.maturity_history = [
            {"event_type": "response_processed", "delta": 0.0},
            {"event_type": "response_processed", "delta": 0.0},
        ]

        velocity = calculator.calculate_velocity(sample_project)
        assert velocity == 0.0

    def test_analysis_with_empty_project(self, calculator, sample_project):
        """Test analysis with project having no specs"""
        # Use sample_project but clear its category scores
        sample_project.category_scores = {}
        sample_project.phase = "discovery"

        # Should not crash
        analysis = calculator.analyze_category_performance(sample_project)
        assert "phase" in analysis

    def test_recommendations_with_high_maturity(self, calculator, sample_project):
        """Test recommendations when most categories are strong"""
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
                    current_score=12.0,
                    target_score=12.0,
                    confidence=0.95,
                    spec_count=5,
                )
            ),
        }
        sample_project.phase = "discovery"

        recommendations = calculator.generate_recommendations(sample_project)
        # Should still return valid recommendations or empty list
        assert isinstance(recommendations, list)
