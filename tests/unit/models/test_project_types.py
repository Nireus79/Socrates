"""
Test project-type-specific category system
Verifies that different project types have appropriate maturity categories
"""

from socratic_system.core import (
    MaturityCalculator,
    get_all_project_types,
    get_project_type_description,
)
from socratic_system.core.project_categories import PROJECT_TYPE_CATEGORIES


def test_project_types_exist():
    """Verify all project types are defined"""
    print("\n" + "=" * 70)
    print("TEST: Project Types Available")
    print("=" * 70)

    project_types = get_all_project_types()

    expected_types = ["software", "business", "creative", "research", "marketing", "educational"]

    for ptype in expected_types:
        assert ptype in project_types, f"Missing project type: {ptype}"
        description = get_project_type_description(ptype)
        print(f"[OK] {ptype.upper():<15} - {description}")

    print(f"\n[OK] All {len(project_types)} project types defined")


def test_categories_by_project_type():
    """Verify each project type has appropriate categories for each phase"""
    print("\n" + "=" * 70)
    print("TEST: Project-Type-Specific Categories")
    print("=" * 70)

    phases = ["discovery", "analysis", "design", "implementation"]

    for project_type, phase_categories in PROJECT_TYPE_CATEGORIES.items():
        print(f"\n{project_type.upper()}:")

        for phase in phases:
            assert phase in phase_categories, f"Missing phase '{phase}' in {project_type}"
            categories = phase_categories[phase]

            # Verify total points = 90
            total_points = sum(categories.values())
            assert (
                total_points == 90
            ), f"{project_type}/{phase} has {total_points} points, expected 90"

            # Count categories
            cat_count = len(categories)
            print(f"  {phase.capitalize():<15}: {cat_count} categories, 90 points")

    print("\n[OK] All project types properly configured")


def test_calculator_project_type_switching():
    """Verify MaturityCalculator can switch between project types"""
    print("\n" + "=" * 70)
    print("TEST: MaturityCalculator Project Type Switching")
    print("=" * 70)

    # Test software project type
    calc = MaturityCalculator("software")
    assert calc.project_type == "software"
    assert "tech_stack" in calc.phase_categories["analysis"]
    print(
        f"[OK] Software categories loaded: {len(calc.phase_categories['analysis'])} analysis categories"
    )

    # Test business project type
    calc.set_project_type("business")
    assert calc.project_type == "business"
    assert "financial_projections" in calc.phase_categories["analysis"]
    assert "tech_stack" not in calc.phase_categories["analysis"]
    print("[OK] Business categories loaded: financial_projections found")

    # Test creative project type
    calc.set_project_type("creative")
    assert calc.project_type == "creative"
    assert "creative_vision" in calc.phase_categories["discovery"]
    assert "problem_definition" not in calc.phase_categories["discovery"]
    print("[OK] Creative categories loaded: creative_vision found")

    # Test research project type
    calc.set_project_type("research")
    assert calc.project_type == "research"
    assert "research_question" in calc.phase_categories["discovery"]
    print("[OK] Research categories loaded: research_question found")

    # Test marketing project type
    calc.set_project_type("marketing")
    assert calc.project_type == "marketing"
    assert "campaign_objective" in calc.phase_categories["discovery"]
    print("[OK] Marketing categories loaded: campaign_objective found")

    # Test educational project type
    calc.set_project_type("educational")
    assert calc.project_type == "educational"
    assert "learning_objectives" in calc.phase_categories["discovery"]
    print("[OK] Educational categories loaded: learning_objectives found")

    print("\n[OK] All project types correctly supported")


def test_category_differences():
    """Demonstrate differences between project types"""
    print("\n" + "=" * 70)
    print("TEST: Category Differences Between Project Types")
    print("=" * 70)

    # Software vs Business - Analysis phase
    software_analysis = PROJECT_TYPE_CATEGORIES["software"]["analysis"]
    business_analysis = PROJECT_TYPE_CATEGORIES["business"]["analysis"]

    print(f"\nSoftware Analysis Categories ({len(software_analysis)}):")
    for cat in sorted(software_analysis.keys())[:4]:
        print(f"  • {cat}")

    print(f"\nBusiness Analysis Categories ({len(business_analysis)}):")
    for cat in sorted(business_analysis.keys())[:4]:
        print(f"  • {cat}")

    print("\nDifferences:")
    software_only = set(software_analysis.keys()) - set(business_analysis.keys())
    business_only = set(business_analysis.keys()) - set(software_analysis.keys())

    if software_only:
        print(f"  Only in Software: {', '.join(sorted(software_only)[:2])}")
    if business_only:
        print(f"  Only in Business: {', '.join(sorted(business_only)[:2])}")

    print("\n[OK] Project types have tailored categories for their domain")


def test_all_phases_have_90_points():
    """Verify all project types have exactly 90 points per phase"""
    print("\n" + "=" * 70)
    print("TEST: Point Distribution (90 points per phase)")
    print("=" * 70)

    all_valid = True
    for project_type, phases in PROJECT_TYPE_CATEGORIES.items():
        for phase, categories in phases.items():
            total = sum(categories.values())
            status = "[OK]" if total == 90 else "[FAIL]"
            if total != 90:
                all_valid = False
            print(f"{status} {project_type.upper():<12} {phase.capitalize():<15}: {total} points")

    assert all_valid, "Not all phases have 90 points!"
    print("\n[OK] All phases properly balanced at 90 points")


def run_all_tests():
    """Run all project type tests"""
    print("\n" + "=" * 70)
    print("PROJECT TYPE SYSTEM TESTS")
    print("=" * 70)

    try:
        test_project_types_exist()
        test_categories_by_project_type()
        test_calculator_project_type_switching()
        test_category_differences()
        test_all_phases_have_90_points()

        print("\n" + "=" * 70)
        print("ALL PROJECT TYPE TESTS PASSED!")
        print("=" * 70)
        print("\n[OK] Project type system fully functional")
        print("[OK] 6 project types supported with tailored categories")
        print("[OK] MaturityCalculator supports type switching")
        print("[OK] All point distributions balanced (90 per phase)")
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
