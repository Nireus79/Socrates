"""
Unit tests for subscription router.

Tests subscription management endpoints including:
- Getting subscription status
- Listing subscription plans
- Upgrading/downgrading plans
- Toggling testing mode
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
class TestSubscriptionStatus:
    """Tests for subscription status endpoint."""

    def test_get_subscription_status_requires_auth(self, client):
        """Test that subscription status requires authentication."""
        response = client.get("/subscription/status")

        assert response.status_code == 401
        assert "Missing authentication credentials" in response.json().get("detail", "")

    def test_get_subscription_status_success(self, client, valid_token):
        """Test getting subscription status with valid token."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/status", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "current_tier" in data["data"]
        assert "testing_mode" in data["data"]
        assert "plan" in data["data"]
        assert "usage" in data["data"]

    def test_get_subscription_status_contains_plan_info(self, client, valid_token):
        """Test that subscription status includes proper plan information."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/status", headers=headers)

        assert response.status_code == 200
        data = response.json()
        plan = data["data"]["plan"]

        # Verify plan has required fields
        assert "tier" in plan
        assert "price" in plan
        assert "projects_limit" in plan
        assert "team_members_limit" in plan
        assert "features" in plan
        assert isinstance(plan["features"], list)

    def test_get_subscription_status_contains_usage_info(self, client, valid_token):
        """Test that subscription status includes usage information."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/status", headers=headers)

        assert response.status_code == 200
        data = response.json()
        usage = data["data"]["usage"]

        # Verify usage has required fields
        assert "projects_used" in usage
        assert "projects_limit" in usage
        assert "team_members_used" in usage
        assert "team_members_limit" in usage
        assert "storage_used_gb" in usage
        assert "storage_limit_gb" in usage

    def test_get_subscription_status_invalid_token(self, client):
        """Test subscription status with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/subscription/status", headers=headers)

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json().get("detail", "")


@pytest.mark.unit
class TestSubscriptionPlans:
    """Tests for listing subscription plans endpoint."""

    def test_list_plans_requires_auth(self, client):
        """Test that list plans requires authentication."""
        response = client.get("/subscription/plans")

        assert response.status_code == 401

    def test_list_subscription_plans_success(self, client, valid_token):
        """Test successfully listing all subscription plans."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/plans", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "plans" in data["data"]

    def test_list_plans_includes_all_tiers(self, client, valid_token):
        """Test that all three subscription tiers are returned."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/plans", headers=headers)

        assert response.status_code == 200
        data = response.json()
        plans = data["data"]["plans"]
        tier_names = {plan["tier"] for plan in plans}

        assert "free" in tier_names
        assert "pro" in tier_names
        assert "enterprise" in tier_names

    def test_list_plans_free_tier_details(self, client, valid_token):
        """Test free tier plan details are correct."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/plans", headers=headers)

        assert response.status_code == 200
        data = response.json()
        plans = data["data"]["plans"]
        free_plan = next((p for p in plans if p["tier"] == "free"), None)

        assert free_plan is not None
        assert free_plan["price"] == 0.0
        assert free_plan["projects_limit"] == 1
        assert free_plan["team_members_limit"] == 1
        assert len(free_plan["features"]) > 0

    def test_list_plans_pro_tier_details(self, client, valid_token):
        """Test pro tier plan details are correct."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/plans", headers=headers)

        assert response.status_code == 200
        data = response.json()
        plans = data["data"]["plans"]
        pro_plan = next((p for p in plans if p["tier"] == "pro"), None)

        assert pro_plan is not None
        assert pro_plan["price"] == 4.99
        assert pro_plan["projects_limit"] == 10
        assert pro_plan["team_members_limit"] == 5

    def test_list_plans_enterprise_tier_details(self, client, valid_token):
        """Test enterprise tier plan details (unlimited)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/subscription/plans", headers=headers)

        assert response.status_code == 200
        data = response.json()
        plans = data["data"]["plans"]
        enterprise_plan = next((p for p in plans if p["tier"] == "enterprise"), None)

        assert enterprise_plan is not None
        assert enterprise_plan["price"] == 9.99
        assert enterprise_plan["projects_limit"] is None  # Unlimited
        assert enterprise_plan["team_members_limit"] is None  # Unlimited


@pytest.mark.unit
class TestSubscriptionUpgrade:
    """Tests for subscription upgrade endpoint."""

    def test_upgrade_requires_auth(self, client):
        """Test that upgrade requires authentication."""
        response = client.post("/subscription/upgrade?new_tier=pro")

        assert response.status_code == 401

    def test_upgrade_to_pro_success(self, client, valid_token):
        """Test successfully upgrading to pro tier."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/upgrade?new_tier=pro", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully upgraded" in data["message"]
        assert data["data"]["new_tier"] == "pro"

    def test_upgrade_to_enterprise_success(self, client, valid_token):
        """Test successfully upgrading to enterprise tier."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/upgrade?new_tier=enterprise", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["new_tier"] == "enterprise"
        assert data["data"]["plan"]["projects_limit"] is None

    def test_upgrade_with_billing_info(self, client, valid_token):
        """Test that upgrade response includes billing information."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/upgrade?new_tier=pro", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "billing" in data["data"]
        billing = data["data"]["billing"]
        assert "amount" in billing
        assert "currency" in billing
        assert "billing_cycle" in billing

    def test_upgrade_invalid_tier(self, client, valid_token):
        """Test upgrade with invalid tier name."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/upgrade?new_tier=invalid_tier", headers=headers)

        assert response.status_code == 400
        assert "Invalid tier" in response.json().get("detail", "")

    def test_upgrade_missing_tier_parameter(self, client, valid_token):
        """Test upgrade without required tier parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/upgrade", headers=headers)

        assert response.status_code == 422  # Validation error


@pytest.mark.unit
class TestSubscriptionDowngrade:
    """Tests for subscription downgrade endpoint."""

    def test_downgrade_requires_auth(self, client):
        """Test that downgrade requires authentication."""
        response = client.post("/subscription/downgrade?new_tier=free")

        assert response.status_code == 401

    def test_downgrade_to_free_success(self, client, valid_token):
        """Test successfully downgrading to free tier."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/downgrade?new_tier=free", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully downgraded" in data["message"]
        assert data["data"]["new_tier"] == "free"

    def test_downgrade_from_enterprise_to_pro(self, client, valid_token):
        """Test downgrading from enterprise to pro."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/downgrade?new_tier=pro", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["new_tier"] == "pro"

    def test_downgrade_includes_warning(self, client, valid_token):
        """Test that downgrade response includes warning about feature loss."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/downgrade?new_tier=free", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "warning" in data["data"]
        assert data["data"]["warning"] is not None

    def test_downgrade_invalid_tier(self, client, valid_token):
        """Test downgrade with invalid tier name."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/downgrade?new_tier=invalid_tier", headers=headers)

        assert response.status_code == 400
        assert "Invalid tier" in response.json().get("detail", "")

    def test_downgrade_missing_tier_parameter(self, client, valid_token):
        """Test downgrade without required tier parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/subscription/downgrade", headers=headers)

        assert response.status_code == 422  # Validation error


@pytest.mark.unit
class TestTestingMode:
    """Tests for testing mode toggle endpoint."""

    def test_testing_mode_requires_auth(self, client):
        """Test that testing mode endpoint requires authentication."""
        response = client.put("/subscription/testing-mode?enabled=true")

        assert response.status_code == 401

    def test_enable_testing_mode(self, client, valid_token):
        """Test enabling testing mode."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode?enabled=true", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["testing_mode"] is True
        assert data["data"]["effective_immediately"] is True

    def test_disable_testing_mode(self, client, valid_token):
        """Test disabling testing mode."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode?enabled=false", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["testing_mode"] is False

    def test_testing_mode_enabled_lists_restrictions(self, client, valid_token):
        """Test that enabled testing mode lists all bypassed restrictions."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode?enabled=true", headers=headers)

        assert response.status_code == 200
        data = response.json()
        restrictions = data["data"]["restrictions_bypassed"]

        assert isinstance(restrictions, list)
        assert len(restrictions) > 0
        assert "Project limits" in restrictions
        assert "Team member limits" in restrictions
        assert "Feature flags" in restrictions
        assert "Cost tracking" in restrictions

    def test_testing_mode_disabled_no_restrictions(self, client, valid_token):
        """Test that disabled testing mode has no restrictions bypassed."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode?enabled=false", headers=headers)

        assert response.status_code == 200
        data = response.json()
        restrictions = data["data"]["restrictions_bypassed"]

        assert len(restrictions) == 0

    def test_testing_mode_enabled_includes_warning(self, client, valid_token):
        """Test that enabled testing mode includes warning message."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode?enabled=true", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "warning" in data["data"]
        assert data["data"]["warning"] is not None

    def test_testing_mode_disabled_no_warning(self, client, valid_token):
        """Test that disabled testing mode has no warning."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode?enabled=false", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["warning"] is None

    def test_testing_mode_missing_enabled_parameter(self, client, valid_token):
        """Test testing mode endpoint without required enabled parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put("/subscription/testing-mode", headers=headers)

        assert response.status_code == 422  # Validation error
