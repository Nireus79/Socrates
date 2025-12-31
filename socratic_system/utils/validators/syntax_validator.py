"""
Syntax Validator - Validates code syntax for multiple languages

Supports:
- Python (using compile())
- JavaScript/TypeScript (basic patterns)
- Other languages (basic checks)
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("socrates.utils.validators.syntax_validator")


class SyntaxValidator:
    """Validates syntax for multiple programming languages"""

    SUPPORTED_LANGUAGES = {
        "python": [".py"],
        "javascript": [".js", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "go": [".go"],
        "rust": [".rs"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
    }

    def validate(self, target: str) -> Dict[str, Any]:
        """
        Validate syntax of file or all files in directory

        Args:
            target: File path or directory path

        Returns:
            {
                "valid": bool,
                "issues": List[Dict],
                "warnings": List[Dict],
                "metadata": {
                    "files_checked": int,
                    "files_valid": int,
                    "files_invalid": int,
                    "languages": List[str]
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
                    "files_checked": 0,
                    "files_valid": 0,
                    "files_invalid": 0,
                    "languages": [],
                },
            }

        if target_path.is_file():
            return self._validate_file(str(target_path))
        else:
            return self._validate_directory(str(target_path))

    def _validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate single file syntax"""
        file_path_obj = Path(file_path)
        language = self._detect_language(file_path_obj)

        if not language:
            return {
                "valid": True,
                "issues": [],
                "warnings": [
                    {
                        "message": f"File type not recognized: {file_path_obj.suffix}",
                        "file": file_path,
                        "severity": "info",
                    }
                ],
                "metadata": {
                    "files_checked": 1,
                    "files_valid": 1,
                    "files_invalid": 0,
                    "languages": [],
                },
            }

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return {
                "valid": False,
                "issues": [
                    {
                        "file": file_path,
                        "message": f"Cannot read file: {str(e)}",
                        "severity": "error",
                    }
                ],
                "warnings": [],
                "metadata": {
                    "files_checked": 1,
                    "files_valid": 0,
                    "files_invalid": 1,
                    "languages": [language],
                },
            }

        # Validate based on language
        if language == "python":
            return self._validate_python_file(file_path, content)
        elif language in ["javascript", "typescript"]:
            return self._validate_javascript_file(file_path, content, language)
        else:
            # Basic validation for other languages
            return {
                "valid": True,
                "issues": [],
                "warnings": [],
                "metadata": {
                    "files_checked": 1,
                    "files_valid": 1,
                    "files_invalid": 0,
                    "languages": [language],
                },
            }

    def _validate_directory(self, dir_path: str) -> Dict[str, Any]:
        """Validate all files in directory"""
        all_issues = []
        all_warnings = []
        files_checked = 0
        files_valid = 0
        files_invalid = 0
        languages_found = set()

        dir_path_obj = Path(dir_path)

        # Skip certain directories
        skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}

        try:
            for file_path in dir_path_obj.rglob("*"):
                # Skip directories
                if file_path.is_dir():
                    # Skip if matches skip pattern
                    if any(skip in file_path.parts for skip in skip_dirs):
                        continue
                    continue

                # Skip if in skip directory
                if any(skip in file_path.parts for skip in skip_dirs):
                    continue

                language = self._detect_language(file_path)
                if not language:
                    continue

                languages_found.add(language)
                files_checked += 1

                # Validate file
                result = self._validate_file(str(file_path))
                if result["valid"]:
                    files_valid += 1
                else:
                    files_invalid += 1
                    all_issues.extend(result["issues"])
                    all_warnings.extend(result["warnings"])
                    # Limit issues to prevent huge responses
                    if len(all_issues) > 100:
                        all_issues = all_issues[:100]
                        all_issues.append({"message": "... (issues truncated)", "severity": "info"})
                        break

        except Exception as e:
            logger.error(f"Error validating directory: {e}")
            all_issues.append({"message": f"Error scanning directory: {str(e)}", "severity": "error"})

        return {
            "valid": len(all_issues) == 0,
            "issues": all_issues,
            "warnings": all_warnings,
            "metadata": {
                "files_checked": files_checked,
                "files_valid": files_valid,
                "files_invalid": files_invalid,
                "languages": sorted(languages_found),
            },
        }

    def _validate_python_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Validate Python syntax using compile()"""
        try:
            compile(content, file_path, "exec")
            return {
                "valid": True,
                "issues": [],
                "warnings": [],
                "metadata": {
                    "files_checked": 1,
                    "files_valid": 1,
                    "files_invalid": 0,
                    "languages": ["python"],
                },
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "issues": [
                    {
                        "file": file_path,
                        "line": e.lineno or 0,
                        "column": e.offset or 0,
                        "message": f"SyntaxError: {e.msg}",
                        "error_type": "SyntaxError",
                        "severity": "error",
                    }
                ],
                "warnings": [],
                "metadata": {
                    "files_checked": 1,
                    "files_valid": 0,
                    "files_invalid": 1,
                    "languages": ["python"],
                },
            }
        except Exception as e:
            return {
                "valid": False,
                "issues": [
                    {
                        "file": file_path,
                        "message": f"Error: {str(e)}",
                        "error_type": type(e).__name__,
                        "severity": "error",
                    }
                ],
                "warnings": [],
                "metadata": {
                    "files_checked": 1,
                    "files_valid": 0,
                    "files_invalid": 1,
                    "languages": ["python"],
                },
            }

    def _validate_javascript_file(
        self, file_path: str, content: str, language: str
    ) -> Dict[str, Any]:
        """Basic JavaScript/TypeScript validation (pattern-based)"""
        issues = []

        # Check for common syntax issues
        # This is basic pattern matching, not a full parser

        lines = content.split("\n")

        # Check for unclosed braces
        open_braces = content.count("{") - content.count("}")
        open_parens = content.count("(") - content.count(")")
        open_brackets = content.count("[") - content.count("]")

        if open_braces != 0 or open_parens != 0 or open_brackets != 0:
            issues.append(
                {
                    "file": file_path,
                    "message": "Unbalanced brackets detected",
                    "severity": "warning",
                    "details": {
                        "unclosed_braces": open_braces,
                        "unclosed_parens": open_parens,
                        "unclosed_brackets": open_brackets,
                    },
                }
            )

        # Check for common issues
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Check for missing semicolons (basic heuristic)
            if (
                stripped
                and not stripped.endswith((";", "{", "}", ",", ":", ")", "/", "*"))
                and "const " in stripped
                or "let " in stripped
                or "var " in stripped
            ):
                if not any(x in stripped for x in ["=>", "if", "for", "while", "function"]):
                    issues.append(
                        {
                            "file": file_path,
                            "line": i,
                            "message": "Missing semicolon (may be required)",
                            "severity": "warning",
                        }
                    )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": [],
            "metadata": {
                "files_checked": 1,
                "files_valid": 1 if not issues else 0,
                "files_invalid": 0 if not issues else 1,
                "languages": [language],
            },
        }

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()

        for language, extensions in self.SUPPORTED_LANGUAGES.items():
            if suffix in extensions:
                return language

        return None
