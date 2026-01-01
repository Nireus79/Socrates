"""
Unit tests for FileChangeTracker - detects and syncs file changes.

Tests cover:
- File hash computation
- Change detection (added, modified, deleted, unchanged)
- Vector DB updates
- Database updates
- Change synchronization
- Error handling and edge cases
"""

from unittest.mock import MagicMock, patch

import pytest

from socratic_system.utils.file_change_tracker import FileChangeTracker


@pytest.fixture
def tracker():
    """Create a FileChangeTracker instance"""
    return FileChangeTracker()


@pytest.fixture
def sample_current_files():
    """Create sample current files"""
    return [
        {"file_path": "src/main.py", "content": "def main(): pass", "language": "python"},
        {"file_path": "src/utils.py", "content": "def util(): pass", "language": "python"},
        {"file_path": "src/new_file.py", "content": "new content", "language": "python"},
        {"file_path": "config.json", "content": "{}", "language": "json"},
    ]


@pytest.fixture
def sample_stored_files():
    """Create sample stored files"""
    return [
        {
            "file_path": "src/main.py",
            "content": "def main(): pass",
            "language": "python",
            "id": "file_1",
        },
        {
            "file_path": "src/utils.py",
            "content": "def old_util(): pass",  # Changed content
            "language": "python",
            "id": "file_2",
        },
        {
            "file_path": "src/old_file.py",
            "content": "old content",  # Will be deleted
            "language": "python",
            "id": "file_3",
        },
        {"file_path": "config.json", "content": "{}", "language": "json", "id": "file_4"},
    ]


class TestComputeHash:
    """Test hash computation"""

    def test_compute_hash_basic(self, tracker):
        """Test basic hash computation"""
        content = "test content"
        hash_value = tracker.compute_hash(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5 hash length

    def test_compute_hash_consistency(self, tracker):
        """Test that same content produces same hash"""
        content = "test content"
        hash1 = tracker.compute_hash(content)
        hash2 = tracker.compute_hash(content)
        assert hash1 == hash2

    def test_compute_hash_different_content(self, tracker):
        """Test that different content produces different hash"""
        hash1 = tracker.compute_hash("content1")
        hash2 = tracker.compute_hash("content2")
        assert hash1 != hash2

    def test_compute_hash_empty_string(self, tracker):
        """Test hash of empty string"""
        hash_value = tracker.compute_hash("")
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32

    def test_compute_hash_unicode_content(self, tracker):
        """Test hash with unicode content"""
        content = "こんにちは世界"
        hash_value = tracker.compute_hash(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32


class TestDetectChanges:
    """Test change detection"""

    def test_detect_new_files(self, tracker):
        """Test detection of new files"""
        current = [{"file_path": "new_file.py", "content": "new"}]
        stored = []

        result = tracker.detect_changes("proj_001", current, stored)
        assert len(result["added"]) == 1
        assert result["added"][0]["file_path"] == "new_file.py"
        assert len(result["modified"]) == 0
        assert len(result["deleted"]) == 0

    def test_detect_modified_files(self, tracker):
        """Test detection of modified files"""
        current = [{"file_path": "file.py", "content": "new content"}]
        stored = [{"file_path": "file.py", "content": "old content"}]

        result = tracker.detect_changes("proj_001", current, stored)
        assert len(result["modified"]) == 1
        assert len(result["added"]) == 0
        assert len(result["deleted"]) == 0

    def test_detect_deleted_files(self, tracker):
        """Test detection of deleted files"""
        current = []
        stored = [{"file_path": "deleted.py", "content": "content"}]

        result = tracker.detect_changes("proj_001", current, stored)
        assert len(result["deleted"]) == 1
        assert len(result["added"]) == 0
        assert len(result["modified"]) == 0

    def test_detect_unchanged_files(self, tracker):
        """Test detection of unchanged files"""
        current = [{"file_path": "file.py", "content": "same content"}]
        stored = [{"file_path": "file.py", "content": "same content"}]

        result = tracker.detect_changes("proj_001", current, stored)
        assert len(result["unchanged"]) == 1
        assert len(result["added"]) == 0
        assert len(result["modified"]) == 0
        assert len(result["deleted"]) == 0

    def test_detect_mixed_changes(
        self, tracker, sample_current_files, sample_stored_files
    ):
        """Test detection of mixed changes"""
        result = tracker.detect_changes("proj_001", sample_current_files, sample_stored_files)

        assert len(result["added"]) > 0  # src/new_file.py
        assert len(result["modified"]) > 0  # src/utils.py
        assert len(result["deleted"]) > 0  # src/old_file.py
        assert len(result["unchanged"]) > 0  # src/main.py, config.json

    def test_detect_changes_empty_files(self, tracker):
        """Test detection with empty file lists"""
        result = tracker.detect_changes("proj_001", [], [])
        assert result["added"] == []
        assert result["modified"] == []
        assert result["deleted"] == []
        assert result["unchanged"] == []

    def test_detect_changes_returns_correct_structure(self, tracker):
        """Test that result has correct structure"""
        result = tracker.detect_changes("proj_001", [], [])
        assert "added" in result
        assert "modified" in result
        assert "deleted" in result
        assert "unchanged" in result


class TestUpdateVectorDB:
    """Test vector DB updates"""

    def test_update_vector_db_no_orchestrator(self, tracker):
        """Test update with no orchestrator"""
        changes = {"added": [], "modified": [], "deleted": [], "unchanged": []}
        result = tracker.update_vector_db(changes, "proj_001", orchestrator=None)

        assert result["status"] == "success"
        assert result["added"] == 0
        assert result["modified"] == 0
        assert result["deleted"] == 0

    def test_update_vector_db_no_processor(self, tracker):
        """Test update when document processor is unavailable"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_agent.return_value = None

        changes = {
            "added": [{"file_path": "file.py", "content": "content"}],
            "modified": [],
            "deleted": [],
        }

        result = tracker.update_vector_db(changes, "proj_001", mock_orchestrator)
        assert result["status"] == "success"

    def test_update_vector_db_with_added_files(self, tracker):
        """Test adding files to vector DB"""
        mock_orchestrator = MagicMock()
        mock_processor = MagicMock()
        mock_processor.process.return_value = {"status": "success", "chunks_created": 5}
        mock_orchestrator.get_agent.return_value = mock_processor

        changes = {
            "added": [{"file_path": "new.py", "content": "new", "language": "python"}],
            "modified": [],
            "deleted": [],
        }

        result = tracker.update_vector_db(changes, "proj_001", mock_orchestrator)
        assert result["status"] == "success"
        assert result["added"] == 1

    def test_update_vector_db_with_modified_files(self, tracker):
        """Test updating modified files in vector DB"""
        mock_orchestrator = MagicMock()
        mock_processor = MagicMock()
        mock_processor.process.return_value = {"status": "success"}
        mock_orchestrator.get_agent.return_value = mock_processor

        changes = {
            "added": [],
            "modified": [{"file_path": "mod.py", "content": "modified", "language": "python"}],
            "deleted": [],
        }

        result = tracker.update_vector_db(changes, "proj_001", mock_orchestrator)
        assert result["status"] == "success"
        assert result["modified"] == 1

    def test_update_vector_db_with_deleted_files(self, tracker):
        """Test deleting files from vector DB"""
        mock_orchestrator = MagicMock()
        mock_processor = MagicMock()
        mock_orchestrator.get_agent.return_value = mock_processor

        changes = {
            "added": [],
            "modified": [],
            "deleted": [{"file_path": "deleted.py", "content": "old"}],
        }

        result = tracker.update_vector_db(changes, "proj_001", mock_orchestrator)
        assert result["status"] == "success"
        assert result["deleted"] == 1

    def test_update_vector_db_handles_exception(self, tracker):
        """Test error handling in vector DB update"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_agent.side_effect = Exception("Processor error")

        changes = {"added": [], "modified": [], "deleted": []}
        result = tracker.update_vector_db(changes, "proj_001", mock_orchestrator)

        assert result["status"] == "error"
        assert "error" in result


class TestUpdateDatabase:
    """Test database updates"""

    def test_update_database_no_database(self, tracker):
        """Test update with no database"""
        changes = {"added": [], "modified": [], "deleted": [], "unchanged": []}
        result = tracker.update_database(changes, "proj_001", database=None)

        assert result["status"] == "success"
        assert result["added"] == 0
        assert result["modified"] == 0
        assert result["deleted"] == 0

    def test_update_database_with_added_files(self, tracker):
        """Test adding files to database"""
        mock_database = MagicMock()
        mock_database.db_path = "/tmp/test.db"

        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.save_files_batch.return_value = (2, "success")
            mock_pm.return_value = mock_manager

            changes = {
                "added": [
                    {"file_path": "new1.py", "content": "new1"},
                    {"file_path": "new2.py", "content": "new2"},
                ],
                "modified": [],
                "deleted": [],
            }

            result = tracker.update_database(changes, "proj_001", mock_database)
            assert result["status"] == "success"
            assert result["added"] == 2

    def test_update_database_with_modified_files(self, tracker):
        """Test updating modified files in database"""
        mock_database = MagicMock()
        mock_database.db_path = "/tmp/test.db"

        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.update_file.side_effect = [(True, "success"), (True, "success")]
            mock_pm.return_value = mock_manager

            changes = {
                "added": [],
                "modified": [
                    {"file_path": "mod1.py", "content": "modified1"},
                    {"file_path": "mod2.py", "content": "modified2"},
                ],
                "deleted": [],
            }

            result = tracker.update_database(changes, "proj_001", mock_database)
            assert result["status"] == "success"
            assert result["modified"] == 2

    def test_update_database_with_deleted_files(self, tracker):
        """Test deleting files from database"""
        mock_database = MagicMock()
        mock_database.db_path = "/tmp/test.db"

        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.delete_file.side_effect = [(True, "success"), (True, "success")]
            mock_pm.return_value = mock_manager

            changes = {
                "added": [],
                "modified": [],
                "deleted": [
                    {"file_path": "del1.py", "content": "old1"},
                    {"file_path": "del2.py", "content": "old2"},
                ],
            }

            result = tracker.update_database(changes, "proj_001", mock_database)
            assert result["status"] == "success"
            assert result["deleted"] == 2

    def test_update_database_handles_exception(self, tracker):
        """Test error handling in database update"""
        mock_database = MagicMock()
        mock_database.db_path = "/tmp/test.db"

        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_pm.side_effect = Exception("Database error")

            changes = {"added": [], "modified": [], "deleted": []}
            result = tracker.update_database(changes, "proj_001", mock_database)

            assert result["status"] == "error"
            assert "error" in result


class TestSyncChanges:
    """Test full synchronization"""

    def test_sync_changes_complete_flow(
        self, tracker, sample_current_files, sample_stored_files
    ):
        """Test complete sync flow"""
        mock_database = MagicMock()
        mock_database.db_path = "/tmp/test.db"
        mock_orchestrator = MagicMock()
        mock_processor = MagicMock()
        mock_orchestrator.get_agent.return_value = mock_processor

        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.save_files_batch.return_value = (1, "success")
            mock_manager.update_file.return_value = (True, "success")
            mock_manager.delete_file.return_value = (True, "success")
            mock_pm.return_value = mock_manager

            result = tracker.sync_changes(
                "proj_001",
                sample_current_files,
                sample_stored_files,
                orchestrator=mock_orchestrator,
                database=mock_database,
            )

            assert result["status"] == "success"
            assert "changes_detected" in result
            assert "database_update" in result
            assert "vector_db_update" in result
            assert "summary" in result

    def test_sync_changes_no_changes(self, tracker):
        """Test sync with no changes"""
        files = [{"file_path": "file.py", "content": "same"}]

        result = tracker.sync_changes("proj_001", files, files)

        assert result["status"] == "success"
        assert len(result["summary"]["added"]) == 0
        assert len(result["summary"]["modified"]) == 0
        assert len(result["summary"]["deleted"]) == 0

    def test_sync_changes_returns_structure(self, tracker):
        """Test that sync returns correct structure"""
        result = tracker.sync_changes("proj_001", [], [])

        assert "status" in result
        assert "changes_detected" in result
        assert "database_update" in result
        assert "vector_db_update" in result
        assert "summary" in result


class TestProcessFileMethods:
    """Test individual file processing methods"""

    def test_process_deleted_files_db(self, tracker):
        """Test processing deleted files in database"""
        mock_manager = MagicMock()
        mock_manager.delete_file.return_value = (True, "success")

        changes = {
            "deleted": [
                {"file_path": "del1.py", "content": "old"},
                {"file_path": "del2.py", "content": "old"},
            ]
        }

        count = tracker._process_deleted_files_db(changes, "proj_001", mock_manager)
        assert count == 2

    def test_process_modified_files_db(self, tracker):
        """Test processing modified files in database"""
        mock_manager = MagicMock()
        mock_manager.update_file.return_value = (True, "success")

        changes = {
            "modified": [
                {"file_path": "mod1.py", "content": "new"},
                {"file_path": "mod2.py", "content": "new"},
            ]
        }

        count = tracker._process_modified_files_db(changes, "proj_001", mock_manager)
        assert count == 2

    def test_process_added_files_db_empty(self, tracker):
        """Test processing empty added files"""
        mock_manager = MagicMock()
        changes = {"added": []}

        count = tracker._process_added_files_db(changes, "proj_001", mock_manager)
        assert count == 0

    def test_process_added_files_db_with_files(self, tracker):
        """Test processing added files"""
        mock_manager = MagicMock()
        mock_manager.save_files_batch.return_value = (3, "success")

        changes = {
            "added": [
                {"file_path": "new1.py", "content": "new"},
                {"file_path": "new2.py", "content": "new"},
                {"file_path": "new3.py", "content": "new"},
            ]
        }

        count = tracker._process_added_files_db(changes, "proj_001", mock_manager)
        assert count == 3

    def test_process_deleted_files_vector(self, tracker):
        """Test processing deleted files in vector DB"""
        changes = {
            "deleted": [
                {"file_path": "del1.py", "content": "old"},
                {"file_path": "del2.py", "content": "old"},
            ]
        }

        count = tracker._process_deleted_files_vector(changes)
        assert count == 2

    def test_process_modified_files_vector(self, tracker):
        """Test processing modified files in vector DB"""
        mock_processor = MagicMock()
        mock_processor.process.return_value = {"status": "success"}

        changes = {
            "modified": [
                {"file_path": "mod1.py", "content": "new", "language": "python"},
                {"file_path": "mod2.py", "content": "new", "language": "python"},
            ]
        }

        count = tracker._process_modified_files_vector(changes, "proj_001", mock_processor)
        assert count == 2

    def test_process_added_files_vector(self, tracker):
        """Test processing added files in vector DB"""
        mock_processor = MagicMock()
        mock_processor.process.return_value = {"status": "success", "chunks_created": 5}

        changes = {
            "added": [
                {"file_path": "new1.py", "content": "new", "language": "python"},
                {"file_path": "new2.py", "content": "new", "language": "python"},
            ]
        }

        count = tracker._process_added_files_vector(changes, "proj_001", mock_processor)
        assert count == 2
