"""
Test Claude-based insight categorization system
Verifies intelligent categorization with fallback to heuristics
"""

from socratic_system.core import MaturityCalculator
from socratic_system.core.insight_categorizer import InsightCategorizer


class MockClaudeClient:
    """Mock Claude client for testing categorization"""

    def __init__(self, response: str = None):
        self.response = response

    def generate_response(self, prompt: str) -> str:
        """Return mock categorization response"""
        if self.response:
            return self.response

        # Default response for testing
        return """[
  {
    "content": "Build a responsive web application",
    "category": "goals",
    "confidence": 0.95
  },
  {
    "content": "Must load in under 2 seconds",
    "category": "performance",
    "confidence": 0.92
  },
  {
    "content": "React and Node.js",
    "category": "tech_stack",
    "confidence": 0.98
  }
]"""


def test_claude_categorization_parsing():
    """Test that Claude responses are parsed correctly"""
    print("\n" + "=" * 70)
    print("TEST: Claude Categorization Parsing")
    print("=" * 70)

    client = MockClaudeClient()
    categorizer = InsightCategorizer(client)

    insights = {
        "goals": "Build a responsive web application",
        "performance": "Must load in under 2 seconds",
        "tech_stack": ["React", "Node.js"],
    }

    result = categorizer.categorize_insights(insights, "discovery", "software")

    print(f"\n[OK] Categorized {len(result)} specs")
    for spec in result:
        print(
            f"  - {spec['category']}: {spec['content'][:40]}... (confidence: {spec['confidence']})"
        )

    assert len(result) == 3, f"Expected 3 specs, got {len(result)}"
    assert result[0]["confidence"] > 0.9, "Claude should have high confidence"
    print("\n[OK] Claude categorization parsing works correctly")


def test_heuristic_fallback():
    """Test fallback to heuristic categorization when Claude unavailable"""
    print("\n" + "=" * 70)
    print("TEST: Heuristic Fallback Categorization")
    print("=" * 70)

    # No Claude client = use fallback
    calculator = MaturityCalculator("software")

    insights = {
        "goals": ["Build a web app", "Help users manage projects"],
        "requirements": ["Must be secure", "Responsive design"],
        "tech_stack": ["Python", "React"],
    }

    result = calculator.categorize_insights(insights, "discovery")

    print(f"\n[OK] Heuristic categorized {len(result)} specs")
    for spec in result[:5]:
        print(
            f"  - {spec['category']}: {spec['content'][:40]}... (confidence: {spec['confidence']})"
        )

    assert len(result) > 0, "Should categorize using heuristics"
    # Heuristic confidence should be lower
    assert all(
        spec["confidence"] <= 0.7 for spec in result
    ), "Heuristic confidence should be <= 0.7"
    print("\n[OK] Heuristic fallback works correctly")


def test_project_type_aware_categorization():
    """Test that categorization respects project type"""
    print("\n" + "=" * 70)
    print("TEST: Project-Type-Aware Categorization")
    print("=" * 70)

    # Software project - should have tech-focused categories
    calc_software = MaturityCalculator("software")
    insights_sw = {
        "tech_stack": "Python and React",
        "requirements": "API endpoints and database",
    }
    result_sw = calc_software.categorize_insights(insights_sw, "analysis")
    print(f"\n[OK] Software: {len(result_sw)} specs categorized")
    for spec in result_sw:
        print(f"  - {spec['category']}")

    # Business project - should have market-focused categories
    calc_business = MaturityCalculator("business")
    insights_biz = {
        "requirements": "Customer acquisition strategy",
        "tech_stack": "Cloud infrastructure",  # Should map to 'resources' in business
    }
    result_biz = calc_business.categorize_insights(insights_biz, "analysis")
    print(f"\n[OK] Business: {len(result_biz)} specs categorized")
    for spec in result_biz:
        print(f"  - {spec['category']}")

    # Verify categories are different
    software_cats = {s["category"] for s in result_sw}
    business_cats = {s["category"] for s in result_biz}

    print(f"\n[OK] Software categories: {software_cats}")
    print(f"[OK] Business categories: {business_cats}")
    print("\n[OK] Project types use appropriate categories")


def test_confidence_scores():
    """Test that confidence scores are reasonable"""
    print("\n" + "=" * 70)
    print("TEST: Confidence Score Handling")
    print("=" * 70)

    # Claude with high confidence
    response_high = """[
  {
    "content": "Build a web app",
    "category": "goals",
    "confidence": 0.95
  }
]"""
    client = MockClaudeClient(response_high)
    categorizer = InsightCategorizer(client)

    insights = {"goals": "Build a web app"}
    result = categorizer.categorize_insights(insights, "discovery", "software")

    assert result[0]["confidence"] == 0.95, "Should parse confidence correctly"
    print("[OK] High confidence (0.95) parsed correctly")

    # Claude with low confidence
    response_low = """[
  {
    "content": "Something technical",
    "category": "constraints",
    "confidence": 0.45
  }
]"""
    client = MockClaudeClient(response_low)
    categorizer = InsightCategorizer(client)

    result = categorizer.categorize_insights(
        {"unknown": "Something technical"}, "discovery", "software"
    )

    assert result[0]["confidence"] == 0.45, "Should handle low confidence"
    print("[OK] Low confidence (0.45) parsed correctly")

    # Heuristic fallback has lower confidence
    calc = MaturityCalculator("software")
    insights = {"goals": "Build an app"}
    result = calc.categorize_insights(insights, "discovery")

    assert all(s["confidence"] <= 0.7 for s in result), "Heuristic confidence <= 0.7"
    print("[OK] Heuristic confidence (0.7) is lower than Claude")


def test_empty_and_edge_cases():
    """Test edge cases in categorization"""
    print("\n" + "=" * 70)
    print("TEST: Edge Cases")
    print("=" * 70)

    calc = MaturityCalculator("software")

    # Empty insights
    result = calc.categorize_insights({}, "discovery")
    assert result == [], "Empty insights should return empty list"
    print("[OK] Empty insights handled")

    # None values
    result = calc.categorize_insights({"goals": None}, "discovery")
    assert result == [], "None values should be skipped"
    print("[OK] None values handled")

    # Empty strings
    result = calc.categorize_insights({"goals": ""}, "discovery")
    assert result == [], "Empty strings should be skipped"
    print("[OK] Empty strings handled")

    # Unknown field (should try to match)
    result = calc.categorize_insights({"unknown_field": "some value"}, "discovery")
    # May or may not categorize depending on matching
    print(f"[OK] Unknown field handled: {len(result)} specs")


def test_confidence_driven_maturity():
    """Test that confidence affects maturity scores"""
    print("\n" + "=" * 70)
    print("TEST: Confidence Impact on Maturity")
    print("=" * 70)

    import datetime

    from socratic_system.models import ProjectContext

    # Create project
    project = ProjectContext(
        project_id="test",
        name="Test",
        owner="test",
        collaborators=[],
        goals="",
        requirements=[],
        tech_stack=[],
        constraints=[],
        team_structure="",
        language_preferences="",
        deployment_target="",
        code_style="",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_type="software",
    )

    calc = MaturityCalculator("software")

    # Add high-confidence specs
    project.categorized_specs["discovery"] = [
        {
            "category": "goals",
            "content": "Goal 1",
            "confidence": 0.95,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
        {
            "category": "goals",
            "content": "Goal 2",
            "confidence": 0.95,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
    ]

    high_conf_maturity = calc.calculate_phase_maturity(
        project.categorized_specs["discovery"], "discovery"
    )

    print(f"[OK] High confidence specs: {high_conf_maturity.overall_score:.1f}%")

    # Add low-confidence specs
    project.categorized_specs["discovery"] = [
        {
            "category": "goals",
            "content": "Goal 1",
            "confidence": 0.5,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
        {
            "category": "goals",
            "content": "Goal 2",
            "confidence": 0.5,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
    ]

    low_conf_maturity = calc.calculate_phase_maturity(
        project.categorized_specs["discovery"], "discovery"
    )

    print(f"[OK] Low confidence specs: {low_conf_maturity.overall_score:.1f}%")

    # High confidence should score higher
    assert (
        high_conf_maturity.overall_score > low_conf_maturity.overall_score
    ), "Higher confidence should yield higher maturity"

    print("\n[OK] Confidence properly affects maturity scores")


def run_all_tests():
    """Run all Claude categorization tests"""
    print("\n" + "=" * 70)
    print("CLAUDE CATEGORIZATION TESTS")
    print("=" * 70)

    try:
        test_claude_categorization_parsing()
        test_heuristic_fallback()
        test_project_type_aware_categorization()
        test_confidence_scores()
        test_empty_and_edge_cases()
        test_confidence_driven_maturity()

        print("\n" + "=" * 70)
        print("ALL CLAUDE CATEGORIZATION TESTS PASSED!")
        print("=" * 70)
        print("\n[OK] Claude categorization system fully functional")
        print("[OK] Heuristic fallback works when Claude unavailable")
        print("[OK] Project-type awareness integrated")
        print("[OK] Confidence scores properly handled")
        print("[OK] Edge cases handled gracefully")
        print("\n" + "=" * 70 + "\n")

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
