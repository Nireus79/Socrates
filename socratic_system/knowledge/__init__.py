"""Knowledge management and RAG - imported from socratic-knowledge library."""

try:
    from socratic_knowledge import (
        DEFAULT_KNOWLEDGE,
        CodeParser,
        KnowledgeEntry,
    )

    __all__ = [
        "KnowledgeEntry",
        "CodeParser",
        "DEFAULT_KNOWLEDGE",
    ]
except ImportError:
    # socratic-knowledge library not installed
    __all__ = []
