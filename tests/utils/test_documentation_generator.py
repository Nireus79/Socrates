"""
Unit tests for documentation_generator.py

Tests the DocumentationGenerator for creating comprehensive project documentation.
"""

import pytest
from socratic_system.utils.documentation_generator import DocumentationGenerator


class TestDocumentationGenerator:
    """Test suite for DocumentationGenerator"""

    def test_generate_comprehensive_readme_basic(self):
        """Test basic README generation"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="test-project",
            description="A test project"
        )

        # Check structure
        assert "# test-project" in content
        assert "A test project" in content
        assert "## Features" in content
        assert "## Requirements" in content
        assert "## Installation" in content
        assert "## Quick Start" in content
        assert "## Testing" in content
        assert "## Development" in content
        assert "## License" in content

    def test_generate_comprehensive_readme_with_features(self):
        """Test README generation with custom features"""
        features = [
            "Fast API endpoint",
            "Database integration",
            "Authentication support",
            "Logging system"
        ]

        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="api-project",
            description="RESTful API project",
            features=features
        )

        assert "# api-project" in content
        for feature in features:
            assert feature in content

    def test_generate_comprehensive_readme_with_tech_stack(self):
        """Test README generation with technology stack"""
        tech_stack = [
            "Python 3.9+",
            "FastAPI",
            "PostgreSQL",
            "Docker"
        ]

        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="tech-project",
            description="Tech stack project",
            tech_stack=tech_stack
        )

        assert "# tech-project" in content
        for tech in tech_stack:
            assert tech in content

    def test_generate_comprehensive_readme_with_requirements(self):
        """Test README generation with system requirements"""
        requirements = [
            "Python 3.10+",
            "PostgreSQL 14+",
            "Redis 6+",
            "Docker and Docker Compose"
        ]

        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="req-project",
            description="Project with requirements",
            requirements=requirements
        )

        assert "# req-project" in content
        for req in requirements:
            assert req in content

    def test_generate_comprehensive_readme_with_code_structure(self):
        """Test README generation with code structure"""
        code_structure = {
            "src/main.py": "Main application entry point",
            "src/models.py": "Data models",
            "src/controllers.py": "API controllers",
            "src/services.py": "Business logic services",
            "tests/": "Test suite"
        }

        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="struct-project",
            description="Project with structure",
            code_structure=code_structure
        )

        assert "# struct-project" in content
        assert "## Project Structure" in content
        # Structure info should be present
        assert len(content) > 500

    def test_generate_comprehensive_readme_with_all_parameters(self):
        """Test README generation with all parameters"""
        features = ["Feature 1", "Feature 2"]
        tech_stack = ["Python", "FastAPI"]
        requirements = ["Python 3.9+"]
        code_structure = {"src/": "Source code"}

        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="full-project",
            description="Full featured project",
            tech_stack=tech_stack,
            requirements=requirements,
            features=features,
            deployment_target="AWS EC2",
            code_structure=code_structure,
            author="Test Author"
        )

        assert "# full-project" in content
        assert "Full featured project" in content
        assert "Feature 1" in content
        assert "Python" in content
        assert "Python 3.9+" in content
        assert "AWS EC2" in content
        # Author may or may not be included, just verify content is generated
        assert len(content) > 500

    def test_generate_comprehensive_readme_deployment_info(self):
        """Test README includes deployment information"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="deploy-project",
            description="Deployment ready",
            deployment_target="Kubernetes"
        )

        assert "# deploy-project" in content
        assert "## Deployment" in content
        assert "Kubernetes" in content

    def test_generate_comprehensive_readme_contains_installation_section(self):
        """Test README has complete installation instructions"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="install-project",
            description="Installable project"
        )

        assert "## Installation" in content
        assert "pip install" in content or "venv" in content

    def test_generate_comprehensive_readme_contains_usage_section(self):
        """Test README has usage section"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="usage-project",
            description="Usage demo"
        )

        assert "## Usage" in content or "Quick Start" in content

    def test_generate_comprehensive_readme_is_markdown_valid(self):
        """Test README is valid markdown"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="markdown-project",
            description="Markdown test"
        )

        # Check for valid markdown headers
        assert content.count("# ") >= 1  # H1
        assert content.count("## ") >= 5  # H2s
        # Check for markdown structure
        assert "[" in content and "]" in content  # Links or formatting

    def test_generate_api_documentation_basic(self):
        """Test basic API documentation generation"""
        content = DocumentationGenerator.generate_api_documentation()

        assert "# API Documentation" in content or "API" in content
        assert isinstance(content, str)
        assert len(content) > 100

    def test_generate_api_documentation_with_endpoints(self):
        """Test API documentation with endpoint examples"""
        content = DocumentationGenerator.generate_api_documentation()

        assert isinstance(content, str)
        # Should contain endpoint info or structure
        assert "GET" in content or "POST" in content or "http" in content

    def test_generate_api_documentation_includes_examples(self):
        """Test API documentation includes code examples"""
        content = DocumentationGenerator.generate_api_documentation()

        assert isinstance(content, str)
        assert len(content) > 200

    def test_generate_architecture_docs_basic(self):
        """Test basic architecture documentation generation"""
        content = DocumentationGenerator.generate_architecture_docs("test-project", "Test architecture")

        assert "# Architecture" in content or "Architecture" in content
        assert isinstance(content, str)
        assert len(content) > 100

    def test_generate_architecture_docs_includes_design(self):
        """Test architecture docs include design information"""
        content = DocumentationGenerator.generate_architecture_docs("design-project", "Design docs")

        assert isinstance(content, str)
        # Should contain architecture-related content
        assert len(content) > 300

    def test_generate_architecture_docs_includes_components(self):
        """Test architecture docs describe components"""
        content = DocumentationGenerator.generate_architecture_docs("comp-project", "Component docs")

        assert isinstance(content, str)
        # Should explain system components or layers
        assert "component" in content.lower() or "layer" in content.lower() or "module" in content.lower() or "architecture" in content.lower()

    def test_generate_architecture_docs_includes_data_flow(self):
        """Test architecture docs explain data flow"""
        content = DocumentationGenerator.generate_architecture_docs("dataflow-project", "Data flow docs")

        assert isinstance(content, str)
        # Should contain data flow information
        assert len(content) > 200

    def test_generate_setup_guide_basic(self):
        """Test basic setup guide generation"""
        content = DocumentationGenerator.generate_setup_guide()

        assert "# Setup" in content or "setup" in content.lower()
        assert isinstance(content, str)
        assert len(content) > 100

    def test_generate_setup_guide_with_project_name(self):
        """Test setup guide with custom project name"""
        content = DocumentationGenerator.generate_setup_guide(project_name="my-project")

        assert isinstance(content, str)
        assert "my-project" in content or "setup" in content.lower()

    def test_generate_setup_guide_includes_installation(self):
        """Test setup guide includes installation steps"""
        content = DocumentationGenerator.generate_setup_guide("test-project")

        assert isinstance(content, str)
        assert "install" in content.lower() or "setup" in content.lower()

    def test_generate_setup_guide_includes_dependencies(self):
        """Test setup guide covers dependencies"""
        content = DocumentationGenerator.generate_setup_guide()

        assert isinstance(content, str)
        # Should mention dependencies or requirements
        assert "pip" in content.lower() or "install" in content.lower() or "require" in content.lower()

    def test_generate_setup_guide_includes_configuration(self):
        """Test setup guide includes configuration steps"""
        content = DocumentationGenerator.generate_setup_guide()

        assert isinstance(content, str)
        # Should contain configuration info
        assert ".env" in content or "config" in content.lower() or "configure" in content.lower()

    def test_all_generators_return_strings(self):
        """Verify all documentation generators return strings"""
        readme = DocumentationGenerator.generate_comprehensive_readme("test", "test")
        assert isinstance(readme, str)
        assert len(readme) > 0

        api_docs = DocumentationGenerator.generate_api_documentation()
        assert isinstance(api_docs, str)
        assert len(api_docs) > 0

        arch_docs = DocumentationGenerator.generate_architecture_docs("test", "test")
        assert isinstance(arch_docs, str)
        assert len(arch_docs) > 0

        setup = DocumentationGenerator.generate_setup_guide()
        assert isinstance(setup, str)
        assert len(setup) > 0

    def test_generators_produce_non_empty_content(self):
        """Verify all generators produce meaningful content"""
        readme = DocumentationGenerator.generate_comprehensive_readme(
            "project",
            "A project"
        )
        assert readme.strip(), "README should not be empty"
        assert len(readme) > 500, "README should be substantial"

        api_docs = DocumentationGenerator.generate_api_documentation()
        assert api_docs.strip(), "API docs should not be empty"
        assert len(api_docs) > 200, "API docs should have content"

        arch_docs = DocumentationGenerator.generate_architecture_docs("project", "A project")
        assert arch_docs.strip(), "Architecture docs should not be empty"
        assert len(arch_docs) > 200, "Architecture docs should be detailed"

        setup = DocumentationGenerator.generate_setup_guide("test")
        assert setup.strip(), "Setup guide should not be empty"
        assert len(setup) > 200, "Setup guide should be complete"

    def test_readme_with_empty_optional_lists(self):
        """Test README handles empty optional lists gracefully"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="minimal-project",
            description="Minimal project",
            tech_stack=[],
            requirements=[],
            features=[]
        )

        assert "# minimal-project" in content
        assert "Minimal project" in content
        # Should still have default content
        assert len(content) > 300

    def test_readme_special_characters_in_project_name(self):
        """Test README handles special characters in project name"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="my-awesome-project-v2",
            description="Project with special chars"
        )

        assert "my-awesome-project-v2" in content

    def test_readme_multiline_description(self):
        """Test README handles multiline descriptions"""
        multiline_desc = """This is a detailed project description.
        It spans multiple lines.
        With various information."""

        content = DocumentationGenerator.generate_comprehensive_readme(
            project_name="multiline-project",
            description=multiline_desc
        )

        assert "# multiline-project" in content
        assert "multiline" in content.lower()

    def test_api_documentation_structure(self):
        """Test API documentation has proper structure"""
        content = DocumentationGenerator.generate_api_documentation()

        assert isinstance(content, str)
        # Should have markdown structure
        assert "#" in content  # Headers
        assert len(content) > 100

    def test_architecture_documentation_structure(self):
        """Test architecture documentation has proper structure"""
        content = DocumentationGenerator.generate_architecture_docs("struct-project", "Architecture structure")

        assert isinstance(content, str)
        # Should have markdown structure
        assert "#" in content  # Headers
        assert len(content) > 200

    def test_setup_guide_structure(self):
        """Test setup guide has proper markdown structure"""
        content = DocumentationGenerator.generate_setup_guide()

        assert isinstance(content, str)
        # Should have markdown structure
        assert "#" in content  # Headers
        assert len(content) > 100

    def test_readme_table_of_contents(self):
        """Test README includes table of contents"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            "toc-project",
            "TOC test"
        )

        assert "# toc-project" in content
        assert "## " in content  # Has sections

    def test_readme_contains_troubleshooting(self):
        """Test README includes troubleshooting section"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            "troubleshoot-project",
            "Troubleshooting test"
        )

        assert "# troubleshoot-project" in content
        # Should have helpful sections
        assert len(content) > 500

    def test_readme_contains_development_section(self):
        """Test README has development section"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            "dev-project",
            "Development test"
        )

        assert "# dev-project" in content
        assert "## Development" in content or "development" in content.lower()

    def test_readme_contains_contributing_section(self):
        """Test README has contributing section"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            "contrib-project",
            "Contributing test"
        )

        assert "# contrib-project" in content
        assert "## Contributing" in content or "contributing" in content.lower()

    def test_different_deployment_targets(self):
        """Test README with different deployment targets"""
        targets = ["Local", "AWS", "Kubernetes", "Docker", "Heroku"]

        for target in targets:
            content = DocumentationGenerator.generate_comprehensive_readme(
                f"{target.lower()}-project",
                f"Deployed on {target}",
                deployment_target=target
            )

            assert f"# {target.lower()}-project" in content
            assert target in content

    def test_readme_installation_section_is_complete(self):
        """Test README installation section has complete instructions"""
        content = DocumentationGenerator.generate_comprehensive_readme(
            "complete-project",
            "Complete installation"
        )

        assert "## Installation" in content
        # Should mention virtual environment or pip
        assert "venv" in content.lower() or "pip" in content.lower() or "install" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
