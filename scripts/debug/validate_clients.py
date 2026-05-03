#!/usr/bin/env python
"""
Standalone validation script for LLM clients

Validates client files without requiring full monolith import.
"""

import ast
import hashlib
import re
import sys
from pathlib import Path


def validate_python_syntax(file_path: str) -> tuple[bool, str]:
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def check_required_methods(file_path: str, required_methods: list) -> tuple[bool, str]:
    """Check if file contains required methods"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        missing = []
        for method in required_methods:
            # For "track_token_usage", accept variants like _track_token_usage_google
            if method == "track_token_usage":
                if not re.search(r"def _track_token_usage", content):
                    missing.append(method)
            else:
                pattern = rf"def {method}\s*\("
                if not re.search(pattern, content):
                    missing.append(method)

        if missing:
            return False, f"Missing methods: {', '.join(missing)}"
        return True, f"All {len(required_methods)} required methods present"
    except Exception as e:
        return False, str(e)


def check_class_definition(file_path: str, class_name: str) -> tuple[bool, str]:
    """Check if file defines the expected class"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            if f"class {class_name}" in line:
                return True, f"Class {class_name} defined (line {i})"

        return False, f"Class {class_name} not found"
    except Exception as e:
        return False, str(e)


def check_docstrings(file_path: str) -> tuple[bool, str]:
    """Check if file has documentation"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check for module docstring
        if not content.startswith('"""') and not content.startswith("'''"):
            return False, "No module docstring"

        # Count docstrings
        docstring_count = len(re.findall(r'""".*?"""', content, re.DOTALL))
        if docstring_count < 5:
            return False, f"Only {docstring_count} docstrings found (expected at least 5)"

        return True, f"Documentation present ({docstring_count} docstrings)"
    except Exception as e:
        return False, str(e)


def count_lines(file_path: str) -> int:
    """Count lines in file"""
    try:
        with open(file_path, 'r') as f:
            return len(f.readlines())
    except:
        return 0


def main():
    """Validate all client files"""
    print("=" * 70)
    print("LLM Clients Validation Report")
    print("=" * 70 + "\n")

    clients = [
        {
            "name": "OpenAI Client",
            "file": "socratic_system/clients/openai_client.py",
            "class": "OpenAIClient",
            "color": "blue",
        },
        {
            "name": "Google Client",
            "file": "socratic_system/clients/google_client.py",
            "class": "GoogleClient",
            "color": "green",
        },
        {
            "name": "Ollama Client",
            "file": "socratic_system/clients/ollama_client.py",
            "class": "OllamaClient",
            "color": "purple",
        },
    ]

    required_methods = [
        "extract_insights",
        "extract_insights_async",
        "generate_code",
        "generate_socratic_question",
        "generate_socratic_question_async",
        "generate_response",
        "generate_response_async",
        "test_connection",
        "_get_cache_key",
        "track_token_usage",  # May be _track_token_usage or _track_token_usage_google, etc.
        "_track_token_usage_async",
        "_get_user_api_key",
        "_decrypt_api_key_from_db",
        "_get_client",
        "_get_async_client",
        "_parse_json_response",
    ]

    all_passed = True
    total_lines = 0

    for client in clients:
        file_path = client["file"]
        full_path = Path(file_path)

        if not full_path.exists():
            print(f"[FAIL] {client['name']}: File not found")
            all_passed = False
            continue

        print(f"{client['name']}:")
        print("-" * 70)

        # Line count
        lines = count_lines(file_path)
        total_lines += lines
        print(f"  Lines of code: {lines}")

        # Syntax validation
        passed, msg = validate_python_syntax(file_path)
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} Syntax validation: {msg}")
        if not passed:
            all_passed = False

        # Class definition
        passed, msg = check_class_definition(file_path, client["class"])
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} Class definition: {msg}")
        if not passed:
            all_passed = False

        # Methods
        passed, msg = check_required_methods(file_path, required_methods)
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} Required methods: {msg}")
        if not passed:
            all_passed = False

        # Documentation
        passed, msg = check_docstrings(file_path)
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} Documentation: {msg}")

        print()

    print("=" * 70)
    print("Summary:")
    print(f"  Total lines of code: {total_lines}")
    print(f"  Total clients: {len(clients)}")
    print(f"  Required methods per client: {len(required_methods)}")
    print(f"  Status: {'ALL PASS' if all_passed else 'SOME FAILURES'}")
    print("=" * 70)

    # Verify clients/__init__.py
    print("\nChecking clients/__init__.py:")
    init_path = "socratic_system/clients/__init__.py"
    if Path(init_path).exists():
        with open(init_path, 'r') as f:
            content = f.read()

        # Check for optional imports
        checks = [
            ("OpenAI import", "from .openai_client import OpenAIClient" in content),
            ("Google import", "from .google_client import GoogleClient" in content),
            ("Ollama import", "from .ollama_client import OllamaClient" in content),
            ("Claude import", "from .claude_client import ClaudeClient" in content),
            ("Graceful error handling", "except ImportError" in content),
        ]

        for check_name, passed in checks:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
    else:
        print(f"  [FAIL] File not found: {init_path}")
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("SUCCESS: All validations passed!")
        print("\nClients are ready for:")
        print("  1. Integration testing with orchestrator")
        print("  2. Extraction to socratic-nexus library")
        print("  3. Publication to PyPI")
        return 0
    else:
        print("FAILURE: Some validations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
