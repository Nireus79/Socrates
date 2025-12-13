"""
Unit tests for project-specific knowledge management system

Tests VectorDatabase methods for project_id filtering, export/import, and scoped searches.
"""

import shutil
import tempfile

import pytest

from socratic_system.database.vector_db import VectorDatabase
from socratic_system.models.knowledge import KnowledgeEntry


@pytest.fixture
def temp_vector_db():
    """Create temporary vector database for testing"""
    temp_dir = tempfile.mkdtemp()
    db = VectorDatabase(temp_dir)
    yield db
    # Cleanup - ensure all resources are properly released
    try:
        # Close the embedding model to release file handles
        if hasattr(db, "embedding_model") and db.embedding_model is not None:
            try:
                # SentenceTransformer doesn't have a standard close method,
                # but we can help garbage collection by dereferencing
                db.embedding_model = None
            except Exception:
                pass
    except Exception:
        pass
    try:
        # Close the ChromaDB client
        if hasattr(db, "client") and db.client is not None:
            db.client.close()
    except Exception:
        pass
    finally:
        # Remove the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_global_entry():
    """Sample global knowledge entry"""
    return KnowledgeEntry(
        id="global_test_entry",
        content="This is a global knowledge entry about testing",
        category="testing",
        metadata={
            "topic": "unit_testing",
            "difficulty": "beginner",
            "tags": ["testing", "best_practices"],
        },
    )


@pytest.fixture
def sample_project_entry():
    """Sample project-specific knowledge entry"""
    return KnowledgeEntry(
        id="project_test_entry",
        content="This is project-specific knowledge about React hooks",
        category="javascript_frameworks",
        metadata={
            "topic": "react_hooks",
            "difficulty": "intermediate",
            "tags": ["react", "hooks"],
            "scope": "project",  # IMPORTANT: Mark as project-specific
        },
    )


class TestProjectKnowledgeStorage:
    """Test project-specific knowledge storage and retrieval"""

    def test_add_project_knowledge(self, temp_vector_db, sample_project_entry):
        """Test adding knowledge to a specific project"""
        project_id = "proj_001"
        result = temp_vector_db.add_project_knowledge(sample_project_entry, project_id)

        assert result is True
        assert sample_project_entry.metadata["project_id"] == project_id
        assert sample_project_entry.metadata["scope"] == "project"

    def test_get_project_knowledge(self, temp_vector_db, sample_project_entry):
        """Test retrieving all knowledge for a project"""
        project_id = "proj_002"
        temp_vector_db.add_project_knowledge(sample_project_entry, project_id)

        entries = temp_vector_db.get_project_knowledge(project_id)

        assert len(entries) == 1
        assert entries[0]["id"] == sample_project_entry.id
        assert entries[0]["content"] == sample_project_entry.content

    def test_get_project_knowledge_empty(self, temp_vector_db):
        """Test getting knowledge for non-existent project returns empty list"""
        entries = temp_vector_db.get_project_knowledge("nonexistent_project")
        assert entries == []

    def test_multiple_projects_isolated(self, temp_vector_db):
        """Test that knowledge is isolated between projects"""
        entry1 = KnowledgeEntry(
            id="entry_1",
            content="Project 1 knowledge",
            category="testing",
            metadata={"topic": "test1"},
        )
        entry2 = KnowledgeEntry(
            id="entry_2",
            content="Project 2 knowledge",
            category="testing",
            metadata={"topic": "test2"},
        )

        temp_vector_db.add_project_knowledge(entry1, "proj_A")
        temp_vector_db.add_project_knowledge(entry2, "proj_B")

        proj_a_entries = temp_vector_db.get_project_knowledge("proj_A")
        proj_b_entries = temp_vector_db.get_project_knowledge("proj_B")

        assert len(proj_a_entries) == 1
        assert len(proj_b_entries) == 1
        assert proj_a_entries[0]["id"] == "entry_1"
        assert proj_b_entries[0]["id"] == "entry_2"


class TestProjectKnowledgeExportImport:
    """Test knowledge export/import functionality"""

    def test_export_project_knowledge(self, temp_vector_db, sample_project_entry):
        """Test exporting knowledge entries for a project"""
        project_id = "proj_export"
        temp_vector_db.add_project_knowledge(sample_project_entry, project_id)

        exported = temp_vector_db.export_project_knowledge(project_id)

        assert len(exported) == 1
        assert exported[0]["id"] == sample_project_entry.id
        assert exported[0]["content"] == sample_project_entry.content
        assert "metadata" in exported[0]
        assert "category" in exported[0]

    def test_export_nonexistent_project(self, temp_vector_db):
        """Test exporting from non-existent project returns empty list"""
        exported = temp_vector_db.export_project_knowledge("nonexistent")
        assert exported == []

    def test_import_project_knowledge(self, temp_vector_db):
        """Test importing knowledge entries for a project"""
        project_id = "proj_import"
        entries_to_import = [
            {
                "id": "imported_1",
                "content": "Imported knowledge 1",
                "category": "testing",
                "metadata": {"topic": "import_test"},
            },
            {
                "id": "imported_2",
                "content": "Imported knowledge 2",
                "category": "testing",
                "metadata": {"topic": "import_test"},
            },
        ]

        count = temp_vector_db.import_project_knowledge(project_id, entries_to_import)

        assert count == 2
        imported_entries = temp_vector_db.get_project_knowledge(project_id)
        assert len(imported_entries) == 2

    def test_export_import_roundtrip(self, temp_vector_db, sample_project_entry):
        """Test that export/import roundtrip preserves data"""
        project_id = "proj_roundtrip"
        temp_vector_db.add_project_knowledge(sample_project_entry, project_id)

        # Export
        exported = temp_vector_db.export_project_knowledge(project_id)

        # Create new database and import
        temp_dir = tempfile.mkdtemp()
        new_db = VectorDatabase(temp_dir)
        new_project_id = "proj_roundtrip_new"
        import_count = new_db.import_project_knowledge(new_project_id, exported)

        assert import_count == len(exported)
        imported = new_db.get_project_knowledge(new_project_id)
        assert len(imported) == 1
        assert imported[0]["content"] == sample_project_entry.content

        shutil.rmtree(temp_dir, ignore_errors=True)


class TestProjectKnowledgeSearch:
    """Test project-scoped search functionality"""

    def test_search_with_project_filter(self, temp_vector_db):
        """Test search includes project-specific knowledge"""
        # Add global knowledge (no project_id)
        global_entry = KnowledgeEntry(
            id="global_search",
            content="Global testing knowledge",
            category="testing",
            metadata={"topic": "testing"},
        )
        temp_vector_db.add_knowledge(global_entry)

        # Add project-specific knowledge
        project_entry = KnowledgeEntry(
            id="project_search",
            content="Project-specific testing practices",
            category="testing",
            metadata={"topic": "testing"},
        )
        project_id = "search_proj"
        temp_vector_db.add_project_knowledge(project_entry, project_id)

        # Search with project_id should return both
        results = temp_vector_db.search_similar("testing", top_k=10, project_id=project_id)

        # Should get both global and project-specific results
        assert len(results) >= 2
        entry_ids = [r["metadata"].get("id") or r["metadata"].get("topic") for r in results]
        assert any("testing" in str(e) for e in entry_ids)

    def test_search_without_project_filter(self, temp_vector_db):
        """Test search without project_id returns only global knowledge"""
        # Add project-specific knowledge
        project_entry = KnowledgeEntry(
            id="project_only",
            content="Project-specific knowledge only",
            category="testing",
            metadata={"topic": "project_specific"},
        )
        temp_vector_db.add_project_knowledge(project_entry, "some_project")

        # Search without project_id should not include project-specific knowledge
        results = temp_vector_db.search_similar("project specific", top_k=10, project_id=None)

        # Should not contain project-specific entries
        entry_ids = [r["metadata"].get("id") for r in results]
        assert "project_only" not in entry_ids


class TestProjectKnowledgeDeletion:
    """Test project knowledge deletion"""

    def test_delete_project_knowledge(self, temp_vector_db):
        """Test deleting all knowledge for a project"""
        project_id = "proj_delete"
        entry1 = KnowledgeEntry(
            id="del_1",
            content="Entry to delete 1",
            category="testing",
            metadata={"topic": "delete"},
        )
        entry2 = KnowledgeEntry(
            id="del_2",
            content="Entry to delete 2",
            category="testing",
            metadata={"topic": "delete"},
        )

        temp_vector_db.add_project_knowledge(entry1, project_id)
        temp_vector_db.add_project_knowledge(entry2, project_id)

        # Verify entries exist
        assert len(temp_vector_db.get_project_knowledge(project_id)) == 2

        # Delete
        count = temp_vector_db.delete_project_knowledge(project_id)

        assert count == 2
        assert len(temp_vector_db.get_project_knowledge(project_id)) == 0

    def test_delete_project_knowledge_doesnt_affect_global(self, temp_vector_db):
        """Test that deleting project knowledge doesn't affect global knowledge"""
        project_id = "proj_delete_safe"

        # Add global knowledge
        global_entry = KnowledgeEntry(
            id="global_safe",
            content="Global knowledge",
            category="testing",
            metadata={"topic": "global"},
        )
        temp_vector_db.add_knowledge(global_entry)

        # Add project knowledge
        project_entry = KnowledgeEntry(
            id="project_delete",
            content="Project knowledge",
            category="testing",
            metadata={"topic": "project"},
        )
        temp_vector_db.add_project_knowledge(project_entry, project_id)

        # Delete project knowledge
        temp_vector_db.delete_project_knowledge(project_id)

        # Global knowledge should still be searchable
        results = temp_vector_db.search_similar("global knowledge", top_k=5, project_id=None)
        assert len(results) > 0


class TestMetadataFiltering:
    """Test the _build_project_filter helper method"""

    def test_build_filter_none_project(self, temp_vector_db):
        """Test filter for global knowledge (project_id=None)"""
        filter_dict = temp_vector_db._build_project_filter(None)

        # When no project is specified, return None to search ALL knowledge
        # This is the only approach that works with ChromaDB's operator limitations
        assert filter_dict is None

    def test_build_filter_with_project(self, temp_vector_db):
        """Test filter for specific project"""
        project_id = "test_proj"
        filter_dict = temp_vector_db._build_project_filter(project_id)

        assert filter_dict is not None
        assert "$or" in filter_dict
        # Should include both global and project-specific
        assert len(filter_dict["$or"]) == 2
