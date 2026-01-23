"""
Language Extractor Registry

Plugin system for registering and managing language-specific code extractors.
Follows the Provider pattern used in Socrates for LLM providers.
"""

import logging
from typing import Dict, Optional, Type, List
from dataclasses import dataclass, field

from .base import BaseLanguageExtractor

logger = logging.getLogger(__name__)


@dataclass
class LanguageExtractorMetadata:
    """Metadata about a registered language extractor"""

    language: str  # Canonical name: 'python', 'javascript', 'typescript'
    display_name: str  # Human-readable name: 'Python', 'JavaScript'
    file_extensions: List[str]  # File extensions: ['.py', '.pyw']
    fence_identifiers: List[str]  # Markdown fence IDs: ['python', 'py']
    extractor_class: Optional[Type[BaseLanguageExtractor]] = None  # Extractor class
    supports_ast: bool = False  # Can parse AST for advanced analysis
    supports_linting: bool = False  # Can run linting checks
    available: bool = True  # Is the validator available?
    description: str = ""  # Description of the extractor
    requires_external_tool: bool = False  # Needs external command-line tools?
    dependencies: List[str] = field(default_factory=list)  # Required Python packages


class LanguageExtractorRegistry:
    """
    Registry for language-specific code extractors.

    Manages registration, lookup, and retrieval of extractors.
    Supports multiple lookup methods (by language, by extension, by fence identifier).
    """

    _extractors: Dict[str, LanguageExtractorMetadata] = {}
    _extension_map: Dict[str, str] = {}  # '.py' -> 'python'
    _fence_map: Dict[str, str] = {}  # 'python' -> 'python'

    @classmethod
    def register(cls, metadata: LanguageExtractorMetadata) -> None:
        """
        Register a language extractor.

        Args:
            metadata: LanguageExtractorMetadata with extractor information

        Raises:
            ValueError: If required fields are missing
        """
        if not metadata.language:
            raise ValueError("Language name is required")
        if not metadata.file_extensions:
            raise ValueError("File extensions are required")
        if not metadata.fence_identifiers:
            raise ValueError("Fence identifiers are required")

        cls._extractors[metadata.language] = metadata

        # Build extension mapping
        for ext in metadata.file_extensions:
            cls._extension_map[ext.lower()] = metadata.language

        # Build fence identifier mapping
        for fence in metadata.fence_identifiers:
            cls._fence_map[fence.lower()] = metadata.language

        logger.debug(f"Registered extractor for language: {metadata.language}")

    @classmethod
    def get_extractor(cls, language: str) -> Optional[BaseLanguageExtractor]:
        """
        Get an extractor instance for a language.

        Args:
            language: Language name (e.g., 'python', 'javascript')

        Returns:
            Extractor instance or None if not available
        """
        metadata = cls._extractors.get(language.lower())

        if not metadata:
            logger.warning(f"No extractor registered for language: {language}")
            return None

        if not metadata.available:
            logger.warning(
                f"Extractor for {language} is not available. "
                f"Install: {', '.join(metadata.dependencies) if metadata.dependencies else 'N/A'}"
            )
            return None

        if not metadata.extractor_class:
            logger.warning(f"No extractor class defined for {language}")
            return None

        return metadata.extractor_class(language)

    @classmethod
    def get_by_extension(cls, file_extension: str) -> Optional[BaseLanguageExtractor]:
        """
        Get an extractor by file extension.

        Args:
            file_extension: File extension (e.g., '.py', '.js')

        Returns:
            Extractor instance or None if not available
        """
        ext_lower = file_extension.lower()
        language = cls._extension_map.get(ext_lower)

        if not language:
            logger.debug(f"No language found for extension: {file_extension}")
            return None

        return cls.get_extractor(language)

    @classmethod
    def get_by_fence(cls, fence_identifier: str) -> Optional[BaseLanguageExtractor]:
        """
        Get an extractor by markdown fence identifier.

        Args:
            fence_identifier: Fence identifier (e.g., 'python', 'js', 'typescript')

        Returns:
            Extractor instance or None if not available
        """
        fence_lower = fence_identifier.lower()
        language = cls._fence_map.get(fence_lower)

        if not language:
            logger.debug(f"No language found for fence identifier: {fence_identifier}")
            return None

        return cls.get_extractor(language)

    @classmethod
    def list_available(cls) -> List[LanguageExtractorMetadata]:
        """
        List all available (installed) extractors.

        Returns:
            List of available LanguageExtractorMetadata
        """
        return [m for m in cls._extractors.values() if m.available]

    @classmethod
    def list_all(cls) -> List[LanguageExtractorMetadata]:
        """
        List all registered extractors (available and unavailable).

        Returns:
            List of all registered LanguageExtractorMetadata
        """
        return list(cls._extractors.values())

    @classmethod
    def get_metadata(cls, language: str) -> Optional[LanguageExtractorMetadata]:
        """
        Get metadata for a language without instantiating the extractor.

        Args:
            language: Language name

        Returns:
            LanguageExtractorMetadata or None
        """
        return cls._extractors.get(language.lower())

    @classmethod
    def is_available(cls, language: str) -> bool:
        """
        Check if an extractor is available for a language.

        Args:
            language: Language name

        Returns:
            True if available, False otherwise
        """
        metadata = cls._extractors.get(language.lower())
        return metadata is not None and metadata.available

    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered extractors (for testing)."""
        cls._extractors.clear()
        cls._extension_map.clear()
        cls._fence_map.clear()
        logger.debug("Cleared all registered extractors")


# Auto-registration of built-in extractors
def auto_register_extractors() -> None:
    """
    Automatically register all available extractors.

    Called on module import to register built-in extractors.
    """
    # Import and register Python extractor
    try:
        from .python_extractor import PythonExtractor

        LanguageExtractorRegistry.register(
            LanguageExtractorMetadata(
                language="python",
                display_name="Python",
                file_extensions=[".py", ".pyw", ".pyx"],
                fence_identifiers=["python", "py", "python3"],
                extractor_class=PythonExtractor,
                supports_ast=True,
                supports_linting=True,
                available=True,
                description="Python code extraction and validation using ast module"
            )
        )
        logger.info("Registered Python extractor")

    except Exception as e:
        logger.error(f"Failed to register Python extractor: {e}")

    # Try to register JavaScript extractor (optional dependency)
    try:
        from .javascript_extractor import JavaScriptExtractor

        LanguageExtractorRegistry.register(
            LanguageExtractorMetadata(
                language="javascript",
                display_name="JavaScript",
                file_extensions=[".js", ".mjs", ".cjs"],
                fence_identifiers=["javascript", "js"],
                extractor_class=JavaScriptExtractor,
                supports_ast=True,
                supports_linting=False,
                available=True,
                description="JavaScript code extraction using esprima parser",
                requires_external_tool=False,
                dependencies=["esprima"]
            )
        )
        logger.info("Registered JavaScript extractor")

    except ImportError:
        # Register as unavailable
        LanguageExtractorRegistry.register(
            LanguageExtractorMetadata(
                language="javascript",
                display_name="JavaScript",
                file_extensions=[".js", ".mjs", ".cjs"],
                fence_identifiers=["javascript", "js"],
                extractor_class=None,
                supports_ast=False,
                supports_linting=False,
                available=False,
                description="JavaScript extraction (requires: pip install esprima)",
                requires_external_tool=False,
                dependencies=["esprima"]
            )
        )
        logger.debug("JavaScript extractor not available (esprima not installed)")

    except Exception as e:
        logger.error(f"Failed to register JavaScript extractor: {e}")


# Call auto-registration on module import
auto_register_extractors()
