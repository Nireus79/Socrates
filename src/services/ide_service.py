"""
IDE Service - VS Code Integration and File Synchronization
=========================================================

Provides IDE integration for the Socratic RAG Enhanced system.
Handles VS Code workspace management, file synchronization, project setup, and development environment configuration.

Features:
- VS Code workspace creation and management
- File synchronization and project structure setup
- Development environment configuration
- Extension recommendations and settings
- Live file watching and updates
- Debug configuration generation
- Task runner setup
"""

import logging
import os
import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import threading
import time

try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from .. import get_config
from ..core import SocraticException

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceConfig:
    """VS Code workspace configuration."""
    name: str
    path: str
    folders: List[str]
    settings: Dict[str, Any]
    extensions: List[str]
    tasks: List[Dict[str, Any]]
    launch_configs: List[Dict[str, Any]]


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


class IDEServiceError(SocraticException):
    """IDE service specific exceptions."""
    pass


class ProjectFileWatcher(FileSystemEventHandler):
    """File system event handler for project file watching."""

    def __init__(self, ide_service, project_path: str):
        super().__init__()
        self.ide_service = ide_service
        self.project_path = project_path
        self.last_event_time = {}
        self.debounce_delay = 1.0  # seconds

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path
        current_time = time.time()

        # Debounce rapid file changes
        if file_path in self.last_event_time:
            if current_time - self.last_event_time[file_path] < self.debounce_delay:
                return

        self.last_event_time[file_path] = current_time

        logger.debug(f"File modified: {file_path}")
        # Notify IDE service of file change
        if hasattr(self.ide_service, '_handle_file_change'):
            self.ide_service._handle_file_change(file_path, 'modified')

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        logger.debug(f"File created: {event.src_path}")
        if hasattr(self.ide_service, '_handle_file_change'):
            self.ide_service._handle_file_change(event.src_path, 'created')

    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return

        logger.debug(f"File deleted: {event.src_path}")
        if hasattr(self.ide_service, '_handle_file_change'):
            self.ide_service._handle_file_change(event.src_path, 'deleted')


class IDEService:
    """
    VS Code integration and file synchronization service.

    Provides methods for:
    - VS Code workspace creation and management
    - File synchronization and project setup
    - Development environment configuration
    - Extension recommendations and settings
    - Project structure management
    - File watching and live updates
    """

    def __init__(self):
        self.config = get_config()
        self.ide_config = self.config.get('services', {}).get('ide', {})

        # Configuration
        self.vscode_path = self.ide_config.get('vscode_path', 'code')
        self.workspace_template = self.ide_config.get('workspace_template', {})
        self.default_extensions = self.ide_config.get('default_extensions', [
            'ms-python.python',
            'ms-python.vscode-pylance',
            'ms-python.black-formatter',
            'ms-vscode.vscode-json',
            'redhat.vscode-yaml',
            'bradlc.vscode-tailwindcss',
            'esbenp.prettier-vscode',
            'ms-vscode.vscode-typescript-next'
        ])
        self.auto_sync = self.ide_config.get('auto_sync', True)
        self.enable_file_watching = self.ide_config.get('enable_file_watching', True)

        # File watchers
        self.observers = {}
        self.file_sync_status = {}

        logger.info("IDE service initialized")

    def _check_vscode_available(self) -> bool:
        """Check if VS Code is available."""
        try:
            result = subprocess.run(
                [self.vscode_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_vscode_version(self) -> Optional[str]:
        """Get VS Code version if available."""
        try:
            result = subprocess.run(
                [self.vscode_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        return None

    def create_workspace(
            self,
            project_name: str,
            project_path: str,
            technology_stack: Optional[Dict[str, Any]] = None,
            additional_folders: Optional[List[str]] = None
    ) -> WorkspaceConfig:
        """
        Create a VS Code workspace configuration.

        Args:
            project_name: Name of the project
            project_path: Path to the project
            technology_stack: Technology stack information
            additional_folders: Additional folders to include in workspace

        Returns:
            WorkspaceConfig object
        """
        try:
            project_path = Path(project_path).resolve()
            workspace_path = project_path / f"{project_name}.code-workspace"

            # Base folders
            folders = [{"path": "."}]
            if additional_folders:
                folders.extend([{"path": folder} for folder in additional_folders])

            # Generate settings based on technology stack
            settings = self._generate_workspace_settings(technology_stack)

            # Generate extensions based on technology stack
            extensions = self._generate_extension_recommendations(technology_stack)

            # Generate tasks
            tasks = self._generate_tasks(technology_stack)

            # Generate launch configurations
            launch_configs = self._generate_launch_configs(technology_stack)

            # Create workspace configuration
            workspace_config = {
                "folders": folders,
                "settings": settings,
                "extensions": {
                    "recommendations": extensions
                },
                "tasks": {
                    "version": "2.0.0",
                    "tasks": tasks
                },
                "launch": {
                    "version": "0.2.0",
                    "configurations": launch_configs
                }
            }

            # Write workspace file
            workspace_path.write_text(json.dumps(workspace_config, indent=2))

            config = WorkspaceConfig(
                name=project_name,
                path=str(workspace_path),
                folders=[str(project_path)],
                settings=settings,
                extensions=extensions,
                tasks=tasks,
                launch_configs=launch_configs
            )

            logger.info(f"Created VS Code workspace: {workspace_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            raise IDEServiceError(f"Workspace creation failed: {e}")

    def _generate_workspace_settings(self, technology_stack: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate VS Code settings based on technology stack."""
        settings = {
            "files.exclude": {
                "**/.git": True,
                "**/.DS_Store": True,
                "**/node_modules": True,
                "**/__pycache__": True,
                "**/*.pyc": True,
                "**/.pytest_cache": True,
                "**/venv": True,
                "**/env": True
            },
            "editor.tabSize": 4,
            "editor.insertSpaces": True,
            "editor.formatOnSave": True,
            "editor.rulers": [80, 120],
            "files.trimTrailingWhitespace": True,
            "files.insertFinalNewline": True
        }

        if not technology_stack:
            return settings

        # Python specific settings
        if any(key.lower() in ['python', 'flask', 'django', 'fastapi'] for key in technology_stack.keys()):
            settings.update({
                "python.defaultInterpreterPath": "./venv/bin/python",
                "python.linting.enabled": True,
                "python.linting.pylintEnabled": True,
                "python.formatting.provider": "black",
                "python.linting.flake8Enabled": True,
                "python.testing.pytestEnabled": True,
                "python.testing.unittestEnabled": False,
                "[python]": {
                    "editor.tabSize": 4,
                    "editor.formatOnSave": True
                }
            })

        # JavaScript/TypeScript specific settings
        if any(key.lower() in ['javascript', 'typescript', 'node', 'react', 'vue', 'angular'] for key in
               technology_stack.keys()):
            settings.update({
                "typescript.preferences.importModuleSpecifier": "relative",
                "javascript.preferences.importModuleSpecifier": "relative",
                "[javascript]": {
                    "editor.tabSize": 2,
                    "editor.formatOnSave": True
                },
                "[typescript]": {
                    "editor.tabSize": 2,
                    "editor.formatOnSave": True
                },
                "[json]": {
                    "editor.tabSize": 2
                }
            })

        # Web development settings
        if any(key.lower() in ['html', 'css', 'scss', 'react', 'vue'] for key in technology_stack.keys()):
            settings.update({
                "emmet.includeLanguages": {
                    "javascript": "javascriptreact",
                    "typescript": "typescriptreact"
                },
                "[html]": {
                    "editor.tabSize": 2
                },
                "[css]": {
                    "editor.tabSize": 2
                },
                "[scss]": {
                    "editor.tabSize": 2
                }
            })

        return settings

    def _generate_extension_recommendations(self, technology_stack: Optional[Dict[str, Any]]) -> List[str]:
        """Generate extension recommendations based on technology stack."""
        extensions = self.default_extensions.copy()

        if not technology_stack:
            return extensions

        # Python extensions
        if any(key.lower() in ['python', 'flask', 'django', 'fastapi'] for key in technology_stack.keys()):
            extensions.extend([
                'ms-python.python',
                'ms-python.vscode-pylance',
                'ms-python.black-formatter',
                'ms-python.flake8',
                'kevinrose.vsc-python-indent'
            ])

        # JavaScript/TypeScript extensions
        if any(key.lower() in ['javascript', 'typescript', 'node'] for key in technology_stack.keys()):
            extensions.extend([
                'ms-vscode.vscode-typescript-next',
                'esbenp.prettier-vscode',
                'dbaeumer.vscode-eslint'
            ])

        # React extensions
        if 'react' in str(technology_stack).lower():
            extensions.extend([
                'es7-react-js-snippets',
                'ms-vscode.vscode-typescript-next'
            ])

        # Vue extensions
        if 'vue' in str(technology_stack).lower():
            extensions.extend([
                'johnsoncodehk.volar',
                'vue.vscode-typescript-vue-plugin'
            ])

        # Database extensions
        if any(key.lower() in ['postgresql', 'mysql', 'sqlite', 'mongodb'] for key in technology_stack.keys()):
            extensions.extend([
                'ms-mssql.mssql',
                'mtxr.sqltools'
            ])

        # Docker extensions
        if 'docker' in str(technology_stack).lower():
            extensions.extend([
                'ms-azuretools.vscode-docker'
            ])

        # Remove duplicates and return
        return list(set(extensions))

    def _generate_tasks(self, technology_stack: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate VS Code tasks based on technology stack."""
        tasks = []

        if not technology_stack:
            return tasks

        # Python tasks
        if any(key.lower() in ['python', 'flask', 'django', 'fastapi'] for key in technology_stack.keys()):
            tasks.extend([
                {
                    "label": "Python: Install Dependencies",
                    "type": "shell",
                    "command": "pip install -r requirements.txt",
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared"
                    }
                },
                {
                    "label": "Python: Run Tests",
                    "type": "shell",
                    "command": "python -m pytest",
                    "group": "test",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared"
                    }
                },
                {
                    "label": "Python: Format Code",
                    "type": "shell",
                    "command": "black .",
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "silent",
                        "focus": False,
                        "panel": "shared"
                    }
                }
            ])

        # Flask specific tasks
        if 'flask' in str(technology_stack).lower():
            tasks.append({
                "label": "Flask: Run Development Server",
                "type": "shell",
                "command": "python -m flask run --debug",
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared"
                }
            })

        # JavaScript/Node tasks
        if any(key.lower() in ['javascript', 'typescript', 'node', 'react', 'vue'] for key in technology_stack.keys()):
            tasks.extend([
                {
                    "label": "NPM: Install Dependencies",
                    "type": "shell",
                    "command": "npm install",
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared"
                    }
                },
                {
                    "label": "NPM: Run Development Server",
                    "type": "shell",
                    "command": "npm run dev",
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared"
                    }
                },
                {
                    "label": "NPM: Run Tests",
                    "type": "shell",
                    "command": "npm test",
                    "group": "test",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared"
                    }
                }
            ])

        return tasks

    def _generate_launch_configs(self, technology_stack: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate VS Code launch configurations based on technology stack."""
        configs = []

        if not technology_stack:
            return configs

        # Python debug configurations
        if any(key.lower() in ['python', 'flask', 'django', 'fastapi'] for key in technology_stack.keys()):
            configs.extend([
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "justMyCode": True
                },
                {
                    "name": "Python: Module",
                    "type": "python",
                    "request": "launch",
                    "module": "pytest",
                    "args": ["-v"],
                    "console": "integratedTerminal",
                    "justMyCode": True
                }
            ])

        # Flask debug configuration
        if 'flask' in str(technology_stack).lower():
            configs.append({
                "name": "Python: Flask",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/app.py",
                "env": {
                    "FLASK_APP": "app.py",
                    "FLASK_ENV": "development"
                },
                "args": [
                    "run",
                    "--no-debugger"
                ],
                "jinja": True,
                "console": "integratedTerminal"
            })

        # Node.js debug configurations
        if any(key.lower() in ['javascript', 'node'] for key in technology_stack.keys()):
            configs.extend([
                {
                    "name": "Node: Launch Program",
                    "type": "node",
                    "request": "launch",
                    "program": "${workspaceFolder}/index.js",
                    "console": "integratedTerminal"
                },
                {
                    "name": "Node: Attach to Process",
                    "type": "node",
                    "request": "attach",
                    "port": 9229
                }
            ])

        return configs

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
        try:
            source_path = Path(source_path)
            target_path = Path(target_path)

            # Create target directory if needed
            target_path.mkdir(parents=True, exist_ok=True)

            sync_results = []

            for file_info in files:
                file_path = file_info.get('path', '')
                content = file_info.get('content', '')

                if not file_path:
                    continue

                source_file = source_path / file_path
                target_file = target_path / file_path

                try:
                    # Create directory structure
                    if create_structure:
                        target_file.parent.mkdir(parents=True, exist_ok=True)

                    # Write file content
                    if isinstance(content, str):
                        target_file.write_text(content, encoding='utf-8')
                    else:
                        # Handle binary content
                        if isinstance(content, bytes):
                            target_file.write_bytes(content)
                        else:
                            # Fallback: encode if somehow still a string
                            target_file.write_bytes(content.encode('utf-8'))

                    sync_result = FileSync(
                        source_path=str(source_file),
                        target_path=str(target_file),
                        status='synced',
                        last_sync=datetime.now()
                    )

                    # Update sync status
                    self.file_sync_status[str(target_file)] = sync_result

                    sync_results.append(sync_result)
                    logger.debug(f"Synced file: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to sync file {file_path}: {e}")
                    sync_result = FileSync(
                        source_path=str(source_file),
                        target_path=str(target_file),
                        status='error',
                        error_message=str(e)
                    )
                    sync_results.append(sync_result)

            logger.info(
                f"File sync completed: {len([s for s in sync_results if s.status == 'synced'])}/{len(sync_results)} successful")
            return sync_results

        except Exception as e:
            logger.error(f"File synchronization failed: {e}")
            raise IDEServiceError(f"File sync failed: {e}")

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
        try:
            project_path = Path(project_path).resolve()
            project_path.mkdir(parents=True, exist_ok=True)

            created_dirs = []
            created_files = []
            total_size = 0

            # Create directories
            directories = structure.get('directories', [])
            for dir_path in directories:
                full_dir = project_path / dir_path
                full_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_dir))
                logger.debug(f"Created directory: {dir_path}")

            # Create files
            files = structure.get('files', {})
            for file_path, content in files.items():
                full_file = project_path / file_path
                full_file.parent.mkdir(parents=True, exist_ok=True)

                if isinstance(content, str):
                    full_file.write_text(content, encoding='utf-8')
                    file_size = len(content.encode('utf-8'))
                else:
                    full_file.write_bytes(content)
                    file_size = len(content)

                created_files.append(str(full_file))
                total_size += file_size
                logger.debug(f"Created file: {file_path} ({file_size} bytes)")

            project_structure = ProjectStructure(
                root_path=str(project_path),
                directories=created_dirs,
                files=created_files,
                total_size=total_size,
                file_count=len(created_files),
                created_at=datetime.now()
            )

            logger.info(
                f"Created project structure: {len(created_dirs)} dirs, {len(created_files)} files, {total_size} bytes")
            return project_structure

        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            raise IDEServiceError(f"Project structure creation failed: {e}")

    def open_in_vscode(self, path: str, new_window: bool = False) -> bool:
        """
        Open a project or file in VS Code.

        Args:
            path: Path to project or file
            new_window: Whether to open in a new window

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._check_vscode_available():
                logger.error("VS Code not available")
                return False

            cmd = [self.vscode_path]
            if new_window:
                cmd.append('--new-window')
            cmd.append(str(path))

            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0:
                logger.info(f"Opened in VS Code: {path}")
                return True
            else:
                logger.error(f"Failed to open in VS Code: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Failed to open in VS Code: {e}")
            return False

    def start_file_watcher(self, project_path: str) -> bool:
        """
        Start file system watcher for a project.

        Args:
            project_path: Path to watch

        Returns:
            True if watcher started successfully, False otherwise
        """
        if not WATCHDOG_AVAILABLE or not self.enable_file_watching:
            logger.warning("File watching not available or disabled")
            return False

        try:
            project_path = str(Path(project_path).resolve())

            # Stop existing watcher if any
            self.stop_file_watcher(project_path)

            # Create and start new watcher
            event_handler = ProjectFileWatcher(self, project_path)
            observer = Observer()
            observer.schedule(event_handler, project_path, recursive=True)
            observer.start()

            self.observers[project_path] = observer
            logger.info(f"Started file watcher for: {project_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            return False

    def stop_file_watcher(self, project_path: str) -> bool:
        """
        Stop file system watcher for a project.

        Args:
            project_path: Path being watched

        Returns:
            True if watcher stopped successfully, False otherwise
        """
        try:
            project_path = str(Path(project_path).resolve())

            if project_path in self.observers:
                observer = self.observers[project_path]
                observer.stop()
                observer.join()
                del self.observers[project_path]
                logger.info(f"Stopped file watcher for: {project_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to stop file watcher: {e}")
            return False

    def _handle_file_change(self, file_path: str, change_type: str) -> None:
        """Handle file system change events."""
        logger.debug(f"File {change_type}: {file_path}")

        # Update sync status if file is tracked
        if file_path in self.file_sync_status:
            sync_info = self.file_sync_status[file_path]
            sync_info.status = 'pending'
            sync_info.last_sync = None

    def get_sync_status(self, project_path: Optional[str] = None) -> List[FileSync]:
        """
        Get file synchronization status.

        Args:
            project_path: Optional path to filter results

        Returns:
            List of FileSync objects
        """
        if project_path:
            project_path = str(Path(project_path).resolve())
            return [
                sync for file_path, sync in self.file_sync_status.items()
                if file_path.startswith(project_path)
            ]

        return list(self.file_sync_status.values())

    def install_extensions(self, extensions: List[str]) -> Dict[str, bool]:
        """
        Install VS Code extensions.

        Args:
            extensions: List of extension IDs to install

        Returns:
            Dict mapping extension ID to installation success
        """
        results = {}

        if not self._check_vscode_available():
            logger.error("VS Code not available for extension installation")
            return {ext: False for ext in extensions}

        for extension in extensions:
            try:
                result = subprocess.run(
                    [self.vscode_path, '--install-extension', extension],
                    capture_output=True,
                    timeout=60
                )

                success = result.returncode == 0
                results[extension] = success

                if success:
                    logger.info(f"Installed VS Code extension: {extension}")
                else:
                    logger.error(f"Failed to install extension {extension}: {result.stderr.decode()}")

            except Exception as e:
                logger.error(f"Error installing extension {extension}: {e}")
                results[extension] = False

        return results

    def cleanup_watchers(self) -> None:
        """Clean up all file watchers."""
        for project_path in list(self.observers.keys()):
            self.stop_file_watcher(project_path)
        logger.info("Cleaned up all file watchers")

    def health_check(self) -> Dict[str, Any]:
        """Check IDE service health and VS Code availability."""
        try:
            vscode_available = self._check_vscode_available()
            vscode_version = self._get_vscode_version() if vscode_available else None

            return {
                "status": "healthy" if vscode_available else "limited",
                "vscode_available": vscode_available,
                "vscode_version": vscode_version,
                "vscode_path": self.vscode_path,
                "watchdog_available": WATCHDOG_AVAILABLE,
                "file_watching_enabled": self.enable_file_watching,
                "auto_sync_enabled": self.auto_sync,
                "active_watchers": len(self.observers),
                "tracked_files": len(self.file_sync_status),
                "default_extensions_count": len(self.default_extensions),
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"IDE service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "vscode_available": False,
                "watchdog_available": WATCHDOG_AVAILABLE,
                "last_check": datetime.now().isoformat()
            }
        