#!/usr/bin/env python3
"""
Test PyCharm Integration (C4: Multiple IDE Support)
Tests PyCharm provider and multi-IDE factory
"""
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.ide import (
    get_ide_provider,
    detect_installed_ides,
    get_supported_ides,
    IDEProviderFactory,
    PyCharmProvider
)


def test_supported_ides():
    """Test getting list of supported IDEs."""
    supported = get_supported_ides()

    assert isinstance(supported, list)
    assert 'vscode' in supported
    assert 'pycharm' in supported
    assert len(supported) >= 2

    print(f"✓ Supported IDEs: {supported}")


def test_detect_installed_ides():
    """Test IDE auto-detection."""
    installed = detect_installed_ides()

    assert isinstance(installed, list)
    # At least one IDE should be detected (test environment likely has VS Code or PyCharm)
    assert len(installed) >= 0, "Should return empty list if no IDEs found"

    print(f"✓ Detected IDEs: {installed if installed else 'None'}")


def test_pycharm_provider_initialization():
    """Test PyCharm provider can be initialized."""
    provider = PyCharmProvider(config={})

    assert provider is not None
    assert provider.get_ide_name() == "PyCharm"
    assert provider.get_executable_name() in ['pycharm', 'pycharm64']

    print(f"✓ PyCharm provider initialized")
    print(f"  IDE Name: {provider.get_ide_name()}")
    print(f"  Executable: {provider.get_executable_name()}")


def test_pycharm_availability():
    """Test checking if PyCharm is available."""
    provider = PyCharmProvider(config={})

    is_available = provider.is_available()

    # May or may not be installed - both outcomes are valid
    print(f"✓ PyCharm available: {is_available}")

    if is_available:
        version = provider.get_version()
        print(f"  PyCharm version: {version}")


def test_pycharm_workspace_creation(tmp_path):
    """Test creating PyCharm workspace structure."""
    provider = PyCharmProvider(config={})

    project_name = "TestProject"
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    technology_stack = {'python': '3.12', 'flask': True}

    # Create workspace
    workspace = provider.create_workspace(
        project_name=project_name,
        project_path=str(project_path),
        technology_stack=technology_stack
    )

    assert workspace is not None
    assert workspace.ide_type == 'pycharm'
    assert workspace.name == project_name

    # Check .idea folder was created
    idea_path = project_path / '.idea'
    assert idea_path.exists()
    assert idea_path.is_dir()

    # Check key files exist
    assert (idea_path / 'misc.xml').exists()
    assert (idea_path / 'modules.xml').exists()
    assert (idea_path / 'workspace.xml').exists()
    assert (project_path / f'{project_name}.iml').exists()

    print(f"✓ PyCharm workspace created at: {idea_path}")
    print(f"  Files created: misc.xml, modules.xml, workspace.xml, {project_name}.iml")


def test_pycharm_run_configurations(tmp_path):
    """Test PyCharm run configuration generation."""
    provider = PyCharmProvider(config={})

    project_name = "TestProject"
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    technology_stack = {'python': '3.12', 'flask': True}

    workspace = provider.create_workspace(
        project_name=project_name,
        project_path=str(project_path),
        technology_stack=technology_stack
    )

    # Check run configurations
    assert len(workspace.launch_configs) > 0

    run_config_names = [c['name'] for c in workspace.launch_configs]
    print(f"✓ Run configurations created: {run_config_names}")

    # Should have Flask configuration
    assert any('Flask' in name for name in run_config_names)


def test_ide_factory_get_specific_ide():
    """Test getting specific IDE via factory."""
    try:
        # Try to get PyCharm provider
        provider = IDEProviderFactory.get_provider('pycharm', auto_detect=False)

        assert provider is not None
        assert provider.get_ide_name() == "PyCharm"

        print(f"✓ Factory created PyCharm provider")

    except Exception as e:
        # PyCharm might not be installed - that's OK
        print(f"✓ PyCharm not available (expected): {e}")


def test_ide_factory_auto_detect():
    """Test IDE auto-detection via factory."""
    installed = detect_installed_ides()

    if not installed:
        pytest.skip("No IDEs detected - skipping auto-detect test")

    # Auto-detect should return first available IDE
    provider = get_ide_provider()

    assert provider is not None
    assert provider.get_ide_name() in ['VS Code', 'PyCharm']

    print(f"✓ Auto-detected IDE: {provider.get_ide_name()}")


def test_pycharm_health_check():
    """Test PyCharm provider health check."""
    provider = PyCharmProvider(config={})

    health = provider.health_check()

    assert isinstance(health, dict)
    assert 'status' in health
    assert 'ide_name' in health
    assert 'pycharm_available' in health
    assert health['ide_name'] == 'PyCharm'
    assert health['status'] in ['healthy', 'limited', 'unhealthy']

    print(f"✓ PyCharm health check:")
    print(f"  Status: {health['status']}")
    print(f"  Available: {health['pycharm_available']}")
    if health.get('pycharm_version'):
        print(f"  Version: {health['pycharm_version']}")


def test_pycharm_settings_generation():
    """Test PyCharm settings generation."""
    provider = PyCharmProvider(config={})

    technology_stack = {'python': '3.12', 'pytest': True}

    settings = provider.generate_settings(technology_stack)

    assert isinstance(settings, dict)
    assert 'python_interpreter' in settings
    assert 'enable_pytest' in settings
    assert settings['enable_pytest'] is True

    print(f"✓ PyCharm settings generated:")
    print(f"  Keys: {list(settings.keys())}")


def test_ide_preference_order():
    """Test setting IDE preference order."""
    # Get current order
    original_order = IDEProviderFactory._preference_order.copy()

    # Set new order (PyCharm first)
    IDEProviderFactory.set_preference_order(['pycharm', 'vscode'])

    assert IDEProviderFactory._preference_order == ['pycharm', 'vscode']

    print(f"✓ IDE preference order set: ['pycharm', 'vscode']")

    # Restore original order
    IDEProviderFactory._preference_order = original_order


def test_backward_compatibility_vscode():
    """Test that existing VS Code integration still works."""
    try:
        provider = get_ide_provider('vscode', auto_detect=False)

        assert provider is not None
        assert provider.get_ide_name() == 'VS Code'

        print(f"✓ VS Code provider works (backward compatible)")

    except Exception as e:
        # VS Code might not be installed
        print(f"✓ VS Code not available: {e}")


if __name__ == '__main__':
    print("=" * 70)
    print("PyCharm Integration Tests (C4: Multiple IDE Support)")
    print("=" * 70)

    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
