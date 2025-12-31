"""
Code parser for extracting structure from source code files.

Supports multiple programming languages and extracts:
- Functions/methods with signatures
- Classes/interfaces with members
- Imports/dependencies
- Module organization
"""

import ast
import re
from typing import Any, Dict, List


class CodeParser:
    """
    Parses code files to extract structural information.

    Supported languages and their detection:
    - Python (.py): Using ast module for accurate parsing
    - JavaScript (.js, .jsx): Regex-based extraction
    - Java (.java): Regex-based extraction
    - C++ (.cpp, .cc, .h): Regex-based extraction
    - C (.c, .h): Regex-based extraction
    """

    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".h": "cpp",
        ".c": "c",
    }

    def __init__(self):
        """Initialize the code parser."""
        self.logger = self._get_logger()

    def _get_logger(self):
        """Get or create logger for this component."""
        try:
            from socratic_system.utils.logger import get_logger

            return get_logger("code_parser")
        except (ImportError, RuntimeError):
            # Fallback if logger not available
            import logging

            return logging.getLogger("code_parser")

    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a code file and extract structure information.

        Args:
            file_path: Path to the source file
            content: File content as string

        Returns:
            Dictionary containing:
            {
                "language": "python",
                "file_path": "/path/to/file.py",
                "functions": [
                    {"name": "calculate", "params": ["x", "y"], "line": 5, "docstring": "..."},
                    ...
                ],
                "classes": [
                    {
                        "name": "Calculator",
                        "line": 10,
                        "methods": [...],
                        "docstring": "...",
                        "parent": "BaseCalculator"
                    },
                    ...
                ],
                "imports": ["math", "sys", "typing"],
                "structure_summary": "5 functions, 2 classes, 8 imports",
                "metrics": {
                    "lines_of_code": 250,
                    "function_count": 5,
                    "class_count": 2,
                    "import_count": 8
                }
            }
        """
        try:
            # Detect language from file extension
            file_ext = self._get_file_extension(file_path).lower()
            language = self.SUPPORTED_LANGUAGES.get(file_ext, "unknown")

            if language == "unknown":
                self.logger.warning(f"Unknown file type: {file_ext}, treating as plain text")
                return self._create_unsupported_response(file_path)

            # Parse based on language
            if language == "python":
                return self._parse_python(file_path, content)
            elif language == "javascript":
                return self._parse_javascript(file_path, content)
            elif language == "java":
                return self._parse_java(file_path, content)
            elif language == "cpp":
                return self._parse_cpp(file_path, content)
            elif language == "c":
                return self._parse_c(file_path, content)
            else:
                return self._create_unsupported_response(file_path)

        except Exception as e:
            self.logger.warning(f"Error parsing file {file_path}: {e}")
            return self._create_error_response(file_path, str(e))

    def _parse_python(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse Python code using ast module."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in Python file {file_path}: {e}")
            return self._create_error_response(file_path, f"Syntax error: {e}")

        lines = content.split("\n")
        functions = self._extract_python_functions(tree)
        classes = self._extract_python_classes(tree)
        imports = self._extract_python_imports(tree)

        # Calculate metrics
        loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])

        return {
            "language": "python",
            "file_path": file_path,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "structure_summary": self._generate_structure_summary(
                "python", functions, classes, imports
            ),
            "metrics": {
                "lines_of_code": loc,
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
            },
        }

    def _extract_python_functions(self, tree: ast.AST) -> List[Dict]:
        """Extract top-level functions from Python AST."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                func_info = {
                    "name": node.name,
                    "params": self._extract_python_params(node),
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                }
                functions.append(func_info)
        return functions

    def _extract_python_classes(self, tree: ast.AST) -> List[Dict]:
        """Extract classes from Python AST."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.col_offset == 0:
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(
                            {
                                "name": item.name,
                                "params": self._extract_python_params(item),
                                "line": item.lineno,
                            }
                        )

                parent_class = None
                if node.bases:
                    parent_class = self._get_node_name(node.bases[0])

                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods,
                    "docstring": ast.get_docstring(node) or "",
                    "parent": parent_class,
                }
                classes.append(class_info)
        return classes

    def _extract_python_imports(self, tree: ast.AST) -> List[str]:
        """Extract imports from Python AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                for alias in node.names:
                    imports.append(f"{node.module}.{alias.name}" if node.module else alias.name)
        return list(set(imports))  # Remove duplicates

    def _parse_javascript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse JavaScript code using regex-based extraction."""
        lines = content.split("\n")
        functions = self._extract_js_functions(lines)
        classes = self._extract_js_classes(content, lines)
        imports = self._extract_js_imports(lines)

        # Calculate metrics
        loc = len([line for line in lines if line.strip() and not line.strip().startswith("//")])

        return {
            "language": "javascript",
            "file_path": file_path,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "structure_summary": self._generate_structure_summary(
                "javascript", functions, classes, imports
            ),
            "metrics": {
                "lines_of_code": loc,
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
            },
        }

    def _extract_js_functions(self, lines: List[str]) -> List[Dict]:
        """Extract function declarations from JavaScript."""
        functions = []
        func_patterns = [
            r"function\s+(\w+)\s*\(([^)]*)\)",
            r"const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
            r"let\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
            r"var\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
        ]

        seen_functions = set()
        for line_num, line in enumerate(lines, 1):
            for pattern in func_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    func_name = match.group(1)
                    params_str = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
                    params = [
                        p.strip().split("=")[0].strip() for p in params_str.split(",") if p.strip()
                    ]

                    if func_name not in seen_functions:
                        functions.append(
                            {"name": func_name, "params": params, "line": line_num, "docstring": ""}
                        )
                        seen_functions.add(func_name)
        return functions

    def _extract_js_classes(self, content: str, lines: List[str]) -> List[Dict]:
        """Extract class declarations from JavaScript."""
        classes = []
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?"
        seen_classes = set()

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(class_pattern, line)
            for match in matches:
                class_name = match.group(1)
                parent = match.group(2) if match.lastindex and match.lastindex >= 2 else None

                if class_name not in seen_classes:
                    methods = self._extract_js_methods(content, class_name)
                    classes.append(
                        {
                            "name": class_name,
                            "line": line_num,
                            "methods": methods,
                            "docstring": "",
                            "parent": parent,
                        }
                    )
                    seen_classes.add(class_name)
        return classes

    def _extract_js_imports(self, lines: List[str]) -> List[str]:
        """Extract imports from JavaScript."""
        imports = []
        import_patterns = [
            r"import\s+(?:{[^}]*}|[\w\s,]+)\s+from\s+['\"]([^'\"]+)['\"]",
            r"const\s+(?:{[^}]*}|[\w\s]+)\s+=\s+require\(['\"]([^'\"]+)['\"]\)",
        ]

        for line in lines:
            for pattern in import_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    module = match.group(1)
                    if module not in imports:
                        imports.append(module)
        return imports

    def _parse_java(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse Java code using regex-based extraction."""
        functions = []
        classes = []
        imports = []

        lines = content.split("\n")

        # Extract imports
        import_pattern = r"import\s+([\w\.]+)(?:\.\*)?;"
        for line in lines:
            matches = re.finditer(import_pattern, line)
            for match in matches:
                module = match.group(1)
                if module not in imports:
                    imports.append(module)

        # Extract class declarations
        class_pattern = r"(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?"
        seen_classes = set()

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(class_pattern, line)
            for match in matches:
                class_name = match.group(1)
                parent = match.group(2) if match.lastindex and match.lastindex >= 2 else None

                if class_name not in seen_classes:
                    methods = self._extract_java_methods(content)
                    classes.append(
                        {
                            "name": class_name,
                            "line": line_num,
                            "methods": methods,
                            "docstring": "",
                            "parent": parent,
                        }
                    )
                    seen_classes.add(class_name)

        # Extract methods/functions
        method_pattern = r"(?:public|private|protected)?\s+(?:static\s+)?(?:synchronized\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)"
        seen_methods = set()

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(method_pattern, line)
            for match in matches:
                match.group(1)
                method_name = match.group(2)
                params_str = match.group(3) if match.lastindex and match.lastindex >= 3 else ""
                params = [p.strip().split()[-1] for p in params_str.split(",") if p.strip()]

                if method_name not in seen_methods and method_name not in [
                    c["name"] for c in classes
                ]:
                    functions.append(
                        {"name": method_name, "params": params, "line": line_num, "docstring": ""}
                    )
                    seen_methods.add(method_name)

        loc = len([line for line in lines if line.strip() and not line.strip().startswith("//")])

        return {
            "language": "java",
            "file_path": file_path,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "structure_summary": self._generate_structure_summary(
                "java", functions, classes, imports
            ),
            "metrics": {
                "lines_of_code": loc,
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
            },
        }

    def _parse_cpp(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse C++ code using regex-based extraction."""
        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []
        imports: List[str] = []

        lines = content.split("\n")

        # Extract includes
        include_pattern = r"#include\s+[<\"]([^>\"]+)[>\"]"
        for line in lines:
            matches = re.finditer(include_pattern, line)
            for match in matches:
                header = match.group(1)
                if header not in imports:
                    imports.append(header)

        # Extract class/struct declarations
        class_pattern = r"(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?"
        seen_classes = set()

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(class_pattern, line)
            for match in matches:
                class_name = match.group(1)
                parent = match.group(2) if match.lastindex and match.lastindex >= 2 else None

                if class_name not in seen_classes:
                    classes.append(
                        {
                            "name": class_name,
                            "line": line_num,
                            "methods": [],
                            "docstring": "",
                            "parent": parent,
                        }
                    )
                    seen_classes.add(class_name)

        # Extract function declarations
        func_pattern = r"(\w+)\s+(\w+)\s*\(([^)]*)\)\s*(?:const)?(?:;|{)"
        seen_functions = set()

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(func_pattern, line)
            for match in matches:
                match.group(1)
                func_name = match.group(2)
                params_str = match.group(3) if match.lastindex and match.lastindex >= 3 else ""
                params = [
                    p.strip().split()[-1].rstrip("*&") for p in params_str.split(",") if p.strip()
                ]

                if func_name not in seen_functions and func_name not in [
                    c["name"] for c in classes
                ]:
                    functions.append(
                        {"name": func_name, "params": params, "line": line_num, "docstring": ""}
                    )
                    seen_functions.add(func_name)

        loc = len([line for line in lines if line.strip() and not line.strip().startswith("//")])

        return {
            "language": "cpp",
            "file_path": file_path,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "structure_summary": self._generate_structure_summary(
                "cpp", functions, classes, imports
            ),
            "metrics": {
                "lines_of_code": loc,
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
            },
        }

    def _parse_c(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse C code using regex-based extraction."""
        # C parsing is similar to C++ but without classes
        functions = []
        imports = []

        lines = content.split("\n")

        # Extract includes
        include_pattern = r"#include\s+[<\"]([^>\"]+)[>\"]"
        for line in lines:
            matches = re.finditer(include_pattern, line)
            for match in matches:
                header = match.group(1)
                if header not in imports:
                    imports.append(header)

        # Extract function declarations
        func_pattern = r"(\w+)\s+(\w+)\s*\(([^)]*)\)\s*(?:;|{)"
        seen_functions = set()

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(func_pattern, line)
            for match in matches:
                match.group(1)
                func_name = match.group(2)
                params_str = match.group(3) if match.lastindex and match.lastindex >= 3 else ""
                params = [
                    p.strip().split()[-1].rstrip("*") for p in params_str.split(",") if p.strip()
                ]

                if func_name not in seen_functions:
                    functions.append(
                        {"name": func_name, "params": params, "line": line_num, "docstring": ""}
                    )
                    seen_functions.add(func_name)

        loc = len([line for line in lines if line.strip() and not line.strip().startswith("//")])

        return {
            "language": "c",
            "file_path": file_path,
            "functions": functions,
            "classes": [],
            "imports": imports,
            "structure_summary": self._generate_structure_summary("c", functions, [], imports),
            "metrics": {
                "lines_of_code": loc,
                "function_count": len(functions),
                "class_count": 0,
                "import_count": len(imports),
            },
        }

    # Helper methods

    def _extract_python_params(self, node: ast.FunctionDef) -> List[str]:
        """Extract parameter names from Python function node."""
        params = []
        if node.args.args:
            params = [arg.arg for arg in node.args.args]
        return params

    def _get_node_name(self, node: Any) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        return ""

    def _extract_js_methods(self, content: str, class_name: str) -> List[Dict]:
        """Extract methods from a JavaScript class."""
        methods = []
        # Simple extraction - find method patterns within class
        # This is a simplified approach; production code would need better parsing
        method_pattern = r"(\w+)\s*\(([^)]*)\)\s*{"
        lines = content.split("\n")

        in_class = False
        for line in lines:
            if f"class {class_name}" in line:
                in_class = True
            elif in_class and line.strip().startswith("}"):
                in_class = False
            elif in_class:
                matches = re.finditer(method_pattern, line)
                for match in matches:
                    method_name = match.group(1)
                    if method_name not in ["if", "for", "while", "switch"]:
                        params_str = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
                        params = [p.strip() for p in params_str.split(",") if p.strip()]
                        methods.append({"name": method_name, "params": params, "line": 0})

        return methods

    def _extract_java_methods(self, content: str) -> List[Dict]:
        """Extract methods from Java class."""
        methods = []
        method_pattern = (
            r"(?:public|private|protected)?\s+(?:static\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)"
        )
        lines = content.split("\n")

        seen = set()
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(method_pattern, line)
            for match in matches:
                method_name = match.group(2)
                params_str = match.group(3) if match.lastindex and match.lastindex >= 3 else ""
                params = [p.strip().split()[-1] for p in params_str.split(",") if p.strip()]

                if method_name not in seen:
                    methods.append({"name": method_name, "params": params, "line": line_num})
                    seen.add(method_name)

        return methods

    def _generate_structure_summary(
        self, language: str, functions: List[Dict], classes: List[Dict], imports: List[str]
    ) -> str:
        """Generate human-readable structure summary."""
        parts = []

        if functions:
            func_names = ", ".join([f["name"] for f in functions[:3]])
            if len(functions) > 3:
                func_names += f", +{len(functions) - 3} more"
            parts.append(f"{len(functions)} function(s): {func_names}")

        if classes:
            class_names = ", ".join([c["name"] for c in classes[:2]])
            if len(classes) > 2:
                class_names += f", +{len(classes) - 2} more"
            parts.append(f"{len(classes)} class(es): {class_names}")

        if imports:
            import_names = ", ".join(imports[:3])
            if len(imports) > 3:
                import_names += f", +{len(imports) - 3} more"
            parts.append(f"{len(imports)} imports")

        if not parts:
            return f"{language} source file with no visible structure"

        return " | ".join(parts)

    def _get_file_extension(self, file_path: str) -> str:
        """Extract file extension from path."""
        if "." in file_path:
            return "." + file_path.split(".")[-1]
        return ""

    def _create_unsupported_response(self, file_path: str) -> Dict[str, Any]:
        """Create response for unsupported file types."""
        return {
            "language": "unknown",
            "file_path": file_path,
            "functions": [],
            "classes": [],
            "imports": [],
            "structure_summary": "Unsupported file type - treating as plain text",
            "metrics": {
                "lines_of_code": 0,
                "function_count": 0,
                "class_count": 0,
                "import_count": 0,
            },
        }

    def _create_error_response(self, file_path: str, error_msg: str) -> Dict[str, Any]:
        """Create response when parsing fails."""
        return {
            "language": "unknown",
            "file_path": file_path,
            "functions": [],
            "classes": [],
            "imports": [],
            "structure_summary": f"Parse error: {error_msg}",
            "error": error_msg,
            "metrics": {
                "lines_of_code": 0,
                "function_count": 0,
                "class_count": 0,
                "import_count": 0,
            },
        }
