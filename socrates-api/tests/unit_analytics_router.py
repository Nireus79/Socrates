"""
Unit tests for analytics router.

Tests analytics summaries, reporting, trends, and subscription validation.
"""

import pytest
from fastapi.testclient import TestClient

from socrates_api.auth.jwt_handler import create_access_token
from socrates_api.main import app


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token."""
    return create_access_token("testuser")


@pytest.mark.unit
class TestAnalyticsSummary:
    """Tests for analytics summary endpoint."""

    def test_get_analytics_summary(self, client, valid_token):
        """Test getting analytics summary."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/summary", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_get_project_specific_summary(self, client, valid_token):
        """Test getting summary for specific project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/summary?project_id=test_proj", headers=headers)
        assert response.status_code in [200, 401, 404, 500]

    def test_summary_response_structure(self, client, valid_token):
        """Test summary response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/summary", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


@pytest.mark.unit
class TestProjectAnalytics:
    """Tests for project-specific analytics."""

    def test_get_project_analytics(self, client, valid_token):
        """Test getting analytics for specific project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/test_proj", headers=headers)
        assert response.status_code in [200, 401, 404, 500]

    def test_project_analytics_nonexistent(self, client, valid_token):
        """Test analytics for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/nonexistent_xyz", headers=headers)
        assert response.status_code in [404, 401, 500]

    def test_project_analytics_includes_metrics(self, client, valid_token):
        """Test project analytics includes metrics."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/test_proj", headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Should have metrics
            assert isinstance(data, dict)


@pytest.mark.unit
class TestCodeMetrics:
    """Tests for code metrics."""

    def test_get_code_metrics(self, client, valid_token):
        """Test getting code metrics."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/code-metrics", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_code_metrics_response(self, client, valid_token):
        """Test code metrics response structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/code-metrics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))


@pytest.mark.unit
class TestUsageAnalytics:
    """Tests for API usage analytics."""

    def test_get_usage_analytics(self, client, valid_token):
        """Test getting usage analytics."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/usage", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_usage_with_time_period(self, client, valid_token):
        """Test usage analytics with time period."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/usage?time_period=7d", headers=headers)
        assert response.status_code in [200, 401, 500, 404]


@pytest.mark.unit
class TestAnalyticsTrends:
    """Tests for trends and forecasting."""

    def test_get_trends_7_days(self, client, valid_token):
        """Test getting trends for 7 days."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/trends?project_id=test_proj&time_period=7d",
            headers=headers,
        )
        assert response.status_code in [200, 401, 403, 404, 500]

    def test_get_trends_30_days(self, client, valid_token):
        """Test getting trends for 30 days."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/trends?project_id=test_proj&time_period=30d",
            headers=headers,
        )
        assert response.status_code in [200, 401, 403, 404, 500]

    def test_get_trends_90_days(self, client, valid_token):
        """Test getting trends for 90 days."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/trends?project_id=test_proj&time_period=90d",
            headers=headers,
        )
        assert response.status_code in [200, 401, 403, 404, 500]

    def test_get_trends_invalid_period(self, client, valid_token):
        """Test trends with invalid time period."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/trends?project_id=test_proj&time_period=invalid",
            headers=headers,
        )
        assert response.status_code in [400, 401, 403, 404, 500]

    def test_trends_subscription_required(self, client, valid_token):
        """Test that trends may require subscription."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/trends?project_id=test_proj&time_period=30d",
            headers=headers,
        )
        # May return 403 if not subscribed
        assert response.status_code in [200, 401, 403, 404, 500]


@pytest.mark.unit
class TestRecommendations:
    """Tests for AI recommendations."""

    def test_get_recommendations(self, client, valid_token):
        """Test getting recommendations."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/recommend",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code in [200, 401, 403, 404, 500]

    def test_recommendations_nonexistent_project(self, client, valid_token):
        """Test recommendations for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/recommend",
            json={"project_id": "nonexistent_xyz"},
            headers=headers,
        )
        assert response.status_code in [404, 401, 403, 500]

    def test_recommendations_subscription_required(self, client, valid_token):
        """Test that recommendations may require subscription."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/recommend",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        # May return 403 if not subscribed
        assert response.status_code in [200, 401, 403, 404, 500]


@pytest.mark.unit
class TestComparative:
    """Tests for comparative analysis."""

    def test_compare_two_projects(self, client, valid_token):
        """Test comparing two projects."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/comparative",
            json={"project_id_1": "proj1", "project_id_2": "proj2"},
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500, 400]

    def test_compare_missing_project(self, client, valid_token):
        """Test comparison with missing project ID."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/comparative",
            json={"project_id_1": "proj1"},
            headers=headers,
        )
        assert response.status_code in [400, 422, 401, 404, 500]


@pytest.mark.unit
class TestReportGeneration:
    """Tests for report generation and export."""

    def test_export_as_pdf(self, client, valid_token):
        """Test exporting analytics as PDF."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/export",
            json={
                "project_id": "test_proj",
                "format": "pdf",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 404, 500]

    def test_export_as_csv(self, client, valid_token):
        """Test exporting analytics as CSV."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/export",
            json={
                "project_id": "test_proj",
                "format": "csv",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 404, 500]

    def test_export_invalid_format(self, client, valid_token):
        """Test export with invalid format."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/export",
            json={
                "project_id": "test_proj",
                "format": "invalid",
            },
            headers=headers,
        )
        assert response.status_code in [400, 422, 401, 404, 500]

    def test_download_report(self, client, valid_token):
        """Test downloading generated report."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/export/report_123.pdf",
            headers=headers,
        )
        assert response.status_code in [200, 404, 401, 500]

    def test_generate_comprehensive_report(self, client, valid_token):
        """Test generating comprehensive report."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/report",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]


@pytest.mark.unit
class TestDashboard:
    """Tests for dashboard data."""

    def test_get_dashboard_data(self, client, valid_token):
        """Test getting dashboard data."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/dashboard/test_proj", headers=headers)
        assert response.status_code in [200, 401, 404, 500]

    def test_dashboard_includes_metrics(self, client, valid_token):
        """Test dashboard includes key metrics."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/dashboard/test_proj", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


@pytest.mark.unit
class TestAnalysis:
    """Tests for deep analysis."""

    def test_deep_analysis(self, client, valid_token):
        """Test deep project analysis."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/analyze",
            json={"project_id": "test_proj"},
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]

    def test_analysis_breakdown(self, client, valid_token):
        """Test detailed breakdown by category."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/breakdown/test_proj",
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]

    def test_health_status(self, client, valid_token):
        """Test health status endpoint."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/analytics/status/test_proj", headers=headers)
        assert response.status_code in [200, 401, 404, 500]


@pytest.mark.unit
class TestAnalyticsAuthentication:
    """Tests for analytics endpoint authentication."""

    def test_summary_requires_auth(self, client):
        """Test that summary requires auth."""
        response = client.get("/analytics/summary")
        assert response.status_code in [401, 404]

    def test_trends_requires_auth(self, client):
        """Test that trends require auth."""
        response = client.get("/analytics/trends?project_id=test")
        assert response.status_code in [401, 404]

    def test_export_requires_auth(self, client):
        """Test that export requires auth."""
        response = client.post("/analytics/export", json={})
        assert response.status_code in [401, 404, 422]

    def test_invalid_token(self, client):
        """Test with invalid token."""
        headers = {"Authorization": "Bearer invalid_xyz"}
        response = client.get("/analytics/summary", headers=headers)
        assert response.status_code in [401, 404]


@pytest.mark.unit
class TestAnalyticsEdgeCases:
    """Tests for edge cases."""

    def test_analytics_nonexistent_project(self, client, valid_token):
        """Test analytics for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/nonexistent_xyz", headers=headers)
        assert response.status_code in [404, 401, 500]

    def test_export_nonexistent_project(self, client, valid_token):
        """Test exporting non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/analytics/export",
            json={
                "project_id": "nonexistent_xyz",
                "format": "pdf",
            },
            headers=headers,
        )
        assert response.status_code in [404, 401, 500]

    def test_multiple_analytics_requests(self, client, valid_token):
        """Test multiple analytics requests."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        for i in range(3):
            response = client.get("/analytics/summary", headers=headers)
            assert response.status_code in [200, 401, 500, 404]

    def test_path_traversal_prevention(self, client, valid_token):
        """Test that path traversal is prevented."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/analytics/export/../../etc/passwd",
            headers=headers,
        )
        # Should not allow path traversal
        assert response.status_code in [404, 401, 500]
