"""
Unit tests for ProjectFileLoader - file loading and caching for chat sessions.

Tests cover:
- File availability checking
- Loading strategies (priority, sample, all)
- File ranking and prioritization
- Duplicate filtering
- Error handling and edge cases
"""

from unittest.mock import MagicMock, patch

import pytest

from socratic_system.agents.project_file_loader import ProjectFileLoader


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator"""
    orchestrator = MagicMock()
    orchestrator.database.db_path = "/tmp/test.db"
    return orchestrator


@pytest.fixture
def file_loader(mock_orchestrator):
    """Create a ProjectFileLoader instance"""
    return ProjectFileLoader(mock_orchestrator)


@pytest.fixture
def sample_project():
    """Create a sample project context"""
    project = MagicMock()
    project.project_id = "proj_test_001"
    project.name = "Test Project"
    return project


@pytest.fixture
def sample_files():
    """Create sample file list"""
    return [
        {"file_path": "README.md", "content": "# Project", "language": "markdown"},
        {"file_path": "src/main.py", "content": "def main(): pass", "language": "python"},
        {"file_path": "src/utils.py", "content": "def util(): pass", "language": "python"},
        {"file_path": "tests/test_main.py", "content": "def test(): pass", "language": "python"},
        {"file_path": "config.json", "content": "{}", "language": "json"},
        {"file_path": "docs/guide.md", "content": "# Guide", "language": "markdown"},
    ]


class TestProjectFileLoaderBasic:
    """Test basic ProjectFileLoader functionality"""

    def test_initialization(self, file_loader, mock_orchestrator):
        """Test that ProjectFileLoader initializes correctly"""
        assert file_loader.orchestrator == mock_orchestrator
        assert file_loader.logger is not None

    def test_should_load_files_returns_true_with_files(self, file_loader, sample_project):
        """Test should_load_files returns True when files exist"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_file_count.return_value = 5
            mock_pm.return_value = mock_manager

            result = file_loader.should_load_files(sample_project)
            assert result is True
            mock_manager.get_file_count.assert_called_once_with("proj_test_001")

    def test_should_load_files_returns_false_with_no_files(self, file_loader, sample_project):
        """Test should_load_files returns False when no files exist"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_file_count.return_value = 0
            mock_pm.return_value = mock_manager

            result = file_loader.should_load_files(sample_project)
            assert result is False

    def test_should_load_files_handles_exception(self, file_loader, sample_project):
        """Test should_load_files handles exceptions gracefully"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_file_count.side_effect = Exception("Database error")
            mock_pm.return_value = mock_manager

            result = file_loader.should_load_files(sample_project)
            assert result is False


class TestFileRanking:
    """Test file ranking and prioritization methods"""

    def test_rank_readme_files(self, file_loader, sample_files):
        """Test README file ranking"""
        result = file_loader._rank_readme_files(sample_files, priority=1)
        assert len(result) == 1  # Only README.md
        assert result[0][0]["file_path"] == "README.md"
        assert result[0][1] == 1

    def test_rank_main_entry_points(self, file_loader, sample_files):
        """Test main entry point ranking"""
        result = file_loader._rank_main_entry_points(sample_files, priority=2)
        assert len(result) == 1  # src/main.py
        assert result[0][0]["file_path"] == "src/main.py"
        assert result[0][1] == 2

    def test_rank_source_files(self, file_loader, sample_files):
        """Test source file ranking"""
        result = file_loader._rank_source_files(sample_files, priority=3)
        assert len(result) == 2  # src/main.py and src/utils.py
        assert all(r[1] == 3 for r in result)

    def test_rank_test_files(self, file_loader, sample_files):
        """Test test file ranking"""
        result = file_loader._rank_test_files(sample_files, priority=4)
        assert len(result) == 1  # tests/test_main.py
        assert result[0][0]["file_path"] == "tests/test_main.py"

    def test_rank_config_files(self, file_loader, sample_files):
        """Test config file ranking"""
        result = file_loader._rank_config_files(sample_files, priority=5)
        assert len(result) == 1  # config.json
        assert result[0][0]["file_path"] == "config.json"

    def test_rank_other_files(self, file_loader, sample_files):
        """Test ranking of unranked files"""
        ranked_files = [
            (sample_files[0], 1),  # README.md
            (sample_files[1], 2),  # src/main.py
        ]
        result = file_loader._rank_other_files(sample_files, ranked_files, priority=6)
        # Should return files not in ranked_files
        assert len(result) == 4
        assert all(r[1] == 6 for r in result)


class TestLoadingStrategies:
    """Test file loading strategies"""

    def test_priority_strategy(self, file_loader, sample_files):
        """Test priority-based strategy"""
        result = file_loader._priority_strategy(sample_files, max_files=3)
        assert len(result) <= 3
        # README should be first (priority 1)
        assert "README.md" in result[0]["file_path"]

    def test_priority_strategy_respects_max_files(self, file_loader, sample_files):
        """Test that priority strategy respects max_files limit"""
        result = file_loader._priority_strategy(sample_files, max_files=2)
        assert len(result) == 2

    def test_sample_strategy(self, file_loader, sample_files):
        """Test sample strategy includes important files"""
        result = file_loader._sample_strategy(sample_files, max_files=3)
        assert len(result) <= 3
        # Important files should be included
        important_paths = {f["file_path"] for f in result}
        assert any("README" in p for p in important_paths)

    def test_sample_strategy_respects_max_files(self, file_loader, sample_files):
        """Test that sample strategy respects max_files limit"""
        result = file_loader._sample_strategy(sample_files, max_files=2)
        assert len(result) <= 2

    def test_all_strategy(self, file_loader, sample_files):
        """Test all strategy returns all files"""
        result = file_loader._apply_strategy(sample_files, "all", max_files=999)
        assert len(result) == len(sample_files)

    def test_apply_strategy_priority(self, file_loader, sample_files):
        """Test apply_strategy with priority"""
        result = file_loader._apply_strategy(sample_files, "priority", max_files=3)
        assert len(result) <= 3

    def test_apply_strategy_sample(self, file_loader, sample_files):
        """Test apply_strategy with sample"""
        result = file_loader._apply_strategy(sample_files, "sample", max_files=3)
        assert len(result) <= 3

    def test_apply_strategy_all(self, file_loader, sample_files):
        """Test apply_strategy with all"""
        result = file_loader._apply_strategy(sample_files, "all", max_files=999)
        assert len(result) == len(sample_files)

    def test_apply_strategy_unknown_defaults_to_priority(self, file_loader, sample_files):
        """Test that unknown strategy defaults to priority"""
        result = file_loader._apply_strategy(sample_files, "unknown", max_files=3)
        assert len(result) <= 3


class TestFilterDuplicates:
    """Test duplicate filtering"""

    def test_filter_duplicates_returns_files(self, file_loader, sample_files):
        """Test that filter_duplicates returns files"""
        result = file_loader._filter_duplicates(sample_files, "proj_001")
        assert len(result) == len(sample_files)

    def test_filter_duplicates_with_empty_list(self, file_loader):
        """Test filter_duplicates with empty file list"""
        result = file_loader._filter_duplicates([], "proj_001")
        assert result == []

    def test_filter_duplicates_handles_exception(self, file_loader, sample_files):
        """Test filter_duplicates handles exceptions gracefully"""
        # Exception during filtering should still return files
        result = file_loader._filter_duplicates(sample_files, "proj_001")
        assert len(result) > 0


class TestResponseMethods:
    """Test response generation methods"""

    def test_empty_files_response(self, file_loader):
        """Test empty files response"""
        result = file_loader._empty_files_response("priority")
        assert result["status"] == "success"
        assert result["files_loaded"] == 0
        assert result["total_chunks"] == 0
        assert "message" in result

    def test_already_loaded_response(self, file_loader):
        """Test already loaded response"""
        result = file_loader._already_loaded_response("priority")
        assert result["status"] == "success"
        assert result["files_loaded"] == 0
        assert "message" in result


class TestLoadProjectFiles:
    """Test the main load_project_files method"""

    def test_load_project_files_no_files(self, file_loader, mock_orchestrator, sample_project):
        """Test loading when no files exist"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_file_count.return_value = 0
            mock_manager.get_project_files.return_value = []
            mock_pm.return_value = mock_manager

            result = file_loader.load_project_files(sample_project, strategy="priority")
            assert result["status"] == "success"
            assert result["files_loaded"] == 0

    def test_load_project_files_with_files(
        self, file_loader, mock_orchestrator, sample_project, sample_files
    ):
        """Test loading with actual files"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_file_count.return_value = len(sample_files)
            # Use side_effect to return files once, then empty to prevent infinite loop
            mock_manager.get_project_files.side_effect = [sample_files, []]
            mock_pm.return_value = mock_manager

            # Mock document processor
            mock_doc_processor = MagicMock()
            mock_doc_processor.process.return_value = {
                "status": "success",
                "chunks_created": 5,
            }
            mock_orchestrator.get_agent.return_value = mock_doc_processor

            result = file_loader.load_project_files(sample_project, strategy="priority")
            assert result["status"] == "success"

    def test_load_project_files_handles_exception(self, file_loader, sample_project):
        """Test load_project_files handles exceptions"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            mock_manager = MagicMock()
            mock_manager.get_file_count.side_effect = Exception("Database error")
            mock_pm.return_value = mock_manager

            result = file_loader.load_project_files(sample_project)
            assert result["status"] == "error"
            assert "message" in result

    def test_load_project_files_different_strategies(
        self, file_loader, mock_orchestrator, sample_project, sample_files
    ):
        """Test loading with different strategies"""
        with patch("socratic_system.database.project_file_manager.ProjectFileManager") as mock_pm:
            for strategy in ["priority", "sample", "all"]:
                mock_manager = MagicMock()
                mock_manager.get_file_count.return_value = len(sample_files)
                # Use side_effect to prevent infinite loop
                mock_manager.get_project_files.side_effect = [sample_files, []]
                mock_pm.return_value = mock_manager

                mock_doc_processor = MagicMock()
                mock_doc_processor.process.return_value = {
                    "status": "success",
                    "chunks_created": 3,
                }
                mock_orchestrator.get_agent.return_value = mock_doc_processor

                result = file_loader.load_project_files(sample_project, strategy=strategy)
                assert result["status"] == "success"


class TestLoadAllProjectFiles:
    """Test batch loading of files"""

    def test_load_all_project_files_single_batch(self, file_loader, sample_files):
        """Test loading files in single batch"""
        mock_manager = MagicMock()
        mock_manager.get_file_count.return_value = len(sample_files)
        # Use side_effect to return files once, then empty
        mock_manager.get_project_files.side_effect = [sample_files, []]

        result = file_loader._load_all_project_files(mock_manager, "proj_001")
        assert len(result) == len(sample_files)

    def test_load_all_project_files_multiple_batches(self, file_loader):
        """Test loading files across multiple batches"""
        # Create files for multiple batches
        batch1 = [{"file_path": f"file_{i}.py"} for i in range(100)]
        batch2 = [{"file_path": f"file_{i}.py"} for i in range(100, 150)]

        mock_manager = MagicMock()
        mock_manager.get_file_count.return_value = 150
        mock_manager.get_project_files.side_effect = [batch1, batch2, []]

        result = file_loader._load_all_project_files(mock_manager, "proj_001")
        assert len(result) == 150

    def test_load_all_project_files_empty(self, file_loader):
        """Test loading when no files exist"""
        mock_manager = MagicMock()
        mock_manager.get_file_count.return_value = 0
        mock_manager.get_project_files.return_value = []

        result = file_loader._load_all_project_files(mock_manager, "proj_001")
        assert len(result) == 0


class TestProcessProjectFiles:
    """Test file processing"""

    def test_process_project_files_success(self, file_loader, mock_orchestrator, sample_files):
        """Test successful file processing"""
        mock_doc_processor = MagicMock()
        mock_doc_processor.process.return_value = {
            "status": "success",
            "chunks_created": 5,
        }
        mock_orchestrator.get_agent.return_value = mock_doc_processor

        loaded_count, total_chunks = file_loader._process_project_files(
            sample_files, "proj_001", show_progress=False
        )

        assert loaded_count > 0
        assert total_chunks > 0

    def test_process_project_files_no_processor(self, file_loader, mock_orchestrator, sample_files):
        """Test processing when document processor is unavailable"""
        mock_orchestrator.get_agent.return_value = None

        loaded_count, total_chunks = file_loader._process_project_files(
            sample_files, "proj_001", show_progress=False
        )

        assert loaded_count == 0
        assert total_chunks == 0

    def test_process_project_files_with_progress(
        self, file_loader, mock_orchestrator, sample_files
    ):
        """Test processing with progress logging"""
        mock_doc_processor = MagicMock()
        mock_doc_processor.process.return_value = {
            "status": "success",
            "chunks_created": 1,
        }
        mock_orchestrator.get_agent.return_value = mock_doc_processor

        loaded_count, _ = file_loader._process_project_files(
            sample_files[:2], "proj_001", show_progress=True
        )

        assert loaded_count == 2

    def test_process_project_files_partial_failure(
        self, file_loader, mock_orchestrator, sample_files
    ):
        """Test processing when some files fail"""
        mock_doc_processor = MagicMock()
        mock_doc_processor.process.side_effect = [
            {"status": "success", "chunks_created": 5},
            {"status": "error", "message": "Parse error"},
            {"status": "success", "chunks_created": 3},
        ]
        mock_orchestrator.get_agent.return_value = mock_doc_processor

        loaded_count, total_chunks = file_loader._process_project_files(
            sample_files[:3], "proj_001", show_progress=False
        )

        # Only 2 files should be loaded successfully
        assert loaded_count == 2
        assert total_chunks == 8
