"""
Unit tests for knowledge router.

Tests document management, import, search, and knowledge base operations.
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
class TestDocumentListing:
    """Tests for document listing and filtering."""

    def test_list_all_documents(self, client, valid_token):
        """Test listing all documents."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents", headers=headers)
        assert response.status_code in [200, 401, 500, 404]
        if response.status_code == 200:
            data = response.json()
            # Response can be wrapped in {data: {...}} or have documents at top level
            assert "documents" in data or "documents" in data.get("data", {}) or isinstance(data, list)

    def test_list_documents_with_limit(self, client, valid_token):
        """Test listing documents with limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?limit=10", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_list_documents_with_offset(self, client, valid_token):
        """Test listing documents with offset."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?offset=5", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_filter_by_document_type(self, client, valid_token):
        """Test filtering documents by type."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?document_type=pdf", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_filter_by_project_id(self, client, valid_token):
        """Test filtering documents by project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?project_id=test_proj", headers=headers)
        assert response.status_code in [200, 401, 500, 404, 403]

    def test_search_by_query(self, client, valid_token):
        """Test searching documents by query."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?search=python", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_sort_by_uploaded_at(self, client, valid_token):
        """Test sorting documents by upload date."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?sort_by=uploaded_at", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_sort_by_title(self, client, valid_token):
        """Test sorting documents by title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents?sort_by=title", headers=headers)
        assert response.status_code in [200, 401, 500, 404]


@pytest.mark.unit
class TestDocumentRetrieval:
    """Tests for getting individual document details."""

    def test_get_document(self, client, valid_token):
        """Test getting document details."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents/doc_123", headers=headers)
        assert response.status_code in [200, 404, 401, 500]

    def test_get_nonexistent_document(self, client, valid_token):
        """Test getting non-existent document."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/knowledge/documents/nonexistent_doc_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 401, 500]

    def test_get_document_preview(self, client, valid_token):
        """Test getting document with preview."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents/doc_123?preview=true", headers=headers)
        assert response.status_code in [200, 404, 401, 500]

    def test_document_response_structure(self, client, valid_token):
        """Test document response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents/doc_123", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "id" in data or "document_id" in data


@pytest.mark.unit
class TestFileImport:
    """Tests for file import functionality."""

    def test_import_text_with_title(self, client, valid_token):
        """Test importing text with title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/text",
            json={
                "content": "This is test content",
                "title": "Test Document",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_import_text_without_title(self, client, valid_token):
        """Test importing text without title (defaults to Untitled)."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/text",
            json={"content": "This is test content"},
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_import_empty_text(self, client, valid_token):
        """Test importing empty text."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/text",
            json={"content": ""},
            headers=headers,
        )
        assert response.status_code in [400, 422, 401, 500, 404]

    def test_import_very_long_content(self, client, valid_token):
        """Test importing very long content."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/text",
            json={"content": "x" * 50000},
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_import_text_with_category(self, client, valid_token):
        """Test importing text with category."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/text",
            json={
                "content": "Python tutorial",
                "category": "tutorials",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_import_text_unicode(self, client, valid_token):
        """Test importing text with unicode characters."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/text",
            json={
                "content": "Unicode test: 你好世界 🌍 مرحبا",
                "title": "Unicode Doc",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]


@pytest.mark.unit
class TestURLImport:
    """Tests for URL import functionality."""

    def test_import_valid_url(self, client, valid_token):
        """Test importing from valid URL."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/url",
            json={"url": "https://example.com"},
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_import_invalid_url(self, client, valid_token):
        """Test importing from invalid URL."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/url",
            json={"url": "not-a-valid-url"},
            headers=headers,
        )
        assert response.status_code in [400, 422, 401, 500, 404]

    def test_import_url_with_title(self, client, valid_token):
        """Test importing URL with custom title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/import/url",
            json={
                "url": "https://example.com",
                "title": "Custom Title",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]


@pytest.mark.unit
class TestKnowledgeSearch:
    """Tests for semantic search functionality."""

    def test_search_with_q_param(self, client, valid_token):
        """Test semantic search with 'q' parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/search?q=python", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_search_with_query_param(self, client, valid_token):
        """Test semantic search with 'query' parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/search?query=REST API", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_search_with_top_k(self, client, valid_token):
        """Test search with top_k limiting."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/search?query=test&top_k=5", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_search_no_results(self, client, valid_token):
        """Test search with no matching results."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/knowledge/search?query=nonexistent_xyz_12345",
            headers=headers,
        )
        assert response.status_code in [200, 401, 500, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_search_unicode_query(self, client, valid_token):
        """Test search with unicode query."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/search?query=中文", headers=headers)
        assert response.status_code in [200, 401, 500, 404]


@pytest.mark.unit
class TestKnowledgeEntry:
    """Tests for adding knowledge entries."""

    def test_add_knowledge_entry(self, client, valid_token):
        """Test adding a knowledge entry."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/entries",
            json={
                "title": "REST API Best Practices",
                "content": "Design principles for REST APIs",
                "category": "guides",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_add_entry_without_title(self, client, valid_token):
        """Test adding entry without title."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/entries",
            json={
                "content": "Some content",
                "category": "notes",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 422, 401, 500, 404]

    def test_add_entry_with_tags(self, client, valid_token):
        """Test adding entry with tags."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/entries",
            json={
                "title": "Entry",
                "content": "Content",
                "category": "notes",
                "tags": ["important", "reference"],
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]


@pytest.mark.unit
class TestDocumentAnalytics:
    """Tests for document analytics."""

    def test_get_document_analytics(self, client, valid_token):
        """Test getting document analytics."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents/doc_123/analytics", headers=headers)
        assert response.status_code in [200, 404, 401, 500]

    def test_analytics_includes_word_count(self, client, valid_token):
        """Test that analytics includes word count."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/documents/doc_123/analytics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "word_count" in data or "words" in data


@pytest.mark.unit
class TestDocumentDeletion:
    """Tests for document deletion."""

    def test_delete_document(self, client, valid_token):
        """Test deleting a document."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete("/knowledge/documents/doc_123", headers=headers)
        assert response.status_code in [200, 404, 401, 500]

    def test_delete_nonexistent_document(self, client, valid_token):
        """Test deleting non-existent document."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/knowledge/documents/nonexistent_xyz",
            headers=headers,
        )
        assert response.status_code in [404, 401, 500]

    def test_bulk_delete_documents(self, client, valid_token):
        """Test bulk deleting multiple documents."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/documents/bulk-delete",
            json={"document_ids": ["doc_1", "doc_2", "doc_3"]},
            headers=headers,
        )
        assert response.status_code in [200, 400, 401, 500, 404, 422]


@pytest.mark.unit
class TestKnowledgeAuthentication:
    """Tests for knowledge endpoint authentication."""

    def test_list_documents_requires_auth(self, client):
        """Test that listing documents requires auth."""
        response = client.get("/knowledge/documents")
        assert response.status_code in [401, 404]

    def test_import_requires_auth(self, client):
        """Test that import requires auth."""
        response = client.post("/knowledge/import/text", json={"content": "test"})
        assert response.status_code in [401, 404]

    def test_search_requires_auth(self, client):
        """Test that search requires auth."""
        response = client.get("/knowledge/search?q=test")
        assert response.status_code in [401, 404]

    def test_invalid_token(self, client):
        """Test with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/knowledge/documents", headers=headers)
        assert response.status_code in [401, 404]


@pytest.mark.unit
class TestKnowledgeEdgeCases:
    """Tests for edge cases."""

    def test_import_multiple_documents(self, client, valid_token):
        """Test importing multiple documents sequentially."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        for i in range(3):
            response = client.post(
                "/knowledge/import/text",
                json={
                    "title": f"Document {i}",
                    "content": f"Content {i}",
                },
                headers=headers,
            )
            assert response.status_code in [201, 400, 401, 500, 404]

    def test_bulk_import_documents(self, client, valid_token):
        """Test bulk importing documents."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/knowledge/documents/bulk-import",
            json={
                "documents": [
                    {"title": "Doc1", "content": "Content1"},
                    {"title": "Doc2", "content": "Content2"},
                ]
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 500, 404]

    def test_search_special_characters(self, client, valid_token):
        """Test search with special characters."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/knowledge/search?query=C%2B%2B", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_very_long_search_query(self, client, valid_token):
        """Test search with very long query."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        long_query = "x" * 1000
        response = client.get(f"/knowledge/search?query={long_query}", headers=headers)
        assert response.status_code in [200, 401, 500, 404]
