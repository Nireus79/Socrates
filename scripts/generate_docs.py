"""
Documentation generator from test cases and docstrings

Extracts documentation from:
- Test module docstrings
- Test class docstrings
- Test function docstrings
- Code comments
- API signatures

Generates:
- API documentation
- Test coverage documentation
- Feature documentation
"""

import os
import sys
import ast
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class DocstringExtractor(ast.NodeVisitor):
    """Extracts docstrings from Python code"""

    def __init__(self, filename: str):
        self.filename = filename
        self.module_doc = None
        self.classes = {}
        self.functions = {}

    def visit_Module(self, node):
        """Extract module docstring"""
        self.module_doc = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Extract class docstring"""
        docstring = ast.get_docstring(node)
        methods = {}

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_doc = ast.get_docstring(item)
                if method_doc:
                    methods[item.name] = method_doc

        if docstring:
            self.classes[node.name] = {
                "docstring": docstring,
                "methods": methods
            }

    def visit_FunctionDef(self, node):
        """Extract function docstring"""
        docstring = ast.get_docstring(node)
        if docstring and not self._is_method(node):
            self.functions[node.name] = docstring
        self.generic_visit(node)

    def _is_method(self, node) -> bool:
        """Check if function is a method (will be caught by visit_ClassDef)"""
        return hasattr(node, '_parent') and isinstance(node._parent, ast.ClassDef)


def extract_from_file(filepath: Path) -> Dict:
    """Extract documentation from a Python file"""
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read())

        extractor = DocstringExtractor(str(filepath))
        extractor.visit(tree)

        return {
            "module_doc": extractor.module_doc,
            "classes": extractor.classes,
            "functions": extractor.functions
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse {filepath}: {e}")
        return {}


def generate_api_docs() -> str:
    """Generate API documentation from source code"""
    output = []
    output.append("# Socrates API Documentation\n")
    output.append("Auto-generated from source code docstrings\n")
    output.append("Generated: " + str(Path.cwd()) + "\n\n")

    # Extract from socratic_system
    socratic_dir = Path("socratic_system")
    if socratic_dir.exists():
        output.append("## Core Library (socratic_system)\n\n")

        for py_file in sorted(socratic_dir.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue

            docs = extract_from_file(py_file)

            if docs["module_doc"] or docs["classes"] or docs["functions"]:
                rel_path = py_file.relative_to(socratic_dir)
                output.append(f"### {rel_path}\n\n")

                if docs["module_doc"]:
                    output.append(f"{docs['module_doc']}\n\n")

                # Classes
                for class_name, class_info in docs["classes"].items():
                    output.append(f"#### {class_name}\n\n")
                    output.append(f"{class_info['docstring']}\n\n")

                    if class_info["methods"]:
                        output.append("**Methods:**\n\n")
                        for method_name, method_doc in class_info["methods"].items():
                            output.append(f"- `{method_name}`: {method_doc}\n")
                        output.append("\n")

                # Functions
                for func_name, func_doc in docs["functions"].items():
                    output.append(f"#### {func_name}\n\n")
                    output.append(f"{func_doc}\n\n")

    return "".join(output)


def generate_test_docs() -> str:
    """Generate test documentation from test files"""
    output = []
    output.append("# Socrates Test Documentation\n\n")
    output.append("Auto-generated from test docstrings\n\n")

    tests_dir = Path("tests")
    test_categories = defaultdict(list)

    # Extract from test files
    if tests_dir.exists():
        for test_file in sorted(tests_dir.glob("test_*.py")):
            docs = extract_from_file(test_file)

            if docs["classes"]:
                test_name = test_file.stem.replace("test_", "")

                for class_name, class_info in docs["classes"].items():
                    category = class_name.replace("Test", "")
                    test_categories[category].append({
                        "class": class_name,
                        "doc": class_info["docstring"],
                        "methods": class_info["methods"]
                    })

    # Generate output by category
    for category, tests in sorted(test_categories.items()):
        output.append(f"## {category}\n\n")

        for test in tests:
            output.append(f"### {test['class']}\n\n")

            if test["doc"]:
                output.append(f"{test['doc']}\n\n")

            if test["methods"]:
                output.append("**Test Cases:**\n\n")
                for method_name, method_doc in sorted(test["methods"].items()):
                    output.append(f"- `{method_name}`: {method_doc}\n")
                output.append("\n")

    return "".join(output)


def generate_feature_docs() -> str:
    """Generate feature documentation"""
    output = []
    output.append("# Socrates Features\n\n")

    features = {
        "Configuration System": [
            "Flexible SocratesConfig with environment variable support",
            "ConfigBuilder fluent API for easy configuration",
            "Cross-platform default paths",
            "Custom knowledge base support"
        ],
        "Event System": [
            "Thread-safe EventEmitter",
            "30+ event types for all operations",
            "Support for one-time listeners",
            "Event listener removal and management"
        ],
        "Multi-Agent Orchestration": [
            "9 specialized agents for different tasks",
            "Agent coordination and scheduling",
            "Event-driven communication",
            "Error handling and recovery"
        ],
        "Database Layer": [
            "SQLite project database",
            "ChromaDB vector database",
            "Soft delete for projects and users",
            "Full-text search support"
        ],
        "REST API": [
            "FastAPI-based HTTP API",
            "10+ endpoints for all functionality",
            "WebSocket support for real-time updates",
            "CORS support for web frontends"
        ],
        "CLI Tool": [
            "Click-based command-line interface",
            "Project management commands",
            "Code generation from CLI",
            "System diagnostics"
        ],
        "IDE Integration": [
            "PyCharm plugin support",
            "VS Code extension support",
            "JSON-RPC communication protocol",
            "Event forwarding to IDEs"
        ],
        "Testing": [
            "150+ comprehensive tests",
            "Unit, integration, and E2E tests",
            "Performance benchmarks",
            "Load testing framework"
        ],
        "CI/CD Pipeline": [
            "Automated testing on multiple platforms",
            "Code quality checks",
            "Automated PyPI publishing",
            "Release management automation"
        ]
    }

    for feature, items in features.items():
        output.append(f"## {feature}\n\n")
        for item in items:
            output.append(f"- {item}\n")
        output.append("\n")

    return "".join(output)


def main():
    """Generate all documentation"""
    print("=" * 70)
    print("SOCRATES DOCUMENTATION GENERATOR")
    print("=" * 70)
    print()

    # Create docs directory
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Generate API documentation
    print("Generating API documentation...")
    api_docs = generate_api_docs()
    api_file = docs_dir / "API.md"
    with open(api_file, "w") as f:
        f.write(api_docs)
    print(f"  Generated: {api_file}")

    # Generate test documentation
    print("Generating test documentation...")
    test_docs = generate_test_docs()
    test_file = docs_dir / "TESTS.md"
    with open(test_file, "w") as f:
        f.write(test_docs)
    print(f"  Generated: {test_file}")

    # Generate feature documentation
    print("Generating feature documentation...")
    feature_docs = generate_feature_docs()
    feature_file = docs_dir / "FEATURES.md"
    with open(feature_file, "w") as f:
        f.write(feature_docs)
    print(f"  Generated: {feature_file}")

    # Generate index
    print("Generating documentation index...")
    index = generate_documentation_index(docs_dir)
    index_file = docs_dir / "INDEX.md"
    with open(index_file, "w") as f:
        f.write(index)
    print(f"  Generated: {index_file}")

    print()
    print("=" * 70)
    print("DOCUMENTATION GENERATED")
    print("=" * 70)
    print(f"\nDocumentation files in: {docs_dir}")
    print("  - API.md (API reference)")
    print("  - TESTS.md (Test documentation)")
    print("  - FEATURES.md (Feature overview)")
    print("  - INDEX.md (Documentation index)")


def generate_documentation_index(docs_dir: Path) -> str:
    """Generate documentation index"""
    output = []
    output.append("# Socrates Documentation Index\n\n")

    output.append("## Quick Links\n\n")
    output.append("- [API Documentation](API.md) - Complete API reference\n")
    output.append("- [Test Documentation](TESTS.md) - Test suite overview\n")
    output.append("- [Features](FEATURES.md) - Feature descriptions\n")
    output.append("- [CI/CD Pipeline](CI_CD.md) - GitHub Actions workflows\n\n")

    output.append("## Main Documentation\n\n")
    output.append("- [README.md](../README.md) - Project overview\n")
    output.append("- [CHANGELOG.md](../CHANGELOG.md) - Release notes\n\n")

    output.append("## Package Documentation\n\n")
    output.append("- [socrates-cli](../socrates-cli/README.md) - CLI tool\n")
    output.append("- [socrates-api](../socrates-api/README.md) - REST API\n\n")

    output.append("## Integration Examples\n\n")
    output.append("- [examples/pycharm_plugin.py](../examples/pycharm_plugin.py)\n")
    output.append("- [examples/vscode_extension.py](../examples/vscode_extension.py)\n")
    output.append("- [examples/react_frontend_server.py](../examples/react_frontend_server.py)\n\n")

    output.append("## Generated Documentation\n\n")
    for doc_file in sorted(docs_dir.glob("*.md")):
        output.append(f"- [{doc_file.name}]({doc_file.name})\n")

    return "".join(output)


if __name__ == "__main__":
    main()
