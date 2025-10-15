"""
Base IDE Provider - Abstract Interface for IDE Integration
===========================================================

Provides abstract base class for all IDE providers.
Makes it easy to add support for new IDEs (JetBrains, Vim, Emacs, etc.) in the future.

Design Pattern: Strategy Pattern + Factory Pattern
- BaseIDEProvider defines the interface all IDEs must implement
- Concrete providers (VSCodeProvider, PyCharmProvider) implement specific IDE logic
- IDEProviderFactory creates appropriate provider based on user preference
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class WorkspaceConfig:
    """IDE workspace configuration (IDE-agnostic)."""
    name: str
    path: str
    folders: List[str]
    settings: Dict[str, Any]
    extensions: List[str]
    tasks: List[Dict[str, Any]]
    launch_configs: List[Dict[str, Any]]
    ide_type: str  # 'vscode', 'pycharm', 'intellij', etc.


@dataclass
class ProjectStructure:
    """Project directory structure information."""
    root_path: str
    directories: List[str]
    files: List[str]
    total_size: int
    file_count: int
    created_at: datetime


@dataclass
class FileSync:
    """File synchronization status."""
    source_path: str
    target_path: str
    status: str  # 'synced', 'pending', 'error', 'conflict'
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None


class BaseIDEProvider(ABC):
    """
    Abstract base class for IDE providers.

    All IDE providers must implement these methods to ensure consistent behavior
    across different IDEs (VS Code, PyCharm, IntelliJ, WebStorm, etc.).

    This abstraction allows the system to support multiple IDEs without changing
    agent code - agents work with the BaseIDEProvider interface, not specific IDEs.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize IDE provider.

        Args:
            config: Optional configuration dict for this IDE
        """
        self.config = config or {}
        self.ide_name = self.get_ide_name()
        self.executable_name = self.get_executable_name()

    @abstractmethod
    def get_ide_name(self) -> str:
        """
        Get human-readable IDE name.

        Returns:
            IDE name (e.g., "VS Code", "PyCharm", "IntelliJ IDEA")
        """
        pass

    @abstractmethod
    def get_executable_name(self) -> str:
        """
        Get IDE executable/command name.

        Returns:
            Executable name (e.g., "code", "pycharm", "idea")
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this IDE is installed and available.

        Returns:
            True if IDE is available, False otherwise
        """
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """
        Get IDE version if available.

        Returns:
            Version string or None if unavailable
        """
        pass

    @abstractmethod
    def create_workspace(
        self,
        project_name: str,
        project_path: str,
        technology_stack: Optional[Dict[str, Any]] = None,
        additional_folders: Optional[List[str]] = None
    ) -> WorkspaceConfig:
        """
        Create IDE workspace configuration.

        Args:
            project_name: Name of the project
            project_path: Path to the project
            technology_stack: Technology stack information
            additional_folders: Additional folders to include

        Returns:
            WorkspaceConfig object with IDE-specific configuration
        """
        pass

    @abstractmethod
    def open_project(self, path: str, new_window: bool = False) -> bool:
        """
        Open a project or file in the IDE.

        Args:
            path: Path to project or file
            new_window: Whether to open in a new window

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def sync_files(
        self,
        source_path: str,
        target_path: str,
        files: List[Dict[str, Any]],
        create_structure: bool = True
    ) -> List[FileSync]:
        """
        Synchronize files to target directory.

        Args:
            source_path: Source directory path
            target_path: Target directory path
            files: List of file information dicts
            create_structure: Whether to create directory structure

        Returns:
            List of FileSync status objects
        """
        pass

    @abstractmethod
    def create_project_structure(
        self,
        project_path: str,
        structure: Dict[str, Any]
    ) -> ProjectStructure:
        """
        Create project directory structure.

        Args:
            project_path: Root project path
            structure: Directory and file structure definition

        Returns:
            ProjectStructure object with creation details
        """
        pass

    @abstractmethod
    def generate_settings(
        self,
        technology_stack: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate IDE-specific settings based on technology stack.

        Args:
            technology_stack: Technology stack information

        Returns:
            Dict of IDE settings
        """
        pass

    @abstractmethod
    def generate_run_configurations(
        self,
        technology_stack: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate IDE-specific run/debug configurations.

        Args:
            technology_stack: Technology stack information

        Returns:
            List of run configuration dicts
        """
        pass

    @abstractmethod
    def install_extensions(self, extensions: List[str]) -> Dict[str, bool]:
        """
        Install IDE extensions/plugins.

        Args:
            extensions: List of extension IDs to install

        Returns:
            Dict mapping extension ID to installation success
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check IDE provider health and availability.

        Returns:
            Dict with health status information
        """
        pass

    # Optional methods with default implementations

    def supports_file_watching(self) -> bool:
        """
        Check if this IDE supports file watching.

        Returns:
            True if file watching is supported
        """
        return False

    def start_file_watcher(self, project_path: str) -> bool:
        """
        Start file system watcher for a project.

        Args:
            project_path: Path to watch

        Returns:
            True if watcher started successfully
        """
        return False

    def stop_file_watcher(self, project_path: str) -> bool:
        """
        Stop file system watcher for a project.

        Args:
            project_path: Path being watched

        Returns:
            True if watcher stopped successfully
        """
        return False

    def get_sync_status(self, project_path: Optional[str] = None) -> List[FileSync]:
        """
        Get file synchronization status.

        Args:
            project_path: Optional path to filter results

        Returns:
            List of FileSync objects
        """
        return []

    def cleanup(self) -> None:
        """Clean up resources (file watchers, temp files, etc.)."""
        pass


class IDEProviderError(Exception):
    """Base exception for IDE provider errors."""
    pass


__all__ = [
    'BaseIDEProvider',
    'WorkspaceConfig',
    'ProjectStructure',
    'FileSync',
    'IDEProviderError'
]
