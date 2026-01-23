"""
Data models for code extraction and validation results

Provides standardized structures for extraction and validation operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ValidationResult:
    """Result of code syntax validation"""

    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    line_number: Optional[int] = None

    def __post_init__(self):
        """Ensure warnings is always a list"""
        if self.warnings is None:
            self.warnings = []


@dataclass
class ExtractionResult:
    """Result of code extraction from markdown"""

    extracted_code: str
    is_valid: bool
    validation_error: Optional[str] = None
    was_markdown: bool = False
    code_blocks_found: int = 0

    def __bool__(self):
        """ExtractionResult is truthy if code is valid"""
        return self.is_valid
