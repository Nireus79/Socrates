"""
Code Extraction Utilities for Markdown-to-Python Conversion

This module handles extraction of Python code from markdown-formatted responses,
ensuring that Claude's markdown-formatted outputs are converted to executable Python.

Problem Solved:
- Claude API returns markdown-formatted responses with code blocks (```python```)
- Multi-file splitting fails on markdown format (invalid Python syntax)
- Solution: Extract actual Python code from markdown before processing
"""

import re
import ast
import logging
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)


class CodeExtractor:
    """Extract and validate Python code from various formats."""

    # Markdown code fence patterns
    CODE_FENCE_PATTERN = r"```(?:python|py)?\n(.*?)```"
    MARKDOWN_HEADER_PATTERN = r"^#+\s"
    MARKDOWN_PATTERNS = [
        r"^#+\s",  # Headers
        r"^-\s",  # Unordered lists
        r"^\d+\.\s",  # Ordered lists
        r"^\*\*",  # Bold
        r"^__",  # Bold alternative
        r"^`{3}",  # Code fences
    ]

    @staticmethod
    def is_markdown_format(content: str) -> bool:
        """
        Check if content appears to be in markdown format.

        Detects common markdown patterns that shouldn't be in Python code.

        Args:
            content: The content to check

        Returns:
            True if content appears to be markdown-formatted
        """
        if not content:
            return False

        lines = content.split("\n")

        # Check for markdown code fences
        if "```python" in content or "```py" in content or "```" in content:
            logger.debug("Detected markdown code fences (```)")
            return True

        # Check for multiple markdown headers
        header_count = sum(1 for line in lines if re.match(CodeExtractor.MARKDOWN_HEADER_PATTERN, line))
        if header_count >= 2:
            logger.debug(f"Detected {header_count} markdown headers (##)")
            return True

        # Check for markdown patterns in first few lines
        first_lines = "\n".join(lines[:10])
        for pattern in CodeExtractor.MARKDOWN_PATTERNS:
            if re.search(pattern, first_lines, re.MULTILINE):
                matches = len(re.findall(pattern, first_lines, re.MULTILINE))
                if matches >= 2:
                    logger.debug(f"Detected markdown pattern: {pattern} ({matches} matches)")
                    return True

        return False

    @staticmethod
    def extract_from_markdown(content: str) -> str:
        """
        Extract Python code from markdown-formatted content.

        Looks for code fences (```python ... ```) and extracts the code between them.
        If no code fences found, returns content as-is (assumes already raw code).

        Args:
            content: Markdown-formatted content potentially containing code blocks

        Returns:
            Extracted Python code, or original content if not markdown
        """
        if not content:
            return content

        # Check if this looks like markdown
        if not CodeExtractor.is_markdown_format(content):
            logger.debug("Content doesn't appear to be markdown, returning as-is")
            return content

        logger.info("Extracting Python code from markdown format")

        # Find all code fences with python/py language
        code_blocks = re.findall(
            CodeExtractor.CODE_FENCE_PATTERN,
            content,
            re.DOTALL
        )

        if code_blocks:
            logger.info(f"Found {len(code_blocks)} code block(s) in markdown")

            # If multiple blocks, combine them
            if len(code_blocks) > 1:
                logger.debug(f"Combining {len(code_blocks)} code blocks")
                extracted = "\n\n".join(block.strip() for block in code_blocks)
            else:
                extracted = code_blocks[0].strip()

            return extracted

        # If no code fences found but content looks like markdown,
        # try to extract code-like sections
        logger.warning("No markdown code fences found, attempting to extract code sections")

        # Remove common markdown elements and keep Python-like lines
        lines = content.split("\n")
        code_lines = []

        for line in lines:
            # Skip markdown headers and list items
            if re.match(r"^#+\s", line):  # Headers
                continue
            if re.match(r"^[-*]\s", line):  # Unordered lists
                continue
            if re.match(r"^\d+\.\s", line):  # Ordered lists
                continue
            if line.strip().startswith("- "):  # Bullet points
                continue
            if line.strip().startswith(">"):  # Blockquotes
                continue

            code_lines.append(line)

        extracted = "\n".join(code_lines).strip()

        if extracted:
            logger.info("Extracted code-like content from markdown")
            return extracted

        # Fallback: return original if extraction failed
        logger.warning("Code extraction failed, returning original content")
        return content

    @staticmethod
    def validate_python_syntax(content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that content is valid Python code.

        Uses ast.parse() to check if code is syntactically valid Python.

        Args:
            content: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if code is valid Python
            - error_message: None if valid, error string if invalid
        """
        if not content or not content.strip():
            return False, "Empty content"

        try:
            ast.parse(content)
            logger.debug("Code validation: syntax is valid")
            return True, None

        except SyntaxError as e:
            error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  {e.text.strip()}"
            logger.error(f"Code validation failed: {error_msg}")
            return False, error_msg

        except ValueError as e:
            error_msg = f"ValueError: {str(e)}"
            logger.error(f"Code validation failed: {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Unexpected error during validation: {error_msg}")
            return False, error_msg

    @staticmethod
    def extract_and_validate(content: str) -> Tuple[str, bool, Optional[str]]:
        """
        Extract code from markdown (if needed) and validate it in one step.

        Convenience method that combines extraction and validation.

        Args:
            content: Original content (may be markdown or raw Python)

        Returns:
            Tuple of (extracted_code, is_valid, error_message)
        """
        # Extract from markdown if needed
        extracted = CodeExtractor.extract_from_markdown(content)

        # Validate the extracted code
        is_valid, error = CodeExtractor.validate_python_syntax(extracted)

        return extracted, is_valid, error

    @staticmethod
    def get_code_statistics(content: str) -> dict:
        """
        Analyze extracted code and return statistics.

        Args:
            content: Python code to analyze

        Returns:
            Dictionary with code statistics
        """
        lines = content.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        comment_lines = [l for l in lines if l.strip().startswith("#")]

        stats = {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "is_valid_python": CodeExtractor.validate_python_syntax(content)[0],
        }

        # Try to parse and get AST statistics
        try:
            tree = ast.parse(content)
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

            stats.update({
                "class_count": len(classes),
                "function_count": len(functions),
                "import_count": len(imports),
            })
        except Exception as e:
            logger.warning(f"Could not parse AST for statistics: {e}")

        return stats
