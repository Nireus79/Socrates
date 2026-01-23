"""
Base abstract class for language-specific code extractors

Defines the interface that all language extractors must implement.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from .models import ValidationResult, ExtractionResult

logger = logging.getLogger(__name__)


class BaseLanguageExtractor(ABC):
    """
    Abstract base class for language-specific code extractors.

    All language extractors must inherit from this class and implement
    the abstract methods. Concrete methods provide common functionality
    for markdown detection and code extraction.
    """

    # Markdown detection patterns
    CODE_FENCE_PATTERN = r"```(?:{fence})\n(.*?)```"
    MARKDOWN_HEADER_PATTERN = r"^#+\s"
    MARKDOWN_PATTERNS = [
        r"^#+\s",  # Headers
        r"^-\s",  # Unordered lists
        r"^\d+\.\s",  # Ordered lists
        r"^\*\*",  # Bold
        r"^__",  # Bold alternative
        r"^`{3}",  # Code fences
    ]

    def __init__(self, language: str):
        """
        Initialize extractor for a specific language.

        Args:
            language: Language name (e.g., 'python', 'javascript')
        """
        self.language = language
        self.logger = logging.getLogger(f"socrates.extractors.{language}")

    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """
        Return file extensions for this language.

        Returns:
            List of extensions (e.g., ['.py', '.pyw'])
        """
        pass

    @abstractmethod
    def get_code_fence_identifiers(self) -> List[str]:
        """
        Return markdown code fence identifiers for this language.

        Used to extract code from markdown code blocks.

        Returns:
            List of fence identifiers (e.g., ['python', 'py', 'python3'])
        """
        pass

    @abstractmethod
    def validate_syntax(self, code: str) -> ValidationResult:
        """
        Validate code syntax using language-specific parser.

        Args:
            code: Source code to validate

        Returns:
            ValidationResult with is_valid and error details
        """
        pass

    @abstractmethod
    def get_import_statements(self, code: str) -> List[str]:
        """
        Extract import/require/use statements from code.

        Used for dependency detection and requirements.txt generation.

        Args:
            code: Source code to analyze

        Returns:
            List of import statements or module names
        """
        pass

    def is_markdown_format(self, content: str) -> bool:
        """
        Check if content appears to be in markdown format.

        Detects common markdown patterns that shouldn't be in source code.

        Args:
            content: Content to check

        Returns:
            True if content appears to be markdown
        """
        if not content:
            return False

        lines = content.split("\n")

        # Check for markdown code fences
        if "```" in content:
            self.logger.debug("Detected markdown code fences (```)")
            return True

        # Check for multiple markdown headers
        header_count = sum(1 for line in lines if re.match(self.MARKDOWN_HEADER_PATTERN, line))
        if header_count >= 2:
            self.logger.debug(f"Detected {header_count} markdown headers (##)")
            return True

        # Check for markdown patterns in first few lines
        first_lines = "\n".join(lines[:10])
        for pattern in self.MARKDOWN_PATTERNS:
            if re.search(pattern, first_lines, re.MULTILINE):
                matches = len(re.findall(pattern, first_lines, re.MULTILINE))
                if matches >= 2:
                    self.logger.debug(f"Detected markdown pattern: {pattern} ({matches} matches)")
                    return True

        return False

    def extract_from_markdown(self, content: str) -> ExtractionResult:
        """
        Extract code blocks from markdown content.

        Looks for code fences using language-specific identifiers
        and extracts the code between them.

        Args:
            content: Markdown-formatted content

        Returns:
            ExtractionResult with extracted code and metadata
        """
        if not content:
            return ExtractionResult(extracted_code="", is_valid=False, validation_error="Empty content")

        # Check if this looks like markdown
        if not self.is_markdown_format(content):
            self.logger.debug("Content doesn't appear to be markdown, returning as-is")
            return ExtractionResult(
                extracted_code=content,
                is_valid=True,
                was_markdown=False
            )

        self.logger.info(f"Extracting {self.language} code from markdown format")

        # Get fence identifiers for this language
        fences = self.get_code_fence_identifiers()

        # Build regex pattern for this language's code fences
        fence_pattern = "|".join(re.escape(fence) for fence in fences)
        pattern = self.CODE_FENCE_PATTERN.format(fence=fence_pattern)

        # Find all code blocks
        code_blocks = re.findall(pattern, content, re.DOTALL)

        if code_blocks:
            self.logger.info(f"Found {len(code_blocks)} code block(s) in markdown")

            # Combine multiple blocks
            extracted = "\n\n".join(block.strip() for block in code_blocks)

            # Validate extraction
            validation = self.validate_syntax(extracted)

            return ExtractionResult(
                extracted_code=extracted,
                is_valid=validation.is_valid,
                validation_error=validation.error_message,
                was_markdown=True,
                code_blocks_found=len(code_blocks)
            )

        # If no code fences found but content looks like markdown,
        # try to extract code-like sections
        self.logger.warning("No markdown code fences found, attempting fallback extraction")

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
            if line.strip().startswith(">"):  # Blockquotes
                continue

            code_lines.append(line)

        extracted = "\n".join(code_lines).strip()

        if extracted:
            self.logger.info("Extracted code-like content from markdown")
            validation = self.validate_syntax(extracted)

            return ExtractionResult(
                extracted_code=extracted,
                is_valid=validation.is_valid,
                validation_error=validation.error_message,
                was_markdown=True,
                code_blocks_found=0
            )

        # Fallback: return original if extraction failed
        self.logger.warning("Code extraction failed, returning original content")
        return ExtractionResult(
            extracted_code=content,
            is_valid=False,
            validation_error="Could not extract valid code from markdown",
            was_markdown=True,
            code_blocks_found=0
        )

    def extract_and_validate(self, content: str) -> ExtractionResult:
        """
        Extract code from markdown (if needed) and validate in one step.

        Convenience method combining extraction and validation.

        Args:
            content: Source content (may be markdown or raw code)

        Returns:
            ExtractionResult with extracted code and validation status
        """
        # Extract from markdown if needed
        extracted = self.extract_from_markdown(content)

        # If extraction failed, return the result
        if not extracted.is_valid:
            return extracted

        # Validate the extracted/original code
        validation = self.validate_syntax(extracted.extracted_code)

        return ExtractionResult(
            extracted_code=extracted.extracted_code,
            is_valid=validation.is_valid,
            validation_error=validation.error_message,
            was_markdown=extracted.was_markdown,
            code_blocks_found=extracted.code_blocks_found
        )

    def get_code_statistics(self, code: str) -> dict:
        """
        Analyze code and return basic statistics.

        Args:
            code: Source code to analyze

        Returns:
            Dictionary with line counts and validity
        """
        lines = code.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        comment_lines = [l for l in lines if l.strip().startswith("#")]

        validation = self.validate_syntax(code)

        return {
            "language": self.language,
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "is_valid": validation.is_valid,
        }
