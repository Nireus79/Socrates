"""
Artifact Saver - Handles saving generated code and documentation to disk

Saves generated artifacts (code, docs, plans, etc.) to organized directories
within the project's generated content folder.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("socrates.utils.artifact_saver")


class ArtifactSaver:
    """Save generated code, documentation, and other artifacts to disk"""

    # File extensions by artifact type
    EXTENSION_MAP = {
        "code": ".py",
        "documentation": ".md",
        "business_plan": ".md",
        "research_protocol": ".md",
        "creative_brief": ".md",
        "marketing_plan": ".md",
        "curriculum": ".md",
    }

    @staticmethod
    def get_generated_content_dir(project_id: str, data_dir: Path | None = None) -> Path:
        """
        Get the directory for generated content for a project.

        Args:
            project_id: ID of the project
            data_dir: Base data directory (default: ~/.socrates)

        Returns:
            Path to generated content directory
        """
        if data_dir is None:
            data_dir = Path.home() / ".socrates"

        generated_dir = data_dir / "generated" / project_id
        return generated_dir

    @staticmethod
    def save_multi_file_project(
        file_structure: dict,
        project_id: str,
        project_name: str,
        data_dir: Path | None = None,
    ) -> tuple[bool, str]:
        """
        Save a multi-file project structure to disk.

        Args:
            file_structure: Dictionary with file paths and contents
            project_id: ID of the project
            project_name: Name of the project
            data_dir: Base data directory (default: ~/.socrates)

        Returns:
            Tuple of (success: bool, project_root_path: str)
        """
        if not file_structure:
            logger.warning("File structure is empty, skipping save")
            return False, ""

        try:
            # Create project root directory
            if data_dir is None:
                data_dir = Path.home() / ".socrates"

            clean_name = project_name.replace(" ", "_").replace("/", "_").lower()[:30]
            project_root = data_dir / "generated" / project_id / clean_name
            project_root.mkdir(parents=True, exist_ok=True)

            # Create all files in the structure
            for file_path, content in file_structure.items():
                full_path = project_root / file_path

                # Create parent directories
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.debug(f"Created file: {full_path}")

            logger.info(f"Saved multi-file project to {project_root}")
            return True, str(project_root)

        except Exception as e:
            logger.error(f"Error saving multi-file project: {e}")
            return False, ""

    @staticmethod
    def save_artifact(
        artifact: str,
        artifact_type: str,
        project_id: str,
        project_name: str,
        data_dir: Path | None = None,
        timestamp: bool = True,
    ) -> tuple[bool, str]:
        """
        Save a generated artifact to disk.

        Args:
            artifact: Content to save
            artifact_type: Type of artifact (code, documentation, business_plan, etc.)
            project_id: ID of the project
            project_name: Name of the project (used in filename)
            data_dir: Base data directory (default: ~/.socrates)
            timestamp: Whether to add timestamp to filename

        Returns:
            Tuple of (success: bool, file_path: str)
        """
        if not artifact or not artifact.strip():
            logger.warning("Artifact is empty, skipping save")
            return False, ""

        try:
            # Get save directory
            save_dir = ArtifactSaver.get_generated_content_dir(project_id, data_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            # Validate content if it's supposed to be code
            actual_artifact_type = artifact_type
            if artifact_type == "code":
                from socratic_system.utils.code_extractor import CodeExtractor
                extractor = CodeExtractor()

                # Check if markdown format slipped through
                if extractor.is_markdown_format(artifact):
                    logger.warning(
                        "Detected markdown format in code artifact. "
                        "Code extraction did not trigger or failed. "
                        "Saving as documentation instead of code."
                    )
                    actual_artifact_type = "documentation"

                    # Try to extract anyway for better content
                    extracted = extractor.extract_from_markdown(artifact)
                    is_valid, error = extractor.validate_python_syntax(extracted)

                    if is_valid:
                        logger.info("Extracted code is valid, saving extracted version")
                        artifact = extracted
                        actual_artifact_type = "code"  # Override back to code
                    else:
                        logger.warning(f"Extracted code invalid: {error}, saving as markdown")
                        actual_artifact_type = "documentation"

            # Determine file extension
            extension = ArtifactSaver.EXTENSION_MAP.get(actual_artifact_type, ".txt")

            # Create filename
            clean_name = project_name.replace(" ", "_").replace("/", "_").lower()[:30]

            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{clean_name}_{artifact_type}_{timestamp_str}{extension}"
            else:
                filename = f"{clean_name}_{artifact_type}{extension}"

            file_path = save_dir / filename

            # Save file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(artifact)

            # Verify file was created
            if not file_path.exists():
                logger.error(f"File was written but does not exist: {file_path}")
                return False, ""

            logger.info(f"Saved {artifact_type} to {file_path}")
            return True, str(file_path)

        except PermissionError as e:
            logger.error(f"Permission denied saving artifact to {save_dir}: {e}")
            return False, ""
        except OSError as e:
            logger.error(f"OS error saving artifact to {save_dir}: {e}")
            return False, ""
        except Exception as e:
            logger.error(f"Error saving artifact: {e}")
            return False, ""

    @staticmethod
    def list_generated_artifacts(project_id: str, data_dir: Path | None = None) -> dict:
        """
        List all generated artifacts for a project.

        Args:
            project_id: ID of the project
            data_dir: Base data directory (default: ~/.socrates)

        Returns:
            Dictionary with artifact types as keys and list of file paths as values
        """
        save_dir = ArtifactSaver.get_generated_content_dir(project_id, data_dir)

        artifacts: dict[str, list[str]] = {}
        if not save_dir.exists():
            return artifacts

        try:
            for file_path in sorted(save_dir.iterdir()):
                if file_path.is_file():
                    # Extract artifact type from filename
                    # Format: {clean_name}_{artifact_type}_{timestamp}.{ext}
                    # or: {clean_name}_{artifact_type}.{ext}
                    stem = file_path.stem
                    parts = stem.split("_")

                    # Try to extract artifact type
                    # Last part before extension is timestamp (if it exists and is numeric)
                    artifact_type = "other"
                    if len(parts) >= 2:
                        # Check if last part is timestamp (YYYYMMDD_HHMMSS format)
                        last_part = parts[-1]
                        if last_part.isdigit() and len(last_part) == 15:
                            # This is a timestamp, so artifact type is second-to-last
                            artifact_type = parts[-2]
                        else:
                            # No timestamp, artifact type is last part
                            artifact_type = parts[-1]

                    if artifact_type not in artifacts:
                        artifacts[artifact_type] = []

                    artifacts[artifact_type].append(str(file_path))
        except Exception as e:
            logger.warning(f"Error listing artifacts: {e}")

        return artifacts

    @staticmethod
    def get_save_location_message(file_path: str) -> str:
        """
        Get a formatted message showing where file was saved.

        Args:
            file_path: Path to saved file

        Returns:
            Formatted message
        """
        from colorama import Fore, Style

        # Show relative path if possible
        try:
            rel_path = Path(file_path).relative_to(Path.home())
            # Use forward slashes for display (more readable)
            display_path = f"~/{rel_path.as_posix()}"
        except ValueError:
            display_path = file_path

        return f"\n{Fore.GREEN}Saved to:{Style.RESET_ALL} {Fore.YELLOW}{display_path}{Style.RESET_ALL}\n"

    @staticmethod
    def get_project_structure_tree(project_path: str) -> str:
        """
        Get a tree representation of project structure.

        Args:
            project_path: Path to project root

        Returns:
            Tree-formatted string of project structure
        """
        from colorama import Fore, Style

        project_root = Path(project_path)
        if not project_root.exists():
            return "Project directory not found"

        lines = []
        lines.append(f"{Fore.CYAN}{project_root.name}/{Style.RESET_ALL}")

        def add_tree(path: Path, prefix: str = "", is_last: bool = True):
            """Recursively add directory tree"""
            if path.is_file():
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{Fore.WHITE}{connector}{path.name}{Style.RESET_ALL}")
            elif path.is_dir():
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{Fore.GREEN}{connector}{path.name}/{Style.RESET_ALL}")

                # Get subdirectories and files
                try:
                    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                    for i, item in enumerate(items):
                        is_last_item = i == len(items) - 1
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        add_tree(item, next_prefix, is_last_item)
                except PermissionError:
                    pass

        # Start tree from first level
        try:
            items = sorted(project_root.iterdir(), key=lambda x: (x.is_file(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                add_tree(item, "", is_last)
        except Exception as e:
            logger.warning(f"Error generating tree: {e}")

        return "\n".join(lines)

    @staticmethod
    def list_project_files(project_path: str) -> list[str]:
        """
        List all files in a project.

        Args:
            project_path: Path to project root

        Returns:
            List of file paths relative to project root
        """
        project_root = Path(project_path)
        files = []

        try:
            for file_path in project_root.rglob("*"):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(project_root)))
        except Exception as e:
            logger.warning(f"Error listing files: {e}")

        return sorted(files)
