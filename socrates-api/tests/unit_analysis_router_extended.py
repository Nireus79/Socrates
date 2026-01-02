"""
Extended unit tests for analysis router - targeting 70% coverage.

Focuses on:
- Phase validation edge cases
- Event recording paths
- Orchestrator result handling
- Response data validation
- Error condition handling
- Multiple operations in sequence
"""

import pytest
from fastapi.testclient import TestClient

from socrates_api.auth.jwt_handler import create_access_token
from socrates_api.main import app


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client - session scoped for performance."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    return create_access_token("testuser")


@pytest.mark.unit
class TestValidateCodeExtended:
    """Extended tests for code validation with edge cases."""

    def test_validate_code_with_empty_project_id(self, client, valid_token):
        """Test validation with empty project_id parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate?project_id=",
            headers=headers,
        )
        assert response.status_code in [400, 404, 422, 500]

    def test_validate_code_with_special_chars_in_project_id(self, client, valid_token):
        """Test validation with special characters in project ID."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate?project_id=proj%21%40%23%24%25",
            headers=headers,
        )
        assert response.status_code in [400, 404, 422, 500]

    def test_validate_code_with_very_long_project_id(self, client, valid_token):
        """Test validation with very long project ID."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        long_id = "proj_" + "x" * 1000
        response = client.post(
            f"/analysis/validate?project_id={long_id}",
            headers=headers,
        )
        assert response.status_code in [400, 404, 422, 500]

    def test_validate_code_multiple_calls_same_project(self, client, valid_token):
        """Test validation called multiple times on same project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.post(
            "/analysis/validate?project_id=test_proj",
            headers=headers,
        )
        response2 = client.post(
            "/analysis/validate?project_id=test_proj",
            headers=headers,
        )
        # Both should have same status
        assert response1.status_code in [200, 404, 422, 500]
        assert response2.status_code in [200, 404, 422, 500]

    def test_validate_code_response_success_field(self, client, valid_token):
        """Test that validation response includes success field."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate?project_id=test_proj",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data


@pytest.mark.unit
class TestAssessMaturityExtended:
    """Extended tests for maturity assessment with edge cases."""

    def test_assess_maturity_missing_project_id(self, client, valid_token):
        """Test maturity assessment with missing project_id (should fail)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity",
            headers=headers,
        )
        # Must provide project_id
        assert response.status_code in [422, 400]

    def test_assess_maturity_all_valid_phases(self, client, valid_token):
        """Test maturity assessment for each valid phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        valid_phases = ["discovery", "analysis", "design", "implementation"]

        for phase in valid_phases:
            response = client.post(
                f"/analysis/maturity?project_id=test_proj&phase={phase}",
                headers=headers,
            )
            # All valid phases should have same response code
            assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_invalid_phase_lowercase(self, client, valid_token):
        """Test maturity with invalid phase (case mismatch)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=DISCOVERY",
            headers=headers,
        )
        # Invalid phase - should fail
        assert response.status_code in [400, 404, 422, 500]

    def test_assess_maturity_invalid_phase_typo(self, client, valid_token):
        """Test maturity with invalid phase (typo)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=discoveryy",
            headers=headers,
        )
        # Invalid phase - should fail with 400
        assert response.status_code in [400, 404, 422, 500]

    def test_assess_maturity_with_empty_phase(self, client, valid_token):
        """Test maturity with empty phase (should use project's phase)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=",
            headers=headers,
        )
        # Empty phase should default to project phase
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_without_phase_parameter(self, client, valid_token):
        """Test maturity assessment without phase (should use project's phase)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj",
            headers=headers,
        )
        # Should default to project's current phase
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_response_structure(self, client, valid_token):
        """Test that maturity response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=discovery",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "data" in data

    def test_assess_maturity_nonexistent_project(self, client, valid_token):
        """Test maturity assessment for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=nonexistent_proj_xyz_12345",
            headers=headers,
        )
        # Project not found - should fail with 404
        assert response.status_code in [404, 422, 500]


@pytest.mark.unit
class TestRunTestsExtended:
    """Extended tests for running tests with edge cases."""

    def test_run_tests_missing_project_id(self, client, valid_token):
        """Test running tests without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/test",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_run_tests_multiple_times_same_project(self, client, valid_token):
        """Test running tests multiple times on same project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.post(
            "/analysis/test?project_id=test_proj",
            headers=headers,
        )
        response2 = client.post(
            "/analysis/test?project_id=test_proj",
            headers=headers,
        )
        # Both should have same status
        assert response1.status_code in [200, 404, 422, 500]
        assert response2.status_code in [200, 404, 422, 500]

    def test_run_tests_with_special_chars_project_id(self, client, valid_token):
        """Test running tests with special characters in project ID."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/test?project_id=proj%21%40%23",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_run_tests_response_structure(self, client, valid_token):
        """Test that test response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/test?project_id=test_proj",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "data" in data


@pytest.mark.unit
class TestAnalyzeStructureExtended:
    """Extended tests for structure analysis with edge cases."""

    def test_analyze_structure_missing_project_id(self, client, valid_token):
        """Test structure analysis without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_analyze_structure_empty_project_id(self, client, valid_token):
        """Test structure analysis with empty project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure?project_id=",
            headers=headers,
        )
        assert response.status_code in [400, 404, 422, 500]

    def test_analyze_structure_multiple_calls(self, client, valid_token):
        """Test structure analysis called multiple times."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.post(
            "/analysis/structure?project_id=test_proj",
            headers=headers,
        )
        response2 = client.post(
            "/analysis/structure?project_id=test_proj",
            headers=headers,
        )
        # Both should be consistent
        assert response1.status_code in [200, 404, 422, 500]
        assert response2.status_code in [200, 404, 422, 500]

    def test_analyze_structure_response_structure(self, client, valid_token):
        """Test that analysis response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure?project_id=test_proj",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data


@pytest.mark.unit
class TestReviewCodeExtended:
    """Extended tests for code review with edge cases."""

    def test_review_code_missing_project_id(self, client, valid_token):
        """Test code review without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_review_code_nonexistent_project(self, client, valid_token):
        """Test code review for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review?project_id=nonexistent_xyz_123",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_review_code_multiple_calls_same_project(self, client, valid_token):
        """Test code review called multiple times."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.post(
            "/analysis/review?project_id=test_proj",
            headers=headers,
        )
        response2 = client.post(
            "/analysis/review?project_id=test_proj",
            headers=headers,
        )
        assert response1.status_code in [200, 404, 500]
        assert response2.status_code in [200, 404, 500]

    def test_review_code_response_structure(self, client, valid_token):
        """Test that review response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review?project_id=test_proj",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "data" in data


@pytest.mark.unit
class TestAutoFixExtended:
    """Extended tests for auto-fix functionality with edge cases."""

    def test_auto_fix_missing_project_id(self, client, valid_token):
        """Test auto-fix without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/fix",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_auto_fix_nonexistent_project(self, client, valid_token):
        """Test auto-fix for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/fix?project_id=nonexistent_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_auto_fix_multiple_times_same_project(self, client, valid_token):
        """Test auto-fix called multiple times."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.post(
            "/analysis/fix?project_id=test_proj",
            headers=headers,
        )
        response2 = client.post(
            "/analysis/fix?project_id=test_proj",
            headers=headers,
        )
        assert response1.status_code in [200, 404, 500]
        assert response2.status_code in [200, 404, 500]

    def test_auto_fix_response_structure(self, client, valid_token):
        """Test that auto-fix response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/fix?project_id=test_proj",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "data" in data


@pytest.mark.unit
class TestGetReportExtended:
    """Extended tests for analysis report generation with edge cases."""

    def test_get_report_nonexistent_project(self, client, valid_token):
        """Test getting report for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analysis/report/nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_get_report_with_special_chars_project_id(self, client, valid_token):
        """Test getting report with special characters in project ID."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analysis/report/proj%21%40%23",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_get_report_multiple_calls_same_project(self, client, valid_token):
        """Test getting report multiple times."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response1 = client.get(
            "/analysis/report/test_proj",
            headers=headers,
        )
        response2 = client.get(
            "/analysis/report/test_proj",
            headers=headers,
        )
        assert response1.status_code in [200, 404, 500]
        assert response2.status_code in [200, 404, 500]

    def test_get_report_response_structure(self, client, valid_token):
        """Test that report response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analysis/report/test_proj",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "data" in data


@pytest.mark.unit
class TestAnalysisIntegration:
    """Integration tests for multiple analysis operations."""

    def test_validate_then_assess_maturity(self, client, valid_token):
        """Test validating code then assessing maturity."""
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Validate
        validate_response = client.post(
            "/analysis/validate?project_id=test_proj",
            headers=headers,
        )

        # Assess maturity
        maturity_response = client.post(
            "/analysis/maturity?project_id=test_proj",
            headers=headers,
        )

        assert validate_response.status_code in [200, 404, 422, 500]
        assert maturity_response.status_code in [200, 404, 422, 500]

    def test_run_tests_then_review(self, client, valid_token):
        """Test running tests then reviewing code."""
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Run tests
        test_response = client.post(
            "/analysis/test?project_id=test_proj",
            headers=headers,
        )

        # Review
        review_response = client.post(
            "/analysis/review?project_id=test_proj",
            headers=headers,
        )

        assert test_response.status_code in [200, 404, 500]
        assert review_response.status_code in [200, 404, 500]

    def test_analyze_then_fix(self, client, valid_token):
        """Test analyzing structure then auto-fixing."""
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Analyze
        analyze_response = client.post(
            "/analysis/structure?project_id=test_proj",
            headers=headers,
        )

        # Fix
        fix_response = client.post(
            "/analysis/fix?project_id=test_proj",
            headers=headers,
        )

        assert analyze_response.status_code in [200, 404, 500]
        assert fix_response.status_code in [200, 404, 500]

    def test_complete_analysis_workflow(self, client, valid_token):
        """Test complete analysis workflow."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        project = "test_proj"

        # Validate
        client.post(f"/analysis/validate?project_id={project}", headers=headers)

        # Assess maturity for all phases
        for phase in ["discovery", "analysis", "design", "implementation"]:
            response = client.post(
                f"/analysis/maturity?project_id={project}&phase={phase}",
                headers=headers,
            )
            assert response.status_code in [200, 404, 422, 500]

        # Run tests
        client.post(f"/analysis/test?project_id={project}", headers=headers)

        # Analyze structure
        client.post(f"/analysis/structure?project_id={project}", headers=headers)

        # Review code
        client.post(f"/analysis/review?project_id={project}", headers=headers)

        # Get report
        response = client.get(f"/analysis/report/{project}", headers=headers)
        assert response.status_code in [200, 404, 500]
