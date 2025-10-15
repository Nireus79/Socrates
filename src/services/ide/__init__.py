"""
IDE Integration Package
=======================

Provides support for multiple IDEs with a unified interface.

Currently supported IDEs:
- VS Code (VSCodeProviderWrapper)
- PyCharm (PyCharmProvider)

Easy to extend with new IDEs:
- Create new provider class inheriting from BaseIDEProvider
- Implement all abstract methods
- Register in IDEProviderFactory
- Add to config.yaml

Usage:
    from src.services.ide import get_ide_provider, detect_installed_ides

    # Get provider for user's preferred IDE
    provider = get_ide_provider('pycharm')

    # Or detect and use best available IDE
    ides = detect_installed_ides()
    provider = get_ide_provider(ides[0])

    # Auto-detect (simplest usage)
    provider = get_ide_provider()  # Returns best available IDE

    # Use provider
    provider.create_workspace('MyProject', '/path/to/project')
    provider.open_project('/path/to/project')
"""

from .base_provider import (
    BaseIDEProvider,
    WorkspaceConfig,
    ProjectStructure,
    FileSync,
    IDEProviderError
)

from .pycharm_provider import PyCharmProvider

from .factory import (
    IDEProviderFactory,
    VSCodeProviderWrapper,
    get_ide_provider,
    detect_installed_ides,
    get_supported_ides
)

__all__ = [
    # Base classes and data structures
    'BaseIDEProvider',
    'WorkspaceConfig',
    'ProjectStructure',
    'FileSync',
    'IDEProviderError',

    # Providers
    'VSCodeProviderWrapper',
    'PyCharmProvider',

    # Factory
    'IDEProviderFactory',

    # Convenience functions
    'get_ide_provider',
    'detect_installed_ides',
    'get_supported_ides',
]
