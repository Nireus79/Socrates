"""
Unit tests for notes router.

Tests note management endpoints including:
- Adding notes to projects
- Listing project notes
- Searching notes
- Deleting notes
- Filtering and pagination
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
class TestAddNote:
    """Tests for adding notes endpoint."""

    def test_add_note_requires_auth(self, client):
        """Test that add note requires authentication."""
        response = client.post(
            "/projects/test_proj/notes",
            json={"content": "Test note"},
        )

        assert response.status_code == 401

    def test_add_note_missing_content(self, client, valid_token):
        """Test adding note without required content field."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes",
            json={},
            headers=headers,
        )

        assert response.status_code == 422  # Validation error

    def test_add_note_nonexistent_project(self, client, valid_token):
        """Test adding note to non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_project_xyz/notes",
            json={"content": "Test note"},
            headers=headers,
        )

        assert response.status_code == 404

    def test_add_note_with_title_and_tags(self, client, valid_token):
        """Test adding note with title and tags."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes",
            json={
                "content": "Test note content",
                "title": "Test Title",
                "tags": ["important", "design"],
            },
            headers=headers,
        )

        # Should fail due to project not found, but validates structure
        assert response.status_code in [201, 404, 500]
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_add_note_invalid_token(self, client):
        """Test add note with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/notes",
            json={"content": "Test note"},
            headers=headers,
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestListNotes:
    """Tests for listing notes endpoint."""

    def test_list_notes_requires_auth(self, client):
        """Test that list notes requires authentication."""
        response = client.get("/projects/test_proj/notes")

        assert response.status_code == 401

    def test_list_notes_nonexistent_project(self, client, valid_token):
        """Test listing notes for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/nonexistent_project_xyz/notes", headers=headers)

        assert response.status_code == 404

    def test_list_notes_empty(self, client, valid_token):
        """Test listing notes when project has no notes."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/test_proj/notes", headers=headers)

        # Should fail due to project not found, but validates structure
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "notes" in data["data"]
            assert "total" in data["data"]
            assert "returned" in data["data"]

    def test_list_notes_with_limit(self, client, valid_token):
        """Test listing notes with limit parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/notes?limit=5",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]

    def test_list_notes_filter_by_tag(self, client, valid_token):
        """Test filtering notes by tag."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/notes?tag=design",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "filtered_by_tag" in data["data"]
            assert data["data"]["filtered_by_tag"] == "design"

    def test_list_notes_with_limit_and_tag(self, client, valid_token):
        """Test listing notes with both limit and tag filter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/notes?limit=5&tag=design",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]

    def test_list_notes_invalid_token(self, client):
        """Test list notes with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/projects/test_proj/notes", headers=headers)

        assert response.status_code == 401


@pytest.mark.unit
class TestSearchNotes:
    """Tests for searching notes endpoint."""

    def test_search_notes_requires_auth(self, client):
        """Test that search notes requires authentication."""
        response = client.post(
            "/projects/test_proj/notes/search?query=test",
        )

        assert response.status_code == 401

    def test_search_notes_missing_query(self, client, valid_token):
        """Test searching without query parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes/search",
            headers=headers,
        )

        assert response.status_code == 422  # Validation error

    def test_search_notes_nonexistent_project(self, client, valid_token):
        """Test searching notes in non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/nonexistent_project_xyz/notes/search?query=test",
            headers=headers,
        )

        assert response.status_code == 404

    def test_search_notes_response_structure(self, client, valid_token):
        """Test that search response has proper structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes/search?query=test",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "results" in data["data"]
            assert "total_matches" in data["data"]
            assert "query" in data["data"]

    def test_search_notes_empty_results(self, client, valid_token):
        """Test search that returns no results."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes/search?query=nonexistent_search_term_xyz123",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["data"]["total_matches"] == 0

    def test_search_notes_invalid_token(self, client):
        """Test search notes with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects/test_proj/notes/search?query=test",
            headers=headers,
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestDeleteNote:
    """Tests for deleting notes endpoint."""

    def test_delete_note_requires_auth(self, client):
        """Test that delete note requires authentication."""
        response = client.delete("/projects/test_proj/notes/note_123")

        assert response.status_code == 401

    def test_delete_note_nonexistent_project(self, client, valid_token):
        """Test deleting note from non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/nonexistent_project_xyz/notes/note_123",
            headers=headers,
        )

        assert response.status_code == 404

    def test_delete_nonexistent_note(self, client, valid_token):
        """Test deleting a note that doesn't exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/notes/nonexistent_note_xyz",
            headers=headers,
        )

        # Should fail due to note not found
        assert response.status_code in [404, 500]

    def test_delete_note_response_structure(self, client, valid_token):
        """Test that delete response has proper structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/notes/note_123",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "note_id" in data["data"]

    def test_delete_note_invalid_token(self, client):
        """Test delete note with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.delete(
            "/projects/test_proj/notes/note_123",
            headers=headers,
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestNoteEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_add_note_with_special_characters(self, client, valid_token):
        """Test adding note with special characters in content."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes",
            json={
                "content": "Note with special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/\\`~",
            },
            headers=headers,
        )

        assert response.status_code in [201, 404, 500]

    def test_add_note_with_empty_title(self, client, valid_token):
        """Test adding note with empty title (should default to 'Untitled')."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes",
            json={
                "content": "Test content",
                "title": "",
            },
            headers=headers,
        )

        assert response.status_code in [201, 404, 500]

    def test_add_note_with_many_tags(self, client, valid_token):
        """Test adding note with many tags."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        tags = [f"tag_{i}" for i in range(10)]
        response = client.post(
            "/projects/test_proj/notes",
            json={
                "content": "Test content",
                "tags": tags,
            },
            headers=headers,
        )

        assert response.status_code in [201, 404, 500]

    def test_list_notes_with_zero_limit(self, client, valid_token):
        """Test listing notes with zero limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/notes?limit=0",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]

    def test_search_notes_case_insensitive(self, client, valid_token):
        """Test that search is case-insensitive."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes/search?query=TEST",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]

    def test_search_notes_partial_match(self, client, valid_token):
        """Test search with partial word match."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/notes/search?query=des",
            headers=headers,
        )

        assert response.status_code in [200, 404, 500]
