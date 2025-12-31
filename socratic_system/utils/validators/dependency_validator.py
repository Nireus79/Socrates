"""
Dependency Validator - Validates project dependencies and imports

Validates:
- Python requirements.txt against actual imports
- JavaScript package.json against actual imports
- Identifies missing and unused dependencies
"""

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("socrates.utils.validators.dependency_validator")


class DependencyValidator:
    """Validates project dependencies for Python and JavaScript"""

    # Common Python built-in modules
    PYTHON_BUILTINS = {
        "sys", "os", "json", "re", "datetime", "time", "math", "random", "string",
        "collections", "itertools", "functools", "operator", "pathlib", "shutil",
        "tempfile", "glob", "subprocess", "threading", "multiprocessing", "asyncio",
        "socket", "ssl", "http", "urllib", "email", "csv", "configparser", "logging",
        "unittest", "pytest", "typing", "abc", "contextlib", "decorator", "io",
        "pickle", "sqlite3", "hashlib", "hmac", "secrets", "stat", "errno", "uuid",
        "doctest", "pdb", "traceback", "inspect", "warnings", "linecache",
        "dis", "dataclasses", "enum", "copy", "types", "pprint", "reprlib", "weakref",
    }

    def validate(self, target: str) -> Dict[str, Any]:
        """
        Validate dependencies for project or file

        Args:
            target: Directory path to project or file path

        Returns:
            {
                "valid": bool,
                "issues": List[Dict],
                "warnings": List[Dict],
                "metadata": {
                    "project_type": str,
                    "total_dependencies": int,
                    "missing_imports": List[str],
                    "unused_dependencies": List[str]
                }
            }
        """
        target_path = Path(target)

        if not target_path.exists():
            return {
                "valid": False,
                "issues": [{"message": f"Path does not exist: {target}", "severity": "error"}],
                "warnings": [],
                "metadata": {
                    "project_type": "unknown",
                    "total_dependencies": 0,
                    "missing_imports": [],
                    "unused_dependencies": [],
                },
            }

        if target_path.is_file():
            target = str(target_path.parent)

        # Detect project type
        project_type = self._detect_project_type(target)

        if project_type == "python":
            return self._validate_python_dependencies(target)
        elif project_type == "javascript":
            return self._validate_javascript_dependencies(target)
        else:
            return {
                "valid": True,
                "issues": [],
                "warnings": [
                    {
                        "message": "Could not detect project type for dependency validation",
                        "severity": "info",
                    }
                ],
                "metadata": {
                    "project_type": "unknown",
                    "total_dependencies": 0,
                    "missing_imports": [],
                    "unused_dependencies": [],
                },
            }

    def _detect_project_type(self, project_dir: str) -> Optional[str]:
        """Detect project type from key files"""
        project_path = Path(project_dir)

        # Check for Python project
        if (project_path / "requirements.txt").exists() or (project_path / "setup.py").exists():
            return "python"

        # Check for JavaScript project
        if (project_path / "package.json").exists():
            return "javascript"

        # Check for Python files
        for _file_path in project_path.rglob("*.py"):
            return "python"

        # Check for JavaScript files
        for _file_path in project_path.rglob("*.js"):
            return "javascript"

        return None

    def _validate_python_dependencies(self, project_dir: str) -> Dict[str, Any]:
        """Validate Python project dependencies"""
        project_path = Path(project_dir)
        issues = []
        warnings = []

        # Read requirements.txt
        requirements_file = project_path / "requirements.txt"
        declared_deps = set()

        if requirements_file.exists():
            try:
                with open(requirements_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        # Extract package name
                        package = re.split(r"[<>=!~\[]", line)[0].strip().lower()
                        if package:
                            declared_deps.add(package)
            except Exception as e:
                issues.append(
                    {
                        "file": str(requirements_file),
                        "message": f"Error reading requirements.txt: {str(e)}",
                        "severity": "error",
                    }
                )
        else:
            warnings.append(
                {
                    "message": "No requirements.txt found",
                    "severity": "warning",
                    "suggestion": "Consider creating a requirements.txt to track dependencies",
                }
            )

        # Extract imports from Python files
        imported_modules = set()

        try:
            for py_file in project_path.rglob("*.py"):
                # Skip common directories
                if any(skip in py_file.parts for skip in {".git", ".venv", "venv", "__pycache__"}):
                    continue

                try:
                    with open(py_file, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Parse AST to extract imports
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module = alias.name.split(".")[0].lower()
                                imported_modules.add(module)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                module = node.module.split(".")[0].lower()
                                imported_modules.add(module)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error scanning Python files: {e}")

        # Find missing imports (not in requirements, not built-in)
        missing_imports = []
        for module in imported_modules:
            # Skip built-ins and local modules
            if module not in self.PYTHON_BUILTINS and module not in declared_deps:
                # Check if it's a local module (same as package name patterns)
                is_local = False
                for py_file in project_path.glob("*.py"):
                    if py_file.stem == module:
                        is_local = True
                        break

                if not is_local:
                    missing_imports.append(module)

        # Find unused dependencies
        unused_deps = []
        for dep in declared_deps:
            # Normalize dependency name for comparison
            dep_normalized = dep.replace("-", "_")
            if dep_normalized not in imported_modules and dep not in imported_modules:
                unused_deps.append(dep)

        # Create issues for missing dependencies
        if missing_imports:
            issues.append(
                {
                    "message": f"Missing dependencies: {', '.join(sorted(missing_imports))}",
                    "severity": "error",
                    "missing_count": len(missing_imports),
                    "missing_modules": sorted(missing_imports),
                    "suggestion": f"Add to requirements.txt: {' '.join(sorted(missing_imports))}",
                }
            )

        # Create warnings for unused dependencies
        if unused_deps:
            warnings.append(
                {
                    "message": f"Potentially unused dependencies: {', '.join(sorted(unused_deps)[:5])}",
                    "severity": "warning",
                    "unused_count": len(unused_deps),
                    "unused_modules": sorted(unused_deps),
                    "suggestion": "Review and remove unused dependencies from requirements.txt",
                }
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "metadata": {
                "project_type": "python",
                "total_dependencies": len(declared_deps),
                "missing_imports": sorted(missing_imports),
                "unused_dependencies": sorted(unused_deps),
            },
        }

    def _validate_javascript_dependencies(self, project_dir: str) -> Dict[str, Any]:
        """Validate JavaScript project dependencies"""
        project_path = Path(project_dir)
        issues = []
        warnings = []

        # Read package.json
        package_json_file = project_path / "package.json"
        declared_deps = set()

        if not package_json_file.exists():
            return {
                "valid": True,
                "issues": [],
                "warnings": [
                    {
                        "message": "No package.json found",
                        "severity": "warning",
                    }
                ],
                "metadata": {
                    "project_type": "javascript",
                    "total_dependencies": 0,
                    "missing_imports": [],
                    "unused_dependencies": [],
                },
            }

        try:
            with open(package_json_file) as f:
                package_data = json.load(f)

            # Collect dependencies from package.json
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_type in package_data:
                    declared_deps.update(package_data[dep_type].keys())
        except Exception as e:
            issues.append(
                {
                    "file": str(package_json_file),
                    "message": f"Error reading package.json: {str(e)}",
                    "severity": "error",
                }
            )
            return {
                "valid": False,
                "issues": issues,
                "warnings": warnings,
                "metadata": {
                    "project_type": "javascript",
                    "total_dependencies": 0,
                    "missing_imports": [],
                    "unused_dependencies": [],
                },
            }

        # Check if node_modules exists
        if not (project_path / "node_modules").exists():
            warnings.append(
                {
                    "message": "node_modules directory not found",
                    "severity": "warning",
                    "suggestion": "Run 'npm install' or 'yarn install' to install dependencies",
                }
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "metadata": {
                "project_type": "javascript",
                "total_dependencies": len(declared_deps),
                "missing_imports": [],
                "unused_dependencies": [],
            },
        }
