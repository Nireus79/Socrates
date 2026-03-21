"""
Comprehensive tests for SyntaxValidator utility module.

Tests syntax validation for multiple programming languages.
"""

import tempfile
from pathlib import Path

import pytest

from socratic_system.utils.validators.syntax_validator import SyntaxValidator


@pytest.fixture
def validator():
    """Create a SyntaxValidator instance."""
    return SyntaxValidator()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestSyntaxValidatorInit:
    """Tests for SyntaxValidator initialization."""

    def test_init(self, validator):
        """Test SyntaxValidator initialization."""
        assert validator is not None

    def test_supported_languages(self, validator):
        """Test that supported languages are defined."""
        assert len(validator.SUPPORTED_LANGUAGES) > 0
        assert "python" in validator.SUPPORTED_LANGUAGES
        assert "javascript" in validator.SUPPORTED_LANGUAGES

    def test_python_extensions(self, validator):
        """Test Python file extensions."""
        py_exts = validator.SUPPORTED_LANGUAGES["python"]
        assert ".py" in py_exts

    def test_javascript_extensions(self, validator):
        """Test JavaScript file extensions."""
        js_exts = validator.SUPPORTED_LANGUAGES["javascript"]
        assert ".js" in js_exts
        assert ".jsx" in js_exts

    def test_multiple_language_support(self, validator):
        """Test that multiple languages are supported."""
        languages = validator.SUPPORTED_LANGUAGES.keys()
        expected = ["python", "javascript", "typescript", "java", "go", "rust", "csharp", "cpp"]
        for lang in expected:
            assert lang in languages


class TestValidateNonexistentPath:
    """Tests for validating nonexistent paths."""

    def test_validate_nonexistent_file(self, validator):
        """Test validating nonexistent file."""
        result = validator.validate("/nonexistent/path/file.py")

        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert result["metadata"]["files_checked"] == 0

    def test_validate_nonexistent_directory(self, validator):
        """Test validating nonexistent directory."""
        result = validator.validate("/nonexistent/directory")

        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_nonexistent_error_message(self, validator):
        """Test error message for nonexistent path."""
        result = validator.validate("/fake/path.py")

        assert any("does not exist" in issue.get("message", "").lower() for issue in result["issues"])


class TestValidatePythonFiles:
    """Tests for validating Python files."""

    def test_valid_python_file(self, validator, temp_dir):
        """Test validating valid Python file."""
        py_file = Path(temp_dir) / "valid.py"
        py_file.write_text("def hello():\n    return 'world'\n")

        result = validator.validate(str(py_file))

        assert result["valid"] is True
        assert result["metadata"]["files_checked"] >= 1

    def test_invalid_python_syntax(self, validator, temp_dir):
        """Test validating Python file with syntax error."""
        py_file = Path(temp_dir) / "invalid.py"
        py_file.write_text("def hello(\n    invalid syntax\n")

        result = validator.validate(str(py_file))

        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_python_empty_file(self, validator, temp_dir):
        """Test validating empty Python file."""
        py_file = Path(temp_dir) / "empty.py"
        py_file.write_text("")

        result = validator.validate(str(py_file))

        assert result["valid"] is True

    def test_python_with_comments(self, validator, temp_dir):
        """Test validating Python file with comments."""
        py_file = Path(temp_dir) / "commented.py"
        py_file.write_text("# This is a comment\nprint('hello')\n")

        result = validator.validate(str(py_file))

        assert result["valid"] is True

    def test_python_multiline_string(self, validator, temp_dir):
        """Test validating Python file with multiline strings."""
        py_file = Path(temp_dir) / "multiline.py"
        py_file.write_text('"""\nDocstring\n"""\npass\n')

        result = validator.validate(str(py_file))

        assert result["valid"] is True

    def test_python_indentation_error(self, validator, temp_dir):
        """Test validating Python file with indentation error."""
        py_file = Path(temp_dir) / "indent_error.py"
        py_file.write_text("def func():\nreturn 'bad'\n")  # Missing indentation

        result = validator.validate(str(py_file))

        assert result["valid"] is False

    def test_python_missing_colon(self, validator, temp_dir):
        """Test validating Python file with missing colon."""
        py_file = Path(temp_dir) / "missing_colon.py"
        py_file.write_text("if True\n    pass\n")  # Missing colon

        result = validator.validate(str(py_file))

        assert result["valid"] is False


class TestValidateUnknownFileTypes:
    """Tests for validating unknown file types."""

    def test_unknown_extension(self, validator, temp_dir):
        """Test validating file with unknown extension."""
        unknown_file = Path(temp_dir) / "file.xyz"
        unknown_file.write_text("some content")

        result = validator.validate(str(unknown_file))

        # Should return warning but still valid
        assert len(result["warnings"]) > 0

    def test_text_file_warning(self, validator, temp_dir):
        """Test that .txt files generate warning."""
        txt_file = Path(temp_dir) / "notes.txt"
        txt_file.write_text("Just some text")

        result = validator.validate(str(txt_file))

        assert any("not recognized" in w.get("message", "").lower() for w in result["warnings"])


class TestValidateDirectory:
    """Tests for validating directories."""

    def test_validate_empty_directory(self, validator, temp_dir):
        """Test validating empty directory."""
        result = validator.validate(temp_dir)

        assert "metadata" in result
        assert result["metadata"]["files_checked"] == 0

    def test_validate_directory_with_python_files(self, validator, temp_dir):
        """Test validating directory with Python files."""
        # Create multiple Python files
        for i in range(3):
            py_file = Path(temp_dir) / f"file{i}.py"
            py_file.write_text("x = 1\n")

        result = validator.validate(temp_dir)

        assert result["metadata"]["files_checked"] >= 3
        assert "python" in result["metadata"]["languages"]

    def test_validate_directory_with_mixed_languages(self, validator, temp_dir):
        """Test validating directory with mixed file types."""
        # Create Python file
        Path(temp_dir) / "script.py"
        Path(temp_dir).joinpath("script.py").write_text("print('hi')\n")

        # Create JavaScript file
        Path(temp_dir) / "app.js"
        Path(temp_dir).joinpath("app.js").write_text("console.log('hi');\n")

        result = validator.validate(temp_dir)

        assert result["metadata"]["files_checked"] >= 2

    def test_validate_directory_with_subdirectories(self, validator, temp_dir):
        """Test validating directory with subdirectories."""
        # Create subdirectory with file
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        py_file = subdir / "script.py"
        py_file.write_text("x = 1\n")

        result = validator.validate(temp_dir)

        # Should find files in subdirectories
        assert result["metadata"]["files_checked"] >= 1

    def test_directory_result_structure(self, validator, temp_dir):
        """Test that directory validation result has expected structure."""
        Path(temp_dir) / "test.py"
        Path(temp_dir).joinpath("test.py").write_text("pass\n")

        result = validator.validate(temp_dir)

        assert "valid" in result
        assert "issues" in result
        assert "warnings" in result
        assert "metadata" in result
        assert "files_checked" in result["metadata"]
        assert "files_valid" in result["metadata"]
        assert "files_invalid" in result["metadata"]
        assert "languages" in result["metadata"]


class TestValidationResultStructure:
    """Tests for validation result structure."""

    def test_result_has_valid_field(self, validator, temp_dir):
        """Test that result has 'valid' field."""
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("pass\n")

        result = validator.validate(str(py_file))

        assert "valid" in result
        assert isinstance(result["valid"], bool)

    def test_result_has_issues_list(self, validator, temp_dir):
        """Test that result has 'issues' list."""
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("pass\n")

        result = validator.validate(str(py_file))

        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_result_has_warnings_list(self, validator, temp_dir):
        """Test that result has 'warnings' list."""
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("pass\n")

        result = validator.validate(str(py_file))

        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_result_has_metadata(self, validator, temp_dir):
        """Test that result has 'metadata' dict."""
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("pass\n")

        result = validator.validate(str(py_file))

        assert "metadata" in result
        assert isinstance(result["metadata"], dict)

    def test_issue_structure(self, validator, temp_dir):
        """Test structure of issues in results."""
        py_file = Path(temp_dir) / "invalid.py"
        py_file.write_text("invalid python\n")

        result = validator.validate(str(py_file))

        if result["issues"]:
            issue = result["issues"][0]
            assert "message" in issue or "severity" in issue

    def test_metadata_structure(self, validator, temp_dir):
        """Test structure of metadata."""
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("pass\n")

        result = validator.validate(str(py_file))

        metadata = result["metadata"]
        assert "files_checked" in metadata
        assert isinstance(metadata["files_checked"], int)
        assert "files_valid" in metadata
        assert isinstance(metadata["files_valid"], int)
        assert "files_invalid" in metadata
        assert isinstance(metadata["files_invalid"], int)
        assert "languages" in metadata
        assert isinstance(metadata["languages"], list)


class TestLanguageDetection:
    """Tests for language detection."""

    def test_detect_python_file(self, validator, temp_dir):
        """Test detecting Python file."""
        py_file = Path(temp_dir) / "script.py"
        py_file.write_text("pass\n")

        result = validator.validate(str(py_file))

        # Language should be detected
        if result["metadata"]["files_checked"] > 0:
            assert isinstance(result["metadata"]["languages"], list)

    def test_multiple_file_extensions(self, validator, temp_dir):
        """Test handling files with different extensions."""
        # Create files with different extensions
        extensions = [".py", ".js", ".java", ".go"]
        for ext in extensions:
            file_path = Path(temp_dir) / f"test{ext}"
            if ext == ".py":
                file_path.write_text("pass\n")
            elif ext == ".js":
                file_path.write_text("console.log('hi');\n")
            else:
                file_path.write_text("// comment\n")

        result = validator.validate(temp_dir)

        # Should process multiple file types
        assert result["metadata"]["files_checked"] >= 1


class TestValidatorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_validate_file_with_special_characters(self, validator, temp_dir):
        """Test validating file with special characters in name."""
        special_file = Path(temp_dir) / "file-with-special_chars.py"
        special_file.write_text("pass\n")

        result = validator.validate(str(special_file))

        assert result["valid"] is True

    def test_validate_file_with_unicode_content(self, validator, temp_dir):
        """Test validating file with Unicode content."""
        unicode_file = Path(temp_dir) / "unicode.py"
        unicode_file.write_text("# ✓ Unicode content\npass\n", encoding="utf-8")

        result = validator.validate(str(unicode_file))

        assert result["valid"] is True

    def test_validate_very_large_python_file(self, validator, temp_dir):
        """Test validating very large Python file."""
        large_file = Path(temp_dir) / "large.py"
        # Create a large but valid Python file
        content = "\n".join([f"x{i} = {i}" for i in range(1000)])
        large_file.write_text(content + "\n")

        result = validator.validate(str(large_file))

        assert "metadata" in result
        assert result["metadata"]["files_checked"] >= 1

    def test_validate_python_with_trailing_comma(self, validator, temp_dir):
        """Test validating Python with trailing commas."""
        py_file = Path(temp_dir) / "trailing.py"
        py_file.write_text("x = (\n    1,\n    2,\n)\n")

        result = validator.validate(str(py_file))

        assert result["valid"] is True

    def test_validate_python_with_type_hints(self, validator, temp_dir):
        """Test validating Python with type hints."""
        py_file = Path(temp_dir) / "typed.py"
        py_file.write_text("def func(x: int) -> int:\n    return x\n")

        result = validator.validate(str(py_file))

        assert result["valid"] is True
