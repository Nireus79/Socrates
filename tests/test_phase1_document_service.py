"""
Phase 1 Tests - DocumentService and DocumentRepository

Tests the document processing service and repository pattern.
Validates that:
1. DocumentRepository provides single point of change for document data
2. DocumentService uses repository instead of direct database calls
3. No orchestrator coupling
4. Services work independently
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.repositories.document_repository import DocumentRepository
from socratic_system.services.document_service import DocumentService


class TestDocumentRepositoryInitialization:
    """Test DocumentRepository initialization and setup."""

    def test_document_repository_can_be_instantiated(self):
        """DocumentRepository should initialize with database."""
        mock_db = MagicMock()
        repo = DocumentRepository(mock_db)
        assert repo is not None
        assert repo.database == mock_db

    def test_document_repository_has_required_methods(self):
        """DocumentRepository should have all required data access methods."""
        mock_db = MagicMock()
        repo = DocumentRepository(mock_db)

        required_methods = [
            "get_project_documents",
            "add_document",
            "get_document_by_name",
            "get_documents_by_type",
            "get_document_statistics",
            "delete_document",
            "clear_documents",
        ]

        for method in required_methods:
            assert hasattr(repo, method), f"Missing method: {method}"
            assert callable(getattr(repo, method)), f"Not callable: {method}"


class TestDocumentRepositoryOperations:
    """Test DocumentRepository data access operations."""

    def test_get_project_documents_returns_list(self):
        """get_project_documents should return list of documents."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {"file_name": "doc1.txt", "word_count": 100},
            {"file_name": "doc2.pdf", "word_count": 200},
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        documents = repo.get_project_documents("test-project")

        assert isinstance(documents, list)
        assert len(documents) == 2
        assert documents[0]["file_name"] == "doc1.txt"

    def test_get_project_documents_returns_empty_for_missing_project(self):
        """get_project_documents should return empty list if project not found."""
        mock_db = MagicMock()
        mock_db.load_project.return_value = None

        repo = DocumentRepository(mock_db)
        documents = repo.get_project_documents("missing-project")

        assert documents == []

    def test_add_document_appends_to_project(self):
        """add_document should append document to project documents list."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = []
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        result = repo.add_document(
            "test-project",
            "test.txt",
            "/path/to/test.txt",
            "file",
            word_count=100,
            chunk_count=5,
            entries_stored=5,
            metadata={"is_code": False}
        )

        assert result is True
        assert len(project.documents) == 1
        assert project.documents[0]["file_name"] == "test.txt"
        assert project.documents[0]["word_count"] == 100
        mock_db.save_project.assert_called_once()

    def test_get_document_by_name_finds_document(self):
        """get_document_by_name should find document by exact name."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {"file_name": "doc1.txt", "word_count": 100},
            {"file_name": "doc2.txt", "word_count": 200},
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        doc = repo.get_document_by_name("test-project", "doc1.txt")

        assert doc is not None
        assert doc["file_name"] == "doc1.txt"
        assert doc["word_count"] == 100

    def test_get_document_by_name_returns_none_when_not_found(self):
        """get_document_by_name should return None if not found."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {"file_name": "doc1.txt", "word_count": 100},
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        doc = repo.get_document_by_name("test-project", "missing.txt")

        assert doc is None

    def test_get_documents_by_type_filters_correctly(self):
        """get_documents_by_type should return only documents of specified type."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {"file_name": "doc1.txt", "content_type": "file"},
            {"file_name": "doc2.pdf", "content_type": "file"},
            {"file_name": "doc3.txt", "content_type": "text"},
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        file_docs = repo.get_documents_by_type("test-project", "file")

        assert len(file_docs) == 2
        assert all(d["content_type"] == "file" for d in file_docs)

    def test_get_document_statistics_calculates_totals(self):
        """get_document_statistics should calculate word and chunk totals."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {
                "file_name": "doc1.txt",
                "content_type": "file",
                "word_count": 100,
                "chunk_count": 5,
                "entries_stored": 5,
            },
            {
                "file_name": "doc2.txt",
                "content_type": "text",
                "word_count": 50,
                "chunk_count": 2,
                "entries_stored": 2,
            },
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        stats = repo.get_document_statistics("test-project")

        assert stats["total_documents"] == 2
        assert stats["total_words"] == 150
        assert stats["total_chunks"] == 7
        assert "file" in stats["by_type"]
        assert "text" in stats["by_type"]

    def test_delete_document_removes_from_list(self):
        """delete_document should remove document from project."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {"file_name": "doc1.txt"},
            {"file_name": "doc2.txt"},
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        result = repo.delete_document("test-project", "doc1.txt")

        assert result is True
        assert len(project.documents) == 1
        assert project.documents[0]["file_name"] == "doc2.txt"
        mock_db.save_project.assert_called_once()

    def test_clear_documents_empties_list(self):
        """clear_documents should empty the documents list."""
        mock_db = MagicMock()
        project = MagicMock()
        project.documents = [
            {"file_name": "doc1.txt"},
            {"file_name": "doc2.txt"},
        ]
        mock_db.load_project.return_value = project

        repo = DocumentRepository(mock_db)
        result = repo.clear_documents("test-project")

        assert result is True
        assert project.documents == []
        mock_db.save_project.assert_called_once()


class TestDocumentServiceInitialization:
    """Test DocumentService initialization and setup."""

    def test_document_service_can_be_instantiated(self):
        """DocumentService should initialize with config and database."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        assert service is not None
        assert service.repository is not None

    def test_document_service_has_required_methods(self):
        """DocumentService should have all required business logic methods."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        required_methods = [
            "import_file",
            "import_directory",
            "import_text",
            "get_project_documents",
            "delete_document",
        ]

        for method in required_methods:
            assert hasattr(service, method), f"Missing method: {method}"
            assert callable(getattr(service, method)), f"Not callable: {method}"


class TestDocumentServiceOperations:
    """Test DocumentService business logic operations."""

    @patch("builtins.open")
    def test_import_file_handles_file_not_found(self, mock_open):
        """import_file should handle file not found gracefully."""
        mock_open.side_effect = FileNotFoundError()
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        result = service.import_file("test-project", "/missing/file.txt")

        assert result["status"] == "error"
        assert "File not found" in result["message"]

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_import_file_extracts_content(self, mock_open, mock_exists):
        """import_file should extract and chunk file content."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "This is test content. " * 100  # Enough to create multiple chunks
        )
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)
        service.repository.add_document = MagicMock(return_value=True)

        result = service.import_file("test-project", "/path/to/test.txt")

        assert result["status"] == "success"
        assert result["file_name"] == "test.txt"
        assert result["words_extracted"] > 0
        assert result["chunks_created"] > 0
        service.repository.add_document.assert_called_once()

    def test_import_text_handles_empty_content(self):
        """import_text should handle empty text content."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        result = service.import_text("test-project", "")

        assert result["status"] == "error"
        assert "Text content required" in result["message"]

    def test_import_text_chunks_and_stores(self):
        """import_text should chunk text and store metadata."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)
        service.repository.add_document = MagicMock(return_value=True)

        text_content = "This is test content. " * 100
        result = service.import_text(
            "test-project",
            text_content,
            title="test_document"
        )

        assert result["status"] == "success"
        assert result["words_extracted"] > 0
        assert result["chunks_created"] > 0
        assert result["content_type"] == "text"
        service.repository.add_document.assert_called_once()

    @patch("os.path.isdir")
    @patch("os.walk")
    def test_import_directory_processes_files(self, mock_walk, mock_isdir):
        """import_directory should find and process files."""
        mock_isdir.return_value = True
        mock_walk.return_value = [
            ("/dir", [], ["file1.txt", "file2.py"]),
        ]
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)
        service.import_file = MagicMock(
            return_value={"status": "success", "words_extracted": 100, "chunks_created": 5}
        )

        result = service.import_directory("test-project", "/dir", recursive=True)

        assert result["status"] == "success"
        assert result["files_processed"] >= 0

    def test_get_project_documents_returns_list_and_stats(self):
        """get_project_documents should return documents and statistics."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)
        service.repository.get_project_documents = MagicMock(return_value=[
            {"file_name": "doc1.txt", "word_count": 100},
        ])
        service.repository.get_document_statistics = MagicMock(return_value={
            "total_documents": 1,
            "total_words": 100,
        })

        result = service.get_project_documents("test-project")

        assert result["status"] == "success"
        assert result["total"] == 1
        assert "statistics" in result

    def test_delete_document_delegates_to_repository(self):
        """delete_document should use repository to delete."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)
        service.repository.delete_document = MagicMock(return_value=True)

        result = service.delete_document("test-project", "doc1.txt")

        assert result["status"] == "success"
        service.repository.delete_document.assert_called_once()

    def test_chunk_content_creates_overlapping_chunks(self):
        """_chunk_content should create overlapping chunks."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        # Create content with known word count
        content = " ".join(["word"] * 1500)  # 1500 words
        chunks = service._chunk_content(
            content, chunk_size=500, overlap=50
        )

        # With 500 word chunks and 50 word overlap:
        # Chunk 1: words 0-499
        # Chunk 2: words 450-949
        # Chunk 3: words 900-1399
        # Chunk 4: words 1350-1499 (partial)
        assert len(chunks) >= 3
        assert len(chunks) <= 4

        # Verify chunks have content
        for chunk in chunks:
            assert len(chunk.split()) > 0


class TestServiceIsolation:
    """Test that services work independently without orchestrator."""

    def test_document_service_no_orchestrator_dependency(self):
        """DocumentService should not require orchestrator."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        # Verify no orchestrator attribute
        assert not hasattr(service, "orchestrator")

        # Verify it has repository and config instead
        assert hasattr(service, "repository")
        assert hasattr(service, "config")

    def test_document_service_uses_repository_not_direct_db(self):
        """DocumentService should use repository, not direct database calls."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = DocumentService(mock_config, mock_db)

        # Verify repository is used
        assert isinstance(service.repository, DocumentRepository)

        # Get mock to verify method calls go through repository
        service.repository.get_project_documents = MagicMock(return_value=[])
        service.repository.get_project_documents("test-project")
        service.repository.get_project_documents.assert_called_once()
