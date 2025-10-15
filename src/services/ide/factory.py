"""
IDE Provider Factory - Multi-IDE Support with Auto-Detection
=============================================================

Provides factory pattern for creating IDE providers.
Automatically detects installed IDEs and selects appropriate provider.

Usage:
    # Auto-detect and use best available IDE
    provider = get_ide_provider()

    # Use specific IDE
    provider = get_ide_provider('pycharm')

    # Detect all installed IDEs
    ides = detect_installed_ides()
    # Returns: ['vscode', 'pycharm'] or ['vscode'] etc.
"""

import logging
from typing import Dict, List, Optional, Type

from .base_provider import BaseIDEProvider, IDEProviderError
from .pycharm_provider import PyCharmProvider

# Import existing IDEService as VSCode provider (backward compatibility)
try:
    from ..ide_service import IDEService as VSCodeLegacyService
    VSCODE_LEGACY_AVAILABLE = True
except ImportError:
    VSCODE_LEGACY_AVAILABLE = False
    VSCodeLegacyService = None

logger = logging.getLogger(__name__)


class VSCodeProviderWrapper(BaseIDEProvider):
    """
    Wrapper for existing IDEService to work with BaseIDEProvider interface.

    This maintains backward compatibility while allowing the new multi-IDE system.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        if VSCODE_LEGACY_AVAILABLE:
            self.service = VSCodeLegacyService()
        else:
            raise IDEProviderError("VS Code service not available")

    def get_ide_name(self) -> str:
        return "VS Code"

    def get_executable_name(self) -> str:
        return self.service.vscode_path if hasattr(self.service, 'vscode_path') else 'code'

    def is_available(self) -> bool:
        if hasattr(self.service, '_check_vscode_available'):
            return self.service._check_vscode_available()
        return False

    def get_version(self) -> Optional[str]:
        if hasattr(self.service, '_get_vscode_version'):
            return self.service._get_vscode_version()
        return None

    def create_workspace(self, project_name, project_path, technology_stack=None, additional_folders=None):
        result = self.service.create_workspace(
            project_name, project_path, technology_stack, additional_folders
        )
        # Add ide_type to result
        if hasattr(result, '__dict__'):
            result.ide_type = 'vscode'
        return result

    def open_project(self, path, new_window=False):
        return self.service.open_in_vscode(path, new_window)

    def sync_files(self, source_path, target_path, files, create_structure=True):
        return self.service.sync_files(source_path, target_path, files, create_structure)

    def create_project_structure(self, project_path, structure):
        return self.service.create_project_structure(project_path, structure)

    def generate_settings(self, technology_stack):
        return self.service._generate_workspace_settings(technology_stack)

    def generate_run_configurations(self, technology_stack):
        return self.service._generate_launch_configs(technology_stack)

    def install_extensions(self, extensions):
        return self.service.install_extensions(extensions)

    def health_check(self):
        result = self.service.health_check()
        result['ide_name'] = 'VS Code'
        return result

    def supports_file_watching(self):
        return True

    def start_file_watcher(self, project_path):
        return self.service.start_file_watcher(project_path)

    def stop_file_watcher(self, project_path):
        return self.service.stop_file_watcher(project_path)

    def get_sync_status(self, project_path=None):
        return self.service.get_sync_status(project_path)

    def cleanup(self):
        if hasattr(self.service, 'cleanup_watchers'):
            self.service.cleanup_watchers()


class IDEProviderFactory:
    """
    Factory for creating IDE providers.

    Supports dynamic provider registration and auto-detection.
    """

    # Registry of available providers
    _providers: Dict[str, Type[BaseIDEProvider]] = {
        'vscode': VSCodeProviderWrapper,
        'pycharm': PyCharmProvider,
    }

    # Default IDE preference order
    _preference_order = ['vscode', 'pycharm']

    @classmethod
    def register_provider(cls, ide_id: str, provider_class: Type[BaseIDEProvider]) -> None:
        """
        Register a new IDE provider.

        Args:
            ide_id: Unique IDE identifier (e.g., 'intellij', 'webstorm')
            provider_class: Provider class implementing BaseIDEProvider

        Example:
            IDEProviderFactory.register_provider('intellij', IntelliJProvider)
        """
        cls._providers[ide_id] = provider_class
        logger.info(f"Registered IDE provider: {ide_id}")

    @classmethod
    def get_provider(
        cls,
        ide_id: Optional[str] = None,
        config: Optional[Dict] = None,
        auto_detect: bool = True
    ) -> BaseIDEProvider:
        """
        Get IDE provider instance.

        Args:
            ide_id: Specific IDE to use ('vscode', 'pycharm', etc.)
                    If None and auto_detect=True, detects best available IDE
            config: Optional configuration dict
            auto_detect: If True and ide_id is None, auto-detect best IDE

        Returns:
            BaseIDEProvider instance

        Raises:
            IDEProviderError: If IDE not found or not available
        """
        # Auto-detect if no IDE specified
        if ide_id is None and auto_detect:
            installed_ides = cls.detect_installed_ides()
            if not installed_ides:
                raise IDEProviderError("No supported IDEs detected")

            ide_id = installed_ides[0]  # Use first (highest priority) available
            logger.info(f"Auto-detected IDE: {ide_id}")

        # Validate IDE ID
        if ide_id not in cls._providers:
            available = list(cls._providers.keys())
            raise IDEProviderError(
                f"Unknown IDE: {ide_id}. Available: {available}"
            )

        # Create provider instance
        try:
            provider_class = cls._providers[ide_id]
            provider = provider_class(config)

            # Verify IDE is actually available
            if not provider.is_available():
                logger.warning(f"{provider.get_ide_name()} not available")
                if auto_detect:
                    # Try next available IDE
                    remaining_ides = [i for i in cls.detect_installed_ides() if i != ide_id]
                    if remaining_ides:
                        logger.info(f"Falling back to: {remaining_ides[0]}")
                        return cls.get_provider(remaining_ides[0], config, auto_detect=False)

                raise IDEProviderError(f"{provider.get_ide_name()} not installed or not accessible")

            logger.info(f"Created IDE provider: {provider.get_ide_name()}")
            return provider

        except Exception as e:
            logger.error(f"Failed to create IDE provider for {ide_id}: {e}")
            raise IDEProviderError(f"Provider creation failed: {e}")

    @classmethod
    def detect_installed_ides(cls) -> List[str]:
        """
        Detect all installed IDEs on the system.

        Returns:
            List of IDE IDs in preference order (most preferred first)

        Example:
            >>> detect_installed_ides()
            ['vscode', 'pycharm']
        """
        installed = []

        for ide_id in cls._preference_order:
            if ide_id not in cls._providers:
                continue

            try:
                provider_class = cls._providers[ide_id]
                provider = provider_class({})

                if provider.is_available():
                    version = provider.get_version()
                    installed.append(ide_id)
                    logger.info(
                        f"Detected {provider.get_ide_name()}"
                        f"{f' {version}' if version else ''}"
                    )

            except Exception as e:
                logger.debug(f"Error checking {ide_id}: {e}")
                continue

        if not installed:
            logger.warning("No supported IDEs detected on system")

        return installed

    @classmethod
    def get_supported_ides(cls) -> List[str]:
        """
        Get list of all supported IDE IDs.

        Returns:
            List of supported IDE identifiers
        """
        return list(cls._providers.keys())

    @classmethod
    def set_preference_order(cls, order: List[str]) -> None:
        """
        Set IDE preference order for auto-detection.

        Args:
            order: List of IDE IDs in preferred order

        Example:
            # Prefer PyCharm over VS Code
            IDEProviderFactory.set_preference_order(['pycharm', 'vscode'])
        """
        # Validate all IDs exist
        for ide_id in order:
            if ide_id not in cls._providers:
                raise ValueError(f"Unknown IDE: {ide_id}")

        cls._preference_order = order
        logger.info(f"Set IDE preference order: {order}")


# Convenience functions for easy usage

def get_ide_provider(
    ide_id: Optional[str] = None,
    config: Optional[Dict] = None,
    auto_detect: bool = True
) -> BaseIDEProvider:
    """
    Get IDE provider instance (convenience function).

    Args:
        ide_id: Specific IDE ('vscode', 'pycharm', etc.) or None for auto-detect
        config: Optional configuration dict
        auto_detect: Auto-detect if ide_id is None

    Returns:
        BaseIDEProvider instance

    Example:
        # Auto-detect best IDE
        provider = get_ide_provider()

        # Use specific IDE
        provider = get_ide_provider('pycharm')

        # With config
        provider = get_ide_provider('vscode', {'vscode_path': '/custom/path/code'})
    """
    return IDEProviderFactory.get_provider(ide_id, config, auto_detect)


def detect_installed_ides() -> List[str]:
    """
    Detect all installed IDEs (convenience function).

    Returns:
        List of IDE IDs in preference order

    Example:
        >>> ides = detect_installed_ides()
        >>> print(f"Found IDEs: {ides}")
        Found IDEs: ['vscode', 'pycharm']
    """
    return IDEProviderFactory.detect_installed_ides()


def get_supported_ides() -> List[str]:
    """
    Get list of all supported IDEs (convenience function).

    Returns:
        List of supported IDE identifiers
    """
    return IDEProviderFactory.get_supported_ides()


__all__ = [
    'IDEProviderFactory',
    'get_ide_provider',
    'detect_installed_ides',
    'get_supported_ides',
    'VSCodeProviderWrapper',
]
