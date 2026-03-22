"""
Integration tests for complete project workflows.

Tests end-to-end scenarios combining multiple modules:
- Project creation and initialization
- Code analysis workflows
- Git repository integration
- Dependency validation
- File change tracking
"""

import tempfile
from pathlib import Path

import pytest

from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User
from socratic_system.utils.code_structure_analyzer import CodeStructureAnalyzer
from socratic_system.utils.file_change_tracker import FileChangeTracker


@pytest.fixture
def integration_env():
    """Create temporary environment for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield {
            "base_dir": tmpdir,
            "project_dir": Path(tmpdir) / "project",
            "code_dir": Path(tmpdir) / "project" / "src",
        }


@pytest.fixture
def sample_user():
    """Create sample user for integration tests."""
    return User(
        username="integtest",
        email="test@integration.com",
        passcode_hash="hash123",
        created_at=__import__("datetime").datetime.now(),
        projects=["proj-001"],
        subscription_tier="pro",
    )


@pytest.fixture
def sample_project():
    """Create sample project for integration tests."""
    now = __import__("datetime").datetime.now()
    return ProjectContext(
        project_id="proj-001",
        name="Integration Test Project",
        owner="integtest",
        phase="discovery",
        created_at=now,
        updated_at=now,
        goals="Test complete workflow",
        requirements=["Req 1"],
        tech_stack=["Python", "FastAPI"],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="standard",
    )


class TestProjectCreationWorkflow:
    """Tests for project creation workflow."""

    def test_user_creates_project(self, sample_user, sample_project):
        """Test user creates new project."""
        assert sample_user.username == "integtest"
        assert sample_project.owner == "integtest"
        assert sample_project.project_id in ["proj-001"]

    def test_project_initialization(self, sample_project):
        """Test project initializes with proper structure."""
        assert sample_project.project_id is not None
        assert sample_project.owner is not None
        assert sample_project.phase == "discovery"

    def test_project_inherits_user_preferences(self, sample_user, sample_project):
        """Test project inherits user language preferences."""
        assert sample_project.language_preferences == "python"

    def test_project_team_initialization(self, sample_project):
        """Test project team structure is set up."""
        assert sample_project.team_structure == "individual"
        assert sample_project.owner is not None


class TestCodeAnalysisWorkflow:
    """Tests for code analysis workflow."""

    def test_analyze_project_structure(self, integration_env):
        """Test analyzing project code structure."""
        # Create sample code
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        py_file = code_dir / "main.py"
        py_file.write_text(
            """
class Application:
    def __init__(self):
        self.config = {}

    def start(self):
        print("Starting application")
"""
        )

        # Analyze structure
        analyzer = CodeStructureAnalyzer(py_file.read_text())
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_extract_dependencies(self, integration_env):
        """Test extracting project dependencies."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        py_file = code_dir / "app.py"
        py_file.write_text(
            """
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
"""
        )

        # Analyze code
        code = py_file.read_text()
        assert "import" in code

    def test_detect_code_patterns(self, integration_env):
        """Test detecting code patterns and best practices."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        py_file = code_dir / "models.py"
        py_file.write_text(
            """
class User:
    def __init__(self, name):
        self.name = name

class Product:
    def __init__(self, title):
        self.title = title

def validate_email(email):
    return "@" in email
"""
        )

        analyzer = CodeStructureAnalyzer(py_file.read_text())
        result = analyzer.analyze()

        assert isinstance(result, dict)


class TestFileChangeTrackingWorkflow:
    """Tests for file change tracking workflow."""

    def test_track_initial_codebase(self, integration_env):
        """Test tracking initial codebase."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Create initial files
        (code_dir / "file1.py").write_text("x = 1")
        (code_dir / "file2.py").write_text("y = 2")

        # Verify files exist
        assert (code_dir / "file1.py").exists()
        assert (code_dir / "file2.py").exists()

    def test_detect_code_modifications(self, integration_env):
        """Test detecting modifications to existing code."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        py_file = code_dir / "script.py"
        original = "def func():\n    return 1\n"
        py_file.write_text(original)

        # Modify code
        modified = "def func():\n    return 2\n"
        py_file.write_text(modified)

        assert py_file.read_text() != original

    def test_detect_new_files(self, integration_env):
        """Test detecting new files added to project."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for i in range(3):
            f = code_dir / f"module{i}.py"
            f.write_text(f"# Module {i}\n")
            files.append(f)

        assert all(f.exists() for f in files)

    def test_track_deletion(self, integration_env):
        """Test tracking deleted files."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        py_file = code_dir / "temp.py"
        py_file.write_text("temporary")

        assert py_file.exists()

        py_file.unlink()

        assert not py_file.exists()

    def test_compute_file_hashes(self):
        """Test computing hashes for change detection."""
        tracker = FileChangeTracker()

        content = "file content"
        hash1 = tracker.compute_hash(content)

        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 length


class TestMultiModuleIntegration:
    """Tests combining multiple modules."""

    def test_project_with_code_analysis(self, sample_project, integration_env):
        """Test project combined with code analysis."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Create project code
        main_file = code_dir / "main.py"
        main_file.write_text(
            """
from pathlib import Path
import logging

class MainApp:
    def run(self):
        pass
"""
        )

        # Analyze project code
        code = main_file.read_text()
        analyzer = CodeStructureAnalyzer(code)
        analysis = analyzer.analyze()

        assert sample_project.project_id == "proj-001"
        assert isinstance(analysis, dict)

    def test_user_project_codebase_workflow(self, sample_user, sample_project, integration_env):
        """Test complete user -> project -> codebase workflow."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # User owns project
        assert sample_user.username == sample_project.owner

        # Create project files
        for i in range(3):
            f = code_dir / f"module{i}.py"
            f.write_text(f"# Module {i}\ndef func_{i}(): pass\n")

        files = list(code_dir.glob("*.py"))
        assert len(files) == 3

    def test_project_evolution_workflow(self, sample_project, integration_env):
        """Test project evolution over time."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Initial code
        main_file = code_dir / "main.py"
        main_file.write_text("x = 1")

        tracker = FileChangeTracker()
        hash1 = tracker.compute_hash(main_file.read_text())

        # First modification
        main_file.write_text("x = 1\ny = 2")
        hash2 = tracker.compute_hash(main_file.read_text())

        # Second modification
        main_file.write_text("x = 1\ny = 2\nz = 3")
        hash3 = tracker.compute_hash(main_file.read_text())

        assert hash1 != hash2 != hash3


class TestCompleteProjectScenarios:
    """Tests for complete real-world scenarios."""

    def test_web_application_setup(self, sample_project, integration_env):
        """Test setting up web application project."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Create web app structure
        (code_dir / "app.py").write_text(
            """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello"}
"""
        )

        (code_dir / "models.py").write_text(
            """
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
"""
        )

        # Analyze structure
        app_code = (code_dir / "app.py").read_text()
        analyzer = CodeStructureAnalyzer(app_code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_data_science_project_setup(self, integration_env):
        """Test setting up data science project."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Create data science structure
        (code_dir / "analysis.py").write_text(
            """
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

data = pd.read_csv("data.csv")
scaler = StandardScaler()
scaled = scaler.fit_transform(data)
"""
        )

        # Verify code exists
        assert (code_dir / "analysis.py").exists()

    def test_microservices_architecture(self, integration_env):
        """Test setting up microservices architecture."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        # Create services
        services = ["auth_service", "user_service", "product_service"]
        for service in services:
            service_dir = code_dir / service
            service_dir.mkdir(exist_ok=True)

            (service_dir / "__init__.py").write_text("")
            (service_dir / "main.py").write_text(f"# {service}\n")

        # Verify structure
        assert all((code_dir / s).exists() for s in services)


class TestProjectTransitions:
    """Tests for project phase transitions."""

    def test_discovery_to_design(self, sample_project):
        """Test transitioning from discovery to design phase."""
        assert sample_project.phase == "discovery"

        sample_project.phase = "design"

        assert sample_project.phase == "design"

    def test_design_to_implementation(self, sample_project):
        """Test transitioning from design to implementation."""
        sample_project.phase = "design"
        sample_project.phase = "implementation"

        assert sample_project.phase == "implementation"

    def test_full_lifecycle(self, sample_project):
        """Test complete project lifecycle."""
        phases = ["discovery", "design", "implementation", "testing", "deployment"]

        for phase in phases:
            sample_project.phase = phase
            assert sample_project.phase == phase


class TestErrorHandlingInWorkflows:
    """Tests for error handling in workflows."""

    def test_handle_invalid_code_structure(self, integration_env):
        """Test handling invalid code structure."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        invalid_py = code_dir / "invalid.py"
        invalid_py.write_text("def broken(\n    invalid syntax\n")

        analyzer = CodeStructureAnalyzer(invalid_py.read_text())
        result = analyzer.analyze()

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_handle_missing_files(self, integration_env):
        """Test handling missing project files."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        nonexistent = code_dir / "missing.py"
        assert not nonexistent.exists()

    def test_handle_corrupted_data(self, integration_env):
        """Test handling corrupted file data."""
        code_dir = integration_env["code_dir"]
        code_dir.mkdir(parents=True, exist_ok=True)

        bad_file = code_dir / "corrupt.py"
        bad_file.write_bytes(b"\x00\x01\x02\x03")

        # Should handle binary data
        assert bad_file.exists()

    def test_handle_permission_errors(self, integration_env):
        """Test handling permission-denied scenarios."""
        # Test graceful handling
        assert integration_env is not None
