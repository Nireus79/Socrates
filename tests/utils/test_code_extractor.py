"""
Unit tests for CodeExtractor utility

Tests markdown detection, code extraction, and Python validation.
"""

import pytest
from socratic_system.utils.code_extractor import CodeExtractor


class TestCodeExtractorDetection:
    """Test markdown format detection"""

    def test_detects_code_fences(self):
        """Should detect markdown code fences"""
        content = """Some explanation

```python
def hello():
    print("world")
```
"""
        assert CodeExtractor.is_markdown_format(content) is True

    def test_detects_markdown_headers(self):
        """Should detect markdown headers"""
        content = """## Title

Some content

### Subtitle

More content
"""
        assert CodeExtractor.is_markdown_format(content) is True

    def test_detects_markdown_lists(self):
        """Should detect unordered lists"""
        content = """- Item 1
- Item 2
- Item 3
"""
        assert CodeExtractor.is_markdown_format(content) is True

    def test_raw_python_not_markdown(self):
        """Should not detect raw Python as markdown"""
        content = """def hello():
    print("world")

class MyClass:
    pass
"""
        assert CodeExtractor.is_markdown_format(content) is False

    def test_empty_content(self):
        """Should handle empty content"""
        assert CodeExtractor.is_markdown_format("") is False
        assert CodeExtractor.is_markdown_format(None) is False

    def test_whitespace_only(self):
        """Should handle whitespace-only content"""
        assert CodeExtractor.is_markdown_format("   \n  \n  ") is False


class TestCodeExtractorExtraction:
    """Test code extraction from markdown"""

    def test_extract_single_code_block(self):
        """Should extract Python code from single code block"""
        content = """# My Module

This is a description.

```python
def hello():
    return "world"
```

More text.
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert 'def hello():' in extracted
        assert 'return "world"' in extracted
        assert '# My Module' not in extracted

    def test_extract_multiple_code_blocks(self):
        """Should combine multiple code blocks"""
        content = """```python
def foo():
    pass
```

Some text.

```python
def bar():
    pass
```
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert 'def foo():' in extracted
        assert 'def bar():' in extracted

    def test_extract_python_syntax_variations(self):
        """Should handle ```py and ```python syntax"""
        content_py = "```py\ndef test(): pass\n```"
        content_python = "```python\ndef test(): pass\n```"

        assert CodeExtractor.extract_from_markdown(content_py).strip() != ""
        assert CodeExtractor.extract_from_markdown(content_python).strip() != ""

    def test_raw_python_unchanged(self):
        """Should return raw Python unchanged"""
        content = "def hello():\n    return 42"
        extracted = CodeExtractor.extract_from_markdown(content)
        assert extracted == content

    def test_extraction_preserves_indentation(self):
        """Should preserve code indentation"""
        content = """```python
class MyClass:
    def method(self):
        if True:
            print("indented")
```
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert "    def method(self):" in extracted
        assert "        if True:" in extracted

    def test_extraction_strips_markdown_headers(self):
        """Should remove markdown headers from extracted code"""
        content = """# Title
## Subtitle
### Sub-subtitle

```python
def test():
    pass
```
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert "# Title" not in extracted
        assert "## Subtitle" not in extracted
        assert "def test():" in extracted


class TestCodeExtractorValidation:
    """Test Python syntax validation"""

    def test_valid_python_code(self):
        """Should validate correct Python code"""
        code = """
def hello():
    print("world")

class MyClass:
    pass
"""
        is_valid, error = CodeExtractor.validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_invalid_syntax(self):
        """Should detect syntax errors"""
        code = """
def hello()
    print("missing colon")
"""
        is_valid, error = CodeExtractor.validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "SyntaxError" in error

    def test_empty_code(self):
        """Should reject empty code"""
        is_valid, error = CodeExtractor.validate_python_syntax("")
        assert is_valid is False
        assert error is not None

    def test_whitespace_only_code(self):
        """Should reject whitespace-only code"""
        is_valid, error = CodeExtractor.validate_python_syntax("   \n  \n  ")
        assert is_valid is False

    def test_markdown_invalid_python(self):
        """Should reject markdown-formatted content as Python"""
        code = "## Title\n\nSome text"
        is_valid, error = CodeExtractor.validate_python_syntax(code)
        assert is_valid is False

    def test_complex_valid_code(self):
        """Should validate complex valid code"""
        code = """
import json
from typing import Dict, List

class DataProcessor:
    def __init__(self, data: Dict):
        self.data = data

    def process(self) -> List[str]:
        results = []
        for key, value in self.data.items():
            results.append(f"{key}: {value}")
        return results

def main():
    processor = DataProcessor({"a": 1, "b": 2})
    print(processor.process())

if __name__ == "__main__":
    main()
"""
        is_valid, error = CodeExtractor.validate_python_syntax(code)
        assert is_valid is True
        assert error is None


class TestCodeExtractorCombined:
    """Test extract_and_validate combined operation"""

    def test_extract_and_validate_markdown(self):
        """Should extract and validate markdown with code blocks"""
        content = """# Module

```python
def hello():
    return 42
```
"""
        extracted, is_valid, error = CodeExtractor.extract_and_validate(content)
        assert is_valid is True
        assert error is None
        assert "def hello():" in extracted

    def test_extract_and_validate_invalid(self):
        """Should detect invalid extracted code"""
        content = """# Module

```python
def hello()
    return 42
```
"""
        extracted, is_valid, error = CodeExtractor.extract_and_validate(content)
        assert is_valid is False
        assert error is not None

    def test_extract_and_validate_raw_python(self):
        """Should validate raw Python without extraction"""
        code = "def test():\n    pass"
        extracted, is_valid, error = CodeExtractor.extract_and_validate(code)
        assert extracted == code
        assert is_valid is True


class TestCodeExtractorStatistics:
    """Test code statistics analysis"""

    def test_statistics_simple_code(self):
        """Should calculate statistics for simple code"""
        code = """# Comment
def hello():
    print("world")

class MyClass:
    pass
"""
        stats = CodeExtractor.get_code_statistics(code)
        assert stats["is_valid_python"] is True
        assert stats["class_count"] == 1
        assert stats["function_count"] == 1
        assert stats["comment_lines"] >= 1
        assert stats["code_lines"] > 0

    def test_statistics_with_imports(self):
        """Should count imports"""
        code = """
import os
import sys
from pathlib import Path

def main():
    pass
"""
        stats = CodeExtractor.get_code_statistics(code)
        assert stats["import_count"] >= 2
        assert stats["is_valid_python"] is True

    def test_statistics_invalid_code(self):
        """Should handle invalid code gracefully"""
        code = "def broken()\n    pass"
        stats = CodeExtractor.get_code_statistics(code)
        assert stats["is_valid_python"] is False


class TestCodeExtractorEdgeCases:
    """Test edge cases and special scenarios"""

    def test_nested_code_blocks(self):
        """Should handle nested markdown patterns"""
        content = """# Main

Text with `inline code` here.

```python
def example():
    # This comment has `backticks`
    pass
```
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert "def example():" in extracted

    def test_mixed_markdown_and_code(self):
        """Should extract code from mixed markdown/code"""
        content = """## Configuration

The `config` module provides:

```python
CONFIG = {
    "debug": True,
    "port": 8000,
}
```

Use it like:

```python
from config import CONFIG
print(CONFIG["port"])
```
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert "CONFIG = {" in extracted
        assert "from config import CONFIG" in extracted

    def test_markdown_with_special_chars(self):
        """Should handle markdown with special characters"""
        content = """# API Reference

**Important**: Use `/api/v1/users` endpoint.

```python
def get_users(url="/api/v1/users"):
    return requests.get(url)
```
"""
        extracted = CodeExtractor.extract_from_markdown(content)
        assert "def get_users" in extracted
        assert '"/api/v1/users"' in extracted

    def test_very_long_code_block(self):
        """Should handle very large code blocks"""
        code_lines = ["def function():" if i == 0 else f"    x = {i}  # line {i}" for i in range(100)]
        code = "\n".join(code_lines)
        content = f"```python\n{code}\n```"

        extracted = CodeExtractor.extract_from_markdown(content)
        assert "def function():" in extracted
        assert len(extracted.split("\n")) > 90

    def test_tabs_vs_spaces(self):
        """Should preserve tab/space indentation"""
        code_with_tabs = "def test():\n\tprint('tabs')"
        code_with_spaces = "def test():\n    print('spaces')"

        content_tabs = f"```python\n{code_with_tabs}\n```"
        content_spaces = f"```python\n{code_with_spaces}\n```"

        assert "\t" in CodeExtractor.extract_from_markdown(content_tabs)
        assert "    " in CodeExtractor.extract_from_markdown(content_spaces)
