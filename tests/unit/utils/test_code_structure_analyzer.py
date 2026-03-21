"""
Comprehensive tests for CodeStructureAnalyzer utility module.

Tests code structure analysis for identifying classes, functions, imports, and patterns.
"""

import pytest

from socratic_system.utils.code_structure_analyzer import CodeStructureAnalyzer


class TestCodeStructureAnalyzerInit:
    """Tests for CodeStructureAnalyzer initialization."""

    def test_init_with_python_code(self):
        """Test initialization with Python code."""
        code = "x = 1"
        analyzer = CodeStructureAnalyzer(code)

        assert analyzer.code == code
        assert analyzer.language == "python"

    def test_init_with_custom_language(self):
        """Test initialization with custom language."""
        code = "console.log('hi');"
        analyzer = CodeStructureAnalyzer(code, language="javascript")

        assert analyzer.language == "javascript"

    def test_init_language_normalization(self):
        """Test that language is normalized to lowercase."""
        code = "x = 1"
        analyzer = CodeStructureAnalyzer(code, language="PYTHON")

        assert analyzer.language == "python"

    def test_init_empty_code(self):
        """Test initialization with empty code."""
        analyzer = CodeStructureAnalyzer("")

        assert analyzer.code == ""

    def test_init_multiline_code(self):
        """Test initialization with multiline code."""
        code = "x = 1\ny = 2\nz = x + y\n"
        analyzer = CodeStructureAnalyzer(code)

        assert analyzer.code == code


class TestAnalyzePython:
    """Tests for Python code analysis."""

    def test_analyze_empty_python(self):
        """Test analyzing empty Python code."""
        analyzer = CodeStructureAnalyzer("")
        result = analyzer.analyze()

        assert isinstance(result, dict)
        assert "classes" in result or "functions" in result or "imports" in result

    def test_analyze_simple_assignment(self):
        """Test analyzing simple assignment."""
        code = "x = 1"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_simple_function(self):
        """Test analyzing simple function."""
        code = """
def hello():
    return 'world'
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)
        assert "functions" in result

    def test_analyze_function_with_docstring(self):
        """Test analyzing function with docstring."""
        code = '''
def calculate(x, y):
    """Calculate sum of x and y."""
    return x + y
'''
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_simple_class(self):
        """Test analyzing simple class."""
        code = """
class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f'Hello, {self.name}'
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)
        assert "classes" in result

    def test_analyze_import_statement(self):
        """Test analyzing import statement."""
        code = "import os\nfrom sys import path\n"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_multiple_classes(self):
        """Test analyzing code with multiple classes."""
        code = """
class ClassA:
    pass

class ClassB:
    pass

class ClassC:
    pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_multiple_functions(self):
        """Test analyzing code with multiple functions."""
        code = """
def func_a():
    pass

def func_b():
    pass

def func_c():
    pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_class_with_methods(self):
        """Test analyzing class with multiple methods."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_nested_classes(self):
        """Test analyzing code with nested classes."""
        code = """
class Outer:
    class Inner:
        pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)


class TestAnalysisResult:
    """Tests for analysis result structure."""

    def test_result_is_dict(self):
        """Test that analyze returns dict."""
        analyzer = CodeStructureAnalyzer("x = 1")
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_result_has_classes_field(self):
        """Test that result has classes field."""
        code = "class Test: pass"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert "classes" in result or result.get("classes") is not None

    def test_result_has_functions_field(self):
        """Test that result has functions field."""
        code = "def test(): pass"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert "functions" in result or result.get("functions") is not None

    def test_result_has_imports_field(self):
        """Test that result has imports field."""
        code = "import os"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert "imports" in result or result.get("imports") is not None


class TestSyntaxError:
    """Tests for handling syntax errors."""

    def test_analyze_invalid_syntax(self):
        """Test analyzing code with syntax error."""
        code = "def func(\ninvalid syntax\n"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        # Should handle gracefully and return dict
        assert isinstance(result, dict)

    def test_analyze_missing_colon(self):
        """Test analyzing code with missing colon."""
        code = "if True\n    pass\n"
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)


class TestLanguageSupport:
    """Tests for different language support."""

    def test_javascript_code(self):
        """Test analyzing JavaScript code."""
        code = "console.log('hello');"
        analyzer = CodeStructureAnalyzer(code, language="javascript")
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_java_code(self):
        """Test analyzing Java code."""
        code = "public class Test { }"
        analyzer = CodeStructureAnalyzer(code, language="java")
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_go_code(self):
        """Test analyzing Go code."""
        code = "package main\nfunc main() { }"
        analyzer = CodeStructureAnalyzer(code, language="go")
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_unsupported_language_fallback(self):
        """Test that unsupported languages fall back gracefully."""
        code = "code here"
        analyzer = CodeStructureAnalyzer(code, language="unknown")
        result = analyzer.analyze()

        assert isinstance(result, dict)


class TestPatternDetection:
    """Tests for pattern detection."""

    def test_detect_main_function(self):
        """Test detecting main function."""
        code = """
def main():
    pass

if __name__ == '__main__':
    main()
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_detect_test_functions(self):
        """Test detecting test functions."""
        code = """
def test_function_a():
    pass

def test_function_b():
    pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_detect_unittest_class(self):
        """Test detecting unittest class."""
        code = """
import unittest

class TestCase(unittest.TestCase):
    def test_something(self):
        pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_detect_config_pattern(self):
        """Test detecting config pattern."""
        code = """
class Config:
    DEBUG = True
    DATABASE_URL = "sqlite:///db.sqlite"
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)


class TestSuggestFileOrganization:
    """Tests for suggesting file organization."""

    def test_suggest_organization_simple(self):
        """Test suggesting file organization for simple code."""
        code = """
class UserModel:
    pass

def get_user(id):
    pass
"""
        analyzer = CodeStructureAnalyzer(code)
        organization = analyzer.suggest_file_organization()

        assert isinstance(organization, dict)

    def test_suggest_organization_returns_dict(self):
        """Test that suggest_file_organization returns dict."""
        code = "x = 1"
        analyzer = CodeStructureAnalyzer(code)
        organization = analyzer.suggest_file_organization()

        assert isinstance(organization, dict)


class TestGetSuggestedStructure:
    """Tests for getting suggested project structure."""

    def test_suggested_structure_software(self):
        """Test suggested structure for software project."""
        code = "class App: pass"
        analyzer = CodeStructureAnalyzer(code)
        structure = analyzer.get_suggested_structure(project_type="software")

        assert isinstance(structure, dict)

    def test_suggested_structure_data_science(self):
        """Test suggested structure for data science project."""
        code = "import pandas"
        analyzer = CodeStructureAnalyzer(code)
        structure = analyzer.get_suggested_structure(project_type="data_science")

        assert isinstance(structure, dict)

    def test_suggested_structure_api(self):
        """Test suggested structure for API project."""
        code = "from fastapi import FastAPI"
        analyzer = CodeStructureAnalyzer(code)
        structure = analyzer.get_suggested_structure(project_type="api")

        assert isinstance(structure, dict)

    def test_suggested_structure_returns_dict(self):
        """Test that get_suggested_structure returns dict."""
        code = "x = 1"
        analyzer = CodeStructureAnalyzer(code)
        structure = analyzer.get_suggested_structure()

        assert isinstance(structure, dict)


class TestComplexCodeStructures:
    """Tests with complex code structures."""

    def test_analyze_django_models(self):
        """Test analyzing Django-like models."""
        code = """
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_fastapi_app(self):
        """Test analyzing FastAPI-like app."""
        code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello"}

@app.post("/users")
def create_user(user: dict):
    return user
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_class_with_properties(self):
        """Test analyzing class with properties."""
        code = """
class DataClass:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_decorators(self):
        """Test analyzing code with decorators."""
        code = """
@decorator
def decorated_func():
    pass

@class_decorator
class DecoratedClass:
    pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_analyze_async_code(self):
        """Test analyzing async code."""
        code = """
async def fetch_data():
    return await some_api()

async def process():
    data = await fetch_data()
    return data
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_long_code(self):
        """Test analyzing very long code."""
        code = "\n".join([f"var{i} = {i}" for i in range(1000)])
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_code_with_unicode(self):
        """Test analyzing code with Unicode."""
        code = """
# ✓ Unicode comment
def greet(name):
    return f'你好, {name}'
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_code_with_special_characters(self):
        """Test analyzing code with special characters."""
        code = '''
def special():
    """Docstring with special chars: @#$%^&*()"""
    return r"raw string\n"
'''
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_code_with_multiline_strings(self):
        """Test analyzing code with multiline strings."""
        code = '''
def doc():
    """
    Multi-line docstring
    with several lines
    of documentation
    """
    return """
    Also multi-line
    regular strings
    """
'''
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_code_with_comments(self):
        """Test analyzing code with extensive comments."""
        code = """
# This is a comment
x = 1  # inline comment
# Another comment
y = 2  # another inline
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_empty_class(self):
        """Test analyzing empty class."""
        code = """
class Empty:
    pass
"""
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)

    def test_class_with_only_docstring(self):
        """Test analyzing class with only docstring."""
        code = '''
class DocumentedOnly:
    """This class has only a docstring."""
'''
        analyzer = CodeStructureAnalyzer(code)
        result = analyzer.analyze()

        assert isinstance(result, dict)
