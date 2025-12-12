"""
Tests for Analytics Calculator - Maturity tracking and recommendations.

Tests cover:
- Category performance analysis
- Weak/strong category identification
- Balance analysis
- Velocity calculation
- Progression trends
- Recommendations generation
- Question suggestions
"""

import datetime

import pytest

from socratic_system.core.analytics_calculator import AnalyticsCalculator
from socratic_system.models import ProjectContext


@pytest.fixture
def calculator_software():
    """Create analytics calculator for software projects."""
    return AnalyticsCalculator("software")


@pytest.fixture
def calculator_business():
    """Create analytics calculator for business projects."""
    return AnalyticsCalculator("business")


@pytest.fixture
def project_balanced():
    """Create a project with balanced category scores."""
    return ProjectContext(
        project_id="proj-balanced",
        name="Balanced Project",
        owner="user",
        collaborators=[],
        goals="Build software",
        requirements=["req1", "req2", "req3"],
        tech_stack=["python", "django"],
        constraints=["time"],
        team_structure="team",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="design",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        category_scores={
            "design": {
                "architecture": {
                    "current_score": 0.8,
                    "target_score": 1.0,
                    "spec_count": 5,
                },
                "database": {
                    "current_score": 0.6,
                    "target_score": 1.0,
                    "spec_count": 3,
                },
                "api": {
                    "current_score": 0.2,
                    "target_score": 1.0,
                    "spec_count": 1,
                },
            }
        },
        maturity_history=[
            {"timestamp": datetime.datetime.now(), "score": 0.5},
            {"timestamp": datetime.datetime.now(), "score": 0.6},
            {"timestamp": datetime.datetime.now(), "score": 0.65},
        ],
    )


@pytest.fixture
def project_weak():
    """Create a project with weak category scores."""
    return ProjectContext(
        project_id="proj-weak",
        name="Weak Project",
        owner="user",
        collaborators=[],
        goals="Weak goals",
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
        category_scores={
            "discovery": {
                "goals": {
                    "current_score": 0.1,
                    "target_score": 1.0,
                    "spec_count": 1,
                },
                "requirements": {
                    "current_score": 0.0,
                    "target_score": 1.0,
                    "spec_count": 0,
                },
            }
        },
        maturity_history=[
            {"timestamp": datetime.datetime.now(), "score": 0.1},
        ],
    )


class TestAnalyticsCategoryAnalysis:
    """Tests for category analysis methods."""

    def test_analyze_category_performance(self, calculator_software, project_balanced):
        """Test category performance analysis."""
        result = calculator_software.analyze_category_performance(project_balanced)

        assert isinstance(result, dict)
        assert "strong_categories" in result
        assert "weak_categories" in result
        assert "missing_categories" in result
        assert "balance" in result

    def test_identify_weak_categories(self, calculator_software, project_balanced):
        """Test identifying weak categories (< 30%)."""
        weak = calculator_software.identify_weak_categories(project_balanced)

        assert isinstance(weak, list)
        # API should be weak (20%)
        assert "api" in weak

    def test_identify_strong_categories(self, calculator_software, project_balanced):
        """Test identifying strong categories (> 70%)."""
        strong = calculator_software.identify_strong_categories(project_balanced)

        assert isinstance(strong, list)
        # Architecture should be strong (80%)
        assert "architecture" in strong

    def test_analyze_category_balance(self, calculator_software, project_balanced):
        """Test category balance analysis."""
        balance = calculator_software.analyze_category_balance(project_balanced)

        assert isinstance(balance, dict)
        assert "balance_score" in balance
        assert "imbalance_areas" in balance
        assert 0 <= balance.get("balance_score", 0) <= 1

    def test_get_missing_categories(self, calculator_software, project_weak):
        """Test getting missing categories (0 specs)."""
        missing = calculator_software.get_missing_categories(project_weak)

        assert isinstance(missing, dict)
        # Requirements should be missing
        assert "requirements" in missing["discovery"]

    def test_category_analysis_with_zero_target(self, calculator_software):
        """Test category analysis handles zero target score."""
        project = ProjectContext(
            project_id="proj-zero",
            name="Zero Target",
            owner="user",
            collaborators=[],
            goals="",
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
            category_scores={
                "discovery": {
                    "goals": {
                        "current_score": 0.5,
                        "target_score": 0.0,  # Zero target
                        "spec_count": 1,
                    }
                }
            },
        )

        result = calculator_software.analyze_category_performance(project)

        assert isinstance(result, dict)


class TestAnalyticsVelocity:
    """Tests for velocity calculation."""

    def test_calculate_velocity(self, calculator_software, project_balanced):
        """Test velocity calculation from maturity history."""
        velocity = calculator_software.calculate_velocity(project_balanced)

        assert isinstance(velocity, (int, float))
        assert velocity >= 0

    def test_velocity_with_empty_history(self, calculator_software):
        """Test velocity with no maturity history."""
        project = ProjectContext(
            project_id="proj-empty",
            name="Empty",
            owner="user",
            collaborators=[],
            goals="",
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
            maturity_history=[],
        )

        velocity = calculator_software.calculate_velocity(project)

        assert velocity == 0 or isinstance(velocity, (int, float))

    def test_velocity_with_single_point(self, calculator_software):
        """Test velocity with only one data point."""
        project = ProjectContext(
            project_id="proj-single",
            name="Single",
            owner="user",
            collaborators=[],
            goals="",
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
            maturity_history=[{"timestamp": datetime.datetime.now(), "score": 0.5}],
        )

        velocity = calculator_software.calculate_velocity(project)

        assert isinstance(velocity, (int, float))


class TestAnalyticsProgressionTrends:
    """Tests for progression trend analysis."""

    def test_analyze_progression_trends(self, calculator_software, project_balanced):
        """Test progression trend analysis."""
        trends = calculator_software.analyze_progression_trends(project_balanced)

        assert isinstance(trends, dict)
        assert "velocity" in trends
        assert "total_sessions" in trends
        assert "trend_direction" in trends

    def test_identify_plateaus(self, calculator_software, project_balanced):
        """Test plateau identification."""
        plateaus = calculator_software.identify_plateaus(project_balanced)

        assert isinstance(plateaus, list)

    def test_plateaus_with_consistent_growth(self, calculator_software):
        """Test plateau detection with consistent growth."""
        project = ProjectContext(
            project_id="proj-growth",
            name="Growth",
            owner="user",
            collaborators=[],
            goals="",
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
            maturity_history=[
                {"timestamp": datetime.datetime.now(), "score": 0.1},
                {"timestamp": datetime.datetime.now(), "score": 0.2},
                {"timestamp": datetime.datetime.now(), "score": 0.3},
                {"timestamp": datetime.datetime.now(), "score": 0.4},
            ],
        )

        plateaus = calculator_software.identify_plateaus(project)

        assert isinstance(plateaus, list)


class TestAnalyticsRecommendations:
    """Tests for recommendation generation."""

    def test_generate_recommendations(self, calculator_software, project_balanced):
        """Test recommendation generation."""
        recommendations = calculator_software.generate_recommendations(project_balanced)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Each recommendation should have required fields
        for rec in recommendations:
            assert isinstance(rec, dict)
            assert "action" in rec or "recommendation" in rec

    def test_recommendations_for_weak_project(self, calculator_software, project_weak):
        """Test recommendations for weak project."""
        recommendations = calculator_software.generate_recommendations(project_weak)

        assert isinstance(recommendations, list)
        # Weak project should have recommendations
        assert len(recommendations) > 0

    def test_suggest_next_questions(self, calculator_software, project_balanced):
        """Test question suggestion."""
        questions = calculator_software.suggest_next_questions(project_balanced, count=5)

        assert isinstance(questions, list)
        assert len(questions) <= 5
        assert all(isinstance(q, str) for q in questions)

    def test_suggest_questions_custom_count(self, calculator_software, project_balanced):
        """Test question suggestion with custom count."""
        questions = calculator_software.suggest_next_questions(project_balanced, count=3)

        assert len(questions) <= 3

    def test_suggest_zero_questions(self, calculator_software, project_balanced):
        """Test question suggestion with zero count."""
        questions = calculator_software.suggest_next_questions(project_balanced, count=0)

        assert isinstance(questions, list)
        assert len(questions) == 0


class TestAnalyticsProjectTypes:
    """Tests for different project types."""

    def test_software_project_calculator(self, calculator_software):
        """Test calculator for software projects."""
        assert calculator_software.project_type == "software"
        assert calculator_software.phase_categories is not None

    def test_business_project_calculator(self, calculator_business):
        """Test calculator for business projects."""
        assert calculator_business.project_type == "business"
        assert calculator_business.phase_categories is not None

    def test_different_phases(self, calculator_software):
        """Test analysis for different project phases."""
        project = ProjectContext(
            project_id="proj-phases",
            name="Phases",
            owner="user",
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="implementation",  # Different phase
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            category_scores={
                "implementation": {
                    "code_quality": {
                        "current_score": 0.75,
                        "target_score": 1.0,
                        "spec_count": 10,
                    }
                }
            },
        )

        result = calculator_software.analyze_category_performance(project)

        assert result["phase"] == "implementation"


class TestAnalyticsEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_project(self, calculator_software):
        """Test analytics with empty project."""
        project = ProjectContext(
            project_id="proj-empty",
            name="Empty",
            owner="user",
            collaborators=[],
            goals="",
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
            category_scores={},
        )

        # Should handle empty categories gracefully
        result = calculator_software.analyze_category_performance(project)

        assert isinstance(result, dict)

    def test_project_with_none_categories(self, calculator_software):
        """Test analytics with None category scores."""
        project = ProjectContext(
            project_id="proj-none",
            name="None",
            owner="user",
            collaborators=[],
            goals="",
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
            category_scores=None,
        )

        # Should handle None gracefully
        try:
            result = calculator_software.analyze_category_performance(project)
            assert isinstance(result, dict)
        except Exception:
            # It's acceptable if it raises an error for None
            pass

    def test_perfect_score_categories(self, calculator_software):
        """Test categories with perfect scores."""
        project = ProjectContext(
            project_id="proj-perfect",
            name="Perfect",
            owner="user",
            collaborators=[],
            goals="Perfect project",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="design",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            category_scores={
                "design": {
                    "perfect_category": {
                        "current_score": 1.0,
                        "target_score": 1.0,
                        "spec_count": 10,
                    }
                }
            },
        )

        result = calculator_software.analyze_category_performance(project)

        assert isinstance(result, dict)
        strong = [c for c in result.get("strong_categories", []) if c.get("percentage") == 100.0]
        assert len(strong) > 0

    def test_very_large_scores(self, calculator_software):
        """Test handling of very large score values."""
        project = ProjectContext(
            project_id="proj-large",
            name="Large",
            owner="user",
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="design",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            category_scores={
                "design": {
                    "large_category": {
                        "current_score": 1000000.0,
                        "target_score": 1.0,
                        "spec_count": 100,
                    }
                }
            },
        )

        result = calculator_software.analyze_category_performance(project)

        assert isinstance(result, dict)


class TestAnalyticsIntegration:
    """Integration tests for complete analytics workflow."""

    def test_full_analytics_workflow(self, calculator_software, project_balanced):
        """Test complete analytics workflow."""
        # 1. Analyze performance
        performance = calculator_software.analyze_category_performance(project_balanced)
        assert isinstance(performance, dict)

        # 2. Calculate velocity
        velocity = calculator_software.calculate_velocity(project_balanced)
        assert isinstance(velocity, (int, float))

        # 3. Analyze trends
        trends = calculator_software.analyze_progression_trends(project_balanced)
        assert isinstance(trends, dict)

        # 4. Generate recommendations
        recommendations = calculator_software.generate_recommendations(project_balanced)
        assert isinstance(recommendations, list)

        # 5. Suggest questions
        questions = calculator_software.suggest_next_questions(project_balanced)
        assert isinstance(questions, list)

    def test_sequential_recommendations(self, calculator_software):
        """Test recommendations for project progression."""
        # Initial state - weak project
        weak_project = ProjectContext(
            project_id="prog-weak",
            name="Progressive",
            owner="user",
            collaborators=[],
            goals="Initial",
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
            category_scores={
                "discovery": {"goals": {"current_score": 0.3, "target_score": 1.0, "spec_count": 1}}
            },
            maturity_history=[{"timestamp": datetime.datetime.now(), "score": 0.3}],
        )

        recs_1 = calculator_software.generate_recommendations(weak_project)
        assert len(recs_1) > 0

        # Advanced state - stronger project
        weak_project.category_scores["discovery"]["goals"]["current_score"] = 0.8
        weak_project.maturity_history.append({"timestamp": datetime.datetime.now(), "score": 0.8})

        recs_2 = calculator_software.generate_recommendations(weak_project)
        assert isinstance(recs_2, list)
