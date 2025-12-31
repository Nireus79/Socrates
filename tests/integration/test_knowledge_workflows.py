"""
Integration tests for knowledge management workflows.

Tests knowledge base functionality:
- Adding and managing knowledge entries
- Searching and categorizing knowledge
- Linking related knowledge
- Knowledge export and backup
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestKnowledgeEntryCreation:
    """Tests for creating knowledge entries."""

    async def test_create_knowledge_entry_success(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test creating a knowledge entry."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/knowledge",
            json={
                "title": "Database Schema Design",
                "content": "Key considerations for designing the database schema",
                "category": "architecture",
                "tags": ["database", "design"],
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        entry = response.json()
        assert entry["title"] == "Database Schema Design"
        assert entry["category"] == "architecture"

    async def test_create_knowledge_with_metadata(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test creating knowledge with additional metadata."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/knowledge",
            json={
                "title": "API Design Principles",
                "content": "REST API best practices",
                "category": "technical",
                "tags": ["api", "rest"],
                "source_url": "https://example.com/api-guide",
                "author": "John Doe",
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        entry = response.json()
        assert entry["source_url"] == "https://example.com/api-guide"

    async def test_create_knowledge_minimal_info(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test creating knowledge with minimal required fields."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/knowledge",
            json={
                "title": "Note",
                "content": "Important note",
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        entry = response.json()
        assert entry["title"] == "Note"


@pytest.mark.integration
class TestKnowledgeRetrieval:
    """Tests for retrieving knowledge entries."""

    async def test_list_project_knowledge(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entries
    ):
        """Test listing all knowledge entries in a project."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge", headers=authenticated_headers
        )
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) >= len(knowledge_entries)

    async def test_get_knowledge_entry_details(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test retrieving a specific knowledge entry."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["entry_id"] == knowledge_entry["entry_id"]

    async def test_list_knowledge_pagination(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test paginating knowledge list."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge?limit=10&offset=0",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) <= 10

    async def test_list_knowledge_sorted_by_date(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test sorting knowledge entries by creation date."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge?sort=created&order=desc",
            headers=authenticated_headers,
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestKnowledgeCategorization:
    """Tests for categorizing knowledge."""

    async def test_filter_knowledge_by_category(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test filtering knowledge by category."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge?category=architecture",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        entries = response.json()
        assert all(e["category"] == "architecture" for e in entries)

    async def test_filter_knowledge_by_tag(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test filtering knowledge by tag."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge?tag=database",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        entries = response.json()
        assert all("database" in e.get("tags", []) for e in entries)

    async def test_auto_categorization_on_create(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test automatic categorization based on content."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/knowledge",
            json={
                "title": "User Authentication Implementation",
                "content": "How to implement OAuth2 authentication",
            },
            headers=authenticated_headers,
        )
        assert response.status_code == 201
        # Should have auto-categorized based on content
        entry = response.json()
        assert entry["category"] is not None

    async def test_list_all_categories(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test retrieving all available categories."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/categories",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)

    async def test_list_all_tags(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test retrieving all tags in use."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/tags",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        tags = response.json()
        assert isinstance(tags, list)


@pytest.mark.integration
class TestKnowledgeSearch:
    """Tests for searching knowledge."""

    async def test_search_knowledge_by_title(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test searching knowledge by title."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/search?q=database",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        entries = response.json()
        assert all("database" in e["title"].lower() for e in entries)

    async def test_search_knowledge_by_content(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test searching knowledge by content."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/search?q=api",
            headers=authenticated_headers,
        )
        assert response.status_code == 200

    async def test_search_full_text(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test full-text search across all fields."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/search?q=requirements",
            headers=authenticated_headers,
        )
        assert response.status_code == 200

    async def test_search_returns_relevance_ranked(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test search results ranked by relevance."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/search?q=test",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        entries = response.json()
        # Most relevant results should be first
        if len(entries) > 1:
            assert all("relevance_score" in e or "rank" in e for e in entries)


@pytest.mark.integration
class TestKnowledgeUpdate:
    """Tests for updating knowledge entries."""

    async def test_update_knowledge_title(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test updating knowledge title."""
        response = await client.put(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            json={"title": "Updated Title"},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_update_knowledge_content(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test updating knowledge content."""
        new_content = "Updated detailed content"
        response = await client.put(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            json={"content": new_content},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["content"] == new_content

    async def test_update_knowledge_tags(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test updating knowledge tags."""
        response = await client.put(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            json={"tags": ["updated", "tags"]},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert set(response.json()["tags"]) == {"updated", "tags"}

    async def test_update_knowledge_category(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test updating knowledge category."""
        response = await client.put(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            json={"category": "technical"},
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert response.json()["category"] == "technical"


@pytest.mark.integration
class TestKnowledgeLinking:
    """Tests for linking related knowledge entries."""

    async def test_link_knowledge_entries(
        self,
        client: AsyncClient,
        authenticated_headers,
        sample_project,
        knowledge_entry,
        related_entry,
    ):
        """Test linking two knowledge entries."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}/link",
            json={"related_entry_id": related_entry["entry_id"]},
            headers=authenticated_headers,
        )
        assert response.status_code == 200

    async def test_list_linked_knowledge(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test retrieving linked knowledge entries."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}/related",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        related = response.json()
        assert isinstance(related, list)

    async def test_unlink_knowledge_entries(
        self,
        client: AsyncClient,
        authenticated_headers,
        sample_project,
        knowledge_entry,
        related_entry,
    ):
        """Test removing link between entries."""
        response = await client.delete(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}/link/{related_entry['entry_id']}",
            headers=authenticated_headers,
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestKnowledgeDeletion:
    """Tests for deleting knowledge entries."""

    async def test_delete_knowledge_entry(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test deleting a knowledge entry."""
        entry_id = knowledge_entry["entry_id"]

        response = await client.delete(
            f"/projects/{sample_project['project_id']}/knowledge/{entry_id}",
            headers=authenticated_headers,
        )
        assert response.status_code == 200

        # Entry should be deleted
        get_response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/{entry_id}",
            headers=authenticated_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_knowledge_cascade_deletes_links(
        self,
        client: AsyncClient,
        authenticated_headers,
        sample_project,
        knowledge_entry,
        related_entry,
    ):
        """Test deleting entry also removes its links."""
        # Delete the entry
        response = await client.delete(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            headers=authenticated_headers,
        )
        assert response.status_code == 200

        # Links should be deleted
        related_response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/{related_entry['entry_id']}/related",
            headers=authenticated_headers,
        )
        related_ids = [e["entry_id"] for e in related_response.json()]
        assert knowledge_entry["entry_id"] not in related_ids


@pytest.mark.integration
class TestKnowledgeExport:
    """Tests for exporting knowledge."""

    async def test_export_knowledge_json(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test exporting knowledge as JSON."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/export?format=json",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    async def test_export_knowledge_markdown(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test exporting knowledge as Markdown."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/export?format=markdown",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        assert "text/markdown" in response.headers.get("content-type", "")

    async def test_export_knowledge_with_category_filter(
        self, client: AsyncClient, authenticated_headers, sample_project
    ):
        """Test exporting specific category only."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/export?format=json&category=architecture",
            headers=authenticated_headers,
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestKnowledgeVersioning:
    """Tests for knowledge versioning and history."""

    async def test_knowledge_has_version_history(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test that knowledge entries track version history."""
        # Update entry
        await client.put(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}",
            json={"content": "Updated content"},
            headers=authenticated_headers,
        )

        # Get history
        response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}/history",
            headers=authenticated_headers,
        )
        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 1

    async def test_restore_previous_knowledge_version(
        self, client: AsyncClient, authenticated_headers, sample_project, knowledge_entry
    ):
        """Test restoring to previous version."""
        # Get history
        history_response = await client.get(
            f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}/history",
            headers=authenticated_headers,
        )
        history = history_response.json()

        if len(history) > 1:
            previous_version = history[0]

            # Restore
            response = await client.post(
                f"/projects/{sample_project['project_id']}/knowledge/{knowledge_entry['entry_id']}/restore",
                json={"version_id": previous_version["version_id"]},
                headers=authenticated_headers,
            )
            assert response.status_code == 200
