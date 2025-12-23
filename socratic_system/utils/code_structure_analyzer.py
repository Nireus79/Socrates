"""
Code Structure Analyzer - Parse and analyze generated code structure

Analyzes generated code to identify:
- Classes and their methods
- Functions and their purposes
- Imports and dependencies
- Code organization patterns
- Suggested file/module boundaries
"""

import ast
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger("socrates.utils.code_structure_analyzer")


class CodeStructureAnalyzer:
    """Analyze code structure to determine file organization"""

    def __init__(self, code: str, language: str = "python"):
        """
        Initialize analyzer.

        Args:
            code: Generated code as string
            language: Programming language (default: python)
        """
        self.code = code
        self.language = language.lower()
        self.classes: List[Dict] = []
        self.functions: List[Dict] = []
        self.imports: List[str] = []
        self.has_tests = False
        self.has_config = False
        self.has_main = False

    def analyze(self) -> Dict:
        """
        Analyze code structure.

        Returns:
            Dictionary with analysis results
        """
        if self.language == "python":
            return self._analyze_python()
        else:
            return self._analyze_generic()

    def _analyze_python(self) -> Dict:
        """Analyze Python code structure using AST"""
        try:
            tree = ast.parse(self.code)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        self.imports.append(f"{module}.{alias.name}")

            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [
                        m.name for m in node.body if isinstance(m, ast.FunctionDef)
                    ]
                    bases = [ast.unparse(b) for b in node.bases]

                    self.classes.append(
                        {
                            "name": node.name,
                            "methods": methods,
                            "bases": bases,
                            "lineno": node.lineno,
                        }
                    )

            # Extract functions (not in classes)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    self.functions.append(
                        {
                            "name": node.name,
                            "lineno": node.lineno,
                            "is_special": node.name.startswith("_"),
                        }
                    )

            # Detect special patterns
            self._detect_patterns()

            return {
                "language": "python",
                "classes": self.classes,
                "functions": self.functions,
                "imports": list(set(self.imports)),
                "has_tests": self.has_tests,
                "has_config": self.has_config,
                "has_main": self.has_main,
                "class_count": len(self.classes),
                "function_count": len(self.functions),
                "import_count": len(set(self.imports)),
            }

        except SyntaxError as e:
            logger.error(f"Syntax error analyzing code: {e}")
            return self._analyze_generic()

    def _detect_patterns(self) -> None:
        """Detect special code patterns"""
        code_lower = self.code.lower()

        # Check for test patterns
        if (
            "unittest" in code_lower
            or "pytest" in code_lower
            or "test_" in code_lower
            or "def test" in code_lower
        ):
            self.has_tests = True

        # Check for config patterns
        if re.search(r"\b(config|settings|env|configuration)\b", code_lower):
            self.has_config = True

        # Check for main patterns
        if '__name__ == "__main__"' in self.code or "if __name__" in self.code:
            self.has_main = True

    def _analyze_generic(self) -> Dict:
        """Analyze code for non-Python languages"""
        analysis = {
            "language": self.language,
            "classes": [],
            "functions": [],
            "imports": [],
            "has_tests": False,
            "has_config": False,
            "has_main": False,
            "lines_of_code": len(self.code.split("\n")),
        }

        code_lower = self.code.lower()

        # Generic class detection
        class_pattern = r"\b(?:class|struct|interface)\s+(\w+)"
        analysis["classes"] = [
            {"name": m[0], "methods": []}
            for m in re.finditer(class_pattern, self.code, re.IGNORECASE)
        ]

        # Generic function detection
        func_patterns = {
            "python": r"^\s*def\s+(\w+)\(",
            "javascript": r"^\s*(?:function|const|let)\s+(\w+)\s*=?\s*(?:\(|function)",
            "typescript": r"^\s*(?:function|const|let)\s+(\w+)\s*=?\s*(?:\(|function)",
            "go": r"^\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\(",
            "java": r"^\s*(?:public|private|protected)?\s+(?:static)?\s+\w+\s+(\w+)\(",
        }

        pattern = func_patterns.get(self.language, r"^\s*(?:function|def)\s+(\w+)")
        analysis["functions"] = [
            {"name": m[0]}
            for m in re.finditer(pattern, self.code, re.MULTILINE | re.IGNORECASE)
        ]

        # Pattern detection
        analysis["has_tests"] = bool(
            re.search(r"\b(?:test|spec|should)\b", code_lower)
        )
        analysis["has_config"] = bool(
            re.search(r"\b(?:config|settings|env|configuration)\b", code_lower)
        )
        analysis["has_main"] = bool(
            re.search(r"\b(?:main|entry)\b", code_lower)
        )

        return analysis

    def suggest_file_organization(self) -> Dict[str, List[str]]:
        """
        Suggest how to organize code into files.

        Returns:
            Dictionary with suggested file organization
        """
        organization = {
            "models.py": [],
            "controllers.py": [],
            "services.py": [],
            "utils.py": [],
            "config.py": [],
            "main.py": [],
            "tests.py": [],
        }

        # Categorize classes
        for cls in self.classes:
            name_lower = cls["name"].lower()

            if any(
                keyword in name_lower
                for keyword in ["model", "entity", "schema", "dao"]
            ):
                organization["models.py"].append(cls["name"])
            elif any(
                keyword in name_lower
                for keyword in ["controller", "handler", "router", "api"]
            ):
                organization["controllers.py"].append(cls["name"])
            elif any(
                keyword in name_lower for keyword in ["service", "manager", "factory"]
            ):
                organization["services.py"].append(cls["name"])
            else:
                organization["utils.py"].append(cls["name"])

        # Categorize functions
        for func in self.functions:
            name_lower = func["name"].lower()

            if name_lower.startswith("test_"):
                organization["tests.py"].append(func["name"])
            elif name_lower in ["main", "run", "start"]:
                organization["main.py"].append(func["name"])
            elif "config" in name_lower:
                organization["config.py"].append(func["name"])
            else:
                organization["utils.py"].append(func["name"])

        # Remove empty files
        return {k: v for k, v in organization.items() if v}

    def get_suggested_structure(self, project_type: str = "software") -> Dict:
        """
        Get suggested project structure based on analysis.

        Args:
            project_type: Type of project (software, library, etc.)

        Returns:
            Suggested directory structure
        """
        analysis = self.analyze()

        if project_type == "software" and (
            analysis["class_count"] > 2 or analysis["function_count"] > 5
        ):
            # Complex project - use modular structure
            return {
                "structure_type": "modular",
                "directories": ["src", "tests", "config", "docs"],
                "files": {
                    "src/models.py": "Data models and entities",
                    "src/controllers.py": "Controllers and handlers",
                    "src/services.py": "Business logic and services",
                    "src/utils.py": "Utility functions",
                    "src/__init__.py": "Package initialization",
                    "tests/__init__.py": "Test package",
                    "tests/test_models.py": "Model tests",
                    "tests/test_services.py": "Service tests",
                    "config/settings.py": "Configuration",
                    "config/__init__.py": "Config package",
                    "main.py": "Entry point",
                    "requirements.txt": "Dependencies",
                    "README.md": "Documentation",
                },
            }
        else:
            # Simple project - single file or simple structure
            return {
                "structure_type": "simple",
                "directories": [],
                "files": {
                    "main.py": "Main code",
                    "requirements.txt": "Dependencies",
                    "README.md": "Documentation",
                },
            }
