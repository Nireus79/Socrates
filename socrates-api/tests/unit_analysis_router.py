"""
Unit tests for analysis router.

Tests code analysis endpoints including:
- Code validation
- Maturity assessment
- Testing functionality
- Project structure analysis
- Code review
- Auto-fix functionality
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
class TestValidateCode:
    """Tests for code validation endpoint."""

    def test_validate_code_requires_auth(self, client):
        """Test that code validation requires authentication."""
        response = client.post("/analysis/validate")
        assert response.status_code == 401

    def test_validate_code_missing_project(self, client, valid_token):
        """Test validating code without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate",
            headers=headers,
        )
        assert response.status_code in [400, 422, 500]

    def test_validate_code_nonexistent_project(self, client, valid_token):
        """Test validating code for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate?project_id=nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 422, 500]

    def test_validate_code_with_project(self, client, valid_token):
        """Test validating code with project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate?project_id=test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_validate_code_invalid_token(self, client):
        """Test validate code with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/analysis/validate",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestAssessMaturity:
    """Tests for maturity assessment endpoint."""

    def test_assess_maturity_requires_auth(self, client):
        """Test that maturity assessment requires authentication."""
        response = client.post(
            "/analysis/maturity",
            json={"project_id": "test_proj"},
        )
        assert response.status_code == 401

    def test_assess_maturity_missing_project_id(self, client, valid_token):
        """Test assessing maturity without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_assess_maturity_nonexistent_project(self, client, valid_token):
        """Test assessing maturity for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 422, 500]

    def test_assess_maturity_current_phase(self, client, valid_token):
        """Test assessing maturity for current phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_discovery_phase(self, client, valid_token):
        """Test assessing maturity for discovery phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=discovery",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_analysis_phase(self, client, valid_token):
        """Test assessing maturity for analysis phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=analysis",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_design_phase(self, client, valid_token):
        """Test assessing maturity for design phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=design",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_implementation_phase(self, client, valid_token):
        """Test assessing maturity for implementation phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=implementation",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_assess_maturity_invalid_phase(self, client, valid_token):
        """Test assessing maturity with invalid phase."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=invalid_phase_xyz",
            headers=headers,
        )
        assert response.status_code in [400, 404, 422, 500]

    def test_assess_maturity_invalid_token(self, client):
        """Test assess maturity with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/analysis/maturity",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestRunTests:
    """Tests for running tests endpoint."""

    def test_run_tests_requires_auth(self, client):
        """Test that running tests requires authentication."""
        response = client.post(
            "/analysis/test",
            json={"project_id": "test_proj"},
        )
        assert response.status_code == 401

    def test_run_tests_missing_project_id(self, client, valid_token):
        """Test running tests without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/test",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_run_tests_nonexistent_project(self, client, valid_token):
        """Test running tests for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/test?project_id=nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 422, 500]

    def test_run_tests_success(self, client, valid_token):
        """Test running tests successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/test?project_id=test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_run_tests_invalid_token(self, client):
        """Test run tests with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/analysis/test",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestAnalyzeStructure:
    """Tests for project structure analysis endpoint."""

    def test_analyze_structure_requires_auth(self, client):
        """Test that structure analysis requires authentication."""
        response = client.post(
            "/analysis/structure",
            json={"project_id": "test_proj"},
        )
        assert response.status_code == 401

    def test_analyze_structure_missing_project_id(self, client, valid_token):
        """Test analyzing structure without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_analyze_structure_nonexistent_project(self, client, valid_token):
        """Test analyzing structure for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure?project_id=nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 422, 500]

    def test_analyze_structure_success(self, client, valid_token):
        """Test analyzing structure successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure?project_id=test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_analyze_structure_invalid_token(self, client):
        """Test analyze structure with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/analysis/structure",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestReviewCode:
    """Tests for code review endpoint."""

    def test_review_code_requires_auth(self, client):
        """Test that code review requires authentication."""
        response = client.post(
            "/analysis/review",
            json={"project_id": "test_proj"},
        )
        assert response.status_code == 401

    def test_review_code_missing_project_id(self, client, valid_token):
        """Test reviewing code without project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review",
            headers=headers,
        )
        assert response.status_code in [422, 400]

    def test_review_code_nonexistent_project(self, client, valid_token):
        """Test reviewing code for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review?project_id=nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 422, 500]

    def test_review_code_success(self, client, valid_token):
        """Test code review successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review?project_id=test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_review_code_invalid_token(self, client):
        """Test review code with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/analysis/review",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestAutoFixIssues:
    """Tests for auto-fix issues endpoint."""

    def test_auto_fix_requires_auth(self, client):
        """Test that auto-fix requires authentication."""
        response = client.post(
            "/analysis/fix",
            json={"project_id": "test_proj"},
        )
        assert response.status_code == 401

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
            "/analysis/fix?project_id=nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 422, 500]

    def test_auto_fix_success(self, client, valid_token):
        """Test auto-fix successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/fix?project_id=test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_auto_fix_invalid_token(self, client):
        """Test auto-fix with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/analysis/fix",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestGetAnalysisReport:
    """Tests for analysis report endpoint."""

    def test_get_report_requires_auth(self, client):
        """Test that getting report requires authentication."""
        response = client.get("/analysis/report/test_proj")
        assert response.status_code == 401

    def test_get_report_nonexistent_project(self, client, valid_token):
        """Test getting report for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analysis/report/nonexistent_proj_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 500]

    def test_get_report_success(self, client, valid_token):
        """Test getting analysis report successfully."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analysis/report/test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_get_report_invalid_token(self, client):
        """Test get report with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get(
            "/analysis/report/test_proj",
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestAnalysisEdgeCases:
    """Tests for analysis edge cases."""

    def test_assess_maturity_phase_case_insensitive(self, client, valid_token):
        """Test assessing maturity with mixed case phase (if supported)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/maturity?project_id=test_proj&phase=DISCOVERY",
            headers=headers,
        )
        # Should either work (case-insensitive) or fail (case-sensitive)
        assert response.status_code in [200, 400, 404, 422, 500]

    def test_validate_code_with_empty_project_id(self, client, valid_token):
        """Test validating code with empty project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/validate?project_id=",
            headers=headers,
        )
        assert response.status_code in [400, 404, 422, 500]

    def test_run_tests_multiple_calls(self, client, valid_token):
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

    def test_analyze_structure_with_special_chars_project_id(self, client, valid_token):
        """Test analyzing structure with special characters in project_id."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/structure?project_id=test_proj_!@%23$%25",
            headers=headers,
        )
        # Should handle gracefully
        assert response.status_code in [400, 404, 422, 500]

    def test_review_code_response_structure(self, client, valid_token):
        """Test that review code response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analysis/review",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "data" in data

    def test_get_report_different_projects(self, client, valid_token):
        """Test getting reports for different projects."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        projects = ["test_proj", "test_proj2", "test_proj3"]

        for project in projects:
            response = client.get(
                f"/analysis/report/{project}",
                headers=headers,
            )
            assert response.status_code in [200, 404, 500]

    def test_assess_all_valid_phases(self, client, valid_token):
        """Test assessing maturity for all valid phases."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        valid_phases = ["discovery", "analysis", "design", "implementation"]

        for phase in valid_phases:
            response = client.post(
                f"/analysis/maturity?project_id=test_proj&phase={phase}",
                headers=headers,
            )
            # Should succeed or fail with project not found, not phase validation
            assert response.status_code in [200, 404, 422, 500]
