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
        """
        Load project files into vector DB based on strategy

        Args:
            project: Project context
            strategy: Loading strategy - "priority" (top 50), "sample" (10%), "all"
            max_files: Maximum number of files to load
            show_progress: Whether to show progress messages

        Returns:
            Dict with status, files_loaded, total_chunks, strategy_used
        """
        try:
            from socratic_system.database.project_file_manager import ProjectFileManager

            file_manager = ProjectFileManager(self.orchestrator.database.db_path)

            # Get all files for the project
            total_files = file_manager.get_file_count(project.project_id)
            self.logger.info(f"Loading {total_files} files for project {project.project_id}")

            # Get files in batches
            all_files = []
            offset = 0
            batch_size = 100

            while True:
                batch = file_manager.get_project_files(
                    project.project_id, offset=offset, limit=batch_size
                )
                if not batch:
                    break
                all_files.extend(batch)
                offset += batch_size

            if not all_files:
                return {
                    "status": "success",
                    "files_loaded": 0,
                    "total_chunks": 0,
                    "strategy_used": strategy,
                    "message": "No files found to load",
                }

            # Apply loading strategy
            selected_files = self._apply_strategy(all_files, strategy, max_files)

            # Filter duplicates (check if already in vector DB)
            new_files = self._filter_duplicates(selected_files, project.project_id)

            if not new_files:
                self.logger.info("All files already loaded in vector DB")
                return {
                    "status": "success",
                    "files_loaded": 0,
                    "total_chunks": 0,
                    "strategy_used": strategy,
                    "message": "All files already loaded",
                }

            # Process files through DocumentProcessor
            loaded_count = 0
            total_chunks = 0

            for idx, file_info in enumerate(new_files):
                if show_progress:
                    self.logger.info(
                        f"Loading files... [{idx + 1}/{len(new_files)}] {file_info['file_path']}"
                    )

                try:
                    # Use orchestrator to access DocumentProcessor
                    doc_processor = self.orchestrator.get_agent("document_processor")

                    if doc_processor:
                        # Process code file
                        result = doc_processor.process(
                            {
                                "action": "process_code_file",
                                "content": file_info["content"],
                                "filename": file_info["file_path"],
                                "language": file_info.get("language", "Unknown"),
                                "project_id": project.project_id,
                            }
                        )

                        if result.get("status") == "success":
                            loaded_count += 1
                            chunks = result.get("chunks_created", 0)
                            total_chunks += chunks
                        else:
                            self.logger.warning(
                                f"Failed to process file {file_info['file_path']}: "
                                f"{result.get('message', 'Unknown error')}"
                            )
                    else:
                        self.logger.warning("DocumentProcessor agent not available")
                        break

                except Exception as e:
                    self.logger.error(
                        f"Error processing file {file_info['file_path']}: {str(e)}"
                    )
                    continue

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
        """
        Priority strategy: Select most important files based on type and name

        Ranking:
        1. README files (high priority)
        2. Main entry points (main.py, index.js, app.py, etc.)
        3. Core source files (src/, lib/)
        4. Test files (tests/, __tests__/)
        5. Configuration files
        6. Other files

        Args:
            files: All available files
            max_files: Maximum files to select

        Returns:
            Selected files ranked by priority
        """
        # Rank files by priority
        ranked_files = []

        # Priority 1: README files
        for file in files:
            if "readme" in file["file_path"].lower():
                ranked_files.append((file, 1))

        # Priority 2: Main entry points
        main_files = {
            "main.py",
            "index.js",
            "app.py",
            "index.py",
            "app.js",
            "server.js",
            "index.ts",
            "main.go",
            "main.rs",
            "main.java",
        }
        for file in files:
            filename = Path(file["file_path"]).name
            if filename in main_files:
                ranked_files.append((file, 2))

        # Priority 3: Core source files (src/, lib/)
        for file in files:
            path_str = file["file_path"]
            if "/src/" in path_str or "/lib/" in path_str or path_str.startswith("src/"):
                ranked_files.append((file, 3))

        # Priority 4: Test files
        for file in files:
            path_str = file["file_path"]
            if "/test" in path_str or path_str.startswith("test"):
                ranked_files.append((file, 4))

        # Priority 5: Config files
        config_exts = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
        for file in files:
            if Path(file["file_path"]).suffix in config_exts:
                ranked_files.append((file, 5))

        # Priority 6: Everything else
        ranked_set = {f["file_path"] for f, _ in ranked_files}
        for file in files:
            if file["file_path"] not in ranked_set:
                ranked_files.append((file, 6))

        # Sort by priority and return top max_files
        ranked_files.sort(key=lambda x: x[1])
        return [f for f, _ in ranked_files[:max_files]]

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
