"""
Generic language extractor with no syntax validation

Provides fallback extractor for languages without specific validators.
Extracts markdown but cannot validate syntax.
"""

import logging
from typing import List

from .base import BaseLanguageExtractor
from .models import ValidationResult

logger = logging.getLogger(__name__)


class GenericExtractor(BaseLanguageExtractor):
    """
    Generic code extractor for languages without specific validators.

    Extracts code from markdown but cannot validate syntax.
    Provides graceful fallback for unsupported languages.
    """

    def __init__(self, language: str, extensions: List[str], fences: List[str]):
        """
        Initialize generic extractor for a language.

        Args:
            language: Language name (e.g., 'rust', 'go')
            extensions: File extensions (e.g., ['.rs', '.toml'])
            fences: Markdown fence identifiers (e.g., ['rust', 'rs'])
        """
        super().__init__(language)
        self._extensions = extensions
        self._fences = fences
        self.logger.debug(f"Initialized GenericExtractor for {language}")

    def get_file_extensions(self) -> List[str]:
        """Return file extensions for this language"""
        return self._extensions

    def get_code_fence_identifiers(self) -> List[str]:
        """Return markdown fence identifiers for this language"""
        return self._fences

    def validate_syntax(self, code: str) -> ValidationResult:
        """
        Validate code syntax.

        For generic extractor, no validation is performed.
        Code is accepted if non-empty.

        Args:
            code: Source code (no validation performed)

        Returns:
            ValidationResult indicating code is valid (with warning)
        """
        if not code or not code.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Empty code"
            )

        # No validation available - assume code is valid but warn user
        warnings = [f"No syntax validation available for {self.language}"]

        return ValidationResult(
            is_valid=True,
            warnings=warnings
        )

    def get_import_statements(self, code: str) -> List[str]:
        """
        Extract import/require/use statements from code.

        For generic extractor, performs simple pattern matching.
        Not language-specific so accuracy is limited.

        Args:
            code: Source code to analyze

        Returns:
            List of potential import statements
        """
        imports = []

        # Simple pattern matching for common import styles
        for line in code.split('\n'):
            line = line.strip()

            # Match various import styles
            if line.startswith('import '):  # import x (Java, Go, etc.)
                imports.append(line)
            elif line.startswith('require('):  # require('x') (Node.js)
                imports.append(line)
            elif line.startswith('use '):  # use x (Perl, Rust)
                imports.append(line)
            elif line.startswith('use std::'):  # use std::x (Rust)
                imports.append(line)
            elif line.startswith('from '):  # from x import y (Python)
                imports.append(line)
            elif line.startswith('#include '):  # #include (C/C++)
                imports.append(line)

        return imports
