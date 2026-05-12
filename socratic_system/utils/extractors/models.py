"""
Data models for code extraction and validation results

Provides standardized structures for extraction and validation operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of code syntax validation"""

    is_valid: bool
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)
    line_number: int | None = None

    def __post_init__(self):
        """Ensure warnings is always a list"""
        if self.warnings is None:
            self.warnings = []


@dataclass
class ExtractionResult:
    """Result of code extraction from markdown"""

    extracted_code: str
    is_valid: bool
    validation_error: str | None = None
    was_markdown: bool = False
    code_blocks_found: int = 0

    def __bool__(self):
        """Return True if code extraction was valid"""
        return self.is_valid
