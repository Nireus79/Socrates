"""
Code Extractor Plugin System

Extensible architecture for language-specific code extraction and validation.
Allows community contributions of new language extractors without core code changes.

Main Classes:
- BaseLanguageExtractor: Abstract base class for all extractors
- LanguageExtractorRegistry: Plugin registry and factory
- ValidationResult: Result of syntax validation
- ExtractionResult: Result of code extraction

Usage:
    from socratic_system.utils.extractors.registry import LanguageExtractorRegistry

    # Get extractor for a language
    extractor = LanguageExtractorRegistry.get_extractor("python")
    if extractor:
        result = extractor.extract_and_validate(markdown_content)
        if result.is_valid:
            print(result.extracted_code)

    # List available extractors
    for metadata in LanguageExtractorRegistry.list_available():
        print(f"{metadata.display_name}: {metadata.description}")
"""

from .base import BaseLanguageExtractor
from .models import ValidationResult, ExtractionResult
from .registry import LanguageExtractorRegistry, LanguageExtractorMetadata
from .python_extractor import PythonExtractor
from .generic_extractor import GenericExtractor

__all__ = [
    "BaseLanguageExtractor",
    "ValidationResult",
    "ExtractionResult",
    "LanguageExtractorRegistry",
    "LanguageExtractorMetadata",
    "PythonExtractor",
    "GenericExtractor",
]
