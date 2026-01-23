"""
Python-specific code extractor and validator

Provides Python code extraction from markdown and syntax validation
using the ast module.
"""

import ast
import logging
from typing import List

from .base import BaseLanguageExtractor
from .models import ValidationResult

logger = logging.getLogger(__name__)


class PythonExtractor(BaseLanguageExtractor):
    """
    Python-specific code extractor and validator.

    Extracts Python code from markdown using language-specific fence identifiers
    and validates syntax using Python's ast module.
    """

    def get_file_extensions(self) -> List[str]:
        """Return file extensions for Python"""
        return [".py", ".pyw", ".pyx"]

    def get_code_fence_identifiers(self) -> List[str]:
        """Return markdown fence identifiers for Python code blocks"""
        return ["python", "py", "python3"]

    def validate_syntax(self, code: str) -> ValidationResult:
        """
        Validate Python code syntax using ast.parse().

        Args:
            code: Python source code to validate

        Returns:
            ValidationResult with validation status and error details
        """
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Empty code"
            )

        try:
            ast.parse(code)
            logger.debug("Python code validation: syntax is valid")
            return ValidationResult(is_valid=True)

        except SyntaxError as e:
            error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  {e.text.strip()}"
            logger.error(f"Python code validation failed: {error_msg}")
            return ValidationResult(
                is_valid=False,
                error_message=error_msg,
                line_number=e.lineno
            )

        except ValueError as e:
            error_msg = f"ValueError: {str(e)}"
            logger.error(f"Python code validation failed: {error_msg}")
            return ValidationResult(
                is_valid=False,
                error_message=error_msg
            )

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Unexpected error during Python validation: {error_msg}")
            return ValidationResult(
                is_valid=False,
                error_message=error_msg
            )

    def get_import_statements(self, code: str) -> List[str]:
        """
        Extract import statements from Python code.

        Extracts top-level module names from import and from...import statements.

        Args:
            code: Python source code to analyze

        Returns:
            List of imported module names (deduplicated and sorted)
        """
        try:
            tree = ast.parse(code)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # import x, y, z
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        imports.append(module_name)

                elif isinstance(node, ast.ImportFrom):
                    # from x import y
                    if node.module:
                        module_name = node.module.split('.')[0]
                        imports.append(module_name)

            # Deduplicate and sort
            return sorted(list(set(imports)))

        except Exception as e:
            logger.warning(f"Failed to extract imports: {e}")
            return []

    def get_code_statistics(self, code: str) -> dict:
        """
        Analyze Python code and return detailed statistics.

        Args:
            code: Python source code to analyze

        Returns:
            Dictionary with code statistics including class/function counts
        """
        stats = super().get_code_statistics(code)

        # Try to parse and get AST statistics
        try:
            tree = ast.parse(code)

            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            imports = self.get_import_statements(code)

            stats.update({
                "class_count": len(classes),
                "function_count": len(functions),
                "import_count": len(imports),
            })

        except Exception as e:
            logger.warning(f"Could not parse AST for statistics: {e}")

        return stats
