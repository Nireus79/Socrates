"""
Project File Loader - Auto-loads project files into vector DB for chat sessions

Handles:
- Checking if project has files to load
- Loading files with different strategies (priority, sample, all)
- Filtering duplicates from vector DB
- Processing files through DocumentProcessor
"""

import logging
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from socratic_system.models import ProjectContext
    from socratic_system.orchestration import AgentOrchestrator

logger = logging.getLogger("socrates.agents.project_file_loader")


class ProjectFileLoader:
    """Auto-loads project files into vector DB for chat sessions"""

    def __init__(self, orchestrator: "AgentOrchestrator") -> None:
        """
        Initialize project file loader

        Args:
            orchestrator: Agent orchestrator with access to database and vector DB
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("socrates.agents.project_file_loader")

    def should_load_files(self, project: "ProjectContext") -> bool:
        """
        Check if project has files and they should be loaded

        Args:
            project: Project context

        Returns:
            True if project has files to load, False otherwise
        """
        try:
            from socratic_system.database.project_file_manager import ProjectFileManager

            file_manager = ProjectFileManager(self.orchestrator.database.db_path)
            file_count = file_manager.get_file_count(project.project_id)
            return file_count > 0
        except Exception as e:
            self.logger.error(f"Error checking if files should be loaded: {str(e)}")
            return False

    def load_project_files(
        self,
        project: "ProjectContext",
        strategy: str = "priority",
        max_files: int = 50,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """Load project files into vector DB based on strategy"""
        try:
            from socratic_system.database.project_file_manager import ProjectFileManager

            file_manager = ProjectFileManager(self.orchestrator.database.db_path)

            # Load all project files
            all_files = self._load_all_project_files(file_manager, project.project_id)
            if not all_files:
                return self._empty_files_response(strategy)

            # Apply strategy and filter duplicates
            selected_files = self._apply_strategy(all_files, strategy, max_files)
            new_files = self._filter_duplicates(selected_files, project.project_id)

            if not new_files:
                return self._already_loaded_response(strategy)

            # Process files and return results
            loaded_count, total_chunks = self._process_project_files(
                new_files, project.project_id, show_progress
            )

            self.logger.info(
                f"Successfully loaded {loaded_count} files "
                f"({total_chunks} chunks) using {strategy} strategy"
            )

            return {
                "status": "success",
                "files_loaded": loaded_count,
                "total_chunks": total_chunks,
                "strategy_used": strategy,
                "total_available": len(all_files),
                "files_selected": len(selected_files),
                "files_new": len(new_files),
            }

        except Exception as e:
            self.logger.error(f"Error loading project files: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to load project files: {str(e)}",
            }

    def _load_all_project_files(
        self, file_manager: Any, project_id: str
    ) -> List[Dict]:
        """Load all project files in batches"""
        total_files = file_manager.get_file_count(project_id)
        self.logger.info(f"Loading {total_files} files for project {project_id}")

        all_files = []
        offset = 0
        batch_size = 100

        while True:
            batch = file_manager.get_project_files(
                project_id, offset=offset, limit=batch_size
            )
            if not batch:
                break
            all_files.extend(batch)
            offset += batch_size

        return all_files

    def _empty_files_response(self, strategy: str) -> Dict[str, Any]:
        """Return response when no files found"""
        return {
            "status": "success",
            "files_loaded": 0,
            "total_chunks": 0,
            "strategy_used": strategy,
            "message": "No files found to load",
        }

    def _already_loaded_response(self, strategy: str) -> Dict[str, Any]:
        """Return response when all files already loaded"""
        self.logger.info("All files already loaded in vector DB")
        return {
            "status": "success",
            "files_loaded": 0,
            "total_chunks": 0,
            "strategy_used": strategy,
            "message": "All files already loaded",
        }

    def _process_project_files(
        self,
        files: List[Dict],
        project_id: str,
        show_progress: bool,
    ) -> tuple[int, int]:
        """Process files through DocumentProcessor and return counts"""
        loaded_count = 0
        total_chunks = 0

        for idx, file_info in enumerate(files):
            if show_progress:
                self.logger.info(
                    f"Loading files... [{idx + 1}/{len(files)}] {file_info['file_path']}"
                )

            doc_processor = self.orchestrator.get_agent("document_processor")
            if not doc_processor:
                self.logger.warning("DocumentProcessor agent not available")
                break

            try:
                result = doc_processor.process(
                    {
                        "action": "process_code_file",
                        "content": file_info["content"],
                        "filename": file_info["file_path"],
                        "language": file_info.get("language", "Unknown"),
                        "project_id": project_id,
                    }
                )

                if result.get("status") == "success":
                    loaded_count += 1
                    total_chunks += result.get("chunks_created", 0)
                else:
                    self.logger.warning(
                        f"Failed to process file {file_info['file_path']}: "
                        f"{result.get('message', 'Unknown error')}"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error processing file {file_info['file_path']}: {str(e)}"
                )

        return loaded_count, total_chunks

    def _apply_strategy(
        self, files: List[Dict], strategy: str, max_files: int
    ) -> List[Dict]:
        """
        Apply loading strategy to select which files to load

        Args:
            files: All available files
            strategy: Loading strategy name
            max_files: Maximum files to select

        Returns:
            Selected files based on strategy
        """
        if strategy == "priority":
            return self._priority_strategy(files, max_files)
        elif strategy == "sample":
            return self._sample_strategy(files, max_files)
        elif strategy == "all":
            return files  # Load everything
        else:
            self.logger.warning(f"Unknown strategy {strategy}, using priority")
            return self._priority_strategy(files, max_files)

    def _priority_strategy(self, files: List[Dict], max_files: int) -> List[Dict]:
        """Priority strategy: Select most important files based on type and name"""
        ranked_files = []

        # Rank files by priority level
        ranked_files.extend(self._rank_readme_files(files, 1))
        ranked_files.extend(self._rank_main_entry_points(files, 2))
        ranked_files.extend(self._rank_source_files(files, 3))
        ranked_files.extend(self._rank_test_files(files, 4))
        ranked_files.extend(self._rank_config_files(files, 5))
        ranked_files.extend(self._rank_other_files(files, ranked_files, 6))

        # Sort by priority and return top max_files
        ranked_files.sort(key=lambda x: x[1])
        return [f for f, _ in ranked_files[:max_files]]

    def _rank_readme_files(self, files: List[Dict], priority: int) -> List[tuple]:
        """Rank README files"""
        return [(f, priority) for f in files if "readme" in f["file_path"].lower()]

    def _rank_main_entry_points(self, files: List[Dict], priority: int) -> List[tuple]:
        """Rank main entry point files"""
        main_files = {
            "main.py", "index.js", "app.py", "index.py", "app.js",
            "server.js", "index.ts", "main.go", "main.rs", "main.java",
        }
        return [
            (f, priority)
            for f in files
            if Path(f["file_path"]).name in main_files
        ]

    def _rank_source_files(self, files: List[Dict], priority: int) -> List[tuple]:
        """Rank core source files"""
        return [
            (f, priority)
            for f in files
            if any(
                x in f["file_path"]
                for x in ["/src/", "/lib/", "src/"]
            )
        ]

    def _rank_test_files(self, files: List[Dict], priority: int) -> List[tuple]:
        """Rank test files"""
        return [
            (f, priority)
            for f in files
            if any(x in f["file_path"] for x in ["/test", "test/"])
        ]

    def _rank_config_files(self, files: List[Dict], priority: int) -> List[tuple]:
        """Rank configuration files"""
        config_exts = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
        return [
            (f, priority)
            for f in files
            if Path(f["file_path"]).suffix in config_exts
        ]

    def _rank_other_files(
        self, files: List[Dict], ranked_files: List[tuple], priority: int
    ) -> List[tuple]:
        """Rank remaining files"""
        ranked_set = {f["file_path"] for f, _ in ranked_files}
        return [(f, priority) for f in files if f["file_path"] not in ranked_set]

    def _sample_strategy(self, files: List[Dict], max_files: int) -> List[Dict]:
        """
        Sample strategy: Random sampling with important files always included

        Args:
            files: All available files
            max_files: Maximum files to select

        Returns:
            Selected files (mix of important + random)
        """
        # First apply priority to get important files
        important = self._priority_strategy(files, max(10, int(max_files * 0.2)))

        # Then add random files
        important_paths = {f["file_path"] for f in important}
        other_files = [f for f in files if f["file_path"] not in important_paths]

        sample_count = max_files - len(important)
        if sample_count > 0 and other_files:
            random_selection = random.sample(
                other_files, min(sample_count, len(other_files))
            )
            return important + random_selection

        return important[:max_files]

    def _filter_duplicates(self, files: List[Dict], project_id: str) -> List[Dict]:
        """
        Filter out files that are already loaded in vector DB

        Args:
            files: Files to check
            project_id: Project ID

        Returns:
            Files not already in vector DB
        """
        new_files = []

        try:
            # Check each file against vector DB
            # This is a placeholder - actual implementation depends on vector DB API
            # For now, assume all files are new (no deduplication yet)
            # In production, query vector DB with metadata filter:
            # results = vector_db.query(
            #     query_texts=[""],
            #     where={"project_id": project_id, "source": file_path},
            #     n_results=1
            # )

            # For now, return all files as new
            new_files = files

        except Exception as e:
            self.logger.warning(f"Error filtering duplicates: {str(e)}")
            # If we can't filter, return all as new
            new_files = files

        return new_files
