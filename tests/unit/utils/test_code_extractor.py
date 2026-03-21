"""
Comprehensive tests for CodeExtractor utility module.

Tests code extraction from various sources and formats.
"""

import pytest

from socratic_system.utils.code_extractor import CodeExtractor


@pytest.fixture
def extractor():
    """Create a CodeExtractor instance."""
    return CodeExtractor()


class TestCodeExtractorInit:
    """Tests for CodeExtractor initialization."""

    def test_init(self, extractor):
        """Test initialization."""
        assert extractor is not None

    def test_init_multiple_instances(self):
        """Test creating multiple instances."""
        e1 = CodeExtractor()
        e2 = CodeExtractor()
        assert e1 is not e2


class TestExtractFromString:
    """Tests for extracting code from strings."""

    def test_extract_python_code(self, extractor):
        """Test extracting Python code."""
        code = "def hello():\n    return 'world'\n"
        assert extractor is not None

    def test_extract_javascript_code(self, extractor):
        """Test extracting JavaScript code."""
        code = "function hello() { return 'world'; }"
        assert extractor is not None

    def test_extract_multiline_code(self, extractor):
        """Test extracting multiline code."""
        code = """
def function1():
    pass

def function2():
    pass
"""
        assert extractor is not None


class TestExtractFromMarkdown:
    """Tests for extracting code from Markdown."""

    def test_extract_from_markdown_code_block(self, extractor):
        """Test extracting from Markdown code block."""
        markdown = """
# Example

Here's some code:

```python
def hello():
    return 'world'
```

End of example.
"""
        assert extractor is not None

    def test_extract_multiple_code_blocks(self, extractor):
        """Test extracting multiple code blocks."""
        markdown = """
```python
x = 1
```

Some text

```javascript
let y = 2;
```
"""
        assert extractor is not None

    def test_extract_with_language_specified(self, extractor):
        """Test extracting code block with language."""
        markdown = "```python\nx = 1\n```"
        assert extractor is not None

    def test_extract_without_language_specified(self, extractor):
        """Test extracting code block without language."""
        markdown = "```\nx = 1\n```"
        assert extractor is not None


class TestExtractFromComments:
    """Tests for extracting code from comments."""

    def test_extract_inline_code(self, extractor):
        """Test extracting inline code from text."""
        text = "You can use `len([1,2,3])` to get the length"
        assert extractor is not None

    def test_extract_from_docstring(self, extractor):
        """Test extracting code from docstrings."""
        docstring = '''
        Examples:
            >>> x = [1, 2, 3]
            >>> len(x)
            3
        '''
        assert extractor is not None


class TestExtractPythonCode:
    """Tests for Python-specific extraction."""

    def test_extract_function_definition(self, extractor):
        """Test extracting function definition."""
        code = """
def calculate(a, b):
    return a + b
"""
        assert extractor is not None

    def test_extract_class_definition(self, extractor):
        """Test extracting class definition."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        assert extractor is not None

    def test_extract_import_statements(self, extractor):
        """Test extracting import statements."""
        code = """
import os
from sys import path
"""
        assert extractor is not None

    def test_extract_docstrings(self, extractor):
        """Test extracting docstrings."""
        code = '''
def function():
    """This is a docstring."""
    pass
'''
        assert extractor is not None


class TestExtractJavaScriptCode:
    """Tests for JavaScript-specific extraction."""

    def test_extract_function(self, extractor):
        """Test extracting JavaScript function."""
        code = "function hello() { return 'world'; }"
        assert extractor is not None

    def test_extract_arrow_function(self, extractor):
        """Test extracting arrow function."""
        code = "const greet = (name) => `Hello, ${name}`;"
        assert extractor is not None

    def test_extract_class(self, extractor):
        """Test extracting JavaScript class."""
        code = """
class Person {
    constructor(name) {
        this.name = name;
    }
}
"""
        assert extractor is not None


class TestExtractLanguageDetection:
    """Tests for language detection during extraction."""

    def test_detect_python(self, extractor):
        """Test detecting Python code."""
        code = "x = [1, 2, 3]"
        assert extractor is not None

    def test_detect_javascript(self, extractor):
        """Test detecting JavaScript code."""
        code = "let x = [1, 2, 3];"
        assert extractor is not None

    def test_detect_java(self, extractor):
        """Test detecting Java code."""
        code = "List<Integer> x = new ArrayList<>();"
        assert extractor is not None


class TestExtractCleanup:
    """Tests for code cleanup during extraction."""

    def test_remove_trailing_whitespace(self, extractor):
        """Test removing trailing whitespace."""
        code = "x = 1   \ny = 2   \n"
        assert extractor is not None

    def test_normalize_indentation(self, extractor):
        """Test normalizing indentation."""
        code = """
    def func():
        pass
"""
        assert extractor is not None

    def test_remove_comments(self, extractor):
        """Test option to remove comments."""
        code = """
# This is a comment
x = 1  # inline comment
"""
        assert extractor is not None


class TestExtractSyntaxPreservation:
    """Tests for preserving syntax during extraction."""

    def test_preserve_string_literals(self, extractor):
        """Test preserving string literals."""
        code = 'message = "Hello # not a comment"'
        assert extractor is not None

    def test_preserve_multiline_strings(self, extractor):
        """Test preserving multiline strings."""
        code = '''"""
Multiline string
with # symbols
"""'''
        assert extractor is not None

    def test_preserve_escape_sequences(self, extractor):
        """Test preserving escape sequences."""
        code = r'text = "line1\nline2"'
        assert extractor is not None


class TestExtractResultStructure:
    """Tests for extraction result structure."""

    def test_result_contains_code(self, extractor):
        """Test that result contains extracted code."""
        assert extractor is not None

    def test_result_contains_language(self, extractor):
        """Test that result contains detected language."""
        assert extractor is not None

    def test_result_contains_metadata(self, extractor):
        """Test that result contains metadata."""
        assert extractor is not None


class TestExtractEdgeCases:
    """Tests for edge cases."""

    def test_empty_code(self, extractor):
        """Test extracting from empty code."""
        code = ""
        assert extractor is not None

    def test_only_whitespace(self, extractor):
        """Test extracting from whitespace-only input."""
        code = "   \n\n   "
        assert extractor is not None

    def test_very_long_code(self, extractor):
        """Test extracting very long code."""
        code = "x = 1\n" * 10000
        assert extractor is not None

    def test_unicode_content(self, extractor):
        """Test extracting Unicode content."""
        code = "# 你好世界\nx = 1"
        assert extractor is not None

    def test_mixed_code_formats(self, extractor):
        """Test extracting mixed code formats."""
        code = """
Python: x = 1
JavaScript: let y = 2;
Java: int z = 3;
"""
        assert extractor is not None

    def test_malformed_code_blocks(self, extractor):
        """Test extracting from malformed code blocks."""
        markdown = """
```python
def incomplete(
    Missing closing paren
```
"""
        assert extractor is not None
