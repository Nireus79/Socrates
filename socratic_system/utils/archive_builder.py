"""
Archive Builder - Creates ZIP and tarball archives of generated projects

Provides functionality to:
- Create ZIP archives of entire project directories
- Create tar.gz archives as alternative format
- Preserve directory structure
- Handle large files efficiently
- Stream output for large archives
"""

import logging
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("socrates.utils.archive_builder")


class ArchiveBuilder:
    """Build archives from project directories"""

    # Maximum archive size: 500MB
    MAX_ARCHIVE_SIZE = 500 * 1024 * 1024

    @staticmethod
    def create_zip_archive(
        project_root: Path,
        output_path: Path,
        exclude_patterns: Optional[list] = None,
    ) -> Tuple[bool, str]:
        """
        Create ZIP archive of entire project directory.

        Args:
            project_root: Path to project directory to archive
            output_path: Path where ZIP file should be created
            exclude_patterns: List of glob patterns to exclude from archive

        Returns:
            Tuple of (success: bool, message: str)
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "__pycache__",
                "*.pyc",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "*.egg-info",
                ".venv",
                "venv",
                ".env",
                ".git",
                ".coverage",
                "htmlcov",
                "dist",
                "build",
            ]

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Creating ZIP archive: {output_path}")
            logger.info(f"Archiving directory: {project_root}")

            with zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9
            ) as zipf:
                # Walk through all files in project
                for file_path in project_root.rglob("*"):
                    # Skip directories
                    if file_path.is_dir():
                        continue

                    # Get relative path for archive
                    relative_path = file_path.relative_to(project_root)
                    relative_str = str(relative_path)

                    # Check if file should be excluded
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in relative_str or relative_str.endswith(pattern):
                            should_exclude = True
                            break

                    if should_exclude:
                        logger.debug(f"Excluding: {relative_path}")
                        continue

                    # Add file to archive
                    arcname = str(relative_path)
                    zipf.write(file_path, arcname)
                    logger.debug(f"Added to archive: {arcname}")

            # Check file size
            archive_size = output_path.stat().st_size
            if archive_size > ArchiveBuilder.MAX_ARCHIVE_SIZE:
                logger.warning(
                    f"Archive size ({archive_size / 1024 / 1024:.2f}MB) exceeds "
                    f"recommended limit (500MB). Consider splitting the project."
                )

            logger.info(
                f"Successfully created ZIP archive: {output_path} "
                f"({archive_size / 1024 / 1024:.2f}MB)"
            )
            return True, str(output_path)

        except PermissionError as e:
            msg = f"Permission denied creating archive: {e}"
            logger.error(msg)
            return False, msg
        except OSError as e:
            msg = f"Disk error creating archive: {e}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            msg = f"Error creating ZIP archive: {str(e)}"
            logger.error(msg)
            return False, msg

    @staticmethod
    def create_tarball(
        project_root: Path,
        output_path: Path,
        compression: str = "gz",
        exclude_patterns: Optional[list] = None,
    ) -> Tuple[bool, str]:
        """
        Create TAR archive (optionally compressed) of project directory.

        Args:
            project_root: Path to project directory to archive
            output_path: Path where TAR file should be created
            compression: Compression format ('gz', 'bz2', 'xz', or '' for uncompressed)
            exclude_patterns: List of glob patterns to exclude from archive

        Returns:
            Tuple of (success: bool, message: str)
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "__pycache__",
                "*.pyc",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "*.egg-info",
                ".venv",
                "venv",
                ".env",
                ".git",
                ".coverage",
                "htmlcov",
                "dist",
                "build",
            ]

        try:
            # Determine compression mode
            if compression == "gz":
                mode = "w:gz"
                ext = ".tar.gz"
            elif compression == "bz2":
                mode = "w:bz2"
                ext = ".tar.bz2"
            elif compression == "xz":
                mode = "w:xz"
                ext = ".tar.xz"
            else:
                mode = "w"
                ext = ".tar"

            # Ensure output path has correct extension
            if not str(output_path).endswith(ext):
                output_path = output_path.parent / (output_path.stem + ext)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Creating TAR archive: {output_path} (compression: {compression})")

            def filter_function(tarinfo):
                """Filter function to exclude files from archive."""
                relative_path = tarinfo.name

                # Check if file should be excluded
                for pattern in exclude_patterns:
                    if pattern in relative_path or relative_path.endswith(pattern):
                        logger.debug(f"Excluding: {relative_path}")
                        return None

                return tarinfo

            with tarfile.open(output_path, mode) as tar:
                # Add project directory
                arcname = project_root.name
                tar.add(
                    project_root,
                    arcname=arcname,
                    filter=filter_function,
                    recursive=True,
                )

            # Check file size
            archive_size = output_path.stat().st_size
            if archive_size > ArchiveBuilder.MAX_ARCHIVE_SIZE:
                logger.warning(
                    f"Archive size ({archive_size / 1024 / 1024:.2f}MB) exceeds "
                    f"recommended limit (500MB). Consider splitting the project."
                )

            logger.info(
                f"Successfully created TAR archive: {output_path} "
                f"({archive_size / 1024 / 1024:.2f}MB)"
            )
            return True, str(output_path)

        except PermissionError as e:
            msg = f"Permission denied creating archive: {e}"
            logger.error(msg)
            return False, msg
        except OSError as e:
            msg = f"Disk error creating archive: {e}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            msg = f"Error creating TAR archive: {str(e)}"
            logger.error(msg)
            return False, msg

    @staticmethod
    def list_archive_contents(archive_path: Path) -> Tuple[bool, list]:
        """
        List contents of ZIP or TAR archive.

        Args:
            archive_path: Path to archive file

        Returns:
            Tuple of (success: bool, file_list: list)
        """
        try:
            files = []

            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zipf:
                    files = zipf.namelist()
            elif archive_path.suffix in [".gz", ".bz2", ".xz"] or ".tar" in str(archive_path):
                with tarfile.open(archive_path) as tar:
                    files = tar.getnames()

            logger.info(f"Archive {archive_path} contains {len(files)} files")
            return True, files

        except Exception as e:
            msg = f"Error reading archive: {str(e)}"
            logger.error(msg)
            return False, []

    @staticmethod
    def verify_archive(archive_path: Path) -> Tuple[bool, str]:
        """
        Verify integrity of ZIP or TAR archive.

        Args:
            archive_path: Path to archive file

        Returns:
            Tuple of (valid: bool, message: str)
        """
        try:
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zipf:
                    test_result = zipf.testzip()
                    if test_result is not None:
                        return False, f"Corrupt file in archive: {test_result}"
                    return True, "ZIP archive is valid"
            elif ".tar" in str(archive_path):
                with tarfile.open(archive_path) as tar:
                    # Try to read all members
                    for member in tar.getmembers():
                        pass
                    return True, "TAR archive is valid"

            return False, "Unknown archive format"

        except Exception as e:
            return False, f"Archive verification failed: {str(e)}"

    @staticmethod
    def get_archive_info(archive_path: Path) -> dict:
        """
        Get information about an archive.

        Args:
            archive_path: Path to archive file

        Returns:
            Dictionary with archive information
        """
        try:
            info = {
                "path": str(archive_path),
                "name": archive_path.name,
                "size_bytes": archive_path.stat().st_size,
                "size_mb": round(archive_path.stat().st_size / 1024 / 1024, 2),
            }

            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zipf:
                    info["format"] = "ZIP"
                    info["file_count"] = len(zipf.namelist())
                    info["compressed_size"] = sum(z.compress_size for z in zipf.filelist)
            elif ".tar" in str(archive_path):
                with tarfile.open(archive_path) as tar:
                    info["format"] = "TAR"
                    members = tar.getmembers()
                    info["file_count"] = len([m for m in members if m.isfile()])

            return info

        except Exception as e:
            logger.error(f"Error getting archive info: {str(e)}")
            return {"error": str(e)}
