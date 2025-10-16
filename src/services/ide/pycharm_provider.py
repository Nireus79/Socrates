"""
PyCharm Provider - JetBrains PyCharm IDE Integration
=====================================================

Provides PyCharm/IntelliJ IDEA integration for Python projects.
Handles .idea/ folder structure, run configurations, and PyCharm-specific settings.

Features:
- .idea/ project structure generation
- Python interpreter configuration
- Run/Debug configurations
- Code style settings
- Inspection profiles
- Project libraries and dependencies
"""

import logging
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .base_provider import (
    BaseIDEProvider,
    WorkspaceConfig,
    ProjectStructure,
    FileSync,
    IDEProviderError
)

logger = logging.getLogger(__name__)


class PyCharmProvider(BaseIDEProvider):
    """
    PyCharm IDE integration provider.

    Supports both PyCharm Community and Professional editions.
    Compatible with other JetBrains Python IDEs (IntelliJ IDEA with Python plugin).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PyCharm provider.

        Args:
            config: Optional configuration dict
        """
        # Set pycharm_path BEFORE calling super().__init__()
        # because super().__init__() calls get_executable_name()
        self.pycharm_path = (config or {}).get('pycharm_path', 'pycharm')
        self.enable_inspections = (config or {}).get('enable_inspections', True)
        self.enable_code_style = (config or {}).get('enable_code_style', True)
        self.file_sync_status = {}

        # Now safe to call super().__init__()
        super().__init__(config)

        logger.info("PyCharm provider initialized")

    def get_ide_name(self) -> str:
        """Get IDE name."""
        return "PyCharm"

    def get_executable_name(self) -> str:
        """Get executable name."""
        return self.pycharm_path

    def is_available(self) -> bool:
        """
        Check if PyCharm is installed and available.

        Returns:
            True if PyCharm is available
        """
        try:
            # Try to run pycharm with --version
            result = subprocess.run(
                [self.pycharm_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Check common installation paths
            common_paths = [
                'pycharm',
                'pycharm64',
                '/usr/bin/pycharm',
                '/usr/local/bin/pycharm',
                'C:\\Program Files\\JetBrains\\PyCharm\\bin\\pycharm64.exe',
                'C:\\Program Files (x86)\\JetBrains\\PyCharm\\bin\\pycharm.exe',
            ]

            for path in common_paths:
                try:
                    result = subprocess.run(
                        [path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.pycharm_path = path
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            return False

    def get_version(self) -> Optional[str]:
        """
        Get PyCharm version.

        Returns:
            Version string or None
        """
        try:
            result = subprocess.run(
                [self.pycharm_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse version from output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'PyCharm' in line:
                        return line.strip()
                return lines[0] if lines else None
        except Exception as e:
            logger.debug(f"Failed to get PyCharm version: {e}")
        return None

    def create_workspace(
        self,
        project_name: str,
        project_path: str,
        technology_stack: Optional[Dict[str, Any]] = None,
        additional_folders: Optional[List[str]] = None
    ) -> WorkspaceConfig:
        """
        Create PyCharm workspace (.idea/ folder structure).

        Args:
            project_name: Project name
            project_path: Path to project root
            technology_stack: Technology stack information
            additional_folders: Additional source folders

        Returns:
            WorkspaceConfig with PyCharm configuration
        """
        try:
            project_path = Path(project_path).resolve()
            idea_path = project_path / '.idea'
            idea_path.mkdir(parents=True, exist_ok=True)

            # Generate all configuration files
            self._create_misc_xml(idea_path, technology_stack)
            self._create_modules_xml(idea_path, project_name)
            self._create_iml_file(project_path, project_name, additional_folders)
            self._create_workspace_xml(idea_path)

            if self.enable_inspections:
                self._create_inspectionProfiles_xml(idea_path)

            if self.enable_code_style:
                self._create_codeStyleSettings_xml(idea_path)

            # Generate settings
            settings = self.generate_settings(technology_stack)

            # Generate run configurations
            run_configs = self.generate_run_configurations(technology_stack)
            self._create_run_configurations(idea_path, run_configs, project_name)

            config = WorkspaceConfig(
                name=project_name,
                path=str(idea_path),
                folders=[str(project_path)],
                settings=settings,
                extensions=[],  # PyCharm uses plugins, not extensions
                tasks=[],  # PyCharm uses run configurations instead
                launch_configs=run_configs,
                ide_type='pycharm'
            )

            logger.info(f"Created PyCharm workspace: {idea_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to create PyCharm workspace: {e}")
            raise IDEProviderError(f"Workspace creation failed: {e}")

    def _create_misc_xml(
        self,
        idea_path: Path,
        technology_stack: Optional[Dict[str, Any]]
    ) -> None:
        """Create .idea/misc.xml with Python interpreter settings."""
        root = ET.Element('project', version='4')

        # Python interpreter configuration
        component = ET.SubElement(root, 'component', name='ProjectRootManager')
        component.set('version', '2')
        component.set('project-jdk-name', 'Python 3.12')
        component.set('project-jdk-type', 'Python SDK')

        # Write XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(idea_path / 'misc.xml', encoding='UTF-8', xml_declaration=True)

    def _create_modules_xml(self, idea_path: Path, project_name: str) -> None:
        """Create .idea/modules.xml."""
        root = ET.Element('project', version='4')
        component = ET.SubElement(root, 'component', name='ProjectModuleManager')
        modules = ET.SubElement(component, 'modules')

        module = ET.SubElement(modules, 'module')
        module.set('fileurl', f'file://$PROJECT_DIR$/{project_name}.iml')
        module.set('filepath', f'$PROJECT_DIR$/{project_name}.iml')

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(idea_path / 'modules.xml', encoding='UTF-8', xml_declaration=True)

    def _create_iml_file(
        self,
        project_path: Path,
        project_name: str,
        additional_folders: Optional[List[str]]
    ) -> None:
        """Create .iml module file."""
        root = ET.Element('module', type='PYTHON_MODULE', version='4')

        # New module root manager
        manager = ET.SubElement(root, 'component', name='NewModuleRootManager')

        # Content root
        content = ET.SubElement(manager, 'content', url='file://$MODULE_DIR$')

        # Add source folders
        source_folders = ['src'] + (additional_folders or [])
        for folder in source_folders:
            folder_path = project_path / folder
            if folder_path.exists():
                ET.SubElement(content, 'sourceFolder')
                content[-1].set('url', f'file://$MODULE_DIR$/{folder}')
                content[-1].set('isTestSource', 'false')

        # Add test folders
        test_folders = ['tests', 'test']
        for folder in test_folders:
            folder_path = project_path / folder
            if folder_path.exists():
                ET.SubElement(content, 'sourceFolder')
                content[-1].set('url', f'file://$MODULE_DIR$/{folder}')
                content[-1].set('isTestSource', 'true')

        # Exclude folders
        exclude_folders = [
            'venv', 'env', '.venv', '__pycache__',
            'node_modules', '.git', '.pytest_cache', '.mypy_cache',
            'build', 'dist', '*.egg-info'
        ]
        for folder in exclude_folders:
            ET.SubElement(content, 'excludeFolder', url=f'file://$MODULE_DIR$/{folder}')

        # Order entries
        ET.SubElement(manager, 'orderEntry', type='inheritedJdk')
        ET.SubElement(manager, 'orderEntry', type='sourceFolder', forTests='false')

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(
            project_path / f'{project_name}.iml',
            encoding='UTF-8',
            xml_declaration=True
        )

    def _create_workspace_xml(self, idea_path: Path) -> None:
        """Create .idea/workspace.xml."""
        root = ET.Element('project', version='4')

        # Run manager component
        ET.SubElement(root, 'component', name='RunManager')

        # Project view component
        ET.SubElement(root, 'component', name='PropertiesComponent')

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(idea_path / 'workspace.xml', encoding='UTF-8', xml_declaration=True)

    def _create_inspectionProfiles_xml(self, idea_path: Path) -> None:
        """Create inspection profiles for code quality."""
        profiles_path = idea_path / 'inspectionProfiles'
        profiles_path.mkdir(exist_ok=True)

        root = ET.Element('component', name='InspectionProjectProfileManager')
        profile = ET.SubElement(root, 'profile', version='1.0')
        ET.SubElement(profile, 'option', name='myName', value='Project Default')

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(
            profiles_path / 'Project_Default.xml',
            encoding='UTF-8',
            xml_declaration=True
        )

    def _create_codeStyleSettings_xml(self, idea_path: Path) -> None:
        """Create code style settings."""
        codestyles_path = idea_path / 'codeStyles'
        codestyles_path.mkdir(exist_ok=True)

        root = ET.Element('component', name='ProjectCodeStyleConfiguration')
        code_scheme = ET.SubElement(root, 'code_scheme', name='Project', version='173')

        # Python code style
        python_style = ET.SubElement(code_scheme, 'Python')
        ET.SubElement(python_style, 'option', name='USE_CONTINUATION_INDENT_FOR_ARGUMENTS', value='true')

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(
            codestyles_path / 'Project.xml',
            encoding='UTF-8',
            xml_declaration=True
        )

    def _create_run_configurations(
        self,
        idea_path: Path,
        run_configs: List[Dict[str, Any]],
        project_name: str
    ) -> None:
        """Create run configuration XML files."""
        runConfigurations_path = idea_path / 'runConfigurations'
        runConfigurations_path.mkdir(exist_ok=True)

        for config in run_configs:
            self._create_single_run_config(runConfigurations_path, config, project_name)

    def _create_single_run_config(
        self,
        configs_path: Path,
        config: Dict[str, Any],
        project_name: str
    ) -> None:
        """Create a single run configuration XML file."""
        config_name = config.get('name', 'Run')
        config_type = config.get('type', 'PythonConfigurationType')

        root = ET.Element('component', name='ProjectRunConfigurationManager')
        configuration = ET.SubElement(root, 'configuration')
        configuration.set('default', 'false')
        configuration.set('name', config_name)
        configuration.set('type', config_type)

        # Add configuration options
        if config_type == 'PythonConfigurationType':
            ET.SubElement(configuration, 'option', name='INTERPRETER_OPTIONS', value='')
            ET.SubElement(configuration, 'option', name='PARENT_ENVS', value='true')

            script_path = config.get('script_path', '$PROJECT_DIR$/main.py')
            ET.SubElement(configuration, 'option', name='SCRIPT_NAME', value=script_path)

            params = config.get('parameters', '')
            ET.SubElement(configuration, 'option', name='PARAMETERS', value=params)

            working_dir = config.get('working_directory', '$PROJECT_DIR$')
            ET.SubElement(configuration, 'option', name='WORKING_DIRECTORY', value=working_dir)

        # Method
        method = ET.SubElement(configuration, 'method', v='2')

        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')

        # Sanitize filename
        safe_name = config_name.replace(' ', '_').replace(':', '')
        tree.write(
            configs_path / f'{safe_name}.xml',
            encoding='UTF-8',
            xml_declaration=True
        )

    def open_project(self, path: str, new_window: bool = False) -> bool:
        """
        Open project in PyCharm.

        Args:
            path: Path to project
            new_window: Whether to open in new window

        Returns:
            True if successful
        """
        try:
            if not self.is_available():
                logger.error("PyCharm not available")
                return False

            cmd = [self.pycharm_path, str(path)]
            if new_window:
                cmd.append('--new-window')

            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0:
                logger.info(f"Opened in PyCharm: {path}")
                return True
            else:
                logger.error(f"Failed to open in PyCharm: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Failed to open in PyCharm: {e}")
            return False

    def sync_files(
        self,
        source_path: str,
        target_path: str,
        files: List[Dict[str, Any]],
        create_structure: bool = True
    ) -> List[FileSync]:
        """Synchronize files to target directory."""
        try:
            source_path = Path(source_path)
            target_path = Path(target_path)
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
                    if create_structure:
                        target_file.parent.mkdir(parents=True, exist_ok=True)

                    if isinstance(content, str):
                        target_file.write_text(content, encoding='utf-8')
                    else:
                        target_file.write_bytes(content if isinstance(content, bytes) else content.encode('utf-8'))

                    sync_result = FileSync(
                        source_path=str(source_file),
                        target_path=str(target_file),
                        status='synced',
                        last_sync=datetime.now()
                    )

                    self.file_sync_status[str(target_file)] = sync_result
                    sync_results.append(sync_result)

                except Exception as e:
                    logger.error(f"Failed to sync file {file_path}: {e}")
                    sync_results.append(FileSync(
                        source_path=str(source_file),
                        target_path=str(target_file),
                        status='error',
                        error_message=str(e)
                    ))

            logger.info(f"File sync completed: {len([s for s in sync_results if s.status == 'synced'])}/{len(sync_results)}")
            return sync_results

        except Exception as e:
            logger.error(f"File synchronization failed: {e}")
            raise IDEProviderError(f"File sync failed: {e}")

    def create_project_structure(
        self,
        project_path: str,
        structure: Dict[str, Any]
    ) -> ProjectStructure:
        """Create project directory structure."""
        try:
            project_path = Path(project_path).resolve()
            project_path.mkdir(parents=True, exist_ok=True)

            created_dirs = []
            created_files = []
            total_size = 0

            # Create directories
            for dir_path in structure.get('directories', []):
                full_dir = project_path / dir_path
                full_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_dir))

            # Create files
            for file_path, content in structure.get('files', {}).items():
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

            return ProjectStructure(
                root_path=str(project_path),
                directories=created_dirs,
                files=created_files,
                total_size=total_size,
                file_count=len(created_files),
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            raise IDEProviderError(f"Project structure creation failed: {e}")

    def generate_settings(self, technology_stack: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate PyCharm settings."""
        settings = {
            'python_interpreter': './venv/bin/python',
            'enable_inspections': self.enable_inspections,
            'enable_code_style': self.enable_code_style,
            'code_style': {
                'indent_size': 4,
                'continuation_indent': 8,
                'max_line_length': 120
            }
        }

        if technology_stack and any('python' in str(k).lower() for k in technology_stack.keys()):
            settings.update({
                'enable_pytest': True,
                'enable_pylint': True,
                'enable_mypy': True
            })

        return settings

    def generate_run_configurations(
        self,
        technology_stack: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate PyCharm run configurations."""
        configs = []

        if not technology_stack:
            return configs

        # Python run configuration
        if any('python' in str(k).lower() for k in technology_stack.keys()):
            configs.append({
                'name': 'Run Main',
                'type': 'PythonConfigurationType',
                'script_path': '$PROJECT_DIR$/main.py',
                'parameters': '',
                'working_directory': '$PROJECT_DIR$'
            })

            # Pytest configuration
            configs.append({
                'name': 'Run Tests',
                'type': 'pytest',
                'script_path': '',
                'parameters': '-v',
                'working_directory': '$PROJECT_DIR$'
            })

        # Flask configuration
        if 'flask' in str(technology_stack).lower():
            configs.append({
                'name': 'Flask App',
                'type': 'PythonConfigurationType',
                'script_path': '$PROJECT_DIR$/app.py',
                'parameters': '',
                'working_directory': '$PROJECT_DIR$',
                'env_vars': {
                    'FLASK_APP': 'app.py',
                    'FLASK_ENV': 'development'
                }
            })

        return configs

    def install_extensions(self, extensions: List[str]) -> Dict[str, bool]:
        """
        Install PyCharm plugins.

        Note: PyCharm plugin installation via CLI is limited.
        Returns False for all as they typically need manual installation.

        Args:
            extensions: List of plugin IDs

        Returns:
            Dict of installation results (all False)
        """
        logger.warning("PyCharm plugin installation via CLI not fully supported")
        return {ext: False for ext in extensions}

    def health_check(self) -> Dict[str, Any]:
        """Check PyCharm provider health."""
        try:
            pycharm_available = self.is_available()
            pycharm_version = self.get_version() if pycharm_available else None

            return {
                'status': 'healthy' if pycharm_available else 'limited',
                'ide_name': self.get_ide_name(),
                'pycharm_available': pycharm_available,
                'pycharm_version': pycharm_version,
                'pycharm_path': self.pycharm_path,
                'enable_inspections': self.enable_inspections,
                'enable_code_style': self.enable_code_style,
                'tracked_files': len(self.file_sync_status),
                'last_check': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"PyCharm health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'pycharm_available': False,
                'last_check': datetime.now().isoformat()
            }

    def cleanup(self) -> None:
        """Clean up resources."""
        self.file_sync_status.clear()
        logger.info("PyCharm provider cleanup complete")


__all__ = ['PyCharmProvider']
