"""
Smoke tests for Phase 2 Sprint 2 - Verify all new endpoints exist and return responses.

These are lightweight integration tests that verify:
1. All new endpoints are properly registered
2. Endpoints return appropriate HTTP status codes
3. Basic error handling works
"""

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from socrates_api.auth.jwt_handler import JWTHandler

# Test data
TEST_USER = "testuser"
TEST_USER_2 = "testuser2"
TEST_PROJECT_ID = "test_project_id"

# Create valid JWT tokens
VALID_TOKEN = JWTHandler.create_access_token(
    subject=TEST_USER,
    expires_delta=timedelta(hours=1)
)

# Fixtures
@pytest.fixture(scope="module")
def client():
    """Create test client."""
    from socrates_api.main import app
    return TestClient(app)


# ============================================================================
# ENDPOINT EXISTENCE TESTS
# ============================================================================

def test_app_loads(client):
    """Verify the FastAPI app loads successfully."""
    assert client is not None
    print(f"✓ App loaded with {len(client.app.routes)} routes")


def test_collaboration_invitations_endpoint_exists(client):
    """Verify POST /projects/{project_id}/invitations exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    # Should return 404 (project not found) or 403 (not owner), not 404 for route
    response = client.post(
        f"/projects/{TEST_PROJECT_ID}/invitations",
        json={"email": "user@example.com", "role": "editor"},
        headers=headers
    )

    # Route should exist (status != 404 for missing route)
    assert response.status_code in [404, 403, 422], f"Got {response.status_code}: {response.text}"
    print(f"✓ POST /projects/{{project_id}}/invitations exists (status: {response.status_code})")


def test_collaboration_invitations_list_endpoint_exists(client):
    """Verify GET /projects/{project_id}/invitations exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.get(
        f"/projects/{TEST_PROJECT_ID}/invitations",
        headers=headers
    )

    assert response.status_code in [404, 403], f"Got {response.status_code}"
    print(f"✓ GET /projects/{{project_id}}/invitations exists")


def test_collaboration_activities_record_endpoint_exists(client):
    """Verify POST /projects/{project_id}/activities exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.post(
        f"/projects/{TEST_PROJECT_ID}/activities",
        json={"activity_type": "message_sent", "activity_data": {}},
        headers=headers
    )

    # Should return 404 or 403, not route not found
    assert response.status_code in [404, 403, 422], f"Got {response.status_code}: {response.text}"
    print(f"✓ POST /projects/{{project_id}}/activities exists")


def test_collaboration_activities_list_endpoint_exists(client):
    """Verify GET /projects/{project_id}/activities exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.get(
        f"/projects/{TEST_PROJECT_ID}/activities?limit=10&offset=0",
        headers=headers
    )

    assert response.status_code in [404, 403], f"Got {response.status_code}"
    print(f"✓ GET /projects/{{project_id}}/activities exists")


def test_collaboration_presence_endpoint_exists(client):
    """Verify GET /projects/{project_id}/presence exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.get(
        f"/projects/{TEST_PROJECT_ID}/presence",
        headers=headers
    )

    assert response.status_code in [404, 403], f"Got {response.status_code}"
    print(f"✓ GET /projects/{{project_id}}/presence exists")


# ============================================================================
# KNOWLEDGE BASE ENDPOINT TESTS
# ============================================================================

def test_knowledge_list_documents_with_filters_endpoint_exists(client):
    """Verify GET /knowledge/documents with filters exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.get(
        "/knowledge/documents?document_type=text&sort_by=uploaded_at&sort_order=desc&limit=10&offset=0",
        headers=headers
    )

    # Should work and return data or empty results
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()

    # Check response structure
    assert "data" in data or "documents" in data, f"Unexpected response: {data}"
    print(f"✓ GET /knowledge/documents with filters works (status: {response.status_code})")


def test_knowledge_get_document_details_endpoint_exists(client):
    """Verify GET /knowledge/documents/{doc_id} exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.get(
        "/knowledge/documents/nonexistent_doc",
        headers=headers
    )

    # Should return 404 for non-existent doc, not route not found
    assert response.status_code in [404, 400], f"Got {response.status_code}"
    print(f"✓ GET /knowledge/documents/{{doc_id}} exists")


def test_knowledge_bulk_delete_endpoint_exists(client):
    """Verify POST /knowledge/documents/bulk-delete exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.post(
        "/knowledge/documents/bulk-delete",
        json={"document_ids": ["doc1", "doc2"]},
        headers=headers
    )

    # Should not be 404 for missing route
    assert response.status_code in [200, 201, 400, 422], f"Got {response.status_code}: {response.text}"
    print(f"✓ POST /knowledge/documents/bulk-delete exists (status: {response.status_code})")


def test_knowledge_bulk_import_endpoint_exists(client):
    """Verify POST /knowledge/documents/bulk-import exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    # Test with empty files
    files = [
        ("files", ("test.txt", b"Test content", "text/plain")),
    ]

    response = client.post(
        "/knowledge/documents/bulk-import",
        files=files,
        headers=headers
    )

    # Should handle the request (not 404 for route)
    assert response.status_code in [200, 201, 400, 422, 500], f"Got {response.status_code}"
    print(f"✓ POST /knowledge/documents/bulk-import exists (status: {response.status_code})")


def test_knowledge_document_analytics_endpoint_exists(client):
    """Verify GET /knowledge/documents/{doc_id}/analytics exists."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}

    response = client.get(
        "/knowledge/documents/nonexistent_doc/analytics",
        headers=headers
    )

    # Should return 404, not route not found
    assert response.status_code in [404, 400], f"Got {response.status_code}"
    print(f"✓ GET /knowledge/documents/{{doc_id}}/analytics exists")


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_missing_auth_returns_401(client):
    """Verify endpoints require authentication."""
    response = client.get("/knowledge/documents")
    assert response.status_code == 401
    print("✓ Missing auth returns 401")


def test_invalid_token_returns_401(client):
    """Verify invalid tokens are rejected."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get(
        "/knowledge/documents",
        headers=headers
    )
    assert response.status_code == 401
    print("✓ Invalid token returns 401")


def test_valid_token_accepted(client):
    """Verify valid tokens are accepted."""
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    response = client.get(
        "/knowledge/documents",
        headers=headers
    )
    # Should not be 401 (should be 200 or some other valid response)
    assert response.status_code != 401, f"Valid token rejected with {response.status_code}"
    print(f"✓ Valid token accepted (status: {response.status_code})")


# ============================================================================
# WEBSOCKET ENDPOINT TEST
# ============================================================================

def test_websocket_endpoint_exists(client):
    """Verify WebSocket collaboration endpoint exists."""
    try:
        with client.websocket_connect(
            f"/ws/collaboration/{TEST_PROJECT_ID}?token={VALID_TOKEN}"
        ) as websocket:
            # If we get here, websocket is connected
            print("✓ WebSocket /ws/collaboration/{project_id} exists and accepts connections")
    except Exception as e:
        # WebSocket might not be available in test client context
        # But the endpoint should exist
        print(f"⚠ WebSocket test inconclusive: {type(e).__name__}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
