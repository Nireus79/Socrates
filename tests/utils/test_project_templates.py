"""
Unit tests for project_templates.py

Tests the ProjectTemplateGenerator for creating various project template files.
"""

import pytest
from socratic_system.utils.project_templates import ProjectTemplateGenerator


class TestProjectTemplateGenerator:
    """Test suite for ProjectTemplateGenerator"""

    def test_generate_pyproject_toml_basic(self):
        """Test basic pyproject.toml generation"""
        content = ProjectTemplateGenerator.generate_pyproject_toml(
            project_name="test-project",
            description="Test project"
        )

        # Verify content
        assert "[build-system]" in content
        assert "[project]" in content
        assert "name = \"test-project\"" in content
        assert "Test project" in content
        assert "setuptools" in content
        assert "wheel" in content

    def test_generate_pyproject_toml_with_dependencies(self):
        """Test pyproject.toml with dependencies"""
        deps = ["requests>=2.0", "numpy>=1.20"]
        dev_deps = ["pytest>=7.0", "black>=22.0"]

        content = ProjectTemplateGenerator.generate_pyproject_toml(
            project_name="data-project",
            dependencies=deps,
            dev_dependencies=dev_deps
        )

        assert "requests>=2.0" in content
        assert "numpy>=1.20" in content
        assert "pytest>=7.0" in content
        assert "black>=22.0" in content
        assert "[tool.black]" in content
        assert "[tool.ruff]" in content
        assert "[tool.mypy]" in content
        assert "[tool.pytest.ini_options]" in content

    def test_generate_pyproject_toml_python_version(self):
        """Test pyproject.toml with specific Python version"""
        content = ProjectTemplateGenerator.generate_pyproject_toml(
            project_name="legacy-project",
            python_version="3.8"
        )

        assert ">=3.8" in content
        assert "python_version = \"3.8\"" in content

    def test_generate_setup_py(self):
        """Test setup.py generation"""
        content = ProjectTemplateGenerator.generate_setup_py(
            project_name="my-package",
            version="0.2.0",
            description="My awesome package"
        )

        assert "my-package" in content
        assert "0.2.0" in content
        assert "My awesome package" in content
        assert "setup(" in content
        assert "find_packages" in content

    def test_generate_setup_cfg(self):
        """Test setup.cfg generation"""
        content = ProjectTemplateGenerator.generate_setup_cfg()

        assert "[metadata]" in content
        assert "[options]" in content
        assert "[bdist_wheel]" in content
        assert "python_requires" in content

    def test_generate_github_workflows(self):
        """Test GitHub workflows generation"""
        workflows = ProjectTemplateGenerator.generate_github_workflows()

        # Should return dictionary with workflow files
        assert isinstance(workflows, dict)
        assert ".github/workflows/ci.yml" in workflows
        assert ".github/workflows/lint.yml" in workflows
        assert ".github/workflows/publish.yml" in workflows

        # Check CI workflow
        ci = workflows[".github/workflows/ci.yml"]
        assert "name: Tests" in ci
        assert "pytest" in ci
        assert "python-version" in ci

        # Check lint workflow
        lint = workflows[".github/workflows/lint.yml"]
        assert "name: Lint" in lint
        assert "black" in lint
        assert "ruff" in lint

        # Check publish workflow
        publish = workflows[".github/workflows/publish.yml"]
        assert "name: Publish" in publish
        assert "PyPI" in publish

    def test_generate_pytest_ini(self):
        """Test pytest.ini generation"""
        content = ProjectTemplateGenerator.generate_pytest_ini()

        assert "[pytest]" in content
        assert "minversion" in content
        assert "python_files" in content
        assert "python_classes" in content
        assert "python_functions" in content
        assert "testpaths" in content

    def test_generate_pre_commit_config(self):
        """Test .pre-commit-config.yaml generation"""
        content = ProjectTemplateGenerator.generate_pre_commit_config()

        assert "repos:" in content
        assert "black" in content
        assert "ruff" in content
        assert "mypy" in content
        assert "pre-commit-hooks" in content

    def test_generate_makefile(self):
        """Test Makefile generation"""
        content = ProjectTemplateGenerator.generate_makefile("test-project")

        assert ".PHONY:" in content
        assert "help:" in content
        assert "install:" in content
        assert "install-dev:" in content
        assert "test:" in content
        assert "lint:" in content
        assert "format:" in content
        assert "clean:" in content
        assert "build:" in content

    def test_generate_license_mit(self):
        """Test MIT license generation"""
        content = ProjectTemplateGenerator.generate_license("MIT")

        assert "MIT License" in content
        assert "Permission is hereby granted" in content
        assert "free of charge" in content

    def test_generate_license_with_author_and_year(self):
        """Test license with custom author and year"""
        content = ProjectTemplateGenerator.generate_license(
            "MIT",
            author="John Doe",
            year="2025"
        )

        assert "Copyright (c) 2025 John Doe" in content

    def test_generate_license_apache(self):
        """Test Apache 2.0 license generation"""
        content = ProjectTemplateGenerator.generate_license("APACHE")

        assert "Apache License" in content

    def test_generate_contributing_md(self):
        """Test CONTRIBUTING.md generation"""
        content = ProjectTemplateGenerator.generate_contributing_md("test-project")

        assert "# Contributing to test-project" in content
        assert "## How to Contribute" in content
        assert "### Reporting Bugs" in content
        assert "### Suggesting Enhancements" in content
        assert "### Submitting Pull Requests" in content
        assert "## Development Setup" in content
        assert "## Code Style" in content
        assert "## Testing" in content

    def test_generate_changelog_md(self):
        """Test CHANGELOG.md generation"""
        content = ProjectTemplateGenerator.generate_changelog_md()

        assert "# Changelog" in content
        assert "## [Unreleased]" in content
        assert "### Added" in content
        assert "### Changed" in content
        assert "### Deprecated" in content
        assert "### Removed" in content
        assert "### Fixed" in content
        assert "### Security" in content

    def test_generate_env_example(self):
        """Test .env.example generation"""
        content = ProjectTemplateGenerator.generate_env_example()

        assert "APP_NAME" in content
        assert "DEBUG" in content
        assert "LOG_LEVEL" in content
        assert "# Environment Configuration Template" in content

    def test_generate_dockerfile(self):
        """Test Dockerfile generation"""
        content = ProjectTemplateGenerator.generate_dockerfile()

        assert "FROM python:" in content
        assert "Stage 1: Builder" in content
        assert "Stage 2: Runtime" in content
        assert "WORKDIR" in content
        assert "RUN pip install" in content
        assert "EXPOSE" in content
        assert "HEALTHCHECK" in content
        assert "CMD" in content

    def test_generate_dockerfile_custom_version(self):
        """Test Dockerfile with custom Python version"""
        content = ProjectTemplateGenerator.generate_dockerfile(python_version="3.10")

        assert "FROM python:3.10-slim" in content

    def test_generate_docker_compose(self):
        """Test docker-compose.yml generation"""
        content = ProjectTemplateGenerator.generate_docker_compose("test-project")

        assert "version: \"3.9\"" in content
        assert "services:" in content
        assert "app:" in content
        assert "postgres:" in content
        assert "redis:" in content
        assert "networks:" in content
        assert "test-project-network" in content
        assert "volumes:" in content

    def test_generate_dockerignore(self):
        """Test .dockerignore generation"""
        content = ProjectTemplateGenerator.generate_dockerignore()

        assert ".git" in content
        assert "__pycache__/" in content
        assert ".venv" in content
        assert ".env" in content
        assert ".DS_Store" in content
        assert ".pytest_cache" in content

    def test_all_templates_are_strings(self):
        """Verify all template methods return strings"""
        pyproject = ProjectTemplateGenerator.generate_pyproject_toml("test")
        assert isinstance(pyproject, str)
        assert len(pyproject) > 0

        setup = ProjectTemplateGenerator.generate_setup_py("test")
        assert isinstance(setup, str)
        assert len(setup) > 0

        cfg = ProjectTemplateGenerator.generate_setup_cfg()
        assert isinstance(cfg, str)
        assert len(cfg) > 0

        workflows = ProjectTemplateGenerator.generate_github_workflows()
        assert isinstance(workflows, dict)
        assert all(isinstance(v, str) for v in workflows.values())

        pytest_ini = ProjectTemplateGenerator.generate_pytest_ini()
        assert isinstance(pytest_ini, str)
        assert len(pytest_ini) > 0

    def test_templates_contain_no_empty_strings(self):
        """Verify templates don't have empty strings"""
        templates = [
            ProjectTemplateGenerator.generate_pyproject_toml("test"),
            ProjectTemplateGenerator.generate_setup_py("test"),
            ProjectTemplateGenerator.generate_makefile("test"),
            ProjectTemplateGenerator.generate_license("MIT"),
            ProjectTemplateGenerator.generate_dockerfile(),
        ]

        for template in templates:
            assert template.strip(), "Template should not be empty"

    def test_makefile_has_all_targets(self):
        """Verify Makefile has all essential targets"""
        makefile = ProjectTemplateGenerator.generate_makefile("test")

        essential_targets = [
            "help",
            "install",
            "install-dev",
            "test",
            "lint",
            "format",
            "type-check",
            "clean",
            "build",
        ]

        for target in essential_targets:
            assert f"{target}:" in makefile, f"Makefile should have {target} target"

    def test_github_workflows_are_valid_yaml(self):
        """Verify GitHub workflows contain valid YAML structure"""
        workflows = ProjectTemplateGenerator.generate_github_workflows()

        for filename, content in workflows.items():
            assert "name:" in content, f"{filename} should have name"
            assert "on:" in content, f"{filename} should have trigger"
            assert "jobs:" in content, f"{filename} should have jobs"

    def test_docker_compose_services(self):
        """Verify docker-compose has required services"""
        content = ProjectTemplateGenerator.generate_docker_compose("test")

        required_services = ["app", "postgres", "redis"]
        for service in required_services:
            assert f"  {service}:" in content or f"  {service}:\n" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
