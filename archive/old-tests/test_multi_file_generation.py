"""Test multi-file code generation functionality"""

import tempfile
from pathlib import Path

from socratic_system.utils.code_structure_analyzer import CodeStructureAnalyzer
from socratic_system.utils.multi_file_splitter import (
    MultiFileCodeSplitter,
    ProjectStructureGenerator,
)
from socratic_system.utils.artifact_saver import ArtifactSaver


# Sample code with proper structure
SAMPLE_CODE = '''
class User:
    """User model"""
    def __init__(self, name, email):
        self.name = name
        self.email = email

class UserController:
    """Handles user API requests"""
    def __init__(self, service):
        self.service = service

    def get_user(self, user_id):
        return self.service.fetch_user(user_id)

class UserService:
    """User business logic"""
    def __init__(self, db):
        self.db = db

    def fetch_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")

def test_user_fetch():
    """Test fetching user"""
    pass

def helper_function():
    """Utility function"""
    return "helper"

if __name__ == "__main__":
    print("Starting application")
'''


def test_code_structure_analyzer():
    """Test code structure analysis"""
    analyzer = CodeStructureAnalyzer(SAMPLE_CODE, language="python")
    analysis = analyzer.analyze()

    assert analysis["class_count"] == 3, f"Expected 3 classes, got {analysis['class_count']}"
    assert analysis["function_count"] >= 2, f"Expected 2+ functions, got {analysis['function_count']}"
    assert analysis["has_main"] is True, "Should detect main entry point"
    assert analysis["has_tests"] is True, "Should detect tests"

    class_names = [c["name"] for c in analysis["classes"]]
    assert "User" in class_names
    assert "UserController" in class_names
    assert "UserService" in class_names

    print("[OK] Code structure analyzer working correctly")


def test_multi_file_splitter():
    """Test code splitting into multiple files"""
    splitter = MultiFileCodeSplitter(SAMPLE_CODE, language="python", project_type="software")
    file_structure = splitter.split()

    # Check that code is split into multiple files
    assert len(file_structure) > 1, "Should create multiple files"
    assert "src/models.py" in file_structure, "Should create models.py"
    assert "src/__init__.py" in file_structure, "Should create __init__.py"

    # Check file contents
    models_content = file_structure["src/models.py"]
    assert "class User" in models_content, "Models should contain User class"

    controllers_content = file_structure.get("src/controllers.py", "")
    assert "UserController" in controllers_content, "Controllers should contain UserController"

    services_content = file_structure.get("src/services.py", "")
    assert "UserService" in services_content, "Services should contain UserService"

    print(f"[OK] Code split into {len(file_structure)} files correctly")


def test_project_structure_generator():
    """Test project structure generation"""
    splitter = MultiFileCodeSplitter(SAMPLE_CODE, language="python")
    file_structure = splitter.split()

    structure = ProjectStructureGenerator.create_structure(
        project_name="My Project",
        generated_files=file_structure,
        project_type="software",
    )

    # Check key files exist
    assert "requirements.txt" in structure, "Should have requirements.txt"
    assert "README.md" in structure, "Should have README.md"
    assert ".gitignore" in structure, "Should have .gitignore"
    assert "main.py" in structure, "Should have main.py"

    # Check file count
    assert len(structure) > 5, "Should create multiple files and directories"

    print(f"[OK] Project structure generated with {len(structure)} files/dirs")


def test_save_multi_file_project():
    """Test saving multi-file project to disk"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        splitter = MultiFileCodeSplitter(SAMPLE_CODE, language="python")
        file_structure = splitter.split()

        structure = ProjectStructureGenerator.create_structure(
            project_name="Test Project",
            generated_files=file_structure,
            project_type="software",
        )

        # Save project
        success, project_root = ArtifactSaver.save_multi_file_project(
            file_structure=structure,
            project_id="test_project",
            project_name="Test Project",
            data_dir=data_dir,
        )

        assert success, "Save should succeed"
        assert project_root, "Should return project root path"

        # Verify files were created
        project_path = Path(project_root)
        assert project_path.exists(), "Project directory should exist"

        # Check key files exist
        assert (project_path / "requirements.txt").exists(), "requirements.txt should exist"
        assert (project_path / "README.md").exists(), "README.md should exist"
        assert (project_path / "main.py").exists(), "main.py should exist"
        assert (project_path / "src" / "__init__.py").exists(), "src/__init__.py should exist"

        print(f"[OK] Multi-file project saved to disk successfully")


def test_project_structure_tree():
    """Test project structure tree visualization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        splitter = MultiFileCodeSplitter(SAMPLE_CODE, language="python")
        file_structure = splitter.split()

        structure = ProjectStructureGenerator.create_structure(
            project_name="Tree Test",
            generated_files=file_structure,
            project_type="software",
        )

        success, project_root = ArtifactSaver.save_multi_file_project(
            file_structure=structure,
            project_id="tree_test",
            project_name="Tree Test",
            data_dir=data_dir,
        )

        # Get tree representation
        tree = ArtifactSaver.get_project_structure_tree(project_root)
        assert tree, "Should return tree structure"
        assert "src" in tree, "Tree should show src directory"
        assert "requirements.txt" in tree, "Tree should show files"

        print("[OK] Project structure tree generated correctly")


def test_list_project_files():
    """Test listing project files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        splitter = MultiFileCodeSplitter(SAMPLE_CODE, language="python")
        file_structure = splitter.split()

        structure = ProjectStructureGenerator.create_structure(
            project_name="List Test",
            generated_files=file_structure,
            project_type="software",
        )

        success, project_root = ArtifactSaver.save_multi_file_project(
            file_structure=structure,
            project_id="list_test",
            project_name="List Test",
            data_dir=data_dir,
        )

        # List files
        files = ArtifactSaver.list_project_files(project_root)
        assert len(files) > 5, f"Should list multiple files, got {len(files)}"
        assert any("models.py" in f for f in files), "Should include models.py"
        assert "requirements.txt" in files, "Should include requirements.txt"
        assert "README.md" in files, "Should include README.md"

        print(f"[OK] Listed {len(files)} files from project")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Multi-File Code Generation")
    print("=" * 70 + "\n")

    test_code_structure_analyzer()
    test_multi_file_splitter()
    test_project_structure_generator()
    test_save_multi_file_project()
    test_project_structure_tree()
    test_list_project_files()

    print("\n" + "=" * 70)
    print("[PASS] All multi-file generation tests passed!")
    print("=" * 70)
